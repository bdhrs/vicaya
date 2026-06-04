---
name: vicaya-3-complete
description: Route Vicaya Phase 7, final-report, style, failure, and self-improvement sections in ../vicaya/SKILL.md and honor context breaks when needed.
---

# Vicaya Stage 3 Completion Router

This staged skill is a section router into `../vicaya/SKILL.md`.

Recommended model tier: fast if the routed canonical scratch/gate state shows Phase 5/6 synthesis is complete.

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
- `### Phase 7 — Write the note`
- `### Frontmatter rules (agents get these wrong — read carefully)`
- `### Correct frontmatter example (reference this when writing)`
- `### PDF generation (run after every successful vault write)`
- `### GitHub push (user-triggered)`
- `## Final report to the user`
- `## When something fails`
- `## When Obsidian isn't running`
- `## Style notes`
- `### Pāḷi/English presentation (vault note only)`
- `### Footnote definitions (vault note only)`
- `## Self-improvement loop (mandatory)`

For each listed heading, read from that heading through the line before the next non-fenced Markdown heading in ../vicaya/SKILL.md that is either (a) of the same or higher level, or (b) itself separately listed in this skill's route list — whichever comes first.

Follow the routed canonical sections exactly.

## Stage Boundary

Owned scope: Phase 7, final report, failure handling relevant to completion, style rules, and self-improvement loop only.

If any routed canonical instruction requires work outside this staged skill's owned scope, do not perform that work here. Stop and hand off with the same scratch slug to the staged skill that owns the required phase.

Entry: governed by the routed canonical sections.

If the routed canonical scratch/gate instructions show Phase 6 is incomplete, stop and hand off to `vicaya-2-synthesize-review` with the same scratch slug.

Do not infer Phase 5/6 completeness by any local checklist.

Exit and finalization: governed by the routed canonical sections.

No next-stage handoff after completion.

## Context Break Guard

At entry, use the routed canonical scratch/resume instructions to determine the last completed gate, whether Phase 0 recorded a `stage-3-context-plan`, and whether Phase 0 recorded a later `context-plan-opt-out`. This guard is stage-local context management only; it does not change any canonical Phase 7, final-report, validation, PDF, scratch gate, run-report sync, self-improvement, scratch format, helper behavior, or owned phase scope requirement.

If no Stage 3 context plan exists, or if a `context-plan-opt-out` exists and the completion work is manageable, proceed normally through this staged skill's owned scope.

If a Stage 3 context plan exists, it is binding for this staged run and overrides any model-tier recommendation. Run only the next planned completion pass, then hard stop at the relevant safe boundary and hand off with the same scratch slug. Do not merge, skip, or continue into the next planned pass because context seems comfortable.

Default extensive-run passes are:

- Create or resume a scratch-local Phase 7 draft file under `data/scratch/`, normally `data/scratch/<scratch-slug>.phase7-draft.md`. Record the draft path, final-note outline, section order, source allocation, and current section status in scratch using the routed canonical scratch logging mechanism. This draft file is a Phase 7 scratch artifact, not the vault note.
- Write the final note into the draft file section by section. Save the draft file after each section and log concise section status in scratch. Continue across sections while context remains healthy; if context pressure rises, hard stop after the current saved section and tell the user to refresh context and rerun `vicaya-3-complete` with the same scratch slug and draft path.
- When the draft file contains the complete note, audit it against the routed canonical Phase 7, frontmatter, bibliography, and style requirements. Hard stop before any vault write if context pressure requires it.
- Write only the complete audited draft to the vault, validate, generate the PDF, run the Phase 7 gate, and sync the run report.
- If context pressure still requires it after the run report is synced, hard stop and tell the user to refresh context and rerun `vicaya-3-complete` with the same scratch slug for the final user report and self-improvement loop.

Never write a partial or draft note to the vault. Partial section drafts are allowed only in the scratch-local draft file. The vault must receive only the complete audited note.

Do not read or create staged shared-reference files under skill/vicaya/shared/.
