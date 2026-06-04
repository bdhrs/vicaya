# Plan — Calibre read-only SQLite metadata search (closes #9)

## GitHub issue: closes #9

## Architecture Decisions
- **Read-only SQLite, mirroring the canon-DB pattern** already in this file — no new
  abstraction, same `sqlite3.connect("file:...?mode=ro", uri=True)` idiom.
- **Graceful fallback over version-check.** On schema error, metadata search calls the
  preserved `_calibre_metadata_search_cli()` (today's implementation, renamed). Simpler
  and more robust than parsing Calibre versions.
- **WHERE uses EXISTS subqueries** for author/tag/comment matching (clear, no JOIN
  fan-out duplicates); tags returned via `group_concat(..., char(31))` split on the
  unit separator to avoid comma-in-tag fragility — single query, no N+1.
- FTS path and `search_calibre` dispatcher untouched.

## Phase 1 — Read-only metadata search (common case)
- [x] Add `_calibre_metadata_db_path(library)` and a small read-only connect helper
  → verify: `uv run python -c "import tools.research_sources"` imports clean
- [x] Rename current `_calibre_metadata_search` → `_calibre_metadata_search_cli`
  (unchanged body), kept as the schema-error fallback
  → verify: ruff check passes, no other references break (`rg _calibre_metadata_search`)
- [x] Implement new `_calibre_metadata_search()` using read-only SQLite: free-text
  LIKE across title/authors/tags/comments, optional exact tag filter, LIMIT; build
  CalibreHit identically; on sqlite3.OperationalError/DatabaseError → call
  `_calibre_metadata_search_cli`
  → verify: new test `test_metadata_search_reads_sqlite_readonly` builds a temp
    metadata.db with 2 books/tags/comments, asserts query + tag-filter hits, runs
    with no calibredb on PATH
- [x] Phase verification
  → verify: `uv run pytest tests/test_research_sources.py -q -k calibre` passes

## Phase 2 — Read-only preflight probe
- [x] Rewrite `calibre_library_available()` to open metadata.db read-only and run
  `SELECT count(*) FROM books`; missing db or error → (False, message)
  → verify: new test asserts (True,"ok") on a temp metadata.db and (False, …) when absent
- [x] Update `TestCalibreCheckHonesty` (3 tests) — they assert the old `calibredb list`
  probe via `_run_calibre`; rewrite to assert the read-only SQLite probe and no lock use
  → verify: `uv run pytest tests/test_research_sources.py -q -k "CalibreCheck or calibre"` passes
- [x] Phase verification
  → verify: full `uv run pytest tests/test_research_sources.py -q` passes

## Phase 3 — Final verification & docs
- [x] Update `kamma/tech.md` library line to note metadata search uses read-only SQLite
  → verify: line reads correctly
- [x] Full gate
  → verify: `uv run ruff check tools/research_sources.py tests/test_research_sources.py`
    and `uv run pyright tools/research_sources.py` both clean; full pytest green
