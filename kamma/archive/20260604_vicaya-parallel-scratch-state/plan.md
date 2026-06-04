# Plan - Make Vicaya scratch run state safe for parallel and restarted sessions

No GitHub issue is associated with this thread.

## Architecture Decisions

- Keep `data/scratch/.active` as a convenience fallback. It should support the
  common single-session path, but explicit run identity must take precedence.
- Fix the helper behavior in `tools/research_sources.py`; do not create a
  separate scratch model in skills or documentation.
- Prefer small resolver changes and focused tests over broad workflow changes.
- Update `skill/vicaya/SKILL.md` only where it documents scratch resume,
  precedence, and parallel-session behavior.
- Preserve scratch file format and phase gate behavior. Existing dossiers must
  remain readable without migration.

## Phase 1 - Characterize Current Scratch Selection

- [x] Inspect the scratch state resolver and command entrypoints.
  - Read `tools/research_sources.py` around `_scratch_path`, `_read_state`,
    `_write_state`, `scratch_init`, `scratch_log`, `scratch_gate`,
    `scratch_verify`, `scratch_resume`, `_maybe_autolog`, and CLI parser
    handling.
  - Confirm which commands currently accept a slug or path, which rely on
    `.active`, and which auto-log through `_maybe_autolog`.
  - -> verify: notes in this `plan.md` or implementation comments identify the
    exact precedence being changed and the commands affected.
  - Note: current `_scratch_path(slug)` precedence is `VICAYA_SCRATCH` ->
    `.active` -> slug -> error. This means `scratch_resume(<slug>)` can resolve
    the stale active scratch before the explicit slug. `scratch-log`,
    `scratch-gate`, and `scratch-verify` currently accept no CLI scratch/slug
    argument and rely on `VICAYA_SCRATCH` or `.active`; `_maybe_autolog` uses
    `VICAYA_SCRATCH` or `.active` and deliberately skips scratch helper
    commands plus `lookup-book`.

- [x] Inspect existing tests before adding new ones.
  - Read `tests/test_research_sources.py` for scratch helper fixtures and
    monkeypatch patterns.
  - Reuse existing fixture style where possible.
  - -> verify: proposed tests fit the existing test file without adding a new
    test framework or broad fixture rewrite.
  - Note: scratch tests are already grouped under `TestScratchDossier` and use
    `tmp_path`, monkeypatched `_SCRATCH_DIR`, direct helper imports, and env
    monkeypatching. New regression tests will reuse that style.

- [x] Add a failing regression test for explicit slug versus stale `.active`.
  - Arrange two scratch files, point `.active` at the first, then call
    `scratch_resume` or the relevant resolver with the second slug.
  - Expected behavior after the fix: the second scratch is selected.
  - -> verify: `UV_CACHE_DIR=/private/tmp/uv-cache uv run pytest tests/test_research_sources.py -q -k scratch` shows the new test fails before the implementation change and passes after it.
  - Note: pre-fix run failed as expected:
    `test_resume_slug_ignores_stale_active_state` returned `stale-run.md`
    instead of `selected-run.md`. The post-fix pass is covered by Phase 2
    verification.

## Phase 2 - Make Explicit Run Selection Reliable

- [x] Update scratch path resolution.
  - In `tools/research_sources.py`, change resolver semantics so explicit slug
    or explicit scratch argument cannot be overridden by `.active`.
  - Preserve environment support for commands that do not otherwise specify a
    target scratch.
  - Keep the change small and local; avoid renaming public commands unless a
    test shows it is necessary.
  - -> verify: the regression test from Phase 1 passes.

- [x] Make `scratch-resume <slug>` reattach helper state.
  - After resolving the selected scratch and computing the next phase, update
    `.active` to the selected scratch and next phase.
  - Handle completed runs without corrupting state; if there is no next phase,
    keep behavior explicit in the returned JSON.
  - -> verify: a focused test confirms `.active` points to the resumed scratch
    after `scratch_resume(<slug>)`.

- [x] Preserve manual logging and auto-logging behavior.
  - Confirm `scratch-log`, `scratch-gate`, and `_maybe_autolog` still use the
    intended scratch when `VICAYA_SCRATCH` is set.
  - Confirm unpinned commands may still use `.active` as the documented
    convenience fallback.
  - -> verify: `UV_CACHE_DIR=/private/tmp/uv-cache uv run pytest tests/test_research_sources.py -q -k scratch` passes.

- [x] Run scoped code-quality checks for touched Python files.
  - -> verify: `UV_CACHE_DIR=/private/tmp/uv-cache uv run ruff check tools/research_sources.py tests/test_research_sources.py` passes.
  - -> verify: `UV_CACHE_DIR=/private/tmp/uv-cache uv run pyright tools/research_sources.py tests/test_research_sources.py` passes, or any existing type-check limitation is recorded with the exact error.
  - Note: ruff passed. Pyright failed on existing optional-path checks in
    `tests/test_research_sources.py`, outside the scratch changes:
    line 42 `DEFAULT_CALIBRE_LIBRARY.exists()` and line 46
    `DEFAULT_CANON_DB.exists()` report `exists` is not a known attribute of
    `None` (`reportOptionalMemberAccess`).

## Phase 3 - Update Canonical Scratch Instructions

- [x] Update the scratchpad documentation in `skill/vicaya/SKILL.md`.
  - Clarify that explicit slug/path selection and `VICAYA_SCRATCH` are the safe
    ways to identify a run.
  - Clarify that `.active` is a single shared convenience pointer.
  - Clarify that parallel sessions still need an explicit run target because
    `.active` cannot represent multiple live researches.
  - Do not rewrite unrelated Vicaya phase instructions.
  - -> verify: `rg -n "scratch-resume|VICAYA_SCRATCH|\\.active|parallel" skill/vicaya/SKILL.md` shows the updated wording in the scratchpad section only.

- [x] Run scoped markdown and diff checks.
  - -> verify: `git diff --check -- tools/research_sources.py tests/test_research_sources.py skill/vicaya/SKILL.md kamma/threads/20260604_vicaya-parallel-scratch-state/spec.md kamma/threads/20260604_vicaya-parallel-scratch-state/plan.md` passes.

## Phase 4 - Final Verification And Handoff

- [x] Run final scoped verification.
  - -> verify: `UV_CACHE_DIR=/private/tmp/uv-cache uv run pytest tests/test_research_sources.py -q -k scratch` passes.
  - -> verify: `UV_CACHE_DIR=/private/tmp/uv-cache uv run ruff check tools/research_sources.py tests/test_research_sources.py` passes.

- [x] Summarize results for review.
  - Include files changed, exact validation run, any failed attempts, and any
    remaining risk around unpinned parallel auto-logging.
  - -> verify: `plan.md` task statuses and notes are accurate enough for
    `/kamma:3-review` to review the thread without relying on chat context.
  - Summary for review:
    - Changed `tools/research_sources.py`: `_scratch_path(slug)` now resolves
      explicit slug before `VICAYA_SCRATCH` and `.active`; `_write_state` can
      clear stale phase when passed `None`; `scratch_resume` now writes the
      selected scratch path and computed next phase back to `.active`.
    - Changed `tests/test_research_sources.py`: added scratch regression tests
      for stale `.active` versus explicit resume slug, resume reattaching active
      state, env-pinned auto-logging over stale state, and unpinned auto-logging
      through `.active`.
    - Changed `skill/vicaya/SKILL.md`: documented scratch target precedence,
      `scratch-resume <slug>` reattachment, and the rule that parallel sessions
      must pin `VICAYA_SCRATCH`.
    - Validation passed:
      `UV_CACHE_DIR=/private/tmp/uv-cache uv run pytest tests/test_research_sources.py -q -k scratch`
      (`15 passed, 56 deselected`);
      `UV_CACHE_DIR=/private/tmp/uv-cache uv run ruff check tools/research_sources.py tests/test_research_sources.py`
      (passed with existing top-level linter-settings deprecation warning);
      `git diff --check -- tools/research_sources.py tests/test_research_sources.py skill/vicaya/SKILL.md kamma/threads/20260604_vicaya-parallel-scratch-state/spec.md kamma/threads/20260604_vicaya-parallel-scratch-state/plan.md`
      (passed).
    - Failed/recorded checks:
      pre-fix regression test failed as expected before the implementation;
      pyright failed on existing `tests/test_research_sources.py` optional
      path checks at lines 42 and 46 (`reportOptionalMemberAccess`), unrelated
      to this scratch change.
    - Remaining risk: unpinned parallel helper auto-logging is still unsafe by
      design because `.active` is one shared pointer. Parallel sessions must set
      `VICAYA_SCRATCH`; this is now documented.
