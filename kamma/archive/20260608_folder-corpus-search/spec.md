# Spec - Indexed File-Tree Research Source

## Overview

Add a separate Vicaya source helper for unmanaged book/document folders. This
must be independent of Calibre: it does not read Calibre metadata, does not call
`calibredb`, and does not require the folder to be a Calibre library.

The new source should support the same practical research pattern Vicaya
currently gets from Calibre:

1. The actual files may live anywhere: local disk, mounted server path, NAS,
   external drive, etc.
2. Vicaya keeps a local searchable database/index.
3. Research runs query the local index quickly.
4. The original source file is accessed only when a researcher/agent needs
   deeper context, extraction, or verification.

Primary motivating source path:

`/Users/deva/filesrv1/share2/Textual/Non-Canonical English/`

A quick probe showed this tree is large, around 13,950 files, and includes
`.htm`, `.html`, `.pdf`, `.doc`, `.txt`, `.mht`, `.mobi`, `.epub`, `.azw3`,
plus web assets and other formats. Live traversal is slow enough that repeated
direct server search should not be the research hot path. Note that on a network
mount the dominant first-refresh cost is reading every file to hash it, not text
extraction; the incremental design below exists primarily to make that a
one-time cost.

## What It Should Do

Create a file-tree corpus tool with these capabilities:

- Configure an unmanaged file-tree corpus through local `.env` values.
- Build and refresh a local SQLite database for the corpus.
- Store document metadata:
  - absolute source path
  - relative path under source root
  - filename
  - extension
  - parent folders / inferred category path
  - file size
  - mtime
  - file content hash (SHA-256 of the bytes)
  - text hash (hash of the normalized extracted text, when text exists)
  - extraction status
  - indexed timestamp
- Extract searchable text where practical using Python stdlib-friendly
  approaches and optional already-present local tools.
- Build a SQLite FTS5 index over the extracted text.
- Make full-text matching diacritic-insensitive in both directions (see
  Diacritic Handling).
- Provide a CLI search command returning JSON hits with snippets.
- Return enough source information for an agent to cite or inspect the original
  file later.
- Avoid duplicate research by grouping exact-duplicate files at index time.

There is one corpus per index database. The index file path *is* the corpus
identity, so no `corpus_id` column is needed in the MVP. Multiple corpora can be
added later by pointing the same functions at different root/index pairs; the
implementation keeps these as parameters rather than hardcoded globals so no
redesign is required.

Suggested CLI shape (matches the existing `search-calibre` / `calibre-check`
naming precedent):

```bash
uv run tools/research_sources.py folder-corpus-refresh [--limit N]
uv run tools/research_sources.py search-folder-corpus "<query>" --limit 20 [--include-duplicates]
uv run tools/research_sources.py folder-corpus-check
uv run tools/research_sources.py folder-corpus-duplicates [--samples N]
```

`folder-corpus-refresh --limit N` indexes at most N files; this exists so a
bounded smoke test never has to trigger a full server walk.

### Configuration

The MVP uses `.env` values, matching Vicaya's existing path-based setup style:

```env
VICAYA_FOLDER_CORPUS_ROOT=/Users/deva/filesrv1/share2/Textual/Non-Canonical English
VICAYA_FOLDER_CORPUS_INDEX=/Users/deva/server-library/noncanonical-english.sqlite
```

`VICAYA_FOLDER_CORPUS_ROOT` is the actual file tree. It may be local or
server-mounted.

`VICAYA_FOLDER_CORPUS_INDEX` is the local SQLite database used for fast search.
Normal research searches this database and should not walk the source tree. The
index must live at a user-controlled local path outside the repository (the
example above is outside git); no default index path may resolve inside the repo.

If extraction caches are needed in a later iteration, add:

```env
VICAYA_FOLDER_CORPUS_CACHE=/Users/deva/server-library/cache
```

The cache is not required for the MVP. The index database remains the required
local search artifact.

### Schema (kept deliberately small)

Two tables plus a tiny metadata table:

- `documents` — one row per indexed file: metadata fields listed above, plus the
  SHA-256 `content_hash`.
- `document_fts` — an FTS5 virtual table holding the extracted text, with
  `rowid = documents.id`. It stores the **original** extracted text (diacritics
  preserved) so snippets display correctly; matching is folded by the tokenizer.
  Created as:
  `CREATE VIRTUAL TABLE document_fts USING fts5(text, tokenize="unicode61 remove_diacritics 2")`.
- `index_meta` — small key/value table for schema version and last-refresh
  timestamp.

`documents` carries both `content_hash` (SHA-256 of the bytes) and `text_hash`
(hash of the normalized extracted text, null when no text was extracted). There
is intentionally no separate `document_text` table (FTS5 already stores the text)
and no separate `duplicate_groups` table (a duplicate group is simply rows
sharing a hash, derived with `GROUP BY` at query time).

### Diacritic Handling

Pāḷi terms appear both with full diacritics (`paṭiccasamuppāda`, `nibbāna`) and,
especially in English secondary literature, in simplified ASCII form
(`paticcasamuppada`, `nibbana`). Search must match across this gap in **both
directions**: a diacritic query must find simplified text and vice versa.

This is achieved by the FTS5 `unicode61 remove_diacritics 2` tokenizer, which
folds diacritics during both indexing and querying. Because the stored text is
the original, returned snippets retain the author's original spelling while
matching is diacritic-insensitive. No manual diacritic folding of the stored
text or the query is required.

### Duplicate Handling

The corpus is expected to contain the same book under slightly different names
and possibly different formats, but the exact shape of that duplication is not
known up front. So duplicate handling is **tiered by confidence**, and the
filename/format patterns are discovered empirically (see Duplicate
Investigation) rather than guessed.

Two hashes are computed during refresh and reused incrementally (see Source
Access Model):

- `content_hash` — SHA-256 of the file bytes.
- `text_hash` — hash of the normalized extracted text, when text exists. (This
  is computed from text we already extract for the FTS index, so it adds no new
  read or extraction cost.)

Tiers:

- **Exact content (auto-suppressed by default).** A duplicate group is the set
  of `documents` rows sharing a `content_hash`, *or* sharing a non-null
  `text_hash`. Both mean "the same content": identical bytes, or identical
  readable text under different bytes/metadata/filename. Search returns one
  representative per group by default (lexicographically first `rel_path`). Each
  hit includes `duplicate_count` and the duplicate paths when duplicates exist.
  `--include-duplicates` returns every member.
- **Weak signals (surfaced, never auto-hidden).** Files that are *not* exact
  matches but look related — same file size, or near-identical normalized
  filename (case- and diacritic-folded, extension and trailing copy/version
  tokens stripped), or same title — are reported on the hit as
  `possible_duplicate_of` hints. They are never suppressed; the research agent
  decides whether they are the same work. This matches the expectation that an
  intelligent agent recognizes same-book duplicates that no exact hash can
  prove.

Fuzzy text-similarity scoring and any auto-suppression beyond exact-content
hashes are out of scope for this thread. Whether any weak signal proves reliable
enough to promote to default suppression is decided from the investigation
findings at review, not assumed now.

### Duplicate Investigation

Because the real duplication pattern is unknown, this thread includes a
read-only diagnostic, `folder-corpus-duplicates`, that surveys the existing
index and reports, for each grouping key, how many clusters and files are
involved plus a sample of clusters for eyeballing:

- by `content_hash` (identical bytes)
- by `text_hash` (identical extracted text, different bytes)
- by normalized filename (candidate, not suppressed)
- by normalized filename + size (stronger candidate)
- by size alone (weak)

It also reports how many duplicate candidates fall in formats that were not
text-extracted (so we know whether `text_hash` actually covers the duplication
or whether the duplicates are mostly in unextracted formats like `.mobi`).

The command queries the local index only and never walks or mutates the source
tree. Its purpose is to turn "I cannot say which format the duplicates are in"
into evidence. That evidence then feeds a dedicated decision step run on a
stronger model in a fresh session (see the split-model plan), which sets the
final duplicate-handling policy for this thread rather than leaving it to the
executor's guess.

### Source Access Model

Search must work from the local index even when the source root is unavailable.
The governing invariant for refresh is:

> **Refresh never mutates the index when the source root is unavailable.** When
> the root is reachable, the walk is authoritative: files that are gone from disk
> have their rows removed.

Consequences:

- A downed mount cannot wipe the index, because refresh skips all writes when the
  root probe fails.
- There is no "soft-deleted / historical row" state machine. When the root is
  reachable and a file is gone, its row (and FTS entry) is deleted.
- `folder-corpus-check` reports the source root as unavailable when it is.
- search still returns indexed hits, each marked `source_available: false` when
  the root is unavailable.
- Original-file inspection or re-extraction fails clearly instead of being
  treated as no results.

## Assumptions & Uncertainties

- The source folder may be local or server-mounted. The implementation must not
  assume either.
- The local index lives at a user-controlled local path outside committed
  project files; `.gitignore` must prevent any `.sqlite` index from being
  committed.
- The first implementation is a file-tree source only, not a general rewrite of
  every Vicaya source.
- Calibre remains unchanged. There is no Calibre migration and no dependency on
  Calibre metadata.
- Duplicate detection is local to this corpus and exact-only in this thread.
  Cross-source dedupe against Calibre is out of scope.
- Text extraction support starts with formats that are easy to handle:
  - plain text (`.txt`, `.md`)
  - `.htm` / `.html` (reusing the existing `_strip_xml` helper)
  - PDF via `pdftotext` if already available on PATH
  - `.epub`, `.odt`, `.docx` through stdlib zip/XML extraction
  - Generic `.xml` is **not** extracted in the MVP (arbitrary XML rarely yields
    useful body text); revisit only for a specific known schema.
- Unsupported formats still appear as index metadata records, with an extraction
  status explaining why no full text exists.
- The repository currently has very few runtime dependencies. Do not add heavy
  new dependencies; all listed extraction is stdlib or an optional already-present
  CLI (`pdftotext`).

## Constraints

- Keep this separate from Calibre code and behavior.
- Preserve existing `search_calibre`, `calibre-check`, and Calibre skill
  instructions.
- Do not use vector RAG for this thread. The project prefers structured local
  search over embeddings.
- Do not repeatedly traverse the server path during normal research. Traversal
  belongs to refresh/check commands.
- Do not mutate, rename, delete, or reorganize files in the source folder.
- Reuse existing text helpers (`_strip_xml`, `_strip_diacritics`) rather than
  reimplementing them. To avoid a circular import — `research_sources.py` will
  call into the new module while the new module wants those helpers — either keep
  `folder_corpus.py` self-contained or factor the shared helpers into a small
  module both import, and have `research_sources.py` import `folder_corpus`
  lazily inside the CLI handler.
- `.py` files must follow project validation rules:
  - `uv run ruff check <changed .py files>`
  - `uv run pyright <changed .py files>`
  - `uv run pyrefly check --search-path . <changed .py files>`
  - `uv run pytest <relevant test file> -q`
- Routine validation must stay scoped to touched files/tests.

## How We'll Know It's Done

- A configured file-tree corpus can be refreshed into a local SQLite index, with
  `--limit N` available for bounded runs.
- The refresh command handles an unavailable source root gracefully and never
  mutates the index in that case.
- Incremental refresh skips both re-reading-for-hash and re-extraction when
  `(rel_path, size, mtime)` is unchanged.
- The search command returns JSON hits from the local index without walking the
  source tree.
- Search hits include title/path-like metadata, snippet text when available,
  extraction status, and duplicate info (`duplicate_count`, duplicate paths).
- Full-text matching is diacritic-insensitive in both directions; snippets retain
  original diacritics.
- Exact-content duplicates (same `content_hash` or same `text_hash`) are grouped
  and suppressed from default results; `--include-duplicates` reveals members.
- Weak duplicate signals (size / normalized filename / title) appear as
  `possible_duplicate_of` hints on hits and are never auto-suppressed.
- `folder-corpus-duplicates` reports duplicate clusters by each grouping key,
  including coverage by unextracted formats, and has been run against the real
  `Non-Canonical English` tree to produce the evidence file.
- The duplicate-handling policy was decided in a dedicated Pro session from that
  evidence (decision doc in the thread) and implemented by the executor — not
  guessed during execution.
- Unsupported files are indexed as metadata records without breaking refresh.
- The Vicaya skill documentation tells agents when and how to use the new
  file-tree source.
- Tests cover:
  - indexing a small fixture tree
  - text/HTML extraction
  - diacritic-insensitive matching in both directions
  - exact-content grouping by both `content_hash` and `text_hash`, and default
    suppression
  - weak-signal `possible_duplicate_of` surfacing (not suppressed)
  - source-root unavailable behavior (no index mutation)
  - CLI JSON shape
  - epub/docx/odt extraction using fixtures built inline as zips (no committed
    binary sample files)

## What's Not Included

- No Calibre integration or Calibre refactor.
- No cross-deduplication against Calibre.
- No fuzzy/open-ended text-similarity scoring. Exact-content hashes (file or
  text) are always auto-suppressed; a precisely-defined weak rule may be promoted
  to auto-suppression only if the Pro decision step judges the evidence safe,
  otherwise weak signals are surfaced only.
- No `corpus_id` / multi-corpus registry (one index file per corpus).
- No generic XML extraction.
- No GUI.
- No background daemon or automatic watcher.
- No destructive cleanup of duplicate files.
- No semantic/vector search.
- No guarantee that every legacy binary format is extractable in the first
  version.
- No project-wide validation beyond the touched-file checks required by project
  rules.
