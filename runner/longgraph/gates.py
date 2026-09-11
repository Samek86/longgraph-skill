"""Gates run after the executor. Close listens only to these results."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Sequence


@dataclass
class GateResult:
    passed: bool
    command: str
    output: str = ""


Script = Callable[[str, Path], bool]


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
        if not command or command.lower().startswith("n/a"):
            return GateResult(passed=True, command=command, output="skipped")
        if callable(self.script):
            passed = bool(self.script(command, cwd))
        elif isinstance(self.script, list):
            passed = bool(self.script.pop(0)) if self.script else self.default
        else:
            passed = self.default
        return GateResult(passed=passed, command=command, output="mock-gate")
