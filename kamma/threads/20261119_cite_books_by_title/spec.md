# Spec — Cite library books by title and author, never by number

## Overview

Research notes cite library books by a number: the `library_refs` frontmatter (`"223: On Meditation — Ajahn Chah"`), footnote labels (`[^calibre-223]`), body tokens (`Calibre #223`, `doc 223`, `#223`) and rows of the "Sources Investigated, Not Used" table. The tools also match citations to search hits by that number: the coverage check (`scratch-check-coverage`), the Phase 7 unread-citation gate (`unread_library_citations`) and the bibliography check (`check-bibliography`).

That number cannot identify a book. It is the index row id, and it changes for reasons that have nothing to do with the book. This thread removes every library number from notes and tools that compare notes, so a citation names the book the way print scholarship does: title and author. The index number survives only as a short-lived handle inside one run (a search hit's `document_id` passed to `read-library`). It never reaches a note.

## Root cause (verified 2026-11-19 by reading the code)

- `documents.id` in `tools/library_folders.py` is `INTEGER PRIMARY KEY`: SQLite hands out the next free row number in the order the refresh first meets each file (`_upsert_document`, `INSERT INTO documents`). Nothing about the book sets it.
- A row is recognised only by its absolute `source_path` (`UNIQUE`). `_delete_missing_documents` deletes rows whose path was not seen, and the file is inserted again with a new id.
- So the id changes on: a rebuild from scratch (every book is renumbered in walk order, and one added folder shifts every later number); a moved or renamed file (Calibre renames a book's folder when its title or author is edited); a library mounted at a different path; and any other user's library (other books, other order).
- `SCHEMA_VERSION` mismatch in `initialize_schema` drops every table, so a schema bump is also a full renumbering.
- `skill/vicaya/SKILL.md` Rule F4 already records one rebuild (2026-09-03) that moved id 8757 from Anālayo's *Memento Mori* to an unrelated title. The skill labels the index id "Calibre #", which invites agents to paste Calibre's own book number from the folder name `…/Title (8904)/`.

## Measured damage (2026-11-19, read-only probes; scripts in the session scratchpad, not kept)

- Top-level vault folder only: 2,058 `library_refs` entries in 270 notes, matched by title tokens against the current index. 594 (29%) point to the right book. 643 hold the Calibre folder number of the right book. 263 point to another book while the title matches exactly one book elsewhere. 221 match several copies of one book. 224 match no title. 113 have titles too short to match. Samples of each class were checked by eye.
- 1,949 of the 2,058 entries already give an author after the title (`Title — Author`).
- Body numbers in top-level notes: 4,910 mentions. 1,887 appear in the same note's `library_refs`. 2,008 appear only in the note's run dossier (`data/scratch/<slug>.md`, header `**Vault note:** <path>`; 133 notes have one). 1,164 resolve to neither. A sample of those showed mostly numbers beside a title already, grouped lists in Not Used rows, and non-library numbers (WisdomLib URLs `…/d/doc1460771.html`, numbered lists `(#1)`).
- Notes holding library numbers or `library_refs`: 306 in `<vault>/Vicaya/`, 13 in `Christianity Comparative/`, 41 in `What the Suttas Say About/`; `Digest/` has none. 360 in total.
- `<vault>/Vicaya` is its own git repository and was clean on 2026-11-19, so every note change is reviewable and reversible before a push.

## A second defect found on the way (verified)

Calibre metadata never reaches this index. `refresh()` calls `_build_calibre_metadata_lookup(root)` only for each configured root, and that function reads only `root / "metadata.db"`. The configured root (one, here) holds several Calibre libraries one level down (`<root>/Bodhirasa eBook Library/metadata.db` and others). Result: 0 of 46,456 indexed documents carry the `[Calibre #… | Authors: … | Tags: …]` prefix, so author and tag search through Calibre metadata does not work today, and the SKILL.md claim that the index prints "Calibre #8904" inside its text is false for this setup.

## What it should do

1. **Every search hit and every `read-library` result carries `cite_as`:** one string, `<Title> — <Authors>`, for the agent to copy into the note.
   - Calibre books: title and authors exactly as Calibre stores them (diacritics kept). Read at refresh time from every `metadata.db` at the root or one level below it, into a new index table keyed by `source_path`. The table is created with `CREATE TABLE IF NOT EXISTS` and rewritten whole on each refresh. **No `SCHEMA_VERSION` bump** (a bump wipes the index). It stays readable when the drive is unmounted.
   - Other books: the file name without its extension. There is no author, so the agent adds the author from the book itself.
   - Measured: 20,528 of 46,456 documents sit inside a Calibre library (16,036 Calibre books). Titles parsed from the folder name match Calibre's title exactly for 78%. 11% differ only in accents ("Mulapannasa" vs "Mūlapaṇṇāsa"). 11% are cut short by Calibre's path limit. That is why the title comes from `metadata.db`, not from the path.
2. **Fix the Calibre metadata lookup** to read `metadata.db` one level below each root, as well as at the root. Drop `Calibre #<id>` from the FTS prefix line, so no Calibre number reaches a snippet. The prefix applies only when a file is next extracted; nothing re-extracts existing rows in this thread.
3. **The note format cites by title and author only:**
   - `library_refs`: `"<Title> — <Author>"` (quoted string, as Rule F4 already requires).
   - Footnotes: `[^lib-<n>]`, numbered 1, 2, 3 in order of first use, like `[^web-<n>]`. Definition: `[^lib-1]: [[<Title>]] — <Author>`.
   - Not Used rows name `<Title> — <Author>`. The consolidated tail row stays as it is.
   - Changes go into `skill/vicaya/SKILL.md` (Rule F4, footnote table, Phase 7 template, bibliography and Not Used examples, coverage-check text, "Read before you cite", hit field list), `skill/vicaya-quick/SKILL.md` (copy `cite_as`), and `skill/vicaya-what-the-suttas-say/SKILL.md` if it repeats the format.
4. **One title matcher** decides whether a citation names a logged hit: fold case and accents, take title words of 3+ letters minus stop words, and require at least 80% of them among the hit's words. Copies of the same book (PDF and EPUB, two folders) all count as that book.
   - *Changed 2026-11-19 after measuring on 1,328 real entries (`artifacts/matcher-measure.md`).* The one-way rule matched unrelated books ("Merit" → "Ten Ways Of Making Merit", every Yoga Sutras translation) and missed Calibre's cut names. The matcher now: reads the hit's words from `cite_as`, the file name and its own folder only (category folders above matched unrelated books); runs both ways (one of the hit's titles must also be found in the citation); accepts one title starting the other word for word, with Calibre's cut last word; rejects a hit whose known author shares no name with the citation's (typos allowed); lets a one- or two-word title count only beside its author; drops bracketed notes, subtitles and file extensions in looser tries. A note line (a Not Used row, a sentence) names a hit when it holds one of the hit's titles by the same rules.
   - A second round (runs 16–22) added number words, Roman volume numerals, joined compound words, author-gated typo tolerance, and a main-title check. Read after it: 11 of 112 judged cases wrong (9.8%), nine of them data problems (no title in the file name, a chapter inside a book, spelling or author errors in Calibre or the note). A miss lets the gate pass that citation, as today, and never refuses a run.
   - *Added 2026-11-19 at the user's suggestion:* when no logged hit matches a citation by name, the checkers look the title up in the indexed text of the logged hits (found by `source_path`, since old numbers move). The probe found the exact cited title near the start of the text for 5 of the 7 hardest misses. See plan task 2.1b.
5. **Checkers compare titles, not numbers:**
   - `scratch-check-coverage`: `unaccounted` = gathered hits whose title the note never names; `cited_not_gathered` = `library_refs` titles that match no logged hit; `folder_number_cited` is removed.
   - `unread_library_citations` (Phase 7 gate): cited = `library_refs` and `[^lib-…]` definitions; read = successful `read-library` results; flagged and rejected lines are matched to readable hits by title. The rules for what counts as flagged, rejected or exempt stay as the PR 37 thread set them.
   - `check-bibliography` (`tools/note_audit.py`): drop the `Calibre #` branch; the author-and-title branch remains.
   - *Added 2026-11-19 after review:* a Not Used row's rejected books come from its first cell only, each book in it checked alone; a gate line names a hit by title, not by a one-word file code; a citation crediting a translator counts as read when a copy was read under its own author; a cited volume, part or chapter number must agree with the hit's.
   - The numeric note-id regex (`_NOTE_DOC_ID_RE`) is removed.
6. **A hard validator check stops numbers coming back:** `validate_note.py` reports a library number anywhere in a note, outside URLs: a `library_refs` entry starting with `<digits>:`, `Calibre #<n>`, `[^calibre-`, or `doc`/`document`/`library` followed by a number. It must report 0 findings on all 360 notes after the migration, and catch each pattern in a seeded note.
7. **Migrate all 360 old notes once** (the user chose this on 2026-11-19), with a one-off script kept in this thread's `artifacts/`, not in `scripts/`:
   - `library_refs`: drop the `<n>:` prefix and keep the title and author already written.
   - Footnote labels `[^calibre-<n>…]` become `[^lib-<k>]`, markers and definitions alike, numbered by first use. The note must still pass the undefined-footnote check.
   - A number token beside a title (`(Calibre #223)`, `(doc 10081)`) is deleted.
   - A grouped or bare number with no title beside it becomes the book's title, looked up first in the note's own `library_refs` (as written in that note), then in the note's run dossier hits (titles as they stood during that run). A number that resolves to neither is removed and listed in the report.
   - URLs are never touched.
   - A dry run writes a report first: counts per action, the unresolved list, and a per-note summary. `--apply` writes the notes.
   - Then regenerate the PDF of every changed note and run the validator over all notes.
   - The changes stay **uncommitted** in the `<vault>/Vicaya` repo for the user to review. No commit, no push, no `sync_notes.py`.

## Assumptions and uncertainties

- **Matcher threshold (measured 2026-11-19).** The 80% share stays, but a share alone was not enough: see item 4 and `artifacts/matcher-measure.md` (15 runs, 92 cases read).
- **Weak non-Calibre titles (uncertain).** File names outside Calibre can be poor, for example `book27_074.html`. An agent who writes a better title may not match its hit, and the coverage check would then report the hit as unaccounted. This is advisory, not a gate. Its rate is measured in the plan.
- **Old dossiers (verified shape, untested at scale).** Run logs written before this change hold hits without `cite_as`. The matcher falls back to `title` and `relative_path`, which those logs do hold.
- **Unresolvable mentions (uncertain).** The number of real library mentions the migration cannot resolve is known only after the dry run. Non-library numbers (URLs, numbered lists) must be left alone. The migration therefore uses a narrower pattern than the gate's old id regex.
- **Resumed runs across a rebuild (accepted risk).** A run resumed with `scratch-resume` after a rebuild holds stale `document_id`s, so `read-library` on an old id may open another book. `read-library` now returns `cite_as`, so the agent can see the mismatch. No further guard.
- **Refresh time (unmeasured).** Rewriting the Calibre title table on each refresh reads 16,036 rows from several small `metadata.db` files, expected to take seconds. The first real refresh measures it.

## Constraints

- Never bump `SCHEMA_VERSION`, and never change the index in a way that forces re-extraction (hours of OCR).
- The index and source files are read-only apart from the normal `library-folders-refresh`, which the plan runs once to fill the title table.
- Vault notes are rewritten only by the migration's `--apply`, and only after its dry-run report exists. No commit or push in the notes repo, and no `sync_notes.py`: publishing is the user's call.
- `VICAYA_SCRATCH=/dev/null/none` on every helper or pytest call while any research run may be live.
- One line per paragraph in every Markdown file (no hard wrapping).
- Committed files use `<vault>` and `<repo root>`, never home-folder paths.

## How we'll know it's done

- Search hits and `read-library` results carry `cite_as`. On the real index, a sample of 20 Calibre hits shows Calibre's exact titles with diacritics.
- The Calibre title table holds about 16,036 books after one real refresh, and that refresh re-extracts no file.
- After the migration, the validator reports 0 library numbers across all 360 notes. A seeded note with each forbidden pattern is caught.
- Every migrated note passes `validate_note.py` as it did before (no new findings), and its PDF is regenerated.
- **Renumbering test:** the same fixture library indexed twice, in a different walk order, gives different `document_id`s but identical coverage, gate and bibliography results for the same note and dossier.
- Coverage and the gate, run on the 20 most recent real dossiers with their migrated notes, give results a reviewer judges right line by line. The report lists them.
- Every new test fails with its change reverted, and the full suite passes.

## What's not included

- Making index numbers stable (keying rows by content hash or similar). Once no note carries a number, nothing depends on it.
- `read-library` by title. The agent searches, then reads by the hit's handle.
- Re-extracting existing documents to add the author and tag prefix. That happens as files are next re-indexed.
- ISBN or DOI lookups.
- The vicaya-quick rule that quotes snippets (`"<snippet>"`). That is a separate question.
- Committing or pushing the migrated notes.
