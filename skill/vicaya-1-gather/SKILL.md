---
name: vicaya-1-gather
description: Route Vicaya Phases 1 - 4c sections in ../vicaya/SKILL.md.
---

# Vicaya Stage 1 Gather Router

This staged skill is a section router into `../vicaya/SKILL.md`.

Recommended model tier: fast.

`../vicaya/SKILL.md` is the only behavioral source of truth.

Do not summarize, paraphrase, replace, weaken, or rewrite any routed canonical instruction.

Stop if any listed section cannot be found as a real non-fenced Markdown heading in `../vicaya/SKILL.md`.

## Route List

Read these exact sections from `../vicaya/SKILL.md` before acting:

- `## Critical execution rules`
- `## Hard rules (read first — these are not preferences)`
- `## Setup — paths and tools`
- `## Calling the helpers`
- `## Helper return shapes (read before calling)`
- ``## Book-identifier lookups (`lookup-book`)``
- ``## DPD dictionary database (`dpd.db`)``
- `## EBC vault (Early Buddhist Connections)`
- `## Research scratchpad`
- `## Evidence tiers`
- `## Research phases (Phase 0 through 7)`
- `## Investigation angles`
- `### Textual layers`
- `### Other schools of Buddhism`
- `### Comparative religion`
- `### Modern voices`
- `### Academic disciplines`
- `### Phase 1 — Vault context`
- `### Phase 2 — Canon search`
- `#### EBC parallel-evidence pull`
- `### Phase 2.5 — SuttaCentral offline parallel search`
- `### Phase 3 — Library search`
- `### Phase 3b — Sanskrit source search`
- `### Phase 4a — Web search`
- `### Phase 4b — YouTube search`
- `### Phase 4c — WisdomLib`
- `## When something fails`

For each listed heading, read from that heading through the line before the next non-fenced Markdown heading in ../vicaya/SKILL.md that is either (a) of the same or higher level, or (b) itself separately listed in this skill's route list — whichever comes first.

Follow the routed canonical sections exactly.

## Stage Boundary

Owned scope: Phase 1 through Phase 4c only.

If any routed canonical instruction requires work outside this staged skill's owned scope, do not perform that work here. Stop and hand off with the same scratch slug to the staged skill that owns the required phase.

Do not run Phase 5 or any later phase.

Entry: governed by the routed canonical sections.

Exit: governed by the routed canonical sections.

Next-stage handoff: use the same scratch slug with `vicaya-2-synthesize-review`; recommended tier advanced.

## Context Break Guard

At entry, use the routed canonical scratch/resume instructions to determine the last completed gate, whether Phase 0 recorded a `stage-1-context-plan`, whether Phase 0 recorded a later `context-plan-opt-out`, and whether the scratch contains a Stage 1 source-block hard-stop note naming an unfinished next block. This guard is stage-local context management only; it does not change any canonical research phase, evidence requirement, scratch format, helper behavior, phase gate, or owned phase scope.

If no Stage 1 context plan exists, or if a `context-plan-opt-out` exists, proceed normally through this staged skill's owned scope.

If a Stage 1 context plan exists, it is binding for this staged run and overrides any model-tier recommendation. Every invocation under that plan runs exactly one next source block, then hard stops at the relevant safe boundary and hands off with the same scratch slug. A prior hard stop is only a handoff checkpoint; it must not be treated as satisfying the whole Stage 1 plan. Do not merge, skip, or continue into a second source block.

The next source block is the first listed block whose gate or source-block checkpoint is not complete in scratch, while respecting routed canonical skip rules and any latest Stage 1 hard-stop handoff note.

Hard-stop safety mode source blocks are:

- Phase 1 vault/EBC context, angle triage, and perspective map, plus Phase 2 root-canon mūla/sutta research; write the Phase 1 gate, then hard stop at a scratch-logged Phase 2 in-progress checkpoint if commentary/ṭīkā research is still required. Do not write the Phase 2 gate until all canonical Phase 2 obligations are complete.
- Phase 2 canonical exegesis/commentary research when applicable, including aṭṭhakathā, ṭīkā, Abhidhamma, Visuddhimagga, and DPD gloss checks required by the scoped question; stop after the Phase 2 gate.
- Phase 2.5 SuttaCentral/offline parallel research when applicable, plus Phase 3 library research and Phase 3b Sanskrit source research when applicable; stop after the Phase 3b gate when applicable, otherwise stop after the latest applicable gate.
- Phase 4a web research, Phase 4b YouTube research when applicable, and Phase 4c WisdomLib research; stop after the Phase 4c gate and hand off to `vicaya-2-synthesize-review`.

If the scoped run did not require Phase 2.5, Phase 3b, or Phase 4b, skip those phases only when the routed canonical scratch/gate instructions allow the skip.

Whether or not a Stage 1 context plan exists, before moving from one major source class to another, ensure useful findings, citations, source status, and any skip rationale are recorded through the routed canonical scratch mechanism. Do not carry handoff-critical gathering results only in model context. This checkpoint is not a new phase gate unless the routed canonical gate instructions require one.

Do not read or create staged shared-reference files under skill/vicaya/shared/.
