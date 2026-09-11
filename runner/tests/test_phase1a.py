from __future__ import annotations

import json
from pathlib import Path

from longgraph.gates import GateRunner
from longgraph.hosts import MockHost, WriteDenied
from longgraph.nodes import Runner, set_ledger_run_status
from longgraph.state import parse_run

from tests.support import copy_fixture


def _status(run_dir: Path) -> dict:
    return json.loads((run_dir / "status.json").read_text(encoding="utf-8"))


def test_mock_roundtrip_add_tests(tmp_path: Path) -> None:
    run_dir = copy_fixture("add-tests-to-cli", tmp_path)
    workspace = tmp_path / "ws"
    runner = Runner(run_dir, gates=GateRunner(default=True), workspace=workspace)
    out = runner.run(steps=1)
    assert (workspace / "tests" / "test_dates.py").is_file()
    assert "GAP-002" in runner.closed_items
    assert out["progress"]["completedRounds"] == 3
    assert out["metadata"]["lastAttempt"]["phase"] == "closed"
    state = parse_run(run_dir)
    assert "GAP-002" not in state.open_gaps
    assert "GAP-002" not in state.next_item
    assert state.run_status in {"exit-ready", "stalled", "closed"}
    assert "supervisor" in runner.host.invocations


def test_forced_gate_fail_then_retry(tmp_path: Path) -> None:
    run_dir = copy_fixture("add-tests-to-cli", tmp_path)
    workspace = tmp_path / "ws"
    verify_fails = {"n": 1}

    def script(command: str, _cwd: Path) -> bool:
        if "test_dates" in command and verify_fails["n"]:
            verify_fails["n"] -= 1
            return False
        return True

    runner = Runner(run_dir, gates=GateRunner(script=script), workspace=workspace)
    runner.run(steps=2)
    status = _status(run_dir)
    assert status["metadata"]["itemRetries"]["GAP-002"] == 1
    assert "GAP-002" in runner.closed_items
    assert status["metadata"]["lastAttempt"]["phase"] == "closed"


def test_supervisor_cannot_write_ledger(tmp_path: Path) -> None:
    run_dir = copy_fixture("add-tests-to-cli", tmp_path)
    runner = Runner(run_dir, workspace=tmp_path / "ws")
    ledger = run_dir / "ledger.md"
    try:
        runner.writer.write("supervisor", ledger, "tampered")
        raised = False
    except WriteDenied:
        raised = True
    assert raised
    assert "tampered" not in ledger.read_text(encoding="utf-8")


def test_executor_cannot_write_directives(tmp_path: Path) -> None:
    run_dir = copy_fixture("add-tests-to-cli", tmp_path)
    runner = Runner(run_dir, workspace=tmp_path / "ws")
    directives = run_dir / "directives.md"
    before = directives.read_text(encoding="utf-8")
    try:
        runner.writer.write("executor", directives, "tampered")
        raised = False
    except WriteDenied:
        raised = True
    assert raised
    assert directives.read_text(encoding="utf-8") == before


def test_done_requires_gate_repass(tmp_path: Path) -> None:
    run_dir = copy_fixture("add-tests-to-cli", tmp_path)
    workspace = tmp_path / "ws"
    allow_verify = {"ok": False}

    def script(command: str, _cwd: Path) -> bool:
        if "test_dates" in command:
            return allow_verify["ok"]
        return True

    host = MockHost(force_ok=True)
    runner = Runner(run_dir, host=host, gates=GateRunner(script=script), workspace=workspace)
    runner.run(steps=1)
    assert host.force_ok is True
    assert "GAP-002" not in runner.closed_items
    assert _status(run_dir)["metadata"]["itemRetries"]["GAP-002"] == 1

    allow_verify["ok"] = True
    runner.run(steps=1)
    assert "GAP-002" in runner.closed_items


def test_pending_audit_blocks_advancement(tmp_path: Path) -> None:
    run_dir = copy_fixture("migrate-blob-storage", tmp_path)
    ledger = run_dir / "ledger.md"
    text = ledger.read_text(encoding="utf-8")
    text = text.replace("Milestone gate: `passed`", "Milestone gate: `pending-audit`")
    ledger.write_text(text, encoding="utf-8")
    workspace = tmp_path / "ws"
    runner = Runner(run_dir, workspace=workspace)
    runner.run(steps=2)
    assert runner.advancement_blocked
    assert runner.stopped_reason == "pending-audit"
    assert not (workspace / "migrations" / "drop_blob.sql").exists()
    assert "executor" not in getattr(runner.host, "invocations", [])


def test_smoke_before_new_item(tmp_path: Path) -> None:
    run_dir = copy_fixture("add-tests-to-cli", tmp_path)
    workspace = tmp_path / "ws"
    order: list[str] = []

    def script(command: str, _cwd: Path) -> bool:
        order.append(command)
        if command == "pytest -q":
            return False
        return True

    runner = Runner(run_dir, gates=GateRunner(script=script), workspace=workspace)
    runner.run(steps=1)
    assert order[0] == "pytest -q"
    assert not (workspace / "tests" / "test_dates.py").exists()
    assert "GAP-002" not in runner.closed_items
    assert _status(run_dir)["metadata"]["itemRetries"]["GAP-002"] == 1


def test_max_rounds_budget(tmp_path: Path) -> None:
    run_dir = copy_fixture("add-tests-to-cli", tmp_path)
    ops = run_dir / "ops.md"
    ops.write_text(ops.read_text(encoding="utf-8").replace("max_rounds: 20", "max_rounds: 2"))
    workspace = tmp_path / "ws"
    runner = Runner(run_dir, workspace=workspace)
    out = runner.run(steps=3)
    assert runner.stopped_reason == "max_rounds"
    assert out["status"] == "paused"
    assert out["status"] != "completed"
    assert not (workspace / "tests" / "test_dates.py").exists()
    assert "GAP-002" not in runner.closed_items


def test_status_completed_implies_ledger_terminal(tmp_path: Path) -> None:
    run_dir = copy_fixture("add-tests-to-cli", tmp_path)
    set_ledger_run_status(run_dir, "closed")
    runner = Runner(run_dir, workspace=tmp_path / "ws")
    out = runner.run(steps=1)
    assert out["status"] == "completed"
    assert parse_run(run_dir).run_status == "closed"
