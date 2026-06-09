# Spec — Rename "folder corpus" → "library folders" + collapse Calibre into it

## Goal
Eliminate the name "folder corpus" everywhere (code, env, docs, skill, justfile,
tests, kamma thread) and replace it with **library folder(s)**. At the same time,
stop treating a Calibre library as a *separate source*: a Calibre library is now
just one kind of library folder, indexed into the same unified SQLite FTS5 index.

## Decisions (confirmed with user)
1. **Remove the standalone Calibre search subsystem (the `calibredb` path).**
   Delete `search_calibre`, `calibre_library_available`, `CalibreHit`,
   `CalibreUnavailable`, all `_calibre_*` helpers, the `_run_calibre` /
   `_calibre_serialize` lock machinery, the `VICAYA_CALIBRE_LIBRARY` env var, and
   the `search-calibre` / `calibre-check` CLI subcommands.
2. **Tag/author search keeps working through the unified index.** It already does:
   `tools/library_folders.py::_build_calibre_metadata_lookup()` reads a library's
   `metadata.db` during refresh and prepends `[Calibre #id | Authors: … | Tags: …]`
   to each book's FTS text. That mechanism **stays** — Calibre tags/authors are
   searchable as part of the index. (User: "the new search must integrate search in
   calibre tags, those will be included in the latest db build.")
3. **Naming.** The library folders *are* the sources:
   - `VICAYA_FOLDER_CORPUS_SOURCES` → `VICAYA_LIBRARY_FOLDERS`
   - `VICAYA_FOLDER_CORPUS_INDEX`   → `VICAYA_LIBRARY_FOLDERS_INDEX`
   - `VICAYA_FOLDER_CORPUS_EXCLUDE` → `VICAYA_LIBRARY_FOLDERS_EXCLUDE`
   - module `tools/folder_corpus.py` → `tools/library_folders.py`
   - test `tests/test_folder_corpus.py` → `tests/test_library_folders.py`
   - class `FolderCorpusConfig` → `LibraryFoldersConfig`
   - CLI `folder-corpus-check|refresh|duplicates` → `library-folders-check|refresh|duplicates`
   - CLI `search-folder-corpus` → `search-library-folders`
   - justfile `fc-*` recipes → `lf-*`
4. **The stale `VICAYA_FOLDER_CORPUS_ROOT`** (only in README + the real `.env`,
   never read by code) disappears, folded into `VICAYA_LIBRARY_FOLDERS`.
5. **Update the real `.env`** (overriding the usual "don't touch .env" rule, by
   explicit user permission) and produce a **migration plan** for the second user.
6. **Update the active kamma thread** `folder-corpus-archives` with the new names.

## Kept deliberately (provenance, not a "separate source")
- The `Calibre #<id>` label inside index FTS text and the citation footnote
  convention `[^calibre-<id>]` stay: the id is the book's stable identity from the
  library's `metadata.db`, not a second search source. Calibre-metadata enrichment
  during refresh (`_build_calibre_metadata_lookup`, the `metadata.db` detection in
  `check()`) stays. **Flag at review** in case the user wants these renamed too.
- `data/calibre_tags.csv` stays (real tag vocabulary of the library).

## Out of scope / left as historical
- `kamma/archive/**` (completed, archived threads) — historical record, not rewritten.
- The GRETIL "corpus" (`VICAYA_GRETIL_PATH`, `search-sanskrit`) — unrelated source,
  must NOT be renamed.

## Acceptance
- `rg -i 'folder.corpus|folder_corpus|VICAYA_CALIBRE|search.calibre|calibre.check'`
  returns nothing outside `kamma/archive/**`.
- `uv run pytest -q`, `ruff`, `pyright`, `pyrefly` all clean on touched files.
- README, SKILL.md, tech.md, project.md, justfile, .env.example, .env all describe a
  single "library folders" source; no standalone Calibre source remains.
- A migration note exists for the second user.
