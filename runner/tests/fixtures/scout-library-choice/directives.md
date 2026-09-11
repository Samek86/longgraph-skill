# shutterlog — Directives (supervisor → executor, one-way)

## Supervisor state (updated in place; executor ignores)

Last completed tick: 2025-01-15 | audited through round: 2 | repo tips: pending

## STANDING — authority only (always in force; treat like red lines)

(none yet)

## Corrections (numbered; live queue = not-yet-folded only)

D-003 · 2025-01-15 — dispatch scout: brief `s3-client`.
  Question: which S3-compatible client library for Python fits our constraints?
  Context: requirements in ops.md (async, <5MB dep, streaming uploads, no C extension).
  Constraints: must support MinIO + AWS S3; must have async interface; actively maintained (commit in last 90d).
  Cap: 8000 tokens.
