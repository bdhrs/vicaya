# Plan — Vicaya index maintenance

## Architecture Decisions
- Backfill by direct read + edit, not a generated script: description text
  and topic-categorization require judgment (existing entries are curated
  prose, not derived from frontmatter mechanically).
- Read missing notes in parallel batches (forked agents) to keep this
  tractable; the coordinator writes the final index edits itself so
  formatting/ordering stays consistent and no concurrent-edit races occur on
  the two index files.

## Phase 1 — Digest misfile
- [x] Move `Vicaya/Christianity Comparative/Real Apologies vs Narcissist
      Apologies.md` to `Vicaya Digest/Real Apologies vs Narcissist
      Apologies.md`.
      → verify: file no longer under `Christianity Comparative/`, present
      under `Vicaya Digest/`.

## Phase 2 — Gather descriptions for missing notes
- [x] For each of the 85 missing notes (64 main, 13 WTSS, 8 CC — one CC item
      turned out to be the Digest misfile, handled in Phase 1 instead),
      dispatched 7 parallel read-only agents; each returned (date, category,
      title, description), and the 32 main-folder notes also needing a
      catalog entry returned a topic-heading assignment.
      → verify: all 7 batches returned; 85 tuples collected, 32 with a
      topic-heading assignment. Done.

## Phase 3 — Update summary-vicaya.md
- [x] Inserted 64 main-folder rows, 13 "What the Suttas Say About" rows, and
      8 "Christianity Comparative" rows, each in chronological order within
      its table.
      → verify: re-read confirms all 85 wikilinks present, dates match
      filenames. Done.

## Phase 4 — Update catalog-by-topics.md
- [x] Inserted all 32 wikilinks under matching topic headings; added one new
      heading ("Avyākata Questions") for a note with no existing fit; bumped
      the header note count from 256 to 288.
      → verify: re-run diff — zero gaps for the 32 target notes. Done.

## Phase 5 — Publish
- [x] `uv run scripts/sync_notes.py "Vicaya/summary-vicaya.md"` — committed
      and pushed.
- [x] `uv run scripts/sync_notes.py "Vicaya/catalog-by-topics.md"` —
      committed and pushed.
      → verify: both reported "Successfully synced". Done.

## Phase 6 — Wire the skill for future runs
- [x] Edited `skill/vicaya/SKILL.md`: added the index-update + publish step
      to the Phase 7 summary line (line 24) and the detailed Phase 7 exit
      sequence (line 2411), both right after `sync_notes.py` publishes the
      note and before the run-report sync.
      → verify: both lines now mention updating and publishing
      `summary-vicaya.md`/`catalog-by-topics.md`. Done.

## Phase 7 — Final verification
- [x] Re-ran the full missing-notes diff for all three folders.
      → verify: zero gaps for every note this thread targeted. Two brand-new
      notes (`2026-08-31 - dhutanga-ascetic-practices`,
      `2026-08-31 - upadanakkhandha-childers-origin-sense`) appeared mid-run
      from a concurrent, unrelated `/vicaya` session — out of this thread's
      scope; they'll be picked up by the next run once Phase 6's wiring
      fires, or a future backfill. Done.
