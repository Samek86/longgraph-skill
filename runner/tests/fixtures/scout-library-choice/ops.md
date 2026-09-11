# shutterlog — Environment & Ops Facts

## Context index

| ID | Use when | Read | Verify |
| --- | --- | --- | --- |
| C-01 | S3 client choice / dual-path upload | ops constraints; findings/s3-client.md | pytest tests/test_storage.py -q |

## Build / test

- smoke: pytest -q
- narrow: pytest tests/test_storage.py -q

## Runner budget

max_rounds: 20
max_retries: 3
smoke: pytest -q

## Timers

| Node | Interval | Timer ID |
| --- | --- | --- |
| executor | 10m | pending |
| supervisor | 30m | pending |
| scout | on-demand | pending |
