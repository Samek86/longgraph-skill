# Soak evidence `tip-5de40a9-n50-mock`

- tip SHA: `5de40a9` (`5de40a977844bcb59b661270c3c5dab08b0e3a6c`)
- host: `mock`
- rounds per fixture: 50 (N≥50 tick budget)
- fixtures: add-tests-to-cli, migrate-blob-storage, scout-library-choice
- command: `bash scripts/ship-soak.sh --rounds 50 --host mock`
- protocol: [`docs/ship/SOAK.md`](../../SOAK.md)
- passed: **yes**

Harness output (compact traces only; isolated work trees deleted). DualTimer /
`grok-bot` was **not** exercised. Live DualTimer multi-day / ≥24h wall-clock
soak remains owner-only — this pack is mock tick evidence, not a fabricated
timer soak.

## Totals (must all be 0 to pass)

- scoreboard pollution: 0
- re-close storm: 0
- timer zombie: 0 (not_exercised / N/A — mock path)
- owner escalation auto-acked: 0 (manual-only)
- uncaught exception: 0
- max_rounds: clean (`completedRounds` never exceeded `ops.max_rounds` without a clean stop)

## Per fixture

### add-tests-to-cli

- passed: True
- ticks: 50/50
- final status: failed
- stopped_reason: max_retries
- faults: none

### migrate-blob-storage

- passed: True
- ticks: 50/50
- final status: running
- stopped_reason: None
- faults: none

### scout-library-choice

- passed: True
- ticks: 50/50
- final status: failed
- stopped_reason: max_retries
- faults: none
