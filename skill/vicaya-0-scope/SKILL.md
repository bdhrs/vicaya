---
name: vicaya-0-scope
description: Route Vicaya Phase 0 section in ../vicaya/SKILL.md and set binding staged context breaks when needed.
---

# Vicaya Stage 0 Scope Router

This staged skill is a section router into `../vicaya/SKILL.md`.

Recommended model tier: advanced.

`../vicaya/SKILL.md is the only behavioral source of truth`.

Do not summarize, paraphrase, replace, weaken, or rewrite any routed canonical instruction.

Stop if any listed section cannot be found as a real non-fenced Markdown heading in `../vicaya/SKILL.md`.

## Route List

Read these exact sections from `../vicaya/SKILL.md` before acting:

- `## Critical execution rules`
- `## Hard rules (read first — these are not preferences)`
- `## Inputs`
- `### Question sanitization`
- `## Setup — paths and tools`
- `## Calling the helpers`
- `## Research scratchpad`
- `## Research phases (Phase 0 through 7)`
- `### Phase 0 — Request understanding and scope check`

For each listed heading, read from that heading through the line before the next non-fenced Markdown heading in ../vicaya/SKILL.md that is either (a) of the same or higher level, or (b) itself separately listed in this skill's route list — whichever comes first.

Follow the routed canonical sections exactly.

## Stage Boundary

Owned scope: Phase 0 only.

If any routed canonical instruction requires work outside this staged skill's owned scope, do not perform that work here. Stop and hand off with the same scratch slug to the staged skill that owns the required phase.

Do not run Phase 1 or any later phase.

Entry: governed by the routed canonical sections.

Exit: governed by the routed canonical sections.

Next-stage handoff: use the same scratch slug with `vicaya-1-gather`; recommended tier fast.

## Stage Context Plan

After Phase 0 scoping and before any Phase 1 work, decide whether the staged run is likely to be extensive enough to require fresh context between later passes. This is stage-local context management only; it does not change any canonical research phase, evidence requirement, synthesis requirement, scratch format, helper behavior, phase gate, or owned phase scope.

Treat the run as extensive only when the scoped question is likely to require sustained work across several evidence channels, such as a broad thematic question, multiple Pali terms or doctrinal frames, canon plus Abhidhamma/commentary comparison, several applicable investigation angles, library/web/YouTube work, or a full-note target.

If the run is not extensive, do not add split friction. Hand off normally with the same scratch slug.

If the run is extensive, use the routed canonical scratch logging mechanism to record concise Phase 0 `stage-1-context-plan`, `stage-2-context-plan`, and `stage-3-context-plan` notes before the Phase 0 exit gate, then include the same hard-stop plan in the final handoff. These logged context plans are binding instructions for later staged skills and override any model-tier recommendation unless the user explicitly opts out before Stage 1 begins. Tell the user to run later staged skills in fresh sessions with the same scratch slug and refresh context between planned passes.

For extensive Stage 1 gathering, record this split shape unless the scoped question clearly calls for a simpler one:

- Phase 1 vault/EBC context, angle triage, and perspective map, then stop after the Phase 1 gate.
- Phase 2 root-canon mūla/sutta research, then hard stop at a scratch-logged Phase 2 in-progress checkpoint if commentary/ṭīkā research is still required. Do not write the Phase 2 gate until all canonical Phase 2 obligations are complete.
- Phase 2 canonical exegesis/commentary research when applicable, including aṭṭhakathā, ṭīkā, Abhidhamma, Visuddhimagga, and DPD gloss checks required by the scoped question, then stop after the Phase 2 gate.
- Phase 2.5 SuttaCentral/offline parallel research when applicable, then stop after the Phase 2.5 gate.
- Phase 3 library research, then stop after the Phase 3 gate.
- Phase 3b Sanskrit source research when applicable, then stop after the Phase 3b gate.
- Phase 4a web research, then stop after the Phase 4 gate.
- Phase 4b YouTube research when applicable, then stop after the Phase 4b gate.
- Phase 4c WisdomLib research, then stop after the Phase 4c gate.

For extensive Stage 2 synthesis/review, record this split shape unless the scoped question clearly calls for a simpler one:

- Phase 5 synthesis, then stop after the Phase 5 gate.
- Phase 6 second-pass review, then stop after the Phase 6 gate and hand off to `vicaya-3-complete`.

For very large dossiers, record that `vicaya-2-synthesize-review` must first write a compact Phase 5 synthesis plan to scratch and stop before drafting, then resume in fresh context to complete Phase 5.

For extensive Stage 3 completion, record this mandatory three-run split shape unless the scoped question clearly calls for a simpler one:

- Run 1: create a Phase 7 writer brief and scratch-local draft file plan. Use a draft path under `data/scratch/`, normally `data/scratch/<scratch-slug>.phase7-draft.md`. Record the draft path, vault-note title, filename slug, outline, section order, source allocation, target frontmatter refs, and section status in scratch. Write only the `## Question` and `## Findings` sections into the draft file, then hard stop.
- Run 2: resume the same draft file. Write the remaining evidence and support sections into the draft file, confirm frontmatter `canon_refs` with the routed canonical citation requirements, run a completion audit against the routed canonical Phase 7/frontmatter/bibliography/style requirements, and hard stop before any vault write.
- Run 3: write only the complete audited draft to the vault, validate, generate the PDF, run the Phase 7 gate, sync the note and run report, complete the final user report, and run the self-improvement loop.

Record that `vicaya-3-complete` must never write a partial or draft note to the vault. Partial section drafts are allowed only in the scratch-local draft file, never in the vault.

At the end of Stage 0 for an extensive run, explicitly tell the user: "I will break this research into the planned fresh-context passes. If you do not want those breaks, say so before starting `vicaya-1-gather`; otherwise run `vicaya-1-gather` with this same scratch slug." Do not ask the executing stages to decide again.

If the user explicitly opts out before Stage 1 begins, use the routed canonical scratch logging mechanism to record a concise Phase 0 `context-plan-opt-out` note. Later staged skills must treat that opt-out note as disabling the planned hard stops while leaving all canonical phase boundaries intact.

If a split is recorded and no opt-out is recorded, do not perform any Phase 1 or later work here. The recorded plan is binding for later staged skills; the scratch file remains the only run state.

Do not read or create staged shared-reference files under skill/vicaya/shared/.
