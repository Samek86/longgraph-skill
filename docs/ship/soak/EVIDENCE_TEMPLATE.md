# Soak evidence template

Filled by `scripts/ship-soak.sh` as `SUMMARY.md` + `summary.json` under
`.longgraph-ship/soak/<run-id>/`.

## `summary.json`

```json
{
  "run_id": "YYYYMMDDTHHMMSSZ",
  "host": "mock",
  "rounds": 50,
  "passed": true,
  "fixtures": ["add-tests-to-cli", "migrate-blob-storage", "scout-library-choice"],
  "totals": {
    "scoreboard_pollution": 0,
    "reclose_storm": 0,
    "timer_zombie": 0,
    "owner_escalation_auto": 0,
    "uncaught_exception": 0
  },
  "source_faults": [],
  "results": [],
  "evidence_dir": ".longgraph-ship/soak/<run-id>"
}
```

`timer_zombie` stays 0 with `timer_zombie_status: not_exercised` unless a
DualTimer / terminal-recreate path is actually ticked.

## `SUMMARY.md`

Human copy of the same totals plus per-fixture ticks, final `status.json`
status, `stopped_reason`, and fault list. Attach this file for D2.

## Per-fixture traces

| File | Host | Contents |
|---|---|---|
| `fixtures/<name>/ticks.jsonl` | mock | one JSON object per tick |
| `fixtures/<name>/emit.txt` | prompt-only | one line per emit |
| `fixtures/<name>/final-status.json` | both | copy of isolated `status.json` |
