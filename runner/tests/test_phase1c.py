from __future__ import annotations

from pathlib import Path

from longgraph.hosts import (
    FakeScheduler,
    GrokBotDualTimerHost,
    Host,
    timer_ids_from_ops,
)
from longgraph.nodes import Runner, set_ledger_run_status

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
    host.busy_nodes.add("executor")
    runner.run(steps=1)
    host.busy_nodes.discard("executor")
    assert runner.stopped_reason is None
    assert "GAP-002" not in runner.closed_items

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
