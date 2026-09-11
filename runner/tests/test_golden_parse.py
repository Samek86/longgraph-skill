from __future__ import annotations

from pathlib import Path

from longgraph.state import parse_run

FIXTURES = Path(__file__).resolve().parent / "fixtures"


def test_golden_parse() -> None:
    add = parse_run(FIXTURES / "add-tests-to-cli")
    assert add.next_item == 'GAP-002 timezone bug in "in N days" (picked up this round)'
    assert add.open_gaps == ["GAP-002"]
    assert add.last_directive_folded == "none"
    assert add.milestone_gate == "n/a"
    assert add.run_status == "active"
    assert add.current_slice.Item == "Fix GAP-002 (timezone off-by-one in in N days)"
    assert add.current_slice["Write set"] == (
        "tests/test_dates.py (and minimal parser fix under date util if required by Done when)"
    )
    assert add.current_slice.Context == "C-01"
    assert add.current_slice.Verify == "pytest tests/test_dates.py -q"
    assert add.current_slice["Done when"] == (
        "previously-xfail midnight case passes; full pytest -q green"
    )

    migrate = parse_run(FIXTURES / "migrate-blob-storage")
    assert migrate.next_item == "M3 (owner-only: drop the blob column)"
    assert migrate.last_directive_folded == "D-003"
    assert migrate.open_gaps == []
    assert migrate.owner_blocked == ["OB-001"]
    assert migrate.milestone_gate == "passed"
    assert migrate.run_status == "active"

    scout = parse_run(FIXTURES / "scout-library-choice")
    assert scout.blocked_on == "findings#s3-client"
    findings = FIXTURES / "scout-library-choice" / "findings" / "s3-client.md"
    assert findings.is_file()
    assert scout.findings_path == "findings/s3-client.md"
    assert (FIXTURES / "scout-library-choice" / scout.findings_path).is_file()
