"""CLI: longgraph run|status|stop <run_dir>."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .hosts import (
    TERMINAL_LEDGER,
    GrokBotDualTimerHost,
    Host,
    MockHost,
    PromptOnlyHost,
    ScheduleError,
)
from .nodes import Runner
from .state import parse_run

HOST_CHOICES = ("mock", "prompt-only", "grok-bot")
# Product default: continuous DualTimer. prompt-only is an explicit degraded fallback.
DEFAULT_HOST = "grok-bot"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="longgraph",
        description=(
            "Compiled-run runner. Default --host is grok-bot (DualTimer continuous path). "
            "prompt-only is an explicit emit-and-exit fallback when the host cannot "
            "schedule timers or cannot shell. mock is the coupled test loop, not the "
            "product path."
        ),
    )
    sub = parser.add_subparsers(dest="cmd", required=True)
    for name in ("run", "status", "stop"):
        item = sub.add_parser(name)
        item.add_argument("run_dir")
        if name == "run":
            item.add_argument(
                "--host",
                choices=HOST_CHOICES,
                default=DEFAULT_HOST,
                help=(
                    "grok-bot (product default): DualTimer continuous host — independent "
                    "timers, no serial peer tick, reseed until terminal. "
                    "prompt-only (fallback): print dual /loop paste blocks and exit. "
                    "mock: coupled executor→supervisor→scout test loop only."
                ),
            )
    return parser


def host_for(name: str, run_dir: Path) -> Host:
    """Construct the Host for a CLI --host value."""
    if name == "mock":
        return MockHost()
    if name == "prompt-only":
        return PromptOnlyHost(run_dir=run_dir)
    if name == "grok-bot":
        return GrokBotDualTimerHost(run_dir=run_dir)
    raise ValueError(f"unknown host {name!r}")


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    run_dir = Path(args.run_dir)
    if args.cmd == "status":
        path = run_dir / "status.json"
        sys.stdout.write(path.read_text(encoding="utf-8"))
        return 0
    if args.cmd == "run" and args.host == "prompt-only":
        host = PromptOnlyHost(run_dir=run_dir)
        sys.stdout.write(host.emit_dual_loop(run_dir=run_dir) + "\n")
        return 0
    if args.cmd == "run" and args.host == "grok-bot":
        host = GrokBotDualTimerHost(run_dir=run_dir)
        try:
            exec_id, sup_id = host.schedule()
        except ScheduleError as exc:
            sys.stderr.write(f"schedule failed (fail-closed): {exc}\n")
            return 1
        state = parse_run(run_dir)
        if state.run_status not in TERMINAL_LEDGER and (not exec_id or not sup_id):
            sys.stderr.write(
                "schedule failed (fail-closed): empty timer ids on non-terminal ledger\n"
            )
            return 1
        runner = Runner(run_dir, host=host)
        runner.run(steps=1)
        state = parse_run(run_dir)
        status = json.loads((run_dir / "status.json").read_text(encoding="utf-8"))
        sys.stdout.write(
            f"scheduled executor={exec_id} supervisor={sup_id}\n"
            f"{status.get('status')} ledger={state.run_status}\n"
        )
        return 0
    runner = Runner(run_dir)
    if args.cmd == "stop":
        runner.stop()
        return 0
    runner.run()
    state = parse_run(run_dir)
    status = json.loads((run_dir / "status.json").read_text(encoding="utf-8"))
    sys.stdout.write(f"{status.get('status')} ledger={state.run_status}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
