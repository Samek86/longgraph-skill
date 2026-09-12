"""Ship-D2: tip mock N=50 soak evidence pack must stay in the tree."""

from __future__ import annotations

import json
import re
from pathlib import Path

_REPO = Path(__file__).resolve().parents[2]
_PACK = _REPO / "docs" / "ship" / "soak" / "tip-5de40a9-n50-mock"
_SUMMARY = _PACK / "SUMMARY.md"
_JSON = _PACK / "summary.json"
_TIP_SHA = "5de40a9"
_REQUIRED_FIXTURES = (
    "add-tests-to-cli",
    "migrate-blob-storage",
    "scout-library-choice",
)
_CRITERIA = (
    (r"scoreboard pollution:\s*0", "scoreboard pollution 0"),
    (r"re-close storm:\s*0", "re-close storm 0"),
    (r"timer zombie:.*(?:not_exercised|not exercised|N/A)", "timer zombie not_exercised"),
    (r"owner escalation.*(?:0|manual-only|manual only)", "owner escalation 0/manual-only"),
    (r"uncaught exception:\s*0", "uncaught exception 0"),
    (r"max_rounds:\s*clean", "max_rounds clean"),
)


def test_tip_soak_evidence_pack_exists() -> None:
    assert _PACK.is_dir(), f"missing {_PACK}"
    assert _SUMMARY.is_file(), f"missing {_SUMMARY}"
    text = _SUMMARY.read_text(encoding="utf-8")
    assert text.strip(), f"{_SUMMARY} is empty"
    assert _TIP_SHA in text, f"{_SUMMARY} must name tip SHA {_TIP_SHA}"
    assert re.search(r"host:\s*`mock`", text), f"{_SUMMARY} must record host=`mock`"
    assert re.search(r"rounds per fixture:\s*50\b", text), (
        f"{_SUMMARY} must record N>=50 (rounds per fixture: 50)"
    )
    for name in _REQUIRED_FIXTURES:
        assert name in text, f"{_SUMMARY} missing fixture {name}"
    assert re.search(r"passed:\s*\*\*yes\*\*", text, re.I), f"{_SUMMARY} must record passed: **yes**"
    for pat, label in _CRITERIA:
        assert re.search(pat, text, re.I), f"{_SUMMARY} missing {label}"


def test_tip_soak_evidence_summary_json() -> None:
    assert _JSON.is_file(), f"missing {_JSON}"
    payload = json.loads(_JSON.read_text(encoding="utf-8"))
    assert _TIP_SHA in str(payload.get("tip_sha") or "") or _TIP_SHA in json.dumps(payload)
    assert payload.get("host") == "mock"
    assert int(payload.get("rounds") or 0) >= 50
    assert payload.get("passed") is True
    fixtures = set(payload.get("fixtures") or [])
    assert fixtures >= set(_REQUIRED_FIXTURES)
    totals = payload.get("totals") or {}
    assert totals.get("scoreboard_pollution") == 0
    assert totals.get("reclose_storm") == 0
    assert totals.get("timer_zombie") == 0
    assert totals.get("owner_escalation_auto") == 0
    assert totals.get("uncaught_exception") == 0
