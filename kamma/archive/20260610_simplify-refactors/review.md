## Thread
- **ID:** 20260610_simplify-refactors
- **Objective:** Implement safe simplification refactors from the 2026-06-10 full-repo analysis with no behavior change.

## Files Changed
- `.gitignore` — removed obsolete root agent-note ignore entries.
- `kamma/tech.md` — moved scoped validation policy into Kamma tech docs.
- `kamma/workflow.md` — moved finalize/archive cleanup guidance into workflow docs.
- `tests/test_research_sources.py` — mocked Gemini subprocess call; updated scratch monkeypatch targets.
- `tools/_common.py` — added shared repo-root, dotenv, env-path, and XML-strip helpers.
- `tools/library_folders.py` — rewired duplicated common helpers to `tools._common`.
- `tools/note_checks.py` — kept public `load_dotenv(path) -> dict` as a shared-parser wrapper.
- `tools/research_sources.py` — delegated scratch subsystem and converted CLI to handler dispatch.
- `tools/scratch.py` — extracted scratch-dossier state, gate, resume, verify, and autolog logic.

## Findings
| # | Severity | Location | What | Why | Fix |
|---|----------|----------|------|-----|-----|
| 1 | minor | `tests/test_research_sources.py:40` | `gemini_available` skip marker was orphaned after mocking the Gemini test. | Dead test helper made the live-CLI dependency look partly preserved. | Removed the unused marker during review. |

## Fixes Applied
- Removed the orphaned `gemini_available` skip marker from `tests/test_research_sources.py`.

## Test Evidence
- `coderabbit review --agent` -> pass, 0 findings.
- `uv run pytest tests/test_research_sources.py -q` -> expected fail: 1 Obsidian-unavailable test, 67 passed, 11 skipped.
- `uv run pytest tests/test_research_sources.py -q -k 'not test_search_returns_list'` -> pass, 67 passed, 11 skipped, 1 deselected.
- `uv run pytest tests/test_cross_check.py tests/test_library_folders.py tests/test_note_checks.py tests/test_validate_note.py tests/test_generate_note_pdf.py -q` -> pass, 83 passed, 3 skipped.
- `uv run ruff check tools/_common.py tools/scratch.py tools/research_sources.py tools/library_folders.py tools/note_checks.py tests/test_research_sources.py` -> pass.
- `uv run pyright tools/_common.py tools/scratch.py tools/research_sources.py tools/library_folders.py tools/note_checks.py tests/test_research_sources.py` -> pass.
- `uv run pyrefly check --search-path . tools/_common.py tools/scratch.py tools/research_sources.py tools/library_folders.py tools/note_checks.py tests/test_research_sources.py` -> pass, 0 errors.
- `uv run tools/research_sources.py --help` -> pass; all 24 subcommands present.
- Scratch smoke and env-pinned `scratch-which` -> pass using temporary paths.
- `git diff --check` -> pass.

## Verdict
PASSED
- Review date: 2026-06-10
- Reviewer: Codex
