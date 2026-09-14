# Ship-S4 — docs dry-run

Prove a stranger can follow **only** the root [README](../../README.md) and
[`runner/README.md`](../../runner/README.md) and succeed with `--host mock`
plus `--host prompt-only` on a fresh machine.

Authority: DISTRIBUTION-READINESS-v1 §S Track S4
("기여자가 README만 보고 새 머신에서 mock+prompt-only 성공 | 외부인 1회 성공 기록").
Contract: [`docs/runner/CONTRACT.md`](../runner/CONTRACT.md) §8,
[`docs/runner/RUNNER-INVARIANTS.md`](../runner/RUNNER-INVARIANTS.md) A6 / A18.

This file is the procedure + record sheet. It is **not** a fake external
human sign-off. A real external S4 sign-off is **owner-recorded later**.

---

## What "success" means

| Path | Documented command | Must happen | Must not happen |
|---|---|---|---|
| `--host prompt-only` | emit two `/loop` paste blocks and exit | rc 0; stdout has `/loop` + `executor.md` + `supervisor.md` | write-set apply; ledger/status mutation; close; wake/notify/dispatch verbs |
| `--host mock` | coupled test loop (not the product path) | rc 0; `Runner` ticks MockHost; `status.json` records a fail-closed attempt | close without gate re-pass; mutate committed `runner/tests/fixtures/` |

Close stays **Default-FAIL**. On `add-tests-to-cli`, product smoke is
`pytest -q` against an empty workspace, so mock typically ends
`status=failed`, `GAP-002` still open, no `test_dates.py`. That is
documented success — not a forged green close.

---

## Procedure (stranger, README only)

Do this on a machine that has Git + Python ≥ 3.11. Do not load `skills/`
as an engine. Do not `git push` from the runner.

1. Clone the repo. Read the root README repository-map row for
   [Runner CLI](../../runner/README.md), then that file's **5-minute
   quickstart**.
2. From `runner/`, create a venv and install editable with dev extras
   (the README install command):

   ```bash
   cd runner
   python -m venv .venv
   source .venv/bin/activate          # Windows: .venv\Scripts\activate
   python -m pip install -e ".[dev]"
   ```

   PowerShell (Windows native):

   ```powershell
   cd runner
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   python -m pip install -e ".[dev]"
   ```

3. **Copy** the fixture. `--host mock` writes `status.json` and creates
   `workspace/` under the run dir. Pointing it at
   `tests/fixtures/add-tests-to-cli` dirties the committed tree.

   ```bash
   cp -R tests/fixtures/add-tests-to-cli /tmp/add-tests-to-cli
   ```

   PowerShell (Windows native):

   ```powershell
   Copy-Item -Recurse tests\fixtures\add-tests-to-cli $env:TEMP\add-tests-to-cli
   ```

4. Safe default — emit-only:

   ```bash
   longgraph run --host prompt-only /tmp/add-tests-to-cli
   ```

   Expect two `/loop` lines (executor + supervisor). `ledger.md` and
   `status.json` stay byte-identical to the copy. Omitting `--host` is
   the same (`prompt-only`).

5. Coupled test loop:

   ```bash
   longgraph run --host mock /tmp/add-tests-to-cli
   ```

   Expect a one-line status (`failed ledger=active` on this fixture).
   `GAP-002` stays open. The committed fixture under
   `runner/tests/fixtures/` must be unchanged.

6. Fill the record below. Optional CI-shaped replay (same checks, clean
   temp venv):

   ```bash
   bash runner/scripts/ship-docs-dry-run.sh
   ```

---

## Record (blank)

Copy this block. Fill every field.

```text
machine OS:
Python version:
install command:
fixture: runner/tests/fixtures/add-tests-to-cli (copied to: )
longgraph run --host prompt-only: pass / fail
longgraph run --host mock: pass / fail
pass/fail:
time:
SHA:
operator: (human name — leave blank on CI/harness runs)
notes:
```

---

## Example evidence (template / CI harness — not an external human)

The block below is a **filled example** from this PR's deterministic
harness (`runner/scripts/ship-docs-dry-run.sh` +
`runner/tests/test_docs_dry_run.py`). It is **not** a substitute for a
real external contributor sign-off. Owner records that later.

```text
machine OS: Linux-6.12.94+-x86_64-with-glibc2.39
Python version: 3.12.3
install command: python -m virtualenv <tmp>/venv && source <tmp>/venv/bin/activate && python -m pip install -e ".[dev]"
fixture: runner/tests/fixtures/add-tests-to-cli (copied under a temp work dir)
longgraph run --host prompt-only: pass (rc=0, emit-only, no close)
longgraph run --host mock: pass (rc=0, fail-closed, no close)
committed fixtures unchanged: pass
pass/fail: pass
time: 0.5s CLI (venv create + pip extra); harness UTC 2026-09-11T23:33:14Z
SHA: 90cfcaebf5b7533afa0c08ae2cbd08a9336f44c9
operator: CI/harness (not an external human)
notes: Coding model for this agent is grok-4.6. Started from main@f313ed3 (H2).
       This agent image lacked ensurepip (`python -m venv` failed); the
       harness fell back to `virtualenv` then editable install. GitHub
       `setup-python` provides `venv`. A real external S4 sign-off is
       owner-recorded later.
```

---

## README gap found (Critical lie, fixed on this PR)

`runner/README.md` previously documented:

```bash
longgraph run --host mock tests/fixtures/add-tests-to-cli
```

That command uses the committed fixture as `run_dir`. MockHost's
`Runner` defaults `workspace` to `run_dir/workspace` and the fail-closed
`GateRunner` writes `status.json` (item retries) into that same tree.
A stranger who followed the README literally would dirty
`runner/tests/fixtures/add-tests-to-cli`.

**Fix (smallest honesty patch):** the 5-minute path now `cp -R` the
fixture first and points both `--host prompt-only` and `--host mock`
at the copy. Root README gained the same 5-minute install+run so the
dry-run procedure does not depend on a missing step. Guard:
`test_docs_dry_run_readme_copy_before_mock`.

No Host / CLI semantics were changed. No new Host code.

---

## Out of scope

S5 CI matrix ([SUPPORT.md](SUPPORT.md); sibling track), Release tag,
ApiHost, prompt compiler, live DualTimer multi-day soak, merging later
ship PRs, inventing an external human success record.
