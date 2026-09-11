"""CLI: longgraph run|status|stop <run_dir>."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .nodes import Runner
from .state import parse_run


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="longgraph", description="Phase 1a MockHost runner")
    sub = parser.add_subparsers(dest="cmd", required=True)
    for name in ("run", "status", "stop"):
        item = sub.add_parser(name)
        item.add_argument("run_dir")
    args = parser.parse_args(argv)
    run_dir = Path(args.run_dir)
    if args.cmd == "status":
        path = run_dir / "status.json"
        sys.stdout.write(path.read_text(encoding="utf-8"))
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
