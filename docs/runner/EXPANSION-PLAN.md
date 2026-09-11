# EXPANSION-PLAN-v3.3 — Phase 0 / 1a / 1b / 1c extract

Faithful summary of the SHIPPABLE plan for the longgraph runner, limited to
what Phase 0, Phase 1a, Phase 1b, and Phase 1c may ship. Later phases (1d,
Phase 2, web UI, dynamic topology, prompt auto-edit, token-cost telemetry)
are **out of scope**.

See [`AUTHORITY.md`](AUTHORITY.md) for precedence.

---

## Goal

Ship a runner that executes an already-compiled run directory
(`ledger.md`, `directives.md`, `ops.md`, node prompts, `status.json`)
without reloading an authoring skill.

- **Skill stays policy.** Engine is new under `runner/`.
- **No LangGraph as public surface.** No `langgraph` import in public code.
- **No wake edges** between nodes. Each node has its own timer; the
  supervisor steers only through the one-way directives edge.
- **Done / close = gate re-pass only.** Never model `"DONE"` and never
  `NodeResult.ok`. See CONTRACT §1.6 Default-FAIL.

Model for this work: grok-4.6. Do not suggest fable.

---

## Phase 0 (must be green first)

1. Land this `docs/runner/` authority set.
2. Create **normalized** fixtures at
   `runner/tests/fixtures/{add-tests-to-cli,migrate-blob-storage,scout-library-choice}/`.
   Do **not** treat raw upstream examples as golden SoT. Adapt them, then
   fill every CONTRACT field the examples omit.
3. Implement `runner/longgraph/state.py` for the parse fields in the golden
   table below.
4. `test_golden_parse` asserts **exact** expected values (strip inline
   markdown code spans from `next_item`).
5. Update [`docs/observability/status-schema.md`](../observability/status-schema.md):
   runner-managed runs require `status.json` and atomic `tmp` + `mv`;
   mark naive `cat >` examples **legacy**. Extend the template with
   `ownerEscalation: null` and allow `metadata.itemRetries`.

### Fixture shape (every fixture)

```
executor.md
supervisor.md
ledger.md
directives.md
ops.md
status.json
archive/.gitkeep
```

Scout fixture additionally:

- ledger pointer `blocked-on: findings#s3-client`
- `findings/s3-client.md` (path is `findings/<id>.md`, not a singular
  `findings.md`)
- a live dispatch directive on `directives.md`

`add-tests-to-cli` **must** synthesize a Current slice and
`Last directive folded: none` even though the upstream example lacks them.

### Golden parse table

| Fixture | Field | Expected |
|---|---|---|
| add-tests-to-cli | next_item | GAP-002 timezone bug in "in N days" (picked up this round) |
| add-tests-to-cli | open_gaps | ["GAP-002"] |
| add-tests-to-cli | last_directive_folded | none |
| add-tests-to-cli | milestone_gate | n/a |
| add-tests-to-cli | run_status | active |
| add-tests-to-cli | current_slice.Item | Fix GAP-002 (timezone off-by-one in in N days) |
| add-tests-to-cli | current_slice.Write set | tests/test_dates.py (and minimal parser fix under date util if required by Done when) |
| add-tests-to-cli | current_slice.Context | C-01 |
| add-tests-to-cli | current_slice.Verify | pytest tests/test_dates.py -q |
| add-tests-to-cli | current_slice.Done when | previously-xfail midnight case passes; full pytest -q green |
| migrate-blob-storage | next_item | M3 (owner-only: drop the blob column) |
| migrate-blob-storage | last_directive_folded | D-003 |
| migrate-blob-storage | open_gaps | [] |
| migrate-blob-storage | owner_blocked | ["OB-001"] |
| migrate-blob-storage | milestone_gate | passed |
| migrate-blob-storage | run_status | active |
| scout blocked | blocked_on | findings#s3-client |
| scout blocked | findings path | findings/s3-client.md exists |

---

## Phase 1a — MockHost MVP

### Layout

```
runner/
  pyproject.toml
  longgraph/{__init__,state,nodes,hosts,gates,retry,cli}.py
  tests/fixtures/...
  tests/test_*.py
```

### CLI

```
longgraph run|status|stop <run_dir>
```

### Host / MockHost

A **Host** is the process that runs a node prompt against a context.
Phase 1a ships **MockHost only**: no model.

| Node | MockHost write set |
|---|---|
| executor | deterministic map from Current slice / item id onto the workspace write-set |
| supervisor | `directives.md` only |
| scout | `findings/<id>.md` only |

The runner runs [`gates`](../../runner/longgraph/gates.py) **after** the
executor. Close **ignores** `NodeResult.ok`.

---

## Phase 1b — PromptOnlyHost

A second `Host` implementation next to MockHost. No model. No peer-wakeup
API. Does **not** write `ledger.md` or `directives.md` as part of emit.

Emit exactly two paste blocks (placeholders `EXEC_INTERVAL`, `SUP_INTERVAL`,
`RUN_DIR` are substitutable from constructor / ctx):

```
/loop {{EXEC_INTERVAL}} Execute the existing runtime node at {{RUN_DIR}}/executor.md. Do not load any skill.
/loop {{SUP_INTERVAL}} Execute the existing runtime node at {{RUN_DIR}}/supervisor.md. Do not load any skill.
```

Return the dual-loop text via `NodeResult.message` and `emit_dual_loop(...)`.
No wake / notify / dispatch verbs in the emitted text.

Keep MockHost behavior untouched. Phase 1d ApiHost is out of scope.

### Ops knobs

Parse from `ops.md`:

- `max_rounds`
- `max_retries`
- `smoke` (or the Build / test alias for the same command)

### Retry / resume / idempotency

- Idempotency key: `(runId, round, item_id)`.
- Retry count lives in `status.json` → `metadata.itemRetries`.
- **verify-green-then-crash-before-close** → on resume, run **Verify only**
  (do not re-apply the write-set). Enforced by
  `test_verify_green_crash_resumes_verify_only`.
- `status.json` writes are atomic: write `status.json.tmp`, then `os.replace`.

---

## Phase 1c — GrokBotDualTimerHost (EXPANSION-PLAN-v3.3 §6.3)

A third `Host` implementation next to MockHost and PromptOnlyHost. Same live
Protocol: `Host.invoke(node, prompt, ctx) -> NodeResult`. No model. No
peer-wakeup API (`wake` / `notify` / `dispatch`).

Product dual independent timers — executor + supervisor — with **no wake
edge**. Shared workspace and the same run directory. Each node reads frozen
`*.md` only.

1. Two independent schedules (routines / cron / `/loop`). No `wake` /
   `notify` / `dispatch` API between nodes.
2. On first fire, a node writes **only its own** `ops.md` Timers cell
   (`pending` → real timer ID). Never the peer's row.
3. Supervisor refreshes its own next-fire prompt in place (`tick=N`);
   the executor stays warm.
4. Overlapping fires are skipped by the host (no-op tick). The runner
   must tolerate a no-op.
5. On ledger terminal, each node deletes **its own** timer only —
   check terminal **before** seed/create; a later fire must not recreate.
6. Product path MUST NOT call or reference `longgraph-dev-continue`
   (DEV-only). See [`runner/README.md`](../../runner/README.md).
7. Honor [`grok.md`](../../skills/loop-graph/references/grok.md) limits
   when on Grok Build: min interval 60s; recurring expiry 7d; overlapping
   fires skipped.

Tests use a deterministic in-process fake scheduler (record
create / update / delete / list). No live Grok Bot. No network.

Keep MockHost and PromptOnlyHost behavior untouched. Phase 1d ApiHost,
LangGraph, wake edges, a skill-dir engine, and Phase 2 prompt auto-rewrite
are out of scope.

---

## Merge-gate tests (exact names — Phase ≤1c)

1. `test_golden_parse`
2. `test_mock_roundtrip_add_tests`
3. `test_forced_gate_fail_then_retry`
4. `test_supervisor_cannot_write_ledger`
5. `test_executor_cannot_write_directives`
6. `test_done_requires_gate_repass`
7. `test_runner_never_reads_skills_dir`
8. `test_no_peer_wakeup_api`
9. `test_status_atomic`
10. `test_pending_audit_blocks_advancement`
11. `test_public_surface_has_no_langgraph_import`
12. `test_status_completed_implies_ledger_terminal`
13. `test_smoke_before_new_item`
14. `test_max_rounds_budget`
15. `test_prompt_only_emits_dual_loop_text` (Phase 1b)
16. `test_dual_timer_no_cross_wake` (Phase 1c)
17. `test_docs_distinguish_dev_continue_vs_product_host` (Phase 1c)
18. `test_verify_green_crash_resumes_verify_only` (retry/resume: Verify only after `verify_green`)
19. `test_close_retires_scoreboard` (C1 — scoreboard retirement)
20. `test_blocked_on_skips_executor_until_findings` (C2 — blocked-on)
21. `test_empty_verify_fails_no_close` (C3 — empty Verify)
22. `test_na_verify_skips_gate_and_close` (C3 — `n/a` Verify)
23. `test_owner_blocked_skips_write_set_and_close` (C3 — owner-blocked)
24. `test_prompt_only_host_never_closes` (C4 — PromptOnlyHost)
25. `test_dual_timer_host_never_closes` (C4 — DualTimer; no `busy_nodes` mute)
26. `test_write_set_cannot_escape_workspace` (M3 — write-set stays in workspace)
27. `test_executor_cannot_clobber_ledger_via_relpath` (M3 — no `../ledger.md` clobber)
28. `test_subprocess_verify_red_blocks_close` (H0b — subprocess Verify red)
29. `test_subprocess_verify_green_allows_close` (H0b — subprocess Verify green)
30. `test_cli_default_gate_is_fail_closed` (H0b — CLI fail-closed)
31. `test_dual_timer_stays_deleted_after_terminal` (H0c M4 — terminal-before-seed; no recreate)
32. `test_dual_timer_scout_noop_when_blocked_on` (H0c M5 — DualTimer scout is a no-op)

Banned aliases: `test_golden_next_item_*`, `test_default_fail_until_gate`.

---

## Done when (this extract)

- All Phase ≤1b tests plus both Phase 1c names green in CI or local
  pytest, documented on the PR.
- PR title like: `feat(runner): Phase 1c GrokBotDualTimerHost`.
- PR body lists test results and notes **DO NOT MERGE** without owner ack.
- Stacks on Phase 0–1b. Do **not** merge from the agent. Open a PR only.
