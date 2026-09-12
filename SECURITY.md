# Security

Runner red lines for compiled run directories. The skill library under
`skills/` is policy only. See also [`runner/README.md`](runner/README.md)
and [`docs/runner/RUNNER-INVARIANTS.md`](docs/runner/RUNNER-INVARIANTS.md)
(A14, A15).

## Workspace escape is denied

Executor write-set destinations are resolved and must stay
`relative_to` the workspace. Paths that escape the workspace — including
`../ledger.md` and other `run_dir` scoreboard files (`ledger.md`,
`directives.md`, `ops.md`, `status.json`) — are denied at the write gate.
A workspace symlink or hardlink (same inode) to those files is also
denied. Named edge writes stay `relative_to` `run_dir`.

## No secrets in fixtures

Fixtures under `runner/tests/fixtures/` are fictional (`taskcat`,
`shutterlog`). No secrets, tokens, credentials, or real client data.
Examples under `skills/loop-graph/examples/` follow the same rule.

## Runner must not `git push`

The runner never publishes a remote. It does not run `git push`. Close,
ledger writes, and Hosts stay local to the run directory and workspace.
Push remains an owner step outside this engine.

## Related fail-closed rules

- **Default-FAIL.** Close is a gate re-pass after an applied write-set.
  `NodeResult.ok` and model "DONE" are not close signals.
- Product Verify/smoke is a fail-closed subprocess (`cwd` = workspace).
- Safe CLI default is `--host prompt-only` (emit-only). `mock` is the
  coupled test loop, not the product path.
