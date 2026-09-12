# Changelog

All notable changes to the longgraph runner and this fork's ship surface
are documented here.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

**Git tags and GitHub Releases are owner-only.** This tree does not create
them. The SemVer string in [`runner/pyproject.toml`](runner/pyproject.toml)
may read `0.3.0-beta` while no matching tag exists.

## [Unreleased]

### Added

- D1 closeout scaffolding: [public claims](docs/ship/PUBLIC_CLAIMS.md) bind
  DISTRIBUTION-READINESS-v1 §1.1 P1–P10 to existing pytest names;
  [S3 negative battery](docs/ship/S3_NEGATIVE_BATTERY.md) indexes the
  negative suite; `test_public_claims_mapped_tests_exist` fails if a
  mapped name leaves the collected suite.
- [Known issues](KNOWN_ISSUES.md) — soak / DualTimer timer-only /
  deferred telemetry residuals.
- S5 support surface freeze: [SUPPORT.md](docs/ship/SUPPORT.md) binds
  CLI hosts (`prompt-only`, `grok-bot`, `mock`), Python 3.11 / 3.12,
  and `ubuntu-latest`. The validate `runner` job is a matrix of those
  two Pythons. Meta-tests: `test_support_surface_doc_exists`,
  `test_ci_runner_matrix_covers_supported_python`,
  `test_support_hosts_match_cli`.

### Fixed

- D2 coding Majors: `_parse_owner_blocked` skips resolved/closed rows
  (M-R2-1 / M-S3-1); `append_correction_packet` refuses at
  `OPEN_DIRECTIVE_CAP` (M-R2-2 / M-S3-2); pending-audit overlap uses
  normalized paths (prior M-ADV-1); live `owner_blocked` binds without
  a slice token (prior M-ADV-2 / CONTRACT §1.6). M-R2-3 DualTimer
  soak stays owner evidence.

## [0.3.0-beta] — planned string (untagged)

Version in `runner/pyproject.toml`. **No git tag is cut from this tree.**

### Added

- Phase 0: runner CONTRACT / INVARIANTS / normalized fixtures /
  `test_golden_parse`.
- Phase 1a: MockHost MVP, Default-FAIL close, CLI
  `longgraph run|status|stop`.
- Phase 1b: PromptOnlyHost dual `/loop` emit (no writes, no close).
- Phase 1c: `GrokBotDualTimerHost` — two independent timers, no wake
  edge, own-cell seed, terminal-before-seed.
- H1: CLI `--host prompt-only|grok-bot|mock`. Safe default is
  emit-only `prompt-only`. `mock` stays the coupled test loop.

### Fixed

- C1–C4: green close retires the live scoreboard; `blocked-on` with
  missing/incomplete findings is scout-only; empty Verify fails;
  `n/a` Verify skips (does not pass); emit-only / timer-only ticks
  never close.
- H0a / M3: write-set destinations resolve inside the workspace;
  executor cannot clobber `run_dir` scoreboard files via `../`.
- H0b: product `GateRunner` is a fail-closed subprocess (`cwd` =
  workspace). `GateRunner()` never defaults to `passed=True`.
- H0c / M4 / M5: DualTimer deletes the invoking node's timer before
  any seed/create on a terminal ledger; a later fire does not recreate.
  Unscheduled scout ticks are a no-op.
- H2 / M1 / M2 / M7: `pending-audit` blocks only the Current-slice
  next-milestone write-set (disjoint lane work continues);
  `ACCEPT-GATE` is the acceptance-release marker; applied-path
  executor folds live corrections and advances the watermark; golden
  `### Round N` sections rotate with `- R…` lines.

### Changed

- Close remains **Default-FAIL**. Emit-only and timer-only ticks never
  close. DualTimer Host does not apply write-sets.

[Unreleased]: https://github.com/Samek86/longgraph-skill/compare/main...HEAD
[0.3.0-beta]: https://github.com/Samek86/longgraph-skill/commits/main
