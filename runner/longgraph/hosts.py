"""Host surface. MockHost, PromptOnlyHost, and GrokBotDualTimerHost are deterministic and have no model."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .rotate import (
    DIRECTIVES_ARCHIVE_HEADING,
    append_correction_packet,
    merge_archive,
    next_directive_id,
    parse_rotation_caps,
    rotate_directives,
)
from .state import parse_run, paths_from_write_set

NOOP_MESSAGE = "no-op"
_TERMINAL_LEDGER = frozenset({"exit-ready", "stalled", "closed"})
_INTERVAL_RE = re.compile(r"^(\d+)\s*([smhd])$", re.I)
_INTERVAL_UNIT_SECONDS = {"s": 1, "m": 60, "h": 3600, "d": 86400}


class WriteDenied(PermissionError):
    """Single-writer edge violation."""


@dataclass
class NodeResult:
    """Node self-report. `ok` is informational and must never close an item.

    `applied` is true only when the executor actually applied a work write-set
    (including a read-only / empty mapping). Emit-only, timer-only, and no-op
    ticks leave it false so the runner cannot close on a mock-green Verify.
    """

    ok: bool = False
    message: str = ""
    writes: list[str] = field(default_factory=list)
    applied: bool = False


class EdgeWriter:
    """Enforces A1–A3 / A14 at the write gate."""

    def __init__(self, run_dir: Path, workspace: Path):
        self.run_dir = Path(run_dir)
        self.workspace = Path(workspace)
        self.log: list[tuple[str, str]] = []

    def write(self, node: str, path: Path | str, content: str) -> None:
        dest = Path(path)
        name = dest.name
        if node == "supervisor" and name == "ledger.md":
            raise WriteDenied("supervisor cannot write ledger")
        if node == "executor" and name == "directives.md":
            raise WriteDenied("executor cannot write directives")
        if node == "scout" and name in {"ledger.md", "directives.md"}:
            raise WriteDenied("scout writes findings only")
        supervisor_directives = name == "directives.md"
        if node == "supervisor" and not supervisor_directives:
            raise WriteDenied("supervisor writes directives only")
        if node == "scout":
            try:
                dest.resolve().relative_to((self.run_dir / "findings").resolve())
            except ValueError as exc:
                raise WriteDenied("scout writes findings only") from exc
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(content, encoding="utf-8")
        self.log.append((node, str(dest)))


class Host:
    """Public host interface. No peer-wake methods exist on this type."""

    def invoke(self, node: str, prompt: str, ctx: dict[str, Any]) -> NodeResult:
        raise NotImplementedError


class MockHost(Host):
    """No-model host: executor applies a write-set map; supervisor/scout stay isolated."""

    def __init__(
        self,
        writer: EdgeWriter | None = None,
        write_map: dict[str, dict[str, str]] | None = None,
        force_ok: bool = True,
    ):
        self.writer = writer
        self.write_map = write_map or {}
        self.force_ok = force_ok
        self.invocations: list[str] = []

    def invoke(self, node: str, prompt: str, ctx: dict[str, Any]) -> NodeResult:
        if self.writer is None:
            writer = ctx.get("writer")
            if writer is None:
                raise RuntimeError("MockHost requires an EdgeWriter")
            self.writer = writer
        self.invocations.append(node)
        if node == "executor":
            return self._executor(ctx)
        if node == "supervisor":
            return self._supervisor(ctx)
        if node == "scout":
            return self._scout(ctx)
        raise ValueError(f"unknown node: {node}")

    def _executor(self, ctx: dict[str, Any]) -> NodeResult:
        item_id = ctx["item_id"]
        mapping = dict(self.write_map.get(item_id) or {})
        if not mapping:
            slice_ = ctx.get("slice")
            write_set = slice_["Write set"] if slice_ is not None else ""
            mapping = paths_from_write_set(write_set)
        writes: list[str] = []
        for rel, content in mapping.items():
            dest = self.writer.workspace / rel
            self.writer.write("executor", dest, content)
            writes.append(rel)
        return NodeResult(ok=self.force_ok, message="mock executor", writes=writes, applied=True)

    def _supervisor(self, ctx: dict[str, Any]) -> NodeResult:
        run_dir = Path(ctx["run_dir"])
        path = run_dir / "directives.md"
        current = path.read_text(encoding="utf-8") if path.exists() else (
            "# Directives\n\n## Supervisor state\n\nLast completed tick: none\n\n"
            "## STANDING — authority only (always in force; treat like red lines)\n\n"
            "(none yet)\n\n"
            "## Corrections (numbered; live queue = not-yet-folded only)\n\n"
            "(none yet)\n"
        )
        watermark = "none"
        if (run_dir / "ledger.md").exists():
            watermark = parse_run(run_dir).last_directive_folded
        ops_path = run_dir / "ops.md"
        ops_text = ops_path.read_text(encoding="utf-8") if ops_path.exists() else ""
        caps = parse_rotation_caps(ops_text)
        # Rotate-before-append: folded IDs leave the live queue first.
        rotated, archive_append = rotate_directives(
            current,
            watermark,
            open_directive_cap=caps.open_directive_cap,
        )
        if archive_append:
            dest = run_dir / "archive" / "directives.md"
            existing = dest.read_text(encoding="utf-8") if dest.exists() else ""
            self.writer.write(
                "supervisor",
                dest,
                merge_archive(existing, archive_append, heading=DIRECTIVES_ARCHIVE_HEADING),
            )
        if "Last completed tick:" in rotated:
            updated = re.sub(
                r"Last completed tick:.*",
                "Last completed tick: mock",
                rotated,
                count=1,
            )
        else:
            updated = rotated.rstrip() + "\nLast completed tick: mock\n"
        next_id = next_directive_id(watermark, updated, archive_append)
        packet = (
            f"{next_id} · mock · plan\n"
            "Context: runner\n"
            "Action: mock supervisor tick\n"
            "Verify: n/a\n"
            "Stop: mock only\n"
        )
        updated = append_correction_packet(updated, packet)
        self.writer.write("supervisor", path, updated)
        return NodeResult(ok=True, message="mock supervisor", writes=["directives.md"])

    def _scout(self, ctx: dict[str, Any]) -> NodeResult:
        blocked = ctx.get("blocked_on") or ""
        ident = blocked.split("#")[-1] if blocked else "brief"
        dest = Path(ctx["run_dir"]) / "findings" / f"{ident}.md"
        if dest.exists():
            return NodeResult(ok=True, message="findings already present", writes=[])
        body = f"# Findings: {ident}\n\n**Status**: complete\n"
        self.writer.write("scout", dest, body)
        return NodeResult(ok=True, message="mock scout", writes=[str(dest)])


_EXEC_PASTE = (
    "/loop {{EXEC_INTERVAL}} Execute the existing runtime node at "
    "{{RUN_DIR}}/executor.md. Do not load any skill."
)
_SUP_PASTE = (
    "/loop {{SUP_INTERVAL}} Execute the existing runtime node at "
    "{{RUN_DIR}}/supervisor.md. Do not load any skill."
)

_DEFAULT_EXEC_INTERVAL = "10m"
_DEFAULT_SUP_INTERVAL = "30m"
_DEFAULT_RUN_DIR = ".longgraph/run"


def _ctx_value(ctx: dict[str, Any] | None, *keys: str) -> str | None:
    if not ctx:
        return None
    for key in keys:
        value = ctx.get(key)
        if value is not None and value != "":
            return str(value).rstrip("/")
    return None


class PromptOnlyHost(Host):
    """No-model host: emit two /loop paste blocks. Never writes edges."""

    def __init__(
        self,
        exec_interval: str = _DEFAULT_EXEC_INTERVAL,
        sup_interval: str = _DEFAULT_SUP_INTERVAL,
        run_dir: str | Path | None = None,
    ):
        self.exec_interval = exec_interval
        self.sup_interval = sup_interval
        self.run_dir = str(run_dir).rstrip("/") if run_dir is not None else None

    def emit_dual_loop(
        self,
        ctx: dict[str, Any] | None = None,
        *,
        exec_interval: str | None = None,
        sup_interval: str | None = None,
        run_dir: str | Path | None = None,
    ) -> str:
        """Return the two paste blocks after placeholder substitution."""
        interval_e = (
            exec_interval
            or _ctx_value(ctx, "EXEC_INTERVAL", "exec_interval")
            or self.exec_interval
            or _DEFAULT_EXEC_INTERVAL
        )
        interval_s = (
            sup_interval
            or _ctx_value(ctx, "SUP_INTERVAL", "sup_interval")
            or self.sup_interval
            or _DEFAULT_SUP_INTERVAL
        )
        dest = (
            (str(run_dir).rstrip("/") if run_dir is not None else None)
            or _ctx_value(ctx, "RUN_DIR", "run_dir")
            or self.run_dir
            or _DEFAULT_RUN_DIR
        )
        executor = (
            _EXEC_PASTE.replace("{{EXEC_INTERVAL}}", interval_e).replace("{{RUN_DIR}}", dest)
        )
        supervisor = (
            _SUP_PASTE.replace("{{SUP_INTERVAL}}", interval_s).replace("{{RUN_DIR}}", dest)
        )
        return f"{executor}\n{supervisor}"

    def invoke(self, node: str, prompt: str, ctx: dict[str, Any]) -> NodeResult:
        # Emit only. Never call a model and never write ledger/directives.
        _ = (node, prompt)
        return NodeResult(ok=True, message=self.emit_dual_loop(ctx), writes=[], applied=False)


def interval_seconds(text: str) -> int:
    """Parse grok.md interval units: Ns, Nm, Nh, Nd."""
    match = _INTERVAL_RE.match(str(text).strip())
    if not match:
        raise ValueError(f"invalid interval {text!r}; expected Ns/Nm/Nh/Nd")
    return int(match.group(1)) * _INTERVAL_UNIT_SECONDS[match.group(2).lower()]


def _timer_row_re(node: str) -> re.Pattern[str]:
    return re.compile(
        rf"^(\|\s*{re.escape(node)}\s*\|\s*[^|\n]+\|\s*)(\S+)(\s*\|)\s*$",
        re.M,
    )


def timer_ids_from_ops(text: str) -> dict[str, str]:
    """Return Timers-cell IDs for executor and supervisor (if present)."""
    found: dict[str, str] = {}
    for node in ("executor", "supervisor"):
        match = _timer_row_re(node).search(text)
        if match:
            found[node] = match.group(2)
    return found


def set_own_timer_cell(text: str, node: str, timer_id: str) -> str:
    """Rewrite only `node`'s Timers cell. Peer rows stay byte-identical."""
    updated, n = _timer_row_re(node).subn(rf"\g<1>{timer_id}\g<3>", text, count=1)
    if n != 1:
        raise ValueError(f"ops.md Timers table has no {node} row")
    return updated


@dataclass
class ScheduledTask:
    """One independent recurring timer. No peer pointer."""

    task_id: str
    prompt: str
    interval: str
    busy: bool = False
    expires_days: int = 7


class FakeScheduler:
    """In-process Grok Build scheduler stand-in. Records create/update/delete/list.

    No network. Honors grok.md limits: min interval 60s; recurring expiry 7d;
    overlapping fires are skipped by the host (task.busy).
    """

    MIN_INTERVAL_SECONDS = 60
    RECURRING_EXPIRY_DAYS = 7

    def __init__(self) -> None:
        self.tasks: dict[str, ScheduledTask] = {}
        self.log: list[tuple[str, str]] = []
        self._n = 0

    def create(self, prompt: str, interval: str, task_id: str | None = None) -> str:
        seconds = interval_seconds(interval)
        if seconds < self.MIN_INTERVAL_SECONDS:
            raise ValueError(
                f"Grok Build minimum recurring interval is {self.MIN_INTERVAL_SECONDS}s"
            )
        if task_id and task_id in self.tasks:
            task = self.tasks[task_id]
            task.prompt = prompt
            task.interval = interval
            self.log.append(("update", task_id))
            return task_id
        self._n += 1
        tid = task_id or f"task-{self._n}"
        self.tasks[tid] = ScheduledTask(
            task_id=tid,
            prompt=prompt,
            interval=interval,
            expires_days=self.RECURRING_EXPIRY_DAYS,
        )
        self.log.append(("create", tid))
        return tid

    def delete(self, task_id: str) -> None:
        self.tasks.pop(task_id, None)
        self.log.append(("delete", task_id))

    def list(self) -> list[ScheduledTask]:
        self.log.append(("list", "*"))
        return list(self.tasks.values())

    def get(self, task_id: str) -> ScheduledTask | None:
        return self.tasks.get(task_id)

    def find_by_pointer(self, pointer: str) -> ScheduledTask | None:
        matches = [task for task in self.tasks.values() if pointer in task.prompt]
        if len(matches) > 1:
            raise RuntimeError(f"multiple scheduler tasks point at {pointer}")
        return matches[0] if matches else None

    def mark_busy(self, task_id: str, busy: bool = True) -> None:
        task = self.tasks.get(task_id)
        if task is not None:
            task.busy = busy


def _node_pointer(run_dir: Path | str, node: str) -> str:
    return f"{str(run_dir).rstrip('/')}/{node}.md"


def _node_prompt(run_dir: Path | str, node: str, *, tick: int | None = None) -> str:
    text = (
        f"Execute the existing runtime node at {_node_pointer(run_dir, node)}. "
        "Do not load any skill."
    )
    if tick is not None:
        text = f"{text} tick={tick}"
    return text


class GrokBotDualTimerHost(Host):
    """Product dual-timer host: two independent schedules, no wake edge.

    Implements the live `Host.invoke(node, prompt, ctx) -> NodeResult` surface.
    Does not call a model. Does not write ledger.md (supervisor) or
    directives.md (executor). Supervisor refreshes its own next-fire prompt
    in place; the executor stays warm.
    """

    def __init__(
        self,
        scheduler: FakeScheduler | None = None,
        exec_interval: str = _DEFAULT_EXEC_INTERVAL,
        sup_interval: str = _DEFAULT_SUP_INTERVAL,
        run_dir: str | Path | None = None,
        workspace: str | Path | None = None,
    ):
        self.scheduler = scheduler or FakeScheduler()
        self.exec_interval = exec_interval
        self.sup_interval = sup_interval
        self.run_dir = Path(run_dir) if run_dir is not None else None
        self.workspace = Path(workspace) if workspace is not None else None
        self.exec_timer_id: str | None = None
        self.sup_timer_id: str | None = None
        self.busy_nodes: set[str] = set()
        self.reads: list[Path] = []
        self._sup_tick = 0

    def schedule(self, ctx: dict[str, Any] | None = None) -> tuple[str, str]:
        """Create two independent timers. Not a peer-wake; no notify/dispatch."""
        run_dir = self._resolve_run_dir(ctx)
        workspace = self._resolve_workspace(ctx, run_dir)
        self.run_dir = run_dir
        self.workspace = workspace
        if self.exec_timer_id and self.scheduler.get(self.exec_timer_id) is None:
            self.exec_timer_id = None
        if self.sup_timer_id and self.scheduler.get(self.sup_timer_id) is None:
            self.sup_timer_id = None
        if self.exec_timer_id is None:
            self.exec_timer_id = self.scheduler.create(
                _node_prompt(run_dir, "executor"),
                self.exec_interval,
            )
        if self.sup_timer_id is None:
            self.sup_timer_id = self.scheduler.create(
                _node_prompt(run_dir, "supervisor"),
                self.sup_interval,
            )
        return self.exec_timer_id, self.sup_timer_id

    def invoke(self, node: str, prompt: str, ctx: dict[str, Any]) -> NodeResult:
        _ = prompt
        if node not in {"executor", "supervisor"}:
            raise ValueError(f"GrokBotDualTimerHost has no {node} schedule")
        run_dir = self._resolve_run_dir(ctx)
        workspace = self._resolve_workspace(ctx, run_dir)
        self.run_dir = run_dir
        self.workspace = workspace

        if self._overlapping(node):
            return NodeResult(ok=True, message=NOOP_MESSAGE, writes=[], applied=False)

        self.busy_nodes.add(node)
        task = self._task_for(node)
        if task is not None:
            task.busy = True
        try:
            self._read_frozen_md(run_dir, node)
            writes: list[str] = []
            if self._seed_own_timer_cell(node, run_dir):
                writes.append("ops.md")
            if self._ledger_terminal(run_dir):
                self._delete_own_timer(node, run_dir)
                return NodeResult(ok=True, message="terminal", writes=writes, applied=False)
            if node == "supervisor":
                self._refresh_supervisor_prompt(run_dir)
            return NodeResult(ok=True, message=f"{node} tick", writes=writes, applied=False)
        finally:
            self.busy_nodes.discard(node)
            if task is not None:
                task.busy = False

    def _resolve_run_dir(self, ctx: dict[str, Any] | None) -> Path:
        raw = _ctx_value(ctx, "run_dir", "RUN_DIR")
        if raw:
            return Path(raw)
        if self.run_dir is not None:
            return Path(self.run_dir)
        raise ValueError("GrokBotDualTimerHost requires run_dir")

    def _resolve_workspace(self, ctx: dict[str, Any] | None, run_dir: Path) -> Path:
        raw = _ctx_value(ctx, "workspace")
        if raw:
            return Path(raw)
        if self.workspace is not None:
            return Path(self.workspace)
        return run_dir / "workspace"

    def _timer_attr(self, node: str) -> str:
        return "exec_timer_id" if node == "executor" else "sup_timer_id"

    def _timer_id(self, node: str) -> str | None:
        return getattr(self, self._timer_attr(node))

    def _set_timer_id(self, node: str, task_id: str) -> None:
        setattr(self, self._timer_attr(node), task_id)

    def _task_for(self, node: str) -> ScheduledTask | None:
        tid = self._timer_id(node)
        return self.scheduler.get(tid) if tid else None

    def _overlapping(self, node: str) -> bool:
        if node in self.busy_nodes:
            return True
        task = self._task_for(node)
        return bool(task and task.busy)

    def _read_frozen_md(self, run_dir: Path, node: str) -> None:
        names = (f"{node}.md", "ledger.md", "ops.md", "directives.md")
        for name in names:
            path = run_dir / name
            if not path.exists():
                continue
            path.read_text(encoding="utf-8")
            self.reads.append(path)

    def _ledger_terminal(self, run_dir: Path) -> bool:
        ledger = run_dir / "ledger.md"
        if not ledger.exists():
            return False
        return parse_run(run_dir).run_status in _TERMINAL_LEDGER

    def _ensure_own_timer(self, node: str, run_dir: Path) -> str:
        existing = self._timer_id(node)
        if existing and self.scheduler.get(existing) is not None:
            return existing
        found = self.scheduler.find_by_pointer(_node_pointer(run_dir, node))
        if found is not None:
            self._set_timer_id(node, found.task_id)
            return found.task_id
        interval = self.exec_interval if node == "executor" else self.sup_interval
        tid = self.scheduler.create(_node_prompt(run_dir, node), interval)
        self._set_timer_id(node, tid)
        return tid

    def _seed_own_timer_cell(self, node: str, run_dir: Path) -> bool:
        ops = run_dir / "ops.md"
        if not ops.exists():
            self._ensure_own_timer(node, run_dir)
            return False
        text = ops.read_text(encoding="utf-8")
        cells = timer_ids_from_ops(text)
        current = cells.get(node, "pending")
        if current != "pending" and self.scheduler.get(current) is not None:
            self._set_timer_id(node, current)
            return False
        tid = self._ensure_own_timer(node, run_dir)
        updated = set_own_timer_cell(text, node, tid)
        if updated == text:
            return False
        ops.write_text(updated, encoding="utf-8")
        return True

    def _delete_own_timer(self, node: str, run_dir: Path) -> None:
        tid = self._timer_id(node)
        if tid is None or self.scheduler.get(tid) is None:
            listed = self.scheduler.list()
            found = self.scheduler.find_by_pointer(_node_pointer(run_dir, node))
            _ = listed
            tid = found.task_id if found is not None else tid
        if tid:
            self.scheduler.delete(tid)
            if self._timer_id(node) == tid:
                self._set_timer_id(node, tid)

    def _refresh_supervisor_prompt(self, run_dir: Path) -> None:
        tid = self._ensure_own_timer("supervisor", run_dir)
        self._sup_tick += 1
        self.scheduler.create(
            _node_prompt(run_dir, "supervisor", tick=self._sup_tick),
            self.sup_interval,
            task_id=tid,
        )
