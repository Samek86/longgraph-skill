"""Windows-native path containment and portable gates (Phase 0–1c).

These tests run on every OS. Drive-letter / case-fold probes skip off
Windows. Junction/symlink creation still uses the existing skip helper
when the platform cannot create the link type.
"""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from longgraph.gates import GateRunner, portable_gate_argv
from longgraph.hosts import EdgeWriter, WriteDenied
from longgraph.nodes import Runner, _workspace_declared_alias
from longgraph.state import (
    contained_in,
    findings_relpath,
    normalize_declared_path,
    safe_findings_ident,
)

from tests.support import copy_fixture


def test_normalize_declared_path_collapses_backslashes() -> None:
    assert (
        normalize_declared_path(r"migrations\..\migrations\drop_blob.sql")
        == "migrations/drop_blob.sql"
    )
    assert normalize_declared_path("docs/../docs/lane-policy.md") == "docs/lane-policy.md"


def test_normalize_declared_path_does_not_make_abs_look_relative() -> None:
    """An absolute / drive / UNC spelling must not collapse into a relative."""
    posix_abs = normalize_declared_path("/etc/passwd")
    assert posix_abs.startswith("/") or ":" in posix_abs
    assert not posix_abs.startswith("etc/")
    drive = normalize_declared_path("C:/Windows/system32/cmd.exe")
    assert "Windows" in drive or "windows" in drive.lower()
    assert not drive.startswith("Windows/")


def test_findings_ident_rejects_windows_separators() -> None:
    assert safe_findings_ident(r"..\decoy") is None
    assert safe_findings_ident(r"foo\bar") is None
    assert findings_relpath(r"findings#..\decoy") is None
    assert findings_relpath("findings#s3-client") == "findings/s3-client.md"


def test_contained_in_is_fail_closed(tmp_path: Path) -> None:
    root = tmp_path / "ws"
    root.mkdir()
    inside = root / "a" / "b.txt"
    inside.parent.mkdir()
    inside.write_text("ok\n", encoding="utf-8")
    assert contained_in(inside, root) is True
    assert contained_in(tmp_path / "outside.txt", root) is False
    assert contained_in(root / ".." / "outside.txt", root) is False


def test_true_false_gates_are_portable(tmp_path: Path) -> None:
    assert portable_gate_argv("true") is not None
    assert portable_gate_argv("false") is not None
    assert portable_gate_argv("pytest -q") is None
    product = GateRunner()
    green = product.run("true", tmp_path)
    red = product.run("false", tmp_path)
    assert green.passed is True
    assert red.passed is False
    assert red.skipped is False


def test_workspace_alias_detects_same_resolved_location(tmp_path: Path) -> None:
    ws = tmp_path / "ws"
    (ws / "migrations").mkdir(parents=True)
    surface = ws / "migrations" / "drop_blob.sql"
    surface.write_text("-- surface\n", encoding="utf-8")
    assert _workspace_declared_alias(
        "migrations/../migrations/drop_blob.sql",
        "migrations/drop_blob.sql",
        ws,
    )


def test_write_set_denies_destination_outside_workspace(tmp_path: Path) -> None:
    run_dir = copy_fixture("add-tests-to-cli", tmp_path)
    workspace = run_dir / "workspace"
    workspace.mkdir(parents=True, exist_ok=True)
    writer = EdgeWriter(run_dir, workspace)
    outside = tmp_path / "other-root" / "pwned.txt"
    with pytest.raises(WriteDenied):
        writer.write("executor", outside, "pwned\n", write_set=True)
    assert not outside.exists()


@pytest.mark.skipif(os.name != "nt", reason="Windows drive-letter containment")
def test_write_set_denies_other_drive(tmp_path: Path) -> None:
    run_dir = copy_fixture("add-tests-to-cli", tmp_path)
    workspace = run_dir / "workspace"
    workspace.mkdir(parents=True, exist_ok=True)
    writer = EdgeWriter(run_dir, workspace)
    here = str(workspace.resolve())[0].upper()
    other = "D" if here != "D" else "E"
    dest = Path(f"{other}:/longgraph-pwned.txt")
    with pytest.raises(WriteDenied):
        writer.write("executor", dest, "pwned\n", write_set=True)


@pytest.mark.skipif(os.name != "nt", reason="NTFS case-insensitive scoreboard")
def test_executor_cannot_clobber_scoreboard_via_casefold(tmp_path: Path) -> None:
    run_dir = copy_fixture("add-tests-to-cli", tmp_path)
    workspace = run_dir
    writer = EdgeWriter(run_dir, workspace)
    before = (run_dir / "ledger.md").read_text(encoding="utf-8")
    with pytest.raises(WriteDenied):
        writer.write("executor", run_dir / "LEDGER.md", "tampered\n", write_set=True)
    assert (run_dir / "ledger.md").read_text(encoding="utf-8") == before


def test_junction_or_symlink_alias_is_audit_surface(tmp_path: Path) -> None:
    """Junction (Windows) or symlink (POSIX) to the audit dest is an alias."""
    ws = tmp_path / "ws"
    surface_dir = ws / "migrations"
    surface_dir.mkdir(parents=True)
    surface = surface_dir / "drop_blob.sql"
    surface.write_text("-- audit surface\n", encoding="utf-8")
    alias_dir = ws / "lane"
    try:
        if os.name == "nt" and hasattr(alias_dir, "is_junction"):
            os.symlink(surface_dir, alias_dir, target_is_directory=True)
        else:
            alias_dir.symlink_to(surface_dir, target_is_directory=True)
    except OSError as exc:
        pytest.skip(f"directory link unsupported here: {exc}")
    assert _workspace_declared_alias("lane/drop_blob.sql", "migrations/drop_blob.sql", ws)
    runner_ws = ws
    assert _workspace_declared_alias(
        "lane/drop_blob.sql",
        "migrations/drop_blob.sql",
        runner_ws,
    )


def test_runner_findings_path_stays_under_findings(tmp_path: Path) -> None:
    run_dir = copy_fixture("scout-library-choice", tmp_path)
    runner = Runner(run_dir, workspace=tmp_path / "ws")
    # Escape via a crafted relative that parse would reject; belt-and-suspenders
    # on the runner containment helper.
    runner_state = runner._state()
    runner_state.findings_path = "../ledger.md"
    assert runner._findings_ready(runner_state) is False
