# Plan - Rebuild Vicaya staged skills as exact section routers

No GitHub issue is associated with this thread.

## Architecture Decisions

- Treat `skill/vicaya/SKILL.md` as the only behavioral source of truth.
  - Rationale: the user explicitly rejected summaries, paraphrases, and context
    reduction by rewriting. Staged context saving is allowed only by loading
    fewer original sections.
- Make staged skills section routers, not alternate documentation.
  - Rationale: each staged skill should select exact canonical sections for the
    current phase, then add only router boundary labels, precondition lines from
    the literal templates, and same-slug handoff labels. Command syntax, gate
    lists, helper behavior, and publishing behavior stay in the canonical skill
    only.
- Remove the failed `skill/vicaya/shared/*.md` summarized references without
  creating replacement shared routing or reference files.
  - Rationale: the failed references caused the deviation. Keeping them invites
    agents to use summaries instead of the canonical skill.
- Reset the failed staged attempt by explicit deletion and overwrite in this
  thread, not by Git reversal.
  - Rationale: `git reset`, `git checkout --`, or `git revert` could discard
    unrelated user work or obscure what this corrective thread actually changed.
- Keep `skill/vicaya/SKILL.md` behavior intact.
  - Rationale: the existing full-run workflow is canonical and must not become
    a dispatcher or staged dependency. The only allowed canonical-skill edit is
    a narrow nonbehavioral update to the existing staged-mode pointer near the
    top, so it says staged skills read exact sections from this file and this
    file remains the only behavioral source of truth.
- Keep `skill/vicaya/README.md` as a concise mode-and-registration note only.
  - Rationale: phase summaries, command syntax, helper behavior, dependency
    tables, and staged handoff instructions are workflow paraphrases. The README
    should say only how the monolithic skill differs from the staged routers and
    how staged routers are distributed beside the monolithic skill.
- Mirror the monolithic `vicaya` skill's active distribution for every staged
  skill.
  - Rationale: if an agent can load `vicaya` from a skill root, it must load the
    staged routers from the same root; stale registrations recreate the failed
    behavior even if the repo files are correct. The staged skills must be
    linked the same way the monolithic `vicaya` skill is linked in each active
    root.
- Use structural verification, not keyword verification.
  - Rationale: prior `rg` checks passed while behavior was missing. The new
    checks must verify heading existence, absence of summarized reference files,
    and absence of behavioral paraphrases in staged skills.
- Do not touch Python code. If a scratch command required by the canonical skill
  is missing or broken, stop and report the blocker.
  - Rationale: this is a skill/documentation rebuild.
- Accept the init-vs-resume inference asymmetry in staged handoff.
  - Rationale: `vicaya-0-scope` creates the scratch via `scratch-init`; stages
    1–3 must re-attach via `scratch-resume <slug>`. The staged skills are
    forbidden from restating command syntax, so a fresh-session agent must
    infer "resume, don't init" from the canonical `## Research scratchpad`
    section. This works for a careful agent following the routed canonical
    text, but it is the thinnest point in the cross-session handoff. It is an
    accepted risk of the no-paraphrase rule, not a plan defect. If a stage
    1–3 agent runs `scratch-init` instead of `scratch-resume`, it will
    overwrite the active pointer; the fix is to re-run with the correct slug.
    Do not add inline resume instructions to the staged skills to compensate.

## Staged Skill Model Recommendations

| Stage skill | Recommended tier | Reason |
|---|---|---|
| `vicaya-0-scope` | Advanced | Phase 0 framing, ambiguity handling, and research brief shape the whole run. |
| `vicaya-1-gather` | Fast | Phase 1-4c source retrieval is mostly mechanical when the canonical sections are followed exactly. |
| `vicaya-2-synthesize-review` | Advanced | Phase 5-6 evidence weighing, synthesis, and second-pass review require reasoning. |
| `vicaya-3-complete` | Fast | Phase 7 rendering and validation are mechanical if the canonical scratch/gate state shows Phase 5/6 synthesis is complete; otherwise hand off to `vicaya-2-synthesize-review` with the same scratch slug. |

Out-of-scope handoff ownership:

- Phase 0 -> `vicaya-0-scope`
- Phase 1 through Phase 4c -> `vicaya-1-gather`
- Phase 5 and Phase 6 -> `vicaya-2-synthesize-review`
- Phase 7, final report, completion failure handling, style rules, and
  self-improvement loop -> `vicaya-3-complete`

## Phase 1 - Pre-edit audit and reset boundary

- [x] Confirm the previous thread remains blocked.
  - Read: `kamma/threads/20260602_vicaya-staged-skills/review.md`.
  - Confirm it contains `## Verdict` followed by `BLOCKED`.
  - Do not edit the previous thread except if the user explicitly asks.
  - -> verify: `rg -n "BLOCKED|Strict audit basis|section-by-section equivalence" kamma/threads/20260602_vicaya-staged-skills/review.md` shows the blocking audit.

- [x] Record the exact files owned by this reset.
  - Owned changes in this thread are limited to:
    - `skill/vicaya-0-scope/SKILL.md`
    - `skill/vicaya-1-gather/SKILL.md`
    - `skill/vicaya-2-synthesize-review/SKILL.md`
    - `skill/vicaya-3-complete/SKILL.md`
    - `skill/vicaya/shared/core.md`
    - `skill/vicaya/shared/scope.md`
    - `skill/vicaya/shared/sources.md`
    - `skill/vicaya/shared/synthesis.md`
    - `skill/vicaya/shared/completion.md`
    - `skill/vicaya/README.md`
    - `skill/vicaya/SKILL.md` lines 10-12 only, for the nonbehavioral staged
      pointer wording described in Phase 7.
    - `kamma/project.md`
    - staged skill symlinks in active external skill roots where `vicaya` itself
      is already registered as a symlink to this repo's `skill/vicaya`
  - External skill roots are in scope only for staged skill link parity. Do not
    modify the monolithic `vicaya` registration. Do not create staged links in
    roots where `vicaya` is not registered.
  - Run `git status --short` immediately before editing.
  - Run `git diff -- skill/vicaya/SKILL.md` immediately before editing and
    record whether any non-pointer hunks already exist. Treat those hunks as
    pre-existing user or prior-thread work: preserve them unchanged, do not
    revert them, and do not count them as this thread's allowed edit.
  - Treat `skill/vicaya/SKILL.md` as behavior-read-only even if it is dirty.
    Do not change any workflow rule, phase text, helper instruction, command,
    heading, or source guidance in that file.
  - For dirty owned docs (`skill/vicaya/README.md`, `kamma/project.md`),
    inspect existing diffs first and edit only stale staged-mode references
    required by this plan.
  - Do not modify unrelated dirty files, including Python files, `runs/*.md`, or
    unrelated thread files.
  - -> verify: fresh `git status --short` is recorded in review notes, this
    thread's repo diff is limited to the approved owned Markdown files, and
    external changes are limited to staged symlink parity. Any non-pointer
    `skill/vicaya/SKILL.md` hunks in the final diff must match the pre-edit diff
    exactly.

- [x] Read the canonical skill headings and route anchors.
  - Run `rg -n "^## |^### |^#### " skill/vicaya/SKILL.md`.
  - Treat this command as a locator only. Manually confirm that each routed
    heading is a real non-fenced Markdown heading, not a heading inside a fenced
    note template or example.
  - Do not save a derived heading list as workflow state. Re-read the canonical
    headings directly during implementation and review.
  - -> verify: output includes every required heading named in this plan.
  - Note: many canonical headings use an em-dash (—, U+2014). All route strings
    in staged skill files and all `rg` patterns in this plan must reproduce that
    exact character. A hyphen (-) or en-dash (–) will silently fail to match.

- [x] Confirm the shared-reference reset boundary.
  - Delete the failed summarized files and leave no shared staged reference
    files.
  - Do not create `skill/vicaya/shared/README.md` or any replacement shared
    routing/reference file.
  - After deleting the five failed shared-reference files,
    `skill/vicaya/shared/` must be absent. If the directory still exists and is
    empty, remove it with `rmdir skill/vicaya/shared`. If it contains any
    unexpected file, stop and ask for approval before touching it.
  - -> verify: `test ! -e skill/vicaya/shared` passes. If it fails, inspect the
    directory. Empty directory means remove with `rmdir`; unexpected contents
    mean block for approval.

## Phase 2 - Reset failed staged implementation

This is the point where the previous failed attempt is removed. Do not use
`git reset`, `git checkout --`, or `git revert` to undo the failed attempt. Use
Git only to inspect status and diffs. The reset is intentional new work in this
thread.

- [x] Delete the failed shared references.
  - Delete these files:
    - `skill/vicaya/shared/core.md`
    - `skill/vicaya/shared/scope.md`
    - `skill/vicaya/shared/sources.md`
    - `skill/vicaya/shared/synthesis.md`
    - `skill/vicaya/shared/completion.md`
  - Delete exactly these files with: `rm skill/vicaya/shared/core.md skill/vicaya/shared/scope.md skill/vicaya/shared/sources.md skill/vicaya/shared/synthesis.md skill/vicaya/shared/completion.md`
  - After deleting those files, `skill/vicaya/shared/` must be absent. If the
    directory remains and is empty, remove it with `rmdir skill/vicaya/shared`.
    Use only empty-directory removal, not recursive deletion.
  - If `skill/vicaya/shared/` contains any unexpected file after deleting the
    five failed files, stop and ask for approval before touching it.
  - -> verify: `test ! -e skill/vicaya/shared` passes. If it fails, inspect the
    directory. Empty directory means remove with `rmdir`; unexpected contents
    mean block for approval.

- [x] Prepare to overwrite the four failed staged skill files.
  - Overwrite these files only with the literal router text in Phases 3-6:
    - `skill/vicaya-0-scope/SKILL.md`
    - `skill/vicaya-1-gather/SKILL.md`
    - `skill/vicaya-2-synthesize-review/SKILL.md`
    - `skill/vicaya-3-complete/SKILL.md`
  - Do not preserve any prose from the failed staged skill files unless it
    appears verbatim in the literal router text in this plan.
  - Do not edit or finalize the previous blocked Kamma thread. It remains
    historical evidence of the failed approach.
  - -> verify: after Phases 3-6, `git diff -- skill/vicaya-* skill/vicaya/shared`
    shows deletion of shared summaries and replacement of staged skills, not
    unrelated cleanup.

- [x] Remove stale references to summarized or shared staged files from staged
  skill docs and durable project docs.
  - The new staged skills must not say to read:
    - `../vicaya/shared/core.md`
    - `../vicaya/shared/scope.md`
    - `../vicaya/shared/sources.md`
    - `../vicaya/shared/synthesis.md`
    - `../vicaya/shared/completion.md`
  - Durable docs must not describe `../vicaya/shared`, `skill/vicaya/shared`,
    `shared/*.md`, shared references, shared-reference files, or shared staged
    references as part of staged behavior.
  - Allowed staged-skill shared-path hit: only the exact guard line
    `Do not read or create staged shared-reference files under skill/vicaya/shared/.`
  - -> verify: `rg -n "../vicaya/shared|skill/vicaya/shared|shared/\\*\\.md|shared references|shared-reference|shared staged reference|shared staged references" skill/vicaya/README.md kamma/project.md skill/vicaya-*/SKILL.md` shows no README or `kamma/project.md` hits, and any staged-skill hit is only the exact guard line.

## Phase 3 - Rebuild `vicaya-0-scope`

For every exact staged-skill content block in Phases 3-6, write the code block
body only. Do not include the surrounding fence markers or list indentation in
the target file.

- [x] Replace `skill/vicaya-0-scope/SKILL.md` with a section-router skill.
  - Use this exact file content:
    ```markdown
    ---
    name: vicaya-0-scope
    description: Route Vicaya Stage 0 to exact canonical Phase 0 sections in ../vicaya/SKILL.md.
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

    Do not read or create staged shared-reference files under skill/vicaya/shared/.
    ```
  - -> verify: read the file end-to-end. Every non-frontmatter line must pass
    the router-line classification in Phase 8. `rg -n "uv run|scratch-init|scratch-resume|scratch-verify|scratch-gate|../vicaya/shared" skill/vicaya-0-scope/SKILL.md` returns no hits.

## Phase 4 - Rebuild `vicaya-1-gather`

- [x] Replace `skill/vicaya-1-gather/SKILL.md` with a section-router skill.
  - Use this exact file content:
    ```markdown
    ---
    name: vicaya-1-gather
    description: Route Vicaya Stage 1 to exact canonical Phase 1 through Phase 4c sections in ../vicaya/SKILL.md.
    ---

    # Vicaya Stage 1 Gather Router

    This staged skill is a section router into `../vicaya/SKILL.md`.

    Recommended model tier: fast.

    `../vicaya/SKILL.md is the only behavioral source of truth`.

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

    Do not read or create staged shared-reference files under skill/vicaya/shared/.
    ```
  - -> verify: read the file end-to-end. Every non-frontmatter line must pass
    the router-line classification in Phase 8. `rg -n "uv run|scratch-init|scratch-resume|scratch-verify|scratch-gate|../vicaya/shared" skill/vicaya-1-gather/SKILL.md` returns no hits.

## Phase 5 - Rebuild `vicaya-2-synthesize-review`

- [x] Replace `skill/vicaya-2-synthesize-review/SKILL.md` with a section-router skill.
  - Use this exact file content:
    ```markdown
    ---
    name: vicaya-2-synthesize-review
    description: Route Vicaya Stage 2 to exact canonical Phase 5 and Phase 6 sections in ../vicaya/SKILL.md.
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

    Do not read or create staged shared-reference files under skill/vicaya/shared/.
    ```
  - -> verify: read the file end-to-end. Every non-frontmatter line must pass
    the router-line classification in Phase 8. `rg -n "uv run|scratch-init|scratch-resume|scratch-verify|scratch-gate|../vicaya/shared" skill/vicaya-2-synthesize-review/SKILL.md` returns no hits.

## Phase 6 - Rebuild `vicaya-3-complete`

- [x] Replace `skill/vicaya-3-complete/SKILL.md` with a section-router skill.
  - Use this exact file content:
    ```markdown
    ---
    name: vicaya-3-complete
    description: Route Vicaya Stage 3 to exact canonical Phase 7, final-report, style, failure, and self-improvement sections in ../vicaya/SKILL.md.
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
    - `### GitHub note sync (pre-approved)`
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

    Do not read or create staged shared-reference files under skill/vicaya/shared/.
    ```
  - -> verify: read the file end-to-end. Every non-frontmatter line must pass
    the router-line classification in Phase 8. `rg -n "uv run|scratch-init|scratch-resume|scratch-verify|scratch-gate|sync_run_report|../vicaya/shared" skill/vicaya-3-complete/SKILL.md` returns no hits.

## Phase 7 - Documentation correction

- [x] Update the existing staged-mode pointer in `skill/vicaya/SKILL.md`.
  - This is the only allowed edit to `skill/vicaya/SKILL.md`.
  - Replace only the existing staged-mode pointer near the top with this exact
    text:
    ```markdown
    For lower-context staged runs, use `vicaya-0-scope`, `vicaya-1-gather`,
    `vicaya-2-synthesize-review`, and `vicaya-3-complete`; those staged skills are
    section routers that read exact sections from this file. This file remains the
    canonical one-goal `/vicaya` workflow and the only behavioral source of truth.
    ```
  - Do not change any canonical heading, phase text, command, helper rule, source
    instruction, scratch behavior, or workflow behavior.
  - -> verify: compared with the pre-edit `git diff -- skill/vicaya/SKILL.md`,
    this thread introduces only this pointer wording change. Any other
    `skill/vicaya/SKILL.md` hunks must be unchanged pre-existing hunks.

- [x] Update `skill/vicaya/README.md`.
  - Replace it with a concise mode-and-registration note only.
  - Do not include phase summaries, command syntax, helper behavior, dependency
    tables, output templates, staged handoff instructions, source layout, known
    limitations, or other workflow paraphrases. Those belong only in
    `skill/vicaya/SKILL.md`, except for the bounded context-budget controls
    later added by Phases 9.5-9.10.
  - The README must state:
    - `/vicaya` is the monolithic full-run skill.
    - The four staged skills are `vicaya-0-scope`, `vicaya-1-gather`,
      `vicaya-2-synthesize-review`, and `vicaya-3-complete`.
    - The staged skills are section routers into exact headings in
      `skill/vicaya/SKILL.md`.
    - The staged skills save context by reading fewer canonical sections and,
      for extensive runs, by using bounded scratch-backed context breaks.
    - `skill/vicaya/SKILL.md` is the only behavioral source of truth.
    - Staged skills must not use summaries, paraphrases, shared staged reference
      files, or replacement behavior.
    - Staged skills must be registered beside `vicaya` in every active skill
      root that distributes `vicaya`.
  - -> verify: read `skill/vicaya/README.md` end-to-end and confirm it contains
    only monolithic-vs-staged mode difference, registration parity, and bounded
    context-budget controls, with no other workflow paraphrase. `rg -n "shared/(core|scope|sources|synthesis|completion)\\.md|concise reference|uv run|Phase [0-9]|Helper|Dependency|Known limitations|Source layout" skill/vicaya/README.md`
    returns no hits.

- [x] Update `kamma/project.md`.
  - Replace the current dual-mode maintenance rule if it mentions staged shared
    references as behavior holders.
  - The maintenance rule must contain this exact wording:
    ```markdown
    Vicaya has two execution modes: full-run `/vicaya` uses `skill/vicaya/SKILL.md`; staged mode uses `vicaya-0-scope`, `vicaya-1-gather`, `vicaya-2-synthesize-review`, and `vicaya-3-complete` as section routers into exact headings in `skill/vicaya/SKILL.md`.
    `skill/vicaya/SKILL.md` is the only behavioral source of truth. Behavioral workflow changes go there first. Staged skill files may only update routing lists, stage-local boundary/precondition lines, and stage-local entry/exit/handoff labels.
    Staged mode saves context only by not reading unrelated original sections. It must not use summaries, paraphrases, shared staged reference files, or replacement behavior.
    Staged skill distribution must mirror the active distribution mechanism used by the monolithic `vicaya` skill. Every active skill root that registers `vicaya` must register the four staged skills beside it, using the same link style and pointing to the corresponding project directories under `skill/`.
    When canonical headings change, update the staged route lists in the same thread or explicitly block the change.
    ```
  - -> verify: `rg -n "section|route|canonical|shared reference|behavior" kamma/project.md` shows the corrected maintenance rule.

## Phase 8 - Structural verification

- [x] Verify every staged heading exists in the canonical skill.
  - For each exact heading listed in each staged skill, run a focused `rg -n`
    search against `skill/vicaya/SKILL.md`.
  - Plain `rg` is only a locator. Manually read around each hit to confirm it is
    a real non-fenced heading anchor in the canonical skill, not a heading
    inside a fenced Markdown example or note template.
  - Do not create a heading-extraction script or generated extraction system.
  - Boundary determination must track code-fence open/close state, not just
    run a heading regex. A `#`-prefixed line inside a fenced block is not a
    heading anchor; an unclosed fence invalidates all subsequent heading
    matches until it closes.
  - -> verify: all routed headings were found as real non-fenced heading
    anchors.

- [x] Verify `## Investigation angles` boundary does not bleed into later phases.
  - `## Investigation angles` is at line 514 of `skill/vicaya/SKILL.md`. The
    next `##`-or-higher heading after it (ignoring fenced lines) is
    `## Final report to the user` at line 1834 — nearly the whole file.
    Note: `## Angle triage` at line 539 appears in `rg` output but is inside
    a fenced code example (fence opens at line 538, closes at line 544); it
    is not a heading anchor and does not stop the boundary.
    Under the amended rule, reading stops at `### Textual layers` (line 546)
    because that heading is separately listed in `vicaya-1-gather`'s route
    list. Confirm this is the actual boundary produced.
  - Read lines 514–560 of `skill/vicaya/SKILL.md` and confirm the boundary
    falls at `### Textual layers` (or the first listed `###` child), not at
    line 1834.
  - -> verify: `## Investigation angles` route covers lines 514–545 only
    (the intro + triage example) and does NOT include Phase 5, Phase 6,
    Phase 7, or note-template content.

- [x] Verify `### Phase 7 — Write the note` boundary is not truncated by fenced
  template headings.
  - The fenced markdown template beginning at line 1543 contains `## Question` (1563),
    `## Findings` (1566), `## Canon Evidence (T1)` (1569), and ~10 other `##`/`###`-level
    lines, and closes at line 1668. None are canonical heading anchors.
  - Confirm `### Phase 7 — Write the note` (1524) reads through line 1669, and
    `### Frontmatter rules (agents get these wrong — read carefully)` (1670) starts the
    next listed section.
  - Read lines 1524–1675 of `skill/vicaya/SKILL.md` and confirm the fenced block open
    at 1543 and close at 1668, with `### Frontmatter rules` beginning immediately
    after.
  - -> verify: `rg -n -C 80 '### Phase 7 — Write the note|### Frontmatter rules' skill/vicaya/SKILL.md`
    shows `### Phase 7` at 1524, the fenced markdown template opening at 1543,
    the fenced template closing at 1668, and `### Frontmatter rules` at 1670.

- [x] Verify `## Self-improvement loop (mandatory)` boundary is not truncated by
  fenced reflection-template headings.
  - The fenced markdown template in this section contains ordinary note headings
    such as `## Retrospective`, `## What I changed this run`, and
    `## Channel tuning`. None are canonical heading anchors.
  - Confirm `## Self-improvement loop (mandatory)` reads through all of its real
    child sections and that fenced headings inside the reflection template are
    ignored as route anchors.
  - -> verify: read the self-improvement section in `skill/vicaya/SKILL.md`
    around the fenced template and confirm the fence opens and closes before
    heading-boundary decisions resume.

- [x] Verify `## Bibliography` routes to the real anchor, not the fenced copy.
  - `## Bibliography` occurs twice in `skill/vicaya/SKILL.md`: real anchor at
    line 394, and a copy at line 1626 inside the Phase 7 note-template fence
    (fence opens at line 1543, closes at line 1668). Both `vicaya-2-synthesize-review`
    and `vicaya-3-complete` route `## Bibliography`.
  - Confirm line 1626 is inside the fenced template and is not a heading anchor.
  - Confirm the route resolves to line 394, not line 1626.
  - -> verify: `rg -n "^## Bibliography" skill/vicaya/SKILL.md` shows two hits;
    manually read around line 1626 to confirm it is inside the fence. The routed
    section reads from line 394 through the line before `### Format rules` (419).

- [x] Verify staged files contain no summarized workflow sections.
  - Read all four staged `SKILL.md` files end-to-end.
  - They may contain routing, entry/exit labels, handoff labels, and stop rules.
  - They must not contain command syntax, phase gate lists, compressed helper docs,
    evidence-tier summaries,
    source-search summaries, note-template summaries, failure-handling
    summaries, or self-improvement summaries.
  - Each staged skill must contain the exact section-boundary rule and the exact
    no-shared guard line required in Phases 3-6.
  - Line-by-line classification gate: every non-frontmatter line must be one of
    short purpose statement, router-only section heading, source-of-truth
    statement, route heading, section-reading rule, stop rule, model tier, owned scope,
    entry/exit/handoff label, same-slug instruction, out-of-scope handoff guard, or explicit
    no-summary/no-shared guard.
  - -> verify: line-by-line classification passes. Use `rg -n "uv run|scratch-init|scratch-resume|scratch-verify|scratch-gate|sync_run_report|Evidence tiers:|Bibliography rules|Phase 2:|Phase 5:|Final note template|Calibre search guidelines" skill/vicaya-*/SKILL.md` only as a locator for forbidden copied behavior; it is not pass/fail evidence by itself.

- [x] Verify no stale shared references remain.
  - Run the stale-reference search against implementation and durable project
    docs only, not against this thread's spec/plan, because this thread
    intentionally names the old failed approach as historical context.
  - This check must catch generic stale wording such as `../vicaya/shared`,
    `skill/vicaya/shared`, `shared/*.md`, `shared references`,
    `shared-reference`, and `shared staged reference`, not only the five deleted
    filenames.
  - Allowed staged-skill shared-path hit: only the exact guard line
    `Do not read or create staged shared-reference files under skill/vicaya/shared/.`
  - -> verify: `rg -n "../vicaya/shared|skill/vicaya/shared|shared/\\*\\.md|shared references|shared-reference|shared staged reference|shared staged references|shared/(core|scope|sources|synthesis|completion)\\.md|concise reference files|concise references" skill/vicaya/README.md kamma/project.md skill/vicaya-*/SKILL.md` shows no README or `kamma/project.md` hits, and any staged-skill hit is only the exact guard line.

- [x] Verify the old shared directory is gone.
  - -> verify: `test ! -e skill/vicaya/shared` passes. If it fails, review must
    block unless the remaining path is removed under the reset rules above.

- [x] Mirror active staged skill registration or symlinks.
  - Identify active skill roots where the monolithic `vicaya` skill is
    registered. Inspect expected roots if they exist:
    - `/Users/deva/.agents/skills`
    - `/Users/deva/.codex/skills`
    - `/Users/deva/.claude/skills`
  - For every active skill root containing `vicaya`, confirm all four staged
    skill registrations exist beside it, use the same registration mechanism as
    `vicaya`, and point to the rebuilt staged directories under this repo's
    `skill/` directory.
  - If `vicaya` is a symlink to
    `/Users/deva/Documents/dps/vicaya/skill/vicaya`, each staged skill must also
    be a sibling symlink:
    - `<root>/vicaya-0-scope` -> `/Users/deva/Documents/dps/vicaya/skill/vicaya-0-scope`
    - `<root>/vicaya-1-gather` -> `/Users/deva/Documents/dps/vicaya/skill/vicaya-1-gather`
    - `<root>/vicaya-2-synthesize-review` -> `/Users/deva/Documents/dps/vicaya/skill/vicaya-2-synthesize-review`
    - `<root>/vicaya-3-complete` -> `/Users/deva/Documents/dps/vicaya/skill/vicaya-3-complete`
  - Create missing staged symlinks with `ln -s <target> <link>`.
  - Current symlink-style commands for `/Users/deva/.agents/skills`:
    - `ln -s /Users/deva/Documents/dps/vicaya/skill/vicaya-0-scope /Users/deva/.agents/skills/vicaya-0-scope`
    - `ln -s /Users/deva/Documents/dps/vicaya/skill/vicaya-1-gather /Users/deva/.agents/skills/vicaya-1-gather`
    - `ln -s /Users/deva/Documents/dps/vicaya/skill/vicaya-2-synthesize-review /Users/deva/.agents/skills/vicaya-2-synthesize-review`
    - `ln -s /Users/deva/Documents/dps/vicaya/skill/vicaya-3-complete /Users/deva/.agents/skills/vicaya-3-complete`
  - Current symlink-style commands for `/Users/deva/.claude/skills`:
    - `ln -s /Users/deva/Documents/dps/vicaya/skill/vicaya-0-scope /Users/deva/.claude/skills/vicaya-0-scope`
    - `ln -s /Users/deva/Documents/dps/vicaya/skill/vicaya-1-gather /Users/deva/.claude/skills/vicaya-1-gather`
    - `ln -s /Users/deva/Documents/dps/vicaya/skill/vicaya-2-synthesize-review /Users/deva/.claude/skills/vicaya-2-synthesize-review`
    - `ln -s /Users/deva/Documents/dps/vicaya/skill/vicaya-3-complete /Users/deva/.claude/skills/vicaya-3-complete`
  - Use those commands only for roots where `vicaya` itself is a sibling symlink
    to `/Users/deva/Documents/dps/vicaya/skill/vicaya`, and only when the staged
    sibling is missing.
  - If a staged symlink exists but points anywhere else, replace only that
    staged symlink with the correct sibling symlink. Do not replace real
    directories or non-symlink files without explicit user approval.
  - If an expected root exists but does not contain `vicaya`, do not create
    staged registrations there; record that the monolithic skill is not
    distributed through that root.
  - If the active loader uses the project `skill/<stage>` directories directly
    and no external registration exists, record that fact.
  - -> verify: for every active root containing `vicaya`, `readlink` for each
    staged sibling returns the matching project `skill/<stage>` directory.

- [x] Verify no Python changes were made.
  - -> verify: `git diff --name-only -- '*.py'` shows no Python files changed by this thread. If Python files are already dirty from unrelated work, inspect `git diff --name-only -- skill kamma` instead and confirm this thread touched only docs/skill Markdown.

- [x] Run whitespace/diff checks for touched docs.
  - -> verify: `git diff --check -- skill/vicaya-0-scope/SKILL.md skill/vicaya-1-gather/SKILL.md skill/vicaya-2-synthesize-review/SKILL.md skill/vicaya-3-complete/SKILL.md skill/vicaya/README.md kamma/project.md` passes.

## Phase 9 - Review gate

- [x] Run fresh `/kamma:3-review` for this thread.
  - Reviewer must check exact source-section routing, not keyword presence.
  - Reviewer must confirm the failed attempt was removed by explicit
    deletion/overwrite in this thread, not by broad `git reset`, `git checkout
    --`, or `git revert`.
  - Reviewer must compare every staged routing list against
    `skill/vicaya/SKILL.md`.
  - Reviewer must confirm routed headings are real non-fenced canonical
    headings, not headings inside examples or note templates.
  - Reviewer must specifically confirm the Phase 7 note template and
    self-improvement reflection template fenced headings are not treated as
    route anchors.
  - Reviewer must verify the staged files contain no behavioral paraphrases.
  - Reviewer must verify the staged files contain no copied command syntax,
    phase gate lists, helper behavior, or publishing behavior.
  - Reviewer must verify every non-frontmatter staged-skill line is router or
    stage-local glue only.
  - Reviewer must verify every staged skill contains the out-of-scope handoff
    guard and does not authorize running phases outside owned scope.
  - Reviewer must verify each staged `SKILL.md` matches the routed section-router
    design from Phases 3-6 except for the bounded context-budget controls
    explicitly added in Phases 9.5, 9.6, 9.7, 9.8, 9.9, and 9.10.
  - Reviewer must verify this thread changed `skill/vicaya/SKILL.md` only in the
    staged-mode pointer near the top and contains no behavioral edits. If the
    file was already dirty, reviewer must confirm non-pointer hunks match the
    recorded pre-edit diff.
  - Reviewer must verify `skill/vicaya/README.md` contains no behavioral
    workflow paraphrase beyond the bounded context-budget controls, and no
    command, phase, helper, dependency, output, source layout, or staged handoff
    summaries. It may describe only the difference between monolithic and staged
    modes, registration parity, and bounded context-budget controls.
  - Reviewer must verify the previous summarized shared references are gone and
    no replacement shared routing/reference file was created.
  - Reviewer must verify `skill/vicaya/shared/` is absent, not merely empty.
  - Reviewer must verify durable docs contain no generic shared-reference
    language, not only no references to the five deleted shared files.
  - Reviewer must verify every active skill root that registers the monolithic
    `vicaya` skill also registers the four staged skills beside it, using the
    same link style and pointing to the rebuilt staged directories.
  - -> verify: `kamma/threads/20260602_vicaya-staged-skills-section-router/review.md` exists and verdict is `PASSED`.

## Phase 9.5 - User revision: Stage 0 context-budget plan

- [x] Add a bounded Stage 0 context plan for extensive staged research.
  - The user clarified that this belongs in `vicaya-0-scope`, not in the
    canonical `vicaya` skill, because the monolithic skill is expected to run
    under a model/context profile where this split is unnecessary.
  - Update the spec to allow the first exception to the pure-router rule:
    `skill/vicaya-0-scope/SKILL.md` may record context breaks when Phase 0
    scoping indicates extensive research.
  - Do not edit `skill/vicaya/SKILL.md`.
  - Do not edit `skill/vicaya-1-gather/SKILL.md` for this context plan; Stage 0
    should tell the user what split to request when Stage 1 is extensive.
  - Update `skill/vicaya/README.md` and `kamma/project.md` only enough to stop
    describing `vicaya-0-scope` as a pure router.
  - The context plan must not change canonical phase gates, helper behavior,
    evidence requirements, or scratch format.
  - The context plan may tell Stage 0 to use the routed canonical scratch
    logging mechanism for a Phase 0 note when a split is recorded.
  - -> verify: `rg -n "Stage Context Plan|context-budget|stage-1-context-plan|stage-2-context-plan|pure router|bounded.*context" skill/vicaya-0-scope/SKILL.md skill/vicaya/README.md kamma/project.md kamma/threads/20260602_vicaya-staged-skills-section-router/spec.md kamma/threads/20260602_vicaya-staged-skills-section-router/plan.md` shows the allowed context plan and matching documentation updates.
  - -> verify: `git diff --check -- skill/vicaya-0-scope/SKILL.md skill/vicaya/README.md kamma/project.md kamma/threads/20260602_vicaya-staged-skills-section-router/spec.md kamma/threads/20260602_vicaya-staged-skills-section-router/plan.md` passes.

Note: the stale Phase 9 review was deleted because it predated Phases 9.5-9.10.
Do not finalize the thread until a fresh review explicitly covers the bounded
binding context-plan and context-break guard exceptions.

## Phase 9.6 - User revision: context breaks inside heavy stages

- [x] Add scratch-backed context-break guards for Stage 1 and Stage 2.
  - The user clarified that long research affects the heavy stages themselves:
    Stage 1 should naturally break around source-gathering groups, and Stage 2
    may also need a restart between synthesis/review work.
  - Update `skill/vicaya-0-scope/SKILL.md` so Phase 0 can recommend a whole-run
    context plan for Stage 1 and Stage 2, not only Stage 1.
  - Update `skill/vicaya-1-gather/SKILL.md` with a bounded context-break guard
    that honors the Phase 0 context plan from scratch and stops after planned gather
    boundaries.
  - Update `skill/vicaya-2-synthesize-review/SKILL.md` with a bounded
    context-break guard that honors the Phase 0 context plan from scratch and can
    split Phase 5/Phase 6 work when the dossier is large.
  - Do not edit `skill/vicaya/SKILL.md`.
  - Do not create workflow state outside the canonical scratch system.
  - Do not change canonical phase gates, helper behavior, evidence
    requirements, source requirements, or synthesis/review requirements.
  - Update `skill/vicaya/README.md`, `kamma/project.md`, and this thread spec
    only enough to describe the bounded context-break exceptions.
  - -> verify: `rg -n "Context Break Guard|Stage Context Advisory|stage-1-context-plan|stage-2-context-plan|context-break" skill/vicaya-0-scope/SKILL.md skill/vicaya-1-gather/SKILL.md skill/vicaya-2-synthesize-review/SKILL.md skill/vicaya/README.md kamma/project.md kamma/threads/20260602_vicaya-staged-skills-section-router/spec.md kamma/threads/20260602_vicaya-staged-skills-section-router/plan.md` shows only the bounded context-management additions.
  - -> verify: superseded by Phase 9.7; `vicaya-3-complete` now intentionally
    has a bounded context-break guard.
  - -> verify: `git diff --check -- skill/vicaya/README.md kamma/project.md kamma/threads/20260602_vicaya-staged-skills-section-router/spec.md kamma/threads/20260602_vicaya-staged-skills-section-router/plan.md` passes, and direct trailing-whitespace checks pass for the untracked staged skill files.

## Phase 9.7 - User revision: context breaks inside Stage 3

- [x] Add scratch-backed context-break guards for Stage 3 completion.
  - The user clarified that `vicaya-3-complete` can also run long enough to
    need context refreshes.
  - Update `skill/vicaya-0-scope/SKILL.md` so Phase 0 can recommend a
    `stage-3-context-plan` for extensive completion work.
  - Update `skill/vicaya-3-complete/SKILL.md` with a bounded context-break
    guard that honors the Phase 0 context plan from scratch and stops only at safe
    completion boundaries.
  - Safe Stage 3 boundaries are: before vault write after recording a complete
    rendered note in scratch; after vault write/validation/PDF/Phase 7 gate/run
    report sync before final report if context pressure requires it.
  - Never write a partial or draft note to the vault.
  - Do not edit `skill/vicaya/SKILL.md`.
  - Do not create workflow state outside the canonical scratch system.
  - Do not change canonical Phase 7, final-report, validation, PDF, scratch
    gate, run-report sync, or self-improvement requirements.
  - Update `skill/vicaya/README.md`, `kamma/project.md`, and this thread spec
    only enough to describe the bounded Stage 3 context-break exception.
  - -> verify: `rg -n "stage-3-context-plan|Stage 3|Context Break Guard|partial or draft note" skill/vicaya-0-scope/SKILL.md skill/vicaya-3-complete/SKILL.md skill/vicaya/README.md kamma/project.md kamma/threads/20260602_vicaya-staged-skills-section-router/spec.md kamma/threads/20260602_vicaya-staged-skills-section-router/plan.md` shows the allowed Stage 3 context-management additions.
  - -> verify: `git diff --check -- skill/vicaya/README.md kamma/project.md kamma/threads/20260602_vicaya-staged-skills-section-router/spec.md kamma/threads/20260602_vicaya-staged-skills-section-router/plan.md` passes, and direct trailing-whitespace checks pass for the untracked staged skill files.

## Phase 9.8 - User revision: make extensive-run context plans binding

- [x] Replace advisory context-break wording with binding hard-stop wording.
  - The user clarified that the advanced Stage 0 model should decide whether
    research is extensive, and executing staged models must follow that decision
    rather than re-evaluate whether the pass split is optional.
  - Update `skill/vicaya-0-scope/SKILL.md` so recorded context plans are binding
    instructions for later staged skills and override model-tier recommendations.
  - Update `skill/vicaya-1-gather/SKILL.md`,
    `skill/vicaya-2-synthesize-review/SKILL.md`, and
    `skill/vicaya-3-complete/SKILL.md` so an existing `stage-N-context-plan`
    requires running only the next planned pass and then hard-stopping at the
    planned boundary.
  - Do not edit `skill/vicaya/SKILL.md`.
  - Do not create workflow state outside the canonical scratch system.
  - Do not change canonical phase gates, helper behavior, evidence
    requirements, source requirements, synthesis/review requirements, Phase 7
    requirements, final-report requirements, validation, PDF, run-report sync,
    or self-improvement requirements.
  - -> verify: `rg -n "advisory|suggestion is advisory|recommend this split|may stop|because context seems comfortable|binding|hard stop|overrides any model-tier recommendation" skill/vicaya-0-scope/SKILL.md skill/vicaya-1-gather/SKILL.md skill/vicaya-2-synthesize-review/SKILL.md skill/vicaya-3-complete/SKILL.md skill/vicaya/README.md kamma/project.md kamma/threads/20260602_vicaya-staged-skills-section-router/spec.md kamma/threads/20260602_vicaya-staged-skills-section-router/plan.md` shows no remaining soft execution wording in active staged instructions and shows the binding hard-stop language.
  - -> verify: `git diff --check -- skill/vicaya/README.md kamma/project.md kamma/threads/20260602_vicaya-staged-skills-section-router/spec.md kamma/threads/20260602_vicaya-staged-skills-section-router/plan.md` passes, and direct trailing-whitespace checks pass for the untracked staged skill files.

## Phase 9.9 - User revision: make Stage 1 gather stops more granular

- [x] Split extensive Stage 1 gathering into source-block hard stops.
  - The user reported that after a manual context wrap before the first planned
    hard stop, the resumed Stage 1 run continued into library search instead of
    hard-stopping again. The current broad Pass A/B/C split can be interpreted
    as already satisfied once Phase 2 is gated, so the next invocation may run a
    large remaining gather span.
  - Update `skill/vicaya-0-scope/SKILL.md` so the default extensive Stage 1
    context plan separates vault/context setup, root-canon sutta research,
    canonical exegesis/commentary research, library research, web research,
    YouTube research, and WisdomLib research into distinct hard-stop blocks.
  - Update `skill/vicaya-1-gather/SKILL.md` so a recorded
    `stage-1-context-plan` means every invocation runs exactly one next source
    block, then hard-stops. A prior hard stop must not be treated as satisfying
    the whole Stage 1 plan.
  - Allow a Stage 1 hard stop inside Phase 2 after root-canon mūla/sutta
    research when commentary/ṭīkā research is still required. This must be a
    scratch-logged in-progress handoff, not a Phase 2 gate; Phase 2 may be
    gated only after all canonical Phase 2 obligations are complete.
  - Update the live scratch run
    `data/scratch/moha-amoha-avijja-vijja.md` with a superseding context-plan
    note so the current research does not keep following the older broad
    Pass A/B/C split.
  - Do not edit `skill/vicaya/SKILL.md`.
  - Do not create workflow state outside the canonical scratch system.
  - Do not change canonical phase gates, helper behavior, evidence
    requirements, source requirements, synthesis/review requirements, Phase 7
    requirements, final-report requirements, validation, PDF, run-report sync,
    or self-improvement requirements.
  - -> verify: `rg -n "source-block|root-canon|commentary|Every invocation|prior hard stop|Phase 2 gate|stage-1-context-plan" skill/vicaya-0-scope/SKILL.md skill/vicaya-1-gather/SKILL.md kamma/threads/20260602_vicaya-staged-skills-section-router/spec.md kamma/threads/20260602_vicaya-staged-skills-section-router/plan.md data/scratch/moha-amoha-avijja-vijja.md` shows the granular Stage 1 hard-stop behavior.
  - -> verify: `git diff --check -- skill/vicaya-0-scope/SKILL.md skill/vicaya-1-gather/SKILL.md kamma/threads/20260602_vicaya-staged-skills-section-router/spec.md kamma/threads/20260602_vicaya-staged-skills-section-router/plan.md kamma/threads/20260602_vicaya-staged-skills-section-router/handoff.md data/scratch/moha-amoha-avijja-vijja.md` passes, and direct trailing-whitespace checks pass for the untracked staged skill files.

## Phase 9.10 - User revision: Stage 3 progressive draft file

- [x] Replace one-pass Stage 3 rendering with a scratch-local draft-file workflow.
  - The user reported that `vicaya-3-complete` tried to write the complete
    final note to a temp file and log it to scratch, but even that render step
    can exceed context on the current `moha-amoha-avijja-vijja` run.
  - Update `skill/vicaya-3-complete/SKILL.md` so a Stage 3 context plan uses a
    durable draft file under `data/scratch/`, written section by section, while
    the main scratch stores only the draft path, section status, and concise
    handoff notes.
  - Update `skill/vicaya-0-scope/SKILL.md` so future extensive Stage 3 context
    plans record the progressive draft-file method instead of "render complete
    final note into scratch".
  - Update the live scratch run
    `data/scratch/moha-amoha-avijja-vijja.md` with a superseding Stage 3 note
    that names the intended draft file:
    `data/scratch/moha-amoha-avijja-vijja.phase7-draft.md`.
  - The draft file is a scratch-local Phase 7 artifact, not the vault note. It
    may contain incomplete section drafts, but the vault must receive only the
    complete audited note.
  - Do not edit `skill/vicaya/SKILL.md`.
  - Do not change canonical Phase 7, final-report, validation, PDF, scratch
    gate, run-report sync, or self-improvement requirements.
  - Do not write a partial or draft note to the vault.
  - -> verify: `rg -n "phase7-draft|draft file|section by section|section status|complete audited note|vault must receive only" skill/vicaya-0-scope/SKILL.md skill/vicaya-3-complete/SKILL.md kamma/threads/20260602_vicaya-staged-skills-section-router/spec.md kamma/threads/20260602_vicaya-staged-skills-section-router/plan.md data/scratch/moha-amoha-avijja-vijja.md` shows the Stage 3 draft-file workflow and the current-run override.
  - -> verify: `git diff --check -- skill/vicaya-0-scope/SKILL.md skill/vicaya-3-complete/SKILL.md kamma/threads/20260602_vicaya-staged-skills-section-router/spec.md kamma/threads/20260602_vicaya-staged-skills-section-router/plan.md kamma/threads/20260602_vicaya-staged-skills-section-router/handoff.md data/scratch/moha-amoha-avijja-vijja.md` passes, and direct trailing-whitespace checks pass for the untracked staged skill files.

## Phase 9.11 - User revision: restored README with staged references

- [x] Add concise staged-skill references without rewriting restored README content.
  - The user restored README content after an overbroad rewrite and requested
    only a few references to the staged subskills wherever the main `vicaya`
    skill is mentioned.
  - Preserve existing main-skill descriptions unless they are no longer
    relevant.
  - Add staged-router references beside the existing monolithic skill references
    in README/setup/source-layout text.
  - Add a durable maintenance note to `kamma/project.md` and `kamma/tech.md`:
    edits to `skill/vicaya/SKILL.md` must check the staged sibling skills, and
    edits to staged sibling skills must verify they still route to the
    canonical skill without silently forking behavior.
  - Do not add phase summaries, helper behavior, command syntax beyond
    registration references, or staged handoff workflow prose.
  - -> verify: `rg -n "vicaya-0-scope|vicaya-1-gather|vicaya-2-synthesize-review|vicaya-3-complete" README.md skill/vicaya/README.md kamma/project.md kamma/tech.md` shows concise staged references.
  - -> verify: `git diff --check -- README.md skill/vicaya/README.md kamma/project.md kamma/tech.md kamma/threads/20260602_vicaya-staged-skills-section-router/plan.md kamma/threads/20260602_vicaya-staged-skills-section-router/spec.md` passes.

## Phase 9.12 - User revision: Stage 3 mandatory three-run split

- [x] Tighten extensive Stage 3 completion from adaptive draft-file stopping to
  a mandatory three-run split.
  - The user completed a live `vicaya-3-complete` run where the current
    "continue while context remains healthy" wording produced a valid hard stop
    before vault write, but only after reaching roughly 95-98% context.
  - Update `skill/vicaya-3-complete/SKILL.md` so an extensive Stage 3 context
    plan performs only the next mandatory pass, then hard stops even if context
    seems comfortable:
    1. writer brief plus `## Question` and `## Findings`;
    2. remaining evidence/support sections plus frontmatter canon-ref
       confirmation and completion audit, stopping before vault write;
    3. vault write, validation, PDF, Phase 7 gate, note/run-report sync, final
       user report, and self-improvement loop.
  - Update `skill/vicaya-0-scope/SKILL.md` so future Phase 0 context plans
    record that same three-run Stage 3 split.
  - Update this thread `spec.md` to document the live-test finding and the
    tightened Stage 3 default.
  - Do not edit `skill/vicaya/SKILL.md`; the monolithic skill's Phase 5
    deferred-draft self-improvement hunk was intentionally reverted because the
    staged skills already own that protection.
  - Do not change canonical Phase 7, final-report, validation, PDF, scratch
    gate, run-report sync, or self-improvement requirements.
  - Do not write a partial or draft note to the vault.
  - -> verify: `rg -n "mandatory three-run|Run 1|Run 2|Run 3|context seems comfortable" skill/vicaya-0-scope/SKILL.md skill/vicaya-3-complete/SKILL.md kamma/threads/20260602_vicaya-staged-skills-section-router/spec.md kamma/threads/20260602_vicaya-staged-skills-section-router/plan.md` shows the three-run Stage 3 split and no adaptive Stage 3 continuation wording.
  - -> verify: `git diff --check -- skill/vicaya-0-scope/SKILL.md skill/vicaya-3-complete/SKILL.md kamma/threads/20260602_vicaya-staged-skills-section-router/spec.md kamma/threads/20260602_vicaya-staged-skills-section-router/plan.md` passes.

## Phase 9.13 - User revision: Stage 1 four-bundle cost control

- [x] Unite extensive Stage 1 source-block hard stops into four cost-controlled
  bundles.
  - The user clarified that the reason for staged mode is research cost control,
    and the previous nine-block Stage 1 split created too many separate
    sessions.
  - Update `skill/vicaya-0-scope/SKILL.md` and
    `skill/vicaya-1-gather/SKILL.md` so the default extensive Stage 1 context
    plan uses these bundled invocations:
    1. Phase 1 vault/EBC context, angle triage, and perspective map plus Phase
       2 root-canon mūla/sutta research;
    2. Phase 2 commentary/exegesis plus Phase 2.5 SuttaCentral/offline
       parallels when applicable;
    3. Phase 3 library plus Phase 3b Sanskrit sources when applicable;
    4. Phase 4a web, Phase 4b YouTube when applicable, and Phase 4c WisdomLib.
  - Preserve the Phase 2 in-progress checkpoint rule: the first bundle may stop
    after root-canon mūla/sutta research when commentary/ṭīkā work remains, and
    Phase 2 may be gated only after all canonical Phase 2 obligations are
    complete.
  - Do not edit `skill/vicaya/SKILL.md`.
  - Do not change canonical phase gates, helper behavior, evidence
    requirements, source requirements, synthesis/review requirements, Phase 7
    requirements, final-report requirements, validation, PDF, run-report sync,
    or self-improvement requirements.
  - Existing scratch files with older Stage 1 notes do not need broad rewriting;
    patch only an in-progress scratch if the older note would force an
    unnecessary extra resume boundary before the next grouped block can
    complete.
  - Patched `data/scratch/vicikiccha-hindrance-vs-fetter.md` with a
    `stage-1-four-bundle-phase-9.13-supersedes` note because its old Phase 4
    wording would otherwise split Phase 4a, Phase 4b, and Phase 4c into
    separate future resumes.
  - -> verify: `rg -n "grouped|four|Phase 1 vault/EBC context.*root-canon|commentary.*Phase 2.5|Phase 3 library.*Phase 3b|Phase 4a web.*Phase 4b.*Phase 4c" skill/vicaya-0-scope/SKILL.md skill/vicaya-1-gather/SKILL.md kamma/threads/20260602_vicaya-staged-skills-section-router/spec.md kamma/threads/20260602_vicaya-staged-skills-section-router/plan.md` shows the four-bundle Stage 1 split.
  - -> verify: `rg -n "stage-1-four-bundle-phase-9.13-supersedes|Phase 4a web plus Phase 4b YouTube.*Phase 4c WisdomLib" data/scratch/vicikiccha-hindrance-vs-fetter.md` shows the targeted scratch supersession.
  - -> verify: `git diff --check -- skill/vicaya-0-scope/SKILL.md skill/vicaya-1-gather/SKILL.md kamma/threads/20260602_vicaya-staged-skills-section-router/spec.md kamma/threads/20260602_vicaya-staged-skills-section-router/plan.md kamma/threads/20260602_vicaya-staged-skills-section-router/handoff.md data/scratch/vicikiccha-hindrance-vs-fetter.md` passes.

## Phase 9.14 - User revision: fixed `1 + 4 + 2 + 3` hard-stop redistribution

- [x] Rebalance staged hard stops without adding new research logic.
  - The user clarified the current goal: cost efficiency and never hitting the
    200k context limit. The model cannot reliably sense current context usage,
    so adaptive wording such as "context seems comfortable", "context pressure
    is high", or "dossier is manageable" must not be used as the control
    mechanism. Only predetermined hard stops work.
  - Golden rule: do not introduce any new research logic. `skill/vicaya/SKILL.md`
    remains the source of the actual workflow, quality standard, evidence
    rules, gates, helper behavior, final-note requirements, and
    self-improvement loop. This thread only redistributes the same canonical
    work across fixed fresh-context sessions.
  - Update `skill/vicaya-0-scope/SKILL.md` and
    `skill/vicaya-1-gather/SKILL.md` so extensive Stage 1 keeps four default
    invocations but rebalances the risky 195k Phase 2-2.5 pass:
    1. Phase 1 vault/EBC context, angle triage, and perspective map plus Phase
       2 root-canon mūla/sutta research;
    2. Phase 2 commentary/exegesis only;
    3. Phase 2.5 plus Phase 3 plus Phase 3b when applicable;
    4. Phase 4a plus Phase 4b plus Phase 4c.
  - Update `skill/vicaya-0-scope/SKILL.md` and
    `skill/vicaya-2-synthesize-review/SKILL.md` so extensive Stage 2 keeps two
    default invocations but rebalances heavy Phase 5 into lighter Phase 6:
    1. canonical Phase 5 entry/verification, source and angle checks, Devil's
       Advocate answers, bibliography/source allocation review, and a
       concise scratch-logged Phase 5 drafting plan; hard stop before full
       drafting;
    2. complete Phase 5 drafting/integration and Phase 5 gate, then run Phase
       6 second-pass review and Phase 6 gate.
  - Update `skill/vicaya-0-scope/SKILL.md` and
    `skill/vicaya-3-complete/SKILL.md` so extensive Stage 3 keeps three
    default invocations but moves heavy early evidence drafting from Run 2 into
    underused Run 1:
    1. writer brief, draft setup, title/slug/outline/source
       allocation/frontmatter targets, `## Question`, `## Findings`, Canon
       Evidence, and Commentary Evidence;
    2. remaining evidence/support sections, bibliography, footnotes,
       frontmatter `canon_refs` confirmation, and completion audit;
    3. vault write, validation, PDF, Phase 7 gate, note/run-report sync, final
       report, and self-improvement loop.
  - Update this thread `spec.md` and `handoff.md` to document the approved
    `1 + 4 + 2 + 3` split and the no-new-logic rule.
  - Update Phase 10 review/finalize criteria to include Phase 9.14.
  - Do not edit `skill/vicaya/SKILL.md`.
  - Do not change canonical phase gates, helper behavior, evidence
    requirements, source requirements, synthesis/review requirements, Phase 7
    requirements, final-report requirements, validation, PDF, run-report sync,
    or self-improvement requirements.
  - -> verify: `rg -n "because context seems|context seems comfortable|context pressure becomes high|dossier is manageable|very large dossiers|completion work is manageable|Devil's Advocate preparation|claim map|claim-map|partial draft structure" skill/vicaya-0-scope/SKILL.md skill/vicaya-1-gather/SKILL.md skill/vicaya-2-synthesize-review/SKILL.md skill/vicaya-3-complete/SKILL.md` returns no active staged-skill hits.
  - -> verify: warning or historical prose in `spec.md`, `plan.md`, and `handoff.md` may mention disallowed adaptive phrases only to say they must not be used, or to preserve earlier superseded phase history.
  - -> verify: `rg -n "1 \\+ 4 \\+ 2 \\+ 3|Phase 2 commentary/exegesis only|Phase 2\\.5.*Phase 3|Phase 5 drafting plan|Canon Evidence.*Commentary Evidence|Golden rule" skill/vicaya-0-scope/SKILL.md skill/vicaya-1-gather/SKILL.md skill/vicaya-2-synthesize-review/SKILL.md skill/vicaya-3-complete/SKILL.md kamma/threads/20260602_vicaya-staged-skills-section-router/spec.md kamma/threads/20260602_vicaya-staged-skills-section-router/plan.md kamma/threads/20260602_vicaya-staged-skills-section-router/handoff.md` shows the approved fixed redistribution.
  - -> verify: `git diff --check -- skill/vicaya-0-scope/SKILL.md skill/vicaya-1-gather/SKILL.md skill/vicaya-2-synthesize-review/SKILL.md skill/vicaya-3-complete/SKILL.md kamma/threads/20260602_vicaya-staged-skills-section-router/spec.md kamma/threads/20260602_vicaya-staged-skills-section-router/plan.md kamma/threads/20260602_vicaya-staged-skills-section-router/handoff.md` passes.

## Phase 9.15 - User revision: sync current unfinished research scratches

- [x] Check the current handoff against the latest Phase 9.14 staged split and
  the current unfinished research runs named by the user.
  - `papanca-canon-usage` had already stopped after the Phase 5 gate under the
    older Stage 2 split. Patch its scratch with a
    `stage-2-context-plan phase-9.14-supersedes` note: because Phase 5 is
    already gated, the next `vicaya-2-synthesize-review` invocation should run
    canonical Phase 6 cross-check and the Phase 6 gate, then hand off to
    `vicaya-3-complete`; future extensive Stage 2 runs use the fixed Phase
    9.14 two-pass split.
  - Patch `papanca-canon-usage` with a
    `stage-3-context-plan phase-9.14-supersedes` note so completion uses the
    rebalanced three-run draft/vault-write split whose Run 1 includes Canon
    Evidence and Commentary Evidence.
  - `vicikiccha-hindrance-vs-fetter` had Phase 3 gated but older Stage 1,
    Stage 2, and Stage 3 context-plan wording. Patch it with Phase 9.14
    superseding context-plan notes for Stage 1, Stage 2, and Stage 3.
  - Update `handoff.md` so it no longer says the stale review was deleted or
    that the next step is necessarily the older fresh review. Record that
    `review.md` currently exists with verdict `PASSED`, and that this
    post-review scratch/handoff sync should be considered before finalization.
  - Do not edit `skill/vicaya/SKILL.md`.
  - Do not change staged skill behavior.
  - Do not continue either research run.
  - -> verify: `rg -n "phase-9.14-supersedes|PHASE .* EXIT GATE" data/scratch/papanca-canon-usage.md data/scratch/vicikiccha-hindrance-vs-fetter.md` shows the new scratch supersession notes and existing gate state.
  - -> verify: `rg -n "Run a fresh /kamma:3-review|stale .*review.*deleted|Phase 9.12 three-run|Phase 9.13 note" kamma/threads/20260602_vicaya-staged-skills-section-router/handoff.md` returns no stale active restart instructions.
  - -> verify: `git diff --check -- kamma/threads/20260602_vicaya-staged-skills-section-router/plan.md kamma/threads/20260602_vicaya-staged-skills-section-router/handoff.md` passes.

## Phase 9.16 - User revision: durable Stage 2 draft and review artifacts

- [x] Audit staged skills for handoff-critical artifacts that could be left in
  a global/system temporary directory, repo-local `temp/`, or another
  non-scratch path.
  - User report: a Phase 5 draft was saved to a global temporary file, the
    machine/session later cleared that file, and the durable scratch still
    showed only the last completed gate. This exposed that immediate
    same-session continuation had hidden a durability problem.
  - Active risk found: Stage 2 allowed a Phase 5 drafting-plan hard stop without
    explicitly naming a durable file for any draft payload written before the
    Phase 5 gate.
  - Lower-risk disposable-temp case found: canonical Phase 6 used a global
    temporary directory for the cross-check prompt/output. Phase 9.17
    supersedes this and moves prompt/output files into scratch-local paths.
  - Update `skill/vicaya-0-scope/SKILL.md` and
    `skill/vicaya-2-synthesize-review/SKILL.md` so any Phase 5 draft payload
    written before the Phase 5 gate must be saved under `data/scratch/`,
    normally `data/scratch/<scratch-slug>.phase5-draft.md`, and the path must be
    logged in the main scratch.
  - Update Stage 2 wording so Phase 5 draft content, Phase 6 raw review output,
    and handoff-critical synthesis payloads must not be left only in a
    global/system temporary directory, repo-local `temp/`, or any other
    non-scratch path.
  - Update this thread `spec.md` and `handoff.md` to document the allowed
    scratch-local Phase 5 draft artifact and the non-scratch-path prohibition.
  - Patch active ignored scratch
    `data/scratch/vicikiccha-hindrance-vs-fetter.md` with a
    `stage-2-durable-artifact-phase-9.16` note because `.active` currently
    points to that run at Phase 5 and it still contained the older Phase 9.14
    Stage 2 artifact-location wording.
  - Do not edit `skill/vicaya/SKILL.md`.
  - Do not change canonical phase gates, helper behavior, evidence
    requirements, source requirements, synthesis/review requirements, Phase 7
    requirements, final-report requirements, validation, PDF, run-report sync,
    or self-improvement requirements.
  - -> verify: `rg -n "phase5-draft|handoff-critical synthesis payloads|Phase 6 raw review output|global/system temporary|repo-local .*temp" skill/vicaya-0-scope/SKILL.md skill/vicaya-2-synthesize-review/SKILL.md kamma/threads/20260602_vicaya-staged-skills-section-router/spec.md kamma/threads/20260602_vicaya-staged-skills-section-router/handoff.md` shows the durable Stage 2 artifact guard.
  - -> verify: `rg -n "global/system temporary|repo-local .*temp|phase5-draft|phase7-draft|draft payload|raw review output|handoff-critical" skill/vicaya-0-scope/SKILL.md skill/vicaya-1-gather/SKILL.md skill/vicaya-2-synthesize-review/SKILL.md skill/vicaya-3-complete/SKILL.md` shows no remaining active staged-skill instruction that leaves handoff-critical work outside `data/scratch/`.
  - -> verify: `rg -n "stage-2-durable-artifact-phase-9.16|phase5-draft|handoff-critical synthesis payloads" data/scratch/vicikiccha-hindrance-vs-fetter.md` shows the current-run supersession note.
  - -> verify: `git diff --check -- skill/vicaya-0-scope/SKILL.md skill/vicaya-2-synthesize-review/SKILL.md kamma/threads/20260602_vicaya-staged-skills-section-router/spec.md kamma/threads/20260602_vicaya-staged-skills-section-router/plan.md kamma/threads/20260602_vicaya-staged-skills-section-router/handoff.md` passes.

## Phase 9.17 - User revision: no global temporary directories in any stage

- [x] Remove global temporary directory usage from all active Vicaya stage
  instructions and add final per-run temp cleanup.
  - User direction: because interruption can happen at any time and continuation
    may happen much later, no stage should ever use global temporary
    directories. Since repo-local temp is allowed only for disposable files,
    final completion must clean this research run's temp files after the needed
    work is done.
  - Update `skill/vicaya/SKILL.md` so:
    - the hard rules include a no-global-temporary-directory rule;
    - Calibre extraction examples use per-run repo-local `temp/<scratch-slug>/`;
    - Phase 6 cross-check prompt/output files use scratch-local files next to
      the current scratch;
    - Phase 6 explicitly logs raw review output in scratch before any hard stop;
    - PDF fallback extraction uses per-run repo-local `temp/<scratch-slug>/`;
    - Phase 7 final cleanup removes only this run's repo-local temp directory
      and never removes `data/scratch/`.
  - Update staged wrappers so final `vicaya-3-complete` cleanup is part of Run
    3, and Stage 2 forbids leaving handoff-critical payloads in any
    global/system temporary directory.
  - Add a superseding note to the active ignored scratch
    `data/scratch/vicikiccha-hindrance-vs-fetter.md` so the current Phase 5
    resume follows the no-global-temporary-directory and final-cleanup rule.
  - Do not change canonical research obligations, evidence requirements,
    phase gates, helper semantics, Phase 7 note requirements, validation, PDF,
    sync, final report, or self-improvement logic.
  - -> verify: a fixed-string scan for global temp path literals across `skill/vicaya/SKILL.md`, `skill/vicaya-*/SKILL.md`, and this thread's `spec.md`/`plan.md`/`handoff.md` returns no active workflow hits.
  - -> verify: `rg -n "cross-check-prompt|cross-check-review|phase5-draft|phase7-draft|repo-local .*temp|No global temporary|clean only this run" skill/vicaya/SKILL.md skill/vicaya-*/SKILL.md` shows scratch-local, repo-local, and cleanup replacements.
  - -> verify: `git diff --check -- skill/vicaya/SKILL.md skill/vicaya-0-scope/SKILL.md skill/vicaya-2-synthesize-review/SKILL.md skill/vicaya-3-complete/SKILL.md kamma/threads/20260602_vicaya-staged-skills-section-router/spec.md kamma/threads/20260602_vicaya-staged-skills-section-router/plan.md kamma/threads/20260602_vicaya-staged-skills-section-router/handoff.md` passes.

## Phase 9.18 - User revision: compact-tolerant default and risk-triggered hard stops

- [x] Make the fixed hard-stop split a risk-triggered safety mode, not the
  default for every extensive run.
  - User clarified the current goal: research logic in `skill/vicaya/SKILL.md`
    is working and must remain unchanged. This thread is only about dividing
    that existing research pattern into staged skills, reducing unnecessary
    cost, and ensuring nothing is lost across compaction or handoff.
  - Default staged execution should be compact-tolerant four-stage flow:
    `vicaya-0-scope` -> `vicaya-1-gather` ->
    `vicaya-2-synthesize-review` -> `vicaya-3-complete`.
  - Normal context compaction is acceptable in the default flow because the
    routed canonical scratch/resume mechanism preserves durable run state.
  - Update `skill/vicaya-0-scope/SKILL.md` so Stage 0 records
    `stage-1-context-plan`, `stage-2-context-plan`, and `stage-3-context-plan`
    only when Phase 0 identifies objective context risk: multiple Pali terms or
    doctrinal frames needing separate searches; required canon/commentary/ṭīkā/
    Abhidhamma/Visuddhimagga/DPD comparison; several investigation angles that
    each require real source work; an explicitly source-exhaustive or
    comprehensive request; an expected final note with many large evidence
    sections; or prior similar live-run token evidence near or above the
    context limit.
  - Keep existing Stage 1, Stage 2, and Stage 3 hard-stop guards binding when a
    recorded context plan exists.
  - Strengthen durable checkpoint rules where auto-compaction can still lose
    work:
    - Stage 1 must record useful findings, citations, source status, and skip
      rationale in scratch before moving between major source classes.
    - Stage 2 must save Phase 5 draft payloads and Phase 6 raw review or
      handoff-critical synthesis payloads in scratch-local files or the main
      scratch whether or not a hard-stop plan exists.
    - Stage 3 must assemble note drafts in a scratch-local Phase 7 draft file
      whether or not a hard-stop plan exists; the vault still receives only the
      complete audited note.
  - Do not edit `skill/vicaya/SKILL.md`.
  - Do not change canonical phase gates, helper behavior, evidence
    requirements, source requirements, synthesis/review requirements, Phase 7
    requirements, validation, PDF, sync, final report, or self-improvement
    logic.
  - Update this thread `spec.md` and `handoff.md` to document default
    compact-tolerant flow, risk-triggered hard-stop safety mode, and durable
    checkpointing.
  - Update Phase 10 review/finalize criteria to include Phase 9.18.
  - -> verify: `rg -n "compact-tolerant|objective context risk|hard-stop safety mode|normal context compaction|stage-1-context-plan|phase5-draft|phase7-draft" skill/vicaya-0-scope/SKILL.md skill/vicaya-1-gather/SKILL.md skill/vicaya-2-synthesize-review/SKILL.md skill/vicaya-3-complete/SKILL.md kamma/threads/20260602_vicaya-staged-skills-section-router/spec.md kamma/threads/20260602_vicaya-staged-skills-section-router/plan.md kamma/threads/20260602_vicaya-staged-skills-section-router/handoff.md` shows the updated policy.
  - -> verify: `git diff -- skill/vicaya/SKILL.md` returns no diff.
  - -> verify: `git diff --check -- skill/vicaya-0-scope/SKILL.md skill/vicaya-1-gather/SKILL.md skill/vicaya-2-synthesize-review/SKILL.md skill/vicaya-3-complete/SKILL.md kamma/threads/20260602_vicaya-staged-skills-section-router/spec.md kamma/threads/20260602_vicaya-staged-skills-section-router/plan.md kamma/threads/20260602_vicaya-staged-skills-section-router/handoff.md` passes.

## Phase 10 - Finalize only after clean review

- [ ] Run `/kamma:4-finalize` only after review passes.
  - `review.md` currently exists with verdict `PASSED`, but Phase 9.15 updated
    handoff text and ignored scratch run state after that review. If following
    Kamma strictly for finalization, run a fresh review or focused review check
    before `/kamma:4-finalize`; no staged skill behavior changed in Phase 9.15.
  - Because Phase 9.5 changed `vicaya-0-scope` after the existing review, first
    rerun review and confirm it accepts the bounded binding context-budget plan
    and context-break guard exceptions from Phases 9.5, 9.6, 9.7, 9.8, 9.9,
    9.10, 9.12, 9.13, 9.14, the handoff/scratch sync in 9.15, durable Stage 2
    artifacts in 9.16, no-global-temp cleanup in 9.17, and compact-tolerant
    default/risk-triggered hard-stop policy in 9.18.
  - Do not finalize if the failed staged attempt was removed by broad Git
    reversal instead of explicit deletion/overwrite in this thread.
  - Do not finalize if any staged skill still summarizes canonical behavior.
  - Do not finalize if any staged skill differs from the routed section-router
    design except for the bounded context-budget controls documented in Phases
    9.5, 9.6, 9.7, 9.8, 9.9, 9.10, 9.12, 9.13, and 9.14, plus the durable
    artifact/no-global-temp cleanup controls in Phases 9.16 and 9.17, and the
    compact-tolerant default plus durable checkpoint controls in Phase 9.18.
  - Do not finalize if any staged skill lacks the out-of-scope handoff guard or
    permits running phases outside its owned scope.
  - Do not finalize if this thread changed `skill/vicaya/SKILL.md` anywhere
    other than the allowed staged-mode pointer wording near the top and the
    Phase 9.17 no-global-temp/per-run cleanup instructions. Pre-existing dirty
    hunks may remain only if they match the recorded pre-edit diff.
  - Do not finalize if any heading route is broken.
  - Do not finalize if any routed heading points to a fenced example heading
    instead of a real canonical section.
  - Do not finalize if the README contains workflow paraphrase beyond the
    bounded context-budget controls, or if documentation still describes concise
    reference files as the staged behavior mechanism.
  - Do not finalize if `skill/vicaya/shared/` exists.
  - Do not finalize if durable docs contain generic shared-reference language
    for staged behavior.
  - Do not finalize if any active skill root that registers the monolithic
    `vicaya` skill lacks matching staged registrations using the same link style,
    or if any active staged skill registration/symlink points somewhere other
    than the rebuilt staged directory.
  - -> verify: thread is finalized according to Kamma workflow and the final
    review remains `PASSED`.
