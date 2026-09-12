# Ship-S1 soak protocol

Repeatable multi-fixture soak for later **D2 Go/No-Go**. This is a *harness +
evidence pack*, not a live multi-day product executor and not LonggraphDev
`continue`.

Authority: [`docs/runner/CONTRACT.md`](../runner/CONTRACT.md),
[`docs/runner/RUNNER-INVARIANTS.md`](../runner/RUNNER-INVARIANTS.md),
[`docs/runner/EXPANSION-PLAN.md`](../runner/EXPANSION-PLAN.md).

---

## What it exercises

The harness copies **≥3 heterogeneous** golden fixtures from
[`runner/tests/fixtures/`](../../runner/tests/fixtures/) into an isolated temp
workspace (committed fixtures are never mutated) and ticks each one **N** times.

| Fixture | Why it is in the set |
|---|---|
| `add-tests-to-cli` | open GAP + real Verify/smoke commands (fail-closed) |
| `migrate-blob-storage` | live `owner_blocked` / `n/a` Verify; owner card stays manual |
| `scout-library-choice` | `blocked-on: findings#…` + findings path |

Default host is **`mock`** (coupled test loop, same fail-closed `GateRunner` as
`longgraph run --host mock`). **`prompt-only`** is emit-only smoke (CLI paste
blocks; no write-set, no close). DualTimer / `grok-bot` is not the default soak
path; timer-zombie is scored only if that path is exercised.

`longgraph run --host mock` has no `--steps` flag (always `Runner.run()` default
8). The harness therefore drives public `Runner.run(steps=1)` × N so N is the
tick count.

---

## How to run

From the repo root, with the runner installed (`cd runner && python3 -m pip install -e ".[dev]"`):

```bash
# CI / local smoke (also the script default)
bash scripts/ship-soak.sh --rounds 2 --host mock
bash scripts/ship-soak.sh --rounds 5 --host mock

# Production D2 evidence (tick budget)
bash scripts/ship-soak.sh --rounds 50 --host mock

# Emit-only smoke
bash scripts/ship-soak.sh --rounds 2 --host prompt-only
```

Optional fixture paths or names after the flags. `--out DIR` writes this run's
evidence there instead of `.longgraph-ship/soak/<run-id>/`.

### Production N

D2 needs **N ≥ 50 ticks per fixture** *or* a **≥ 24h** wall-clock soak. This
harness is **tick-counted**. A 24h wall-clock run is operator-owned (do not
confuse it with Grok Bot product timers or LonggraphDev continue). Record the
chosen budget on the evidence `SUMMARY.md`.

---

## Pass criteria

All of the following must be **0** (or N/A as noted):

| Check | Fail when |
|---|---|
| Scoreboard pollution | Committed fixtures change; isolated write escapes `run_dir` / workspace; workspace gains `ledger.md` / `directives.md` / `ops.md` / `status.json`; unexpected clobber of those edges (including isolated `ops.md` under mock / prompt-only) |
| Re-close storm | Same item closed repeatedly without progress (duplicate close markers, duplicate `closedItems`, or `completedRounds` increment without a new unique close) |
| Timer zombie | DualTimer / timer recreate after a terminal ledger **if that path is exercised**. mock / prompt-only: `not_exercised` (counts as 0) |
| Owner escalation | Harness auto-acks `ownerEscalation` or closes a live Current-slice `owner_blocked` item. Owner reply stays **manual only** |
| Uncaught exception | Any traceback from the runner / CLI during a tick |
| `max_rounds` | `completedRounds` exceeds `ops.max_rounds` without a clean stop (`paused` / `stopped_reason=max_rounds` / other terminal stop) |

Green closes under fail-closed gates are **not** required for a harness pass.
MockHost write-set content is a stub; product Verify/smoke is fail-closed, so
fixtures with real `pytest` commands typically retry and stop without forging a
close. That is expected and still a valid scoreboard-safety soak.

---

## Evidence layout

| Kind | Path | Git |
|---|---|---|
| Protocol (this file) | [`docs/ship/SOAK.md`](SOAK.md) | committed |
| Templates | [`docs/ship/soak/README.md`](soak/README.md), [`docs/ship/soak/EVIDENCE_TEMPLATE.md`](soak/EVIDENCE_TEMPLATE.md) | committed |
| Tip mock N=50 (this tree) | [`docs/ship/soak/tip-5de40a9-n50-mock/`](soak/tip-5de40a9-n50-mock/) | **committed** (SUMMARY + compact traces) |
| Live scratch | `.longgraph-ship/soak/<run-id>/` | **gitignored** |

Each harness run writes `SUMMARY.md` + `summary.json` plus per-fixture traces
(`ticks.jsonl` or `emit.txt`, `final-status.json`). Isolated work trees are
deleted after the run. Do not commit those work trees.

**Mock N=50 tick evidence is in-repo** at
[`soak/tip-5de40a9-n50-mock/`](soak/tip-5de40a9-n50-mock/) for tip
`5de40a9`. That pack is the D2 tick-budget close for `host=mock`. It
remains valid for post-soak tip `f2f493b`
(`f2f493b52a66daac172fdde9ace485297a32b297`): that commit is the
docs-only soak pack merge (PR #23) and does not change runner engine
files versus `5de40a9`. A live DualTimer multi-day / ≥24h wall-clock
soak remains **owner-only** (do not fabricate DualTimer logs). Go/No-Go:
[`D2-GO-NOGO.md`](D2-GO-NOGO.md).

---

## Attach for D2 Go/No-Go

1. Production tick budget: `--rounds 50` on `mock` (this tree already has
   that pack), **or** a documented ≥24h owner wall-clock run.
2. Point reviewers at
   [`docs/ship/soak/tip-5de40a9-n50-mock/SUMMARY.md`](soak/tip-5de40a9-n50-mock/SUMMARY.md)
   (and `summary.json`). Scratch copies may still land under
   `.longgraph-ship/soak/<run-id>/`.
3. State fixture names, N (or wall-clock), host, and the zero-counts
   including `max_rounds` clean.
4. Do not treat a CI smoke (`N=2` / `N=5`) as D2 evidence.

CI gates the committed tip pack via `test_tip_soak_evidence_pack_exists`
(file + field checks; it does **not** re-run 50 ticks).

---

## Out of scope (this protocol)

- Git tags / GitHub Releases / merging
- Inventing LangGraph, wake edges, ApiHost, or a prompt compiler
- Changing Default-FAIL / Host semantics
- Adversarial FINDINGS rewrite (Ship-S2)
- Grok Bot product timers as LonggraphDev continue
