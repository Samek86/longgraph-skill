"""Runner loop: independent node ticks, gate-after-executor, Default-FAIL close."""

from __future__ import annotations

import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .gates import GateRunner
from .hosts import NOOP_MESSAGE, EdgeWriter, Host, MockHost
from .retry import RetryKey, increment_retry, set_last_attempt, should_resume_verify_only
from .rotate import (
    DIRECTIVES_ARCHIVE_HEADING,
    ROUNDS_ARCHIVE_HEADING,
    RotationCaps,
    append_round_log_line,
    merge_archive,
    parse_rotation_caps,
    rotate_directives,
    rotate_rounds_log,
)
from .state import RunState, derive_item_id, parse_run

TERMINAL_LEDGER = frozenset({"exit-ready", "stalled", "closed"})
STOP_STATUS = frozenset({"completed", "cancelled", "failed"})
_AUTHORING_PART = "skills"


class CrashBeforeClose(RuntimeError):
    """verify-green-then-crash-before-close (resume Verify only)."""


class StatusContractError(ValueError):
    """status.json contract violation."""


def _utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def write_status(path: Path, payload: dict, *, ledger_run_status: str | None = None) -> None:
    """Atomic tmp + os.replace. completed requires a terminal ledger."""
    if payload.get("status") == "completed":
        if ledger_run_status not in TERMINAL_LEDGER:
            raise StatusContractError(
                "status completed requires ledger run_status in "
                f"{sorted(TERMINAL_LEDGER)}; got {ledger_run_status!r}"
            )
    dest = Path(path)
    tmp = dest.with_name(dest.name + ".tmp")
    tmp.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    os.replace(tmp, dest)


def _looks_like_milestone_advance(state: RunState) -> bool:
    if state.milestone_gate != "pending-audit":
        return False
    text = f"{state.current_slice.Item} {state.next_item}"
    return bool(re.search(r"\bM\d+\b", text))


class Runner:
    """Drive one run directory. Nodes are ticked independently; no wake API."""

    def __init__(
        self,
        run_dir: str | Path,
        *,
        host: Host | None = None,
        gates: GateRunner | None = None,
        workspace: str | Path | None = None,
        crash_before_close: bool = False,
    ):
        self.run_dir = Path(run_dir)
        self.workspace = Path(workspace) if workspace else self.run_dir / "workspace"
        self.workspace.mkdir(parents=True, exist_ok=True)
        self.writer = EdgeWriter(self.run_dir, self.workspace)
        if host is None:
            self.host = MockHost(self.writer)
        else:
            self.host = host
            if isinstance(host, MockHost) and host.writer is None:
                host.writer = self.writer
        self.gates = gates or GateRunner()
        self.crash_before_close = crash_before_close
        self.reads: list[Path] = []
        self.closed_items: list[str] = []
        self.stopped_reason: str | None = None
        self.advancement_blocked = False

    def _read(self, path: Path) -> str:
        resolved = Path(path).resolve()
        self.reads.append(resolved)
        if _AUTHORING_PART in resolved.parts:
            raise RuntimeError("runner must not read the authoring tree")
        return resolved.read_text(encoding="utf-8")

    def _load_status(self) -> dict:
        path = self.run_dir / "status.json"
        if not path.exists():
            raise FileNotFoundError("runner-managed runs require status.json")
        return json.loads(self._read(path))

    def _save_status(self, status: dict, ledger_run_status: str) -> None:
        status["updatedAt"] = _utc_now()
        write_status(
            self.run_dir / "status.json",
            status,
            ledger_run_status=ledger_run_status,
        )

    def _state(self) -> RunState:
        return parse_run(self.run_dir, read_text=self._read)

    def _rotation_caps(self) -> RotationCaps:
        ops = self.run_dir / "ops.md"
        text = ops.read_text(encoding="utf-8") if ops.exists() else ""
        return parse_rotation_caps(text)

    def _append_archive(self, node: str, name: str, fragment: str, heading: str) -> None:
        if not fragment or not fragment.strip():
            return
        dest = self.run_dir / "archive" / name
        existing = dest.read_text(encoding="utf-8") if dest.exists() else ""
        self.writer.write(node, dest, merge_archive(existing, fragment, heading=heading))

    def _rotate_directives(self, state: RunState) -> None:
        """Rotate folded (and cap-excess) corrections before any supervisor append."""
        path = self.run_dir / "directives.md"
        if not path.exists():
            return
        current = path.read_text(encoding="utf-8")
        caps = self._rotation_caps()
        new_text, archive = rotate_directives(
            current,
            state.last_directive_folded,
            open_directive_cap=caps.open_directive_cap,
        )
        self._append_archive("supervisor", "directives.md", archive, DIRECTIVES_ARCHIVE_HEADING)
        if new_text != current:
            self.writer.write("supervisor", path, new_text)

    def _tick_supervisor(self, state: RunState) -> None:
        self._rotate_directives(state)
        prompt_path = self.run_dir / "supervisor.md"
        prompt = self._read(prompt_path) if prompt_path.exists() else ""
        result = self.host.invoke(
            "supervisor",
            prompt,
            {
                "run_dir": self.run_dir,
                "writer": self.writer,
                "slice": state.current_slice,
            },
        )
        # Overlapping supervisor fire is a complete no-op tick.
        _ = result

    def _tick_scout(self, state: RunState) -> None:
        if not state.blocked_on:
            return
        prompt = ""
        self.host.invoke(
            "scout",
            prompt,
            {
                "run_dir": self.run_dir,
                "writer": self.writer,
                "blocked_on": state.blocked_on,
            },
        )

    def _close_item(self, state: RunState, status: dict, item_id: str, key: RetryKey) -> None:
        self.closed_items.append(item_id)
        meta = status.setdefault("metadata", {})
        closed = meta.setdefault("closedItems", [])
        if item_id not in closed:
            closed.append(item_id)
        progress = status.setdefault("progress", {})
        progress["completedRounds"] = int(progress.get("completedRounds", 0)) + 1
        progress["completedItems"] = int(progress.get("completedItems", 0)) + 1
        set_last_attempt(status, key, "closed")
        ledger = self.run_dir / "ledger.md"
        text = ledger.read_text(encoding="utf-8")

        def _bump(match: re.Match[str]) -> str:
            return f"{match.group(1)}{int(match.group(2)) + 1}"

        text = re.sub(r"(Round:\s*)(\d+)", _bump, text, count=1)
        already = f"<!-- runner closed {item_id} -->" in text
        if not already:
            text = append_round_log_line(text, item_id)
            text = text.rstrip() + f"\n\n<!-- runner closed {item_id} -->\n"
        caps = self._rotation_caps()
        text, archive = rotate_rounds_log(text, keep_rounds=caps.keep_rounds)
        self.writer.write("executor", ledger, text)
        self._append_archive("executor", "rounds.md", archive, ROUNDS_ARCHIVE_HEADING)

    def _mark_completed(self, state: RunState, status: dict) -> None:
        if state.run_status not in TERMINAL_LEDGER:
            raise StatusContractError("cannot complete while ledger is not terminal")
        status["status"] = "completed"
        status["phase"] = "done"
        for node in status.get("nodes", {}).values():
            if isinstance(node, dict):
                node["status"] = "stopped"
        self._save_status(status, state.run_status)

    def run(self, *, steps: int = 8) -> dict[str, Any]:
        for _ in range(steps):
            state = self._state()
            status = self._load_status()
            if status.get("status") in STOP_STATUS:
                break
            if state.run_status in TERMINAL_LEDGER:
                self._mark_completed(state, status)
                break

            ops = state.ops
            completed = int(status.get("progress", {}).get("completedRounds", 0))
            if ops.max_rounds is not None and completed >= ops.max_rounds:
                self.stopped_reason = "max_rounds"
                status["status"] = "paused"
                status["phase"] = "blocked"
                self._save_status(status, state.run_status)
                break

            item_id = derive_item_id(state)
            key = RetryKey(str(status.get("runId") or self.run_dir.name), completed + 1, item_id)

            if _looks_like_milestone_advance(state):
                self.advancement_blocked = True
                self.stopped_reason = "pending-audit"
                self._tick_supervisor(state)
                self._save_status(status, state.run_status)
                break

            resume_verify = should_resume_verify_only(status, key)
            if not resume_verify:
                started = list(status.setdefault("metadata", {}).setdefault("startedItems", []))
                is_new = item_id not in started
                if is_new and ops.smoke:
                    smoke = self.gates.run(ops.smoke, self.workspace)
                    if not smoke.passed:
                        increment_retry(status, item_id)
                        set_last_attempt(status, key, "write")
                        if status["metadata"]["itemRetries"].get(item_id, 0) >= ops.max_retries:
                            self.stopped_reason = "max_retries"
                            status["status"] = "failed"
                        self._save_status(status, state.run_status)
                        if self.stopped_reason:
                            break
                        continue
                if item_id not in started:
                    status["metadata"]["startedItems"].append(item_id)
                prompt_path = self.run_dir / "executor.md"
                prompt = self._read(prompt_path) if prompt_path.exists() else ""
                result = self.host.invoke(
                    "executor",
                    prompt,
                    {
                        "item_id": item_id,
                        "slice": state.current_slice,
                        "run_dir": self.run_dir,
                        "workspace": self.workspace,
                        "writer": self.writer,
                    },
                )
                # Default-FAIL: NodeResult.ok is ignored.
                _ = result.ok
                if (result.message or "").strip().lower().startswith(NOOP_MESSAGE):
                    self._save_status(status, state.run_status)
                    continue
                set_last_attempt(status, key, "write")

            verify_cmd = state.current_slice.get("Verify") or ""
            gate = self.gates.run(verify_cmd, self.workspace)
            set_last_attempt(status, key, "verify")
            if gate.passed:
                set_last_attempt(status, key, "verify_green")
                self._save_status(status, state.run_status)
                if self.crash_before_close:
                    raise CrashBeforeClose("verify-green-then-crash-before-close")
                self._close_item(state, status, item_id, key)
            else:
                increment_retry(status, item_id)
                if status["metadata"]["itemRetries"].get(item_id, 0) >= ops.max_retries:
                    self.stopped_reason = "max_retries"
                    status["status"] = "failed"

            self._tick_supervisor(state)
            if state.blocked_on:
                self._tick_scout(state)
            self._save_status(status, state.run_status)
            if self.stopped_reason:
                break

        return json.loads((self.run_dir / "status.json").read_text(encoding="utf-8"))

    def stop(self) -> dict[str, Any]:
        state = self._state()
        status = self._load_status()
        status["status"] = "cancelled"
        status["phase"] = "done"
        self._save_status(status, state.run_status)
        return status


def set_ledger_run_status(run_dir: Path, run_status: str) -> None:
    path = Path(run_dir) / "ledger.md"
    text = path.read_text(encoding="utf-8")
    updated, n = re.subn(
        r"^Run status:\s*`?[\w-]+`?",
        f"Run status: `{run_status}`",
        text,
        count=1,
        flags=re.M,
    )
    if n == 0:
        updated = text.rstrip() + f"\nRun status: `{run_status}`\n"
    path.write_text(updated, encoding="utf-8")
