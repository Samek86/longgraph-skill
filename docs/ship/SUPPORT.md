# Support surface (DISTRIBUTION-READINESS-v1 §S Track S5)

Frozen Host / Python / OS surface for the runner under `runner/`.
A stranger should read this table and know what is supported.
CI must exercise the same matrix.

Authority: [`docs/runner/CONTRACT.md`](../runner/CONTRACT.md) §8,
[`docs/runner/RUNNER-INVARIANTS.md`](../runner/RUNNER-INVARIANTS.md) A18,
[`longgraph.cli.HOST_CHOICES`](../../runner/longgraph/cli.py).
Workflow: [`.github/workflows/validate.yml`](../../.github/workflows/validate.yml)
(`runner` job). Residuals: [`KNOWN_ISSUES.md`](../../KNOWN_ISSUES.md).

**S5 exit = this table + the CI runner matrix.** Do not advertise a
stronger Host, Python, or OS than the named pytest can fail.

Git tags and GitHub Releases are owner-only. This document does not
claim a published release.

The **Frozen surface** table is the source the meta-tests parse. Keep
each axis on **one** row. Values that CI binds stay in backticks.

## Frozen surface

| Axis | Values |
| --- | --- |
| CLI hosts | `prompt-only` `grok-bot` `mock` |
| Python | `3.11` `3.12` |
| OS | `ubuntu-latest` `windows-latest` |

## CLI hosts

| CLI `--host` | Class | Status |
| --- | --- | --- |
| `prompt-only` | `PromptOnlyHost` | **Supported.** Safe default. Emit-only (dual `/loop` paste blocks). No write-set, no close. |
| `grok-bot` | `GrokBotDualTimerHost` | **Supported.** DualTimer product path. Timer-only: owns two independent timers, does **not** apply write-sets, no peer wake. |
| `mock` | `MockHost` | **Supported for tests only.** Coupled executor→supervisor→scout loop. Not the product path. |

Omitting `--host` is emit-only (`prompt-only`). The CLI must not silently
treat MockHost as the product path. This list must stay identical to
`HOST_CHOICES`.

## Python

Supported (CI-bound): **3.11** and **3.12**.

`runner/pyproject.toml` lower bound is `requires-python = ">=3.11"`.
That bound is an install floor, not a claim that every newer CPython
is supported. **3.13+ is not a support claim** until a matrix cell is
green. Do not invent 3.13 in this table.

## OS

CI and product claims: **`ubuntu-latest` (Linux)** and
**`windows-latest` (Windows native)**.

Windows is native CPython under PowerShell or cmd — not WSL-only.
Install from `runner/` with `pip install -e ".[dev]"` and invoke
`longgraph run …`. Workspace / findings / audit-surface containment
stays **fail-closed** across drives and NTFS case-folding. Junctions
and symlinks (when the OS can create them) are aliases; tests skip a
link type only when the platform cannot create it.

macOS is **not** in the runner matrix and is **not** supported.

`true` / `false` Verify placeholders are portable (no `/bin/true`).
Other Verify/smoke strings run via the process shell (`cmd.exe` on
Windows). This freeze does **not** claim DualTimer live soak on any OS.

## Explicit non-support / limits

- **LangGraph** is not a public contract. Product `runner/longgraph/`
  must not import it (P10).
- **Wake edges** are forbidden. DualTimer does not serial-tick peers.
- **`longgraph-dev-continue`** is DEV-only. It is not the product
  runtime and must not appear in product Host paths.
- **DualTimer does not apply write-sets.** Close still requires an
  applied write-set plus gate re-pass. Timer-only ticks never close.
- **Git tags / GitHub Releases** are owner-only. Agents must not
  create them. The SemVer string in `pyproject.toml` may exist with
  no matching tag.
- **ApiHost**, prompt compiler, and an engine under `skills/` are
  out of scope for this freeze.
- **Live DualTimer multi-day soak** is owner evidence (M-R2-3), not
  implied by this document.

## Alignment (CI-bound)

| Check | Pytest |
| --- | --- |
| Doc exists and freezes the three axes | `test_support_surface_doc_exists` |
| Workflow runner matrix covers supported Python and OS | `test_ci_runner_matrix_covers_supported_python` |
| SUPPORT.md host list matches CLI `HOST_CHOICES` | `test_support_hosts_match_cli` |
