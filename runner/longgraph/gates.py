"""Gates run after an applied executor write-set. Close needs a green, non-skipped result."""

from __future__ import annotations

import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Sequence

# Unix ``true`` / ``false`` are not cmd.exe builtins. Keep the documented
# fixture tokens portable without going through ``/bin/sh``.
_PORTABLE_TRUE = (sys.executable, "-c", "raise SystemExit(0)")
_PORTABLE_FALSE = (sys.executable, "-c", "raise SystemExit(1)")


def portable_gate_argv(command: str) -> tuple[str, ...] | None:
    """Exact ``true`` / ``false`` tokens → argv that does not need a POSIX shell."""
    token = (command or "").strip()
    if token == "true":
        return _PORTABLE_TRUE
    if token == "false":
        return _PORTABLE_FALSE
    return None


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
    """Fail-closed gate. Product path execs Verify/smoke via subprocess.

    Tests may inject `script=` or an explicit `default=` bool. Omitting both
    (CLI / `longgraph run`) never forges `passed=True`.
    """

    def __init__(
        self,
        script: Script | Sequence[bool] | None = None,
        default: bool | None = None,
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
            return GateResult(passed=passed, command=command, output="mock-gate")
        if isinstance(self.script, list):
            if self.script:
                passed = bool(self.script.pop(0))
            elif self.default is not None:
                passed = bool(self.default)
            else:
                passed = False
            return GateResult(passed=passed, command=command, output="mock-gate")
        if self.default is not None:
            return GateResult(passed=bool(self.default), command=command, output="mock-gate")
        return self._run_subprocess(command, cwd)

    def _run_subprocess(self, command: str, cwd: Path) -> GateResult:
        """Exec `command` with cwd = workspace (or the caller-supplied root)."""
        argv = portable_gate_argv(command)
        try:
            if argv is not None:
                completed = subprocess.run(
                    argv,
                    cwd=cwd,
                    capture_output=True,
                    text=True,
                )
            else:
                completed = subprocess.run(
                    command,
                    shell=True,
                    cwd=cwd,
                    capture_output=True,
                    text=True,
                )
        except OSError as exc:
            return GateResult(passed=False, command=command, output=str(exc))
        output = "".join(part for part in (completed.stdout, completed.stderr) if part)
        return GateResult(
            passed=completed.returncode == 0,
            command=command,
            output=output,
        )
