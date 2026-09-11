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

Rounds log and live Corrections are bounded and archived. Older `- R…`
lines rotate into `archive/rounds.md` (`KEEP_ROUNDS`, default 5). Folded
corrections rotate into `archive/directives.md` at the ledger watermark
before the supervisor appends; the live queue is capped
(`OPEN_DIRECTIVE_CAP`, default 8). Caps are read from `ops.md` when present.

`longgraph-dev-continue` is DEV-only and must not appear in product Host paths.
