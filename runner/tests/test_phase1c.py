from __future__ import annotations

from pathlib import Path

from longgraph.hosts import (
    NOOP_MESSAGE,
    FakeScheduler,
    GrokBotDualTimerHost,
    Host,
    timer_ids_from_ops,
)
from longgraph.nodes import Runner, set_ledger_run_status
from longgraph.state import parse_run

from tests.support import copy_fixture

_BANNED_CROSS_WAKE = ("wake", "notify", "dispatch")
_DENY = (
    "`longgraph-dev-continue` is DEV-only and must not appear in product Host paths."
)
_REPO = Path(__file__).resolve().parents[2]


def _ctx(run_dir: Path, workspace: Path) -> dict:
    return {"run_dir": run_dir, "workspace": workspace}


def test_dual_timer_no_cross_wake(tmp_path: Path) -> None:
    run_dir = copy_fixture("add-tests-to-cli", tmp_path)
    workspace = tmp_path / "ws"
    workspace.mkdir()
    ledger = run_dir / "ledger.md"
    directives = run_dir / "directives.md"
    ops = run_dir / "ops.md"
    ledger_before = ledger.read_text(encoding="utf-8")
    directives_before = directives.read_text(encoding="utf-8")
    ops_before = ops.read_text(encoding="utf-8")

    scheduler = FakeScheduler()
    host = GrokBotDualTimerHost(
        scheduler=scheduler,
        exec_interval="10m",
        sup_interval="30m",
        run_dir=run_dir,
        workspace=workspace,
    )

    for cls in (Host, GrokBotDualTimerHost, FakeScheduler):
        for name in dir(cls):
            if name.startswith("_"):
                continue
            lowered = name.lower()
            for token in _BANNED_CROSS_WAKE:
                assert token not in lowered, f"{cls.__name__}.{name}"

    assert FakeScheduler.MIN_INTERVAL_SECONDS == 60
    assert FakeScheduler.RECURRING_EXPIRY_DAYS == 7
    try:
        scheduler.create("too-fast", "30s")
        raised = False
    except ValueError:
        raised = True
    assert raised

    exec_id, sup_id = host.schedule()
    assert exec_id != sup_id
    assert scheduler.get(exec_id) is not None
    assert scheduler.get(sup_id) is not None
    assert {t.task_id for t in scheduler.list()} == {exec_id, sup_id}
    assert host.workspace == workspace
    assert host.run_dir == run_dir

    assert timer_ids_from_ops(ops.read_text(encoding="utf-8")) == {
        "executor": "pending",
        "supervisor": "pending",
    }

    exec_prompt = run_dir / "executor.md"
    result = host.invoke("executor", exec_prompt.read_text(encoding="utf-8"), _ctx(run_dir, workspace))
    assert not result.message.lower().startswith("no-op")
    cells = timer_ids_from_ops(ops.read_text(encoding="utf-8"))
    assert cells["executor"] == exec_id
    assert cells["supervisor"] == "pending"
    assert directives.read_text(encoding="utf-8") == directives_before
    assert scheduler.get(exec_id).prompt == (
        f"Execute the existing runtime node at {run_dir}/executor.md. "
        "Do not load any skill."
    )
    assert "tick=" not in scheduler.get(exec_id).prompt

    sup_prompt = run_dir / "supervisor.md"
    result = host.invoke(
        "supervisor",
        sup_prompt.read_text(encoding="utf-8"),
        _ctx(run_dir, workspace),
    )
    assert not result.message.lower().startswith("no-op")
    cells = timer_ids_from_ops(ops.read_text(encoding="utf-8"))
    assert cells["executor"] == exec_id
    assert cells["supervisor"] == sup_id
    assert ledger.read_text(encoding="utf-8") == ledger_before
    assert "tick=1" in scheduler.get(sup_id).prompt
    assert ("update", sup_id) in scheduler.log
    assert scheduler.get(sup_id).expires_days == 7

    peer_ops = ops.read_text(encoding="utf-8")
    scheduler.mark_busy(exec_id, True)
    overlap = host.invoke(
        "executor",
        exec_prompt.read_text(encoding="utf-8"),
        _ctx(run_dir, workspace),
    )
    assert overlap.message.strip().lower().startswith("no-op")
    assert overlap.writes == []
    assert ops.read_text(encoding="utf-8") == peer_ops
    scheduler.mark_busy(exec_id, False)

    runner = Runner(run_dir, host=host, workspace=workspace)
    runner.run(steps=1)
    assert runner.stopped_reason is None
    assert "GAP-002" not in runner.closed_items
    assert "GAP-002" in parse_run(run_dir).open_gaps
    assert parse_run(run_dir).run_status == "active"

    set_ledger_run_status(run_dir, "closed")
    host.invoke("executor", exec_prompt.read_text(encoding="utf-8"), _ctx(run_dir, workspace))
    assert scheduler.get(exec_id) is None
    assert scheduler.get(sup_id) is not None
    assert ("delete", exec_id) in scheduler.log
    assert ("delete", sup_id) not in scheduler.log
    assert timer_ids_from_ops(ops.read_text(encoding="utf-8"))["supervisor"] == sup_id

    host.invoke("supervisor", sup_prompt.read_text(encoding="utf-8"), _ctx(run_dir, workspace))
    assert scheduler.get(sup_id) is None
    assert scheduler.get(exec_id) is None
    assert ("delete", sup_id) in scheduler.log

    for path in host.reads:
        assert path.suffix == ".md"
        assert run_dir in path.parents or path.parent == run_dir

    assert ops_before != ops.read_text(encoding="utf-8")


def test_docs_distinguish_dev_continue_vs_product_host() -> None:
    readme = (_REPO / "runner" / "README.md").read_text(encoding="utf-8")
    docs_dir = _REPO / "docs" / "runner"
    blob = readme
    if docs_dir.is_dir():
        for path in docs_dir.glob("*.md"):
            blob += "\n" + path.read_text(encoding="utf-8")
    assert _DENY in readme or _DENY in blob
    assert "longgraph-dev-continue" in readme
    assert "DEV-only" in readme
    assert "must not appear in product Host paths" in readme

    product = _REPO / "runner" / "longgraph"
    for py in product.glob("*.py"):
        text = py.read_text(encoding="utf-8")
        assert "longgraph-dev-continue" not in text, py


def _create_ids(scheduler: FakeScheduler) -> list[str]:
    return [tid for action, tid in scheduler.log if action == "create"]


def _delete_ids(scheduler: FakeScheduler) -> list[str]:
    return [tid for action, tid in scheduler.log if action == "delete"]


def test_dual_timer_stays_deleted_after_terminal(tmp_path: Path) -> None:
    run_dir = copy_fixture("add-tests-to-cli", tmp_path)
    workspace = tmp_path / "ws"
    workspace.mkdir()
    scheduler = FakeScheduler()
    host = GrokBotDualTimerHost(
        scheduler=scheduler,
        exec_interval="10m",
        sup_interval="30m",
        run_dir=run_dir,
        workspace=workspace,
    )
    exec_id, sup_id = host.schedule()
    exec_prompt = (run_dir / "executor.md").read_text(encoding="utf-8")
    sup_prompt = (run_dir / "supervisor.md").read_text(encoding="utf-8")
    ctx = _ctx(run_dir, workspace)
    host.invoke("executor", exec_prompt, ctx)
    host.invoke("supervisor", sup_prompt, ctx)

    set_ledger_run_status(run_dir, "closed")
    assert parse_run(run_dir).run_status == "closed"

    first_exec = host.invoke("executor", exec_prompt, ctx)
    first_sup = host.invoke("supervisor", sup_prompt, ctx)
    assert first_exec.message == "terminal"
    assert first_sup.message == "terminal"
    assert first_exec.applied is False
    assert first_sup.applied is False
    assert host.exec_timer_id is None
    assert host.sup_timer_id is None
    assert scheduler.get(exec_id) is None
    assert scheduler.get(sup_id) is None
    assert scheduler.tasks == {}
    creates_after_first = _create_ids(scheduler)
    deletes_after_first = _delete_ids(scheduler)
    assert exec_id in deletes_after_first
    assert sup_id in deletes_after_first

    second_exec = host.invoke("executor", exec_prompt, ctx)
    second_sup = host.invoke("supervisor", sup_prompt, ctx)
    assert second_exec.message == "terminal"
    assert second_sup.message == "terminal"
    assert host.exec_timer_id is None
    assert host.sup_timer_id is None
    assert scheduler.tasks == {}
    # Second terminal fire must not create, then delete, a replacement task.
    assert _create_ids(scheduler) == creates_after_first
    assert _delete_ids(scheduler) == deletes_after_first


def test_dual_timer_scout_noop_when_blocked_on(tmp_path: Path) -> None:
    run_dir = copy_fixture("scout-library-choice", tmp_path)
    workspace = tmp_path / "ws"
    workspace.mkdir()
    findings = run_dir / "findings" / "s3-client.md"
    findings.write_text("# Findings: s3-client\n\n**Status**: incomplete\n", encoding="utf-8")
    scheduler = FakeScheduler()
    host = GrokBotDualTimerHost(
        scheduler=scheduler,
        run_dir=run_dir,
        workspace=workspace,
    )
    host.schedule()
    creates_before = _create_ids(scheduler)
    ctx = {**_ctx(run_dir, workspace), "blocked_on": "findings#s3-client"}

    result = host.invoke("scout", "", ctx)
    assert result.ok is True
    assert result.message.strip().lower().startswith(NOOP_MESSAGE)
    assert result.writes == []
    assert result.applied is False
    assert _create_ids(scheduler) == creates_before
    assert scheduler.tasks  # executor + supervisor remain; scout did not schedule

    runner = Runner(run_dir, host=host, workspace=workspace)
    runner.run(steps=1)
    assert runner.stopped_reason is None
    assert runner.closed_items == []
    assert parse_run(run_dir).blocked_on == "findings#s3-client"
    assert parse_run(run_dir).run_status == "active"
    assert _create_ids(scheduler) == creates_before
