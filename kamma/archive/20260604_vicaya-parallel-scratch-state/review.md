## Thread
- **ID:** 20260604_vicaya-parallel-scratch-state
- **Objective:** Make Vicaya scratch run state safe for parallel and restarted sessions.

## Files Changed
- `tools/research_sources.py` — updates scratch target precedence, resume reattachment, and shared next-phase resolution.
- `tests/test_research_sources.py` — adds focused scratch resolver, resume, and auto-log regression tests.
- `skill/vicaya/SKILL.md` — documents explicit scratch selection, `.active` fallback, and parallel-run pinning.
- `kamma/threads/20260604_vicaya-parallel-scratch-state/spec.md` — records thread scope and acceptance criteria.
- `kamma/threads/20260604_vicaya-parallel-scratch-state/plan.md` — records implementation steps and verification notes.

## Findings
| # | Severity | Location | What | Why | Fix |
|---|----------|----------|------|-----|-----|
| 1 | major | `tools/research_sources.py:2135` | `scratch_resume` persisted a plain next phase, so thematic runs gated through Phase 2 would resume into auto-skipped Phase 2.5. | A restarted thematic run could route later auto-logs into a skipped phase, breaking existing phase semantics. | Added `_next_worked_phase`, reused it from `scratch_gate` and `scratch_resume`, and added a thematic resume regression test. |

## Fixes Applied
- Factored next worked phase calculation into `_next_worked_phase`.
- Updated `scratch_resume` to preserve thematic auto-skip behavior when reattaching `.active`.
- Added `test_resume_thematic_run_reattaches_next_worked_phase`.

## Test Evidence
- `UV_CACHE_DIR=/private/tmp/uv-cache uv run pytest tests/test_research_sources.py -q -k scratch` -> pass, `16 passed, 56 deselected`
- `UV_CACHE_DIR=/private/tmp/uv-cache uv run ruff check tools/research_sources.py tests/test_research_sources.py` -> pass, with existing top-level linter-settings deprecation warning
- `git diff --check -- tools/research_sources.py tests/test_research_sources.py skill/vicaya/SKILL.md kamma/threads/20260604_vicaya-parallel-scratch-state/spec.md kamma/threads/20260604_vicaya-parallel-scratch-state/plan.md` -> pass
- `UV_CACHE_DIR=/private/tmp/uv-cache uv run pyright tools/research_sources.py tests/test_research_sources.py` -> fail on existing optional member checks in `tests/test_research_sources.py:42` and `tests/test_research_sources.py:46`
- `coderabbit review --agent` -> pass, `findings: 0` in limited/free CLI mode

## Verdict
PASSED
- Review date: 2026-06-04
- Reviewer: Codex
