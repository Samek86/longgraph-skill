"""H1: CLI Host surface — default is DualTimer continuous; prompt-only is fallback."""

from __future__ import annotations

from pathlib import Path

import pytest

from longgraph.cli import DEFAULT_HOST, HOST_CHOICES, build_parser, host_for, main
from longgraph.gates import GateRunner
from longgraph.hosts import (
    FakeScheduler,
    GrokBotDualTimerHost,
    MockHost,
    PromptOnlyHost,
    ScheduleError,
)
from longgraph.nodes import Runner, set_ledger_run_status
from longgraph.state import parse_run

from tests.support import copy_fixture


def _record_invokes(host: GrokBotDualTimerHost) -> list[str]:
    seen: list[str] = []
    inner = host.invoke

    def spy(node: str, prompt: str, ctx: dict) -> object:
        seen.append(node)
        return inner(node, prompt, ctx)

    host.invoke = spy  # type: ignore[method-assign]
    return seen


def _ctx(run_dir: Path, workspace: Path) -> dict:
    return {"run_dir": run_dir, "workspace": workspace}


def test_cli_default_host_is_continuous_dual_timer(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """(a) Default host is continuous DualTimer; (e) prompt-only remains non-default."""
    parser = build_parser()
    parsed = parser.parse_args(["run", "--host", "grok-bot", "some-run"])
    assert parsed.host == "grok-bot"
    assert set(HOST_CHOICES) == {"mock", "prompt-only", "grok-bot"}
    assert DEFAULT_HOST == "grok-bot"
    assert parser.parse_args(["run", "some-run"]).host == "grok-bot"
    help_text = parser.format_help()
    assert "grok-bot" in help_text
    assert "prompt-only" in help_text
    assert "mock" in help_text
    assert "product default" in help_text.lower() or "DualTimer continuous" in help_text
    assert "fallback" in help_text.lower()

    with pytest.raises(SystemExit):
        parser.parse_args(["run", "--host", "api-host", "some-run"])

    assert isinstance(host_for("grok-bot", tmp_path), GrokBotDualTimerHost)
    assert isinstance(host_for("prompt-only", tmp_path), PromptOnlyHost)
    assert isinstance(host_for("mock", tmp_path), MockHost)
    assert host_for("grok-bot", tmp_path).owns_timers is True
    assert host_for("mock", tmp_path).owns_timers is False

    run_dir = copy_fixture("add-tests-to-cli", tmp_path)
    rc = main(["run", "--host", "grok-bot", str(run_dir)])
    assert rc == 0
    out = capsys.readouterr().out
    assert "scheduled executor=" in out
    assert "supervisor=" in out
    assert "/loop " not in out

    # Omitting --host is DualTimer continuous — not emit-and-exit, not mock-as-product.
    default_dir = copy_fixture("add-tests-to-cli", tmp_path / "default")
    rc_default = main(["run", str(default_dir)])
    assert rc_default == 0
    default_out = capsys.readouterr().out
    assert "scheduled executor=" in default_out
    assert "/loop " not in default_out
    assert not (default_dir / "workspace" / "tests" / "test_dates.py").exists()
    assert parse_run(default_dir).run_status == "active"

    # (e) prompt-only remains available as an explicit non-default fallback.
    emit_dir = copy_fixture("add-tests-to-cli", tmp_path / "emit")
    rc_emit = main(["run", "--host", "prompt-only", str(emit_dir)])
    assert rc_emit == 0
    emitted = capsys.readouterr().out
    assert "/loop " in emitted
    assert "executor.md" in emitted
    assert "supervisor.md" in emitted
    assert not (emit_dir / "workspace" / "tests" / "test_dates.py").exists()


def test_non_terminal_tick_reseeds_both_timers(tmp_path: Path) -> None:
    """(b) After a non-terminal tick, both executor and supervisor timers are reseeded."""
    run_dir = copy_fixture("add-tests-to-cli", tmp_path)
    workspace = tmp_path / "ws"
    workspace.mkdir()
    scheduler = FakeScheduler()
    host = GrokBotDualTimerHost(
        scheduler=scheduler,
        run_dir=run_dir,
        workspace=workspace,
    )
    exec_id, sup_id = host.schedule()
    assert scheduler.get(exec_id) is not None
    assert scheduler.get(sup_id) is not None

    # Drop both tasks so a tick must recreate them.
    scheduler.delete(exec_id)
    scheduler.delete(sup_id)
    host.exec_timer_id = None
    host.sup_timer_id = None
    assert scheduler.tasks == {}

    ctx = _ctx(run_dir, workspace)
    result = host.invoke(
        "executor",
        (run_dir / "executor.md").read_text(encoding="utf-8"),
        ctx,
    )
    assert result.message == "executor tick"
    assert result.applied is False
    assert len(scheduler.tasks) == 2
    assert host.exec_timer_id is not None
    assert host.sup_timer_id is not None
    assert scheduler.get(host.exec_timer_id) is not None
    assert scheduler.get(host.sup_timer_id) is not None
    # Own ops cell only — peer Timers cell stays pending (no peer wake / peer write).
    from longgraph.hosts import timer_ids_from_ops

    cells = timer_ids_from_ops((run_dir / "ops.md").read_text(encoding="utf-8"))
    assert cells["executor"] == host.exec_timer_id
    assert cells["supervisor"] == "pending"


def test_schedule_failure_fails_closed(tmp_path: Path) -> None:
    """(c) Schedule / reseed failure is fail-closed — hard error, never silent idle."""
    run_dir = copy_fixture("add-tests-to-cli", tmp_path)
    workspace = tmp_path / "ws"
    workspace.mkdir()
    scheduler = FakeScheduler()
    host = GrokBotDualTimerHost(
        scheduler=scheduler,
        run_dir=run_dir,
        workspace=workspace,
    )
    scheduler.fail_next_create = True
    with pytest.raises(ScheduleError, match="fail-closed"):
        host.schedule()
    assert scheduler.tasks == {}

    # Reseed path: schedule once, delete a timer, refuse the next create on invoke.
    host2_sched = FakeScheduler()
    host2 = GrokBotDualTimerHost(
        scheduler=host2_sched,
        run_dir=run_dir,
        workspace=workspace,
    )
    exec_id, _sup_id = host2.schedule()
    host2_sched.delete(exec_id)
    host2.exec_timer_id = None
    host2_sched.fail_next_create = True
    with pytest.raises(ScheduleError):
        host2.invoke(
            "supervisor",
            (run_dir / "supervisor.md").read_text(encoding="utf-8"),
            _ctx(run_dir, workspace),
        )

    bad = copy_fixture("add-tests-to-cli", tmp_path / "cli-fail")

    class BoomScheduler(FakeScheduler):
        def create(self, prompt: str, interval: str, task_id: str | None = None) -> str:
            raise ScheduleError("injected schedule refusal")

    boom = GrokBotDualTimerHost(scheduler=BoomScheduler(), run_dir=bad)
    with pytest.raises(ScheduleError, match="injected"):
        boom.schedule()


def test_cli_schedule_failure_returns_nonzero(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """CLI DualTimer path exits non-zero when schedule raises (fail-closed)."""
    run_dir = copy_fixture("add-tests-to-cli", tmp_path)

    def boom_schedule(self: GrokBotDualTimerHost, ctx=None):  # noqa: ANN001
        raise ScheduleError("cli schedule refused")

    monkeypatch.setattr(GrokBotDualTimerHost, "schedule", boom_schedule)
    rc = main(["run", "--host", "grok-bot", str(run_dir)])
    assert rc == 1


def test_terminal_tick_does_not_reseed(tmp_path: Path) -> None:
    """(d) Terminal ledger stops reseeding — no create after delete."""
    run_dir = copy_fixture("add-tests-to-cli", tmp_path)
    workspace = tmp_path / "ws"
    workspace.mkdir()
    scheduler = FakeScheduler()
    host = GrokBotDualTimerHost(
        scheduler=scheduler,
        run_dir=run_dir,
        workspace=workspace,
    )
    exec_id, sup_id = host.schedule()
    ctx = _ctx(run_dir, workspace)
    host.invoke("executor", (run_dir / "executor.md").read_text(encoding="utf-8"), ctx)
    host.invoke("supervisor", (run_dir / "supervisor.md").read_text(encoding="utf-8"), ctx)

    set_ledger_run_status(run_dir, "closed")
    creates_before = [tid for action, tid in scheduler.log if action == "create"]

    terminal_exec = host.invoke(
        "executor",
        (run_dir / "executor.md").read_text(encoding="utf-8"),
        ctx,
    )
    terminal_sup = host.invoke(
        "supervisor",
        (run_dir / "supervisor.md").read_text(encoding="utf-8"),
        ctx,
    )
    assert terminal_exec.message == "terminal"
    assert terminal_sup.message == "terminal"
    assert scheduler.tasks == {}
    assert host.exec_timer_id is None
    assert host.sup_timer_id is None
    creates_after = [tid for action, tid in scheduler.log if action == "create"]
    assert creates_after == creates_before
    assert scheduler.get(exec_id) is None
    assert scheduler.get(sup_id) is None


def test_grok_bot_host_does_not_serial_tick_peers(tmp_path: Path) -> None:
    run_dir = copy_fixture("add-tests-to-cli", tmp_path)
    workspace = tmp_path / "ws"
    workspace.mkdir()
    scheduler = FakeScheduler()
    host = GrokBotDualTimerHost(
        scheduler=scheduler,
        run_dir=run_dir,
        workspace=workspace,
    )
    host.schedule()
    seen = _record_invokes(host)
    runner = Runner(
        run_dir,
        host=host,
        gates=GateRunner(default=True),
        workspace=workspace,
    )
    runner.run(steps=2)
    assert "executor" in seen
    assert "supervisor" not in seen
    assert "scout" not in seen
    assert runner.closed_items == []

    mock_dir = copy_fixture("add-tests-to-cli", tmp_path / "mock")
    mock_ws = tmp_path / "mock-ws"
    mock_host = MockHost()
    mock_runner = Runner(
        mock_dir,
        host=mock_host,
        gates=GateRunner(default=True),
        workspace=mock_ws,
    )
    mock_runner.run(steps=1)
    assert "executor" in mock_host.invocations
    assert "supervisor" in mock_host.invocations

    scout_dir = copy_fixture("scout-library-choice", tmp_path / "scout")
    findings = scout_dir / "findings" / "s3-client.md"
    findings.write_text("# Findings: s3-client\n\n**Status**: incomplete\n", encoding="utf-8")
    scout_ws = tmp_path / "scout-ws"
    scout_ws.mkdir()
    scout_host = GrokBotDualTimerHost(
        scheduler=FakeScheduler(),
        run_dir=scout_dir,
        workspace=scout_ws,
    )
    scout_host.schedule()
    scout_seen = _record_invokes(scout_host)
    scout_runner = Runner(scout_dir, host=scout_host, workspace=scout_ws)
    scout_runner.run(steps=1)
    assert "scout" not in scout_seen
    assert scout_runner.closed_items == []
