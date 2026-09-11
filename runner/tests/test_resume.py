from __future__ import annotations

import json
from pathlib import Path

import pytest

from longgraph.gates import GateRunner
from longgraph.hosts import MockHost
from longgraph.nodes import CrashBeforeClose, Runner

from tests.support import copy_fixture

_ITEM = "GAP-002"
_CLOSED_MARK = f"<!-- runner closed {_ITEM} -->"
_VERIFY = "pytest tests/test_dates.py -q"
_SMOKE = "pytest -q"


def _status(run_dir: Path) -> dict:
    return json.loads((run_dir / "status.json").read_text(encoding="utf-8"))


def test_verify_green_crash_resumes_verify_only(tmp_path: Path) -> None:
    run_dir = copy_fixture("add-tests-to-cli", tmp_path)
    workspace = tmp_path / "ws"
    host = MockHost()
    gates = GateRunner(default=True)

    crashed = Runner(
        run_dir,
        host=host,
        gates=gates,
        workspace=workspace,
        crash_before_close=True,
    )
    with pytest.raises(CrashBeforeClose, match="verify-green-then-crash-before-close"):
        crashed.run(steps=1)

    assert _ITEM not in crashed.closed_items
    status = _status(run_dir)
    assert _ITEM not in (status.get("metadata") or {}).get("closedItems", [])
    assert _CLOSED_MARK not in (run_dir / "ledger.md").read_text(encoding="utf-8")

    last = status["metadata"]["lastAttempt"]
    assert last["phase"] == "verify_green"
    assert last["key"]["runId"] == status["runId"] == "2026-07-28-taskcat-tests"
    assert last["key"]["round"] == 3
    assert last["key"]["item_id"] == _ITEM

    write_set = workspace / "tests" / "test_dates.py"
    assert write_set.is_file()
    marker = "# resume-must-not-reapply-write-set\n"
    write_set.write_text(write_set.read_text(encoding="utf-8") + marker, encoding="utf-8")

    assert host.invocations.count("executor") == 1
    assert gates.calls.count(_VERIFY) == 1
    assert gates.calls.count(_SMOKE) == 1

    resumed = Runner(
        run_dir,
        host=host,
        gates=gates,
        workspace=workspace,
        crash_before_close=False,
    )
    out = resumed.run(steps=1)

    assert host.invocations.count("executor") == 1
    assert gates.calls.count(_VERIFY) == 2
    assert gates.calls.count(_SMOKE) == 1

    assert _ITEM in resumed.closed_items
    assert _ITEM in (out["metadata"].get("closedItems") or [])
    assert out["metadata"]["lastAttempt"]["phase"] == "closed"
    assert out["metadata"]["lastAttempt"]["key"]["runId"] == "2026-07-28-taskcat-tests"
    assert out["metadata"]["lastAttempt"]["key"]["round"] == 3
    assert out["metadata"]["lastAttempt"]["key"]["item_id"] == _ITEM
    assert _CLOSED_MARK in (run_dir / "ledger.md").read_text(encoding="utf-8")
    assert marker in write_set.read_text(encoding="utf-8")
