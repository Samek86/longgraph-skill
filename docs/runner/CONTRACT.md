# Runner CONTRACT (Phase 0 / 1a / 1b / 1c)

Field names, close semantics, and fixture authorship for the runner.
Skill templates keep their human headings; the runner parses the fields
below. See [`AUTHORITY.md`](AUTHORITY.md).

---

## 1. Ledger (`ledger.md`) — single scoreboard, executor is the only writer

### 1.1 Status header

| Field | Header line | Values / notes |
|---|---|---|
| `next_item` | `Next unclosed work item:` | Rest of the line. **Strip inline markdown code spans** (`…`) before compare. |
| `last_directive_folded` | `Last directive folded:` | `none` or a `D-xxx` id. Fixtures must write the line even when the upstream example omitted it. |
| `milestone_gate` | `Milestone gate:` | `open` \| `pending-audit` \| `passed` \| `n/a` (strip backticks; ignore trailing commentary). |
| `run_status` | `Run status:` | `active` \| `exit-ready` \| `stalled` \| `closed` (first token, strip backticks). |
| `blocked_on` | `blocked-on:` | Pointer such as `findings#s3-client`. May live in the Current slice or a round line. Absent → `None`. |
| `open_gaps` | Debt & gap register | Live `GAP-xxx` row ids. Skip rows whose text marks the gap resolved/closed. Empty prose / no rows → `[]`. |
| `owner_blocked` | owner-blocked table | Live `OB-xxx` ids. Skip rows whose text marks the decision resolved/closed (same closed-words as `open_gaps`). `(none)` / `（none）` / empty → `[]`. Live ids apply to this run's Current slice — no literal `OB-xxx` token is required in the slice text. |

### 1.2 Current slice

Rewritten in place. Keys are the human labels (spaces included):

| Key | Meaning |
|---|---|
| `Item` | The independently verifiable workset for this round |
| `Write set` | Exact paths (or `read-only`). Resolved inside the workspace; relative escapes, symlinks, and hardlink/inode aliases to `run_dir` scoreboard files (`ledger.md`, `directives.md`, `ops.md`, `status.json`) are denied. |
| `Context` | `ops.md` context id(s), e.g. `C-01` |
| `Verify` | One narrow command |
| `Done when` | One observable condition |

Access: `state.current_slice["Write set"]` or `state.current_slice.Item`.

### 1.3 Findings path

`blocked-on: findings#<id>` resolves to **`findings/<id>.md`**.
Do not use a singular `findings.md` as the golden path.

### 1.7 Rounds log (bounded)

The Rounds log keeps the last `KEEP_ROUNDS` (default 5) **live round
entries**. An entry is one `- R…` line **or** one `### Round N` section
(heading plus body until the next entry). Mixed logs are allowed; both
shapes rotate. Older entries move to `archive/rounds.md` (create with a
heading if missing). `KEEP_ROUNDS` is read from `ops.md` when present.
The executor is the only writer of the ledger and of `archive/rounds.md`.

### 1.4 Pending promotion / pending-audit

While `milestone_gate` is `pending-audit`, the executor must not **advance**
the milestone (no next-milestone write-set, no flip to `passed` without an
acceptance directive). Lane work that is already registered and disjoint
from the audit surface may continue; the runner still treats milestone
advancement as blocked.

The runner blocks the executor write-set only when the **Current-slice
write-set** is the next-milestone surface: the Current-slice `Item` starts
with `M\d+` and the write-set is not `read-only`, **or** the write-set
paths overlap Pending promotion `Audit surface:`. Overlap compares
**normalized** paths (`relative_to` a dummy root / `normpath`), not raw
string equality — `migrations/../migrations/drop_blob.sql` is the same
file as `migrations/drop_blob.sql`. An `M\d+` token in `next_item` or a
lane `Item` is not enough to stop the run.

**Acceptance-release marker.** A live correction releases the gate when
it contains the exact token `ACCEPT-GATE` (ASCII, case-insensitive), or
when its first-line verb (the third `·`-separated field) is
`accept-gate`. The runner folds that packet after an applied write-set
(any Host that sets `NodeResult.applied`), flips `Milestone gate` to
`passed`, and advances `Last directive folded` — the executor never
self-passes. A same-tick next-milestone unblock may also fold before
apply on an applied-work Host. A bare `accept` verb without
`ACCEPT-GATE` is a lane/item verdict and does not flip the gate.

### 1.5 Terminal ledger

`run_status` in `{exit-ready, stalled, closed}` is terminal. Both node
timers stop. GrokBotDualTimerHost deletes the invoking node's timer and
returns **before** any Timers-cell seed or scheduler create; a later
fire must not recreate a deleted task. `status.json` may be
`"completed"` **only** when the ledger is already terminal (see §3).

### 1.6 Default-FAIL (close semantics)

An item is **FAIL until its gate re-passes**.

- The runner runs the Verify (and required smoke/full) gate **after** an
  **applied** executor write-set (or on resume-Verify). Emit-only,
  timer-only, and no-op ticks (`NodeResult.applied` is false) never
  close, even if a mock Verify would pass.
- **Close** happens only when that gate is green on this attempt **and**
  the tick applied work (or resumed Verify after a prior applied write).
- `NodeResult.ok` is informational and **must be ignored** for close.
- A model utterance of `DONE` / "done" is not a signal. There is no
  close path that trusts the node result.
- Empty Verify **fails** (do not close). `n/a` Verify **skips** the gate
  and skips close; the item stays open. Neither forges a green close.
- Product Verify / smoke is a **fail-closed subprocess** (`cwd` = the
  workspace, or the documented run root the caller passed). Non-zero
  exit fails. `GateRunner()` with no `script=` hook never defaults to
  `passed=True`; tests may still inject `script=` or an explicit
  `default=`.
- Live `owner_blocked` ids apply to the Current slice of this run (no
  literal `OB-xxx` token required in the slice text): no write-set, no
  close. Resolved/closed table rows are not live and must not over-block.
  Unlike `pending-audit`, a live OB has no lane-continue exception —
  any live id fails closed for this slice.
- `blocked-on: findings#<id>` with missing or incomplete findings: no
  executor write-set, no close; scout-only tick until
  `findings/<id>.md` marks **Status**: complete.
- A red gate increments `metadata.itemRetries[item_id]` and leaves the
  item open (Default-FAIL). Exhausting `max_retries` stops the run
  without forging a close.
- Green close **rewrites the live scoreboard**: the closed item leaves
  `open_gaps`; `Next unclosed work item` and Current slice advance, or
  `run_status` becomes terminal when nothing remains. Re-close of an
  already-retired item is idempotent (no second `completedRounds`, no
  re-applied write-set).

---

## 2. Directives (`directives.md`) — supervisor is the only writer

Live queue, not a log. The executor reads it and folds above
`last_directive_folded`. The executor **never writes** this file.
The supervisor **never writes** the ledger.

A scout **dispatch** is a numbered correction (or an explicit dispatch
line) naming `brief <id>`. Scout output does not land here.

### Watermark / rotate

On an applied executor tick (`NodeResult.applied` on any Host), the
runner reads live Corrections above `Last directive folded`, applies
each one or records an explicit no-op, and advances the watermark.
`ACCEPT-GATE` (see §1.4) is the apply that flips a pending milestone
gate; every other packet is a no-op fold. Close may fold again; a
second pass is a no-op once the watermark has moved.

Before the supervisor appends, move Corrections entries with IDs ≤ the
ledger watermark (`Last directive folded`) to `archive/directives.md`
(create with a heading if missing). Next ID = max(watermark, highest
live ID) + 1; never reuse rotated IDs. `OPEN_DIRECTIVE_CAP` (default 8,
from `ops.md` when present) is **append discipline**: do not add more
unfolded packets once the live queue is at the cap. The append helper
**refuses** (leaves the file unchanged) when
`len(unfolded_packets) >= OPEN_DIRECTIVE_CAP`. Callers rotate-before-append
so folded IDs leave the live queue first; rotation must **not** archive
packets the watermark has not passed — that silently drops unfolded
corrections. Supervisor state and STANDING are not rotated.

---

## 3. Ops (`ops.md`) — ambient; nodes do not treat it as an edge

Runner-parsed knobs (line form `key: value`, or the Build / test alias):

| Key | Meaning |
|---|---|
| `max_rounds` | Hard budget. When `progress.completedRounds >= max_rounds`, stop. Not a close. |
| `max_retries` | Per-item retry cap (see §5). |
| `smoke` | Command run **before a new item** starts. Alias: a Build / test line beginning with `smoke`. |
| `KEEP_ROUNDS` | Live Rounds log entries to keep (`- R…` or `### Round N`; default 5). Alias: `keep_rounds`. |
| `OPEN_DIRECTIVE_CAP` | Live Corrections append cap (default 8). Does not archive unfolded packets. Alias: `open_directive_cap`. |

Missing knobs: `max_rounds` / `max_retries` default to a high backstop
(100 / 3) so fixtures without them still parse; tests that care set them
explicitly.

The Timers table is ambient, not an edge. On first fire each node writes
**only its own** Timer ID cell (`pending` → real ID). The peer row is
untouched. GrokBotDualTimerHost is the product dual-timer path; it must
not reference `longgraph-dev-continue`.

---

## 4. Status (`status.json`) — runner-managed, required, atomic

Runner-managed runs **require** `status.json`. Writes are
`status.json.tmp` then `os.replace` (atomic `tmp` + `mv`).
Naive `cat > status.json` examples in older docs are **legacy** and must
not be copied into the runner.

Required additions for this phase:

```json
{
  "ownerEscalation": null,
  "metadata": {
    "itemRetries": {},
    "lastAttempt": null
  }
}
```

| Field | Meaning |
|---|---|
| `ownerEscalation` | `null` or a small choice-card object. Template seeds `null`. |
| `metadata.itemRetries` | `{ "<item_id>": <int> }` |
| `metadata.lastAttempt` | `{ "key": { "runId", "round", "item_id" }, "phase": "write" \| "verify" \| "verify_green" \| "closed" }` |

`status: "completed"` implies the ledger `run_status` is already terminal.
The runner must refuse to persist `completed` otherwise.

Missing `status.json` is tolerated only for **legacy skill-hosted** runs.
The runner will not start without the file.

---

## 5. Retry / idempotency

Idempotency key: `(runId, round, item_id)`.

- Re-entering the same key after a crash does not invent a new item.
- If `lastAttempt.phase == verify_green` and the process died before
  close, **resume Verify only** — do not re-apply the write-set.
- Retry count is `metadata.itemRetries[item_id]`, not a second scoreboard.

---

## 6. Fixture authorship

Fixtures under `runner/tests/fixtures/` are the **golden SoT** for parse
and MockHost tests.

Rules:

1. Adapt from `skills/loop-graph/examples/` when useful, then **normalize**
   to this CONTRACT. Do not vendor a raw example as the fixture.
2. Every fixture includes the file set in EXPANSION-PLAN Phase 0.
3. Synthesize any missing header / Current slice field the golden table
   names. `add-tests-to-cli` must include Current slice +
   `Last directive folded: none`.
4. Scout findings live at `findings/<id>.md`.
5. No secrets, no real client data. Fictional projects only
   (`taskcat`, `shutterlog`).
6. `archive/.gitkeep` keeps the directory; golden parse does not read
   archives.

---

## 7. Public parse API

`longgraph.state.parse_run(run_dir) -> RunState`

`RunState` exposes the ledger fields in §1 plus `ops` and `status`.
`next_item` is already span-stripped.

---

## 8. CLI Host (`longgraph run --host`)

| Value | Host | Role |
|---|---|---|
| `prompt-only` | `PromptOnlyHost` | **Safe default.** Emit two `/loop` paste blocks and exit. |
| `grok-bot` | `GrokBotDualTimerHost` | Product DualTimer. Independent timers; Runner does not serial-tick peers. |
| `mock` | `MockHost` | Coupled test loop only. Not the product path. |

Omitting `--host` is emit-only (`prompt-only`). The CLI must not silently
treat MockHost as the product default.
