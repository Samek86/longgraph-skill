from __future__ import annotations

import ast
import json
import os
from pathlib import Path

import pytest

from longgraph.hosts import Host, MockHost, PromptOnlyHost
from longgraph.nodes import Runner, StatusContractError, write_status
from longgraph.state import parse_run

from tests.support import copy_fixture

PACKAGE = Path(__file__).resolve().parents[1] / "longgraph"


def test_runner_never_reads_skills_dir(tmp_path: Path) -> None:
    for py in PACKAGE.glob("*.py"):
        text = py.read_text(encoding="utf-8")
        assert "skills/loop" not in text
        assert 'Path("skills")' not in text
        assert "Path('skills')" not in text

    bait = tmp_path / "skills" / "loop-graph" / "SKILL.md"
    bait.parent.mkdir(parents=True)
    bait.write_text("TRIPWIRE_DO_NOT_READ\n", encoding="utf-8")
    run_dir = copy_fixture("add-tests-to-cli", tmp_path)
    runner = Runner(run_dir, workspace=tmp_path / "ws")
    runner.run(steps=1)
    for path in runner.reads:
        assert "skills" not in path.parts
        contents = path.read_text(encoding="utf-8") if path.is_file() else ""
        assert "TRIPWIRE_DO_NOT_READ" not in contents


def test_no_peer_wakeup_api() -> None:
    banned = ("wake", "wakeup", "notify_peer", "resume_peer", "wake_peer")
    for cls in (Host, MockHost, PromptOnlyHost, Runner):
        for name in dir(cls):
            if name.startswith("_"):
                continue
            lowered = name.lower()
            assert all(token not in lowered for token in banned), f"{cls.__name__}.{name}"
    for py in PACKAGE.glob("*.py"):
        tree = ast.parse(py.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                lowered = node.name.lower()
                assert "wake" not in lowered
                assert "notify_peer" not in lowered


def test_status_atomic(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    dest = tmp_path / "status.json"
    dest.write_text("{}", encoding="utf-8")
    seen: list[tuple[str, str]] = []
    real_replace = os.replace

    def spy(src: str | os.PathLike[str], dst: str | os.PathLike[str]) -> None:
        seen.append((str(src), str(dst)))
        real_replace(src, dst)

    monkeypatch.setattr(os, "replace", spy)
    payload = {"status": "running", "metadata": {"itemRetries": {}}}
    write_status(dest, payload, ledger_run_status="active")
    assert seen
    src, dst = seen[0]
    assert src.endswith(".tmp")
    assert dst.endswith("status.json")
    assert json.loads(dest.read_text(encoding="utf-8"))["status"] == "running"

    with pytest.raises(StatusContractError):
        write_status(dest, {"status": "completed"}, ledger_run_status="active")


def test_public_surface_has_no_langgraph_import() -> None:
    for py in PACKAGE.glob("*.py"):
        tree = ast.parse(py.read_text(encoding="utf-8"), filename=str(py))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    assert not alias.name.startswith("langgraph"), py
            elif isinstance(node, ast.ImportFrom):
                mod = node.module or ""
                assert not mod.startswith("langgraph"), py
