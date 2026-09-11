# taskcat — longgraph Ledger

> This ledger is the run's only scoreboard. Authority order: the task book in `executor.md` > this ledger. Supervisor corrections: `directives.md`.

## Status header

Current milestone: single goal (date parser green) | Round: 3 | Last round net lines: +18/−0
Next unclosed work item: GAP-002 timezone bug in `"in N days"` (picked up this round)
Last directive folded: none
Convergence tracker: rounds since last 5: **3** | net lines since last +400: **+42** | **next round converges: no**
Milestone gate: `n/a` (single goal — no intermediate boundaries)
Run status: `active`

---

## Current slice (the next round starts here)

Item: Fix GAP-002 (timezone off-by-one in in N days)
Write set: tests/test_dates.py (and minimal parser fix under date util if required by Done when)
Context: C-01
Verify: pytest tests/test_dates.py -q
Done when: previously-xfail midnight case passes; full pytest -q green

---

## Starting snapshot

- Repo `taskcat` @ `feature/date-parser-tests`, tip `a1b2c3d` (local commits only, never pushed).
- `docs/date-formats.md` documents 6 input forms: `YYYY-MM-DD`, `today`, `tomorrow`, `next <weekday>`, `in N days`, `N days ago`.
- Baseline: `tests/test_dates.py` covered only the first 2 forms; full suite green.

---

## Gate scoreboard

| Gate | Status | Evidence / next action |
| --- | --- | --- |
| Every documented form has a test | in-progress | 5/6 forms tested (missing: `N days ago`) |
| All date tests pass | in-progress | blocked on GAP-002 |
| Full suite green | closed | `pytest -q` green as of Round 3 start |

## owner-blocked

（none）

## Debt & gap register

| ID | Priority | One line |
| --- | --- | --- |
| GAP-001 | P2 | `next <weekday>` on the same weekday: spec unclear (today or +7?) — resolved by owner as +7 in Round 2 |
| GAP-002 | P1 | `"in N days"` ignores local timezone, off-by-one near midnight UTC — found in Round 2, being fixed in Round 3 |

## Rounds log

### Round 1 — 2026-07-19
- **Item**: test the `next <weekday>` form
- **Gate**: `pytest tests/test_dates.py -q` → 4 passed; full `pytest -q` green
- **Change**: added 4 parametrized cases for `next mon`..`next sun`
- **Verify**: all 4 pass
- **Net lines**: +22/−0
- **Open**: same-weekday semantics ambiguous → logged GAP-001
- **Next**: resolve GAP-001, then test `in N days`

### Round 2 — 2026-07-19
- **Item**: test the `in N days` form (after owner resolved GAP-001 = +7)
- **Gate**: `pytest tests/test_dates.py -q` → 6 passed, 1 xfail; full suite green
- **Change**: added cases for `in 1 day` / `in 3 days`; marked the midnight case xfail
- **Verify**: xfail reproduces a timezone off-by-one → **logged GAP-002, did NOT fix it here**
- **Net lines**: +16/−0
- **Open**: GAP-002
- **Next**: fix GAP-002 (P1) before adding the last form

### Round 3 — 2026-07-19
- **Item**: fix GAP-002 (timezone off-by-one in `in N days`)
- **Gate**: pending this round
- **Change**: not yet closed
- **Verify**: pending
- **Net lines**: +18/−0 (carried from the in-progress slice)
- **Open**: GAP-002
- **Next**: close GAP-002 then test `N days ago`
