"""Ship-S4 CLI checks used by runner/scripts/ship-docs-dry-run.sh."""

from __future__ import annotations

import hashlib
import json
import os
import platform
import shutil
import subprocess
import sys
import tempfile
from contextlib import redirect_stderr, redirect_stdout
from datetime import datetime, timezone
from io import StringIO
from pathlib import Path

_RUNNER = Path(__file__).resolve().parents[1]
_ROOT = _RUNNER.parent
_FIXTURE = _RUNNER / "tests" / "fixtures" / "add-tests-to-cli"
_ITEM = "GAP-002"


def _fingerprint(root: Path) -> dict[str, str]:
    out: dict[str, str] = {}
    for path in sorted(root.rglob("*")):
        if path.is_file():
            out[path.relative_to(root).as_posix()] = hashlib.sha256(path.read_bytes()).hexdigest()
    return out


def _git_sha() -> str:
    try:
        out = subprocess.check_output(
            ["git", "rev-parse", "HEAD"],
            cwd=_ROOT,
            text=True,
        )
        return out.strip()
    except (OSError, subprocess.CalledProcessError):
        return "unknown"


def _status(run_dir: Path) -> dict:
    return json.loads((run_dir / "status.json").read_text(encoding="utf-8"))


def _run_cli(host: str, run_dir: Path) -> tuple[int, str]:
    """Prefer the installed `longgraph` script (README path); else call main()."""
    exe = shutil.which("longgraph")
    if exe:
        proc = subprocess.run(
            [exe, "run", "--host", host, str(run_dir)],
            cwd=_RUNNER,
            capture_output=True,
            text=True,
            check=False,
        )
        return proc.returncode, proc.stdout + proc.stderr
    if str(_RUNNER) not in sys.path:
        sys.path.insert(0, str(_RUNNER))
    from longgraph.cli import main as cli_main

    buf = StringIO()
    err = StringIO()
    with redirect_stdout(buf), redirect_stderr(err):
        rc = cli_main(["run", "--host", host, str(run_dir)])
    return rc, buf.getvalue() + err.getvalue()


def main() -> int:
    if str(_RUNNER) not in sys.path:
        sys.path.insert(0, str(_RUNNER))
    from longgraph.state import parse_run

    raw_work = (os.environ.get("LONGGRAPH_DOCS_DRY_RUN_WORK") or "").strip()
    work = Path(raw_work).resolve() if raw_work else Path()
    if not raw_work or not work.is_dir():
        tmp = (
            os.environ.get("TMPDIR")
            or os.environ.get("TEMP")
            or os.environ.get("TMP")
            or tempfile.gettempdir()
        )
        work = Path(tmp) / "longgraph-docs-dry-run-inline"
        work.mkdir(parents=True, exist_ok=True)

    committed_before = _fingerprint(_FIXTURE)
    prompt_dir = work / "prompt"
    mock_dir = work / "mock"
    if prompt_dir.exists():
        shutil.rmtree(prompt_dir)
    if mock_dir.exists():
        shutil.rmtree(mock_dir)
    shutil.copytree(_FIXTURE, prompt_dir)
    shutil.copytree(_FIXTURE, mock_dir)
    prompt_before = _fingerprint(prompt_dir)

    started = datetime.now(timezone.utc)
    rc_prompt, emit = _run_cli("prompt-only", prompt_dir)
    prompt_state = parse_run(prompt_dir)
    prompt_ok = (
        rc_prompt == 0
        and "/loop " in emit
        and "executor.md" in emit
        and "supervisor.md" in emit
        and all(verb not in emit.lower() for verb in ("wake", "notify", "dispatch"))
        and _fingerprint(prompt_dir) == prompt_before
        and prompt_state.run_status == "active"
        and _ITEM in prompt_state.open_gaps
        and "<!-- runner closed GAP-002 -->"
        not in (prompt_dir / "ledger.md").read_text(encoding="utf-8")
    )

    rc_mock, mock_out = _run_cli("mock", mock_dir)
    mock_status = _status(mock_dir)
    mock_state = parse_run(mock_dir)
    retries = (mock_status.get("metadata") or {}).get("itemRetries") or {}
    mock_ok = (
        rc_mock == 0
        and "ledger=" in mock_out
        and mock_status.get("status") == "failed"
        and mock_state.run_status == "active"
        and _ITEM in mock_state.open_gaps
        and _ITEM not in (mock_status.get("metadata") or {}).get("closedItems", [])
        and retries.get(_ITEM, 0) >= 1
        and (mock_dir / "workspace").is_dir()
        and not (mock_dir / "workspace" / "tests" / "test_dates.py").exists()
        and "<!-- runner closed GAP-002 -->"
        not in (mock_dir / "ledger.md").read_text(encoding="utf-8")
    )
    committed_ok = _fingerprint(_FIXTURE) == committed_before
    ended = datetime.now(timezone.utc)
    elapsed = (ended - started).total_seconds()
    passed = prompt_ok and mock_ok and committed_ok

    install = os.environ.get(
        "LONGGRAPH_DOCS_DRY_RUN_INSTALL",
        'cd runner && python -m pip install -e ".[dev]"',
    )
    print("## Ship-S4 harness evidence (not an external human sign-off)")
    print()
    print(f"- machine OS: `{platform.platform()}`")
    print(f"- Python version: `{sys.version.split()[0]}`")
    print(f"- install command: `{install}`")
    print(f"- fixture: `runner/tests/fixtures/add-tests-to-cli` (copied under `{work}`)")
    print(f"- `longgraph run --host prompt-only`: {'pass' if prompt_ok else 'FAIL'} (rc={rc_prompt}, emit-only, no close)")
    print(f"- `longgraph run --host mock`: {'pass' if mock_ok else 'FAIL'} (rc={rc_mock}, fail-closed, no close)")
    print(f"- committed fixtures unchanged: {'pass' if committed_ok else 'FAIL'}")
    print(f"- pass/fail: {'pass' if passed else 'FAIL'}")
    print(
        f"- time: {elapsed:.1f}s (UTC {started.strftime('%Y-%m-%dT%H:%M:%SZ')} -> "
        f"{ended.strftime('%Y-%m-%dT%H:%M:%SZ')})"
    )
    print(f"- SHA: `{_git_sha()}`")
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
