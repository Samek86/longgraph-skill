# Scout Node Lifecycle

The **scout node** is an optional off-critical-path research role for loop-graph runs. This document defines its lifecycle, dispatch mechanics, findings protocol, and integration with focused presets.

## When Scout is Used

Scout enters the hot path automatically for **focused presets** where bounded research off the critical path helps:

- **loop-research**: Always — research is the primary goal
- **loop-deliver**: Optional — when requirements need bounded investigation (e.g. API compatibility checks)
- **loop-converge**: Optional — when code needs investigation (e.g. runtime observability probes)

Custom packs may include Scout when the decision criteria require it.

## Scout vs. Plain Subagent

Use a scout node (durable findings edge) when:

- Research is **off the critical path** but load-bearing
- The answer must **survive a dropped session**
- The supervisor must **audit the research independently**

Use a plain executor subagent (synchronous, throwaway) for:

- Quick lookups that fit in one context window
- Answers that don't need supervisor review
- Decisions that don't block other work

## Lifecycle Stages

### 1. Brief Registration

**Who**: Supervisor or owner during compile time  
**What**: A research brief is registered with:

```markdown
| Field | Purpose |
|-------|---------|
| `id` | Brief identifier (becomes findings filename anchor) |
| `question` | The specific thing to answer |
| `context` | Pointers to files/docs/URLs to start from |
| `constraints` | Non-negotiables the answer must satisfy |
| `cap` | Token budget or time bound (hard ceiling) |
```

**Where**: Recorded in `ops.md` Context index or as a numbered directive

**Example**:
```markdown
Brief-001 (s3-client): Which S3-compatible Python client library fits our async/size/maintenance constraints?
- Context: requirements in ops.md (async, <5MB dep, streaming uploads, no C extension)
- Constraints: MinIO + AWS S3; async interface; actively maintained (commit in last 90d)
- Cap: 8000 tokens
```

### 2. Scout Dispatch

**Who**: Supervisor (via directive) or owner (manual)  
**When**: When executor hits `blocked-on: findings#<brief-id>` or proactively before a decision point  
**What**: Scout node activates with the brief

**Mechanics**:
- Scout runs in a **fresh context** (no shared state with executor/supervisor)
- Scout reads ledger + ops (read-only) for context
- Scout writes **only** to its findings edge: `findings/<brief-id>.md`
- Scout runs **once** per brief (not a loop)

**Dispatch methods**:

A. **Proactive** (preferred for known decision points):
```markdown
D-003 · 2025-01-15 — dispatch scout: brief `s3-client`
  Question: which S3-compatible client library for Python fits our constraints?
  Context: requirements in ops.md
  Constraints: (as above)
  Cap: 8000 tokens
```

B. **Reactive** (when executor blocks):
Executor registers `blocked-on: findings#<brief-id>` in ledger; supervisor sees it and dispatches

### 3. Scout Execution

**Input read-set**:
- `ledger.md` (read-only, for context)
- `ops.md` (read-only, for environment facts)
- External docs, changelogs, APIs, READMEs (via file read / web fetch)
- The research brief itself

**Output write-set**:
- **Only** `findings/<brief-id>.md` (scout is single writer of this file)
- Never writes ledger, directives, ops, or implementation files

**Work**:
1. Orient: read ledger for current plan context
2. Research: gather sources, compare options, verify constraints
3. Write findings file (see format below)
4. Stop

**Stop conditions** (priority order):
1. **Brief answered** — all sub-questions resolved → `Status: complete`
2. **Cap hit** — token/time ceiling reached → `Status: partial (cap hit)`
3. **Blocked** — unanswerable without info scout can't access → `Status: blocked (clarification needed)`
4. **Already answered** — answer already in ledger/repo → one-line pointer

### 4. Findings Format

```markdown
# Findings: {{BRIEF_ID}}

**Brief**: {{one-line restatement of the question}}
**Status**: complete | partial (cap hit) | blocked (clarification needed)
**Date**: {{ISO date}}

## Answer (≤3 sentences)

{{The answer, or "no clear winner — see comparison."}}

## Comparison

| Option | Fits constraints? | Key tradeoff | Evidence |
| --- | --- | --- | --- |
| ... | yes/no/partial | one line | link or version checked |

## Recommendation

{{Pick + one-line rationale, or "no recommendation — depends on {{X}}"}}

## Notes (audit trail — not for executor to read in full)

{{Links checked, versions verified, compatibility tested.}}
```

**Consumption target**: Answer + Comparison must be readable in **under 30 seconds**. Notes are for supervisor audit only.

### 5. Executor Consumption

**When**: Executor reaches the ledger item with `blocked-on: findings#<brief-id>`  
**What**: Executor reads findings file (read-on-reference, not read-every-round)  
**Decision**:
- Accept recommendation → record decision + rationale in ledger
- Reject recommendation → record why + alternative choice
- Findings are **advisory only** — executor decides

**Example**:
```markdown
### Round 4 — 2025-01-15
- **Item**: implement dual-path upload (resumed — scout answered)
- **Decision**: minioclient 7.2 — fits all constraints per findings#s3-client
- **Change**: added minioclient to requirements, implemented async upload path
- **Retire**: findings#s3-client consumed → moved to archive/findings-s3-client.md
```

### 6. Findings Retirement

**When**: Decision is recorded in ledger  
**What**: 
1. Record decision + rationale in ledger's round log
2. Move consumed finding to `archive/findings-<brief-id>.md` (or delete it)
3. Remove `blocked-on` pointer from ledger

**Why**: Keeps findings edge O(active briefs), not O(total briefs ever dispatched)

**Lifecycle complete** ✓

### 7. Supervisor Audit (Optional)

**When**: During routine supervisor review or at milestone gates  
**What**: Supervisor independently verifies:
- Scout answered the brief (didn't drift to a different question)
- Sources are cited and versions recorded
- Comparison is fair (same test conditions)
- Executor's decision matches the recorded rationale

**Outcome**: If audit fails, supervisor appends correction to directives

## Integration with Presets

### loop-research Preset

Scout is **always active** and on the hot path:

- Compiler auto-emits `findings/` directory and Scout brief template
- Supervisor instructions include Scout dispatch triggers
- Executor template includes findings consumption protocol
- Default: proactive dispatch (before decision points)

### loop-deliver Preset

Scout is **conditionally active**:

- Compiler emits Scout infrastructure when pack detects investigation needs (e.g. API compatibility)
- Typical triggers: external API checks, library compatibility, performance baseline establishment
- Default: reactive dispatch (executor blocks, supervisor dispatches)

### loop-converge Preset

Scout is **conditionally active**:

- Compiler emits Scout infrastructure when detectors need verification
- Typical triggers: runtime observability probes, reflection/plugin usage checks
- Default: reactive dispatch

### Custom Packs

Include Scout when:
- Decision requires evidence gathering that can run in parallel with main work
- Research is load-bearing but off the critical path
- Answer must be auditable by supervisor

Omit Scout when:
- All decisions are pre-answered in the pack
- Research would block the critical path (use executor subagent instead)
- No supervisor exists to audit findings

## Parallel Scouts

When multiple briefs are active simultaneously:

**Directory structure**:
```
findings/
├── s3-client.md          # Brief-001
├── async-framework.md    # Brief-002
└── db-migration.md       # Brief-003
```

**Each scout**:
- Runs in its own fresh context
- Writes only to its own `findings/<brief-id>.md` file
- Single-writer invariant preserved (one scout per file)
- No coordination between scouts

**Executor consumption**: Reads each findings file on-reference via ledger pointer

## Anti-Patterns

❌ **Scout writes ledger** — Violates single-writer invariant  
❌ **Scout implements** — Violates advisory-only authority  
❌ **Executor reads findings every round** — Wastes tokens; use read-on-reference  
❌ **Findings accumulate forever** — Retire consumed findings to archive  
❌ **Scout runs in executor's context** — Breaks clean-context separation  
❌ **Brief has no cap** — Scout can run unbounded

## File Checklist

When Scout is active in a run, these artifacts exist:

- [ ] `findings/` directory (empty at compile time)
- [ ] Scout brief(s) registered in `ops.md` or directives
- [ ] Executor template includes findings consumption protocol
- [ ] Supervisor template includes Scout dispatch triggers (if supervisor exists)
- [ ] Scout node prompt is available (from templates/scout.md)

## References

- Scout node prompt: [`../templates/scout.md`](../templates/scout.md)
- Findings edge template: [`../templates/findings.md`](../templates/findings.md)
- Worked example: [`../examples/scout-library-choice/`](../examples/scout-library-choice/)
- Preset contract: [`preset-contract.md`](preset-contract.md)
