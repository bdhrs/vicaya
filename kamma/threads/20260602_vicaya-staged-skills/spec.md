# Spec - Split Vicaya into model-aware staged skills

## Overview

Vicaya currently lives mostly in one large skill file:
`skill/vicaya/SKILL.md`. That file contains global rules, setup details,
helper documentation, investigation angles, research phases, synthesis rules,
note-writing rules, validation/PDF/report instructions, failure handling, style
rules, and self-improvement instructions.

This makes long research runs expensive in context because every agent loads the
full workflow even when it is only doing one kind of work. It also mixes tasks
that require different model strengths:

- question framing and research strategy need the advanced model;
- source retrieval and logging can usually be done by the fast model;
- evidence synthesis and critique need the advanced model;
- final note rendering, validation, PDF generation, and run-report sync can
  usually be done by the fast model if the synthesis is complete.

This thread gives Vicaya two permanent execution modes while preserving the
same research behavior and scratch-gate continuity:

- Full-run mode: `/vicaya <question>` via `skill/vicaya/SKILL.md`, for models
  with enough context and reliability to run the whole workflow in one goal.
- Staged mode: four smaller skills for models or sessions where context load
  makes one-goal execution unreliable.

The staged mode is:

- `vicaya-0-scope`: advanced-model stage for Phase 0 framing, run class,
  ambiguity handling, and a durable research brief.
- `vicaya-1-gather`: fast-model stage for Phase 1 through Phase 4c source
  gathering and logging.
- `vicaya-2-synthesize-review`: advanced-model stage for Phase 5 synthesis and
  Phase 6 second-pass review/cross-check integration.
- `vicaya-3-complete`: fast-model stage for Phase 7 final note writing,
  validation, PDF generation, run report, final response, and self-improvement
  mechanics.

The staged skills should use concise reference files rather than full duplicated
copies of all instructions. Each stage skill must stay thin, load only the
shared/core material and phase reference needed for that stage, and include no
less than what is required for correctness.

`RESUME.md` is temporary and must not be used as a durable handoff mechanism or
architectural dependency.

## What it should do

Preserve the full-run skill permanently:

- `skill/vicaya/SKILL.md` remains a canonical full-run workflow.
- It is not deprecated and is not a temporary compatibility artifact.
- Its rules must stay aligned with the staged workflow.
- Its core structure must remain intact. This thread may make small local
  pointer/clarity tweaks, but it must not redesign the original skill, turn it
  into a dispatcher, or require it to load the staged reference files.
- Duplication between the original full-run skill and staged/shared files is
  acceptable. The two modes are separate supported ways to run Vicaya:
  one-goal full-run mode through the original skill, and step-by-step staged
  mode through the new stage skills.
- The staged workflow must build on the original skill rather than replacing or
  restructuring it, because the original owner is satisfied with the existing
  full-run workflow.

Create four new stage skills under `skill/`:

- `skill/vicaya-0-scope/SKILL.md`
- `skill/vicaya-1-gather/SKILL.md`
- `skill/vicaya-2-synthesize-review/SKILL.md`
- `skill/vicaya-3-complete/SKILL.md`

Each staged skill must be thin and have:

- a clear `name` and `description`;
- a short purpose statement;
- a model recommendation: advanced or fast;
- entry conditions, including the prior gate or scratch state expected;
- exit conditions, including which `scratch-gate` must be run before stopping;
- resume instructions using `uv run tools/research_sources.py scratch-resume <slug>`;
- exact phase scope;
- only the helper documentation, rules, and style guidance relevant to that
  stage.

Create concise reference files under `skill/vicaya/shared/`:

- `core.md`
  - Hard rules that apply to every stage.
  - Scratch dossier, gates, resume, and handoff rules.
  - Failure handling.
  - Citation discipline.
  - No AI/model attribution in scholarship body.
  - No process logging inside research notes.
  - Pali spelling conventions, including exact-diacritic search requirements.
  - YAML safety.
  - Obsidian launch rule.
  - Warning: `RESUME.md` is temporary and must not be used as workflow state.

- `scope.md`
  - Phase 0 request understanding.
  - Question sanitization.
  - Exact scratch fields from the current full skill:
    `question_original`, `question_polished`, `scope_assumptions`, and
    `ambiguity_status`.
  - Run class decision: `sutta-anchored` vs `thematic`.
  - Ambiguity handling and when to ask the user.
  - Research brief format for the handoff to `vicaya-1-gather`, including
    initial angle recommendations, likely search terms, likely source classes,
    named counter-perspectives to look for, and known scope limits.
  - Required `scratch-init`, `scratch-log 0`, and `scratch-gate 0` commands.

- `sources.md`
  - Phase 1 through Phase 4c source-gathering instructions only.
  - Source helper commands and return shapes needed for gathering.
  - Vault, canon, DPD, EBC, SC parallels, Calibre, Sanskrit, web, YouTube, and
    WisdomLib guidance.
  - Investigation-angle triage and perspective-map rules.
  - Requirement to follow the Phase 0 research brief unless new evidence
    justifies a logged adjustment.
  - Required phase-gate sequence: `scratch-gate 1`, `scratch-gate 2`,
    `scratch-gate 2.5` when applicable, `scratch-gate 3`, `scratch-gate 3b`
    when applicable, `scratch-gate 4`, `scratch-gate 4b`, and
    `scratch-gate 4c`.

- `synthesis.md`
  - Evidence tiers.
  - Bibliography rules needed before drafting.
  - Phase 5 synthesis rules.
  - Phase 6 cross-check rules.
  - Citation pre-annotation and `[REJECTED]` handling.
  - Requirements for writing the synthesis and integrations into scratch.
  - Required phase-gate sequence: `scratch-gate 5`, then `scratch-gate 6`.
  - No full Phase 7 note template, validation, PDF, or run-report mechanics.

- `completion.md`
  - Phase 7 note template and frontmatter rules.
  - Pali/English presentation and footnote rules.
  - Validation and PDF generation.
  - Run reflection and run-report sync.
  - Final report to user.
  - Self-improvement loop.
  - No full Phase 0-4c source-gathering instructions.

Stage loading must be:

- `vicaya-0-scope` reads `core.md` and `scope.md`.
- `vicaya-1-gather` reads `core.md` and `sources.md`.
- `vicaya-2-synthesize-review` reads `core.md` and `synthesis.md`.
- `vicaya-3-complete` reads `core.md` and `completion.md`.

The original `skill/vicaya/SKILL.md` should remain valid. It may gain a short
pointer to the staged skills, but the monolithic workflow must not be deleted,
deprecated, or treated as a fallback in this thread.

Verify staged-skill discoverability before documenting direct staged invocation:

- Do not assume sibling directories under `skill/` are automatically callable.
- Confirm whether `vicaya-0-scope`, `vicaya-1-gather`,
  `vicaya-2-synthesize-review`, and `vicaya-3-complete` are directly
  discoverable by the target agent environment.
- If they are not directly discoverable, document the exact install/symlink
  requirement or keep docs explicit that the staged files exist in-repo but must
  be installed before direct invocation.

Update project documentation so future development does not silently update only
one workflow path. At minimum:

- Add a note to `skill/vicaya/README.md` explaining the staged skills,
  recommended model usage, and handoff sequence as a second permanent execution
  mode.
- Add a durable maintenance rule to `kamma/project.md`: changes to Vicaya
  workflow rules must be reflected in both `skill/vicaya/SKILL.md` and the
  relevant staged skill/shared reference.

## Assumptions & uncertainties

Assumptions:

- The current phase semantics remain unchanged: Phase 0 through Phase 7 still
  exist, with the same gate IDs in `tools/research_sources.py`.
- `tools/research_sources.py` already supplies the durable handoff system
  through scratch files, `.active`, `scratch-gate`, `scratch-verify`, and
  `scratch-resume`.
- `scratch-gate 0` already exists and is the correct exit point for the
  advanced-model scope stage.
- No new runtime handoff mechanism is needed for this thread.
- The staged skills are Markdown skill files, not Python code.
- `skill/vicaya/SKILL.md` remains a permanent canonical full-run workflow. The
  staged skills are a second supported execution profile, not a replacement.
- The original full-run skill remains self-contained. Any overlap created by
  extracting staged/shared instructions is intentional and allowed.
- Model recommendations are instructional. The skill files should tell the user
  which model tier is recommended, but they should not add automation that
  switches models.
- `RESUME.md`, if present, is temporary and must not be referenced in
  staged-skill instructions except to say not to rely on it.

Uncertainties:

- Exact reference-file boundaries may need adjustment after measuring the
  size/readability of the extracted sections.
- `vicaya-3-complete` is marked fast-model by default, but it must stop and hand
  back to `vicaya-2-synthesize-review` if final-note writing exposes unresolved
  evidence conflicts or missing citations.
- There may be external symlinks to `skill/vicaya`; this thread should not
  assume or modify external symlink state unless the user asks.

## Constraints

- Do not change `.env` or `.ini` files.
- Do not change research behavior unless required to split instructions.
- Do not deprecate, delete, or weaken the full-run `/vicaya` workflow.
- Do not redesign the core structure of `skill/vicaya/SKILL.md`; only add small
  local tweaks needed to point to staged mode or preserve alignment.
- Do not remove duplication merely for elegance. In this thread, preserving two
  separate execution modes is more important than forcing a single-source
  instruction architecture.
- Do not modify `tools/research_sources.py` unless tests reveal the existing
  scratch/handoff support is insufficient.
- Do not automate model switching. Stage files should state the recommended
  model tier and exact handoff point only.
- Do not use `RESUME.md` as a durable workflow artifact.
- Preserve scratch-gate semantics exactly:
  - Phase 0 exits with `scratch-gate 0`.
  - Phase 4c exits with `scratch-gate 4c`.
  - Phase 5 starts with `scratch-verify`.
  - Phase 5 exits with `scratch-gate 5`.
  - Phase 6 exits with `scratch-gate 6`.
  - Phase 7 exits with `scratch-gate 7` and
    `uv run scripts/sync_run_report.py`.
- Follow project test scope: run localized tests/checks only, not full-suite
  validation, unless explicitly approved.
- For documentation-only changes, verification may be structural grep/read
  checks rather than pytest.
- If Python code is changed, use localized tests plus `ruff`, `pyright`, and
  `pyrefly` only for touched files.

## How we'll know it's done

The thread is done when:

- The four staged skill directories exist with valid `SKILL.md` files.
- `skill/vicaya/SKILL.md` remains a valid permanent full-run workflow, with a
  clear pointer to staged mode but no deprecation language.
- Each stage skill clearly states:
  - its recommended model tier;
  - what phases it owns;
  - how to enter;
  - how to resume;
  - how to exit;
  - which next skill to invoke.
- Reference files exist and prevent unnecessary duplicated bulk text.
- Staged skill discoverability has been verified, or the docs state the exact
  install/symlink requirement before direct staged invocation is claimed.
- The staged skills preserve all critical rules needed for their phase scope.
- The hard-stop design is explicit:
  - stop after `vicaya-0-scope` / `scratch-gate 0` for model switch to fast;
  - stop after `vicaya-1-gather` / `scratch-gate 4c` for model switch to
    advanced;
  - stop after `vicaya-2-synthesize-review` / `scratch-gate 6` for model switch
    to fast;
  - optional hand-back from `vicaya-3-complete` to
    `vicaya-2-synthesize-review` if evidence conflicts remain.
- `skill/vicaya/README.md` and `kamma/project.md` contain durable guidance for
  both permanent execution modes, model recommendations, and maintenance rules.
- Structural verification confirms:
  - `vicaya-0-scope` includes Phase 0, model recommendation "advanced", and
    `scratch-gate 0`, and does not include full source-gathering bodies.
  - `vicaya-1-gather` includes Phases 1-4c, model recommendation "fast", and
    `scratch-gate 4c`, and does not include full Phase 5-7 note-template
    material.
  - `vicaya-2-synthesize-review` includes Phases 5-6, model recommendation
    "advanced", `scratch-verify`, `scratch-gate 5`, and `scratch-gate 6`, and
    does not include full source-gathering phase instructions or the full Phase
    7 note template.
  - `vicaya-3-complete` includes Phase 7, model recommendation "fast",
    validation/PDF/report/reflection instructions, and `scratch-gate 7`, and
    does not include full source-gathering or synthesis instructions.
  - all staged skills mention `scratch-resume`;
  - all staged skills mention their required entry and exit gates.
- Existing scratch tests remain valid if no Python code changes are made. If
  Python is untouched, no pytest run is required beyond optional localized
  confirmation.

## What's not included

- Splitting `vicaya-1-gather` into separate sutta/library/web skills.
- Rewriting the research workflow.
- Refactoring the original full-run skill into shared references or a staged
  dispatcher.
- Deprecating or replacing the full-run `/vicaya` skill.
- Replacing scratch files with a new handoff system.
- Automating model switches.
- Using or formalizing `RESUME.md`.
- Changing source helper behavior.
- Changing note validation, PDF generation, sync, or publishing behavior.
- Updating external skill symlinks under `~/.claude`, `~/.agents`, or
  `~/.codex` unless explicitly requested.
- Running a full Vicaya research session as a test.
