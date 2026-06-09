## Thread
- **ID:** obsidian-cli-fix
- **Objective:** Fix two compounding bugs that caused every `/vicaya` run to report "Obsidian CLI couldn't connect even after launching the app"

## Files Changed
- `tools/research_sources.py` — `search_vault`: raise `RuntimeError` on non-JSON CLI output instead of silently returning `[]`
- `skill/vicaya/SKILL.md` — Hard Rule 4: replace broken Linux launch command and add Windows; fix trigger phrasing
- `tests/test_research_sources.py` — add `TestSearchVaultErrorHandling` (6 tests covering all error/success paths)

## Findings
| # | Severity | Location | What | Why | Fix |
|---|----------|----------|------|-----|-----|
| 1 | minor | `SKILL.md:35` | Trigger said "raises a RuntimeError" but agent sees a subprocess traceback | Imprecise — careful agent might not match | Rephrased to "exits with a traceback containing 'app may not be running'" |
| 2 | nit | `research_sources.py:189` | `(result.stderr or result.stdout)` — stderr always empty for this CLI, so ordering is misleading | No behavioral impact | Left as-is; correct by accident |

## Fixes Applied
- Finding 1 resolved: Hard Rule 4 trigger phrasing updated in `SKILL.md`

## Test Evidence
- `uv run ruff check tools/research_sources.py tests/test_research_sources.py` → All checks passed
- `uv run pyright tools/research_sources.py tests/test_research_sources.py` → 0 errors, 0 warnings
- `uv run pyrefly check --search-path . tools/research_sources.py tests/test_research_sources.py` → 0 errors
- `uv run pytest tests/test_research_sources.py -q` → 78 passed, 1 skipped
- `uv run pytest tests/test_research_sources.py -q -k SearchVault` → 6 passed

## Verdict
PASSED
- Review date: 2026-06-10
- Reviewer: Claude (same agent as implementor — reduced independence noted)
