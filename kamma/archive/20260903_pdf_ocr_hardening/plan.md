# Plan: reintroduce PDF OCR, plus durable refresh

Spec: `spec.md`. Baseline `65e3bd1`, 410 tests passing. No GitHub issue.

## Phase 1 — implement

- [x] T1 — Re-add the OCR fallback from `e22ef34`; apply the truncation status change inline; re-write the three trivial fixes while touching the code (prepend rather than default the worker's module path variable, frame the worker reply so library output cannot corrupt it, delete the comment claiming chunking preserves work when a chunk hangs). → verify: a real PDF OCRs; missing, error and empty all escalate; truncation is recorded.
- [x] T2 — Durability: write-ahead mode plus periodic commit. → verify: kill a refresh part-way and the completed files are retained; a search succeeds while a refresh runs.
- [x] T3 — Bump `SCHEMA_VERSION` to `"3"`. → verify: an existing index is rebuilt on the next refresh.
- [x] T4 — Two recipes, help text showing both passes and their order. → verify: help output.

## Phase 2 — verify for real

- [x] T5 — End-to-end on a real scanned book from the library: status, character count, elapsed time.
- [x] T10 — Per-chunk timeout, keeping the chunks a stalled book finished. Added after measurement triggered the spec's own deferral condition. → verify: the two books measured as stalling now return partial text with a stalled status instead of nothing after 1800 s.
- [x] T6 — Full suite plus scoped checks on touched files.

## Phase 3 — run it and measure, don't forecast

- [~] T7 — Text pass, then OCR pass, on the real library. Record the actual per-book and total rate as it runs. **Running in the user's own terminal since 14:45 on 2026-09-03** (`just lf-refresh-text`, 46,427 files, ~7 file/s early). The agent must not run it: it outlives an agent session, and it is the user's data. Numbers land in their terminal.
- [ ] T8 — Only if the measured rate is unacceptable: open a new thread for concurrency, carrying the real numbers. Blocked on T7.

## Phase 4 — review and finalize

- [x] T9 — Independent review; propose one commit bundling the work; do not commit. Done: CodeRabbit plus an independent agent review, verdict PASS with findings, recorded in `review_01.md` with the handoff in `review_handoff.md`. All 11 findings fixed, including a MAJOR cross-cutting one the agent's own sweep had missed.

## Deviations

- 2026-09-03 — First draft described a tree the rollback had already destroyed; found by external review, not by me. Re-baselined.
- 2026-09-03 — Second draft was over-built: ~30 tasks, a concurrency commitment resting on three unmeasured numbers, and a re-invention of the schema-version mechanism that already exists. Found by external review. Replaced with the nine tasks above. Verified three of the review's load-bearing claims directly: a schema-version change already drops and rebuilds the index; `e22ef34` already escalates on missing/error/empty; and the 1,739-PDF figure I labelled "verified" was marked "not run" in its own source.
- 2026-09-03 — T1 also had to decide what `--retry-failed` does with a truncated row. `_should_skip` compared the status to the literal `ok`, so recording truncation would have made every retry pass re-OCR the same capped pages for hours. Changed the check to treat any `ok…` status as done, which is what the spec's "only ever finished by a deliberate re-run at a raised cap" requires. Covered by a regression test.
- 2026-09-03 — T2's periodic commit is on a clock (`REFRESH_COMMIT_SECONDS`, 30 s), not a file count. A count loses up to N scanned books on the OCR pass, where N books can be many hours; a clock costs at most one interval whether the walk is doing instant text files or one slow book.
- 2026-09-03 — T4 added one recipe, not two. `lf-refresh-retry` already was the retry pass; it was re-worded as "pass 2 of 2" rather than duplicated under a second name. Both passes and their order now appear in `just --list` and in the justfile header.
- 2026-09-03 — Restored the `PDF OCR fallback` section the revert removed from `tech.md`, and documented the truncation status, the reply framing, the two-pass order and the WAL/periodic-commit durability there and in `README.md`. `workflow.md` requires `tech.md` to lead implementation, and it was describing code that is now present again.
- 2026-09-03 — Also added the schema-version regression test the spec's claim in scope item 3 rested on. There was none: the "mechanism already exists" was true but untested.

## Noticed — not touching

- `tools/library_folders.py` — the OCR kill switch matches only the literal `"0"`, so `VICAYA_LIBRARY_FOLDERS_OCR=false` silently leaves OCR on. Wrong direction to fail for an escape hatch, but out of this thread's scope.
- `pyproject.toml` — `onnxruntime` has no version floor; this stack is sensitive to ONNX runtime versions.
- `tools/library_folders.py` — `_delete_missing_documents` still reads every row into Python and matches roots by exact string. Deferred by the spec.
- `test_search_works_while_a_refresh_holds_an_open_write` passes with WAL off too, because SQLite's rollback-journal mode also lets readers in until the writer commits. It asserts a real requirement from the spec but is not WAL-discriminating; the WAL pragma is covered separately.
- 2026-09-03 — Engine sanity check at the user's request (`measurements.md`). Tesseract vs pdf-inspector, with ground truth built by re-rendering a text-layer PDF as an image-only PDF. Roughly tied on speed and search quality; tesseract loses every IAST diacritic; pdf-inspector stalls on 17 % of real scanned books (2 of 12) and the whole-file timeout then discards up to 130 already-OCR'd pages. Engine kept; the timeout granularity was the real defect.
- 2026-09-03 — T10 added, replacing the whole-file timeout with a per-chunk one. `spec.md` deferred this "only if wedged books are observed burning the full timeout in practice"; that condition fired in 2 of 12 books, so the deferral resolved to *do it*. The worker now streams one framed reply per chunk and the parent bounds each chunk (`OCR_CHUNK_TIMEOUT`, 120 s — 6x the slowest chunk observed), keeping the finished pages and recording `partial: ocr stalled at page N of M` (deliberately not an `ok…` status, so `--retry-failed` revisits it). `OCR_SUBPROCESS_TIMEOUT` stays as a whole-file backstop.
- 2026-09-03 — The chunk reader is a thread plus a queue rather than a poll on the pipe: a wedged worker leaves the read blocked forever, so only a separate thread lets the deadline fire. It also means the reader works against any file-like object, which is what makes the stall path testable at all.
- 2026-09-03 — Projected effect on a full run over ~2,000 scanned books: about 240 h down to about 87 h, and no book left wholly unindexed.

## Corrections to my own earlier reporting in this thread

- I reported pdf-inspector at 0.68 s/page. That was one easy book. Across ten real books the median is 1.18 s/page — no faster than tesseract.
- I suggested diacritic-heavy scans were the likely failure mode. They are not: both Pāḷi Text Society journals, the Milindapañha and Mayrhofer's *Handbuch des Pali* all completed. The two stalls were English philosophy and psychoanalysis.
- Nobody in this thread, including me, tested the engine choice against the tesseract already installed on the machine until the user asked. The dependency weight had been questioned in review; the engine choice never was.
