# D2 Go/No-Go (DISTRIBUTION-READINESS-v1 §8)

Filled checklist for the **R — Release engineering** pack. This is the
owner's cut sheet for a D2 candidate tag. Agents prepare the evidence;
they do **not** tag or publish.

Authority: [`docs/runner/CONTRACT.md`](../runner/CONTRACT.md),
[`docs/runner/RUNNER-INVARIANTS.md`](../runner/RUNNER-INVARIANTS.md),
[`docs/runner/EXPANSION-PLAN.md`](../runner/EXPANSION-PLAN.md),
DISTRIBUTION-READINESS-v1 (S exit → D2; R release engineering).

**Coding D2 evidence pack: READY.**
**Publish: NOT done** until the owner cuts a SemVer tag and records a
D2 publish ack. New git tags and GitHub Releases are **owner-only**.
Agents must not create them.

Preferred SemVer string: **`0.4.0-rc.1`** (in
[`runner/pyproject.toml`](../../runner/pyproject.toml)). S exit allows
`0.4.0` or `1.0.0-rc.1`; this tree uses `0.4.0-rc.1` so we do not claim
stable without an owner tag. The `0.4.0-rc.1` tag does **not** exist.

---

## Tip under review

| Field | Value |
| --- | --- |
| Main SHA | `f2f493b` (`f2f493b52a66daac172fdde9ace485297a32b297`) |
| Engine / Critical=0 tip | `5de40a9` (`5de40a977844bcb59b661270c3c5dab08b0e3a6c`) — PR #22, C-TIP-3 closed |
| Post-soak tip | `f2f493b` is the #23 merge of the mock N=50 evidence pack. Runner engine files are unchanged vs `5de40a9` (docs + meta-test only). |
| Existing owner-cut tag | Annotated `0.3.0-beta` at `eeb7591` (do not retarget) |

---

## §8 checklist

Status **MET** is coding-pack evidence on this tip. Status **OWNER-ONLY**
is unchecked: the owner must do that step. Do not treat MET rows as a
published release.

| Gate | Status | Evidence |
| --- | --- | --- |
| Main tip SHA recorded | **MET** | `f2f493b` / `f2f493b52a66daac172fdde9ace485297a32b297` |
| Adversarial Critical=0 | **MET** | [`ADVERSARIAL-TIP.md`](ADVERSARIAL-TIP.md) — Critical remaining **0**; C-TIP-3 fixed on #22 @ `5de40a9` |
| Mock soak N≥50 | **MET** | [`soak/tip-5de40a9-n50-mock/`](soak/tip-5de40a9-n50-mock/) — `host=mock`, N=50, pass. Protocol: [`SOAK.md`](SOAK.md). Valid for post-soak tip `f2f493b` (docs-only soak commit). |
| Public claims P1–P10 CI-bound | **MET** | [`PUBLIC_CLAIMS.md`](PUBLIC_CLAIMS.md) |
| Support surface S5 | **MET** | [`SUPPORT.md`](SUPPORT.md) — CLI hosts `prompt-only` / `grok-bot` / `mock`; Python 3.11 / 3.12; `ubuntu-latest` |
| S3 negative battery | **MET** | [`S3_NEGATIVE_BATTERY.md`](S3_NEGATIVE_BATTERY.md), [`NEGATIVE-BATTERY.md`](NEGATIVE-BATTERY.md) |
| SECURITY red lines | **MET** | [`SECURITY.md`](../../SECURITY.md) — workspace escape denied, no secrets in fixtures, runner must not `git push` |
| CHANGELOG + residuals | **MET** | [`CHANGELOG.md`](../../CHANGELOG.md), [`KNOWN_ISSUES.md`](../../KNOWN_ISSUES.md) |
| Version string `0.4.0-rc.1` | **MET** | [`runner/pyproject.toml`](../../runner/pyproject.toml) (candidate string only) |
| CI Validate + Runner py3.11/3.12 | **MET** | PR #23 on this tip: Validate + Runner SUCCESS |
| Live DualTimer soak (M-R2-3) | **OWNER-ONLY** | Unchecked. No in-repo DualTimer / ≥24h wall-clock logs. Do not fabricate. |
| Owner "D2 publish" ack | **OWNER-ONLY** | Unchecked. Coding pack READY is not publish. |
| New SemVer tag / GitHub Release beyond `0.3.0-beta` | **OWNER-ONLY** | Unchecked. Tag `0.4.0-rc.1` does **not** exist. Agents must not create it. |

---

## Owner-only residuals (unchecked)

These rows stay unchecked until the owner acts. Agents must not tick
them, invent DualTimer soak logs, or create tags / Releases.

- [ ] Live DualTimer multi-day / ≥24h wall-clock soak (M-R2-3 / M-TIP-3 / OB-008). Mock N=50 is **not** this row.
- [ ] Owner "D2 publish" ack (human). Coding evidence READY ≠ published.
- [ ] New SemVer tag and GitHub Release beyond existing owner-cut `0.3.0-beta`. Preferred next tag: `0.4.0-rc.1`. Do not retarget `0.3.0-beta`.

---

## What this pack is / is not

| Is | Is not |
| --- | --- |
| R release-engineering prep so the owner can cut a D2 candidate | A published `0.4.0-rc.1` tag or GitHub Release |
| Coding ladder H0–H2, S1–S5, tip Critical=0, tip mock soak — done | Live DualTimer product soak evidence |
| Version string `0.4.0-rc.1` in `pyproject.toml` | A claim that the rc.1 tag already exists |
| Default-FAIL + Host semantics unchanged | Phase 1d ApiHost or Phase 2 prompt compiler |

---

## Owner cut (when ready)

1. Re-read this file and the MET evidence links.
2. Decide whether M-R2-3 DualTimer soak is required before the candidate
   tag, or is an explicit residual on the Release notes.
3. Record the D2 publish ack.
4. Owner-only: annotated tag `0.4.0-rc.1` (or the chosen SemVer) and
   GitHub Release. Agents must not run `git tag` or `gh release create`.
