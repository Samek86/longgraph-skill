"""Ship-S1: smoke the multi-fixture soak harness (short N, three fixtures)."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
SCRIPT = REPO / "scripts" / "ship-soak.sh"
SCRIPT_PY = REPO / "scripts" / "ship_soak.py"


def test_soak_harness_smoke_three_fixtures(tmp_path: Path) -> None:
    out = tmp_path / "soak-evidence"
    env = os.environ.copy()
    runner = str(REPO / "runner")
    env["PYTHONPATH"] = runner + (os.pathsep + env["PYTHONPATH"] if env.get("PYTHONPATH") else "")
    assert SCRIPT.is_file()
    assert SCRIPT_PY.is_file()
    # Drive the Python entry (Windows-native). The bash wrapper is a thin exec.
    proc = subprocess.run(
        [
            sys.executable,
            str(SCRIPT_PY),
            "--rounds",
            "2",
            "--host",
            "mock",
            "--out",
            str(out),
        ],
        cwd=REPO,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0, proc.stdout + "\n" + proc.stderr
    summary_md = out / "SUMMARY.md"
    summary_json = out / "summary.json"
    assert summary_md.is_file()
    assert summary_json.is_file()
    payload = json.loads(summary_json.read_text(encoding="utf-8"))
    assert payload["passed"] is True
    assert payload["rounds"] == 2
    assert payload["host"] == "mock"
    assert set(payload["fixtures"]) == {
        "add-tests-to-cli",
        "migrate-blob-storage",
        "scout-library-choice",
    }
    assert payload["totals"]["scoreboard_pollution"] == 0
    assert payload["totals"]["reclose_storm"] == 0
    assert payload["totals"]["timer_zombie"] == 0
    assert payload["totals"]["owner_escalation_auto"] == 0
    assert payload["totals"]["uncaught_exception"] == 0
    for name in payload["fixtures"]:
        assert (out / "fixtures" / name / "ticks.jsonl").is_file()
        assert (out / "fixtures" / name / "final-status.json").is_file()
