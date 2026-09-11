"""H0b: product GateRunner is a fail-closed subprocess, not a forged default-pass."""

from __future__ import annotations

import json
from pathlib import Path

from longgraph.cli import main
from longgraph.gates import GateRunner
from longgraph.nodes import Runner
from longgraph.state import parse_run

from tests.support import copy_fixture

_ITEM = "GAP-002"
_VERIFY = "pytest tests/test_dates.py -q"
_SMOKE = "pytest -q"


def _status(run_dir: Path) -> dict:
    return json.loads((run_dir / "status.json").read_text(encoding="utf-8"))


def _product_run(tmp_path: Path, *, verify: str, smoke: str = "true") -> Path:
    run_dir = copy_fixture("add-tests-to-cli", tmp_path)
    ledger = run_dir / "ledger.md"
    ledger.write_text(
        ledger.read_text(encoding="utf-8").replace(f"Verify: {_VERIFY}", f"Verify: {verify}"),
        encoding="utf-8",
    )
    ops = run_dir / "ops.md"
    ops.write_text(
        ops.read_text(encoding="utf-8").replace(f"smoke: {_SMOKE}", f"smoke: {smoke}"),
        encoding="utf-8",
    )
    return run_dir


def test_subprocess_verify_red_blocks_close(tmp_path: Path) -> None:
    workspace = tmp_path / "ws"
    workspace.mkdir()
    product = GateRunner()
    assert product.script is None
    assert product.default is not True
    red = product.run("false", workspace)
    assert red.passed is False
    assert red.skipped is False

    run_dir = _product_run(tmp_path, verify="false")
    runner = Runner(run_dir, workspace=workspace)
    runner.run(steps=1)
    assert (workspace / "tests" / "test_dates.py").is_file()
    assert _ITEM not in runner.closed_items
    assert _ITEM not in (_status(run_dir).get("metadata") or {}).get("closedItems", [])
    assert _status(run_dir)["metadata"]["itemRetries"][_ITEM] == 1
    assert parse_run(run_dir).run_status == "active"
    assert _ITEM in parse_run(run_dir).open_gaps


def test_subprocess_verify_green_allows_close(tmp_path: Path) -> None:
    workspace = tmp_path / "ws"
    workspace.mkdir()
    product = GateRunner()
    green = product.run("true", workspace)
    assert green.passed is True
    assert green.skipped is False

    run_dir = _product_run(tmp_path, verify="true")
    runner = Runner(run_dir, workspace=workspace)
    out = runner.run(steps=1)
    assert (workspace / "tests" / "test_dates.py").is_file()
    assert _ITEM in runner.closed_items
    assert _ITEM in (out.get("metadata") or {}).get("closedItems", [])
    assert out["metadata"]["lastAttempt"]["phase"] == "closed"
    assert _ITEM not in parse_run(run_dir).open_gaps


def test_cli_default_gate_is_fail_closed(tmp_path: Path) -> None:
    product = GateRunner()
    assert product.script is None
    assert product.default is not True
    forged_would_pass = GateRunner(default=True).run("false", tmp_path)
    assert forged_would_pass.passed is True
    assert product.run("false", tmp_path).passed is False

    run_dir = _product_run(tmp_path, verify="false")
    rc = main(["run", str(run_dir)])
    assert rc == 0
    status = _status(run_dir)
    assert _ITEM not in (status.get("metadata") or {}).get("closedItems", [])
    assert "<!-- runner closed GAP-002 -->" not in (run_dir / "ledger.md").read_text(
        encoding="utf-8"
    )
    assert parse_run(run_dir).run_status == "active"
    assert _ITEM in parse_run(run_dir).open_gaps
    assert status["status"] == "failed"
    assert status["metadata"]["itemRetries"][_ITEM] >= 1
