# Runner invariants (Phase ≤1c)

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
on-reference via `blocked-on: findings#<id>`. Missing or incomplete
findings block the executor write-set and close; that tick is scout-only.

**A4 — No wake edge.** Each node has one self-driving timer. There is no
API that lets a node wake, resume, or notify a peer. A directive is
picked up on the executor's next fire; a `blocked-on` pointer is picked
up on the scout's next fire. Absence of work is a complete tick.

**A5 — One independently verifiable work item per round.** A coherent
workset may share one claim, write set, and gate. Verify the same round.
Register-then-defer side gaps.

**A6 — Default-FAIL close (CONTRACT §1.6).** Close is a **gate re-pass**
after an applied write-set (or resume-Verify). Ignore `NodeResult.ok`.
Ignore model "DONE". Empty Verify fails (no close). `n/a` Verify skips
the gate and close. Live Current-slice `owner_blocked` (any live
`OB-xxx` for this run — no slice-token match required) skips write-set
and close. Emit-only / timer-only / no-op ticks never close. A red gate
leaves the item open. Green close rewrites the live scoreboard.
Product Verify/smoke is a fail-closed subprocess (`cwd` = workspace).
`GateRunner()` with no `script=` hook never forges `passed=True`.

**A7 — Smoke before a new item.** When the runner starts an item it has
not already written in this attempt, it runs the ops `smoke` command
first (same subprocess gate as Verify). Smoke red → do not apply the
write-set.

**A8 — Pending-audit blocks advancement.** `milestone_gate: pending-audit`
forbids starting the next milestone's write-set or flipping the gate to
`passed` without an acceptance directive (`ACCEPT-GATE` / first-line verb
`accept-gate`). Disjoint registered lane work may continue. Write-set /
audit-surface overlap uses normalized paths (`.` / `..` cannot dodge).
An `M\d+` token in `next_item` or a lane `Item` is not a run stop.

**A9 — Hard budgets.** `max_rounds` stops the run (not a close).
`max_retries` stops retries on one item (not a close).

**A10 — Status is required and atomic.** Runner-managed runs have
`status.json`. Writes are tmp + replace. `status: completed` implies a
terminal ledger (`exit-ready` / `stalled` / `closed`).

**A11 — Retry key and resume.** Idempotency key is `(runId, round, item_id)`.
Counts live in `metadata.itemRetries`. After verify-green crash-before-close,
resume Verify only (`test_verify_green_crash_resumes_verify_only`).

**A12 — Skill is not the engine.** The runner never reads the authoring
tree (`skills/`). Runtime follows the self-contained files in the run
directory. Engine code lives under `runner/`, never under `skills/`.

**A13 — No LangGraph public surface.** Public modules under
`runner/longgraph/` must not import `langgraph`.

**A14 — Host isolation of writes.** MockHost (and later hosts) enforce
A1–A3 at the write gate: supervisor cannot write the ledger; executor
cannot write directives; scout cannot write either. Write destinations
are resolved; Host write-set must stay `relative_to` the workspace, and
named edge files must stay `relative_to` `run_dir`. An executor write-set
must not escape the workspace or resolve to `run_dir/ledger.md`,
`directives.md`, `ops.md`, or `status.json`. `_close_item` / runner-owned
ledger updates remain the only legitimate scoreboard writers.
PromptOnlyHost emits paste text only and must not write ledger or
directives. GrokBotDualTimerHost may write only the invoking node's
`ops.md` Timers cell; it must not write `ledger.md` from the supervisor
or `directives.md` from the executor.

**A15 — Absolute red lines stay red lines.** No secrets in run files, no
push from the runner, no treating examples as golden SoT.

**A16 — Authoring / runtime split.** Author skills may interview and
compile. They never execute their output. The runner never reloads them.

**A17 — Product dual timers, no DEV continue.** GrokBotDualTimerHost owns
two independent timers with no wake edge. A terminal ledger deletes the
invoking node's timer **before** any seed/create and clears the in-memory
id; a later fire must not recreate. Nodes this host does not schedule
(scout) are a no-op. `longgraph-dev-continue` is DEV-only and must not
appear in product Host paths.

**A18 — CLI Host is explicit; DualTimer is not MockHost.** `--host` is
`mock` \| `prompt-only` \| `grok-bot`. The **safe default** is
`prompt-only` (emit-only). `mock` is the coupled test loop
(executor→supervisor→scout in one process) and is **not** the product
path. `grok-bot` wires `GrokBotDualTimerHost`. When `Host.owns_timers` is
true, the Runner must not drive supervisor/scout from the executor
branch.

---

## D — CI list (Phase ≤1c)

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
| 10 | `test_pending_audit_blocks_advancement` | A8 — next-milestone write-set blocked |
| 11 | `test_public_surface_has_no_langgraph_import` | A13 |
| 12 | `test_status_completed_implies_ledger_terminal` | A10 |
| 13 | `test_smoke_before_new_item` | A7 |
| 14 | `test_max_rounds_budget` | A9 |
| 15 | `test_prompt_only_emits_dual_loop_text` | Phase 1b PromptOnlyHost dual `/loop` emit, no wake verbs |
| 16 | `test_dual_timer_no_cross_wake` | Phase 1c dual timers, no wake/notify/dispatch, own-cell seed, own-timer delete, overlap no-op |
| 17 | `test_docs_distinguish_dev_continue_vs_product_host` | A15, A17 — DEV-only deny; product Host source must not name `longgraph-dev-continue` |
| 18 | `test_verify_green_crash_resumes_verify_only` | A11 — `verify_green` crash-before-close resumes Verify only; write-set is not re-applied |
| 19 | `test_close_retires_scoreboard` | A1, A6 — green close leaves `open_gaps` / advances `next_item` or marks terminal; re-close is idempotent |
| 20 | `test_blocked_on_skips_executor_until_findings` | A3 — missing/incomplete findings: scout-only, no write-set, no close |
| 21 | `test_empty_verify_fails_no_close` | A6 — empty Verify fails; no close |
| 22 | `test_na_verify_skips_gate_and_close` | A6 — `n/a` Verify skips gate and close |
| 23 | `test_owner_blocked_skips_write_set_and_close` | A6 — live Current-slice `owner_blocked`: no write-set, no close |
| 24 | `test_prompt_only_host_never_closes` | A6, A14 — PromptOnlyHost emit-only never closes |
| 25 | `test_dual_timer_host_never_closes` | A6, A14, A17 — DualTimer timer-only never closes; no `busy_nodes` mute |
| 26 | `test_write_set_cannot_escape_workspace` | A14 — write-set destinations resolve inside the workspace |
| 27 | `test_executor_cannot_clobber_ledger_via_relpath` | A1, A14 — `../ledger.md` (and sibling run-dir edges) cannot clobber the scoreboard |
| 28 | `test_subprocess_verify_red_blocks_close` | A6 — product subprocess Verify red does not close |
| 29 | `test_subprocess_verify_green_allows_close` | A6 — product subprocess Verify green may close |
| 30 | `test_cli_default_gate_is_fail_closed` | A6 — CLI / `GateRunner()` is fail-closed, not a forged pass |
| 31 | `test_dual_timer_stays_deleted_after_terminal` | A17 — terminal-before-seed; second fire creates zero new scheduler tasks |
| 32 | `test_dual_timer_scout_noop_when_blocked_on` | A3, A4, A17 — DualTimer scout / unscheduled node is a no-op |
| 33 | `test_cli_accepts_grok_bot_host` | A18 — CLI `--host grok-bot`; safe default is `prompt-only` |
| 34 | `test_grok_bot_host_does_not_serial_tick_peers` | A4, A17, A18 — DualTimer does not serial-tick peers; MockHost still does |
| 35 | `test_pending_audit_allows_lane_work` | A8 — disjoint lane work continues under `pending-audit` |
| 36 | `test_acceptance_directive_releases_pending_audit` | A8 — `ACCEPT-GATE` flips `pending-audit` to `passed` |
| 37 | `test_executor_folds_directives_and_advances_watermark` | A2 — applied path folds live corrections and advances the watermark |
| 38 | `test_rounds_log_rotates_golden_round_sections` | §1.7 — `### Round N` (golden fixture shape) rotates |
| 39 | `test_public_claims_mapped_tests_exist` | Ship-S — every P1–P10 backtick test name is in the collected suite |
| 40 | `test_resolved_owner_blocked_does_not_over_block` | A6 — resolved/closed OB rows are not live |
| 41 | `test_owner_blocked_applies_without_slice_token` | A6 — live OB binds without an `OB-xxx` token in the slice |
| 42 | `test_open_directive_cap_refuses_append_at_cap` | §2 — supervisor append refuses at `OPEN_DIRECTIVE_CAP` |
| 43 | `test_pending_audit_blocks_normalized_audit_surface_overlap` | A8 — `a/../a/file` cannot dodge the audit surface |
