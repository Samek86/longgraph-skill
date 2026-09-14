# Changelog

All notable changes to the longgraph runner and this fork's ship surface
are documented here.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

**New git tags and GitHub Releases are owner-only.** Agents must not
create them. Prior tag `0.3.0-beta` and its GitHub prerelease already
exist at `eeb7591` (do not retarget). Lightweight tag `0.4.0-rc.1`
and GitHub prerelease already exist at `a4cce0f`. This tree does not
cut **new** tags.

## [Unreleased]

Further work after the `0.4.0-rc.1` candidate lands here. Tag
`0.4.0-rc.1` and its GitHub prerelease already exist at `a4cce0f`.
Owner D2 *stable* / non-rc publish ack is **not** done. Live DualTimer
soak (M-R2-3) remains owner-only.

### Added

- Windows native runner support (PowerShell / cmd, not WSL-only).
  S5 OS freeze is now `ubuntu-latest` + `windows-latest`; the validate
  `runner` job is an OS × Python 3.11/3.12 matrix. Portable `true` /
  `false` Verify tokens; fail-closed path containment across drives,
  NTFS case-fold, and junction/symlink aliases.

### Fixed

- Runner gates no longer depend on `/bin/true` / `/bin/false`.
- Declared-path normalization uses a drive-aware dummy root.
- Docs dry-run / soak tests drive the Python entries so Windows CI
  does not require a bash wrapper.

## [0.4.0-rc.1] — 2026-09-12 (prerelease; tag exists at `a4cce0f`)

Version in `runner/pyproject.toml`. **Coding D2 evidence pack READY.**
Lightweight tag `0.4.0-rc.1` and GitHub prerelease exist at `a4cce0f`
(`a4cce0f54fc887e91158dcf630d328f2af709061`). History: #24 @
`3824ef4` then #25 reconcile, then the tag object at tip `a4cce0f`.
Owner D2 *stable* / non-rc publish ack is **not** done. This section
does **not** claim DualTimer soak happened.

Go/No-Go: [`docs/ship/D2-GO-NOGO.md`](docs/ship/D2-GO-NOGO.md).

### Added

- D2 Go/No-Go checklist (DISTRIBUTION-READINESS-v1 §8) with concrete
  SHAs and evidence links for tip `a4cce0f` (PR #25; history #24 @
  `3824ef4` then #25 reconcile). Owner-only rows stay unchecked: live
  DualTimer soak (M-R2-3), D2 *stable* publish ack. Tag/Release
  `0.4.0-rc.1` is MET (prerelease at `a4cce0f`).
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
- Tip re-pass evidence: [ADVERSARIAL-TIP.md](docs/ship/ADVERSARIAL-TIP.md)
  on tip `eeb7591` (main advanced to `5de40a9`; C-TIP-3 closed).
  Meta-test `test_adversarial_tip_doc_exists`.
- Tip mock soak N=50 evidence pack for `5de40a9`:
  [`docs/ship/soak/tip-5de40a9-n50-mock/`](docs/ship/soak/tip-5de40a9-n50-mock/).
  Valid for #25 tip `a4cce0f` (docs-only after #24 @ `3824ef4`).
  Meta-test `test_tip_soak_evidence_pack_exists`. Live DualTimer soak
  remains owner-only. Agents must not create **new** tags.

### Fixed

- C-TIP-3: `pending-audit` blocks a workspace hardlink or symlink
  alias to the audit surface (same file as a declared `Audit surface:`
  dest). Path-spelling overlap (C-TIP-1) already existed.
- M-TIP-1: executor write-set cannot clobber `run_dir` scoreboard
  files via workspace hardlink or symlink alias (`os.path.samefile`).
  Relative-escape and symlink-via-`resolve` deny already existed.
- M-TIP-2: ACCEPT-GATE fold runs after any applied write-set (not
  MockHost-only). Other packets still fold on close. Pre-apply
  same-tick next-milestone release stays on the applied-work Host
  path. Emit/timer hosts still do not apply.

- D2 coding Majors: `_parse_owner_blocked` skips resolved/closed rows
  (M-R2-1 / M-S3-1); `append_correction_packet` refuses at
  `OPEN_DIRECTIVE_CAP` (M-R2-2 / M-S3-2); pending-audit overlap uses
  normalized paths (prior M-ADV-1); live `owner_blocked` binds without
  a slice token (prior M-ADV-2 / CONTRACT §1.6). M-R2-3 DualTimer
  soak stays owner evidence.

## [0.3.0-beta] — 2026-09-12 (owner-cut prerelease)

Version in `runner/pyproject.toml` at tag time. Annotated tag
`0.3.0-beta` points at `eeb759164f42b5ceb5fbeb25405a027286e3b93a`.
New tags and GitHub Releases remain owner-only; agents must not
create them.

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

[Unreleased]: https://github.com/Samek86/longgraph-skill/compare/0.4.0-rc.1...HEAD
[0.4.0-rc.1]: https://github.com/Samek86/longgraph-skill/releases/tag/0.4.0-rc.1
[0.3.0-beta]: https://github.com/Samek86/longgraph-skill/releases/tag/0.3.0-beta
