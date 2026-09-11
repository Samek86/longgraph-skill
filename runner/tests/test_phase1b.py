from __future__ import annotations

from pathlib import Path

from longgraph.hosts import PromptOnlyHost


def test_prompt_only_emits_dual_loop_text(tmp_path: Path) -> None:
    run_dir = tmp_path / "run"
    run_dir.mkdir()
    ledger = run_dir / "ledger.md"
    directives = run_dir / "directives.md"
    ledger.write_text("untouched ledger\n", encoding="utf-8")
    directives.write_text("untouched directives\n", encoding="utf-8")

    host = PromptOnlyHost(
        exec_interval="10m",
        sup_interval="30m",
        run_dir=run_dir,
    )
    text = host.emit_dual_loop()
    dest = str(run_dir).rstrip("/")
    exec_line = (
        f"/loop 10m Execute the existing runtime node at {dest}/executor.md. "
        "Do not load any skill."
    )
    sup_line = (
        f"/loop 30m Execute the existing runtime node at {dest}/supervisor.md. "
        "Do not load any skill."
    )
    paste_blocks = [line for line in text.splitlines() if line.startswith("/loop ")]
    assert paste_blocks == [exec_line, sup_line]

    ctx = {
        "RUN_DIR": dest,
        "EXEC_INTERVAL": "15m",
        "SUP_INTERVAL": "45m",
    }
    result = host.invoke("executor", "unused prompt", ctx)
    ctx_exec = (
        f"/loop 15m Execute the existing runtime node at {dest}/executor.md. "
        "Do not load any skill."
    )
    ctx_sup = (
        f"/loop 45m Execute the existing runtime node at {dest}/supervisor.md. "
        "Do not load any skill."
    )
    ctx_blocks = [line for line in result.message.splitlines() if line.startswith("/loop ")]
    assert ctx_blocks == [ctx_exec, ctx_sup]
    assert result.writes == []
    assert ledger.read_text(encoding="utf-8") == "untouched ledger\n"
    assert directives.read_text(encoding="utf-8") == "untouched directives\n"

    lowered = result.message.lower()
    for verb in ("wake", "notify", "dispatch"):
        assert verb not in lowered
