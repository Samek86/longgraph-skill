# Ship-S3 negative battery

DISTRIBUTION-READINESS-v1 §S Track S3. A CI-gated map of abuse / failure
modes that must end in **expected fail or stop** — no forged close, no
write-set when blocked, no timer zombie, no path escape.

Authority: [`docs/runner/CONTRACT.md`](../runner/CONTRACT.md),
[`docs/runner/RUNNER-INVARIANTS.md`](../runner/RUNNER-INVARIANTS.md),
public claims P1–P10 (wording already proven by named pytest on this
tip). Rebased onto current `main` after #14 (D1 closeout) and #16
(S2 adversarial). The C-S3-1 / C-S3-2 engine fixes also landed on
main via #16; this file keeps the S3 battery map. It does not replace
root [`KNOWN_ISSUES.md`](../../KNOWN_ISSUES.md) or
[`PUBLIC_CLAIMS.md`](PUBLIC_CLAIMS.md). D1's index of already-green
negatives is [`S3_NEGATIVE_BATTERY.md`](S3_NEGATIVE_BATTERY.md).

Base: current `main` (H2 + D1 + S2). Original probe tip was
`f313ed33fef188d2ba9c889bb2871a0601f49812` (H2).
Majors that are not Critical stay in
[`KNOWN_ISSUES_S3.md`](KNOWN_ISSUES_S3.md).

The table below is the source the meta-test parses. Keep each scenario
on **one** row. Bind only backtick `test_*` names that exist in
`runner/tests/`. `test_negative_battery_doc_exists` fails if the doc is
missing, if any of S3-01–S3-08 leave the table, or if a named test
leaves the collected suite.

## Verdict

**PASS after same-PR Critical fixes.**

Critical remaining for battery scenarios: **0**.

## Already green on main (f313ed3)

These scenarios were already proven by merge-gate tests on H2. This PR
does not duplicate their bodies — the table binds the existing names.

| Id | Already-green coverage |
|---|---|
| S3-02 | `test_na_verify_skips_gate_and_close` |
| S3-03 | `test_empty_verify_fails_no_close` |
| S3-04 | `test_blocked_on_skips_executor_until_findings` |
| S3-05 | `test_verify_green_crash_resumes_verify_only` (verify-green resume; not a SIGKILL harness) |
| S3-07 | `test_owner_blocked_skips_write_set_and_close` |
| S3-08 | `test_prompt_only_host_never_closes` `test_dual_timer_host_never_closes` |

S3-01 workspace + `run_dir` scoreboard containment was already green
(`test_write_set_cannot_escape_workspace`,
`test_executor_cannot_clobber_ledger_via_relpath`). Findings-id
containment was **not**.

S3-06 `max_rounds` stop and DualTimer **invoke()** stay-deleted were
already green (`test_max_rounds_budget`,
`test_dual_timer_stays_deleted_after_terminal`). DualTimer
**schedule()** / CLI `--host grok-bot` recreate was **not**.

## Newly added this PR

| Id | New name | Why |
|---|---|---|
| S3-01 | `test_blocked_on_rejects_findings_path_escape` | `blocked-on: findings#../decoy` escaped `findings/` and unblocked write-set + close (C-S3-1) |
| S3-06 | `test_dual_timer_schedule_on_terminal_creates_zero_tasks` | `schedule()` / CLI grok-bot created timers on a terminal ledger (C-S3-2) |
| meta | `test_negative_battery_doc_exists` | Doc + scenario-id → real `def test_*` mapping |

## Battery table

| Id | Expected | Pytest | Claim | On main (f313ed3) | This PR |
|---|---|---|---|---|---|
| S3-01 | Write-set stays in the workspace; `../` cannot clobber `run_dir` scoreboard files; `findings#<id>` cannot escape `findings/` or close | `test_write_set_cannot_escape_workspace` `test_executor_cannot_clobber_ledger_via_relpath` `test_blocked_on_rejects_findings_path_escape` | P3, P6 | FAIL (findings escape) | PASS |
| S3-02 | `n/a` Verify skips the gate (skip ≠ pass); no close | `test_na_verify_skips_gate_and_close` | P1 | PASS | PASS |
| S3-03 | Empty / whitespace Verify fails; no close | `test_empty_verify_fails_no_close` | P1 | PASS | PASS |
| S3-04 | Missing or incomplete `blocked-on` findings: scout-only; no write-set; no close | `test_blocked_on_skips_executor_until_findings` | P6 | PASS | PASS |
| S3-05 | After verify-green crash-before-close, resume is Verify only; write-set is not reapplied | `test_verify_green_crash_resumes_verify_only` | P9 | PASS | PASS |
| S3-06 | `max_rounds` / terminal ledger is a stop, not a close; DualTimer `schedule()` / `invoke()` do not recreate timers | `test_max_rounds_budget` `test_dual_timer_stays_deleted_after_terminal` `test_dual_timer_schedule_on_terminal_creates_zero_tasks` | P8 | FAIL (schedule recreate) | PASS |
| S3-07 | Live Current-slice `owner_blocked`: no write-set; no close | `test_owner_blocked_skips_write_set_and_close` | P6 | PASS | PASS |
| S3-08 | Emit-only PromptOnlyHost and timer-only DualTimer ticks never close alone | `test_prompt_only_host_never_closes` `test_dual_timer_host_never_closes` | P7 | PASS | PASS |

Mid-verify kill is the verify-green resume path (P9). This tree does
not add a fragile SIGKILL harness.

## Criticals found on f313ed3 and fixed here

### C-S3-1 — `blocked-on` path traversal unblocked write-set and close

- **Claim.** `blocked-on: findings#<id>` resolves only to
  `findings/<id>.md`. Missing or incomplete findings are scout-only.
- **At f313ed3.** `findings_relpath` concatenated the raw `#` suffix.
  `_findings_ready` treated any existing file whose body said
  `Status: complete` as ready, including `findings/../decoy.md`.
- **Invariant.** A3, CONTRACT §1.3 / §1.6, P6.
- **Fix.** `safe_findings_ident` rejects `..` / slashes.
  `_findings_ready` requires the resolved path under `run_dir/findings/`.
  MockHost scout no-ops an unsafe id.

### C-S3-2 — DualTimer `schedule()` created tasks on a terminal ledger

- **Claim.** A terminal ledger deletes the invoking node's timer
  **before** any Timers-cell seed or scheduler create. A later fire
  must not recreate a deleted task.
- **At f313ed3.** `GrokBotDualTimerHost.schedule()` always
  `scheduler.create` when in-memory ids are empty. CLI `--host grok-bot`
  calls `schedule()` then `Runner.run(steps=1)`, which marks
  `completed` on a terminal ledger **without** invoking the Host, so
  invoke()'s terminal-before-seed path never ran. A later `schedule()`
  after a correct delete also recreated tasks.
- **Invariant.** A17, CONTRACT §1.5, P8.
- **Fix.** `schedule()` deletes leftover own-timers and returns
  without `create` when the ledger is terminal.

## How to run

```bash
cd runner && python3 -m pytest -q
```

CI job **Runner Phase 0–1c tests** collects this file. No separate
workflow.
