# Spec: swap the OCR backend to ocrmypdf, and wire in diacritic restoration

**Goal:** replace the hand-rolled OCR pipeline with `ocrmypdf`, delete the bespoke worker that caused the unkillable deadlock, and add diacritic restoration so the switch costs nothing in quote fidelity.

Decided by measurement in `kamma/threads/20260903_ocr_bakeoff/` — read `measurements.md` and `swap_scope.md` there before starting, **then `scope_audit.md` in this thread**, which found 4 blocking gaps in that scope note and whose corrections are already folded into `plan.md`. No GitHub issue.

## Why

The bake-off measured three candidates against a rule committed before any number existed. Results:

| | projection for 263,524 pages | memory/unit | books stalled | word accuracy |
|---|---:|---:|---:|---:|
| **ocrmypdf** | **1.32 days** | 488 MB | 0 of 22 | 91.7 % |
| incumbent | 4.31 days (user observed 6) | 5.0 GB | 4 of 22 (18 %) | 96.1 % |
| tesseract direct | 10.8 days | ~900 MB | 1 of 22, a 30-min stall | 92.0 % |

ocrmypdf wins on speed (**3.27×** the incumbent's projection like-for-like, both sides OCR-only — the 4.5× against the observed six days is a looser mixed-basis figure), on memory (10× less, which is what caps the incumbent at 3-way), and on robustness (zero stalls against the incumbent's 18 %). The incumbent's only remaining advantage was diacritic preservation — and Phase 6 measured that loss as **recoverable at 99.7 %** by a frontier model, from resources this project already owns. Mid-tier models reach only ~85 %, so the tier is a cost decision (plan T14). The memorisation control was never run, so treat the figure as an optimistic bound until plan T12 closes it.

## What this thread does

1. Swap the OCR backend to `ocrmypdf` and delete the bespoke machinery.
2. Add the two mandatory safety behaviours the bake-off found by measurement.
3. Wire diacritic restoration into the **quote path**, not the index path.

## Scope of the deletion

`swap_scope.md` in the bake-off thread is the authoritative list: 14 symbols with line numbers, two dependencies (`pdf-inspector`, `onnxruntime`), one now-unused `.env` key (`PDFIUM_LIB_PATH`), and the cross-file status-vocabulary contract. **Re-verify every line number against the current file before editing** — that document was written on 2026-09-04 and the tree is shared.

## Mandatory behaviours, both measured not assumed

**1. Pre-decrypt encrypted PDFs.** ocrmypdf refuses them outright (`EncryptedPdfError`, rc=8). **43 of 1,735 pending books (2.5 %)** are affected — measured across the whole population, not extrapolated. Verified fix: open with `pikepdf` and save to a temp file, then OCR that. **`pikepdf` must be added to `pyproject.toml`** — the bake-off's claim that it was already available was verified against the system Python, not the project venv, which has `include-system-site-packages = false`. These carry an empty user password, so no credentials are involved. Without this, 43 books fail silently-ish.

**2. Detect implausibly short output.** Both tesseract-based candidates returned **84 characters for an entire 85-page book** while reporting success — a book the incumbent read correctly (211,181 characters). A return code cannot catch this. Flag any book whose character count is far too low for its page count and give it a distinguishable status. **n=1**: the population rate is unknown, which is exactly why the detector is required rather than optional.

## Diacritic restoration — where it goes, and where it must not

**Restoration belongs on the quote path only.** The FTS index uses `unicode61 remove_diacritics 2` and folds diacritics on both sides of a query — verified. Search therefore never needed diacritics, and restoring them across 263,524 pages would be pure waste. Restore the handful of passages a researcher actually cites, at citation time.

**Do not write restored text back into the index.** The index is the search substrate; a restoration pass over it would be expensive, unverifiable at scale, and would put model output where measured OCR output belongs. Stored text stays as ocrmypdf produced it.

Measured accuracy (token-weighted, 303 diacritic tokens unless noted):

| approach | accuracy |
|---|---:|
| do nothing (what ocrmypdf stores) | 0 % |
| DPD lexicon, unique matches only | 8.6 % |
| DPD + usage-frequency prior from `data/scratch/` | 72.2 % |
| Haiku 4.5, context only | 80.7 % |
| Sonnet 5, context only | 84.7 % |
| DeepSeek V4 Flash, context only | 85.6 % |
| **Opus 5, context only** | **99.7 %** (CI 98.1–99.9, n=297/303) |

## Decision rule for this thread

Committed before implementation:

| Gate | Threshold | Why |
|---|---|---|
| Throughput | ≥ 3× faster than the incumbent on a real multi-book run | the whole point; below this the swap is not worth the churn |
| Memory | ≤ 1 GB per concurrent unit at the chosen parallelism | measured 488 MB; anything near the incumbent's 5 GB means something is wrong |
| Robustness | zero unrecoverable failures across the bake-off's 22-book corpus, including both encrypted books and both named stallers | the two mandatory behaviours must demonstrably work |
| Test suite | 452 passed, 1 skipped or better, with the real-hung-subprocess regression test preserved in equivalent form | a mock that returns immediately is how the original deadlock passed 452 tests |
| Restoration | ≥ 95 % on the bake-off's fixture **through the shipped code path**, or the residual error rate stated wherever a restored quote appears | below that it misleads more than it helps |

## Assumptions to verify, not inherit

- **A1** that `--optimize 0` and dropping `--force-ocr` are safe speedups. Both look free (this pipeline wants only the sidecar text) but **neither was measured**. Measure before adopting.
- **A2** that ocrmypdf's zero stalls hold beyond 22 books. The incumbent's stall rate was 18 % on the same corpus, so this is a real difference — but 22 books is 1.3 % of the population.
- **A3** that removing `OCR_PAGE_CAP` is safe. It exists because the incumbent got heavier per page; ocrmypdf may not need it, but the `ok: ocr truncated …` status disappears with it and three files read that vocabulary.
- **A4** that the restoration figure survives a memorisation control. **T20 of the bake-off was never run** — the 98.2 % rests on a published book a model may have seen. Run that control before promising 98 % to a user.

## Constraints

- Never modify `.env`. Tell the user `PDFIUM_LIB_PATH` is unused; let them remove it.
- `ocrmypdf` is a **system** package, not a uv dependency — `uv sync` will not install it. A missing binary must degrade gracefully by returning `None` from a `shutil.which` probe, mirroring the `pdftotext` pattern already in the file. **Correction from the scope audit:** the kill switch is *not* this mechanism — it is an explicit user opt-out, and the real availability probe is the `ImportError` guard the swap deletes. See plan T2a.
- Shared tree: no `git stash`, no whole-tree checkout or reset, no commits unless asked.
- The user runs any long job in their own terminal. Do not start a full rebuild from an agent session.
- The live index is read-only to this thread except through the normal refresh path.

## How we'll know it's done

- A real multi-book OCR run through the new backend, with the measured rate stated next to the bake-off's 0.433 s/page.
- Both encrypted books and both named stallers processed successfully.
- The bespoke worker, framed protocol, per-chunk timeouts, reader thread and page cap gone, with `rg --hidden` showing no orphaned readers.
- Restoration available on the quote path, with its measured accuracy and the memorisation caveat stated to the user.
- Full suite green, with real-subprocess coverage for the new failure paths.

## What's not included

- Restoring diacritics in the stored index. Explicitly out of scope, see above.
- Re-litigating the bake-off. If a number looks wrong, measure it again and record a finding; do not quietly adopt a different conclusion.
- Fine-tuning any OCR or restoration model.

## Confidence

8 of 10 that the swap lands cleanly — the measurements are solid and the deletion scope is mapped. 5 of 10 on the restoration UX, which is genuinely undesigned: nobody has decided what a researcher sees when a quote is restored, or how they are told it is model output rather than what the page says. That is the part most likely to need a conversation with the user before code.
