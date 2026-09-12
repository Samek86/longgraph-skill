# Ship-D2 tip re-pass (eeb7591)

Hostile source review of the runner on **main tip**
`eeb759164f42b5ceb5fbeb25405a027286e3b93a`
(`fix(runner): deny hardlink scoreboard clobber (M-TIP-1)`).

Authority: [`docs/runner/CONTRACT.md`](../runner/CONTRACT.md),
[`docs/runner/RUNNER-INVARIANTS.md`](../runner/RUNNER-INVARIANTS.md),
[`docs/runner/AUTHORITY.md`](../runner/AUTHORITY.md),
public claims P1–P10, [`KNOWN_ISSUES.md`](../../KNOWN_ISSUES.md).
Prior tip @ `2b9e516` had Critical C-TIP-1 (pending-audit path-alias)
and C-TIP-2 (OB token strip) — fixed in #19. M-TIP-1 hardlink and
M-TIP-2 ACCEPT-GATE fold landed in the #20/#21 stack. This pack is
the **in-repo** re-pass of `eeb7591`, not a replay of R2 / S3.

Scope: `runner/longgraph/{nodes,hosts,state,rotate,gates,cli}.py`
plus the merge-gate suite. Token/$ telemetry, ApiHost, prompt-compiler,
and LangGraph stay deferred. This document does **not** invent live
DualTimer multi-day soak logs (M-R2-3 / M-TIP-3 remains owner
evidence) and does **not** claim a D2 publish or a new tag.

## Method

Contract checklist first (P1–P10 / A1–A18). Then cross-read the
close path, write gate, pending-audit overlap, OB binding, findings
resolution, and DualTimer `schedule()` / `invoke()` / CLI
`--host grok-bot`. Then throwaway probes under `/tmp` for every
candidate Critical: hardlink/symlink variants (scoreboard + audit
surface), pending-audit spellings, OB without a slice token, DualTimer
schedule-on-terminal, findings path escape. Line cites are files
actually read on this tip. Pre-fix C-TIP-3 is labeled **at eeb7591**.

## Verdict

| Severity | Remaining |
| --- | --- |
| Critical | **0** |

**D2 Critical=0 MET** after the same-PR C-TIP-3 close (audit-surface
hardlink/symlink alias). C-TIP-1 / C-TIP-2 / M-TIP-1 / M-TIP-2
re-checked **CONFIRMED-FIXED**. Critical count remaining: **0**.

## Re-check of named tip findings

| Id | Claim | Status |
| --- | --- | --- |
| C-TIP-1 | Pending-audit path-alias (`a/../a/file`) cannot dodge the audit surface | **CONFIRMED-FIXED** |
| C-TIP-2 | Live `owner_blocked` binds with no `OB-xxx` token in the slice | **CONFIRMED-FIXED** |
| M-TIP-1 | Workspace hardlink/symlink cannot clobber `run_dir` scoreboard files | **CONFIRMED-FIXED** |
| M-TIP-2 | ACCEPT-GATE fold runs after any applied write-set, not MockHost-only | **CONFIRMED-FIXED** |

### C-TIP-1 — CONFIRMED-FIXED

- **Evidence.** `normalize_declared_path`
  (`runner/longgraph/state.py` 149–166) collapses `.` / `..`.
  `current_slice_is_next_milestone_surface`
  (`runner/longgraph/nodes.py` 139–144) intersects normalized
  write-set and `Audit surface:` paths. Probe:
  `migrations/../migrations/drop_blob.sql`,
  `migrations/./drop_blob.sql`, `./migrations/drop_blob.sql`,
  `migrations//drop_blob.sql`, `foo/../migrations/drop_blob.sql`
  → `stopped_reason=pending-audit`, executor not invoked.
- **Regression.** `test_pending_audit_blocks_normalized_audit_surface_overlap`.

### C-TIP-2 — CONFIRMED-FIXED

- **Evidence.** `current_slice_owner_blocked`
  (`runner/longgraph/state.py` 129–137) is `bool(state.owner_blocked)`
  — no slice-token match. Runner skips write-set/close
  (`nodes.py` 574–576). Probe on `migrate-blob-storage` with every
  `OB-001` token stripped from Item / Write set / Verify / Done when /
  next_item: `owner_blocked=["OB-001"]`, executor not invoked, no close.
- **Regression.** `test_owner_blocked_applies_without_slice_token`.

### M-TIP-1 — CONFIRMED-FIXED

- **Evidence.** `EdgeWriter._aliased_protected_run_file`
  (`runner/longgraph/hosts.py` 97–109) denies `os.path.samefile`
  aliases to `ledger.md` / `directives.md` / `ops.md` /
  `status.json`. Probe: workspace symlink, nested hardlink
  `workspace/sub/hard-ledger.md`, and directory symlink
  `workspace/evil → run_dir` then `evil/ledger.md` — all
  `WriteDenied`, scoreboard bytes unchanged.
- **Regression.** `test_executor_cannot_clobber_scoreboard_via_hardlink`.

### M-TIP-2 — CONFIRMED-FIXED

- **Evidence.** After `NodeResult.applied`, runner calls
  `_fold_accept_gate_after_apply` (`nodes.py` 390–401, 632–634)
  regardless of Host. Pre-apply same-tick release stays on
  `_applied_work_path()` (`nodes.py` 355–356). Probe: non-MockHost
  that applies `docs/lane-policy.md` with a live ACCEPT-GATE packet
  → `milestone_gate=passed`, watermark `D-004`.
- **Regression.** `test_accept_gate_folds_after_applied_non_mock_host`.

## Critical

None remaining.

One new hole reproduced on eeb7591 and closed in this PR:

### C-TIP-3 — pending-audit hardlink/symlink audit-surface dodge (FIXED)

- **Claim.** While `milestone_gate` is `pending-audit`, a lane
  write-set that names the same file as Pending promotion
  `Audit surface:` must not apply. Overlap includes path spelling
  **and** workspace inode / symlink aliases (A8, CONTRACT §1.4).
- **Evidence (at eeb7591).** Overlap was string-only after
  `normalize_declared_path`. Probe: workspace
  `migrations/drop_blob.sql` already present; hardlink (and a
  second probe: symlink) at `lane/alias.sql`; Current-slice Item
  `GAP-010 lane via alias`, Write set `lane/alias.sql`, gate
  `pending-audit`. `current_slice_is_next_milestone_surface` was
  False. MockHost applied the write-set (inode write clobbered the
  audit-surface file) and closed `GAP-010`. Same result via
  symlink. That is a blocked write-set apply.
- **Invariant.** A8, CONTRACT §1.4, P1 (no close of an advancement
  surface while pending).
- **Minimal fix (this PR).** `_workspace_declared_alias`
  (`nodes.py` 99–118) treats `os.path.samefile` and symlink
  `Path.resolve` equality as overlap.
  `current_slice_is_next_milestone_surface` takes `workspace`
  (`nodes.py` 145–152, 547–552).
- **Regression.** `test_pending_audit_blocks_audit_surface_hardlink_alias`.

## Major

Open capability / soak residuals only. Coding Majors from S2 / S3 /
the tip containment stack stay fixed.

### M-TIP-3 — product DualTimer Host is still timer-only (open)

Same residual as M-R2-3 / M-S3-3. `GrokBotDualTimerHost.invoke`
returns `applied=False` (`hosts.py` 581, 586). CLI `--host grok-bot`
never closes. This pack does **not** invent multi-day soak logs.
Owner evidence.

### M-R2-1 / M-R2-2 / M-ADV-1 / M-ADV-2 / M-TIP-1 / M-TIP-2 — FIXED

Already on this tip (and C-TIP-1 / C-TIP-2 re-check above). See
[`KNOWN_ISSUES.md`](../../KNOWN_ISSUES.md).

## Minor / Nit / deferred

- **`_CLOSED_WORDS` matches `closed` inside “not yet closed”.**
  `_parse_owner_blocked` (`state.py` 242–252) skips a row whose
  Why-now cell says `not yet closed — waiting owner`. Fail-open
  for that wording; the same heuristic is used for gaps (D2
  M-R2-1). Golden fixtures do not use that phrase. Not a path
  alias or forge-close. Left as a heuristic residual.
- **`ACCEPT-GATE` matches anywhere in the packet.** Spec-faithful
  (`rotate.py` `is_accept_gate_packet`). A commentary mention
  would flip the gate.
- **`status.json` `ownerEscalation` is not schema-checked on read.**
- **Product Verify is `subprocess` + `shell=True`** (`gates.py`
  71–88), `cwd` = workspace. Trusted compiled ledger.
- **Token / $ telemetry, ApiHost, prompt-compiler.** Deferred.
- **No live DualTimer soak.** Owner-only (do not fabricate).

## Other probes that held (not Critical)

| Probe | Result |
| --- | --- |
| `findings#../decoy` / `#..` / `#foo/bar` / `#/abs` | `safe_findings_ident` None; scout-only (`state.py` 96–114, `nodes.py` 438–451) |
| Findings file symlink to a complete decoy outside `findings/` | `relative_to(findings/)` fails; no write-set |
| DualTimer `schedule()` on `Run status: closed` | zero scheduler tasks (`hosts.py` 537–540) |
| schedule → invoke → terminal → schedule → supervisor invoke | no recreate |
| CLI `--host grok-bot` on `stalled` | `rc=0`, Timers cells unseeded |
| PromptOnlyHost / DualTimer + `GateRunner(default=True)` | never close |
| Empty / `n/a` Verify | no close; `n/a` skips executor |
| `GateRunner()` + `false` | `passed=False` |
| Write-set `../ledger.md` | `WriteDenied` escape |

## Owner-only residuals

New git tags, GitHub Releases, live DualTimer product soaks, and
merge to `main` are owner-only. Annotated tag `0.3.0-beta` and its
prerelease already exist at `eeb7591` (owner-cut). This PR does
not create a tag or Release and must not be merged without owner
ack.
