# Measurement: tesseract vs pdf-inspector, 2026-09-03

Run at the user's request as a sanity check on the engine choice, which no
earlier thread ever tested. Machine: 22 cores, load 0.4–2.7 during runs.
Every timing is a fresh process; synthetic-scan figures are the median of 3
after a discarded warmup.

## Method

`pdf-inspector`'s `process_pdf_with_ocr` is *selective* — on a PDF that has a
text layer it reads the layer and never OCRs (0.20 s for 10 pages), so a
text-layer PDF cannot be used to compare OCR directly. Instead: take 10 pages
of a real text-layer PDF (an 84000 translation, heavy in IAST diacritics),
render them to 300 dpi greyscale images, and rebuild them as an image-only PDF
with no text layer. Ground truth is the original text layer; both engines face
the same page images with a known correct answer.

Tesseract is run as the full pipeline it would need in production: `pdftoppm`
rasterise plus one `tesseract` process per page, `OMP_THREAD_LIMIT=1`, 10
parallel jobs. Single-job figures are given too, because pdf-inspector was
observed using ~5 cores, so a 1-job tesseract comparison is not like-for-like.

## Synthetic scan — 10 pages, ground truth known

| engine | wall clock | s/page | word acc (diacritics folded) | word acc (strict) | diacritics kept |
|---|---|---|---|---|---|
| tesseract, 1 job | 37.6 s | 3.76 | 0.954 | 0.907 | 0 / 135 |
| tesseract, 10 jobs | 14.1 s | 1.41 | 0.954 | 0.907 | 0 / 135 |
| tesseract, 10 jobs, psm 3 | 14.1 s | 1.41 | 0.954 | 0.907 | 0 / 135 |
| pdf-inspector | 16.5 s | 1.65 | 0.979 | 0.977 | 134 / 135 |

Character-level similarity is much lower for tesseract (0.657 vs 0.967) but
that is mostly reading order and marginal page numbers, not character errors —
word accuracy stays high.

## Diacritics

Tesseract's `eng` model has no IAST glyphs, so every one of 135 Pāḷi/Sanskrit
diacritics is lost: `Ākāśagarbha` → `Akagagarbha` / `Akaéagarbha`, `sūtra` →
`sutra`, `Vajrayāna` → `Vajrayana`. pdf-inspector keeps 134 of 135.

This matters less than it looks, because the FTS index is built with
`unicode61 remove_diacritics 2` — it folds diacritics on both sides of a
query. Verified directly: a search for `sūtra`, `sutra`, `Ākāśagarbha` or
`akasagarbha` all match either engine's output. Only a genuine letter
substitution (`ś` → `g`, giving `Akagagarbha`) becomes unfindable.

Restricted to the 33 truth word types that carry a diacritic, findability
after folding:

| engine | findable |
|---|---|
| tesseract | 29 / 33 = 87.9 % |
| pdf-inspector | 27 / 33 = 81.8 % |

So for *search* tesseract is not worse; it is marginally better. The loss is
confined to quote fidelity — text pasted into a note keeps the wrong letters.

No stock tesseract model fixes this. `san` and `hin` are Devanagari, the wrong
script entirely. `script/Latin.traineddata` would at best add macrons
(Latvian/Māori use them); no language tesseract trains on uses the under-dots
`ṭ ḍ ṇ ṃ ḷ ṣ` or `ś`. Covering IAST would mean fine-tuning a model.

## Real books from the library — the result that decides it

| book | pages | pdf-inspector | tesseract, 10 jobs |
|---|---|---|---|
| WhatisMeditation.PDF | 107 | 72.6 s, 87,782 chars, `ok` | 178.1 s, 89,455 chars |
| Naked Awareness.PDF | 150 (of 161) | **1800 s timeout, 0 chars** | 257.8 s, 721,871 chars |
| total | 257 | 1872.6 s, 87,782 chars | 435.9 s, 811,326 chars |

The second book wedged pdf-inspector: 30 minutes of wall clock, no CPU
activity for most of it (load 0.4 at 23 minutes in), zero output, book left
unindexed. That is the deadlock the subprocess isolation was built to survive,
and it did survive it correctly — but the book is still lost and the half hour
still spent. Tesseract read the same 150 pages in 4.3 minutes. Its output was
checked for garbage and is clean prose: 4,812 chars/page, mean word length
4.9.

Across the two real books tesseract is 4.3× faster and returns 9× more text,
entirely because one wedge dominates everything else.

## Caveat

n = 2 real books, one of which wedged. A 50 % wedge rate is not established by
one observation. The wedge rate across a sample of scanned books is the number
that decides how bad pdf-inspector actually is in production, and it has not
been measured.

## Consequence for this thread

`spec.md` says to re-add the OCR fallback from `e22ef34` unchanged. That
instruction now conflicts with measured evidence, so it cannot be followed
without a decision from the user. Options recorded, not chosen:

1. Swap the engine to tesseract. Drops `onnxruntime`, the manually-installed
   PDFium library, `ORT_DYLIB_PATH` plumbing and the first-run model download.
   Very likely also drops the subprocess-isolation design, which exists only
   because `process_pdf_with_ocr` deadlocks — tesseract is already one process
   per page, so a bad page costs one page instead of a whole book. Costs
   correct diacritics in stored text.
2. Keep pdf-inspector, accept that some books burn the full 1800 s timeout.
   Faster per page when it works (0.68 vs 1.66 s/page on a real book).
3. Measure the wedge rate over ~12 scanned books first, then decide.

## Wedge rate — 12 random scanned books, 2026-09-03

Sampled from all 20,428 library PDFs with a fixed seed, keeping files 0.5–60 MB
and ≥30 pages with no pdftotext text layer. 12 of 121 candidates examined were
scans, i.e. **~9.9 %, about 2,000 scanned books** in the library. This is the
first measured figure for that count; the earlier spec's withdrawn "1,739"
guess was the right order of magnitude.

Each book runs the production OCR path — 150-page cap, 10-page chunks — in a
child that reports per chunk, so a stalled chunk is distinguishable from a
merely slow book. Stall threshold 120 s against observed chunk medians of
8–18 s.

| verdict | books |
|---|---|
| completed | 10 |
| wedged | 2 |
| other/error | 0 |
| **wedge rate** | **2/12 = 17 %** (Wilson 95 % CI 4.7 % – 44.8 %) |

Completed books: mean 152.8 s, median **1.18 s/page**, mean 1.38 s/page.

Both wedges are unambiguous — normal chunks throughout, then one chunk that
never returns:

| book | chunks | median chunk | slowest chunk | already-OCR'd text discarded |
|---|---|---|---|---|
| Companion to the Philosophy Of | 13/15 | 18.3 s | 19.9 s | 383,475 chars (130 pages) |
| Psychoanalysis and Buddhism | 3/15 | 11.6 s | 12.6 s | 59,469 chars (30 pages) |

Diacritic-heavy scans were **not** the failure mode: both Pāḷi Text Society
journals, the Milindapañha and Mayrhofer's *Handbuch des Pali* all completed.
The two failures are English philosophy and psychoanalysis.

Because the production worker joins all chunks and returns only at the end, a
wedge discards every completed chunk. The first failure lost 130 successfully
OCR'd pages.

### Projection over ~2,026 scanned books

| approach | total wall clock | books left unindexed |
|---|---|---|
| pdf-inspector, measured 17 % wedge | 72 h useful + **169 h burnt on timeouts** = 240 h | 338 |
| pdf-inspector, CI low (4.7 %) | 82 h + 48 h = 129 h | 95 |
| pdf-inspector, CI high (44.8 %) | 47 h + 454 h = 501 h | 908 |
| tesseract, 1.70 s/page, 10 jobs | 118 h | 0 observed (n = 2) |
| pdf-inspector + per-chunk timeout | ~87 h | 0 fully lost |

At the measured rate, 70 % of a pdf-inspector run is spent waiting on books it
will never index.

### The deferred item has been triggered

`spec.md` deferred per-chunk timeout bounds with the condition "only if wedged
books are observed burning the full timeout in practice". They were, in 2 of 12
books. A per-chunk bound plus keeping the last good prefix converts a 1800 s
total loss into a ~30 s partial success, and is the single highest-value change
available — it cuts the projected run from 240 h to ~87 h and stops discarding
completed pages, without changing engines.

### Honest asymmetry

Tesseract has been run on 2 real books and one synthetic scan, never on these
12. Its zero-wedge record rests on n = 2, not on the same sample. A fair
comparison means running the same 12 books through tesseract — about 40
minutes.

## Follow-up: the stalls are intermittent, 2026-09-03

Re-running both stalled books through the fixed per-chunk code path: both
completed all 150 capped pages.

| book | first attempt | after the fix |
|---|---|---|
| Psychoanalysis and Buddhism | stalled after 3/15 chunks | `ok: ocr truncated at 150 of 456 pages`, 357,797 chars, 204.4 s |
| Companion to the Philosophy Of | stalled after 13/15 chunks | `ok: ocr truncated at 150 of 587 pages`, 452,606 chars, 253.2 s |

Two consequences.

The stall path is therefore **not** verified against real data — it did not
trigger. It is covered by unit tests only. Confirming it live needs a caught
stall.

More importantly the 17 % is a **per-attempt** rate, not a property of
particular books. That flips how a stalled row should be treated: a retry is
likely to succeed, so it must stay retryable. The stalled status was changed
from `ok: ocr stalled…` to `partial: ocr stalled…` for exactly that reason —
`_should_skip` re-extracts anything not starting with `ok`. Keeping it as an
`ok…` status would have kept the partial text forever and never completed the
book, which is the silent-incompleteness failure the original review objected
to.
