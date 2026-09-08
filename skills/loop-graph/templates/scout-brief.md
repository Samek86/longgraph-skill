<!--
loop-graph template: scout-brief.md — RESEARCH BRIEF TEMPLATE for scout dispatch.
This is an authoring-only template used during compilation. The compiler fills it with
preset-specific questions, then either:
  A. Records it in ops.md Context index (for proactive dispatch), or
  B. Includes it in supervisor.md dispatch instructions (for reactive dispatch)

This file is never saved to the run directory as-is. It's a template fragment.
-->

# Research Brief: {{BRIEF_ID}}

**ID**: `{{BRIEF_ID}}`  
**Question**: {{RESEARCH_QUESTION}}  
**Context**: {{CONTEXT_POINTERS}}  
**Constraints**: {{NON_NEGOTIABLES}}  
**Cap**: {{TOKEN_OR_TIME_BUDGET}}

## Background

{{WHY_THIS_QUESTION_MATTERS}}

## Expected Deliverable

Answer format: See [`templates/findings.md`](findings.md) for the standard findings structure.

The scout writes to `findings/{{BRIEF_ID}}.md` and stops.

## Dispatch Trigger

{{PROACTIVE_OR_REACTIVE}}

- **Proactive**: Dispatch before executor reaches decision point (supervisor schedules it early)
- **Reactive**: Dispatch when executor hits `blocked-on: findings#{{BRIEF_ID}}` in ledger

## Success Criteria

The finding is consumable by the executor in **under 30 seconds** of reading:
- Clear answer or "no clear winner — depends on X"
- Fair comparison table with evidence
- Recommendation with one-line rationale

## Failure Modes to Avoid

- Drifting to a different question
- Implementing instead of researching
- Comparing under different test conditions
- Omitting sources or version pins
- Exceeding the cap without writing partial findings
