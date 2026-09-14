"""Ship-S5: SUPPORT.md + CI runner matrix stay aligned with the CLI."""

from __future__ import annotations

import re
from pathlib import Path

from longgraph.cli import HOST_CHOICES

_REPO = Path(__file__).resolve().parents[2]
_SUPPORT_MD = _REPO / "docs" / "ship" / "SUPPORT.md"
_WORKFLOW = _REPO / ".github" / "workflows" / "validate.yml"
_PYPROJECT = _REPO / "runner" / "pyproject.toml"
_ROOT_README = _REPO / "README.md"
_RUNNER_README = _REPO / "runner" / "README.md"

_AXIS_ROW = re.compile(r"^\|\s*(CLI hosts|Python|OS)\s*\|\s*(.+?)\s*\|")
_TICK = re.compile(r"`([^`]+)`")
_REQUIRED_AXES = ("CLI hosts", "Python", "OS")
_REQUIRED_HOSTS = frozenset({"prompt-only", "grok-bot", "mock"})
_REQUIRED_PYTHON = frozenset({"3.11", "3.12"})
_REQUIRED_OS = frozenset({"ubuntu-latest", "windows-latest"})
_MATRIX_OS = re.compile(r"^\s+os:\s*\[([^\]]+)\]", re.M)
_NON_SUPPORT = (
    "LangGraph",
    "wake",
    "longgraph-dev-continue",
    "write-set",
    "owner-only",
)
_MATRIX_PY = re.compile(r"python-version:\s*\[([^\]]+)\]")
_MATRIX_ITEM = re.compile(r"['\"]([^'\"]+)['\"]")


def parse_frozen_surface(text: str) -> dict[str, list[str]]:
    """Map Frozen surface axes to backtick values."""
    axes: dict[str, list[str]] = {}
    for line in text.splitlines():
        match = _AXIS_ROW.match(line)
        if not match:
            continue
        axes[match.group(1)] = _TICK.findall(match.group(2))
    return axes


def runner_job_block(workflow: str) -> str:
    """Return the `runner:` job body from validate.yml."""
    match = re.search(r"^  runner:\n", workflow, re.M)
    assert match, "validate.yml has no runner job"
    rest = workflow[match.start() :]
    nxt = re.search(r"\n  [A-Za-z][\w-]*:", rest[len("  runner:\n") :])
    return rest if nxt is None else rest[: nxt.start() + 1]


def parse_runner_python_matrix(workflow: str) -> set[str]:
    block = runner_job_block(workflow)
    found = _MATRIX_PY.search(block)
    assert found, "runner job has no python-version matrix"
    return set(_MATRIX_ITEM.findall(found.group(1)))


def parse_runner_os_matrix(workflow: str) -> set[str]:
    block = runner_job_block(workflow)
    found = _MATRIX_OS.search(block)
    assert found, "runner job has no os matrix"
    return set(_MATRIX_ITEM.findall(found.group(1)))


def test_support_surface_doc_exists() -> None:
    assert _SUPPORT_MD.is_file(), f"missing {_SUPPORT_MD}"
    text = _SUPPORT_MD.read_text(encoding="utf-8")
    axes = parse_frozen_surface(text)
    missing = [axis for axis in _REQUIRED_AXES if axis not in axes]
    assert not missing, f"SUPPORT.md Frozen surface missing axes: {missing}"
    assert set(axes["CLI hosts"]) == _REQUIRED_HOSTS
    assert set(axes["Python"]) == _REQUIRED_PYTHON
    assert set(axes["OS"]) == _REQUIRED_OS
    lowered = text.lower()
    for token in _NON_SUPPORT:
        assert token.lower() in lowered, f"SUPPORT.md missing non-support note: {token}"


def test_ci_runner_matrix_covers_supported_python() -> None:
    workflow = _WORKFLOW.read_text(encoding="utf-8")
    support = parse_frozen_surface(_SUPPORT_MD.read_text(encoding="utf-8"))
    matrix = parse_runner_python_matrix(workflow)
    documented = set(support["Python"])
    assert matrix == _REQUIRED_PYTHON, f"runner matrix {sorted(matrix)}"
    assert documented == matrix, (
        "SUPPORT.md Python and validate.yml runner matrix drifted: "
        f"doc={sorted(documented)} ci={sorted(matrix)}"
    )

    block = runner_job_block(workflow)
    os_matrix = parse_runner_os_matrix(workflow)
    assert os_matrix == _REQUIRED_OS, f"runner os matrix {sorted(os_matrix)}"
    assert set(support["OS"]) == os_matrix, (
        "SUPPORT.md OS and validate.yml runner matrix drifted: "
        f"doc={sorted(support['OS'])} ci={sorted(os_matrix)}"
    )
    assert "ubuntu-latest" in block
    assert "windows-latest" in block
    assert "macos-" not in block
    assert "runs-on: ${{ matrix.os }}" in block

    pyproject = _PYPROJECT.read_text(encoding="utf-8")
    assert 'requires-python = ">=3.11"' in pyproject


def test_support_hosts_match_cli() -> None:
    support = parse_frozen_surface(_SUPPORT_MD.read_text(encoding="utf-8"))
    documented = set(support["CLI hosts"])
    cli = set(HOST_CHOICES)
    assert documented == _REQUIRED_HOSTS
    assert documented == cli, (
        "SUPPORT.md hosts and CLI HOST_CHOICES drifted: "
        f"doc={sorted(documented)} cli={sorted(cli)}"
    )


def test_support_surface_readme_points_at_doc() -> None:
    for path in (_ROOT_README, _RUNNER_README):
        text = path.read_text(encoding="utf-8")
        assert "docs/ship/SUPPORT.md" in text, f"{path} missing SUPPORT.md pointer"
