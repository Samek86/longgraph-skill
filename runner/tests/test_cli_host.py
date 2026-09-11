"""H1: CLI Host surface — grok-bot is selectable; DualTimer does not serial-tick peers."""

from __future__ import annotations

from pathlib import Path

import pytest

from longgraph.cli import DEFAULT_HOST, HOST_CHOICES, build_parser, host_for, main
from longgraph.gates import GateRunner
from longgraph.hosts import FakeScheduler, GrokBotDualTimerHost, MockHost, PromptOnlyHost
from longgraph.nodes import Runner

from tests.support import copy_fixture


def _record_invokes(host: GrokBotDualTimerHost) -> list[str]:
    seen: list[str] = []
    inner = host.invoke

    def spy(node: str, prompt: str, ctx: dict) -> object:
        seen.append(node)
        return inner(node, prompt, ctx)

    host.invoke = spy  # type: ignore[method-assign]
    return seen


def test_cli_accepts_grok_bot_host(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    parser = build_parser()
    parsed = parser.parse_args(["run", "--host", "grok-bot", "some-run"])
    assert parsed.host == "grok-bot"
    assert set(HOST_CHOICES) == {"mock", "prompt-only", "grok-bot"}
    assert DEFAULT_HOST == "prompt-only"
    assert parser.parse_args(["run", "some-run"]).host == "prompt-only"
    help_text = parser.format_help()
    assert "grok-bot" in help_text
    assert "prompt-only" in help_text
    assert "mock" in help_text

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

    # Safe default is emit-only — not mock-as-product (no write-set apply).
    emit_dir = copy_fixture("add-tests-to-cli", tmp_path / "emit")
    rc_default = main(["run", str(emit_dir)])
    assert rc_default == 0
    emitted = capsys.readouterr().out
    assert "/loop " in emitted
    assert "executor.md" in emitted
    assert "supervisor.md" in emitted
    assert not (emit_dir / "workspace" / "tests" / "test_dates.py").exists()


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
