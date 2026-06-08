## Thread
- **ID:** 20260608_folder-corpus-search
- **Objective:** Add an indexed unmanaged file-tree corpus source independent of Calibre.

## Files Changed
- `.env.example` - adds folder corpus root/index configuration placeholders.
- `.gitignore` - ignores local SQLite indexes and duplicate evidence output.
- `README.md` - documents setup, behavior, and new-machine build/verification for the separate folder corpus source.
- `kamma/tech.md` - records folder corpus architecture and production index path.
- `skill/vicaya/SKILL.md` - adds search/refresh commands and research guidance.
- `tools/research_sources.py` - wires folder corpus CLI subcommands.
- `tools/folder_corpus.py` - implements config, schema, refresh, search, duplicates, extraction, and unreadable-file handling.
- `tests/test_folder_corpus.py` - covers config, refresh, search, duplicates, extraction, CLI JSON, and read-error handling.
- `kamma/threads/20260608_folder-corpus-search/*` - thread plan, decision, evidence, handoff, and review records.

## Findings
No unresolved findings.

## Fixes Applied
- Removed earlier dead `OFFICE_ZIP_EXTENSIONS` constant.
- Resolved the operational blocker by creating `/Users/deva/server-library/`, preserving the 25-document legacy DB, and placing the configured production index at `/Users/deva/server-library/noncanonical-english.sqlite`.
- Added refresh resilience for per-file stat/read/extraction errors so one bad corpus file cannot abort the full refresh.
- Moved the one-time migration script out of the repository to `/private/tmp/migrate_folder_corpus_index.sh`; the committed feature now relies only on env-configured paths.
- Added README instructions for building and verifying the folder corpus index on a new machine.

## Test Evidence
- `UV_CACHE_DIR=/private/tmp/uv-cache uv run ruff check tools/folder_corpus.py tools/research_sources.py tests/test_folder_corpus.py` -> pass.
- `UV_CACHE_DIR=/private/tmp/uv-cache uv run pyright tools/folder_corpus.py tools/research_sources.py tests/test_folder_corpus.py` -> pass.
- `UV_CACHE_DIR=/private/tmp/uv-cache uv run pyrefly check --search-path . tools/folder_corpus.py tools/research_sources.py tests/test_folder_corpus.py` -> pass; pyrefly used preset `basic`.
- `UV_CACHE_DIR=/private/tmp/uv-cache uv run pytest tests/test_folder_corpus.py -q -rs` -> pass, `21 passed, 1 skipped`; skipped PDF extraction because `pdftotext` is absent.
- `coderabbit review --agent` -> pass, 0 findings after fixes; limited/free CLI mode.
- `rg -n "folder-corpus-refresh|search-folder-corpus|folder-corpus-duplicates|pdftotext|metadata-only" README.md` -> pass; README includes new-machine build/use instructions and extraction coverage caveat.
- `UV_CACHE_DIR=/private/tmp/uv-cache uv run tools/research_sources.py folder-corpus-refresh` -> pass; `indexed: 37448`, `written: 36448`, `skipped: 1000`, `text_extracted: 19771`, `metadata_only: 16677`, `error_count: 0`, `limited: false`.
- `UV_CACHE_DIR=/private/tmp/uv-cache uv run tools/research_sources.py folder-corpus-check` -> pass; configured index exists with `document_count: 37448`.
- `UV_CACHE_DIR=/private/tmp/uv-cache uv run tools/research_sources.py search-folder-corpus "dhamma" --limit 5` -> pass; returned hits from the configured index with `source_available: true`.
- `UV_CACHE_DIR=/private/tmp/uv-cache uv run tools/research_sources.py folder-corpus-duplicates --samples 10` -> pass; diagnostic completed against the configured index.
- Duplicate summary from `duplicates(samples=0)` -> pass; content-hash clusters 1937/6377 files, text-hash clusters 1619/6069 files, non-text duplicate candidates 11487 files.

## Verdict
PASSED
- Review date: 2026-06-08
- Reviewer: Codex
