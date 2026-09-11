# shutterlog — Environment & Ops Facts

## Context index

| ID | Use when | Read | Verify |
| --- | --- | --- | --- |
| C-01 | M3 cutover / OB-001 | attachments schema; object-store listing | scripts/smoke_serve.sh |

## Build / test

- smoke: scripts/smoke_serve.sh
- narrow: pytest tests/test_storage.py -q
- full: pytest -q

## Runner budget

max_rounds: 40
max_retries: 3
smoke: scripts/smoke_serve.sh

## Timers

| Node | Interval | Timer ID |
| --- | --- | --- |
| executor | 10m | pending |
| supervisor | 30m | pending |
