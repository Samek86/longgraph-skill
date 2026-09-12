"""Ship-R: D2 Go/No-Go pack and candidate version must stay aligned."""

from __future__ import annotations

import re
from pathlib import Path

_REPO = Path(__file__).resolve().parents[2]
_DOC = _REPO / "docs" / "ship" / "D2-GO-NOGO.md"
_PYPROJECT = _REPO / "runner" / "pyproject.toml"
_TIP_SHA = "f2f493b"
_TIP_SHA_FULL = "f2f493b52a66daac172fdde9ace485297a32b297"
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
_UNCHECKED_TAG = re.compile(
    r"- \[ \].*(?:SemVer tag|GitHub Release|0\.4\.0-rc\.1)",
    re.I,
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
    assert _UNCHECKED_TAG.search(text), (
        f"{_DOC} must keep an unchecked new SemVer tag / Release row"
    )
    assert "not exist" in lowered or "does **not** exist" in lowered, (
        f"{_DOC} must state that the {_VERSION} tag does not exist"
    )


def test_runner_version_is_040_rc1() -> None:
    text = _PYPROJECT.read_text(encoding="utf-8")
    match = _VERSION_LINE.search(text)
    assert match, f"{_PYPROJECT} has no project version line"
    assert match.group(1) == _VERSION, (
        f"{_PYPROJECT} version drifted: {match.group(1)!r} != {_VERSION!r}"
    )
