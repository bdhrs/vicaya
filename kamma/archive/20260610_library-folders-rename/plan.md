# Plan — Rename "folder corpus" → "library folders" + collapse Calibre

Source of truth for this thread. Markers: `[ ]` todo · `[~]` in progress · `[x]` done.

## Decisions already confirmed with user
- Remove the standalone `calibredb` Calibre search subsystem entirely (B1).
- Tag/author search keeps working via the unified index (B2 stays — `_build_calibre_metadata_lookup` kept).
- Naming: `VICAYA_LIBRARY_FOLDERS` / `_INDEX` / `_EXCLUDE`; module `tools/library_folders.py`;
  CLI `library-folders-{check,refresh,duplicates}` + `search-library-folders`; justfile `lf-*`.
- Update real `.env` (explicit user permission); produce migration note for second user.
- Update active kamma thread `folder-corpus-archives` with new names.
- GRETIL "corpus" references are **NOT** touched (separate source, unrelated name).
- `kamma/archive/**` and `runs/**` are **NOT** touched (historical records).

## Phase 1 — Code module rename (`tools/`) ✅ DONE
- [x] `mv tools/folder_corpus.py tools/library_folders.py`
- [x] Docstring, `SOURCES_ENV/INDEX_ENV/EXCLUDE_ENV` values, class `FolderCorpusConfig` → `LibraryFoldersConfig` (all occurrences), `desc="folder-corpus refresh"` → `"library-folders refresh"`.

## Phase 2 — `tools/research_sources.py` ✅ DONE
- [x] Removed `search_calibre` from module docstring.
- [x] Removed `import unicodedata` + `_strip_diacritics` (only used by Calibre).
- [x] Removed `DEFAULT_CALIBRE_LIBRARY`, `CalibreHit` dataclass.
- [x] Removed entire `# ---------- Calibre search ----------` block (~400 lines).
- [x] Updated autolog string → `"library-folders-check called at phase start"`.
- [x] Renamed `_load_folder_corpus_module` → `_load_library_folders_module` (path `library_folders.py`, spec id `vicaya_library_folders`).
- [x] Renamed CLI parsers and dispatch: `folder-corpus-*` → `library-folders-*`, `search-folder-corpus` → `search-library-folders`.
- [x] Removed `search-calibre` + `calibre-check` parsers and dispatch branches.

## Phase 3 — Tests ✅ DONE
- [x] `mv tests/test_folder_corpus.py tests/test_library_folders.py`
- [x] Updated imports: `tools.folder_corpus` → `tools.library_folders`, `FolderCorpusConfig` → `LibraryFoldersConfig`
- [x] `ROOT_ENV` → `SOURCES_ENV`; `folder_corpus.` → `library_folders.`; `monkeypatch.setattr(folder_corpus,` → `library_folders,`
- [x] Fixed single-root API: `config.root` → `config.roots[0]`; `LibraryFoldersConfig(root=` → `roots=[`
- [x] Fixed `check()` assertions: `root_available`/`root_path` → `source_roots[0]["available"]`/`source_roots[0]["path"]`
- [x] Updated CLI test function name + command strings + env var
- [x] `tests/test_research_sources.py`: removed Calibre imports, `_calibre_library_present`, `calibre_available`, `_build_calibre_metadata_db`, `TestSearchCalibre`, `TestCalibreReadOnlySqlite`, `TestCalibreCheckHonesty`, `TestCalibreFtsFallback`. Removed now-unused `import subprocess`.

## Phase 4 — Config ✅ DONE
- [x] `.env.example`: dropped `VICAYA_CALIBRE_LIBRARY` block; renamed folder-corpus vars; rewrote comments.
- [x] Real `.env`: `VICAYA_CALIBRE_LIBRARY` removed; `VICAYA_FOLDER_CORPUS_ROOT` → `VICAYA_LIBRARY_FOLDERS=~/MyFiles/2_Resources/Libraries`; `_INDEX` and `_EXCLUDE` renamed.
- [x] `justfile`: comment + `fc-*` recipes → `lf-*`; updated CLI command names.

## Phase 5 — Docs ✅ DONE
- [x] `kamma/project.md`: "Calibre library" → "library folders" (2 occurrences).
- [x] `kamma/tech.md`: merged "Library search" + "Folder corpus search" → "Library folders search"; updated Resources env vars + constraints + Documentation Ownership.
- [x] `README.md`: removed standalone Calibre section; rewrote as "Library folders search"; fixed env block, dir tree, autonomous setup section.
- [x] `skill/vicaya/SKILL.md`: ALL changes done by subagent — removed `search-calibre`/`calibre-check` tool rows, `CalibreHit` struct, Calibre source entry; updated mandatory search rule; converted per-route guidance; updated CLI examples; updated checklist items. Verified clean: `rg 'search-calibre|calibre-check|VICAYA_CALIBRE|FOLDER_CORPUS' skill/vicaya/SKILL.md` returns NOTHING.
- [x] `skill/vicaya/README.md`: "Calibre library" → "library folders"; Phase 3 description updated; `calibredb` dependency row removed; "Calibre FTS" limitation block removed.

## Phase 6 — kamma thread rename + migration ✅ DONE
- [x] `mv kamma/threads/folder-corpus-archives kamma/threads/library-folders-archives`
- [x] Updated spec.md, plan.md, handoff.md: all `folder_corpus.py`, `folder-corpus`, `fc-refresh`, titles updated to library-folders equivalents.
- [x] `kamma/threads/library-folders-rename/migration.md` written — steps for second user.

## Phase 7 — Validation ✅ DONE
- [x] ruff: all checks passed.
- [x] pyright: 0 errors (pre-existing `_find_agama_path` nullability fixed; `textutil` unreachable is platform-only, pre-existing).
- [x] pyrefly: 0 errors (12 suppressed, pre-existing).
- [x] pytest: 110 passed, 1 skipped. Fixed 4 bugs found during validation:
  - 2 remaining `root=` → `roots=[...]` in test_library_folders.py (lines 129, 408).
  - `_strip_diacritics` moved out of shared_helper into library_folders.py (removed from research_sources.py in Phase 2 but still called via shared_helper).
  - `source_root` added to manual INSERT in test_library_folders.py line 177.
  - `_exact_duplicate_map` extended to `(id, source_path, rel_path)` tuples so `duplicate_paths` returns relative paths (tests expected rel_path, code returned source_path).
- [x] Final sweep: all matches are inside `kamma/threads/library-folders-rename/` (intentional — the rename thread's own docs reference old names). No old refs in code, tests, env, docs, or skill files.

## Phase 8 — Review + finalize ✅ DONE
- [x] Self-review complete — all findings fixed inline during Phase 7 validation.
- [x] Ready for user review; awaiting explicit commit permission.

## Open question (not part of this thread)
User asked: "Should we fold the GRETIL Sanskrit library into the unified library-folders index?" — decided NO for now (separate decision, different use pattern). Do not act on this here.

## Notes for next session
- `skill/vicaya/README.md` is the only file still needing edits (Phase 5 last item).
- Then Phase 6 (thread rename + migration.md).
- Then validation run.
- The pyright "module not found" errors for `tools.library_folders` and `weasyprint` are expected false-positives at static analysis time — pytest finds them fine via `sys.path`.
- Pre-existing pyright issues in `test_research_sources.py` (lines 463-464 re `_find_agama_path`) are unrelated to this rename; leave them.
