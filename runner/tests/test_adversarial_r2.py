"""Ship-S2: adversarial R2 evidence pack must stay in the tree."""

from __future__ import annotations

from pathlib import Path

_REPO = Path(__file__).resolve().parents[2]
_R2 = _REPO / "docs" / "ship" / "ADVERSARIAL-R2.md"


def test_adversarial_r2_doc_exists() -> None:
    assert _R2.is_file(), f"missing {_R2}"
    text = _R2.read_text(encoding="utf-8")
    assert text.strip(), f"{_R2} is empty"
    assert "## Critical" in text, f"{_R2} lacks a ## Critical section"
