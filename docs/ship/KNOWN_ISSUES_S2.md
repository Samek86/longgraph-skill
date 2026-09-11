# Known issues (Ship-S2 / adversarial R2)

Residuals after the S2 re-pass on main tip `f313ed3` plus the two
Critical fixes in this PR. D2 must not treat “Critical = 0” as
“no leftovers.” Full write-up:
[`ADVERSARIAL-R2.md`](ADVERSARIAL-R2.md).

This file lives under `docs/ship/` so it does not collide with the
root `KNOWN_ISSUES.md` on unmerged PR #14.

## Major (open)

### M-R2-1 — resolved `OB-xxx` rows still parse as live

`_parse_owner_blocked` does not skip resolved/closed wording.
`_parse_open_gaps` does. A resolved OB row can keep skipping
write-set and close (fail-closed / over-block).

### M-R2-2 — `OPEN_DIRECTIVE_CAP` is not an append gate

The cap is documented as supervisor append discipline. Rotation
correctly refuses to archive unfolded packets. `append_correction_packet`
and MockHost still append past the cap.

### M-R2-3 — DualTimer Host is timer-only

`--host grok-bot` owns two independent timers and does not apply
write-sets. Close still needs an applied write-set plus gate re-pass.
No live multi-day DualTimer soak on this tip (PR #15 is out of
scope here).

## Deferred (not Major)

- Token / $ telemetry, ApiHost, prompt-compiler (EXPANSION-PLAN
  later phases).
- Schema-check of `ownerEscalation` on read.
- Per-packet explicit no-op lines for folded non-`ACCEPT-GATE`
  corrections (watermark is the current record).

## Owner-only

Git tags, GitHub Releases, live DualTimer product soaks, and merge
to `main` require owner ack. This PR must not be merged without it.
