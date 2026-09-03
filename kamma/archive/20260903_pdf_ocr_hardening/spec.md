# Spec: reintroduce PDF OCR, plus durable refresh

**Goal:** PDFs with no usable text layer get OCR'd as a fallback, and a long refresh survives interruption.

Baseline `65e3bd1`. 410 tests passing. No GitHub issue.

## Scope

1. Re-add the OCR fallback from `e22ef34` unchanged, except: record truncation in the status string when the 150-page cap cuts a book short. Escalation on missing/error/empty is already the original behaviour — nothing to do.
2. Make refresh durable: write-ahead mode on open, and commit every N files during the walk, so an interrupted run keeps what it finished.
3. Bump `SCHEMA_VERSION` from `"2"` to `"3"` so the index rebuilds once with the new extractor. This *is* extractor versioning — the mechanism already exists and drops the index on mismatch.
4. Two recipes: text-only pass, then the retry pass for OCR, with the order stated in help text.

Everything else is out of scope.

## Decisions already made — do not re-litigate

- OCR only as a fallback, when no text was obtained.
- Rebuild runs in two passes, text first.
- Full 150-page cap; one complete pass, not a shallow sweep.
- Truncation is recorded. A capped book is only ever finished by a deliberate re-run at a raised cap.
- The reading-order (`-layout`) decision stands on the original four-book benchmark. A table-heavy or interlinear book was never tested; that risk is knowingly accepted.

## Deferred to separate threads

- **Concurrency.** Only if a real measured run proves a single worker too slow. It is also the highest-risk change available here: several workers writing one SQLite index is how you get lock errors or a corrupt index, and it needs a producer/consumer design with a single writer. Not on a forecast.
- **Per-chunk timeout bounds.** Only if wedged books are observed burning the full timeout in practice.
- **Deletion-guard cleanup** (reads all rows into memory; exact-string root matching can silently disable cleanup). Working and tested; orthogonal to OCR.
- **Health check reporting ok on an empty index.**

## Corrections to my earlier work

Recorded so no one inherits them.

- I claimed the reading-order change was never measured. **False** — the original spec documents a four-book benchmark.
- I claimed silent truncation was an undiscovered defect. **False** — it was a documented, accepted trade-off. Recording it is a reversal of an approved decision, not a bug fix.
- I narrowed OCR escalation to empty-only. **Wrong**, and dropped.
- I presented "1,739 PDFs with no text layer" as a verified input and built a three-day throughput forecast on it. **The source explicitly marked that figure "not run".** The forecast, and the concurrency work it justified, are withdrawn.
- My first draft of this spec described a tree that the rollback had already destroyed, because I reverted the repo and never updated the document.

## Done when

- A real scanned book from the library OCRs end-to-end, not a stub. The original feature shipped 13 passing tests and was never once run outside mocks.
- Killing a refresh mid-run retains the files it finished.
- Search works while a refresh runs.
- Both passes are runnable by command.

## Confidence

High. Nothing speculative remains: no forecast, no unmeasured arithmetic, and the one genuinely risky idea is deferred until a real run justifies it.
