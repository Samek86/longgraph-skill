"""Gates run after an applied executor write-set. Close needs a green, non-skipped result."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Sequence


@dataclass
class GateResult:
    passed: bool
    command: str
    output: str = ""
    skipped: bool = False


Script = Callable[[str, Path], bool]


def classify_verify(command: str | None) -> str:
    """Return `empty`, `n/a`, or `run` for a Current-slice Verify field."""
    stripped = (command or "").strip()
    if not stripped:
        return "empty"
    if stripped.lower().startswith("n/a"):
        return "n/a"
    return "run"


class GateRunner:
    """Injectable gate runner. Default is pass (MockHost MVP)."""

    def __init__(
        self,
        script: Script | Sequence[bool] | None = None,
        default: bool = True,
    ):
        self.script = list(script) if isinstance(script, Sequence) and not callable(script) else script
        self.default = default
        self.calls: list[str] = []

    def run(self, command: str, cwd: Path | None = None) -> GateResult:
        cwd = Path(cwd or ".")
        self.calls.append(command)
        kind = classify_verify(command)
        if kind == "empty":
            return GateResult(passed=False, command=command, output="empty-verify")
        if kind == "n/a":
            return GateResult(passed=False, command=command, output="skipped", skipped=True)
        if callable(self.script):
            passed = bool(self.script(command, cwd))
        elif isinstance(self.script, list):
            passed = bool(self.script.pop(0)) if self.script else self.default
        else:
            passed = self.default
        return GateResult(passed=passed, command=command, output="mock-gate")
