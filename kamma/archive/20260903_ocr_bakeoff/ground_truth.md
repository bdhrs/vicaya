# Phase 1 — ground truth (T4)

Built 2026-09-03.

## Source

`Bodhirasa eBook Library/T.W. Rhys Davids/Pali Text Society Pali-English Dictionary (2162)/Pali Text Society Pali-English Dictionary - T.W. Rhys Davids.pdf` — a Pāḷi-English dictionary with a live text layer (`extraction_status='ok'` in the index), every headword carrying IAST diacritics. Pages 50–69 (20 pages) selected.

## Build steps

1. `pdftotext -f 50 -l 69` on the source → the answer key text, kept as the correct reading.
2. `pdftoppm -f 50 -l 69 -r 300 -gray -png` on the source → 20 greyscale PNGs at 300 dpi.
3. `img2pdf` (installed as an ocrmypdf dependency, `python3-img2pdf`) assembled the 20 PNGs into `ground_truth.pdf` — an image-only PDF with no text layer, only the rendered page images.

## Verification

- `pdftotext ground_truth.pdf -` → 20 bytes total, all `\f` (form feed, one per page break). Zero actual characters — confirms the rebuilt PDF has no text layer, per spec's verify line.
- `pdfinfo ground_truth.pdf` → 20 pages, matches source range.
- Answer key diacritic count: **1,233** IAST diacritic characters (āīūṃṅñṭḍṇḷṛ and capitals), well over the ≥100 threshold.

## Artifacts (session scratchpad, not committed)

- `ground_truth.pdf` — the image-only 20-page PDF every candidate OCRs.
- `answer_key.txt` — the original text-layer extraction, the correct answer for scoring in Phase 3.
