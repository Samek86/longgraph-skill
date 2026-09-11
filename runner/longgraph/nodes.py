"""Runner loop: independent node ticks, gate-after-executor, Default-FAIL close."""

from __future__ import annotations

import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .gates import GateRunner, classify_verify
from .hosts import NOOP_MESSAGE, EdgeWriter, Host, MockHost
from .retry import RetryKey, increment_retry, set_last_attempt, should_resume_verify_only
from .rotate import (
    DIRECTIVES_ARCHIVE_HEADING,
    ROUNDS_ARCHIVE_HEADING,
    RotationCaps,
    append_round_log_line,
    fold_corrections_into_ledger,
    is_accept_gate_packet,
    merge_archive,
    parse_rotation_caps,
    rotate_directives,
    rotate_rounds_log,
    unfolded_packets,
)
from .state import (
    RunState,
    current_slice_owner_blocked,
    derive_item_id,
    findings_status_complete,
    parse_run,
    paths_from_write_set,
)

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


_MILESTONE_ITEM = re.compile(r"^\s*M\d+\b")
_READ_ONLY_WRITE_SET = frozenset({"", "read-only", "n/a", "none", "-", "—"})
_AUDIT_SURFACE = re.compile(r"^Audit surface:\s*(.*)$", re.I | re.M)


def _audit_surface_paths(ledger_text: str) -> set[str]:
    """Paths named on Pending promotion `Audit surface:` (empty if none)."""
    in_section = False
    for line in ledger_text.splitlines():
        raw = line.strip()
        if raw.startswith("## ") and "pending promotion" in raw.lower():
            in_section = True
            continue
        if in_section and raw.startswith("## "):
            break
        if not in_section:
            continue
        match = _AUDIT_SURFACE.match(raw)
        if match:
            return set(paths_from_write_set(match.group(1)))
    return set()


def current_slice_is_next_milestone_surface(state: RunState, ledger_text: str = "") -> bool:
    """True when the Current-slice write-set is the next-milestone surface.

    CONTRACT §1.4 / A8: `pending-audit` blocks that surface only. An
    already-registered lane item whose write-set is `read-only` or
    disjoint from the audit surface may continue. `next_item` mentioning
    `M\\d+` is not enough to block.
    """
    write_set = (state.current_slice.get("Write set") or "").strip()
    if write_set.lower() in _READ_ONLY_WRITE_SET:
        return False
    item = state.current_slice.Item or ""
    if _MILESTONE_ITEM.match(item):
        return True
    if ledger_text:
        audit = _audit_surface_paths(ledger_text)
        writes = set(paths_from_write_set(write_set))
        if audit and writes & audit:
            return True
    return False


_GAP_ROW = re.compile(r"^(\|\s*)(GAP-\d+)(\s*\|.*)$")
_CLOSED_WORDS = re.compile(r"\bresolved\b|\bclosed\b|\bclosure\b", re.I)


def _gap_one_liner(text: str, gap_id: str) -> str:
    for line in text.splitlines():
        if not re.match(rf"^\|\s*{re.escape(gap_id)}\s*\|", line):
            continue
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if len(cells) >= 3:
            return cells[-1]
    return ""


def _mark_gap_resolved(text: str, item_id: str) -> str:
    if not re.match(r"GAP-\d+$", item_id):
        return text
    out: list[str] = []
    for line in text.splitlines(keepends=True):
        raw = line.split("\n")[0]
        match = _GAP_ROW.match(raw)
        if match and match.group(2) == item_id and not _CLOSED_WORDS.search(raw):
            nl = "\n" if line.endswith("\n") else ""
            line = raw.rstrip() + " — resolved" + nl
        out.append(line)
    return "".join(out)


def _set_header_rest(text: str, label: str, value: str) -> str:
    pattern = re.compile(rf"^({re.escape(label)}:\s*).*$", re.M)
    if not pattern.search(text):
        return text
    return pattern.sub(lambda match: match.group(1) + value, text, count=1)


def _rewrite_current_slice(text: str, fields: dict[str, str]) -> str:
    lines = text.splitlines(keepends=True)
    start: int | None = None
    end = len(lines)
    for i, line in enumerate(lines):
        raw = line.split("\n")[0]
        if start is None and raw.startswith("## ") and raw.lower().startswith("## current slice"):
            start = i
            continue
        if start is not None and raw.startswith("## "):
            end = i
            break
    if start is None:
        return text
    body = (
        "\n"
        f"Item: {fields['Item']}\n"
        f"Write set: {fields['Write set']}\n"
        f"Context: {fields['Context']}\n"
        f"Verify: {fields['Verify']}\n"
        f"Done when: {fields['Done when']}\n"
        "\n"
    )
    return "".join(lines[: start + 1]) + body + "".join(lines[end:])


def retire_live_scoreboard(text: str, item_id: str, remaining_gaps: list[str]) -> str:
    """Rewrite next-item / Current slice / gap register after a green close."""
    updated = _mark_gap_resolved(text, item_id)
    if remaining_gaps:
        next_label = remaining_gaps[0]
        one = _gap_one_liner(updated, next_label)
        if one:
            next_label = f"{next_label} {one}"
        slice_fields = {
            "Item": next_label,
            "Write set": "read-only",
            "Context": "n/a",
            "Verify": "n/a",
            "Done when": "awaiting a compiled slice",
        }
        run_status = None
    else:
        next_label = "none"
        slice_fields = {
            "Item": "(none)",
            "Write set": "read-only",
            "Context": "n/a",
            "Verify": "n/a",
            "Done when": "no remaining unclosed work",
        }
        run_status = "exit-ready"
    updated = _set_header_rest(updated, "Next unclosed work item", next_label)
    updated = _rewrite_current_slice(updated, slice_fields)
    if run_status is not None:
        updated, n = re.subn(
            r"^Run status:\s*`?[\w-]+`?",
            f"Run status: `{run_status}`",
            updated,
            count=1,
            flags=re.M,
        )
        if n == 0:
            updated = updated.rstrip() + f"\nRun status: `{run_status}`\n"
    return updated


def next_item_label(remaining_gaps: list[str], ledger_text: str) -> str:
    if not remaining_gaps:
        return "none"
    gap_id = remaining_gaps[0]
    one = _gap_one_liner(ledger_text, gap_id)
    return f"{gap_id} {one}".strip() if one else gap_id


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
        self.writer.write(
            node,
            dest,
            merge_archive(existing, fragment, heading=heading),
            write_set=False,
        )

    def _rotate_directives(self, state: RunState) -> None:
        """Rotate folded corrections (IDs ≤ watermark) before any supervisor append."""
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
            self.writer.write("supervisor", path, new_text, write_set=False)

    def _applied_work_path(self) -> bool:
        """MockHost is the coupled applied-work path. Emit/timer hosts do not fold."""
        return isinstance(self.host, MockHost)

    def _persist_directive_fold(self, state: RunState) -> RunState:
        """Write ACCEPT-GATE / watermark onto the ledger. Executor is the writer."""
        ledger = self.run_dir / "ledger.md"
        directives = self.run_dir / "directives.md"
        if not ledger.exists() or not directives.exists():
            return state
        text = ledger.read_text(encoding="utf-8")
        updated, _, _ = fold_corrections_into_ledger(
            text,
            directives.read_text(encoding="utf-8"),
            state.last_directive_folded,
        )
        if updated != text:
            self.writer.write("executor", ledger, updated, write_set=False)
            return self._state()
        return state

    def _maybe_release_pending_audit(self, state: RunState) -> RunState:
        """Fold an ACCEPT-GATE correction so the pending gate can flip."""
        if not self._applied_work_path() or state.milestone_gate != "pending-audit":
            return state
        directives = self.run_dir / "directives.md"
        if not directives.exists():
            return state
        packets = unfolded_packets(
            directives.read_text(encoding="utf-8"),
            state.last_directive_folded,
        )
        if not any(is_accept_gate_packet(packet) for _, packet in packets):
            return state
        return self._persist_directive_fold(state)

    def _host_owns_timers(self) -> bool:
        """True when the Host owns independent timers (no coupled peer ticks)."""
        return bool(getattr(self.host, "owns_timers", False))

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

    def _findings_ready(self, state: RunState) -> bool:
        if not state.blocked_on:
            return True
        rel = state.findings_path
        if not rel:
            return False
        path = (self.run_dir / rel).resolve()
        root = (self.run_dir / "findings").resolve()
        try:
            path.relative_to(root)
        except ValueError:
            return False
        if not path.is_file():
            return False
        return findings_status_complete(self._read(path))

    def _item_already_closed(self, status: dict, item_id: str) -> bool:
        if item_id in self.closed_items:
            return True
        closed = (status.get("metadata") or {}).get("closedItems") or []
        if item_id in closed:
            return True
        ledger = self.run_dir / "ledger.md"
        if ledger.exists():
            return f"<!-- runner closed {item_id} -->" in ledger.read_text(encoding="utf-8")
        return False

    def _close_item(self, state: RunState, status: dict, item_id: str, key: RetryKey) -> None:
        ledger = self.run_dir / "ledger.md"
        text = ledger.read_text(encoding="utf-8")
        meta = status.setdefault("metadata", {})
        closed = meta.setdefault("closedItems", [])
        already = (
            item_id in self.closed_items
            or item_id in closed
            or f"<!-- runner closed {item_id} -->" in text
        )
        remaining = [gap for gap in state.open_gaps if gap != item_id]
        if already:
            healed = retire_live_scoreboard(text, item_id, remaining)
            if healed != text:
                caps = self._rotation_caps()
                healed, archive = rotate_rounds_log(healed, keep_rounds=caps.keep_rounds)
                self.writer.write("executor", ledger, healed, write_set=False)
                self._append_archive("executor", "rounds.md", archive, ROUNDS_ARCHIVE_HEADING)
            return

        self.closed_items.append(item_id)
        closed.append(item_id)
        progress = status.setdefault("progress", {})
        progress["completedRounds"] = int(progress.get("completedRounds", 0)) + 1
        progress["completedItems"] = int(progress.get("completedItems", 0)) + 1
        progress["currentItem"] = remaining[0] if remaining else "none"
        set_last_attempt(status, key, "closed")

        def _bump(match: re.Match[str]) -> str:
            return f"{match.group(1)}{int(match.group(2)) + 1}"

        text = re.sub(r"(Round:\s*)(\d+)", _bump, text, count=1)
        text = retire_live_scoreboard(text, item_id, remaining)
        directives = self.run_dir / "directives.md"
        if directives.exists():
            text, _, _ = fold_corrections_into_ledger(
                text,
                directives.read_text(encoding="utf-8"),
                state.last_directive_folded,
            )
        text = append_round_log_line(text, item_id, next_item=next_item_label(remaining, text))
        text = text.rstrip() + f"\n\n<!-- runner closed {item_id} -->\n"
        caps = self._rotation_caps()
        text, archive = rotate_rounds_log(text, keep_rounds=caps.keep_rounds)
        self.writer.write("executor", ledger, text, write_set=False)
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

            state = self._maybe_release_pending_audit(state)
            item_id = derive_item_id(state)
            key = RetryKey(str(status.get("runId") or self.run_dir.name), completed + 1, item_id)

            ledger_text = (self.run_dir / "ledger.md").read_text(encoding="utf-8")
            if (
                state.milestone_gate == "pending-audit"
                and current_slice_is_next_milestone_surface(state, ledger_text)
            ):
                self.advancement_blocked = True
                self.stopped_reason = "pending-audit"
                if not self._host_owns_timers():
                    self._tick_supervisor(state)
                self._save_status(status, state.run_status)
                break

            if self._item_already_closed(status, item_id):
                self._close_item(state, status, item_id, key)
                self._save_status(status, state.run_status)
                continue

            if state.blocked_on and not self._findings_ready(state):
                if not self._host_owns_timers():
                    self._tick_scout(state)
                self._save_status(status, state.run_status)
                continue

            verify_cmd = state.current_slice.get("Verify") or ""
            verify_kind = classify_verify(verify_cmd)
            if current_slice_owner_blocked(state) or verify_kind == "n/a":
                self._save_status(status, state.run_status)
                continue

            if verify_kind == "empty":
                self.gates.run(verify_cmd, self.workspace)
                set_last_attempt(status, key, "verify")
                increment_retry(status, item_id)
                if status["metadata"]["itemRetries"].get(item_id, 0) >= ops.max_retries:
                    self.stopped_reason = "max_retries"
                    status["status"] = "failed"
                if not self._host_owns_timers():
                    self._tick_supervisor(state)
                self._save_status(status, state.run_status)
                if self.stopped_reason:
                    break
                continue

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
                if not result.applied:
                    self._save_status(status, state.run_status)
                    continue
                set_last_attempt(status, key, "write")

            gate = self.gates.run(verify_cmd, self.workspace)
            set_last_attempt(status, key, "verify")
            if gate.skipped:
                if not self._host_owns_timers():
                    self._tick_supervisor(state)
                self._save_status(status, state.run_status)
                continue
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

            if not self._host_owns_timers():
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
