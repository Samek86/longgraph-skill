# Runner CONTRACT (Phase 0 / 1a / 1b)

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
| `owner_blocked` | owner-blocked table | Live `OB-xxx` ids. `(none)` / `（none）` / empty → `[]`. |

### 1.2 Current slice

Rewritten in place. Keys are the human labels (spaces included):

| Key | Meaning |
|---|---|
| `Item` | The independently verifiable workset for this round |
| `Write set` | Exact paths (or `read-only`) |
| `Context` | `ops.md` context id(s), e.g. `C-01` |
| `Verify` | One narrow command |
| `Done when` | One observable condition |

Access: `state.current_slice["Write set"]` or `state.current_slice.Item`.

### 1.3 Findings path

`blocked-on: findings#<id>` resolves to **`findings/<id>.md`**.
Do not use a singular `findings.md` as the golden path.

### 1.4 Pending promotion / pending-audit

While `milestone_gate` is `pending-audit`, the executor must not **advance**
the milestone (no next-milestone write-set, no flip to `passed` without an
acceptance directive). Lane work that is already registered and disjoint
from the audit surface may continue; the runner still treats milestone
advancement as blocked.

### 1.5 Terminal ledger

`run_status` in `{exit-ready, stalled, closed}` is terminal. Both node
timers stop. `status.json` may be `"completed"` **only** when the ledger
is already terminal (see §3).

### 1.6 Default-FAIL (close semantics)

An item is **FAIL until its gate re-passes**.

- The runner runs the Verify (and required smoke/full) gate **after** the
  executor tick.
- **Close** happens only when that gate is green on this attempt.
- `NodeResult.ok` is informational and **must be ignored** for close.
- A model utterance of `DONE` / "done" is not a signal. There is no
  close path that trusts the node result.
- A red gate increments `metadata.itemRetries[item_id]` and leaves the
  item open (Default-FAIL). Exhausting `max_retries` stops the run
  without forging a close.

---

## 2. Directives (`directives.md`) — supervisor is the only writer

Live queue, not a log. The executor reads it and folds above
`last_directive_folded`. The executor **never writes** this file.
The supervisor **never writes** the ledger.

A scout **dispatch** is a numbered correction (or an explicit dispatch
line) naming `brief <id>`. Scout output does not land here.

---

## 3. Ops (`ops.md`) — ambient; nodes do not treat it as an edge

Runner-parsed knobs (line form `key: value`, or the Build / test alias):

| Key | Meaning |
|---|---|
| `max_rounds` | Hard budget. When `progress.completedRounds >= max_rounds`, stop. Not a close. |
| `max_retries` | Per-item retry cap (see §5). |
| `smoke` | Command run **before a new item** starts. Alias: a Build / test line beginning with `smoke`. |

Missing knobs: `max_rounds` / `max_retries` default to a high backstop
(100 / 3) so fixtures without them still parse; tests that care set them
explicitly.

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
