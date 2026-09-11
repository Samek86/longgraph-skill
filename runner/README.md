# longgraph runner (Phase 1a MockHost / Phase 1b PromptOnlyHost / Phase 1c GrokBotDualTimerHost)

Engine for compiled run directories. The skill library under `skills/` is
policy only — this package never loads it.

Authority: [`docs/runner/AUTHORITY.md`](../docs/runner/AUTHORITY.md).

```bash
cd runner
python -m pip install -e ".[dev]"
python -m pytest
longgraph run|status|stop <run_dir>
longgraph run --host prompt-only <run_dir>
```

Default host is MockHost (no model). `--host prompt-only` prints the two
`/loop` paste blocks and does not call a model or write ledger/directives.
`GrokBotDualTimerHost` schedules two independent timers (executor +
supervisor) with no wake edge between them. Close is gate re-pass only.

`longgraph-dev-continue` is DEV-only and must not appear in product Host paths.
