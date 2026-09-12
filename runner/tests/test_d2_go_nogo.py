"""Ship-R: D2 Go/No-Go pack and candidate version must stay aligned."""

from __future__ import annotations

import re
from pathlib import Path

_REPO = Path(__file__).resolve().parents[2]
_DOC = _REPO / "docs" / "ship" / "D2-GO-NOGO.md"
_PYPROJECT = _REPO / "runner" / "pyproject.toml"
_TIP_SHA = "a4cce0f"
_TIP_SHA_FULL = "a4cce0f54fc887e91158dcf630d328f2af709061"
_SOAK_PATH = "soak/tip-5de40a9-n50-mock"
_VERSION = "0.4.0-rc.1"
_VERSION_LINE = re.compile(r'^version\s*=\s*"([^"]+)"', re.M)
_UNCHECKED_DUALTIMER = re.compile(
    r"- \[ \].*(?:DualTimer|M-R2-3)",
    re.I,
)
_UNCHECKED_PUBLISH = re.compile(
    r"- \[ \].*(?:publish|ack)",
    re.I,
)
_RC1_PRESENT = re.compile(
    r"(?:tag|Release).{0,200}0\.4\.0-rc\.1.{0,200}(?:exist|\*\*MET\*\*)"
    r"|0\.4\.0-rc\.1.{0,200}(?:exists|prerelease|\*\*MET\*\*)",
    re.I | re.S,
)
_RC1_ABSENT = re.compile(
    r"0\.4\.0-rc\.1.{0,80}does\s+(?:\*\*)?not(?:\*\*)?\s+exist",
    re.I | re.S,
)


def test_d2_go_nogo_doc_exists() -> None:
    assert _DOC.is_file(), f"missing {_DOC}"
    text = _DOC.read_text(encoding="utf-8")
    assert text.strip(), f"{_DOC} is empty"
    assert _TIP_SHA in text or _TIP_SHA_FULL in text, (
        f"{_DOC} must name tip SHA {_TIP_SHA} (or the full SHA)"
    )
    assert _SOAK_PATH in text, f"{_DOC} must point at {_SOAK_PATH}"
    assert "ADVERSARIAL-TIP.md" in text, f"{_DOC} must cite ADVERSARIAL-TIP.md"
    lowered = text.lower()
    assert "owner-only" in lowered, f"{_DOC} must mark owner-only residuals"
    assert "tag" in lowered and "publish" in lowered, (
        f"{_DOC} must mention owner-only tag/publish"
    )
    assert _VERSION in text, f"{_DOC} must name candidate version {_VERSION}"
    assert _UNCHECKED_DUALTIMER.search(text), (
        f"{_DOC} must keep an unchecked DualTimer / M-R2-3 owner-only row"
    )
    assert _UNCHECKED_PUBLISH.search(text), (
        f"{_DOC} must keep an unchecked owner D2 publish ack row"
    )
    assert _RC1_PRESENT.search(text), (
        f"{_DOC} must acknowledge that tag/Release {_VERSION} exists (or MET)"
    )
    assert not _RC1_ABSENT.search(text), (
        f"{_DOC} must not claim that the {_VERSION} tag is absent"
    )


def test_runner_version_is_040_rc1() -> None:
    text = _PYPROJECT.read_text(encoding="utf-8")
    match = _VERSION_LINE.search(text)
    assert match, f"{_PYPROJECT} has no project version line"
    assert match.group(1) == _VERSION, (
        f"{_PYPROJECT} version drifted: {match.group(1)!r} != {_VERSION!r}"
    )
