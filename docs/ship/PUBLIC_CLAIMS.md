# Public claims (DISTRIBUTION-READINESS-v1 §1.1)

P1–P10 are **CI-bound**. Each claim is wording CONTRACT / INVARIANTS
already prove. Do not advertise a stronger sentence than the named
pytest can fail.

Authority: [`docs/runner/CONTRACT.md`](../runner/CONTRACT.md),
[`docs/runner/RUNNER-INVARIANTS.md`](../runner/RUNNER-INVARIANTS.md).
Residuals: [`KNOWN_ISSUES.md`](../../KNOWN_ISSUES.md).
Negatives: [`S3_NEGATIVE_BATTERY.md`](S3_NEGATIVE_BATTERY.md).

The table is the source the meta-test parses. Keep each claim on **one**
row. Bind only backtick `test_*` names that exist in
`runner/tests/`. `test_public_claims_mapped_tests_exist` fails if any
of those names leave the collected suite.

Git tags are owner-only. This document does not claim a published
release.

## P1–P10

| Id | Claim (CI-bound) | Pytest |
| --- | --- | --- |
| P1 | Close is gate re-pass after an applied write-set. `NodeResult.ok` / model `DONE` is ignored. | `test_done_requires_gate_repass` |
| P2 | Green close retires the live scoreboard (item leaves `open_gaps` / `next_item`, or the run becomes terminal). Re-close is idempotent. | `test_close_retires_scoreboard` |
| P3 | Executor write-set destinations resolve inside the workspace and cannot clobber `run_dir` scoreboard files via relative escape, symlink, or hardlink/alias. | `test_write_set_cannot_escape_workspace` `test_executor_cannot_clobber_ledger_via_relpath` `test_executor_cannot_clobber_scoreboard_via_hardlink` |
| P4 | Product Verify / smoke is a fail-closed subprocess (`cwd` = workspace). Non-zero exit fails. `GateRunner()` never defaults to `passed=True`. | `test_subprocess_verify_red_blocks_close` `test_subprocess_verify_green_allows_close` `test_cli_default_gate_is_fail_closed` |
| P5 | Dual independent timers, no wake edge, Host write isolation (supervisor ≠ ledger; executor ≠ directives). DualTimer does not serial-tick peers. | `test_dual_timer_no_cross_wake` `test_no_peer_wakeup_api` `test_supervisor_cannot_write_ledger` `test_executor_cannot_write_directives` `test_grok_bot_host_does_not_serial_tick_peers` |
| P6 | Missing / incomplete `blocked-on` findings are scout-only. Live Current-slice `owner_blocked` skips write-set and close (no slice-token required). Resolved OB rows do not over-block. | `test_blocked_on_skips_executor_until_findings` `test_owner_blocked_skips_write_set_and_close` `test_owner_blocked_applies_without_slice_token` `test_resolved_owner_blocked_does_not_over_block` |
| P7 | Emit-only (PromptOnlyHost) and timer-only (DualTimer) ticks never close. | `test_prompt_only_host_never_closes` `test_dual_timer_host_never_closes` |
| P8 | `max_rounds` is a hard stop, not a close. A terminal ledger deletes DualTimer tasks; a later fire does not recreate them. | `test_max_rounds_budget` `test_dual_timer_stays_deleted_after_terminal` |
| P9 | After verify-green crash-before-close, resume runs Verify only (write-set is not re-applied). Mid-verify kill is this resume path, not a SIGKILL test. | `test_verify_green_crash_resumes_verify_only` |
| P10 | Public `runner/longgraph/` modules do not import `langgraph`. Product Host source does not name `longgraph-dev-continue`. | `test_public_surface_has_no_langgraph_import` `test_docs_distinguish_dev_continue_vs_product_host` |

H2 merge-gate names (`test_pending_audit_allows_lane_work`,
`test_acceptance_directive_releases_pending_audit`,
`test_executor_folds_directives_and_advances_watermark`,
`test_rounds_log_rotates_golden_round_sections`) stay on the CI list.
They are contract-fidelity tests, not extra P-ids.
