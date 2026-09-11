from __future__ import annotations

import json
import re
from pathlib import Path

from longgraph.gates import GateRunner
from longgraph.hosts import MockHost
from longgraph.nodes import Runner
from longgraph.rotate import next_directive_id

_STATUS = {
    "version": "1.0",
    "runId": "rotation-synthetic",
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


def _round_lines(*ns: int) -> str:
    return "".join(
        f"- R{n} 2026-01-0{min(n, 9)} | GAP-001 | verify: green | next: GAP-001\n" for n in ns
    )


def _packet(n: int, verb: str = "accept") -> str:
    ident = f"D-{n:03d}"
    return (
        f"{ident} · 2026-01-01 · {verb}\n"
        "Context: C-01\n"
        f"Action: correction {ident}\n"
        "Verify: true\n"
        "Stop: none\n"
    )


def test_rounds_log_rotates_to_archive(tmp_path: Path) -> None:
    ledger = (
        "# synthetic — ledger\n\n"
        "## Status header\n\n"
        "Current milestone: single | Round: 7 | Last round net lines: +0\n"
        "Next unclosed work item: GAP-001\n"
        "Last directive folded: none\n"
        "Milestone gate: n/a\n"
        "Run status: `active`\n\n"
        "## Current slice\n\n"
        "Item: GAP-001 rotate rounds\n"
        "Write set: read-only\n"
        "Context: C-01\n"
        "Verify: true\n"
        "Done when: closed\n\n"
        "## Rounds log — last 5 only (older → `archive/rounds.md`)\n\n"
        + _round_lines(1, 2, 3, 4, 5, 6, 7)
    )
    directives = (
        "# synthetic — Directives\n\n"
        "## Supervisor state\n\n"
        "Last completed tick: none\n\n"
        "## STANDING — authority only\n\n"
        "(none yet)\n\n"
        "## Corrections (numbered; live queue = not-yet-folded only)\n\n"
        "(none yet)\n"
    )
    run_dir = _write_run(tmp_path, ledger=ledger, directives=directives)
    runner = Runner(run_dir, gates=GateRunner(default=True), workspace=tmp_path / "ws")
    runner.run(steps=1)
    assert "GAP-001" in runner.closed_items

    live = (run_dir / "ledger.md").read_text(encoding="utf-8")
    live_rounds = re.findall(r"^- R(\d+)\b", live, re.M)
    assert len(live_rounds) <= 5
    assert "1" not in live_rounds
    assert "2" not in live_rounds
    assert "3" not in live_rounds

    archive = run_dir / "archive" / "rounds.md"
    assert archive.is_file()
    archived = archive.read_text(encoding="utf-8")
    assert archived.lstrip().startswith("#")
    assert re.search(r"^- R1\b", archived, re.M)
    assert re.search(r"^- R2\b", archived, re.M)
    assert re.search(r"^- R3\b", archived, re.M)
    assert "GAP-001" in archived or "R1" in archived


def test_directives_rotate_at_watermark(tmp_path: Path) -> None:
    ledger = (
        "# synthetic — ledger\n\n"
        "## Status header\n\n"
        "Current milestone: single | Round: 1 | Last round net lines: +0\n"
        "Next unclosed work item: GAP-001\n"
        "Last directive folded: D-003\n"
        "Milestone gate: n/a\n"
        "Run status: `active`\n\n"
        "## Current slice\n\n"
        "Item: GAP-001 fold directives\n"
        "Write set: read-only\n"
        "Context: C-01\n"
        "Verify: true\n"
        "Done when: closed\n\n"
        "## Rounds log\n\n"
        "- R1 2026-01-01 | seed | verify: green | next: GAP-001\n"
    )
    standing = "S-001 · PRE-AUTH — keep this standing line\n"
    directives = (
        "# synthetic — Directives\n\n"
        "## Supervisor state\n\n"
        "Last completed tick: none | audited through round: 0\n\n"
        "## STANDING — authority only (always in force; treat like red lines)\n\n"
        f"{standing}\n"
        "## Corrections (numbered; live queue = not-yet-folded only)\n\n"
        + _packet(1)
        + "\n"
        + _packet(2)
        + "\n"
        + _packet(3)
        + "\n"
        + _packet(4)
        + "\n"
        + _packet(5)
    )
    run_dir = _write_run(tmp_path, ledger=ledger, directives=directives)
    host = MockHost()
    runner = Runner(
        run_dir,
        host=host,
        gates=GateRunner(default=True),
        workspace=tmp_path / "ws",
    )
    runner.run(steps=1)
    assert "supervisor" in host.invocations

    live = (run_dir / "directives.md").read_text(encoding="utf-8")
    archive = run_dir / "archive" / "directives.md"
    assert archive.is_file()
    archived = archive.read_text(encoding="utf-8")
    assert archived.lstrip().startswith("#")

    # Applied-path fold advances the watermark through live packets (D-004,
    # D-005). Rotate-before-append then archives IDs ≤ the new watermark.
    for folded in ("D-001", "D-002", "D-003", "D-004", "D-005"):
        assert not re.search(rf"^{folded}\b", live, re.M), folded
        assert re.search(rf"^{folded}\b", archived, re.M), folded

    assert standing.strip() in live
    live_ids = [int(m.group(1)) for m in re.finditer(r"^D-(\d+)\b", live, re.M)]
    assert live_ids
    assert all(n > 5 for n in live_ids)
    allocated = next_directive_id("D-005", live, archived)
    assert int(re.search(r"(\d+)", allocated).group(1)) > 5
    assert allocated not in {"D-001", "D-002", "D-003", "D-004", "D-005"}
    assert not re.search(r"^D-001\b", live, re.M)
