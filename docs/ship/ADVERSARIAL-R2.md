# Ship-S2 adversarial re-pass (R2)

Hostile source review of the runner on **main tip**
`f313ed33fef188d2ba9c889bb2871a0601f49812`
(`fix(runner): H2 contract fidelity (M1/M2/M7)`).

Authority: [`docs/runner/CONTRACT.md`](../runner/CONTRACT.md),
[`docs/runner/RUNNER-INVARIANTS.md`](../runner/RUNNER-INVARIANTS.md),
[`docs/runner/AUTHORITY.md`](../runner/AUTHORITY.md),
DISTRIBUTION-READINESS-v1 §S + public claims P1–P10 (wording already
proven by named pytest on this tip). Prior Criticals C1–C4 were filed
against `d7a9df3` and are already merged. This is the re-pass, not a
replay.

Scope: `runner/longgraph/{nodes,hosts,state,rotate,retry,gates,cli}.py`
plus the merge-gate suite. Open ship PRs #14 / #15 were **not** rebased.
`docs/ship/SOAK.md` is absent on this tip (lives on unmerged #15) — no
pointer added. Token/$ telemetry and ApiHost / prompt-compiler stay
deferred (Minor).

Method: contract checklist first; then cross-read; then throwaway
probes under `/tmp` for every candidate Critical. Line cites are
files actually read. Pre-fix holes are labeled **at f313ed3**.

## Verdict

**PASS after same-PR Critical fixes.** Two Criticals reproduced on
f313ed3 and closed in this PR (regression tests green). Critical
count remaining: **0**. Majors stay listed here and in
[`KNOWN_ISSUES_S2.md`](KNOWN_ISSUES_S2.md) so D2 cannot hide them.

## Critical

None remaining.

The two holes found on the RC tip, with the same-PR close:

### C-R2-1 — `blocked-on` path traversal unblocked write-set and close (FIXED)

- **Claim.** `blocked-on: findings#<id>` resolves only to
  `findings/<id>.md`. Missing or incomplete findings are scout-only:
  no executor write-set, no close.
- **Evidence (at f313ed3).**
  `findings_relpath` concatenated the raw `#` suffix
  (`runner/longgraph/state.py` 92–98) with no segment check.
  `Runner._findings_ready` (`nodes.py` 379–388) did
  `self.run_dir / rel` and treated any existing file whose body said
  `Status: complete` as ready. Probe: ledger
  `blocked-on: findings#../decoy`, decoy at `run_dir/decoy.md` with
  `**Status**: complete`, real `findings/s3-client.md` still
  `incomplete` → MockHost applied `shutterlog/storage.py` and closed
  the item. `findings_relpath("findings#../decoy")` was
  `findings/../decoy.md`.
- **Invariant.** A3, CONTRACT §1.3 / §1.6, P6.
- **Minimal fix (this PR).** `safe_findings_ident` rejects `..` /
  slashes (`state.py` 95–113). `_findings_ready` requires the
  resolved path to stay under `run_dir/findings/` (`nodes.py` 379–393).
  MockHost scout no-ops an unsafe id (`hosts.py` 246–251).
- **Regression.** `test_blocked_on_rejects_findings_path_escape`.

### C-R2-2 — DualTimer `schedule()` created tasks on a terminal ledger (FIXED)

- **Claim.** A terminal ledger deletes the invoking node's timer
  **before** any Timers-cell seed or scheduler create. A later fire
  must not recreate a deleted task. Product CLI `--host grok-bot`
  is this Host.
- **Evidence (at f313ed3).** `GrokBotDualTimerHost.schedule`
  (`hosts.py` 484–504) always `scheduler.create` when in-memory ids
  are empty — no `_ledger_terminal` check. CLI
  (`cli.py` 68–72) calls `schedule()` **then** `Runner.run(steps=1)`.
  `Runner.run` (`nodes.py` 464–466) sees a terminal ledger, marks
  `completed`, and **never invokes** the Host, so invoke()'s
  terminal-before-seed path never runs. Probe 1: `schedule()` on
  `Run status: closed` created `task-1`/`task-2`; after `run()`
  both tasks were still in the scheduler. Probe 2: after invoke()
  correctly deleted timers, a second `schedule()` created
  `task-3`/`task-4`. `test_dual_timer_stays_deleted_after_terminal`
  only covers `invoke()`, not `schedule()` / CLI.
- **Invariant.** A17, CONTRACT §1.5, P8.
- **Minimal fix (this PR).** `schedule()` deletes leftover own-timers
  and returns without `create` when the ledger is terminal
  (`hosts.py` 487–500).
- **Regression.** `test_dual_timer_schedule_on_terminal_creates_zero_tasks`
  (Host API + CLI `--host grok-bot` leaves `ops.md` Timers cells
  unseeded).

## Major

### M-R2-1 — resolved `OB-xxx` rows stay “live”

- **Claim.** `owner_blocked` is **live** `OB-xxx` ids. `(none)` /
  empty → `[]`. A resolved row must not keep blocking the Current
  slice.
- **Evidence.** `_parse_open_gaps` skips `_CLOSED_WORDS`
  (`state.py` 223–232). `_parse_owner_blocked` (`state.py` 235–239)
  does not. Probe: rewrite the migrate-blob-storage OB-001 row to
  include `resolved` and flip Verify to `true` → `owner_blocked`
  was still `["OB-001"]`; no write-set, no close.
- **Invariant.** CONTRACT §1.1 `owner_blocked`, A6 (live
  Current-slice `owner_blocked`).
- **Minimal suggested fix.** Apply the same closed-word skip (or an
  explicit “live row” rule) in `_parse_owner_blocked`. Add a fixture
  row that is marked resolved and assert it is absent from
  `state.owner_blocked`. Fail-closed today (over-block), so not a
  forged close.

### M-R2-2 — `OPEN_DIRECTIVE_CAP` is not enforced on append

- **Claim.** `OPEN_DIRECTIVE_CAP` (default 8) is **append
  discipline**: do not add more unfolded packets once the live
  queue is at the cap. Rotation must not archive packets the
  watermark has not passed.
- **Evidence.** `rotate_directives` intentionally ignores the cap
  for archive (`rotate.py` 275–278, `_ = cap`).
  `append_correction_packet` (`rotate.py` 382–402) never reads the
  cap. `MockHost._supervisor` always appends. Probe: 8 live packets
  + one more append → 9 live ids. H2 test
  `test_rotate_does_not_cap_unfolded_packets` only guards the
  “do not silently drop” side.
- **Invariant.** CONTRACT §2 watermark / rotate.
- **Minimal suggested fix.** Refuse (or no-op) append when
  `len(unfolded_packets) >= OPEN_DIRECTIVE_CAP`. Keep the
  no-cap-rotate behavior. Product DualTimer does not append
  corrections itself (timer-only).

### M-R2-3 — product DualTimer Host is still timer-only

- **Claim.** Close is a gate re-pass after an **applied** write-set.
  `GrokBotDualTimerHost` owns timers and must not forge close; it
  also does not apply work.
- **Evidence.**   `GrokBotDualTimerHost.invoke` returns
  `applied=False` (`hosts.py` 541–546). CLI grok-bot
  seeds FakeScheduler in-process and ticks `steps=1`. No live Grok
  Bot scheduler, no multi-day soak on this tip.
- **Invariant.** A6, A17, P7. Already covered by
  `test_dual_timer_host_never_closes`. Residual is capability, not
  a forged close.
- **Minimal suggested fix.** Owner soak / a Host that applies work.
  Out of scope for S2. Do not advertise DualTimer as a closer.

## Minor / Nit / deferred

- **DualTimer writes `ops.md` outside EdgeWriter.**
  `_seed_own_timer_cell` (`hosts.py` ~619 at f313ed3,
  `ops.write_text`) is the A14-allowed Timers-cell write. No
  EdgeWriter audit line. Keep it; do not treat as Critical.
- **`ACCEPT-GATE` matches anywhere in the packet.**
  `is_accept_gate_packet` (`rotate.py` 332–344) is token-OR-verb,
  matching CONTRACT §1.4. A commentary line that mentions the
  token would flip the gate. Spec-faithful; tighten only if a run
  shows accidental flips.
- **Bare `accept` verb does not flip the gate.** Re-checked: a
  packet whose verb is `accept` and whose body does **not** contain
  the `ACCEPT-GATE` token leaves `pending-audit` in place (the
  first `/tmp` probe was contaminated by putting the token in the
  Action sentence).
- **`Runner()` defaults to MockHost.** A18 / CLI default is
  `prompt-only` (`cli.py` 14–15, 64–67). Constructor default is
  test-loop only. Fine if CLI stays the product entry.
- **`status.json` `ownerEscalation` is not schema-checked on read.**
  CONTRACT §4 names the field; `parse_run` / `_load_status` accept
  whatever JSON is there. Missing file still fails closed
  (`nodes.py` 259–263).
- **Product Verify is `subprocess` + `shell=True`** (`gates.py`
  71–88), `cwd` = workspace. Trusted compiled ledger, fail-closed
  on non-zero. Not a write-gate claim.
- **Token / $ telemetry, ApiHost, prompt-compiler.** EXPANSION-PLAN
  Phase 2 / 1d. Deferred. Not Critical.
- **No `git push` in `runner/longgraph/`.** Grep empty. A15 holds
  on this tree.

## Untested contract claims

Sentences the suite does not yet fail if they regress (after this
PR’s two new names):

| Contract sentence | Gap |
|---|---|
| `owner_blocked` is **live** rows only (resolved/closed skipped) | No test; parser over-includes (M-R2-1) |
| `OPEN_DIRECTIVE_CAP` refuses a further append | No test; append always succeeds (M-R2-2) |
| Folded non-`ACCEPT-GATE` packets record an explicit no-op in the ledger | Watermark advances; no per-packet no-op line |
| `ownerEscalation` must be present (null or card) | Read path does not validate |
| `KEEP_ROUNDS` / `keep_rounds` and `OPEN_DIRECTIVE_CAP` / `open_directive_cap` aliases | `parse_rotation_caps` implements both; no dedicated alias test |
| Mid-write crash resume | Only `verify_green` crash is specified and tested (P9) |
| Live Grok Build scheduler (min 60s / 7d expiry in product) | FakeScheduler unit checks only |
| Multi-day DualTimer soak | Absent on this tip (PR #15 / owner) |

P1–P10 mapped tests that **do** exist on this tip and were spot-checked:

| Id | Claim | Named pytest on main |
|---|---|---|
| P1 | Close is gate re-pass; ignore `NodeResult.ok` / `DONE` | `test_done_requires_gate_repass` |
| P2 | Green close retires the scoreboard; re-close idempotent | `test_close_retires_scoreboard` |
| P3 | Write-set stays in workspace; no `../ledger.md` clobber | `test_write_set_cannot_escape_workspace` `test_executor_cannot_clobber_ledger_via_relpath` |
| P4 | Fail-closed subprocess Verify/smoke; `GateRunner()` never defaults pass | `test_subprocess_verify_red_blocks_close` `test_subprocess_verify_green_allows_close` `test_cli_default_gate_is_fail_closed` |
| P5 | Dual timers, no wake, write isolation, no serial peer tick | `test_dual_timer_no_cross_wake` `test_no_peer_wakeup_api` `test_supervisor_cannot_write_ledger` `test_executor_cannot_write_directives` `test_grok_bot_host_does_not_serial_tick_peers` |
| P6 | Missing/incomplete findings scout-only; live `owner_blocked` skips write/close | `test_blocked_on_skips_executor_until_findings` `test_owner_blocked_skips_write_set_and_close` (+ R2 escape test) |
| P7 | Emit-only / timer-only never close | `test_prompt_only_host_never_closes` `test_dual_timer_host_never_closes` |
| P8 | `max_rounds` is a stop, not a close; terminal DualTimer stays deleted | `test_max_rounds_budget` `test_dual_timer_stays_deleted_after_terminal` (+ R2 schedule test) |
| P9 | verify-green crash resumes Verify only | `test_verify_green_crash_resumes_verify_only` |
| P10 | No `langgraph` public import; no `longgraph-dev-continue` in product Host source | `test_public_surface_has_no_langgraph_import` `test_docs_distinguish_dev_continue_vs_product_host` |

H2 names (`test_pending_audit_allows_lane_work`,
`test_acceptance_directive_releases_pending_audit`,
`test_executor_folds_directives_and_advances_watermark`,
`test_rounds_log_rotates_golden_round_sections`) stay on the CI
list. They are contract fidelity, not extra P-ids.

## What looks solid

- Default-FAIL close path: `NodeResult.ok` discarded (`nodes.py`
  558–565); empty Verify fails; `n/a` skips; emit/timer `applied`
  is false and cannot close.
- Green close rewrites the live scoreboard (`retire_live_scoreboard`,
  `test_close_retires_scoreboard`). Re-close is idempotent.
- Write-gate A14: supervisor ≠ ledger, executor ≠ directives, scout
  ≠ either; workspace `relative_to`; protected run-dir names.
- `pending-audit` blocks only the Current-slice next-milestone
  surface; disjoint lane work continues; `ACCEPT-GATE` /
  `accept-gate` is the release marker; bare `accept` is not.
- Directive watermark advances on the applied close path; rotation
  does **not** archive unfolded packets.
- Rounds log rotates both `- R…` lines and `### Round N` sections.
- `status: completed` refuses a non-terminal ledger (`write_status`).
- verify-green crash-before-close resumes Verify only.
- CLI `--host` default is `prompt-only`; `mock` is explicit; DualTimer
  does not serial-tick peers (`owns_timers`).
- Authoring tree is not read; no `langgraph` import; no
  `longgraph-dev-continue` in `runner/longgraph/`.
- Prior C1–C4 / H0–H2 merge-gate names are present and internally
  consistent with the post-H2 contract.
