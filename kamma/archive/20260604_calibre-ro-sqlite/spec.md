# Spec — Calibre read-only SQLite metadata search (closes #9)

## GitHub issue
Closes #9 — "Calibre library locked when running concurrent /vicaya sessions"

## Overview
Concurrent /vicaya runs serialize on the Calibre phase because every search and
preflight shells out to `calibredb`, which holds an exclusive OS lock (Option A,
`_calibre_serialize()`, already queues them fairly instead of crashing). This thread
implements Option B: read `metadata.db` directly in read-only mode for the two hot
paths, removing lock contention for the common case. Unlimited concurrent readers
are safe on a `mode=ro` SQLite connection — the same pattern already used for the
canon DB.

## What it should do
- `_calibre_metadata_search()` queries `<library>/metadata.db` via a read-only
  SQLite connection, matching the free-text query against title, author names,
  tags, and comments (LIKE), with optional tag-name filtering (exact, case-insensitive
  — matching the current `tags:"=X"` semantics). Returns the same CalibreHit shape.
- `calibre_library_available()` probes by opening metadata.db read-only and running
  `SELECT count(*) FROM books` — instant, lock-free.
- If the schema is not as expected (sqlite OperationalError/DatabaseError), metadata
  search falls back to the existing `calibredb list` path; the preflight returns
  (False, message).
- FTS path (`_calibre_fts_search`) is unchanged — still uses `calibredb`.

## Assumptions & uncertainties
- Calibre metadata.db schema (`books`, `authors`, `books_authors_link`, `tags`,
  `books_tags_link`, `comments`) has been stable since Calibre 2.x. Schema-change
  risk is mitigated by the fallback, not a version parser.
- The query is already diacritic-stripped to ASCII before reaching metadata search
  (done in `search_calibre`), so LIKE matching needs no normalization change.
- calibredb free-text search hits all fields; we cover title/author/tags/comments —
  the fields CalibreHit actually surfaces. Edge fields (series, publisher) are not
  matched. Judged acceptable; noted.

## Constraints
- Read-only only — never open metadata.db writable.
- CalibreHit shape, search_calibre dispatch, and FTS path must not change.
- No new dependencies (stdlib sqlite3 only).

## How we'll know it's done
- New hermetic tests build a temp metadata.db and assert metadata search + preflight
  work with no calibredb/lock involvement.
- Two concurrent metadata searches no longer block each other.
- ruff + pyright clean; full suite passes.

## What's not included
- FTS bypass (Option C) — FTS stays on calibredb.
- Removing `_calibre_serialize()` — it still guards the FTS path and any fallback.
