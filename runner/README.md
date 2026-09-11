# longgraph runner (Phase 1a / 1b / 1c + DISTRIBUTION H0–H2 / Ship-S)

Engine for compiled run directories. The skill library under `skills/` is
policy only — this package never loads it.

Authority: [`docs/runner/AUTHORITY.md`](../docs/runner/AUTHORITY.md).
Security: [`SECURITY.md`](../SECURITY.md).
Ship claims (CI-bound): [`docs/ship/PUBLIC_CLAIMS.md`](../docs/ship/PUBLIC_CLAIMS.md).
Changelog: [`CHANGELOG.md`](../CHANGELOG.md).
Residuals: [`KNOWN_ISSUES.md`](../KNOWN_ISSUES.md).

Distribution string: `0.3.0-beta` (in `pyproject.toml`; **not tagged**
from this tree). This is **Ship-S / D1 closeout** after H2. Soak /
GitHub Release stay owner-only.

## Host capability table

| CLI `--host` | Class | Emit | Apply write-set | Owns timers | Serial peer ticks |
|---|---|---|---|---|---|
| `prompt-only` (**safe default**) | `PromptOnlyHost` | dual `/loop` paste blocks | no | no | n/a (emit and exit) |
| `grok-bot` (product DualTimer) | `GrokBotDualTimerHost` | no | no (timer-only) | yes | **no** — independent timers, no peer wake |
| `mock` (tests only) | `MockHost` | no | yes | no | yes — coupled executor→supervisor→scout |

`longgraph run` without `--host` is **emit-only** (`prompt-only`). It does
**not** silently default to MockHost as the product path.

Close is **Default-FAIL**: gate re-pass after an applied write-set. Emit-only
and timer-only ticks never close. Product Verify/smoke is a fail-closed
subprocess (`cwd` = workspace).

## 5-minute quickstart

```bash
cd runner
python -m pip install -e ".[dev]"
python -m pytest
```

Use a compiled run directory (or a fixture):

```bash
# 1. Safe default — emit two /loop paste blocks; no writes, no coupled loop
longgraph run --host prompt-only tests/fixtures/add-tests-to-cli
#    omitting --host is the same (defaults to prompt-only)

# 2. Product DualTimer — two independent timers, no peer wake
longgraph run --host grok-bot tests/fixtures/add-tests-to-cli

# 3. MockHost coupled test loop — not the product path
longgraph run --host mock tests/fixtures/add-tests-to-cli

longgraph status <run_dir>
longgraph stop <run_dir>
```

Executor write-set paths resolve inside the workspace and cannot clobber
`run_dir` scoreboard files (`ledger.md`, `directives.md`, `ops.md`,
`status.json`); runner close remains the only ledger writer.
`GrokBotDualTimerHost` schedules two independent timers (executor +
supervisor) with no wake edge between them. A terminal ledger stops each
node's timer without reseeding; scout ticks are a no-op. Close is gate
re-pass only after an applied write-set; emit-only and timer-only ticks
never close.
Green close rewrites the live scoreboard so the item leaves the
register. Product Verify/smoke is a fail-closed subprocess
(`cwd` = workspace): non-zero exit fails; empty Verify fails; `n/a`
skips (does not pass). CLI / `longgraph run` does not default
`GateRunner` to `passed=True`. Empty / `n/a` Verify and live
Current-slice `owner_blocked` do not close. `blocked-on` with missing
findings is scout-only (MockHost). DualTimer hosts do not drive
supervisor/scout from the executor branch.

Rounds log and live Corrections are bounded and archived. Older `- R…`
lines **and** `### Round N` sections rotate into `archive/rounds.md`
(`KEEP_ROUNDS`, default 5). On an applied executor tick, live corrections
above `Last directive folded` are folded (apply or no-op) and the
watermark advances in the same ledger write as the round. Folded
corrections then rotate into `archive/directives.md` at that watermark
before the supervisor appends. `OPEN_DIRECTIVE_CAP` (default 8) is
append discipline — it does not archive unfolded packets. Caps are read
from `ops.md` when present. A live `ACCEPT-GATE` correction (or first-line
verb `accept-gate`) is the only runner path that flips
`milestone_gate: pending-audit` to `passed`. Disjoint registered lane
work may continue while the gate is pending.

`longgraph-dev-continue` is DEV-only and must not appear in product Host paths.
