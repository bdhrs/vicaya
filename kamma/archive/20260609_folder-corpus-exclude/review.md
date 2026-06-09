## Thread
- **ID:** 20260609_folder-corpus-exclude
- **Objective:** Add an optional folder-exclusion list to the unmanaged folder-corpus refresh.

## Files Changed
- `tools/folder_corpus.py` — `EXCLUDE_ENV`, `FolderCorpusConfig.exclude`, `_env_excludes`, `_is_excluded`, directory pruning in `_iter_files`, wired into `refresh`, and `exclude_paths` in `check`.
- `tests/test_folder_corpus.py` — config parse (comma-separated + `~`), unset-empty, refresh skips excluded subtree, unbounded refresh drops newly-excluded rows, `check` reports excludes.
- `.env.example`, `README.md`, `kamma/tech.md` — document `VICAYA_FOLDER_CORPUS_EXCLUDE`.
- `.env` (live, gitignored, user-approved) — exclude `~/MyFiles/2_Resources/Libraries/Bodhirasa eBook Library`.

## Findings
No unresolved findings.

- Backward compatible: `exclude` defaults to `()`; all 21 pre-existing tests still pass.
- Pruning happens at the `os.walk` directory level, so excluded subtrees are never descended into (no wasted hashing/extraction).
- Exclusion is refresh-time only; `search`/`duplicates` read the index and stay consistent. On an unbounded refresh, rows previously indexed under a newly-excluded folder are removed by the existing delete-missing pass.

## Test Evidence
- `uv run ruff check tools/folder_corpus.py tests/test_folder_corpus.py` → pass.
- `uv run pyright tools/folder_corpus.py tools/research_sources.py tests/test_folder_corpus.py` → 0 errors, 0 warnings.
- `uv run pyrefly check --search-path . …` → 0 errors (12 suppressed).
- `uv run pytest tests/test_folder_corpus.py -q -rs` → 26 passed, 1 skipped (PDF test; `weasyprint`/`pdftotext` env-dependent).
- `uv run tools/research_sources.py folder-corpus-check` → live config reports `exclude_paths: ["/home/bodhirasa/MyFiles/2_Resources/Libraries/Bodhirasa eBook Library"]`, `root_available: true`.

## Note
- The configured index `~/MyFiles/2_Resources/Libraries.sqlite` exists schema-only (0 docs) from an interrupted earlier refresh. Harmless; the next full `folder-corpus-refresh` populates it incrementally and now skips the excluded Calibre subtree. No live refresh was run during this thread (121 GB tree, multi-hour).

## Verdict
PASSED
- Review date: 2026-06-09
- Reviewer: Claude (Opus 4.8)
