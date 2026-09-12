# Known issues

Residuals after Phase 0–1c, DISTRIBUTION H0–H2, and the D2 coding
closeout. D1 closeout binds public claims to CI. D2 coding Majors
M-R2-1 / M-R2-2 (and the prior audit-path / OB-token holes) are
fixed in this tree; live DualTimer soak (M-R2-3) is still owner
evidence. See [public claims](docs/ship/PUBLIC_CLAIMS.md),
[`docs/ship/KNOWN_ISSUES_S2.md`](docs/ship/KNOWN_ISSUES_S2.md), and
[`docs/runner/CONTRACT.md`](docs/runner/CONTRACT.md).

## D2 blocked — soak / DualTimer capability

No multi-day soak on live DualTimer product agents (M-R2-3 /
M-S3-3). Coding Majors from Ship-S2 / S3 that this tree can close
are closed: resolved OB rows are not live; `OPEN_DIRECTIVE_CAP`
refuses append-at-cap; pending-audit overlap uses normalized paths;
live OBs bind without a slice token. This tree does not fabricate
soak logs.

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
