# Known issues

Residuals after Phase 0–1c, DISTRIBUTION H0–H2, the D2 coding
closeout, the S5 support-surface freeze, and the tip containment
pass (M-TIP-1 / M-TIP-2). D1 closeout binds public claims to CI.
D2 coding Majors M-R2-1 / M-R2-2 (and the prior audit-path /
OB-token holes) are fixed in this tree; live DualTimer soak
(M-R2-3) is still owner evidence. See
[public claims](docs/ship/PUBLIC_CLAIMS.md),
[support surface](docs/ship/SUPPORT.md),
[`docs/ship/KNOWN_ISSUES_S2.md`](docs/ship/KNOWN_ISSUES_S2.md), and
[`docs/runner/CONTRACT.md`](docs/runner/CONTRACT.md).

## Tip containment (fixed)

### M-TIP-1 — workspace hardlink alias clobber — FIXED

`Path.resolve` already followed a workspace symlink to
`run_dir/ledger.md` (deny via `relative_to` / protected name). A
hardlink keeps a workspace path and shares the inode, so write-set
could overwrite the scoreboard. The write gate now denies
`os.path.samefile` aliases to `ledger.md` / `directives.md` /
`ops.md` / `status.json`.
Test: `test_executor_cannot_clobber_scoreboard_via_hardlink`.

### M-TIP-2 — ACCEPT-GATE fold after any applied path — FIXED

Pre-apply same-tick next-milestone release stays on the applied-work
Host path (MockHost, or `Host.applies_write_set`). After any
`NodeResult.applied` tick the runner folds a live `ACCEPT-GATE`
packet regardless of Host. Other packets still fold on close.
Emit-only / timer-only hosts still never apply, so they never fold
— that is a Host capability limit, not a forged pass.
Test: `test_accept_gate_folds_after_applied_non_mock_host`.

## D2 blocked — soak / DualTimer capability

No multi-day soak on live DualTimer product agents (M-R2-3 /
M-S3-3). Coding Majors from Ship-S2 / S3 that this tree can close
are closed: resolved OB rows are not live; `OPEN_DIRECTIVE_CAP`
refuses append-at-cap; pending-audit overlap uses normalized paths;
live OBs bind without a slice token. This tree does not fabricate
soak logs.

## Support surface — Linux + Python 3.11/3.12 only

CI and product claims are **`ubuntu-latest` (Linux)** plus Python
**3.11 and 3.12**. `requires-python = ">=3.11"` is the install floor;
3.13+ and macOS / Windows are not matrix-proven and are not
supported. This freeze is not soak evidence.

## DualTimer Host is timer-only

`GrokBotDualTimerHost` (`--host grok-bot`) owns two independent timers
and does **not** apply write-sets. Close still requires an applied
write-set plus gate re-pass (MockHost in tests; a future Host that
applies work). Timer-only ticks never close —
`test_dual_timer_host_never_closes`.

## Token / $ telemetry deferred

Phase 2 / token-cost telemetry is out of scope
([`docs/runner/EXPANSION-PLAN.md`](docs/runner/EXPANSION-PLAN.md)).
No public claim binds a dollar or token figure.

## M8-style residuals

Scanned the collected suite for tests that freeze pre-H2 lies
(pending-audit over-stop of all work, unrotated `### Round N`, dead
directive fold).

- `test_pending_audit_blocks_advancement` still requires a
  **next-milestone** write-set to stop. That matches CONTRACT §1.4 /
  A8 after H2. Lane-continue is
  `test_pending_audit_allows_lane_work`. The old name was not
  rewritten.
- No other green contract test was clearly wrong versus current
  code. This slice does not casually rewrite them.

## Owner-only

Git tags, GitHub Releases, and live DualTimer product soaks are
owner-only. Agents must not create tags.
