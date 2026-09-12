"""Ship-S1 multi-fixture soak driver.

Not a product runtime. Copies committed fixtures into an isolated workspace,
ticks them via public runner APIs (MockHost loop) or the emit-only CLI
(prompt-only), and writes a machine+human evidence pack.

CLI ``longgraph run --host mock`` always uses Runner.run() default steps=8
and has no --steps flag, so mock soaks drive ``Runner.run(steps=1)`` N times
with the same fail-closed GateRunner the CLI uses.
"""

from __future__ import annotations

import argparse
import hashlib
import io
import json
import re
import shutil
import sys
import traceback
from collections import Counter
from contextlib import redirect_stdout
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

PROTECTED = frozenset({"ledger.md", "directives.md", "ops.md", "status.json"})
CLOSE_MARK = re.compile(r"<!-- runner closed (\S+) -->")
STOP_OK = frozenset({"completed", "cancelled", "failed", "paused"})
DEFAULT_FIXTURES = (
    "add-tests-to-cli",
    "migrate-blob-storage",
    "scout-library-choice",
)
SMOKE_DEFAULT_ROUNDS = 5


def _utc_run_id() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def _repo_root() -> Path:
    return Path(__file__).resolve().parent.parent


def _ensure_runner_path(repo: Path) -> None:
    runner = repo / "runner"
    if str(runner) not in sys.path:
        sys.path.insert(0, str(runner))


def fingerprint(root: Path) -> dict[str, str]:
    out: dict[str, str] = {}
    if not root.exists():
        return out
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        rel = path.relative_to(root).as_posix()
        out[rel] = hashlib.sha256(path.read_bytes()).hexdigest()
    return out


def _is_relative_to(path: Path, root: Path) -> bool:
    try:
        path.resolve().relative_to(root.resolve())
        return True
    except ValueError:
        return False


def _load_status(run_dir: Path) -> dict[str, Any]:
    path = run_dir / "status.json"
    if not path.is_file():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def _closed_markers(run_dir: Path) -> list[str]:
    ledger = run_dir / "ledger.md"
    if not ledger.is_file():
        return []
    return CLOSE_MARK.findall(ledger.read_text(encoding="utf-8"))


def _resolve_fixtures(repo: Path, raw: list[str]) -> list[tuple[str, Path]]:
    fixtures_root = repo / "runner" / "tests" / "fixtures"
    names = raw or list(DEFAULT_FIXTURES)
    resolved: list[tuple[str, Path]] = []
    for item in names:
        path = Path(item)
        if path.is_dir() and (path / "ledger.md").is_file():
            resolved.append((path.name, path.resolve()))
            continue
        candidate = fixtures_root / item
        if candidate.is_dir() and (candidate / "ledger.md").is_file():
            resolved.append((item, candidate.resolve()))
            continue
        raise SystemExit(f"soak: fixture not found or missing ledger.md: {item}")
    return resolved


def _writer_faults(writer_log: list[tuple[str, str]], run_dir: Path, workspace: Path) -> list[str]:
    faults: list[str] = []
    for node, dest in writer_log:
        dest_p = Path(dest).resolve()
        in_run = _is_relative_to(dest_p, run_dir)
        in_ws = _is_relative_to(dest_p, workspace)
        if not in_run and not in_ws:
            faults.append(f"escape:{node}:{dest_p}")
            continue
        if in_ws and dest_p.name in PROTECTED:
            faults.append(f"workspace-scoreboard:{node}:{dest_p.name}")
        if in_run and dest_p.name in PROTECTED and dest_p.parent.resolve() == run_dir.resolve():
            if node == "supervisor" and dest_p.name != "directives.md":
                faults.append(f"clobber:{node}:{dest_p.name}")
            elif node == "executor" and dest_p.name != "ledger.md":
                faults.append(f"clobber:{node}:{dest_p.name}")
            elif node == "scout":
                faults.append(f"clobber:{node}:{dest_p.name}")
    return faults


def _workspace_scoreboard_faults(workspace: Path) -> list[str]:
    if not workspace.exists():
        return []
    faults: list[str] = []
    for path in workspace.rglob("*"):
        if path.is_file() and path.name in PROTECTED:
            faults.append(f"workspace-scoreboard-file:{path.relative_to(workspace)}")
    return faults


def _check_max_rounds(status: dict[str, Any], max_rounds: int, stopped_reason: str | None) -> list[str]:
    completed = int((status.get("progress") or {}).get("completedRounds") or 0)
    state = status.get("status")
    if completed > max_rounds:
        return ["max_rounds_exceeded_without_clean_stop"]
    if completed >= max_rounds and state not in STOP_OK and stopped_reason != "max_rounds":
        return ["max_rounds_exceeded_without_clean_stop"]
    return []


def soak_mock_fixture(
    *,
    name: str,
    source: Path,
    work_root: Path,
    rounds: int,
    evidence_dir: Path,
) -> dict[str, Any]:
    from longgraph.cli import host_for
    from longgraph.nodes import Runner
    from longgraph.state import current_slice_owner_blocked, derive_item_id, parse_run

    run_dir = work_root / "run"
    shutil.copytree(source, run_dir)
    workspace = work_root / "workspace"
    workspace.mkdir(parents=True, exist_ok=True)

    ops_before = (run_dir / "ops.md").read_bytes() if (run_dir / "ops.md").is_file() else b""
    host = host_for("mock", run_dir)
    runner = Runner(run_dir, host=host, workspace=workspace)

    initial_status = _load_status(run_dir)
    initial_closed = list((initial_status.get("metadata") or {}).get("closedItems") or [])
    initial_rounds = int((initial_status.get("progress") or {}).get("completedRounds") or 0)
    initial_escalation = initial_status.get("ownerEscalation")
    ticks: list[dict[str, Any]] = []
    faults: list[str] = []
    uncaught: str | None = None

    for i in range(1, rounds + 1):
        before_markers = _closed_markers(run_dir)
        before_status = _load_status(run_dir)
        before_closed = list((before_status.get("metadata") or {}).get("closedItems") or [])
        before_rounds = int((before_status.get("progress") or {}).get("completedRounds") or 0)
        try:
            runner.run(steps=1)
        except Exception:  # noqa: BLE001 — soak must surface any runner crash
            uncaught = traceback.format_exc()
            faults.append("uncaught_exception")
            ticks.append({"tick": i, "uncaught": True})
            break
        after_status = _load_status(run_dir)
        after_markers = _closed_markers(run_dir)
        after_closed = list((after_status.get("metadata") or {}).get("closedItems") or [])
        after_rounds = int((after_status.get("progress") or {}).get("completedRounds") or 0)
        marker_counts = Counter(after_markers)
        if any(n > 1 for n in marker_counts.values()):
            faults.append("reclose_storm")
        if len(after_closed) != len(set(after_closed)):
            faults.append("reclose_storm")
        new_unique = set(after_closed) - set(before_closed)
        if after_rounds - before_rounds > max(len(new_unique), 0):
            faults.append("reclose_storm")
        if set(before_markers) and after_rounds > before_rounds:
            # A previously marked item must not mint another completedRound alone.
            if not new_unique and after_rounds > before_rounds:
                faults.append("reclose_storm")
        try:
            state = parse_run(run_dir)
            if current_slice_owner_blocked(state):
                item_id = derive_item_id(state)
                if item_id in new_unique:
                    faults.append("owner_escalation_auto")
        except Exception as exc:  # parse failure is a soak fault
            faults.append(f"parse:{exc}")
        ticks.append(
            {
                "tick": i,
                "status": after_status.get("status"),
                "completedRounds": after_rounds,
                "closedItems": after_closed,
                "stopped_reason": runner.stopped_reason,
                "close_markers": after_markers,
            }
        )

    faults.extend(_writer_faults(runner.writer.log, run_dir, workspace))
    faults.extend(_workspace_scoreboard_faults(workspace))
    if (run_dir / "ops.md").is_file() and (run_dir / "ops.md").read_bytes() != ops_before:
        faults.append("ops_clobber")

    final_status = _load_status(run_dir)
    try:
        state = parse_run(run_dir)
        max_rounds = int(state.ops.max_rounds)
    except Exception:
        max_rounds = 100
        state = None  # type: ignore[assignment]
    faults.extend(_check_max_rounds(final_status, max_rounds, runner.stopped_reason))
    if initial_escalation is not None and final_status.get("ownerEscalation") is None:
        faults.append("owner_escalation_auto")

    faults = list(dict.fromkeys(faults))
    fixture_ev = evidence_dir / "fixtures" / name
    fixture_ev.mkdir(parents=True, exist_ok=True)
    (fixture_ev / "ticks.jsonl").write_text(
        "".join(json.dumps(row) + "\n" for row in ticks),
        encoding="utf-8",
    )
    (fixture_ev / "final-status.json").write_text(
        json.dumps(final_status, indent=2) + "\n",
        encoding="utf-8",
    )

    pollution = [
        f
        for f in faults
        if f.startswith(("escape:", "workspace-scoreboard", "clobber:", "ops_clobber"))
    ]
    return {
        "name": name,
        "host": "mock",
        "rounds_requested": rounds,
        "ticks_ran": len(ticks),
        "passed": not faults,
        "faults": faults,
        "scoreboard_pollution": len(pollution),
        "reclose_storm": sum(1 for f in faults if f == "reclose_storm"),
        "timer_zombie": 0,
        "timer_zombie_status": "not_exercised",
        "owner_escalation_auto": sum(1 for f in faults if f == "owner_escalation_auto"),
        "uncaught_exception": uncaught,
        "initial_completedRounds": initial_rounds,
        "final_completedRounds": int((final_status.get("progress") or {}).get("completedRounds") or 0),
        "initial_closedItems": initial_closed,
        "final_closedItems": list((final_status.get("metadata") or {}).get("closedItems") or []),
        "final_status": final_status.get("status"),
        "stopped_reason": runner.stopped_reason,
        "max_rounds": max_rounds,
        "writer_log_len": len(runner.writer.log),
    }


def soak_prompt_only_fixture(
    *,
    name: str,
    source: Path,
    work_root: Path,
    rounds: int,
    evidence_dir: Path,
) -> dict[str, Any]:
    from longgraph.cli import main

    run_dir = work_root / "run"
    shutil.copytree(source, run_dir)
    before = fingerprint(run_dir)
    emits: list[str] = []
    faults: list[str] = []
    uncaught: str | None = None
    for i in range(1, rounds + 1):
        buf = io.StringIO()
        try:
            with redirect_stdout(buf):
                rc = main(["run", "--host", "prompt-only", str(run_dir)])
        except Exception:  # noqa: BLE001
            uncaught = traceback.format_exc()
            faults.append("uncaught_exception")
            break
        if rc != 0:
            faults.append(f"cli_exit:{rc}")
        emits.append(f"tick={i} rc={rc}\n{buf.getvalue()}")
    after = fingerprint(run_dir)
    if before != after:
        faults.append("scoreboard_pollution")
    fixture_ev = evidence_dir / "fixtures" / name
    fixture_ev.mkdir(parents=True, exist_ok=True)
    (fixture_ev / "emit.txt").write_text("\n".join(emits) + "\n", encoding="utf-8")
    (fixture_ev / "final-status.json").write_text(
        json.dumps(_load_status(run_dir), indent=2) + "\n",
        encoding="utf-8",
    )
    return {
        "name": name,
        "host": "prompt-only",
        "rounds_requested": rounds,
        "ticks_ran": len(emits),
        "passed": not faults,
        "faults": faults,
        "scoreboard_pollution": 1 if "scoreboard_pollution" in faults else 0,
        "reclose_storm": 0,
        "timer_zombie": 0,
        "timer_zombie_status": "not_exercised",
        "owner_escalation_auto": 0,
        "uncaught_exception": uncaught,
        "final_status": _load_status(run_dir).get("status"),
        "stopped_reason": None,
    }


def _write_evidence(
    evidence_dir: Path,
    *,
    run_id: str,
    host: str,
    rounds: int,
    source_before: dict[str, dict[str, str]],
    source_after: dict[str, dict[str, str]],
    results: list[dict[str, Any]],
) -> None:
    source_faults: list[str] = []
    for name, before in source_before.items():
        if source_after.get(name) != before:
            source_faults.append(f"committed_fixture_mutated:{name}")
            for result in results:
                if result["name"] == name:
                    result["faults"] = list(result.get("faults") or []) + [
                        "committed_fixture_mutated"
                    ]
                    result["passed"] = False
                    result["scoreboard_pollution"] = int(result.get("scoreboard_pollution") or 0) + 1

    passed = all(r.get("passed") for r in results) and not source_faults
    totals = {
        "scoreboard_pollution": sum(int(r.get("scoreboard_pollution") or 0) for r in results)
        + len(source_faults),
        "reclose_storm": sum(int(r.get("reclose_storm") or 0) for r in results),
        "timer_zombie": sum(int(r.get("timer_zombie") or 0) for r in results),
        "owner_escalation_auto": sum(int(r.get("owner_escalation_auto") or 0) for r in results),
        "uncaught_exception": sum(1 for r in results if r.get("uncaught_exception")),
    }
    payload = {
        "run_id": run_id,
        "host": host,
        "rounds": rounds,
        "passed": passed,
        "fixtures": [r["name"] for r in results],
        "totals": totals,
        "source_faults": source_faults,
        "results": results,
        "evidence_dir": str(evidence_dir),
    }
    (evidence_dir / "summary.json").write_text(
        json.dumps(payload, indent=2) + "\n",
        encoding="utf-8",
    )
    lines = [
        f"# Soak evidence `{run_id}`",
        "",
        f"- host: `{host}`",
        f"- rounds per fixture: {rounds}",
        f"- fixtures: {', '.join(r['name'] for r in results)}",
        f"- passed: **{'yes' if passed else 'no'}**",
        "",
        "## Totals (must all be 0 to pass)",
        "",
        f"- scoreboard pollution: {totals['scoreboard_pollution']}",
        f"- re-close storm: {totals['reclose_storm']}",
        f"- timer zombie: {totals['timer_zombie']} (mock/prompt-only: not exercised)",
        f"- owner escalation auto-acked: {totals['owner_escalation_auto']}",
        f"- uncaught exception: {totals['uncaught_exception']}",
        "",
        "## Per fixture",
        "",
    ]
    for result in results:
        lines.append(f"### {result['name']}")
        lines.append("")
        lines.append(f"- passed: {result['passed']}")
        lines.append(f"- ticks: {result.get('ticks_ran')}/{result.get('rounds_requested')}")
        lines.append(f"- final status: {result.get('final_status')}")
        lines.append(f"- stopped_reason: {result.get('stopped_reason')}")
        lines.append(f"- faults: {result.get('faults') or 'none'}")
        lines.append("")
    if source_faults:
        lines.append("## Committed fixture mutation")
        lines.append("")
        for fault in source_faults:
            lines.append(f"- {fault}")
        lines.append("")
    (evidence_dir / "SUMMARY.md").write_text("\n".join(lines), encoding="utf-8")


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="ship-soak",
        description=(
            "Ship-S1 multi-fixture soak harness. Copies fixtures to an isolated "
            "temp workspace and ticks them. Production D2: --rounds 50 (N>=50) "
            "or a >=24h operator wall-clock run. CI/smoke default is "
            f"{SMOKE_DEFAULT_ROUNDS}."
        ),
    )
    parser.add_argument(
        "--rounds",
        type=int,
        default=SMOKE_DEFAULT_ROUNDS,
        help=f"ticks per fixture (default {SMOKE_DEFAULT_ROUNDS}; production N>=50)",
    )
    parser.add_argument(
        "--host",
        choices=("mock", "prompt-only"),
        default="mock",
        help="mock: closed-loop scoreboard checks; prompt-only: emit-only smoke",
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=None,
        help="evidence directory for this run (default .longgraph-ship/soak/<run-id>)",
    )
    parser.add_argument(
        "--run-id",
        default=None,
        help="override run id (UTC timestamp used when omitted)",
    )
    parser.add_argument(
        "fixtures",
        nargs="*",
        help="fixture names under runner/tests/fixtures/ or paths to run dirs",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    if args.rounds < 1:
        raise SystemExit("soak: --rounds must be >= 1")
    repo = _repo_root()
    _ensure_runner_path(repo)
    fixtures = _resolve_fixtures(repo, list(args.fixtures))
    run_id = args.run_id or _utc_run_id()
    evidence_dir = Path(args.out) if args.out else repo / ".longgraph-ship" / "soak" / run_id
    evidence_dir = evidence_dir.resolve()
    evidence_dir.mkdir(parents=True, exist_ok=True)

    source_before = {name: fingerprint(src) for name, src in fixtures}
    work_root = evidence_dir / "work"
    if work_root.exists():
        shutil.rmtree(work_root)
    work_root.mkdir(parents=True)

    results: list[dict[str, Any]] = []
    for name, source in fixtures:
        dest = work_root / name
        dest.mkdir()
        if args.host == "prompt-only":
            results.append(
                soak_prompt_only_fixture(
                    name=name,
                    source=source,
                    work_root=dest,
                    rounds=args.rounds,
                    evidence_dir=evidence_dir,
                )
            )
        else:
            results.append(
                soak_mock_fixture(
                    name=name,
                    source=source,
                    work_root=dest,
                    rounds=args.rounds,
                    evidence_dir=evidence_dir,
                )
            )

    source_after = {name: fingerprint(src) for name, src in fixtures}
    _write_evidence(
        evidence_dir,
        run_id=run_id,
        host=args.host,
        rounds=args.rounds,
        source_before=source_before,
        source_after=source_after,
        results=results,
    )

    # Isolated work copies can be large; keep summary + per-fixture traces.
    shutil.rmtree(work_root, ignore_errors=True)

    summary = json.loads((evidence_dir / "summary.json").read_text(encoding="utf-8"))
    sys.stdout.write((evidence_dir / "SUMMARY.md").read_text(encoding="utf-8"))
    sys.stdout.write(f"\nevidence: {evidence_dir}\n")
    return 0 if summary.get("passed") else 1


if __name__ == "__main__":
    raise SystemExit(main())
