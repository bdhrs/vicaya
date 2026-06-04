# Spec - Rebuild Vicaya staged skills as exact section routers

No GitHub issue is associated with this thread.

## Overview

The previous staged-skills thread,
`kamma/threads/20260602_vicaya-staged-skills/`, is blocked. Its spec required
"concise reference files" and "thin" staged skills that loaded summarized
phase references. That requirement was wrong for Vicaya. It caused the staged
workflow to become a paraphrased alternate workflow instead of a strict
division of the existing monolithic skill.

This thread starts over with the corrected requirement:

- `skill/vicaya/SKILL.md` remains the only behavioral source of truth.
- Staged skills must not summarize, paraphrase, simplify, weaken, or rewrite
  any workflow rule.
- Context saving is allowed only by not loading unrelated original sections.
- The staged skills are section routers: they tell the agent exactly which
  sections of `skill/vicaya/SKILL.md` to read for the current stage, then add
  only stage-local boundary, precondition, entry, exit, model-tier, and handoff
  glue.

The result should preserve two permanent execution modes:

- Full-run mode: `/vicaya <question>` via `skill/vicaya/SKILL.md`.
- Staged mode: four smaller skills that route to exact original sections for
  the current stage only.

The staged mode is:

- `vicaya-0-scope`: Phase 0 only; advanced model recommended.
- `vicaya-1-gather`: Phase 1 through Phase 4c only; fast model recommended.
- `vicaya-2-synthesize-review`: Phase 5 and Phase 6 only; advanced model
  recommended.
- `vicaya-3-complete`: Phase 7, final report, failure handling relevant to
  completion, style rules, and self-improvement loop; fast model recommended
  only when the canonical scratch/gate state shows Phase 5/6 synthesis is
  complete.

Out-of-scope handoff ownership:

- Phase 0 -> `vicaya-0-scope`
- Phase 1 through Phase 4c -> `vicaya-1-gather`
- Phase 5 and Phase 6 -> `vicaya-2-synthesize-review`
- Phase 7, final report, completion failure handling, style rules, and
  self-improvement loop -> `vicaya-3-complete`

## What it should do

### Preserve the monolithic skill

- Keep `skill/vicaya/SKILL.md` as the canonical one-goal `/vicaya` workflow.
- Do not deprecate it.
- Do not turn it into a dispatcher.
- Do not require it to load staged files.
- Do not redesign its structure as part of this thread.
- One narrow nonbehavioral edit is allowed in `skill/vicaya/SKILL.md`: the
  existing staged-mode pointer near the top may be reworded only to state that
  staged skills read exact sections from this file and that this file remains
  the only behavioral source of truth.
- If `skill/vicaya/SKILL.md` is already dirty before implementation, preserve
  those pre-existing hunks unchanged. This thread may introduce only the
  staged-mode pointer wording change; any other canonical-skill diff must be
  recorded as pre-existing or block review.
- If any staged pointer, README text, or project documentation references
  staged mode, it must state that staged mode reads exact sections from the
  canonical skill.

### Replace the failed staged implementation

Remove or overwrite the failed staged content created by the blocked thread:

- `skill/vicaya-0-scope/SKILL.md`
- `skill/vicaya-1-gather/SKILL.md`
- `skill/vicaya-2-synthesize-review/SKILL.md`
- `skill/vicaya-3-complete/SKILL.md`
- `skill/vicaya/shared/core.md`
- `skill/vicaya/shared/scope.md`
- `skill/vicaya/shared/sources.md`
- `skill/vicaya/shared/synthesis.md`
- `skill/vicaya/shared/completion.md`

The replacement must not contain summarized phase references. Delete
`skill/vicaya/shared/` entirely if it contains only the failed staged-reference
files. Do not leave an empty shared directory as a future routing target. Do
not create replacement shared routing or reference files. Staged skills must not
point at any file under `skill/vicaya/shared/`.

### Create four section-router staged skills

Each staged `SKILL.md` must be a router only. It may contain only:

- frontmatter `name` and `description`;
- short purpose statement;
- router-only section headings;
- recommended model tier;
- explicit source-of-truth statement:
  `../vicaya/SKILL.md is the only behavioral source of truth`;
- exact list of headings from `../vicaya/SKILL.md` to read before acting;
- mechanical section-boundary rule for those headings;
- instruction to follow those sections exactly;
- instruction to stop if any listed section cannot be found;
- exact owned phase scope;
- entry/exit/handoff labels that point back to the canonical routed sections;
- same-scratch-slug handoff label for the next staged skill, where one exists;
- out-of-scope handoff guard that stops rather than performing work owned by
  another staged skill;
- explicit guards against `skill/vicaya/shared/` references;
- no summarized replacement for the listed original sections.

Implementation must not compose new staged-skill prose from these requirements.
The staged skill files must be replaced with the literal router text provided in
the implementation plan. Only the router-only frontmatter name/description,
stage-specific route list, owned scope, recommended model tier, and next-stage
handoff label may differ between staged skills, plus stage-specific
stop/precondition lines that appear in the literal router text in the
implementation plan.

Entry, exit, and handoff glue must not copy command syntax, gate checklists,
helper behavior, or other workflow rules from the canonical skill. If a staged
skill needs those details, it must route to the relevant section in
`../vicaya/SKILL.md`.

Each staged skill must include this exact section-boundary rule:

`For each listed heading, read from that heading through the line before the
next non-fenced Markdown heading in ../vicaya/SKILL.md that is either (a) of
the same or higher level, or (b) itself separately listed in this skill's
route list — whichever comes first.`

Each staged skill must include this exact guard line:

`Do not read or create staged shared-reference files under skill/vicaya/shared/.`

Each staged skill must include this exact out-of-scope guard line:

```text
If any routed canonical instruction requires work outside this staged skill's owned scope, do not perform that work here. Stop and hand off with the same scratch slug to the staged skill that owns the required phase.
```

### Stage section routing

A routed section means the named heading as a real Markdown heading anchor in
source order. Do not use headings inside fenced code blocks as route anchors.
For headings that occur more than once, verify the intended non-fenced
canonical occurrence. For each listed heading, read from that heading through
the line before the next non-fenced heading in ../vicaya/SKILL.md that is
either (a) of the same or higher level, or (b) itself separately listed in this
skill's route list — whichever comes first. Do not use generic heading
extraction that can swallow unrelated later phases.

Route lists in staged skills must be written in canonical source order to
reduce reader error. For `vicaya-0-scope`, this means `## Inputs` and
`### Question sanitization` appear before `## Setup — paths and tools`.

Every stage must read the shared global original sections needed for safe
execution, plus its owned phase sections.

All stages must read these exact original sections from `../vicaya/SKILL.md`:

- `## Critical execution rules`
- `## Hard rules (read first — these are not preferences)`
- `## Setup — paths and tools`
- `## Calling the helpers`
- `## Research scratchpad`
- `## Research phases (Phase 0 through 7)`

`vicaya-0-scope` must also read:

- `## Inputs`
- `### Question sanitization`
- `### Phase 0 — Request understanding and scope check`

`vicaya-1-gather` must also read:

- `## Helper return shapes (read before calling)`
- ``## Book-identifier lookups (`lookup-book`)``
- ``## DPD dictionary database (`dpd.db`)``
- `## EBC vault (Early Buddhist Connections)`
- `## Evidence tiers`
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

`vicaya-2-synthesize-review` must also read:

- `## Evidence tiers`
- `## Bibliography`
- `### Phase 5 — Synthesis`
- `### Phase 6 — Second-pass review (cross-check)`
- `## When something fails`
- `## Style notes`
- `### Pāḷi/English presentation (vault note only)`
- `### Footnote definitions (vault note only)`

`vicaya-3-complete` must also read:

- `## Evidence tiers`
- `## Bibliography`
- `### Phase 7 — Write the note`
- `### Frontmatter rules (agents get these wrong — read carefully)`
- `### Correct frontmatter example (reference this when writing)`
- `### PDF generation (run after every successful vault write)`
- `### GitHub note sync (pre-approved)`
- `## Final report to the user`
- `## When something fails`
- `## When Obsidian isn't running`
- `## Style notes`
- `### Pāḷi/English presentation (vault note only)`
- `### Footnote definitions (vault note only)`
- `## Self-improvement loop (mandatory)`

These routing lists may only be expanded during implementation. Do not tighten
or remove a listed section in this thread. If a listed section appears
irrelevant or missing, stop and revise the plan with explicit user approval.
They must not be replaced with summaries.

### Handoff behavior

The staged handoff must use the existing scratch system described in the
canonical skill only. Staged skills must not restate scratch command syntax,
phase gate lists, helper behavior, or publishing commands. They may only say:

- use the same scratch slug for the next staged skill;
- read and follow the routed canonical scratch, entry, exit, and handoff
  sections exactly;
- if a routed canonical instruction requires work outside the current staged
  skill's owned scope, stop and hand off with the same scratch slug to the
  staged skill that owns that phase;
- do not introduce any workflow state outside the canonical scratch system.

For `vicaya-3-complete`, Phase 5/6 completeness must be determined only by the
routed canonical scratch/gate instructions. If the canonical scratch/gate state
shows Phase 6 is incomplete, stop and hand off to `vicaya-2-synthesize-review`
with the same scratch slug. Do not infer completion from a local checklist.

### Documentation

Update documentation to reflect the corrected staged design:

- `skill/vicaya/README.md` must be a concise mode-and-registration note only:
  it states the difference between the monolithic full-run skill and the four
  staged section-router skills, and it states distribution parity. It must not
  include phase summaries, command syntax, helper behavior, dependency tables,
  output templates, staged handoff instructions, or other workflow paraphrases.
- `kamma/project.md` must state that staged mode routes to exact sections in
  `skill/vicaya/SKILL.md`, and that behavioral changes belong in the monolithic
  skill first.
- Any existing statement that staged/shared files contain concise references
  must be removed or corrected.

Staged skill distribution must mirror the active distribution mechanism used by
the monolithic `vicaya` skill. For every active skill root where `vicaya` is
registered, each staged skill must also be registered beside it and point to the
corresponding project directory under `skill/`.

If an active skill root registers `vicaya` as a symlink to
`/Users/deva/Documents/dps/vicaya/skill/vicaya`, each staged skill in that root
must also be a sibling symlink to its matching project directory:

- `<root>/vicaya-0-scope` -> `/Users/deva/Documents/dps/vicaya/skill/vicaya-0-scope`
- `<root>/vicaya-1-gather` -> `/Users/deva/Documents/dps/vicaya/skill/vicaya-1-gather`
- `<root>/vicaya-2-synthesize-review` -> `/Users/deva/Documents/dps/vicaya/skill/vicaya-2-synthesize-review`
- `<root>/vicaya-3-complete` -> `/Users/deva/Documents/dps/vicaya/skill/vicaya-3-complete`

This thread may create missing staged symlinks or replace stale staged symlinks
in active skill roots, using the same symlink style as the existing monolithic
`vicaya` registration. Do not modify the monolithic `vicaya` registration
itself. Do not create staged registrations in roots where `vicaya` is not
registered.

## Assumptions & uncertainties

Assumptions:

- `skill/vicaya/SKILL.md` is stable enough to use heading names as routing
  anchors.
- Markdown heading names are the correct routing primitive; no new Python
  extraction script is required.
- The agent using a staged skill can read `../vicaya/SKILL.md` from the sibling
  `vicaya` skill directory.
- The current scratch commands already support staged handoff. If not, stop and
  report the blocker; no Python code changes belong in this thread.
- Stages 1–3 re-attach to an existing scratch file via `scratch-resume <slug>`
  rather than creating a new one. The staged skills do not state this command;
  a fresh-session agent must follow the routed canonical `## Research scratchpad`
  section to determine the correct re-attach behavior. This is an accepted risk
  of the no-paraphrase rule; it is not a defect to fix in this thread.
- Active skill roots may include `/Users/deva/.agents/skills/`,
  `/Users/deva/.codex/skills/`, and `/Users/deva/.claude/skills/`. Only roots
  where the monolithic `vicaya` skill is registered require staged registrations,
  and the staged registrations must use the same registration mechanism as
  monolithic `vicaya`.

Uncertainties:

- Some section headings inside the Phase 7 note template are also ordinary note
  headings. Verification must distinguish real canonical skill headings from
  headings inside fenced Markdown examples.
- `## Bibliography` occurs twice in `skill/vicaya/SKILL.md`: real anchor at
  line 394, and a fenced copy at line 1626 inside the Phase 7 note template.
  Stages that route `## Bibliography` must resolve to line 394. Verification
  must confirm the line 1626 occurrence is fenced and never treated as an anchor.
- If heading names later change in `skill/vicaya/SKILL.md`, staged routing can
  break. This is acceptable only if review catches it with explicit heading
  existence checks.

## Constraints

- Do not change `.env` or `.ini` files.
- Do not change research behavior.
- Do not summarize or paraphrase original workflow instructions.
- Do not introduce workflow state outside the canonical scratch system.
- Do not edit Python code. If a canonical scratch command is missing or broken,
  stop and report the blocker.
- Do not run project-wide validation by default.
- For documentation-only changes, use structural read/grep checks.
- Preserve unrelated dirty files and user changes.
- Do not modify the monolithic `vicaya` registration. Staged skill links may be
  created or corrected only in active skill roots where `vicaya` is already
  registered, and must use the same link style as `vicaya`.
- Do not use `git reset`, `git checkout --`, or `git revert` to remove the
  failed staged attempt. Use Git only for inspection.
- Do not commit, pull, or push.

## User revision — staged context-budget controls

This section intentionally supersedes the pure-router constraint for bounded
context-management instructions in `skill/vicaya-0-scope/SKILL.md`,
`skill/vicaya-1-gather/SKILL.md`, and
`skill/vicaya-2-synthesize-review/SKILL.md`, and
`skill/vicaya-3-complete/SKILL.md`. The canonical full-run skill remains
unchanged because it targets a model/context profile that does not need this
staged-context protection.

`vicaya-0-scope` may include one bounded stage-local context-plan block that
asks the advanced model to decide, after Phase 0 scoping and before Phase 1
work, whether Stage 1, Stage 2, and Stage 3 are likely to be extensive enough
to require fixed fresh-context hard stops. This context plan is allowed only to
manage staged-run context-budget risk.

`vicaya-1-gather`, `vicaya-2-synthesize-review`, and `vicaya-3-complete` may
include bounded stage-local context-break guards. These guards must honor any
Phase 0 context plan recorded in scratch and must stop at the planned natural
boundaries inside their owned scope so the next session can resume with the
same scratch slug. A recorded context plan is binding for staged mode and
overrides model-tier recommendations unless the user explicitly opts out before
Stage 1 begins and that opt-out is recorded in scratch.

For extensive Stage 1 gathering, the default context plan must prefer grouped
cost-control source-block hard stops over per-source micro-sessions. Stage 1
source blocks should default to four bundled sessions where applicable:

- Phase 1 vault/context setup plus root-canon mūla/sutta research;
- canonical exegesis/commentary research only;
- Phase 2.5 parallel research plus library research plus Sanskrit source
  research;
- web, YouTube, and WisdomLib research.

Every `vicaya-1-gather` invocation under a recorded `stage-1-context-plan`
must run exactly one next grouped source block and then hard-stop again; a
prior hard stop is only a handoff checkpoint, not evidence that the whole Stage
1 plan has already been satisfied.

Stage 1 may hard-stop inside Phase 2 after root-canon mūla/sutta research when
commentary/ṭīkā research remains. That stop must be recorded as a concise
in-progress handoff note in scratch. It must not write the Phase 2 gate until
all canonical Phase 2 obligations are complete.

For extensive Stage 2 synthesis/review, the default context plan must keep two
sessions and rebalance the heavy Phase 5 work into the lighter Phase 6 session
without introducing new synthesis or review logic:

- Phase 5 entry verification, scratch review, source completeness check, angle
  coverage check, Devil's Advocate answers, bibliography/source allocation
  review, and a concise scratch-logged Phase 5 drafting plan; then hard stop
  before full drafting.
- Complete Phase 5 drafting/integration and the Phase 5 gate, then run Phase 6
  second-pass review and the Phase 6 gate.

For extensive Stage 3 completion, the default context plan may use a
scratch-local Phase 7 draft file under `data/scratch/`, normally
`data/scratch/<scratch-slug>.phase7-draft.md`. The draft file is a durable
completion artifact for section-by-section note writing; the main scratch must
record the draft path, section order, source allocation, section status, and
handoff notes. This avoids requiring the model to hold or paste the complete
final note in one context. It does not change the canonical Phase 7 gate,
validation, PDF, run-report sync, final report, or self-improvement
requirements.

The Stage 3 draft file may contain incomplete section drafts, but it is never
the vault note. The vault must receive only the complete audited note after all
sections are finished and checked against the routed canonical Phase 7,
frontmatter, bibliography, and style requirements.

After live testing showed that adaptive "continue while context remains healthy"
wording can still push Stage 3 completion to the edge of context, extensive
Stage 3 completion must default to a fixed three-run split:

- Run 1: create the Phase 7 writer brief and scratch-local draft file, record
  title/slug/outline/source allocation/frontmatter targets, write `## Question`,
  `## Findings`, Canon Evidence, and Commentary Evidence, then hard stop.
- Run 2: write the remaining evidence/support sections, confirm frontmatter
  `canon_refs`, audit the complete draft against routed canonical Phase
  7/frontmatter/bibliography/style requirements, then hard stop before any vault
  write.
- Run 3: write only the complete audited draft to the vault, validate, generate
  PDF, run the Phase 7 gate, sync the note and run report, complete the final
  user report, and run the self-improvement loop.

Under these default splits, staged skills must not continue from one run group
into the next for any reason. Do not rely on model judgement such as "context
seems comfortable", "context pressure is high", "the dossier is manageable",
or conditional/adaptive continuation. The model cannot reliably calculate
current context usage, so context control must be predetermined hard stops.

The approved extensive staged split is `1 + 4 + 2 + 3`: one Stage 0 scoping
invocation, four Stage 1 gathering invocations, two Stage 2 synthesis/review
invocations, and three Stage 3 completion invocations.

Golden rule: do not introduce any new research logic. The canonical
`skill/vicaya/SKILL.md` remains the source of the actual workflow, quality
standard, evidence rules, gates, helper behavior, final-note requirements, and
self-improvement loop. This staged thread only redistributes the same
canonical work across fixed fresh-context sessions.

The context plan and guards may:

- record no split for ordinary runs;
- record binding split Stage 1 passes for extensive research;
- record binding split Stage 2 passes for extensive synthesis/review;
- record binding split Stage 3 passes for extensive completion work;
- tell the user to refresh context between those passes;
- use the canonical scratch logging mechanism routed from
  `../vicaya/SKILL.md` to record context plans, opt-outs, and mid-stage
  handoffs.
- use a scratch-logged Stage 1 grouped source-block checkpoint inside Phase 2
  when a source-class split is needed before the canonical Phase 2 gate.
- use a scratch-local Phase 7 draft file for section-by-section final-note
  drafting, with scratch-logged path and section status.

The context plan and guards must not:

- change any canonical research phase, source requirement, evidence standard,
  synthesis requirement, review requirement, helper behavior, or phase gate;
- introduce any new research logic beyond fixed redistribution of canonical
  work across fresh-context sessions;
- create workflow state outside the canonical scratch system, except for the
  scratch-local Phase 7 draft file allowed above;
- perform work outside the owning staged skill's phase scope;
- modify `skill/vicaya/SKILL.md`;
- authorize any staged skill to summarize or replace canonical workflow
  instructions;
- allow a partial or draft note to be written to the vault.

If Stage 0 judges the run extensive, it must explicitly tell the user that the
planned fresh-context passes will be used by default, and that the user should
say so before starting Stage 1 if they do not want those breaks. If the user
opts out, the opt-out must be logged in scratch and later staged skills must
treat the planned hard stops as disabled while keeping all canonical phase
boundaries intact.

Durable staged-mode documentation may mention these bounded context-management
exceptions so it does not falsely describe all staged skills as pure routers.

## How we'll know it's done

The thread is done when:

- The failed summarized staged references are removed.
- `skill/vicaya/shared/` is absent after the failed summarized references are
  removed.
- The failed staged attempt was reset by explicit deletion/overwrite in this
  thread, not by broad Git reversal.
- The four staged skill files exist.
- Each staged skill routes to exact headings in `../vicaya/SKILL.md`.
- No staged skill contains a paraphrased substitute for the canonical workflow
  sections it points to.
- No staged skill copies canonical command syntax, phase gate lists, helper
  behavior, or publishing behavior.
- Every stage has correct model recommendation, owned phase scope, stage
  boundary labels, and next-stage handoff label.
- Every staged skill stops and hands off with the same scratch slug if a routed
  canonical instruction requires work outside its owned scope.
- `skill/vicaya/SKILL.md` remains the canonical full-run skill.
- If `skill/vicaya/SKILL.md` is edited, the diff is limited to the existing
  staged-mode pointer near the top and contains no behavioral workflow change,
  aside from any pre-existing hunks recorded before implementation.
- `skill/vicaya/README.md` describes only monolithic-vs-staged mode difference,
  distribution parity, and bounded staged context-budget controls, with no
  other workflow paraphrase.
- README files contain concise staged-skill references beside the main skill
  references without replacing the restored main-skill descriptions.
- `kamma/project.md` and `kamma/tech.md` describe the maintenance coupling
  between the canonical skill and staged sibling skills.
- Verification confirms that every heading named by a staged skill exists as a
  real non-fenced heading in `skill/vicaya/SKILL.md`.
- Verification confirms no staged skill or durable project doc introduces
  workflow state outside the canonical scratch system.
- Verification confirms active staged skill registrations use the same link
  style as the monolithic `vicaya` registration and point to the rebuilt staged
  directories.
- Review confirms there are no behavioral additions, omissions, or summaries in
  the staged files, except for the bounded binding context-budget plan and
  context-break guards allowed by the user-revision section above.
- Review confirms extensive `vicaya-1-gather` runs use one grouped source-block
  hard stop per invocation, default to no more than four Stage 1 gathering
  invocations where all blocks apply, and do not treat a prior hard stop as
  completion of the whole Stage 1 plan.
- Review confirms extensive `vicaya-2-synthesize-review` runs default to two
  invocations where the first records a Phase 5 drafting plan and the second
  completes Phase 5 plus Phase 6.
- Review confirms extensive `vicaya-3-complete` runs use a scratch-local
  Phase 7 draft file for section-by-section note writing and never write an
  incomplete draft to the vault.
- Review confirms the approved extensive split is `1 + 4 + 2 + 3`, uses only
  predetermined hard stops, and introduces no new research logic beyond
  redistributing canonical work across fresh-context sessions.

## What's not included

- No redesign of Vicaya research phases.
- No generated extraction system.
- No new scratch/handoff mechanism.
- No Python code changes.
- No model-switching automation.
- No cleanup of unrelated dirty files.
- No finalization of the previous blocked thread.
