"""C1–C4: close retires the scoreboard; blocked-on / empty / n/a / owner-blocked / emit-only."""

from __future__ import annotations

import json
from pathlib import Path

from longgraph.gates import GateRunner, classify_verify
from longgraph.hosts import FakeScheduler, GrokBotDualTimerHost, MockHost, PromptOnlyHost
from longgraph.nodes import Runner
from longgraph.state import findings_relpath, parse_run, safe_findings_ident

from tests.support import copy_fixture


def _status(run_dir: Path) -> dict:
    return json.loads((run_dir / "status.json").read_text(encoding="utf-8"))


def test_close_retires_scoreboard(tmp_path: Path) -> None:
    run_dir = copy_fixture("add-tests-to-cli", tmp_path)
    workspace = tmp_path / "ws"
    runner = Runner(run_dir, gates=GateRunner(default=True), workspace=workspace)
    out = runner.run(steps=3)

    assert runner.closed_items == ["GAP-002"]
    assert (out.get("metadata") or {}).get("closedItems") == ["GAP-002"]
    assert out["progress"]["completedRounds"] == 3
    assert out["progress"]["completedItems"] == 3
    assert out["status"] == "completed"

    state = parse_run(run_dir)
    assert "GAP-002" not in state.open_gaps
    assert "GAP-002" not in state.next_item
    assert state.run_status in {"exit-ready", "stalled", "closed"}
    ledger = (run_dir / "ledger.md").read_text(encoding="utf-8")
    assert "<!-- runner closed GAP-002 -->" in ledger
    assert ledger.count("<!-- runner closed GAP-002 -->") == 1


def test_blocked_on_skips_executor_until_findings(tmp_path: Path) -> None:
    run_dir = copy_fixture("scout-library-choice", tmp_path)
    workspace = tmp_path / "ws"
    findings = run_dir / "findings" / "s3-client.md"
    findings.write_text("# Findings: s3-client\n\n**Status**: incomplete\n", encoding="utf-8")
    host = MockHost()
    runner = Runner(run_dir, host=host, gates=GateRunner(default=True), workspace=workspace)

    runner.run(steps=1)
    assert "executor" not in host.invocations
    assert "scout" in host.invocations
    assert not (workspace / "shutterlog" / "storage.py").exists()
    assert runner.closed_items == []
    assert parse_run(run_dir).run_status == "active"
    assert parse_run(run_dir).blocked_on == "findings#s3-client"

    findings.unlink()
    host.invocations.clear()
    runner.run(steps=1)
    assert "executor" not in host.invocations
    assert "scout" in host.invocations
    assert findings.is_file()
    assert not (workspace / "shutterlog" / "storage.py").exists()
    assert runner.closed_items == []

    host.invocations.clear()
    runner.run(steps=1)
    assert "executor" in host.invocations
    assert (workspace / "shutterlog" / "storage.py").is_file()


def test_blocked_on_rejects_findings_path_escape(tmp_path: Path) -> None:
    """A3 / §1.3: findings#../decoy must not resolve outside findings/ or close."""
    assert safe_findings_ident("../decoy") is None
    assert findings_relpath("findings#../decoy") is None
    assert findings_relpath("findings#s3-client") == "findings/s3-client.md"

    run_dir = copy_fixture("scout-library-choice", tmp_path)
    workspace = tmp_path / "ws"
    decoy = run_dir / "decoy.md"
    decoy.write_text("# decoy\n\n**Status**: complete\n", encoding="utf-8")
    findings = run_dir / "findings" / "s3-client.md"
    findings.write_text("# Findings: s3-client\n\n**Status**: incomplete\n", encoding="utf-8")
    ledger = run_dir / "ledger.md"
    ledger.write_text(
        ledger.read_text(encoding="utf-8").replace(
            "blocked-on: findings#s3-client",
            "blocked-on: findings#../decoy",
        ),
        encoding="utf-8",
    )
    state = parse_run(run_dir)
    assert state.blocked_on == "findings#../decoy"
    assert state.findings_path is None

    host = MockHost()
    runner = Runner(run_dir, host=host, gates=GateRunner(default=True), workspace=workspace)
    runner.run(steps=1)
    assert "executor" not in host.invocations
    assert not (workspace / "shutterlog" / "storage.py").exists()
    assert runner.closed_items == []
    assert parse_run(run_dir).run_status == "active"


def test_empty_verify_fails_no_close(tmp_path: Path) -> None:
    run_dir = copy_fixture("add-tests-to-cli", tmp_path)
    ledger = run_dir / "ledger.md"
    text = ledger.read_text(encoding="utf-8")
    ledger.write_text(
        text.replace("Verify: pytest tests/test_dates.py -q", "Verify:"),
        encoding="utf-8",
    )
    workspace = tmp_path / "ws"
    forged = GateRunner(script=lambda _command, _cwd: True)
    empty = forged.run("", workspace)
    assert empty.passed is False
    assert empty.skipped is False
    assert classify_verify("") == "empty"
    assert classify_verify("   ") == "empty"

    runner = Runner(run_dir, gates=GateRunner(script=lambda _c, _p: True), workspace=workspace)
    runner.run(steps=1)
    assert "GAP-002" not in runner.closed_items
    assert not (workspace / "tests" / "test_dates.py").exists()
    assert _status(run_dir)["metadata"]["itemRetries"]["GAP-002"] == 1
    assert parse_run(run_dir).run_status == "active"
    assert "GAP-002" in parse_run(run_dir).open_gaps


def test_na_verify_skips_gate_and_close(tmp_path: Path) -> None:
    run_dir = copy_fixture("add-tests-to-cli", tmp_path)
    ledger = run_dir / "ledger.md"
    text = ledger.read_text(encoding="utf-8")
    ledger.write_text(
        text.replace(
            "Verify: pytest tests/test_dates.py -q",
            "Verify: n/a — not gateable this round",
        ),
        encoding="utf-8",
    )
    workspace = tmp_path / "ws"
    script_calls: list[str] = []

    def script(command: str, _cwd: Path) -> bool:
        script_calls.append(command)
        return True

    gates = GateRunner(script=script)
    skipped = gates.run("n/a — owner-blocked on OB-001", workspace)
    assert skipped.skipped is True
    assert skipped.passed is False
    assert script_calls == []
    assert classify_verify("n/a — owner-blocked on OB-001") == "n/a"

    runner = Runner(run_dir, gates=gates, workspace=workspace)
    runner.run(steps=2)
    assert script_calls == []
    assert "GAP-002" not in runner.closed_items
    assert not (workspace / "tests" / "test_dates.py").exists()
    assert parse_run(run_dir).run_status == "active"
    assert "GAP-002" in parse_run(run_dir).open_gaps
    assert "GAP-002" not in (_status(run_dir).get("metadata") or {}).get("itemRetries", {})


def test_owner_blocked_skips_write_set_and_close(tmp_path: Path) -> None:
    run_dir = copy_fixture("migrate-blob-storage", tmp_path)
    ledger = run_dir / "ledger.md"
    text = ledger.read_text(encoding="utf-8")
    ledger.write_text(
        text.replace("Verify: n/a — owner-blocked on OB-001", "Verify: true"),
        encoding="utf-8",
    )
    workspace = tmp_path / "ws"
    runner = Runner(run_dir, gates=GateRunner(default=True), workspace=workspace)
    runner.run(steps=2)
    assert not (workspace / "migrations" / "drop_blob.sql").exists()
    assert runner.closed_items == []
    state = parse_run(run_dir)
    assert state.owner_blocked == ["OB-001"]
    assert state.run_status == "active"
    assert state.next_item.startswith("M3")


def test_prompt_only_host_never_closes(tmp_path: Path) -> None:
    run_dir = copy_fixture("add-tests-to-cli", tmp_path)
    workspace = tmp_path / "ws"
    host = PromptOnlyHost(run_dir=run_dir)
    runner = Runner(
        run_dir,
        host=host,
        gates=GateRunner(default=True),
        workspace=workspace,
    )
    runner.run(steps=2)
    assert runner.closed_items == []
    assert not (workspace / "tests" / "test_dates.py").exists()
    state = parse_run(run_dir)
    assert state.run_status == "active"
    assert "GAP-002" in state.open_gaps
    assert "GAP-002" in state.next_item


def test_dual_timer_host_never_closes(tmp_path: Path) -> None:
    run_dir = copy_fixture("add-tests-to-cli", tmp_path)
    workspace = tmp_path / "ws"
    workspace.mkdir()
    host = GrokBotDualTimerHost(
        scheduler=FakeScheduler(),
        run_dir=run_dir,
        workspace=workspace,
    )
    host.schedule()
    assert not host.busy_nodes
    runner = Runner(
        run_dir,
        host=host,
        gates=GateRunner(default=True),
        workspace=workspace,
    )
    runner.run(steps=2)
    assert runner.closed_items == []
    assert "GAP-002" in parse_run(run_dir).open_gaps
    assert parse_run(run_dir).run_status == "active"
    assert not (workspace / "tests" / "test_dates.py").exists()
