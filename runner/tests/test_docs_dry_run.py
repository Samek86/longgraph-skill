"""Ship-S4: README mock + prompt-only paths stay honest and CI-gated."""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

from longgraph.cli import main
from longgraph.state import parse_run

from tests.support import copy_fixture

_REPO = Path(__file__).resolve().parents[2]
_DOC = _REPO / "docs" / "ship" / "DOCS-DRY-RUN.md"
_RUNNER_README = _REPO / "runner" / "README.md"
_FIXTURE = Path(__file__).resolve().parent / "fixtures" / "add-tests-to-cli"
_ITEM = "GAP-002"


def _fingerprint(root: Path) -> dict[str, str]:
    out: dict[str, str] = {}
    for path in sorted(root.rglob("*")):
        if path.is_file():
            out[path.relative_to(root).as_posix()] = hashlib.sha256(path.read_bytes()).hexdigest()
    return out


def _status(run_dir: Path) -> dict:
    return json.loads((run_dir / "status.json").read_text(encoding="utf-8"))


def test_docs_dry_run_doc_exists() -> None:
    assert _DOC.is_file(), f"missing {_DOC}"
    text = _DOC.read_text(encoding="utf-8")
    assert "--host mock" in text
    assert "--host prompt-only" in text


def test_docs_dry_run_readme_copy_before_mock() -> None:
    """Running mock on tests/fixtures/ mutates the committed tree — README must copy first."""
    readme = _RUNNER_README.read_text(encoding="utf-8")
    assert "docs/ship/DOCS-DRY-RUN.md" in readme
    assert "--host mock" in readme
    assert "--host prompt-only" in readme
    assert "cp -R tests/fixtures/add-tests-to-cli" in readme
    assert "longgraph run --host mock tests/fixtures/add-tests-to-cli" not in readme
    assert "longgraph run --host prompt-only tests/fixtures/add-tests-to-cli" not in readme


def test_docs_dry_run_mock_and_prompt_only(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """Documented CLI paths on a fixture copy: prompt-only emit-only; mock coupled, no close."""
    committed_before = _fingerprint(_FIXTURE)

    prompt_dir = copy_fixture("add-tests-to-cli", tmp_path / "prompt")
    prompt_before = _fingerprint(prompt_dir)
    rc_prompt = main(["run", "--host", "prompt-only", str(prompt_dir)])
    prompt_out = capsys.readouterr().out
    assert rc_prompt == 0
    assert "/loop " in prompt_out
    assert "executor.md" in prompt_out
    assert "supervisor.md" in prompt_out
    lowered = prompt_out.lower()
    for verb in ("wake", "notify", "dispatch"):
        assert verb not in lowered
    assert _fingerprint(prompt_dir) == prompt_before
    assert not (prompt_dir / "workspace" / "tests" / "test_dates.py").exists()
    prompt_state = parse_run(prompt_dir)
    assert prompt_state.run_status == "active"
    assert _ITEM in prompt_state.open_gaps
    assert _ITEM in prompt_state.next_item
    assert "<!-- runner closed GAP-002 -->" not in (prompt_dir / "ledger.md").read_text(
        encoding="utf-8"
    )

    mock_dir = copy_fixture("add-tests-to-cli", tmp_path / "mock")
    rc_mock = main(["run", "--host", "mock", str(mock_dir)])
    mock_out = capsys.readouterr().out
    assert rc_mock == 0
    assert "ledger=" in mock_out
    mock_status = _status(mock_dir)
    mock_state = parse_run(mock_dir)
    assert mock_status.get("status") == "failed"
    assert mock_state.run_status == "active"
    assert _ITEM in mock_state.open_gaps
    assert _ITEM not in (mock_status.get("metadata") or {}).get("closedItems", [])
    assert "<!-- runner closed GAP-002 -->" not in (mock_dir / "ledger.md").read_text(
        encoding="utf-8"
    )
    retries = (mock_status.get("metadata") or {}).get("itemRetries") or {}
    assert retries.get(_ITEM, 0) >= 1
    assert (mock_dir / "workspace").is_dir()
    assert not (mock_dir / "workspace" / "tests" / "test_dates.py").exists()

    assert _fingerprint(_FIXTURE) == committed_before


def test_docs_dry_run_harness_script(tmp_path: Path) -> None:
    script = _REPO / "runner" / "scripts" / "ship-docs-dry-run.sh"
    script_py = _REPO / "runner" / "scripts" / "ship_docs_dry_run.py"
    assert script.is_file()
    assert script_py.is_file()
    committed_before = _fingerprint(_FIXTURE)
    env = os.environ.copy()
    env["TMPDIR"] = str(tmp_path)
    env["TEMP"] = str(tmp_path)
    env["TMP"] = str(tmp_path)
    env["LONGGRAPH_DOCS_DRY_RUN_WORK"] = str(tmp_path)
    runner = str(_REPO / "runner")
    env["PYTHONPATH"] = runner + (os.pathsep + env["PYTHONPATH"] if env.get("PYTHONPATH") else "")
    proc = subprocess.run(
        [sys.executable, str(script_py)],
        cwd=_REPO,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
    blob = proc.stdout + "\n" + proc.stderr
    assert proc.returncode == 0, blob
    assert "--host prompt-only" in proc.stdout
    assert "--host mock" in proc.stdout
    assert "pass/fail: pass" in proc.stdout
    assert _fingerprint(_FIXTURE) == committed_before
