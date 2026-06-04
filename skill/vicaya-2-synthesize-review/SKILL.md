---
name: vicaya-2-synthesize-review
description: Route Vicaya Phases 5 and 6 sections in ../vicaya/SKILL.md.
---

# Vicaya Stage 2 Synthesis And Review Router

This staged skill is a section router into `../vicaya/SKILL.md`.

Recommended model tier: advanced.

`../vicaya/SKILL.md is the only behavioral source of truth`.

Do not summarize, paraphrase, replace, weaken, or rewrite any routed canonical instruction.

Stop if any listed section cannot be found as a real non-fenced Markdown heading in `../vicaya/SKILL.md`.

## Route List

Read these exact sections from `../vicaya/SKILL.md` before acting:

- `## Critical execution rules`
- `## Hard rules (read first — these are not preferences)`
- `## Setup — paths and tools`
- `## Calling the helpers`
- `## Research scratchpad`
- `## Evidence tiers`
- `## Bibliography`
- `## Research phases (Phase 0 through 7)`
- `### Phase 5 — Synthesis`
- `### Phase 6 — Second-pass review (cross-check)`
- `## When something fails`
- `## Style notes`
- `### Pāḷi/English presentation (vault note only)`
- `### Footnote definitions (vault note only)`

For each listed heading, read from that heading through the line before the next non-fenced Markdown heading in ../vicaya/SKILL.md that is either (a) of the same or higher level, or (b) itself separately listed in this skill's route list — whichever comes first.

Follow the routed canonical sections exactly.

## Stage Boundary

Owned scope: Phase 5 and Phase 6 only.

If any routed canonical instruction requires work outside this staged skill's owned scope, do not perform that work here. Stop and hand off with the same scratch slug to the staged skill that owns the required phase.

Do not run Phase 7.

Entry: governed by the routed canonical sections.

Exit: governed by the routed canonical sections.

Next-stage handoff: use the same scratch slug with `vicaya-3-complete`; recommended tier fast if the routed canonical scratch/gate state shows Phase 5/6 synthesis is complete.

## Context Break Guard

At entry, use the routed canonical scratch/resume and scratch/verify instructions to determine the last completed gate, whether Phase 0 recorded a `stage-2-context-plan`, whether Phase 0 recorded a later `context-plan-opt-out`, and whether scratch contains a Phase 5 drafting-plan checkpoint. This guard is stage-local context management only; it does not change any canonical synthesis requirement, review requirement, scratch format, helper behavior, phase gate, or owned phase scope.

If no Stage 2 context plan exists, or if a `context-plan-opt-out` exists, proceed normally through Phase 5 and Phase 6.

If a Stage 2 context plan exists, it is binding for this staged run and overrides any model-tier recommendation. Run only the next planned synthesis/review pass, then hard stop after the planned scratch checkpoint or canonical gate and hand off with the same scratch slug. Do not merge, skip, or continue into the next planned pass.

Default extensive-run passes are:

- Phase 5 entry verification, scratch review, source completeness check, angle coverage check, Devil's Advocate answers, bibliography/source allocation review, and a concise Phase 5 drafting plan recorded in scratch using the routed canonical scratch logging mechanism; hard stop before full drafting and tell the user to refresh context and rerun `vicaya-2-synthesize-review` with the same scratch slug.
- Resume from the Phase 5 drafting plan, complete Phase 5 drafting/integration and the Phase 5 gate, then run Phase 6 second-pass review and the Phase 6 gate; hard stop and hand off to `vicaya-3-complete` with the same scratch slug.

Do not read or create staged shared-reference files under skill/vicaya/shared/.
