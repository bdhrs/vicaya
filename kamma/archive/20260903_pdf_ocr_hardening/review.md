# Independent review 01 — of the implementation

Reviewed 2026-09-03 by an independent agent working from `review_handoff.md`, plus a CodeRabbit pass.

**Verdict: PASSED** — "PASS with findings, no blocking issues". Every finding has since been fixed, so nothing is outstanding against the code.

The reviewer confirmed the mid-thread pivot (keep `pdf-inspector`, bound each chunk instead of the whole file) as correct and correctly arrived at, judged `_collect_ocr_chunks` and the timeout/status semantics correct, and — the item the handoff asked to be checked hardest — judged the stall fake faithful: `_FakeWorkerStdout.readline()` blocks rather than returning empty after the canned lines, which is what forces the reader-thread design and lets the deadline fire.

One caveat accepted as stated: the 240 h → 87 h projection rides on a 17 % stall rate with a 95 % CI of 4.7 %–44.8 % at n=12. It is an order-of-magnitude estimate, not a promise. It no longer drives a build decision, because concurrency stays deferred.

## Findings and resolution — all 11 fixed

| # | source | finding | resolution |
|---|---|---|---|
| 1 | CodeRabbit | `plan.md` T10 still said the stalled status was `ok: ocr stalled…` | wording corrected to `partial:` |
| 2 | CodeRabbit | the first chunk shares the ordinary deadline but also pays startup, imports, ONNX init, PDFium load and a one-time model download | added `OCR_FIRST_CHUNK_TIMEOUT` (600 s) for the first chunk only, with a test asserting it exceeds the per-chunk bound |
| 3 | self-audit | `_ocr_worker_main` dead in production, alive only via six tests | deleted; the six tests now drive `_ocr_worker_chunks` through `_drain_ocr_worker`, which mirrors the production reduction |
| 4 | self-audit | `_extract_pdf_ocr_fallback` docstring described the pre-rewrite design | rewritten to describe per-chunk bounds and the status contract |
| 5 | self-audit | `proc.stdout` never closed, ~2,000 books per pass | explicit close, plus a test asserting the pipe is closed |
| 6 | self-audit | a lost `meta` reply left `page_count` 0, so `_ocr_status` returned a complete `ok` | guarded on `page_count > 0`, with a test |
| 7 | **review, MAJOR** | `skill/vicaya/SKILL.md` tested `extraction_status` for literal equality with `"ok"` in two places | see below |
| 8 | review | `tech.md` named `_ocr_worker_main` as the subprocess entry point; it is `_OCR_WORKER_SNIPPET` driving `_ocr_worker_chunks` | corrected, and the per-chunk bound is now described as the live bound rather than `OCR_SUBPROCESS_TIMEOUT` |
| 9 | review | the `ok`-prefix contract spanned five files as a bare `startswith` | extracted as `extraction_succeeded()`, documenting the whole vocabulary in one place; `_should_skip` now calls it; 7 parametrized contract tests |
| 10 | review | a worker that crashed mid-book was labelled `stalled` | now `partial: ocr worker died at page N of M`, with a test |
| 11 | review | the reader thread was never joined | joined with a 5 s timeout alongside the pipe close |

## Finding 7 in full, because it is the one that mattered

`skill/vicaya/SKILL.md` told the research agent that any status other than exactly `"ok"` was a refresh gap, and to extract manually with `pdftotext`. Under the new vocabulary a scanned book OCR'd to the page cap is `ok: ocr truncated at 150 of 600 pages` — 150 searchable, quotable pages. The skill would have declared it not indexed, logged it as a Critical Gap, and sent the agent to run `pdftotext` on it: precisely the extraction that already returned nothing and caused OCR to run.

This is the cross-cutting contract break the thread existed to prevent, in the consumer the feature serves. The skill now reads the status by prefix with each case spelled out (`ok`, `ok: …`, `partial: …`, and the failure statuses), and is told explicitly not to hand-run `pdftotext` on a scanned PDF whose status mentions `ocr`.

Root cause worth keeping: the implementing agent swept `tools/`, `tests/`, `README.md` and `tech.md` for `extraction_status` readers and stopped there. The project's own guidance says to enumerate the non-obvious roots — skill and prompt files among them — and it was not followed. The sweep that found it was `rg --hidden -n 'extraction_status' --glob '!.git' .`

## State after the review

452 tests pass repo-wide. `ruff check`, `ruff format --check`, `pyright` and `pyrefly` all clean on both touched Python files. Twelve tests were added addressing the findings; one of them exposed a mistake in an earlier test of this thread, which patched the ordinary chunk deadline for a case governed by the first-chunk deadline.

## Still not verified, carried forward

- The stall recovery path has never fired against a real wedged child. Both books measured as stalling completed on re-run, so `partial: ocr stalled…` is covered by unit tests with a faked worker only. The user's full rebuild is the first live exercise.
- Cold start is unmeasured. Every timing in `measurements.md` is warm-start, with the OCR models already cached.
- Tesseract's zero-stall record is n=2 real books plus one synthetic; it was never run against the same 12. Moot while the engine stays.
