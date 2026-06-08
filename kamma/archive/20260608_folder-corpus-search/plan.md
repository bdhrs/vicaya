# Plan - Indexed File-Tree Research Source

## Architecture Decisions

- Build this as a separate folder-corpus source, not as Calibre integration. It
  must not call `calibredb`, read Calibre metadata, or alter `search_calibre`.
- Use two `.env` values:
  - `VICAYA_FOLDER_CORPUS_ROOT` = actual source folder, local or
    server-mounted.
  - `VICAYA_FOLDER_CORPUS_INDEX` = local SQLite database used for fast search.
- Store extracted text in the FTS5 table itself; store metadata + hash in
  `documents`. No separate cache path in the MVP.
- Keep the schema to two tables plus a tiny meta table:
  - `documents` (metadata + `content_hash`)
  - `document_fts` (FTS5, `rowid = documents.id`, stores original text)
  - `index_meta` (schema version, last refresh)
  - No `document_text` table (FTS5 holds the text). No `duplicate_groups` table
    (groups are rows sharing `content_hash`, derived with `GROUP BY`).
- One corpus per index file; no `corpus_id` column. Keep root/index as function
  parameters so more corpora can be added later without redesign.
- Add a focused module, `tools/folder_corpus.py`, and wire commands through
  `tools/research_sources.py`. Import `folder_corpus` lazily inside the CLI
  handler to avoid a circular import; reuse `_strip_xml` (factor into a shared
  helper if needed rather than duplicating logic).
- Use SQLite FTS5, not vector search.
- Make matching diacritic-insensitive both directions via FTS5
  `tokenize="unicode61 remove_diacritics 2"`. Store original text so snippets
  keep diacritics. (Verified working in the local sqlite 3.47.1 build.)
- Tiered duplicate handling. Auto-suppress only exact-content duplicates by
  default: rows sharing `content_hash` (SHA-256 of bytes) or `text_hash` (hash
  of normalized extracted text). Surface weak signals (size / normalized
  filename / title) as `possible_duplicate_of` hints without suppressing. No
  fuzzy similarity scoring. The real duplication pattern is discovered with a
  read-only `folder-corpus-duplicates` diagnostic run against the actual tree;
  findings + a promotion recommendation are written up for review rather than
  guessed now.
- Use stdlib extractors first; optional external tools (`pdftotext`) only when
  already present, with clear extraction status. No Calibre tools.
- Split-model plan (Kamma model boundary, `.claude/commands/kamma/2-do.md:44-45`).
  All build/mechanical work runs on **Fast**. The single judgment call — how to
  handle duplicates given real evidence — is isolated to one **Pro** phase that
  only analyzes and decides, writing a decision doc and task list but no code.
  The two phase boundaries around it are marked `⚠️ MODEL SWITCH REQUIRED`, so
  the executor writes a handoff and stops for a fresh session at each switch.
  Fast never decides duplicate policy by guesswork; Pro never writes
  implementation code.

## Dependency Order

Config and schema must exist before refresh. Refresh must exist before search.
Duplicate grouping depends on indexed `content_hash`/`text_hash` values; the
duplicate investigation depends on a populated index (ideally the real tree).
Skill/docs updates depend on final command names and JSON shape.

## Phase 1 - Config, Schema, and Health Check (Fast)

- [x] Add `tools/folder_corpus.py` with config resolution and dataclasses
  - Read `VICAYA_FOLDER_CORPUS_ROOT` and `VICAYA_FOLDER_CORPUS_INDEX`.
  - Expand `~`.
  - Return a clear unavailable status when either value is missing.
  - New `.py` file starts with a one-sentence purpose description.
  -> verify: run `uv run python -c "from tools.folder_corpus import default_config; print(default_config())"` with env unset; expect no crash and an unavailable/missing config result.

- [x] Define the SQLite schema and initialization function
  - Tables: `documents`, `document_fts` (FTS5,
    `tokenize="unicode61 remove_diacritics 2"`), and `index_meta`.
  - `documents` columns: id, source path, relative path, filename, extension,
    inferred category path, size, mtime, `content_hash`, `text_hash` (nullable),
    extraction status, indexed timestamp.
  - `document_fts` stores original extracted text, `rowid = documents.id`.
  - `index_meta` holds schema version and last-refresh timestamp.
  -> verify: run a small Python snippet against a temp db, call schema init, query `sqlite_master`, expect `documents`, `document_fts`, `index_meta`.

- [x] Add `folder-corpus-check` CLI command in `tools/research_sources.py`
  - Reports JSON with root path, index path, root availability, index
    availability, FTS5 availability (probe a temp `CREATE VIRTUAL TABLE`), and
    document count if the index exists.
  - Does not traverse the source tree.
  -> verify: run `VICAYA_FOLDER_CORPUS_ROOT=/tmp/missing VICAYA_FOLDER_CORPUS_INDEX=/tmp/fc.sqlite uv run tools/research_sources.py folder-corpus-check`; expect JSON, `fts5: true`, and non-crashing unavailable root status.

- [x] Add focused tests for config/check/schema
  - Create `tests/test_folder_corpus.py`.
  - Use temp paths only.
  -> verify: run `uv run pytest tests/test_folder_corpus.py -q`, expect pass.

- [x] Phase verification
  -> verify: run `uv run ruff check tools/folder_corpus.py tools/research_sources.py tests/test_folder_corpus.py`, `uv run pyright tools/folder_corpus.py tools/research_sources.py tests/test_folder_corpus.py`, `uv run pyrefly check --search-path . tools/folder_corpus.py tools/research_sources.py tests/test_folder_corpus.py`, and `uv run pytest tests/test_folder_corpus.py -q`; expect all pass.

## Phase 2 - Refresh and Basic Search (Fast)

- [x] Implement `folder-corpus-refresh` (with `--limit N`)
  - Probe the root first: if unavailable, write nothing and report unavailable.
  - Walk the configured root only during refresh.
  - Ignore obvious web asset/noise extensions by default where appropriate, but
    stay conservative for document-like files.
  - Index metadata for every accepted file and compute SHA-256.
  - Extract text for `.txt`, `.md`, `.htm`, `.html` using stdlib-safe logic
    (reuse `_strip_xml` for HTML). Do not extract generic `.xml` in the MVP.
  - Store original extracted text in `document_fts`, and compute `text_hash`
    from the normalized extracted text (null when no text was extracted).
  - Record unsupported formats as metadata-only, not as failures.
  - `--limit N` caps the number of files indexed in one run.
  -> verify: create a temp fixture tree with text/html/unsupported files, run refresh, query the db, expect all fixture files represented and text extracted for supported files.

- [x] Implement incremental refresh behavior
  - Skip both re-reading-for-hash and re-extraction when
    `(rel_path, size, mtime)` is unchanged; reuse the stored `content_hash` and
    `text_hash`.
  - When the root is reachable, delete rows (and FTS entries) for files that no
    longer exist on disk. When the root is unavailable, mutate nothing.
  -> verify: run refresh twice on a temp fixture, assert unchanged files are not re-hashed/re-extracted (counter or timestamp); remove a fixture file, refresh, assert its row is gone; make root unavailable, refresh, assert the index is untouched.

- [x] Implement `search-folder-corpus`
  - Query local SQLite/FTS only.
  - Return JSON hits with document id, title/filename, relative path, absolute
    source path, extension, snippet (via `snippet()`), extraction status,
    `duplicate_count`, duplicate paths when present, `possible_duplicate_of`
    hints when weak signals match, and `source_available`.
  - Do not walk or read source files during search.
  -> verify: make source root unavailable after refresh, run search from the existing index, expect hits returned with `source_available: false`.

- [x] Add search tests
  - Cover text search, HTML tag stripping, diacritic-insensitive matching in
    both directions (query `paticcasamuppada` vs stored `paṭiccasamuppāda` and
    vice versa), metadata-only files, and unavailable source root.
  -> verify: run `uv run pytest tests/test_folder_corpus.py -q`, expect pass.

- [x] Phase verification
  -> verify: run the scoped ruff, pyright, pyrefly, and pytest bundle for changed Python files; expect all pass.

## Phase 3 - Duplicate Machinery, Diagnostic, and Broader Extraction (Fast)

> Builds the duplicate scaffolding with a deliberately **safe placeholder
> default** (auto-suppress exact-content only; surface weak signals). The final
> duplicate policy is set later by the Pro decision phase, not here.

- [x] Add exact-content duplicate grouping (file hash + text hash)
  - A duplicate group is rows sharing one `content_hash`, or rows sharing one
    non-null `text_hash`, derived with `GROUP BY` at search time (no stored
    group table).
  - Representative = lexicographically first `rel_path`.
  -> verify: fixture (a) two byte-identical files with different names, and (b) two files with identical text but different bytes (e.g. different trailing whitespace/metadata); each pair returns one default hit with `duplicate_count: 2`.

- [x] Add duplicate visibility option
  - `search-folder-corpus` suppresses non-representative group members by
    default.
  - Add `--include-duplicates` to return all matching members.
  - Include duplicate paths (or hash) in default representative hits.
  -> verify: same duplicate fixtures return one hit by default and all members with `--include-duplicates`.

- [x] Surface weak duplicate signals without suppressing
  - Compute, at search time, `possible_duplicate_of` hints for hits that are not
    exact-content matches but share size, normalized filename (case- and
    diacritic-folded via `_strip_diacritics`, extension and trailing
    copy/version tokens stripped), or title.
  - These are reported on the hit and never removed from results.
  -> verify: fixture two non-identical files with near-identical names; both appear in results and each carries a `possible_duplicate_of` hint; neither is suppressed.

- [x] Add `folder-corpus-duplicates` read-only diagnostic
  - Query the index only; never walk or mutate the source tree.
  - Report, per grouping key (`content_hash`, `text_hash`, normalized filename,
    normalized filename + size, size), the cluster count, file count, and a
    sample of `--samples N` clusters with their paths.
  - Report how many duplicate candidates fall in non-text-extracted formats.
  -> verify: against a temp fixture with known dup clusters, output JSON shows the expected per-key counts and sample paths; running with no index reports cleanly.

- [x] Add additional practical extractors without Calibre coupling
  - `.epub`: stdlib zip + HTML/XML extraction.
  - `.odt` / `.docx`: stdlib zip + XML text extraction where practical.
  - `.pdf`: optional `pdftotext` if available; otherwise status
    `unsupported: pdftotext not found`.
  - `.doc`, `.rtf`, `.mobi`, `.azw3`: metadata-only unless a non-Calibre,
    clearly optional local extractor is already available and simple.
  -> verify: epub/docx/odt fixtures built inline as zips extract correctly; PDF test skips when `pdftotext` is absent.

- [x] Phase verification
  -> verify: run the scoped ruff, pyright, pyrefly, and pytest bundle for changed Python files; expect all pass.

## Phase 4 - Gather Duplicate Evidence (Fast)

> Mechanical only: index the real tree and dump the diagnostic. No analysis, no
> policy decision, no default-behavior change here.

- [x] Index the real tree and capture the diagnostic into an evidence file
  - Configure
    `VICAYA_FOLDER_CORPUS_ROOT=/Users/deva/filesrv1/share2/Textual/Non-Canonical English`
    and a local index such as `/Users/deva/server-library/noncanonical-english.sqlite`.
  - Run `folder-corpus-check`, then `folder-corpus-refresh` indexing as large a
    sample as is practical (use `--limit N` if a full index is too slow), then
    `search-folder-corpus` as a smoke test.
  - Run `folder-corpus-duplicates --samples N` and save the raw JSON to
    `kamma/threads/20260608_folder-corpus-search/dup-evidence.json` (gitignored
    or kept out of the commit).
  - Record what was indexed (file count, whether bounded), not conclusions.
  - Result: real root was available; indexed 1000 files with `--limit 1000`
    into `/Users/deva/server-library/noncanonical-english.sqlite`;
    extracted text for 92 files and stored metadata only for 908 files.
  -> verify: `dup-evidence.json` exists with per-key cluster counts, sample clusters, and unextracted-format coverage; if the real tree was unavailable, record the reason and capture the diagnostic from the largest available fixture instead.

- [x] Phase verification and handoff for model switch
  - Run the scoped ruff/pyright/pyrefly/pytest bundle for any changed files.
  - Write `handoff.md` covering build state, what was indexed, and the evidence
    file location, per the model-switch protocol.
  -> verify: scoped checks pass; `handoff.md` and `dup-evidence.json` are present.

## Phase 5 - ⚠️ MODEL SWITCH REQUIRED — Duplicate Policy Decision (Pro)

> Switch to a **fresh Pro session** before this phase. Pro **only analyzes and
> decides** — it writes a decision doc and updates the remaining task list, but
> writes **no implementation code**.

- [x] Analyze the evidence and decide the duplicate-handling policy
  - Read `dup-evidence.json` and `spec.md`.
  - Judge, per grouping key: how many real clusters exist, what formats the
    duplicates are actually in, how much duplication `text_hash` already covers
    vs. how much sits in unextracted formats, and the false-positive risk of
    each weak signal.
  - Decide the final policy: which tiers auto-suppress by default (baseline:
    `content_hash` + `text_hash`), whether any precisely-defined weak rule
    (e.g. normalized filename **and** identical size) is safe to promote to
    auto-suppression, what stays surfaced as `possible_duplicate_of`, and how
    the representative is chosen. No open-ended fuzzy similarity scoring.
  - Note any extraction gap worth closing if the evidence shows duplicates
    concentrated in an unextracted format.
  -> verify: a decision doc (e.g. `dup-decision.md`) records the chosen policy per tier with the evidence-based rationale and explicit accept/reject for each weak signal.

- [x] Translate the decision into concrete Phase 6 tasks and set the switch
  - Append/adjust the Phase 6 task list below so it implements exactly the
    decided policy (deltas from the safe placeholder built in Phase 3).
  - Write `handoff.md` pointing Fast at the decision doc and the precise code
    deltas.
  -> verify: Phase 6 tasks match the decision doc; `handoff.md` names the decision doc and the exact changes; no source code was modified in this phase.
  - Done: policy recorded in `dup-decision.md`; Phase 6 first task rewritten
    below into three concrete deltas; `handoff.md` rewritten for the Fast switch.
    No source code changed in this phase.

## Phase 6 - ⚠️ MODEL SWITCH REQUIRED — Implement Decision, Docs, Finalize (Fast)

> Switch back to a **fresh Fast session**. Implement exactly the Pro decision;
> do not re-litigate it.

> Decision source: `dup-decision.md`. Auto-suppression stays at the Phase 3
> baseline (`content_hash` ∪ `text_hash`, transitive, lexicographically-first
> representative) — **no weak signal is promoted**. The deltas only *narrow* the
> weak-hint surface and *close the `.doc` extraction gap*. Do not re-decide policy.

- [x] Narrow the weak-signal set in `_weak_duplicate_hints`
  - In `tools/folder_corpus.py` (~L624-628), remove `size` and `title` from the
    `values` dict; keep only `normalized_filename`. Rationale: `size` is pure
    noise (37 unrelated `.doc` block-size collisions); `title` is redundant with
    `normalized_filename` (both derive from the filename stem).
  -> verify: a fixture where two files share only byte size produces **no**
    `possible_duplicate_of` hint; two files with near-identical names still do.

- [x] Filter junk filenames/extensions from filename hints
  - Skip generic stop-names (`metadata`, `picasa`, `index`, `contents`, `cover`,
    `title`) and non-document extensions (`.ini`, `.opf`) when building the
    `normalized_filename` hint, so `metadata.opf` / `Picasa.ini` clusters stop
    generating hints.
  -> verify: a fixture with `metadata.opf` in two folders yields no hint; a
    fixture with two real same-named documents still yields one.

- [x] Close the `.doc` extraction gap (optional external tool)
  - Add `.doc` text extraction in `extract_text`, mirroring `_extract_pdf`:
    prefer `textutil -convert txt -stdout` on macOS, else `antiword`/`catdoc` if
    on `PATH`; check `shutil.which`, use a subprocess timeout and clear status
    strings, and fall back to metadata-only status when no extractor exists. No
    new Python dependency. This is the highest-value delta: `.doc` is ~59% of
    duplicate candidates and currently invisible to `text_hash`.
  - Leave `.mobi`/`.azw3` metadata-only; leave `.pdf` unchanged (`pdftotext`
    already wired — operator just re-runs refresh on a machine where it exists).
  -> verify: a `.doc` fixture extracts text when an extractor is present and the
    test **skips** when none is (mirroring the `pdftotext` skip); two `.doc`
    files with identical text now collapse via `text_hash`.

- [x] Update/extend tests to lock in the decided behavior
  - Assert: `size`/`title` never appear as hint signals; junk filenames produce
    no hints; `normalized_filename` hints still surface and are never suppressed;
    `content_hash`/`text_hash` suppression and `--include-duplicates` unchanged.
  -> verify: `uv run pytest tests/test_folder_corpus.py -q` passes.

- [x] Update `.env.example`
  - Add `VICAYA_FOLDER_CORPUS_ROOT` and `VICAYA_FOLDER_CORPUS_INDEX`.
  - Explain that root may be server-mounted while index must be local and
    outside the repo.
  -> verify: inspect `.env.example`; expect both variables and no local personal path hardcoded as default.

- [x] Confirm `.gitignore` excludes index databases and the evidence file
  - Ensure no `.sqlite` index or `dup-evidence.json` can be committed.
  -> verify: `git check-ignore` (or inspection) confirms the patterns are ignored; `git status` stays clean of any index db or evidence file.

- [x] Update `README.md` and `kamma/tech.md`
  - Document the new source as a separate unmanaged file-tree corpus.
  - State that normal search uses local SQLite and source files are touched only
    during refresh or manual inspection.
  - Describe the final duplicate behavior as decided.
  - Preserve current Calibre documentation unchanged except for mentioning this
    is a separate source.
  -> verify: run `rg -n "FOLDER_CORPUS|file-tree|folder corpus|Calibre" README.md kamma/tech.md`; expect clear separate-source wording.

- [x] Update `skill/vicaya/SKILL.md`
  - Add the new command to the source helper command table.
  - Add a research phase note telling agents to use file-tree search as a
    separate secondary-source search, that exact-content duplicates are already
    collapsed, that `possible_duplicate_of` hints flag likely same-book matches
    to judge (not double-count), and to treat unavailable source files as an
    access gap rather than no evidence.
  - Check staged sibling skills only for affected route headings; do not
    duplicate behavior into staged skills.
  -> verify: run `rg -n "search-folder-corpus|folder-corpus" skill/vicaya/SKILL.md skill/vicaya-*`; expect canonical skill has instructions and staged skills still route only.

- [x] Add CLI smoke tests for JSON shape
  - Test `folder-corpus-check`, `folder-corpus-refresh`,
    `search-folder-corpus`, and `folder-corpus-duplicates` via subprocess
    against temp fixtures.
  -> verify: run `uv run pytest tests/test_folder_corpus.py -q`, expect pass.

- [x] Run final scoped validation
  -> verify: run `uv run ruff check tools/folder_corpus.py tools/research_sources.py tests/test_folder_corpus.py`, `uv run pyright tools/folder_corpus.py tools/research_sources.py tests/test_folder_corpus.py`, `uv run pyrefly check --search-path . tools/folder_corpus.py tools/research_sources.py tests/test_folder_corpus.py`, and `uv run pytest tests/test_folder_corpus.py -q`; expect all pass.

- [x] Prepare review handoff
  - Summarize files changed, the duplicate decision and what it implemented,
    validation run, unsupported formats, and any real-path smoke-test
    limitations.
  -> verify: `git diff --stat` shows only expected files; no `.env`, index db, evidence file, or source-library files are staged/modified.

## Suggested Commit Message

`feat(sources): add indexed file-tree corpus search`

## Post-Review Operational Completion

The implementation is reviewed, but the thread is **not ready to finalize**
until the configured production index is usable.

- [x] Move the existing folder-corpus indexes into `/Users/deva/server-library/`
  - Current blocker: `/Users/deva/server-library` is a SQLite file, not a
    directory, so `/Users/deva/server-library/noncanonical-english.sqlite`
    cannot exist yet.
  - Preserve the existing 25-document SQLite file as
    `/Users/deva/server-library/noncanonical-english-legacy-25docs.sqlite`.
  - Move the 1000-document sample index from
    `/Users/deva/Documents/server-library/noncanonical-english.sqlite` to
    `/Users/deva/server-library/noncanonical-english.sqlite`.
  -> verify: `folder-corpus-check` reports `index_exists: true` and
  `document_count: 1000`.

- [x] Run an unbounded refresh against the real corpus
  - Command:
    `UV_CACHE_DIR=/private/tmp/uv-cache uv run tools/research_sources.py folder-corpus-refresh`
  - Do not pass `--limit`.
  -> verify: `folder-corpus-check` reports a document count representing the
  real accepted corpus, not the 25-document legacy file or 1000-document sample.

- [x] Smoke-test the production search database
  - Commands:
    `UV_CACHE_DIR=/private/tmp/uv-cache uv run tools/research_sources.py search-folder-corpus "dhamma" --limit 5`
    `UV_CACHE_DIR=/private/tmp/uv-cache uv run tools/research_sources.py folder-corpus-duplicates --samples 10`
  -> verify: search returns hits from
  `/Users/deva/server-library/noncanonical-english.sqlite`, duplicates report
  completes, and `source_available` is true.

- [x] Re-run `/kamma:3-review`
  - The review should pass only after the configured production index exists and
    the smoke tests above pass.
