## Thread
- **ID:** 20260604_calibre-ro-sqlite
- **Objective:** Read Calibre metadata.db directly (read-only SQLite) for metadata search + preflight, removing calibredb lock contention for concurrent /vicaya runs (closes #9).

## Files Changed
- `tools/research_sources.py` — new read-only SQLite `_calibre_metadata_search`; old CLI path preserved as `_calibre_metadata_search_cli` fallback; `calibre_library_available` probes metadata.db read-only; added `_calibre_metadata_db_path`.
- `tests/test_research_sources.py` — added `TestCalibreReadOnlySqlite` (hermetic temp-db tests) + `_build_calibre_metadata_db`; rewrote `TestCalibreCheckHonesty` for the SQLite probe.
- `kamma/tech.md` — library-search line now documents read-only SQLite metadata path.

## Findings
| # | Severity | Location | What | Why | Fix |
|---|----------|----------|------|-----|-----|
| 1 | nit | `research_sources.py` except clause | `(OperationalError, DatabaseError)` was redundant — OperationalError is a subclass of DatabaseError | Cleaner | Simplified to `except sqlite3.DatabaseError` |

Correctness: all SQL parameterized (no injection); connections closed via try/finally on every path; missing/corrupt db → graceful fallback (search) or (False, msg) (preflight). Architecture: mirrors existing canon-DB read-only pattern. Security: read-only URI, no writes possible. Performance: single query, correlated subqueries bounded by LIMIT — measured 12–24ms per search. No dead code (CLI path retained as safety net; `_run_calibre`/`CalibreUnavailable` still used by FTS + fallback).

## Fixes Applied
- Simplified the schema-error except clause to `sqlite3.DatabaseError` (finding #1).

## Test Evidence
- `pytest -k "calibre or Calibre"` → 10 passed, 1 skipped (real-library gated)
- full `pytest tests/test_research_sources.py` → 75 passed, 1 skipped
- `ruff check` (tools + tests) → pass
- `pyright tools/research_sources.py` → 0 errors
- Live real-library: `calibre-check` → ok; metadata search returned real hits + snippets + tag filtering; 5 concurrent searches completed in 25ms total wall with a trip-wire confirming the calibredb lock path was never entered.

## Verdict
PASSED
- Review date: 2026-06-04
- Reviewer: kamma (inline)
