# Known issues (Ship-S3 / negative battery)

Residuals after the S3 battery and the D2 closeout PR. D2 must not
treat “Critical = 0” as “no leftovers.” Full battery:
[`NEGATIVE-BATTERY.md`](NEGATIVE-BATTERY.md).

This file lives under `docs/ship/` so it does not collide with the
root [`KNOWN_ISSUES.md`](../../KNOWN_ISSUES.md).

## Major (fixed in D2 closeout)

### M-S3-1 — resolved `OB-xxx` rows still parse as live — FIXED

Same hole as M-R2-1. `_parse_owner_blocked` now skips `_CLOSED_WORDS`.
S3-07 still holds for a **live** Current-slice OB.
Tests: `test_parse_owner_blocked_skips_resolved_rows`,
`test_resolved_owner_blocked_does_not_over_block`,
`test_owner_blocked_skips_write_set_and_close`.

### M-S3-2 — `OPEN_DIRECTIVE_CAP` is not an append gate — FIXED

Same hole as M-R2-2. `append_correction_packet` and MockHost refuse
when the unfolded queue is at the cap. Product DualTimer does not
append corrections itself (timer-only).
Test: `test_open_directive_cap_refuses_append_at_cap`.

## Tip (fixed after D2)

### M-TIP-1 — workspace hardlink alias clobber — FIXED

Same hole class as S3-01 / P3, plus inode alias. Write-set cannot
clobber scoreboard files via hardlink or symlink.
Test: `test_executor_cannot_clobber_scoreboard_via_hardlink`.

### M-TIP-2 — ACCEPT-GATE fold after any applied path — FIXED

ACCEPT-GATE fold is runner-owned after any applied write-set.
Other packets still fold on close. DualTimer remains timer-only
(M-S3-3) and does not apply, so it does not fold.
Test: `test_accept_gate_folds_after_applied_non_mock_host`.

## Major (open)

### M-S3-3 — DualTimer Host is timer-only

`--host grok-bot` owns two independent timers and does not apply
write-sets. S3-08 requires that a timer-only tick never closes —
already proven. Residual is capability, not a forged close. Live
multi-day DualTimer soak is out of scope here (PR #15).

## Deferred (not Major)

- Token / $ telemetry, ApiHost, prompt-compiler (EXPANSION-PLAN
  later phases).
- Schema-check of `ownerEscalation` on read.
- Per-packet explicit no-op lines for folded non-`ACCEPT-GATE`
  corrections (watermark is the current record).
- SIGKILL mid-verify harness (P9 is the verify-green resume gate).

## Owner-only

Git tags, GitHub Releases, live DualTimer product soaks, and merge
to `main` require owner ack. This PR must not be merged without it.
