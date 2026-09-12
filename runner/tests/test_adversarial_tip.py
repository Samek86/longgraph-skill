"""Ship-D2: tip re-pass evidence pack must stay in the tree."""

from __future__ import annotations

import re
from pathlib import Path

_REPO = Path(__file__).resolve().parents[2]
_TIP = _REPO / "docs" / "ship" / "ADVERSARIAL-TIP.md"
_TIP_SHA = "eeb7591"
_TIP_SHA_FULL = "eeb759164f42b5ceb5fbeb25405a027286e3b93a"
_CRITICAL_ZERO = re.compile(
    r"Critical(?: count)?(?: remaining)?\s*[:=|]\s*\**0\**",
    re.I,
)


def test_adversarial_tip_doc_exists() -> None:
    assert _TIP.is_file(), f"missing {_TIP}"
    text = _TIP.read_text(encoding="utf-8")
    assert text.strip(), f"{_TIP} is empty"
    assert _TIP_SHA in text or _TIP_SHA_FULL in text, (
        f"{_TIP} must name tip SHA {_TIP_SHA} (or the full SHA)"
    )
    assert "## Critical" in text, f"{_TIP} lacks a ## Critical section"
    assert _CRITICAL_ZERO.search(text), (
        f"{_TIP} must state a Critical | **0** (or Critical count remaining: **0**) verdict"
    )
