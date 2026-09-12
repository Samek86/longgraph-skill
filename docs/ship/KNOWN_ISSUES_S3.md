# Known issues (Ship-S3 / negative battery)

Residuals after the S3 battery on main tip `f313ed3` plus the two
Critical fixes in this PR. D2 must not treat “Critical = 0” as
“no leftovers.” Full battery:
[`NEGATIVE-BATTERY.md`](NEGATIVE-BATTERY.md).

This file lives under `docs/ship/` so it does not collide with the
root `KNOWN_ISSUES.md` on unmerged PR #14.

## Major (open)

### M-S3-1 — resolved `OB-xxx` rows still parse as live

`_parse_open_gaps` skips `_CLOSED_WORDS` (`resolved` / `closed` /
`closure`). `_parse_owner_blocked` does not. A resolved OB row can
keep skipping write-set and close (fail-closed / over-block, not a
forged close). S3-07 still holds for a **live** Current-slice OB.

### M-S3-2 — `OPEN_DIRECTIVE_CAP` is not an append gate

The cap is documented as supervisor append discipline. Rotation
correctly refuses to archive unfolded packets.
`append_correction_packet` and MockHost still append past the cap.
Not a forged close; product DualTimer does not append corrections
itself (timer-only).

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
