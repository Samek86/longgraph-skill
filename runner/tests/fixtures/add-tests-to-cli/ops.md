# taskcat — Environment & Ops Facts

> Read the index first, then only the row needed by the current ledger item.

## Context index

| ID | Use when | Read | Verify |
| --- | --- | --- | --- |
| C-01 | date parser / GAP-002 | docs/date-formats.md; date util | pytest tests/test_dates.py -q |

Always-hot: `ledger.md` status/current slice + directives above the watermark.

## Build / test

- smoke: pytest -q
- narrow: pytest tests/test_dates.py -q

## Runner budget

max_rounds: 20
max_retries: 3
smoke: pytest -q

## Timers

| Node | Interval | Timer ID |
| --- | --- | --- |
| executor | 10m | pending |
| supervisor | 30m | pending |
