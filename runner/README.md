# longgraph runner (Phase 1a / 1b / 1c + DISTRIBUTION H0–H2 / Ship-S)

Engine for compiled run directories. The skill library under `skills/` is
policy only — this package never loads it.

**AI / agent instruction:** always invoke the CLI explicitly
(`longgraph run --host …`). Do **not** treat skill compile, `/longgraph`,
or a `/loop` paste as starting the runner. Skill-only is not the default
engine path on this fork and does not harden gates.

Authority: [`docs/runner/AUTHORITY.md`](../docs/runner/AUTHORITY.md).
Security: [`SECURITY.md`](../SECURITY.md).
Ship claims (CI-bound): [`docs/ship/PUBLIC_CLAIMS.md`](../docs/ship/PUBLIC_CLAIMS.md).
Support surface (S5): [`docs/ship/SUPPORT.md`](../docs/ship/SUPPORT.md).
Changelog: [`CHANGELOG.md`](../CHANGELOG.md).
Residuals: [`KNOWN_ISSUES.md`](../KNOWN_ISSUES.md).
Negative battery (Ship-S3): [`docs/ship/NEGATIVE-BATTERY.md`](../docs/ship/NEGATIVE-BATTERY.md).

Distribution string: `0.4.0-rc.1` (in `pyproject.toml`) on `main`.
Tag `0.4.0-rc.1` and its GitHub prerelease already exist; do not
chase SHAs. New tags and Releases stay owner-only.
Go/No-Go: [`docs/ship/D2-GO-NOGO.md`](../docs/ship/D2-GO-NOGO.md).
Multi-fixture soak harness (Ship-S1):
[`docs/ship/SOAK.md`](../docs/ship/SOAK.md). Tip mock N=50 tick evidence
is in [`docs/ship/soak/tip-5de40a9-n50-mock/`](../docs/ship/soak/tip-5de40a9-n50-mock/).
Live DualTimer / ≥24h wall-clock soak stays owner-only.

## Host capability table

| CLI `--host` | Class | Emit | Apply write-set | Owns timers | Serial peer ticks |
|---|---|---|---|---|---|
| `prompt-only` (**safe default**) | `PromptOnlyHost` | dual `/loop` paste blocks | no | no | n/a (emit and exit) |
| `grok-bot` (product DualTimer) | `GrokBotDualTimerHost` | no | no (timer-only) | yes | **no** — independent timers, no peer wake |
| `mock` (tests only) | `MockHost` | no | yes | no | yes — coupled executor→supervisor→scout |

`longgraph run` without `--host` is **emit-only** (`prompt-only`). It does
**not** silently default to MockHost as the product path.

## Support surface

| Axis | Supported (CI-bound) |
|---|---|
| CLI `--host` | `prompt-only` (safe default), `grok-bot` (DualTimer, timer-only), `mock` (tests only) |
| Python | 3.11, 3.12 |
| OS | ubuntu-latest (Linux) |

Full freeze + explicit non-support:
[`docs/ship/SUPPORT.md`](../docs/ship/SUPPORT.md). macOS / Windows and
Python 3.13+ are not matrix-proven and are not supported. The venv
`Scripts\activate` hint below is a shell path, not a platform claim.

Close is **Default-FAIL**: gate re-pass after an applied write-set. Emit-only
and timer-only ticks never close. Product Verify/smoke is a fail-closed
subprocess (`cwd` = workspace).

## 5-minute quickstart

```bash
cd runner
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
python -m pip install -e ".[dev]"
python -m pytest
```

Use a **copy** of a compiled run directory (or a fixture). `--host mock`
writes `status.json` and creates `workspace/` under the run dir — do not
point it at `tests/fixtures/`.

```bash
cp -R tests/fixtures/add-tests-to-cli /tmp/add-tests-to-cli

# 1. Safe default — emit two /loop paste blocks; no writes, no coupled loop
longgraph run --host prompt-only /tmp/add-tests-to-cli
#    omitting --host is the same (defaults to prompt-only)

# 2. Product DualTimer — two independent timers, no peer wake
longgraph run --host grok-bot /tmp/add-tests-to-cli

# 3. MockHost coupled test loop — not the product path; copy first
longgraph run --host mock /tmp/add-tests-to-cli

longgraph status /tmp/add-tests-to-cli
longgraph stop /tmp/add-tests-to-cli
```

Contributor dry-run (DISTRIBUTION S4): [`docs/ship/DOCS-DRY-RUN.md`](../docs/ship/DOCS-DRY-RUN.md).

Executor write-set paths resolve inside the workspace and cannot clobber
`run_dir` scoreboard files (`ledger.md`, `directives.md`, `ops.md`,
`status.json`) via relative escape, symlink, or hardlink/alias; runner
close remains the only ledger writer.
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
Current-slice `owner_blocked` do not close: any live `OB-xxx` applies
to this run's Current slice (no literal token required). Resolved or
closed owner-blocked rows are not live and must not over-block.
`blocked-on` with missing findings is scout-only (MockHost). DualTimer
hosts do not drive supervisor/scout from the executor branch.

Rounds log and live Corrections are bounded and archived. Older `- R…`
lines **and** `### Round N` sections rotate into `archive/rounds.md`
(`KEEP_ROUNDS`, default 5). On an applied executor tick (any Host that
sets `NodeResult.applied`), a live `ACCEPT-GATE` packet is folded
immediately. Other live corrections fold on close with the round write.
Close may fold again; a second pass is a no-op. Folded
corrections then rotate into `archive/directives.md` at that watermark
before the supervisor appends. `OPEN_DIRECTIVE_CAP` (default 8) is
append discipline — the append helper refuses once the unfolded queue
is at the cap; it does not archive unfolded packets. Caps are read
from `ops.md` when present. A live `ACCEPT-GATE` correction (or first-line
verb `accept-gate`) is the only runner path that flips
`milestone_gate: pending-audit` to `passed`. Disjoint registered lane
work may continue while the gate is pending. Write-set / audit-surface
overlap uses normalized paths (`.` / `..` cannot dodge the surface) and
denies a workspace hardlink or symlink alias to a surface dest.

`longgraph-dev-continue` is DEV-only and must not appear in product Host paths.
