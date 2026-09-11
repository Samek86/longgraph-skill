"""H2 contract fidelity: pending-audit lane/accept, directive fold, golden rounds."""

from __future__ import annotations

import json
import re
from pathlib import Path

from longgraph.gates import GateRunner
from longgraph.hosts import MockHost
from longgraph.nodes import Runner
from longgraph.rotate import rotate_directives, rotate_rounds_log
from longgraph.state import parse_run

from tests.support import copy_fixture

FIXTURES = Path(__file__).resolve().parent / "fixtures"

_STATUS = {
    "version": "1.0",
    "runId": "h2-contract",
    "status": "running",
    "phase": "executing",
    "progress": {"completedRounds": 0, "completedItems": 0},
    "nodes": {
        "executor": {"status": "active"},
        "supervisor": {"status": "active"},
    },
    "ownerEscalation": None,
    "metadata": {"itemRetries": {}, "lastAttempt": None},
}


def _write_run(
    dest: Path,
    *,
    ledger: str,
    directives: str,
    ops: str | None = None,
) -> Path:
    run_dir = dest / "run"
    run_dir.mkdir()
    (run_dir / "archive").mkdir()
    (run_dir / "ledger.md").write_text(ledger, encoding="utf-8")
    (run_dir / "directives.md").write_text(directives, encoding="utf-8")
    (run_dir / "ops.md").write_text(
        ops
        or (
            "max_rounds: 20\n"
            "max_retries: 3\n"
            "KEEP_ROUNDS: 5\n"
            "OPEN_DIRECTIVE_CAP: 8\n"
        ),
        encoding="utf-8",
    )
    (run_dir / "status.json").write_text(json.dumps(_STATUS, indent=2) + "\n", encoding="utf-8")
    (run_dir / "executor.md").write_text("# executor\n", encoding="utf-8")
    (run_dir / "supervisor.md").write_text("# supervisor\n", encoding="utf-8")
    return run_dir


def _empty_directives(*packets: str) -> str:
    body = "".join(packets) if packets else "(none yet)\n"
    return (
        "# synthetic — Directives\n\n"
        "## Supervisor state\n\n"
        "Last completed tick: none\n\n"
        "## STANDING — authority only\n\n"
        "(none yet)\n\n"
        "## Corrections (numbered; live queue = not-yet-folded only)\n\n"
        f"{body}"
    )


def _packet(n: int, verb: str = "plan", extra: str = "") -> str:
    ident = f"D-{n:03d}"
    action = extra or f"correction {ident}"
    return (
        f"{ident} · 2026-01-01 · {verb}\n"
        "Context: C-01\n"
        f"Action: {action}\n"
        "Verify: true\n"
        "Stop: none\n"
    )


def _ledger(
    *,
    item: str,
    write_set: str,
    next_item: str,
    gate: str,
    folded: str = "none",
    audit_surface: str | None = None,
) -> str:
    pending = (
        f"## Pending promotion\n\n"
        f"Boundary: M2→M3\n"
        f"Audit surface: {audit_surface}\n"
        f"Evidence: pending\n\n"
        if audit_surface
        else "## Pending promotion\n\nnone\n\n"
    )
    return (
        "# synthetic — ledger\n\n"
        "## Status header\n\n"
        "Current milestone: M2 | Round: 1 | Last round net lines: +0\n"
        f"Next unclosed work item: {next_item}\n"
        f"Last directive folded: {folded}\n"
        f"Milestone gate: `{gate}`\n"
        "Run status: `active`\n\n"
        "## Current slice\n\n"
        f"Item: {item}\n"
        f"Write set: {write_set}\n"
        "Context: C-01\n"
        "Verify: true\n"
        "Done when: closed\n\n"
        f"{pending}"
        "## Rounds log\n\n"
        "- R1 2026-01-01 | seed | verify: green | next: lane\n"
    )


def test_pending_audit_allows_lane_work(tmp_path: Path) -> None:
    """M1: disjoint registered lane work continues under pending-audit."""
    ledger = _ledger(
        item="GAP-010 lane docs (disjoint from the audit surface)",
        write_set="docs/lane-policy.md",
        next_item="M3 (owner-only: drop the blob column)",
        gate="pending-audit",
        audit_surface="migrations/drop_blob.sql, tests/test_storage.py",
    )
    run_dir = _write_run(tmp_path, ledger=ledger, directives=_empty_directives())
    workspace = tmp_path / "ws"
    host = MockHost()
    runner = Runner(run_dir, host=host, gates=GateRunner(default=True), workspace=workspace)
    runner.run(steps=1)
    assert runner.stopped_reason != "pending-audit"
    assert runner.advancement_blocked is False
    assert "executor" in host.invocations
    assert (workspace / "docs" / "lane-policy.md").is_file()
    assert "GAP-010" in runner.closed_items
    assert parse_run(run_dir).milestone_gate == "pending-audit"


def test_acceptance_directive_releases_pending_audit(tmp_path: Path) -> None:
    """M1: ACCEPT-GATE on a live correction flips pending-audit to passed."""
    ledger = _ledger(
        item="M3 (owner-only: drop the blob column)",
        write_set="migrations/drop_blob.sql",
        next_item="M3 (owner-only: drop the blob column)",
        gate="pending-audit",
        folded="D-003",
        audit_surface="migrations/drop_blob.sql",
    )
    directives = _empty_directives(
        _packet(4, "accept", "ACCEPT-GATE — flip Milestone gate to passed")
    )
    run_dir = _write_run(tmp_path, ledger=ledger, directives=directives)
    workspace = tmp_path / "ws"
    host = MockHost()
    runner = Runner(run_dir, host=host, gates=GateRunner(default=True), workspace=workspace)
    runner.run(steps=1)
    assert runner.stopped_reason != "pending-audit"
    assert "executor" in host.invocations
    assert (workspace / "migrations" / "drop_blob.sql").is_file()
    state = parse_run(run_dir)
    assert state.milestone_gate == "passed"
    assert state.last_directive_folded == "D-004"


def test_executor_folds_directives_and_advances_watermark(tmp_path: Path) -> None:
    """M2: applied-path close folds live corrections and advances the watermark."""
    ledger = _ledger(
        item="GAP-001 fold directives",
        write_set="read-only",
        next_item="GAP-001 fold directives",
        gate="n/a",
        folded="none",
    )
    directives = _empty_directives(_packet(1, "plan"), "\n", _packet(2, "plan"))
    run_dir = _write_run(tmp_path, ledger=ledger, directives=directives)
    host = MockHost()
    runner = Runner(
        run_dir,
        host=host,
        gates=GateRunner(default=True),
        workspace=tmp_path / "ws",
    )
    runner.run(steps=1)
    assert "GAP-001" in runner.closed_items
    state = parse_run(run_dir)
    assert state.last_directive_folded == "D-002"
    ledger_text = (run_dir / "ledger.md").read_text(encoding="utf-8")
    assert re.search(r"^Last directive folded:\s*D-002\b", ledger_text, re.M)


def test_rounds_log_rotates_golden_round_sections() -> None:
    """M7: golden `### Round N` sections rotate like `- R` lines."""
    golden = (FIXTURES / "add-tests-to-cli" / "ledger.md").read_text(encoding="utf-8")
    assert "### Round 1" in golden
    assert "### Round 2" in golden
    assert "### Round 3" in golden
    assert not re.search(r"^- R\d+\b", golden, re.M)

    new, archive = rotate_rounds_log(golden, keep_rounds=2)
    live_body = new.split("## Rounds log", 1)[1]
    assert "### Round 1" in archive
    assert "### Round 1" not in live_body
    assert "### Round 2" in live_body
    assert "### Round 3" in live_body
    live_headings = re.findall(r"^### Round \d+", live_body, re.M)
    assert len(live_headings) == 2

    mixed = (FIXTURES / "migrate-blob-storage" / "ledger.md").read_text(encoding="utf-8")
    mixed_new, mixed_archive = rotate_rounds_log(mixed, keep_rounds=3)
    mixed_live = mixed_new.split("## Rounds log", 1)[1]
    assert re.search(r"^- R5\b", mixed_archive, re.M)
    assert re.search(r"^- R6\b", mixed_archive, re.M)
    assert not re.search(r"^- R5\b", mixed_live, re.M)
    assert "### Round 9" in mixed_live


def test_rounds_log_rotates_golden_round_sections_on_close(tmp_path: Path) -> None:
    """M7: closing a golden-shaped ledger archives `### Round` under KEEP_ROUNDS."""
    run_dir = copy_fixture("add-tests-to-cli", tmp_path)
    ops = run_dir / "ops.md"
    ops.write_text(ops.read_text(encoding="utf-8") + "\nKEEP_ROUNDS: 2\n", encoding="utf-8")
    runner = Runner(
        run_dir,
        gates=GateRunner(default=True),
        workspace=tmp_path / "ws",
    )
    runner.run(steps=1)
    assert "GAP-002" in runner.closed_items
    live = (run_dir / "ledger.md").read_text(encoding="utf-8").split("## Rounds log", 1)[1]
    archive = (run_dir / "archive" / "rounds.md").read_text(encoding="utf-8")
    assert "### Round 1" in archive
    live_entries = re.findall(r"^(?:### Round \d+|- R\d+)\b", live, re.M)
    assert len(live_entries) <= 2


def test_rotate_does_not_cap_unfolded_packets() -> None:
    """M2: OPEN_DIRECTIVE_CAP must not archive packets above the watermark."""
    packets = "".join(_packet(n) + "\n" for n in range(1, 11))
    text = _empty_directives(packets)
    new, archive = rotate_directives(text, "none", open_directive_cap=8)
    assert archive == ""
    live_ids = [int(m.group(1)) for m in re.finditer(r"^D-(\d+)\b", new, re.M)]
    assert live_ids == list(range(1, 11))
