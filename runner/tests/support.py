from __future__ import annotations

import shutil
from pathlib import Path

FIXTURES = Path(__file__).resolve().parent / "fixtures"


def copy_fixture(name: str, dest: Path) -> Path:
    run_dir = dest / "run"
    shutil.copytree(FIXTURES / name, run_dir)
    return run_dir
