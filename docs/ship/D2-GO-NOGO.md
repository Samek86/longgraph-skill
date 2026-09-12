# D2 Go/No-Go (DISTRIBUTION-READINESS-v1 §8)

Filled checklist for the **R — Release engineering** pack. This is the
owner's cut sheet for a D2 candidate. Agents prepare the evidence;
they do **not** tag or publish.

Authority: [`docs/runner/CONTRACT.md`](../runner/CONTRACT.md),
[`docs/runner/RUNNER-INVARIANTS.md`](../runner/RUNNER-INVARIANTS.md),
[`docs/runner/EXPANSION-PLAN.md`](../runner/EXPANSION-PLAN.md),
DISTRIBUTION-READINESS-v1 (S exit → D2; R release engineering).

**Coding D2 evidence pack: READY.**
**Publish: NOT done** until the owner records a D2 *stable* / non-rc
publish ack. Lightweight tag `0.4.0-rc.1` and GitHub prerelease
`0.4.0-rc.1` already exist at `a4cce0f`. rc.1 prerelease existence is
**not** a stable publish ack. New git tags and GitHub Releases remain
**owner-only**. Agents must not create them.

Preferred SemVer string: **`0.4.0-rc.1`** (in
[`runner/pyproject.toml`](../../runner/pyproject.toml)). S exit allows
`0.4.0` or `1.0.0-rc.1`; this tree uses `0.4.0-rc.1` so we do not claim
stable without an owner ack. Tag `0.4.0-rc.1` **exists** (object
points at `a4cce0f`). GitHub Release `0.4.0-rc.1` is a prerelease.

History: #24 @ `3824ef4` (release-prep) then #25 reconcile, then the
tag object at tip `a4cce0f`.

---

## Tip under review

| Field | Value |
| --- | --- |
| Main SHA | `a4cce0f` (`a4cce0f54fc887e91158dcf630d328f2af709061`) — PR #25 docs reconcile merged |
| Engine / Critical=0 tip | `5de40a9` (`5de40a977844bcb59b661270c3c5dab08b0e3a6c`) — PR #22, C-TIP-3 closed |
| Post-soak tip | Mock N=50 pack is [`soak/tip-5de40a9-n50-mock/`](soak/tip-5de40a9-n50-mock/). #23 (`f2f493b`) landed the pack; #24 (`3824ef4`) is release-prep docs/version/meta; #25 (`a4cce0f`) is the docs reconcile. Tag object is at tip `a4cce0f`. Runner engine files are unchanged vs `5de40a9`. |
| Existing owner-cut tags | Lightweight `0.4.0-rc.1` at `a4cce0f` (GitHub prerelease). Prior `0.3.0-beta` at `eeb7591` (do not retarget). |

---

## §8 checklist

Status **MET** is coding-pack evidence on this tip. Status **OWNER-ONLY**
is unchecked: the owner must do that step. Do not treat MET rows as a
published stable release.

| Gate | Status | Evidence |
| --- | --- | --- |
| Main tip SHA recorded | **MET** | `a4cce0f` / `a4cce0f54fc887e91158dcf630d328f2af709061` |
| Adversarial Critical=0 | **MET** | [`ADVERSARIAL-TIP.md`](ADVERSARIAL-TIP.md) — Critical remaining **0**; C-TIP-3 fixed on #22 @ `5de40a9` |
| Mock soak N≥50 | **MET** | [`soak/tip-5de40a9-n50-mock/`](soak/tip-5de40a9-n50-mock/) — `host=mock`, N=50, pass. Protocol: [`SOAK.md`](SOAK.md). Valid for #25 tip `a4cce0f` (docs + version/meta only after engine tip `5de40a9`; #24 @ `3824ef4` then #25 reconcile). |
| Public claims P1–P10 CI-bound | **MET** | [`PUBLIC_CLAIMS.md`](PUBLIC_CLAIMS.md) |
| Support surface S5 | **MET** | [`SUPPORT.md`](SUPPORT.md) — CLI hosts `prompt-only` / `grok-bot` / `mock`; Python 3.11 / 3.12; `ubuntu-latest` |
| S3 negative battery | **MET** | [`S3_NEGATIVE_BATTERY.md`](S3_NEGATIVE_BATTERY.md), [`NEGATIVE-BATTERY.md`](NEGATIVE-BATTERY.md) |
| SECURITY red lines | **MET** | [`SECURITY.md`](../../SECURITY.md) — workspace escape denied, no secrets in fixtures, runner must not `git push` |
| CHANGELOG + residuals | **MET** | [`CHANGELOG.md`](../../CHANGELOG.md), [`KNOWN_ISSUES.md`](../../KNOWN_ISSUES.md) |
| Version string `0.4.0-rc.1` | **MET** | [`runner/pyproject.toml`](../../runner/pyproject.toml) |
| CI Validate + Runner py3.11/3.12 | **MET** | PR #25 on this tip: Validate + Runner SUCCESS |
| SemVer tag / GitHub Release `0.4.0-rc.1` | **MET** | Tag `0.4.0-rc.1` exists (object at `a4cce0f` / `a4cce0f54fc887e91158dcf630d328f2af709061`). GitHub Release `0.4.0-rc.1` is a prerelease. Agents must not create **new** tags or Releases. |
| Live DualTimer soak (M-R2-3) | **OWNER-ONLY** | Unchecked. No in-repo DualTimer / ≥24h wall-clock logs. Do not fabricate. |
| Owner "D2 publish" ack (stable / non-rc) | **OWNER-ONLY** | Unchecked. rc.1 prerelease existence is not a stable publish ack. Coding pack READY is not stable publish. |

---

## Owner-only residuals (unchecked)

These rows stay unchecked until the owner acts. Agents must not tick
them, invent DualTimer soak logs, or create **new** tags / Releases.

- [ ] Live DualTimer multi-day / ≥24h wall-clock soak (M-R2-3 / M-TIP-3 / OB-008). Mock N=50 is **not** this row.
- [ ] Owner "D2 publish" ack (stable / non-rc). Coding evidence READY ≠ published. rc.1 prerelease ≠ stable publish ack.
- [ ] Future **stable** / non-rc SemVer tag and GitHub Release. Do not retarget `0.3.0-beta` or `0.4.0-rc.1`.

---

## What this pack is / is not

| Is | Is not |
| --- | --- |
| R release-engineering prep; rc.1 tag+prerelease already cut at `a4cce0f` | A stable / non-rc publish or D2 publish ack |
| Coding ladder H0–H2, S1–S5, tip Critical=0, tip mock soak — done | Live DualTimer product soak evidence |
| Version string `0.4.0-rc.1` in `pyproject.toml`; tag+prerelease exist | A claim that DualTimer soak happened |
| Default-FAIL + Host semantics unchanged | Phase 1d ApiHost or Phase 2 prompt compiler |

---

## Owner cut (when ready)

1. Re-read this file and the MET evidence links.
2. Decide whether M-R2-3 DualTimer soak is required before a *stable*
   / non-rc tag, or remains an explicit residual on the Release notes.
3. Record the D2 *stable* publish ack.
4. Owner-only: annotated *stable* / non-rc SemVer tag and GitHub
   Release when ready. Tag `0.4.0-rc.1` and its prerelease already
   exist at `a4cce0f`. Agents must not run `git tag` or
   `gh release create`. Do not retarget `0.3.0-beta` or `0.4.0-rc.1`.
