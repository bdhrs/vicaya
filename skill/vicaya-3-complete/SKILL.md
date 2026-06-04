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

Default extensive-run passes are mandatory three-run passes. Each invocation performs only the next pass below, then hard stops even if context seems comfortable.

- Run 1: create or resume a scratch-local Phase 7 draft file under `data/scratch/`, normally `data/scratch/<scratch-slug>.phase7-draft.md`. Record the draft path, vault-note title, filename slug, final-note outline, section order, source allocation, target frontmatter refs, and current section status in scratch using the routed canonical scratch logging mechanism. Write only the `## Question` and `## Findings` sections into the draft file, save it, log concise section status, and hard stop.
- Run 2: resume the same draft file. Write the remaining evidence and support sections into the draft file: Canon Evidence, Commentary Evidence, Scholarly Sources, Web Evidence, Teacher Talks and Accessible Sources, Related Notes, Sources Investigated Not Used, Angles Not Pursued, Critical Gaps, Bibliography, footer, and footnote definitions. Confirm frontmatter `canon_refs` with the routed canonical citation requirements. Audit the complete draft against the routed canonical Phase 7, frontmatter, bibliography, and style requirements, save it, log the audit status, and hard stop before any vault write.
- Run 3: write only the complete audited draft to the vault, validate, generate the PDF, run the Phase 7 gate, sync the note and run report, complete the final user report, and run the self-improvement loop.

Never write a partial or draft note to the vault. Partial section drafts are allowed only in the scratch-local draft file. The vault must receive only the complete audited note.

Do not read or create staged shared-reference files under skill/vicaya/shared/.
