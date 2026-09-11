"""Ship-S3: negative battery doc maps to real pytest; Critical regressions."""

from __future__ import annotations

import re
from pathlib import Path

from longgraph.cli import main
from longgraph.gates import GateRunner
from longgraph.hosts import FakeScheduler, GrokBotDualTimerHost, MockHost
from longgraph.nodes import Runner, set_ledger_run_status
from longgraph.state import findings_relpath, parse_run, safe_findings_ident

from tests.support import copy_fixture

_REPO = Path(__file__).resolve().parents[2]
_TESTS = Path(__file__).resolve().parent
_BATTERY_MD = _REPO / "docs" / "ship" / "NEGATIVE-BATTERY.md"
_SCENARIO_ROW = re.compile(r"^\|\s*(S3-\d+)\s*\|")
_TEST_NAME = re.compile(r"`(test_[A-Za-z0-9_]+)`")
_DEF_TEST = re.compile(r"^def (test_[A-Za-z0-9_]+)\s*\(", re.M)
_REQUIRED_IDS = tuple(f"S3-{i:02d}" for i in range(1, 9))
_CRITICAL_REMAINING = re.compile(
    r"Critical(?: count)?(?: remaining)?(?: for battery scenarios)?\s*[:=]\s*\**0\**",
    re.I,
)


def parse_battery_scenario_tests(text: str) -> dict[str, list[str]]:
    """Map S3-xx ids to backtick test names from the battery table."""
    mapped: dict[str, list[str]] = {}
    for line in text.splitlines():
        match = _SCENARIO_ROW.match(line)
        if not match:
            continue
        sid = match.group(1)
        names = _TEST_NAME.findall(line)
        if names:
            mapped[sid] = names
    return mapped


def collect_defined_test_names(tests_dir: Path = _TESTS) -> set[str]:
    """Every `def test_*` under runner/tests/ (file scan, not a filtered session)."""
    names: set[str] = set()
    for path in sorted(tests_dir.glob("test_*.py")):
        names.update(_DEF_TEST.findall(path.read_text(encoding="utf-8")))
    return names


def test_negative_battery_doc_exists() -> None:
    assert _BATTERY_MD.is_file(), f"missing {_BATTERY_MD}"
    text = _BATTERY_MD.read_text(encoding="utf-8")
    assert text.strip(), f"{_BATTERY_MD} is empty"
    assert _CRITICAL_REMAINING.search(text), (
        f"{_BATTERY_MD} must state Critical remaining = 0 for battery scenarios"
    )

    mapped = parse_battery_scenario_tests(text)
    missing_ids = [sid for sid in _REQUIRED_IDS if sid not in mapped]
    assert not missing_ids, f"NEGATIVE-BATTERY.md missing scenario ids: {missing_ids}"

    required = {name for names in mapped.values() for name in names}
    assert required, "NEGATIVE-BATTERY.md table has no backtick test names"

    collected = collect_defined_test_names()
    missing = sorted(required - collected)
    assert not missing, (
        "NEGATIVE-BATTERY.md names missing from the collected suite: "
        + ", ".join(missing)
    )


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


def _create_ids(scheduler: FakeScheduler) -> list[str]:
    return [tid for action, tid in scheduler.log if action == "create"]


def test_dual_timer_schedule_on_terminal_creates_zero_tasks(tmp_path: Path) -> None:
    """A17 / §1.5: schedule() on a terminal ledger must not create or recreate."""
    run_dir = copy_fixture("add-tests-to-cli", tmp_path)
    workspace = tmp_path / "ws"
    workspace.mkdir()
    set_ledger_run_status(run_dir, "closed")
    assert parse_run(run_dir).run_status == "closed"

    scheduler = FakeScheduler()
    host = GrokBotDualTimerHost(
        scheduler=scheduler,
        exec_interval="10m",
        sup_interval="30m",
        run_dir=run_dir,
        workspace=workspace,
    )
    exec_id, sup_id = host.schedule()
    assert exec_id == ""
    assert sup_id == ""
    assert scheduler.tasks == {}
    assert _create_ids(scheduler) == []
    assert host.exec_timer_id is None
    assert host.sup_timer_id is None

    ops_before = (run_dir / "ops.md").read_text(encoding="utf-8")
    rc = main(["run", "--host", "grok-bot", str(run_dir)])
    assert rc == 0
    assert (run_dir / "ops.md").read_text(encoding="utf-8") == ops_before
    assert parse_run(run_dir).run_status == "closed"

    active = copy_fixture("add-tests-to-cli", tmp_path / "active")
    active_ws = tmp_path / "active-ws"
    active_ws.mkdir()
    live = FakeScheduler()
    live_host = GrokBotDualTimerHost(
        scheduler=live,
        run_dir=active,
        workspace=active_ws,
    )
    first_exec, first_sup = live_host.schedule()
    assert live.tasks
    ctx = {"run_dir": active, "workspace": active_ws}
    live_host.invoke("executor", (active / "executor.md").read_text(encoding="utf-8"), ctx)
    live_host.invoke("supervisor", (active / "supervisor.md").read_text(encoding="utf-8"), ctx)
    set_ledger_run_status(active, "closed")
    live_host.invoke("executor", (active / "executor.md").read_text(encoding="utf-8"), ctx)
    live_host.invoke("supervisor", (active / "supervisor.md").read_text(encoding="utf-8"), ctx)
    assert live.tasks == {}
    creates_after_delete = _create_ids(live)
    again_exec, again_sup = live_host.schedule()
    assert again_exec == ""
    assert again_sup == ""
    assert live.tasks == {}
    assert _create_ids(live) == creates_after_delete
    _ = (first_exec, first_sup)
