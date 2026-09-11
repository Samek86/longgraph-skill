"""Ship-S: PUBLIC_CLAIMS.md P1–P10 names must stay in the collected suite."""

from __future__ import annotations

import re
from pathlib import Path

_REPO = Path(__file__).resolve().parents[2]
_TESTS = Path(__file__).resolve().parent
_CLAIMS_MD = _REPO / "docs" / "ship" / "PUBLIC_CLAIMS.md"
_CLAIM_ROW = re.compile(r"^\|\s*(P\d+)\s*\|")
_TEST_NAME = re.compile(r"`(test_[A-Za-z0-9_]+)`")
_DEF_TEST = re.compile(r"^def (test_[A-Za-z0-9_]+)\s*\(", re.M)
_REQUIRED_IDS = tuple(f"P{i}" for i in range(1, 11))


def parse_public_claims_table(text: str) -> dict[str, list[str]]:
    """Map P-ids to backtick test names from the §1.1 markdown table."""
    claims: dict[str, list[str]] = {}
    for line in text.splitlines():
        match = _CLAIM_ROW.match(line)
        if not match:
            continue
        pid = match.group(1)
        names = _TEST_NAME.findall(line)
        if names:
            claims[pid] = names
    return claims


def collect_defined_test_names(tests_dir: Path = _TESTS) -> set[str]:
    """Names pytest can collect: every `def test_*` under runner/tests/.

    File scan (not `request.session.items`) so a filtered invocation
    such as `scripts/ship-negative-battery.sh` still checks the full suite.
    """
    names: set[str] = set()
    for path in sorted(tests_dir.glob("test_*.py")):
        names.update(_DEF_TEST.findall(path.read_text(encoding="utf-8")))
    return names


def test_public_claims_mapped_tests_exist() -> None:
    assert _CLAIMS_MD.is_file(), f"missing {_CLAIMS_MD}"
    claims = parse_public_claims_table(_CLAIMS_MD.read_text(encoding="utf-8"))
    missing_ids = [pid for pid in _REQUIRED_IDS if pid not in claims]
    assert not missing_ids, f"PUBLIC_CLAIMS.md missing P-ids: {missing_ids}"

    required = {name for names in claims.values() for name in names}
    assert required, "PUBLIC_CLAIMS.md table has no backtick test names"

    collected = collect_defined_test_names()
    missing = sorted(required - collected)
    assert not missing, (
        "PUBLIC_CLAIMS.md names missing from the collected suite: " + ", ".join(missing)
    )
