# Handoff - folder corpus search operational completion

## Current State

The folder-corpus implementation exists and code-level validation passed, but
the thread is **not ready to finalize**. The active review is intentionally
`BLOCKED` because the configured production index is not yet operational.

The user wants the index under:

`/Users/deva/server-library/noncanonical-english.sqlite`

The project `.env`, thread `spec.md`, and thread `plan.md` have been updated to
that path. Stale references to `/Users/deva/Documents/server-library` were
removed except where documenting the source of the old sample index to migrate.

## Important Sandbox Note

Earlier in this session, writing under `/Users/deva/server-library` failed:

`mv: rename /Users/deva/server-library to /Users/deva/server-library.legacy-25docs.sqlite: Operation not permitted`

The user says they have now added `/Users/deva/server-library` to the sandbox,
but the current session likely cannot see the updated writable root until
restart. On restart, verify write access before continuing.

## What Was Done

- Added/kept `tools/folder_corpus.py` for unmanaged folder-corpus indexing and
  search.
- Wired CLI commands in `tools/research_sources.py`:
  - `folder-corpus-check`
  - `folder-corpus-refresh`
  - `search-folder-corpus`
  - `folder-corpus-duplicates`
- Added tests in `tests/test_folder_corpus.py`.
- Added `scripts/migrate_folder_corpus_index.sh` to move existing SQLite files
  into `/Users/deva/server-library/` once sandbox access allows it.
- Changed `kamma/threads/20260608_folder-corpus-search/review.md` to `BLOCKED`
  and added the operational blocker.
- Added “Post-Review Operational Completion” tasks to `plan.md`.

## Current Verified Status Before Restart

`folder-corpus-check` returned:

- `root_available: true`
- `index_path: /Users/deva/server-library/noncanonical-english.sqlite`
- `index_exists: false`
- `document_count: null`

Filesystem state before restart:

- `/Users/deva/server-library` was a SQLite file with 25 documents.
- `/Users/deva/Documents/server-library/noncanonical-english.sqlite` was a
  1000-document sample index.

## Next Steps After Restart

1. Verify sandbox write access and current filesystem state:

```sh
ls -ld /Users/deva/server-library /Users/deva/Documents/server-library 2>/dev/null || true
UV_CACHE_DIR=/private/tmp/uv-cache uv run tools/research_sources.py folder-corpus-check
```

2. Run the migration script if `/Users/deva/server-library` is still a file or
   the sample index is still under Documents:

```sh
sh scripts/migrate_folder_corpus_index.sh
```

3. Verify the migrated sample index:

```sh
UV_CACHE_DIR=/private/tmp/uv-cache uv run tools/research_sources.py folder-corpus-check
```

Expected interim result: `index_exists: true`, `document_count: 1000`.

4. Run the full unbounded refresh. Do not pass `--limit`:

```sh
UV_CACHE_DIR=/private/tmp/uv-cache uv run tools/research_sources.py folder-corpus-refresh
```

This is the operation that makes the tool operational for the real corpus. It
will walk and hash the full mounted source tree, so it may take time.

5. Verify operational completion:

```sh
UV_CACHE_DIR=/private/tmp/uv-cache uv run tools/research_sources.py folder-corpus-check
UV_CACHE_DIR=/private/tmp/uv-cache uv run tools/research_sources.py search-folder-corpus "dhamma" --limit 5
UV_CACHE_DIR=/private/tmp/uv-cache uv run tools/research_sources.py folder-corpus-duplicates --samples 10
```

The final `document_count` should reflect the real accepted corpus, not 25 and
not the bounded 1000-file sample.

6. Update the post-review tasks in `plan.md`, rerun `/kamma:3-review`, and only
   then finalize with `/kamma:4-finalize`.

## Validation Already Run

These passed before the operational blocker was discovered:

- `UV_CACHE_DIR=/private/tmp/uv-cache uv run ruff check tools/folder_corpus.py tools/research_sources.py tests/test_folder_corpus.py`
- `UV_CACHE_DIR=/private/tmp/uv-cache uv run pyright tools/folder_corpus.py tools/research_sources.py tests/test_folder_corpus.py`
- `UV_CACHE_DIR=/private/tmp/uv-cache uv run pyrefly check --search-path . tools/folder_corpus.py tools/research_sources.py tests/test_folder_corpus.py`
- `UV_CACHE_DIR=/private/tmp/uv-cache uv run pytest tests/test_folder_corpus.py -q -rs`
- `coderabbit review --agent` returned 0 findings.
- `sh -n scripts/migrate_folder_corpus_index.sh` passed.

## Key Point

Do not mark this thread complete just because the code is reviewed. It is
complete only when the configured production index exists at
`/Users/deva/server-library/noncanonical-english.sqlite`, has been refreshed
without `--limit`, and search works from that configured index.
