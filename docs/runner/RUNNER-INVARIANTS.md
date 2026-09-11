# Runner invariants (Phase ≤1a)

A* rules the runner must not break, plus the CI list that proves them.
Tune numbers (intervals, caps, retries). Do not change the shape.
See [`AUTHORITY.md`](AUTHORITY.md).

---

## A — Load-bearing rules

**A1 — Single scoreboard, one writer.** `ledger.md` is the only scoreboard.
The executor is its **exactly one** writer. Nobody else edits it.

**A2 — One-way directives.** The supervisor steers only through
`directives.md`. It never edits the ledger and never shares the
executor's context.

**A3 — Scout writes findings only.** Scout output is `findings/<id>.md`.
It does not write the ledger or directives. The executor reads findings
on-reference via `blocked-on: findings#<id>`.

**A4 — No wake edge.** Each node has one self-driving timer. There is no
API that lets a node wake, resume, or notify a peer. A directive is
picked up on the executor's next fire; a `blocked-on` pointer is picked
up on the scout's next fire. Absence of work is a complete tick.

**A5 — One independently verifiable work item per round.** A coherent
workset may share one claim, write set, and gate. Verify the same round.
Register-then-defer side gaps.

**A6 — Default-FAIL close (CONTRACT §1.6).** Close is a **gate re-pass**
only. Ignore `NodeResult.ok`. Ignore model "DONE". A red gate leaves the
item open.

**A7 — Smoke before a new item.** When the runner starts an item it has
not already written in this attempt, it runs the ops `smoke` command
first. Smoke red → do not apply the write-set.

**A8 — Pending-audit blocks advancement.** `milestone_gate: pending-audit`
forbids starting the next milestone's write-set or flipping the gate to
`passed` without an acceptance directive.

**A9 — Hard budgets.** `max_rounds` stops the run (not a close).
`max_retries` stops retries on one item (not a close).

**A10 — Status is required and atomic.** Runner-managed runs have
`status.json`. Writes are tmp + replace. `status: completed` implies a
terminal ledger (`exit-ready` / `stalled` / `closed`).

**A11 — Retry key and resume.** Idempotency key is `(runId, round, item_id)`.
Counts live in `metadata.itemRetries`. After verify-green crash-before-close,
resume Verify only.

**A12 — Skill is not the engine.** The runner never reads the authoring
tree (`skills/`). Runtime follows the self-contained files in the run
directory. Engine code lives under `runner/`, never under `skills/`.

**A13 — No LangGraph public surface.** Public modules under
`runner/longgraph/` must not import `langgraph`.

**A14 — Host isolation of writes.** MockHost (and later hosts) enforce
A1–A3 at the write gate: supervisor cannot write the ledger; executor
cannot write directives; scout cannot write either.

**A15 — Absolute red lines stay red lines.** No secrets in run files, no
push from the runner, no treating examples as golden SoT.

**A16 — Authoring / runtime split.** Author skills may interview and
compile. They never execute their output. The runner never reloads them.

---

## D — CI list (Phase ≤1a only)

Exact test names. Do not add the banned aliases
`test_golden_next_item_*` or `test_default_fail_until_gate`.

| # | Test | Guards |
|---|---|---|
| 1 | `test_golden_parse` | A15, golden table, span-strip |
| 2 | `test_mock_roundtrip_add_tests` | MockHost write-set + gate-after-executor |
| 3 | `test_forced_gate_fail_then_retry` | A6, A11 |
| 4 | `test_supervisor_cannot_write_ledger` | A1, A2, A14 |
| 5 | `test_executor_cannot_write_directives` | A2, A14 |
| 6 | `test_done_requires_gate_repass` | A6 |
| 7 | `test_runner_never_reads_skills_dir` | A12, A16 |
| 8 | `test_no_peer_wakeup_api` | A4 |
| 9 | `test_status_atomic` | A10 |
| 10 | `test_pending_audit_blocks_advancement` | A8 |
| 11 | `test_public_surface_has_no_langgraph_import` | A13 |
| 12 | `test_status_completed_implies_ledger_terminal` | A10 |
| 13 | `test_smoke_before_new_item` | A7 |
| 14 | `test_max_rounds_budget` | A9 |

Phase 1b+ tests do not belong in this PR.
