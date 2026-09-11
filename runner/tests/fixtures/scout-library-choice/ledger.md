# shutterlog — longgraph Ledger

> This ledger is the run's only scoreboard. Authority order: the task book in `executor.md` > this ledger. Supervisor corrections: `directives.md`.

## Status header

Current milestone: M1 dual-path writes | Round: 2 | Last round net lines: +12/−0
Next unclosed work item: implement dual-path upload (blocked on scout)
Last directive folded: none
Convergence tracker: rounds since last 5: **2** | net lines since last +400: **+12** | **next round converges: no**
Milestone gate: `open`
Run status: `active`

---

## Current slice (the next round starts here)

Item: implement dual-path upload (new photos → object store)
Write set: shutterlog/storage.py
Context: C-01
Verify: pytest tests/test_storage.py -q
Done when: upload path uses the chosen S3 client; narrow storage tests green
blocked-on: findings#s3-client

---

## Starting snapshot

- Repo `shutterlog` @ `feature/object-storage`. Staging only.
- M1 needs an S3-compatible client before the upload path can land.
- Request-routing is unblocked and may continue while the scout researches.

## Gate scoreboard

| Gate | Status | Evidence / next action |
| --- | --- | --- |
| Dual-path upload implemented | in-progress | blocked-on findings#s3-client |
| Full suite green | closed | `pytest -q` green as of Round 2 start |

## owner-blocked

(none)

## Debt & gap register

| ID | Priority | One line |
| --- | --- | --- |
| GAP-010 | P2 | request-routing headers still use the legacy fallback — legal lane work |

## Rounds log

### Round 2 — 2025-01-15
- **Item**: implement dual-path upload (new photos → object store)
- **blocked-on**: findings#s3-client
- **Next**: continue with request-routing (not blocked) while scout researches
