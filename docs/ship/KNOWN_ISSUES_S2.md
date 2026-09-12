# Known issues (Ship-S2 / adversarial R2)

Residuals after the S2 re-pass and the D2 closeout PR. D2 must not
treat “Critical = 0” as “no leftovers.” Full write-up:
[`ADVERSARIAL-R2.md`](ADVERSARIAL-R2.md).

This file lives under `docs/ship/` so it does not collide with the
root [`KNOWN_ISSUES.md`](../../KNOWN_ISSUES.md).

## Major (fixed in D2 closeout)

### M-R2-1 — resolved `OB-xxx` rows still parse as live — FIXED

`_parse_owner_blocked` now skips resolved/closed wording, same as
`_parse_open_gaps`. Tests:
`test_parse_owner_blocked_skips_resolved_rows`,
`test_owner_blocked_skips_write_set_and_close` (live still blocks),
`test_resolved_owner_blocked_does_not_over_block`.

### M-R2-2 — `OPEN_DIRECTIVE_CAP` is not an append gate — FIXED

`append_correction_packet` refuses when
`len(unfolded_packets) >= OPEN_DIRECTIVE_CAP`. MockHost
rotate-before-append then honors the cap. Rotation still refuses to
archive unfolded packets.
Test: `test_open_directive_cap_refuses_append_at_cap`.

### Prior M-ADV-1 — audit-surface path bypass — FIXED

Pending-audit write-set / `Audit surface:` overlap uses normalized
paths (`relative_to` / `normpath`).
`migrations/../migrations/drop_blob.sql` cannot dodge
`migrations/drop_blob.sql`.
Test: `test_pending_audit_blocks_normalized_audit_surface_overlap`.

### Prior M-ADV-2 — OB token binding — FIXED

Live `owner_blocked` applies to this run's Current slice with no
literal `OB-xxx` token in the slice text (CONTRACT §1.6). Resolved
rows stay unblocked (M-R2-1).
Test: `test_owner_blocked_applies_without_slice_token`.

## Major (open)

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
