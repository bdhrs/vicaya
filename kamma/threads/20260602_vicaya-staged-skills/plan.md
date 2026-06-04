# Plan - Split Vicaya into model-aware staged skills

No GitHub issue is associated with this thread.

## Architecture Decisions

- Keep `skill/vicaya/SKILL.md` as a permanent canonical full-run skill.
  - Rationale: Vicaya intentionally supports two permanent execution modes:
    full-run mode via `skill/vicaya/SKILL.md` for high-context models, and staged
    mode via `vicaya-0-scope` through `vicaya-3-complete` for smaller or
    weaker-context models. The full skill is not deprecated.
- Add four staged skills as a second execution mode, not as a replacement for
  `/vicaya`.
  - `skill/vicaya-0-scope/SKILL.md`: Phase 0, advanced model.
  - `skill/vicaya-1-gather/SKILL.md`: Phases 1-4c, fast model.
  - `skill/vicaya-2-synthesize-review/SKILL.md`: Phases 5-6, advanced model.
  - `skill/vicaya-3-complete/SKILL.md`: Phase 7 and final reporting, fast model.
- Use one core reference plus one reference file per cognitive work type under
  `skill/vicaya/shared/`.
  - `core.md`: continuity, gates, global rules, handoff, failure rules.
  - `scope.md`: Phase 0 framing, run class, ambiguity handling, research brief.
  - `sources.md`: Phase 1-4c source-gathering helper commands and rules.
  - `synthesis.md`: Phase 5-6 synthesis, evidence tiers, bibliography, review.
  - `completion.md`: Phase 7 note writing, validation, PDF, run report, style.
- Use existing scratch/gate commands as the only durable handoff system.
  - No new Python handoff mechanism.
  - No reliance on `RESUME.md`.
  - No automated model switching.
- Treat this as documentation/skill refactor unless implementation proves
  otherwise.
  - Do not edit `tools/research_sources.py` unless a staged-skill requirement
    cannot be represented with current scratch commands.
- Verification is structural grep/read checks unless Python code is changed.
  - Do not run full-suite validation for doc-only changes.
- Keep staged `SKILL.md` files thin.
  - They should state purpose, model tier, entry gate, owned phases, references
    to read, exit gate, and next skill.
  - They should not duplicate full helper documentation or unrelated phase
    bodies.
- Do not treat grep hits as sufficient proof of correctness.
  - Use `rg` to locate expected text, then read the staged skills and shared
    references end-to-end for coherence.

## Model Strategy

| Stage skill | Recommended tier | Reason |
|---|---|---|
| `vicaya-0-scope` | Advanced | Question framing, run-class choice, ambiguity handling, and search strategy affect the entire run. |
| `vicaya-1-gather` | Fast | Source retrieval, helper execution, and scratch logging are mostly mechanical once the research brief exists. |
| `vicaya-2-synthesize-review` | Advanced | Evidence weighing, conflict resolution, synthesis, and adversarial review require strong reasoning. |
| `vicaya-3-complete` | Fast | Final note rendering, validation, PDF generation, and run-report sync are mostly mechanical after synthesis is approved. |

`vicaya-3-complete` must explicitly stop and hand back to
`vicaya-2-synthesize-review` if it finds unresolved evidence conflicts, missing
citations, or synthesis gaps that require new reasoning.

## Phase 1 - Pre-edit scope check and source mapping

- [x] Inspect the current monolithic skill and record which sections feed each
  reference file and staged skill.
  - Read: `skill/vicaya/SKILL.md`
  - Map these sections:
    - `## Critical execution rules`
    - `## Hard rules`
    - `## Inputs`
    - `## Setup - paths and tools`
    - `## Calling the helpers`
    - `## Helper return shapes`
    - `## Book-identifier lookups`
    - `## DPD dictionary database`
    - `## EBC vault`
    - `## Research scratchpad`
    - `## Evidence tiers`
    - `## Bibliography`
    - `## Investigation angles`
    - `### Phase 0` through `### Phase 7`
    - `## Final report to the user`
    - `## When something fails`
    - `## Style notes`
    - `## Self-improvement loop`
  - Assign each section to exactly one of:
    - `core.md`
    - `scope.md`
    - `sources.md`
    - `synthesis.md`
    - `completion.md`
    - short local text in one staged `SKILL.md`
  - -> verify: run `rg -n "^## |^### Phase" skill/vicaya/SKILL.md`, confirm
    all listed sections still exist and have a mapped destination.

- [x] Confirm existing scratch commands support the four-stage handoff without
  Python changes.
  - Inspect: `tools/research_sources.py`
  - Confirm these commands already exist:
    - `scratch-init`
    - `scratch-log`
    - `scratch-gate 0`
    - `scratch-gate 4c`
    - `scratch-verify`
    - `scratch-gate 6`
    - `scratch-gate 7`
    - `scratch-resume`
  - -> verify: `rg -n "scratch-init|scratch-log|scratch-gate|scratch-verify|scratch-resume|Phase 0" tools/research_sources.py` shows the commands and Phase 0 gate support.

- [x] Confirm this thread will not use `RESUME.md`.
  - Do not read it for workflow content.
  - Do not add any instruction that depends on it.
  - -> verify: staged-skill design uses only scratch dossier, gates,
    `scratch-log`, and `scratch-resume`.

- [x] Phase verification.
  - -> verify: no implementation files edited yet; `git status --short` is only
    inspected for awareness, not cleaned or reverted.

## Phase 2 - Verify staged skill discoverability

- [x] Confirm whether sibling skill directories under `skill/` are directly
  callable in the target agent environment.
  - Inspect the active skill registration/symlink mechanism for Claude/Codex.
  - Do not assume `skill/vicaya-0-scope/`, `skill/vicaya-1-gather/`,
    `skill/vicaya-2-synthesize-review/`, or `skill/vicaya-3-complete/` becomes
    callable automatically just because the directories exist in this repo.
  - -> verify: staged skill names are either confirmed directly callable, or the
    exact install/symlink requirement is documented before any direct invocation
    is documented.

- [x] If staged skills are not automatically discoverable, choose the least
  invasive documented path.
  - Option A: document the exact install/symlink step needed to make all four
    staged skills callable, without performing external symlink changes unless
    the user explicitly approves them.
  - Option B: document staged files as in-repo staged workflows that must be
    installed before direct invocation.
  - -> verify: no README, `SKILL.md`, or project-doc text claims staged skill
    invocation is available unless discoverability has been verified or the
    required install/symlink step is named.

- [x] Phase verification.
  - -> verify: implementation knows whether staged skill invocation is available
    directly, requires install/symlink work, or must be documented as an in-repo
    workflow only.

## Phase 3 - Create reference files

- [x] Create directory `skill/vicaya/shared/`.
  - -> verify: `test -d skill/vicaya/shared` exits 0.

- [x] Create `skill/vicaya/shared/core.md`.
  - Include concise shared rules from:
    - critical execution rules;
    - hard rules;
    - scratch dossier and gate discipline;
    - handoff and resume rules;
    - failure handling;
    - YAML frontmatter safety;
    - Obsidian launch rule;
    - citation discipline;
    - no AI/model attribution in scholarship body;
    - no process logging inside research notes;
    - Pali spelling conventions.
  - Include exact warning: `RESUME.md is temporary; do not use it as handoff state.`
  - -> verify: `rg -n "scratch-resume|scratch-gate|RESUME.md|No AI|YAML|Citations" skill/vicaya/shared/core.md` shows hits.

- [x] Create `skill/vicaya/shared/scope.md`.
  - Include:
    - Phase 0 request understanding;
    - question sanitization;
    - exact scratch fields from the full skill:
      - `question_original`;
      - `question_polished`;
      - `scope_assumptions`;
      - `ambiguity_status`;
    - run-class decision: `sutta-anchored` vs `thematic`;
    - ambiguity handling and when to ask the user;
    - research brief format for the handoff to `vicaya-1-gather`;
    - required research brief contents:
      - polished question;
      - run class;
      - initial angle recommendations;
      - likely search terms;
      - likely source classes;
      - named counter-perspectives to look for;
      - known scope limits;
    - command sequence:
      - `uv run tools/research_sources.py scratch-init <slug>`
      - `uv run tools/research_sources.py scratch-log 0 scope-brief --summary "<brief>"`
      - `uv run tools/research_sources.py scratch-gate 0`
  - Do not include source-search helper bodies.
  - -> verify: `rg -n "Phase 0|question_original|question_polished|scope_assumptions|ambiguity_status|scratch-init|scratch-log 0|scratch-gate 0|research brief|sutta-anchored|thematic" skill/vicaya/shared/scope.md` shows hits.

- [x] Create `skill/vicaya/shared/sources.md`.
  - Include source-gathering helper commands and return shapes needed by
    Phases 1-4c.
  - Include helper references for:
    - `search-vault`
    - `search-canon`
    - `resolve-citation`
    - `lookup-book`
    - DPD lookup guidance
    - `get-ebc-overview`
    - `search-ebc`
    - `sc-parallels`
    - `search-calibre`
    - `calibre-check`
    - `search-sanskrit`
    - web fetch logging
    - YouTube search/transcript guidance
    - WisdomLib lookup/logging guidance
  - Include investigation-angle triage and source-specific guidance needed to
    run Phase 1 through Phase 4c.
  - Include the required gate sequence:
    - `uv run tools/research_sources.py scratch-gate 1`
    - `uv run tools/research_sources.py scratch-gate 2`
    - `uv run tools/research_sources.py scratch-gate 2.5` when applicable
    - `uv run tools/research_sources.py scratch-gate 3`
    - `uv run tools/research_sources.py scratch-gate 3b` when applicable
    - `uv run tools/research_sources.py scratch-gate 4`
    - `uv run tools/research_sources.py scratch-gate 4b`
    - `uv run tools/research_sources.py scratch-gate 4c`
  - Do not include full Phase 5-7 writing instructions.
  - -> verify: `rg -n "Phase 1|Phase 4c|search-canon|search-calibre|get-ebc-overview|sc-parallels|YouTube|WisdomLib|scratch-gate 1|scratch-gate 4c" skill/vicaya/shared/sources.md` shows hits.

- [x] Create `skill/vicaya/shared/synthesis.md`.
  - Include:
    - evidence tiers;
    - bibliography rules needed before drafting;
    - Phase 5 synthesis rules;
    - Phase 6 cross-check rules;
    - citation pre-annotation and `[REJECTED]` handling;
    - requirements for logging synthesis and review integrations into scratch.
    - required gate sequence:
      - `uv run tools/research_sources.py scratch-gate 5`
      - `uv run tools/research_sources.py scratch-gate 6`
  - Do not include full Phase 0-4c source-gathering bodies.
  - Do not include the full Phase 7 note template, validation, PDF, or run-report
    mechanics.
  - -> verify: `rg -n "Evidence tiers|Bibliography|Phase 5|Phase 6|cross-check|REJECTED|scratch-gate 5|scratch-gate 6" skill/vicaya/shared/synthesis.md` shows hits.

- [x] Create `skill/vicaya/shared/completion.md`.
  - Include:
    - Phase 7 final-note writing;
    - frontmatter rules;
    - final note template;
    - Pali/English presentation rules;
    - footnote rules;
    - validation and PDF generation;
    - run reflection;
    - run report sync;
    - final report to user;
    - self-improvement loop.
  - Preserve warning that `scripts/sync_run_report.py` is pre-approved and may
    pull, commit, and push run reports.
  - Do not include full source-gathering or synthesis instructions.
  - -> verify: `rg -n "Phase 7|validate_note|generate_note_pdf|sync_run_report|Final report|Self-improvement|may pull, commit, and push" skill/vicaya/shared/completion.md` shows hits.

- [x] Phase verification.
  - -> verify: read `core.md`, `scope.md`, `sources.md`, `synthesis.md`, and
    `completion.md` end-to-end; confirm they are concise references and do not
    duplicate the entire monolithic skill wholesale.

## Phase 4 - Create model-aware staged skills

- [x] Apply the thin staged-skill template to all four staged `SKILL.md` files.
  - Each staged `SKILL.md` should contain only:
    - frontmatter;
    - short purpose statement;
    - recommended model tier;
    - entry condition and required prior gate;
    - shared reference files to read;
    - owned phases;
    - required exit gate;
    - next skill / stop instruction.
  - Do not copy full helper documentation, unrelated phase bodies, final note
    templates, or cross-stage rules into these files.
  - -> verify: after all four files exist, read them end-to-end and confirm they
    are thin dispatch files that delegate detailed instructions to shared
    references.

- [x] Create directory `skill/vicaya-0-scope/`.
  - -> verify: `test -d skill/vicaya-0-scope` exits 0.

- [x] Create `skill/vicaya-0-scope/SKILL.md`.
  - Frontmatter:
    ```markdown
    ---
    name: vicaya-0-scope
    description: Frame a Vicaya research question, initialize scratch state, and produce the research brief for source gathering.
    ---
    ```
  - Must state: recommended model tier is advanced.
  - Must read shared files:
    - `../vicaya/shared/core.md`
    - `../vicaya/shared/scope.md`
  - Must own:
    - Phase 0 - request understanding and scope check.
    - question sanitization.
    - exact scratch fields: `question_original`, `question_polished`,
      `scope_assumptions`, and `ambiguity_status`.
    - run-class decision.
    - ambiguity handling.
    - durable research brief for the gathering stage.
  - Must start new runs with:
    - `uv run tools/research_sources.py scratch-init <slug>`
    - add `--class thematic` for non-sutta-anchored questions.
  - Must support continuation with:
    - `uv run tools/research_sources.py scratch-resume <slug>`
  - Must exit with:
    - `uv run tools/research_sources.py scratch-log 0 scope-brief --summary "<brief>"`
    - `uv run tools/research_sources.py scratch-gate 0`
    - explicit instruction: `Stop here. Switch to the fast model and invoke vicaya-1-gather.`
  - -> verify: `rg -n "advanced|Phase 0|question_original|question_polished|scope_assumptions|ambiguity_status|scratch-init|scratch-log 0|scratch-gate 0|vicaya-1-gather|fast model" skill/vicaya-0-scope/SKILL.md` shows hits.

- [x] Create directory `skill/vicaya-1-gather/`.
  - -> verify: `test -d skill/vicaya-1-gather` exits 0.

- [x] Create `skill/vicaya-1-gather/SKILL.md`.
  - Frontmatter:
    ```markdown
    ---
    name: vicaya-1-gather
    description: Run Vicaya source-gathering phases from Phase 1 through Phase 4c, then stop before synthesis.
    ---
    ```
  - Must state: recommended model tier is fast.
  - Must read shared files:
    - `../vicaya/shared/core.md`
    - `../vicaya/shared/sources.md`
  - Entry instructions:
    - Run `uv run tools/research_sources.py scratch-resume <slug>`.
    - Confirm the prior gate is Phase 0.
    - Read the Phase 0 research brief before source gathering.
  - Must own:
    - Phase 1 - vault context, angle triage, EBC seed lookup, perspective map.
    - Phase 2 - canon search and EBC pulls.
    - Phase 2.5 - SuttaCentral offline parallels.
    - Phase 3 - library search.
    - Phase 3b - Sanskrit source search.
    - Phase 4a - web search.
    - Phase 4b - YouTube search.
    - Phase 4c - WisdomLib.
  - Must run every phase gate as each phase completes:
    - `scratch-gate 1`
    - `scratch-gate 2`
    - `scratch-gate 2.5` when applicable
    - `scratch-gate 3`
    - `scratch-gate 3b` when applicable
    - `scratch-gate 4`
    - `scratch-gate 4b`
    - `scratch-gate 4c`
  - Must exit with:
    - `uv run tools/research_sources.py scratch-gate 4c`
    - explicit instruction: `Stop here. Switch to the advanced model and invoke vicaya-2-synthesize-review.`
  - -> verify: `rg -n "fast|Phase 1|Phase 2|Phase 2.5|Phase 3|Phase 3b|Phase 4a|Phase 4b|Phase 4c|scratch-gate 1|scratch-gate 4c|vicaya-2-synthesize-review|advanced model" skill/vicaya-1-gather/SKILL.md` shows hits.

- [x] Create directory `skill/vicaya-2-synthesize-review/`.
  - -> verify: `test -d skill/vicaya-2-synthesize-review` exits 0.

- [x] Create `skill/vicaya-2-synthesize-review/SKILL.md`.
  - Frontmatter:
    ```markdown
    ---
    name: vicaya-2-synthesize-review
    description: Synthesize Vicaya evidence, run second-pass review, integrate accepted findings, and stop before final note writing.
    ---
    ```
  - Must state: recommended model tier is advanced.
  - Must read shared files:
    - `../vicaya/shared/core.md`
    - `../vicaya/shared/synthesis.md`
  - Entry instructions:
    - Run `uv run tools/research_sources.py scratch-resume <slug>`.
    - Run `uv run tools/research_sources.py scratch-verify`.
    - Read the scratch file before drafting.
    - Do not draft if `scratch-verify` fails.
  - Must own:
    - Phase 5 - synthesis.
    - Phase 6 - second-pass review / cross-check.
  - Must run `uv run tools/research_sources.py scratch-gate 5` after Phase 5
    synthesis is recorded in scratch.
  - Must exit with:
    - `uv run tools/research_sources.py scratch-gate 6`
    - explicit instruction: `Stop here. Switch to the fast model and invoke vicaya-3-complete.`
  - Must not write the final vault note.
  - -> verify: `rg -n "advanced|scratch-resume|scratch-verify|Phase 5|Phase 6|cross-check|scratch-gate 5|scratch-gate 6|vicaya-3-complete|fast model" skill/vicaya-2-synthesize-review/SKILL.md` shows hits.

- [x] Create directory `skill/vicaya-3-complete/`.
  - -> verify: `test -d skill/vicaya-3-complete` exits 0.

- [x] Create `skill/vicaya-3-complete/SKILL.md`.
  - Frontmatter:
    ```markdown
    ---
    name: vicaya-3-complete
    description: Complete a Vicaya run by writing the final note, validating it, generating PDF output, gating Phase 7, and publishing the run report.
    ---
    ```
  - Must state: recommended model tier is fast.
  - Must read shared files:
    - `../vicaya/shared/core.md`
    - `../vicaya/shared/completion.md`
  - Entry instructions:
    - Run `uv run tools/research_sources.py scratch-resume <slug>`.
    - Confirm prior gate is Phase 6.
    - Read the Phase 5 draft and Phase 6 integrations from scratch.
  - Must own:
    - Phase 7 - write final note.
    - frontmatter rules.
    - final note template.
    - validation.
    - PDF generation.
    - Phase 7 gate.
    - run report sync.
    - final report to user.
    - self-improvement loop.
  - Must include commands:
    - `uv run scripts/validate_note.py "Vicaya/<YYYY-MM-DD> - <slug>.md"`
    - `uv run scripts/generate_note_pdf.py "Vicaya/<YYYY-MM-DD> - <slug>.md"`
    - `uv run tools/research_sources.py scratch-gate 7`
    - `uv run scripts/sync_run_report.py`
  - Must stop and hand back to `vicaya-2-synthesize-review` if it finds
    unresolved evidence conflicts, missing citations, or synthesis gaps.
  - Must preserve warning that `scripts/sync_run_report.py` is pre-approved and
    may pull, commit, and push run reports.
  - -> verify: `rg -n "fast|Phase 7|validate_note|generate_note_pdf|scratch-gate 7|sync_run_report|Final report|Self-improvement|vicaya-2-synthesize-review|may pull, commit, and push" skill/vicaya-3-complete/SKILL.md` shows hits.

- [x] Phase verification.
  - -> verify: read all four staged `SKILL.md` files end-to-end; confirm each
    stage loads only `core.md` plus one stage-specific reference file, states
    its model tier, and stops at its required handoff point.

## Phase 5 - Update docs and maintenance rule

- [x] Add staged-skill usage notes to `skill/vicaya/README.md`.
  - Include:
    ```markdown
    ## Execution modes

    Vicaya supports two permanent execution modes:

    - Full-run mode: use `/vicaya <question>` with `skill/vicaya/SKILL.md` when
      the model has enough context and can reliably execute the whole workflow
      in one goal.
    - Staged mode: use `vicaya-0-scope`, `vicaya-1-gather`,
      `vicaya-2-synthesize-review`, and `vicaya-3-complete` when context load or
      model strength makes staged execution safer.

    Both modes use the same scratch dossier, gates, citations, validation, PDF
    generation, and run-report rules. Durable handoff is the scratch dossier plus
    `scratch-gate`/`scratch-resume`.
    `RESUME.md` is temporary and must not be used as workflow state.
    ```
  - If Phase 2 found staged skills are not directly discoverable, include the
    exact install/symlink requirement before telling users to invoke them.
  - -> verify: `rg -n "Execution modes|Full-run mode|Staged mode|vicaya-0-scope|vicaya-1-gather|vicaya-2-synthesize-review|vicaya-3-complete|RESUME.md" skill/vicaya/README.md` shows hits, then read the section and confirm it does not imply unverified staged invocation.

- [x] Add a short pointer near the top of `skill/vicaya/SKILL.md`.
  - Insert after the opening description, not inside phase instructions:
    ```markdown
    ## Execution modes

    This full skill is the permanent full-run workflow for high-context models
    that can reliably execute Vicaya in one goal. Vicaya also has a staged mode:
    use `vicaya-0-scope` on the advanced model for Phase 0, `vicaya-1-gather`
    on the fast model for Phases 1-4c, `vicaya-2-synthesize-review` on the
    advanced model for Phases 5-6, and `vicaya-3-complete` on the fast model
    for Phase 7. Both modes use the same scratch dossier, gates, and
    `scratch-resume`; do not rely on `RESUME.md`.
    ```
  - If Phase 2 found staged skills are not directly discoverable, include the
    exact install/symlink requirement before telling users to invoke them.
  - -> verify: `rg -n "Execution modes|full-run workflow|vicaya-0-scope|vicaya-2-synthesize-review|scratch-resume|RESUME.md" skill/vicaya/SKILL.md` shows hits, then read the section and confirm it does not deprecate `/vicaya` or imply unverified staged invocation.

- [x] Add durable maintenance rule to `kamma/project.md`.
  - Add section:
    ```markdown
    ## Vicaya skill maintenance rule

    Vicaya has two permanent execution modes: full-run mode via
    `skill/vicaya/SKILL.md`, and staged mode via `skill/vicaya-0-scope/`,
    `skill/vicaya-1-gather/`, `skill/vicaya-2-synthesize-review/`, and
    `skill/vicaya-3-complete/`, with shared references under
    `skill/vicaya/shared/`. The full-run skill is not deprecated.

    Any change to Vicaya phase rules, helper usage, scratch gates, citation
    policy, final-note shape, validation/PDF/report behavior, model-tier
    recommendation, or self-improvement behavior must update
    `skill/vicaya/SKILL.md`, the relevant staged skill, and the relevant shared
    reference in the same thread. `RESUME.md` is temporary and must not be used
    as workflow state.
    ```
  - -> verify: `rg -n "Vicaya skill maintenance rule|two permanent execution modes|full-run skill is not deprecated|staged mode|shared references|RESUME.md" kamma/project.md` shows hits.

- [x] Phase verification.
  - -> verify: read the changed docs and confirm they do not claim external
    symlinks were updated and do not claim model switching is automated.

## Phase 6 - Structural verification

- [x] Verify all staged skill files exist.
  - -> verify: `test -f skill/vicaya-0-scope/SKILL.md; and test -f skill/vicaya-1-gather/SKILL.md; and test -f skill/vicaya-2-synthesize-review/SKILL.md; and test -f skill/vicaya-3-complete/SKILL.md`

- [x] Verify all reference files exist.
  - -> verify: `test -f skill/vicaya/shared/core.md; and test -f skill/vicaya/shared/scope.md; and test -f skill/vicaya/shared/sources.md; and test -f skill/vicaya/shared/synthesis.md; and test -f skill/vicaya/shared/completion.md`

- [x] Verify staged skills mention model tier, resume, and gates.
  - -> verify:
    - `rg -n "advanced|scratch-resume|scratch-gate 0" skill/vicaya-0-scope/SKILL.md`
    - `rg -n "fast|scratch-resume|scratch-gate 1|scratch-gate 4c" skill/vicaya-1-gather/SKILL.md`
    - `rg -n "advanced|scratch-resume|scratch-verify|scratch-gate 5|scratch-gate 6" skill/vicaya-2-synthesize-review/SKILL.md`
    - `rg -n "fast|scratch-resume|scratch-gate 7|sync_run_report" skill/vicaya-3-complete/SKILL.md`
    - Then read all four staged files end-to-end and confirm the hits are used
      correctly, not merely present as stray text.

- [x] Verify the full-run skill remains first-class.
  - -> verify: read the added `skill/vicaya/SKILL.md` execution-mode section and
    confirm it says the full skill is permanent/full-run, does not use
    deprecation/fallback language, and presents staged mode as an alternate
    execution profile.

- [x] Verify stage-specific references do not reload irrelevant bulk.
  - -> verify:
    - `rg -n "Phase 5|Phase 6|Phase 7|final note template" skill/vicaya/shared/sources.md` returns no full late-stage instructions.
    - `rg -n "Phase 1|Phase 2|search-canon|search-calibre|YouTube|WisdomLib" skill/vicaya/shared/synthesis.md` returns no full gathering instructions.
    - `rg -n "Phase 1|Phase 2|search-canon|Phase 5 synthesis|cross-check prompt" skill/vicaya/shared/completion.md` returns no full gathering or synthesis instructions.

- [x] Verify `RESUME.md` is only mentioned as something not to rely on.
  - -> verify: `rg -n "RESUME.md" skill/vicaya skill/vicaya-0-scope skill/vicaya-1-gather skill/vicaya-2-synthesize-review skill/vicaya-3-complete kamma/project.md`
  - Expected: every hit says not to rely on it / not workflow state.

- [x] Verify no Python code was changed by this thread.
  - -> verify: `git diff --name-only -- skill kamma | rg "\.py$"` returns no
    output for this thread's changes.
  - If Python output appears, stop and run localized checks for those touched
    files:
    - `uv run ruff check <changed .py files>`
    - `uv run pyright <changed .py files>`
    - `uv run pyrefly check --search-path . <changed .py files>`
    - relevant localized pytest only.

- [x] Verify Markdown references are coherent.
  - -> verify: read all new `SKILL.md` files and shared files end-to-end; confirm
    relative references point to existing files.

## Phase 7 - Review readiness

- [x] Prepare review notes.
  - Include:
    - files changed;
    - the two permanent execution modes;
    - four staged skill boundaries;
    - model recommendation for each stage;
    - staged-skill discoverability result;
    - shared/reference files;
    - verification commands and results;
    - known limitation: `vicaya-3-complete` is fast-model by default, but must
      hand back to advanced synthesis if unresolved reasoning appears.
  - -> verify: review notes are ready for `/kamma:3-review`.

- [x] Suggested commit message for user.
  - Use:
    ```text
    docs(vicaya): split workflow into model-aware staged skills
    ```
  - -> verify: commit message is documented in final implementation summary
    only; do not run `git commit`.

## Phase 8 - Post-review staged skill registration bugfix

- [x] Register staged skills in the same loaded skill root as the main `vicaya`
  skill.
  - User-reported bug: the main skill was linked in `/Users/deva/.agents/skills/`,
    but the four staged skills were not.
  - Create these symlinks:
    - `/Users/deva/.agents/skills/vicaya-0-scope` ->
      `/Users/deva/Documents/dps/vicaya/skill/vicaya-0-scope`
    - `/Users/deva/.agents/skills/vicaya-1-gather` ->
      `/Users/deva/Documents/dps/vicaya/skill/vicaya-1-gather`
    - `/Users/deva/.agents/skills/vicaya-2-synthesize-review` ->
      `/Users/deva/Documents/dps/vicaya/skill/vicaya-2-synthesize-review`
    - `/Users/deva/.agents/skills/vicaya-3-complete` ->
      `/Users/deva/Documents/dps/vicaya/skill/vicaya-3-complete`
  - -> verify: `ls -l /Users/deva/.agents/skills/vicaya*` shows the main skill
    and all four staged skills linked to this repo.

- [x] Update docs so registration instructions match the active local skill
  root.
  - Update `skill/vicaya/README.md` to document
    `/Users/deva/.agents/skills/` as the shared agent skill root now containing
    the staged skill symlinks.
  - Keep `skill/vicaya/SKILL.md` almost untouched: it should contain only a
    minimal pointer to staged mode and must not carry staged registration or
    symlink mechanics.
  - Update `kamma/threads/20260602_vicaya-staged-skills/review.md` with the
    applied fix and verification evidence.
  - -> verify: `rg -n "agents/skills|vicaya-0-scope|vicaya-3-complete" skill/vicaya/README.md` shows the active skill-root documentation.
  - -> verify: `rg -n "lower-context staged runs|canonical one-goal" skill/vicaya/SKILL.md` shows the intentionally minimal full-run skill pointer.
  - -> verify: `rg -n "agents/skills|Direct staged invocation|target agent's loaded skill root" skill/vicaya/SKILL.md` returns no output.

## Phase 9 - Explicit next-stage handoff instructions

- [x] Add clear final handoff instructions to each staged skill.
  - User-reported gap: the staged skills end by naming the next skill, but they
    do not clearly tell the user or next agent to reuse the same scratch slug,
    run `scratch-resume <slug>`, and read the previous stage's logged findings.
  - Update only:
    - `skill/vicaya-0-scope/SKILL.md`
    - `skill/vicaya-1-gather/SKILL.md`
    - `skill/vicaya-2-synthesize-review/SKILL.md`
    - `skill/vicaya-3-complete/SKILL.md`
  - Each staged skill must end with a copyable instruction naming:
    - the next skill or final/hand-back condition;
    - the model tier for the next stage;
    - the same scratch `<slug>`;
    - `uv run tools/research_sources.py scratch-resume <slug>`;
    - the previous-stage scratch findings the next stage must read.
  - -> verify: pre-edit `rg -n "## Next-stage instruction|previous stage|same <slug>|scratch-resume <slug>.*previous" skill/vicaya-0-scope/SKILL.md skill/vicaya-1-gather/SKILL.md skill/vicaya-2-synthesize-review/SKILL.md skill/vicaya-3-complete/SKILL.md` returned no output, confirming the gap.
  - -> verify: post-edit `rg -n "## Next-stage instruction|same scratch slug|scratch-resume <slug>|previous stage" skill/vicaya-0-scope/SKILL.md skill/vicaya-1-gather/SKILL.md skill/vicaya-2-synthesize-review/SKILL.md skill/vicaya-3-complete/SKILL.md` shows hits in all staged skills.
  - -> verify: `rg -n "[[:blank:]]+$" skill/vicaya-0-scope/SKILL.md skill/vicaya-1-gather/SKILL.md skill/vicaya-2-synthesize-review/SKILL.md skill/vicaya-3-complete/SKILL.md kamma/threads/20260602_vicaya-staged-skills/plan.md` returns no output.

## Phase 10 - Align vicaya-3-complete final output with main skill

- [x] Make the staged completion path print the same final report structure as
  the main `skill/vicaya/SKILL.md`.
  - User-reported gap: `vicaya-3-complete` currently ends with a generic final
    stage message instead of the main skill's Section 1 / Section 2 / Section 3
    final terminal report.
  - Confirmed mismatch before edit:
    - `rg -n "Section 1|Section 2|Section 3|sync_notes|AskUserQuestion|GitHub push|bdhrs/vicaya-notes|Final report to the user" skill/vicaya-3-complete/SKILL.md skill/vicaya/shared/completion.md` showed `sync_notes` only in `completion.md` and no Section 1 / Section 2 / Section 3 final-report structure in `vicaya-3-complete`.
  - Read before documenting script side effects:
    - `scripts/sync_notes.py`
    - `scripts/sync_run_report.py`
  - Update only:
    - `skill/vicaya-3-complete/SKILL.md`
    - `skill/vicaya/shared/completion.md`
    - `kamma/threads/20260602_vicaya-staged-skills/plan.md`
    - `kamma/threads/20260602_vicaya-staged-skills/review.md`
  - Required behavior:
    - keep validation and PDF generation after every successful vault write;
    - include the user-approved note-repo publishing prompt and
      `uv run scripts/sync_notes.py "Vicaya/<YYYY-MM-DD> - <slug>.md"`;
    - keep Phase 7 exit as `scratch-gate 7`, then
      `uv run scripts/sync_run_report.py`;
    - require the final terminal report to use the same three sections as the
      main skill: Run summary, Skill improvements made, Distillation reminder.
  - -> verify: `rg -n "Section 1|Section 2|Section 3|sync_notes|bdhrs/vicaya-notes|scratch-gate 7|sync_run_report|Final report to the user|Do not print a generic" skill/vicaya-3-complete/SKILL.md skill/vicaya/shared/completion.md` shows the aligned staged completion instructions.
  - -> verify: `rg -n "Section 1 — Run summary|Section 2 — Skill improvements made|Section 3 — Distillation reminder|Skill distillation due|Example \\(good\\)|Example \\(bad" skill/vicaya/SKILL.md skill/vicaya-3-complete/SKILL.md skill/vicaya/shared/completion.md` shows matching main-skill final report labels and reminder text.
  - -> verify: `rg -n "Final stage complete for scratch slug|generic successful-ending" skill/vicaya-3-complete/SKILL.md skill/vicaya/shared/completion.md` returns no old generic success message; the only hit is the explicit prohibition against printing one.
  - -> verify: `rg -n "[[:blank:]]+$" skill/vicaya-3-complete/SKILL.md skill/vicaya/shared/completion.md kamma/threads/20260602_vicaya-staged-skills/plan.md` returns no output.
