"""Host surface. MockHost is deterministic and has no model."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .state import paths_from_write_set


class WriteDenied(PermissionError):
    """Single-writer edge violation."""


@dataclass
class NodeResult:
    """Node self-report. `ok` is informational and must never close an item."""

    ok: bool = False
    message: str = ""
    writes: list[str] = field(default_factory=list)


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
        if node == "supervisor" and name != "directives.md":
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
        return NodeResult(ok=self.force_ok, message="mock executor", writes=writes)

    def _supervisor(self, ctx: dict[str, Any]) -> NodeResult:
        path = Path(ctx["run_dir"]) / "directives.md"
        current = path.read_text(encoding="utf-8") if path.exists() else (
            "# Directives\n\n## Supervisor state\n\nLast completed tick: none\n"
        )
        if "Last completed tick:" in current:
            updated = re.sub(
                r"Last completed tick:.*",
                "Last completed tick: mock",
                current,
                count=1,
            )
        else:
            updated = current.rstrip() + "\nLast completed tick: mock\n"
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
