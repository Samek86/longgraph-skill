# S3 negative battery

Index of fail-closed / deny / no-close cases already on `main`.
This is not a new suite — it names pytest that must stay green.

Run locally (no network):

```bash
./scripts/ship-negative-battery.sh
```

Or: `cd runner && python -m pytest` (full merge-gate). Mid-verify kill
is covered by the verify-green crash-resume path. This tree does not
add a fragile SIGKILL test.

| Negative | What must not happen | Pytest |
| --- | --- | --- |
| Escape write-set | Write outside the workspace, or clobber `run_dir` scoreboard files via `../` | `test_write_set_cannot_escape_workspace` `test_executor_cannot_clobber_ledger_via_relpath` |
| Empty Verify | Empty / whitespace Verify forges a green close | `test_empty_verify_fails_no_close` |
| `n/a` Verify | `n/a` is treated as pass | `test_na_verify_skips_gate_and_close` |
| Missing findings / `blocked-on` | Executor applies a write-set or closes while findings are missing or incomplete | `test_blocked_on_skips_executor_until_findings` |
| `owner_blocked` | Current-slice live `OB-*` still writes or closes | `test_owner_blocked_skips_write_set_and_close` `test_owner_blocked_applies_without_slice_token` |
| Resolved OB over-block | A resolved/closed OB row skips write-set / close | `test_resolved_owner_blocked_does_not_over_block` |
| Directive cap | Supervisor append grows the unfolded queue past `OPEN_DIRECTIVE_CAP` | `test_open_directive_cap_refuses_append_at_cap` |
| Audit-surface dodge | `a/../a/file` write-set skips a `pending-audit` surface | `test_pending_audit_blocks_normalized_audit_surface_overlap` |
| `max_rounds` | Exhausting the budget forges `completed` / a close | `test_max_rounds_budget` |
| Emit-only / timer-only no-close | PromptOnlyHost or DualTimer closes without applying a write-set | `test_prompt_only_host_never_closes` `test_dual_timer_host_never_closes` |
| Terminal no timer recreate | A later DualTimer fire reseeds a deleted task | `test_dual_timer_stays_deleted_after_terminal` |
| Mid-verify kill (resume) | After verify-green crash-before-close, resume re-applies the write-set | `test_verify_green_crash_resumes_verify_only` |
| Subprocess Verify red | Product `GateRunner` treats a red process as pass | `test_subprocess_verify_red_blocks_close` `test_cli_default_gate_is_fail_closed` |

Related claim table: [`PUBLIC_CLAIMS.md`](PUBLIC_CLAIMS.md).
