# Known issues

Residuals after Phase 0–1c and DISTRIBUTION H0–H2. D1 closeout binds
public claims to CI; it does **not** close D2. See
[public claims](docs/ship/PUBLIC_CLAIMS.md) and
[`docs/runner/CONTRACT.md`](docs/runner/CONTRACT.md).

## D2 blocked — soak / adversarial re-pass

No multi-day soak on live DualTimer product agents. The original
adversarial Grok review has not been re-run against post-H2 code.
D2 stays blocked until the owner collects that evidence. This tree
does not fabricate soak logs or re-run an external review.

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
