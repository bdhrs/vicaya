# Handoff for independent review — PDF OCR hardening

Written 2026-09-03 by the implementing agent, for a reviewer starting with no context from the implementation session. Everything below is uncommitted working-tree state.

## What you are reviewing

Baseline for the change: `65e3bd1`. Current `HEAD` is `6684cd3` — two `chore: update runs` commits from a parallel session landed mid-work and are unrelated to this thread.

Modified, all by this thread:

| file | what changed |
|---|---|
| `tools/library_folders.py` | re-added the PDF OCR fallback; per-chunk timeout; WAL + periodic commit; schema version 3 |
| `tests/test_library_folders.py` | +31 tests (59 → 90 in this file) |
| `justfile` | new `lf-refresh-text` recipe; two-pass order in the header and doc-comments |
| `README.md` | two-pass rebuild, truncation status, durability |
| `kamma/tech.md` | restored the `PDF OCR fallback` section the revert deleted, plus the new behaviour |

Untracked, all thread documents: `spec.md`, `plan.md`, `measurements.md`, `review_handoff.md` (this file), plus two pre-existing files written before the implementation session — `prior_review.md` (reviews the reverted implementation `e22ef34`) and `review_external_01.md` (reviews an earlier draft of the spec and plan). Neither of those two reviews has seen the current code.

**No review has yet examined this implementation.** Plan task T9 is open. That is why you are here.

## Read these first, in this order

1. `spec.md` — what was agreed, including a "do not re-litigate" list and a deferred list.
2. `measurements.md` — the benchmark that changed the plan mid-thread. Load-bearing; challenge it.
3. `plan.md` — tasks, plus a `Deviations` section and a `Corrections to my own earlier reporting` section.

## History you need, because the tree lies about it

The OCR feature originally shipped as `e22ef34`, was reviewed harshly (`prior_review.md`), and was then **reverted** by `8a5952a`. An earlier planning session wrote a spec describing a tree that the revert had already destroyed; an external reviewer caught it and the documents were re-baselined. So: `git log` contains a full OCR implementation that is *not* the one under review, and the thread contains two reviews of things that no longer exist. Do not confuse them with the current code.

## The mid-thread pivot

`spec.md` says to re-add the OCR fallback "unchanged". That instruction was not followed to the letter, deliberately.

The user asked, correctly, whether the whole `pdf-inspector` + `onnxruntime` + PDFium stack was over-engineered next to the `tesseract` already installed on the machine. Nobody in the thread — including the implementing agent — had ever tested that. The measurement is in `measurements.md`. Summary: the two engines are roughly tied on speed and on search quality; tesseract loses every IAST diacritic (0 of 135, against 134 of 135); and `pdf-inspector` stalls mid-book on 17 % of attempts (2 of 12 random scanned books), where the old whole-file timeout then charged 1800 s and discarded every completed chunk — one book lost 130 of 150 already-OCR'd pages.

Conclusion drawn: the engine was not the defect, the timeout granularity was. The engine was kept and a per-chunk timeout added as task T10. That is the single largest change beyond the spec, and the one most worth a second opinion.

## Claims that are load-bearing — please attack these

- **That a per-chunk timeout is the right fix**, rather than switching engines or adding concurrency. Projection: ~240 h → ~87 h over the library's ~2,000 scanned books, no book wholly unindexed. The projection arithmetic is in `measurements.md`; the inputs are a 17 % stall rate (Wilson 95 % CI 4.7 %–44.8 %, n=12) and a 9.9 % scanned-book fraction (12 of 121 candidates examined, size- and page-filtered).
- **That a stalled row must stay retryable while a page-cap truncation must not.** Stalls proved intermittent — both stalling books completed on the next attempt — so a stall is `partial: ocr stalled at page N of M` and gets re-extracted, whereas a cap truncation is `ok: ocr truncated at 150 of 600 pages` and is skipped. `_should_skip` implements this as "any status starting with `ok` is done". Is that prefix test too blunt?
- **That the accuracy comparison was fair.** Ground truth was built by rendering 10 pages of a real text-layer PDF to 300 dpi greyscale and rebuilding them as an image-only PDF, because `process_pdf_with_ocr` is *selective* and simply reads an existing text layer (0.20 s for 10 pages) rather than OCRing. Tesseract was given `pdftoppm` rasterisation plus one process per page at 10-way parallelism, since `pdf-inspector` was observed using ~5 cores. Is that like-for-like?
- **That the diacritic loss does not matter for search.** The FTS tokenizer is `unicode61 remove_diacritics 2`, verified to fold diacritics on both sides of a query. Restricted to the 33 diacritic-bearing word types in the sample, findability after folding was tesseract 29/33 vs `pdf-inspector` 27/33.

## Verification status — what is and is not proven

Green: 441 tests pass repo-wide; `ruff check`, `ruff format --check`, `pyright` and `pyrefly` all clean on both touched Python files.

Verified against real data:

- OCR end-to-end on real scanned books: 107 pages → `ok`, 87,782 chars, 72.6 s. Also 456- and 587-page books → `ok: ocr truncated at 150 of N pages` with 357,797 and 452,606 chars.
- A whole-file hang on a real book, before the fix: 1800 s timeout, 0 chars.
- Stall rate on 12 random scanned books: 2 wedged, 10 completed.
- WAL and the periodic commit: both proven fail-before/pass-after by temporarily reverting each and re-running the tests.

**Not verified against real data:**

- **The stall recovery path never fired live.** When the two stalling books were re-run through the fixed code they both completed, so `partial: ocr stalled…` and the keep-the-finished-chunks behaviour are covered by unit tests only. This is the biggest gap. The unit tests fake the worker process; check whether the fake faithfully models a wedged child.
- Tesseract's zero-stall record is n=2 real books plus one synthetic. It was never run against the same 12. Irrelevant while the engine stays, but do not let the write-ups overstate it.
- `test_search_works_while_a_refresh_holds_an_open_write` passes with WAL off too, because SQLite's rollback-journal mode also admits readers until the writer commits. It asserts a real spec requirement but does not discriminate WAL. Noted in `plan.md`.

## Findings already known — confirm, refute, and find what we both missed

From CodeRabbit (`coderabbit review --agent --uncommitted --include-untracked`, 2 findings, both judged valid, **both still open**):

1. `plan.md` T10 deviation text still says the stalled status is `ok: ocr stalled…`. Stale: the status became `partial:` afterwards. Documentation only.
2. The first chunk shares the ordinary `OCR_CHUNK_TIMEOUT`, but it also absorbs interpreter startup, `pdf_inspector` import, ONNX runtime init, PDFium load, and — on a machine that has never run OCR — a one-time model download. A slow first download could be read as a stall. Not a risk on this machine, where the models are already cached, so every timing in `measurements.md` is warm-start. Real for a fresh install.

Found by the implementing agent's own audit, **all still open**:

3. `_ocr_worker_main` is dead in production. The worker snippet drives `_ocr_worker_chunks`; the aggregate wrapper survives only because six tests call it. The type checker already reports it unaccessed. The tests do reach the real generator through it, so this is not a false green, but it is the shape of one — please check that judgement rather than taking it.
4. The `_extract_pdf_ocr_fallback` docstring still describes the old design: "bounded by `OCR_SUBPROCESS_TIMEOUT`", and only the page-cap status. Stale on the very function that was rewritten.
5. `proc.stdout` is never closed — no `with proc:` and no explicit close, so a pipe per book relies on garbage collection. ~2,000 books per full pass.
6. If the `meta` reply is lost, `page_count` stays 0 and `_ocr_status` returns plain `ok` even for a truncated or stalled book. Low likelihood, wrong label.

Deliberately out of scope, recorded in `plan.md` under `Noticed — not touching`: the OCR kill switch matches only the literal `"0"`, so `=false` leaves OCR on; `onnxruntime` has no version floor; `_delete_missing_documents` reads all rows into Python and matches roots by exact string.

## Where to look hardest

`_collect_ocr_chunks` in `tools/library_folders.py` is the new concurrency-adjacent code and the least exercised. It runs a daemon reader thread feeding a queue, because a wedged worker leaves `readline` blocked forever and only a separate thread lets the deadline fire. Consider: the thread's lifetime after `proc.kill()`; whether a partial line can be mis-framed; whether the marker scan can be fooled by a chunk whose OCR'd text happens to contain the marker string; behaviour when the child writes a very large single line; and whether `OCR_SUBPROCESS_TIMEOUT` as a whole-file backstop can still strand a book with text on the floor.

Second: the `ok`-prefix contract now spans `_ocr_status`, `_should_skip`, the two `just` recipes, `README.md` and `tech.md`. Check they agree, and that no other reader of `extraction_status` was missed.

## Rules for you

- **Do not run a library refresh, and do not touch the index.** A full rebuild is running in the user's own terminal right now. The index lives outside the repo at the path in `$VICAYA_LIBRARY_FOLDERS_INDEX`.
- Never modify `.env`. Never run `git stash` or any whole-tree checkout/reset — this tree is shared with other agent sessions with their own uncommitted work.
- Do not commit. The user commits.
- Scoped checks only: `uv run pytest tests/test_library_folders.py -q`, and `ruff check` / `pyright` / `pyrefly check --search-path .` on the two touched Python files. The full suite is `uv run pytest -q` and takes ~40 s.
- OCR needs the environment sourced (`set -a; . ./.env; set +a`) or `PDFIUM_LIB_PATH` is unset and every OCR attempt fails.
- Benchmark scripts from the measurement session are in this session's scratchpad, not the repo, and will not survive. `measurements.md` records the method well enough to rebuild them.

## What a useful review returns

A verdict on the pivot: was keeping the engine and bounding each chunk the right call on the evidence given, or does the evidence support something else. Then confirmation or refutation of findings 1–6, and anything neither the implementing agent nor CodeRabbit saw — with priority on correctness of `_collect_ocr_chunks` and on whether any status-string reader was missed.
