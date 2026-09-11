# Runner authority (Phase 0 / 1a / 1b / 1c)

These files are the **runner's contract**. The skill library under `skills/`
remains **policy and authoring** — it is never the engine, and the runner
never loads it at runtime.

| Document | Owns |
|---|---|
| [`CONTRACT.md`](CONTRACT.md) | Ledger / directives / ops / status field names, Default-FAIL, fixture authorship |
| [`RUNNER-INVARIANTS.md`](RUNNER-INVARIANTS.md) | A* rules and the Phase ≤1c CI list |
| [`EXPANSION-PLAN.md`](EXPANSION-PLAN.md) | Phase 0 / 1a / 1b / 1c extract of EXPANSION-PLAN-v3.3 (golden table, Host/MockHost, PromptOnlyHost, GrokBotDualTimerHost, retry) |
| [`SECURITY.md`](../../SECURITY.md) | Workspace escape denied, no secrets in fixtures, runner must not `git push` |

**Conflict rule.** If a skill prompt, example, or host note disagrees with
CONTRACT or RUNNER-INVARIANTS, the runner docs win for anything under
`runner/`. Skill examples stay human-readable illustrations; they are **not**
the golden source of truth. Normalized fixtures live at
`runner/tests/fixtures/<name>/`.

**What this extract is.** EXPANSION-PLAN-v3.3 is the SHIPPABLE brief for the
longgraph runner. The copies here cover Phase 0 (contracts + fixtures +
parser), Phase 1a (MockHost MVP), Phase 1b (PromptOnlyHost dual `/loop`
emit), Phase 1c (GrokBotDualTimerHost), and DISTRIBUTION H0–H2 (write-path
containment, fail-closed gates, DualTimer terminal/scout, CLI Host,
contract fidelity for long runs). Later phases (1d+) are out of scope
and must not be invented in this tree.

**Brand.** Product / repo / slash / run-root remain longgraph /
longgraph-skill / `/longgraph` / `.longgraph/`. The engine is a **new** tree
under `runner/`. Do not put engine code in `skills/`.
