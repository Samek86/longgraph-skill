from __future__ import annotations

import shutil
from pathlib import Path

import pytest

FIXTURES = Path(__file__).resolve().parent / "fixtures"


@pytest.fixture
def fixtures_root() -> Path:
    return FIXTURES


def copy_fixture(name: str, dest: Path) -> Path:
    run_dir = dest / "run"
    shutil.copytree(FIXTURES / name, run_dir)
    return run_dir
