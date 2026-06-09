# Spec — Folder Corpus: extract more file types

## Problem
The folder-corpus index (`tools/folder_corpus.py`) leaves ~5,150 of 32,552 docs
(16%) unextracted. Many are text-bearing formats currently marked
`unsupported:` or `empty`. Measured distribution of the non-`ok` files:

| Bucket | Count | Disposition |
|---|---|---|
| Kindle/Mobipocket: `.mobi` 1277, `.azw3` 826, `.prc` 95, `.azw` 52, `.lit` 27, `.pdb` 1, `.chm` 2 | ~2280 | **extract** via `ebook-convert` (Calibre, already installed) |
| `.rtf` | 351 | **extract** via `ebook-convert` |
| `.mht`/`.mhtml` web archives | 42 | **extract** via stdlib `email` + HTML strip |
| `.pptx` | 30 | **extract** via existing zip pattern (`ppt/slides/*.xml`) |
| misc text: `.json` 4, `.jsonl` 11, `.py` 1, `.shtml` 8, `.xht` 1, `.xml` 1 | ~26 | **extract** as text / HTML |
| audio/image: `.mp3` 355, `.ram` 7, `.tif` 1, `.jpg-old` 2 | ~365 | **reclassify as noise** (not text) |
| `.zip` 1209, `.7z` 3, `.bz2` 1 archives | ~1213 | **deferred** (the wall) |
| `empty` (no text after extract) | 764 | **deferred** — mostly image-only PDFs needing OCR |
| `.djvu` 5, spreadsheets ~6, corrupt PDFs ~30 | ~40 | **deferred** — niche / needs OCR / corrupt |

## Approach
Tackle low-hanging fruit first, easiest → hardest, stop at the wall. No new
dependencies — `ebook-convert`, `pandoc`, `catdoc`, `7z` are already on PATH;
`.mht`/`.pptx`/misc are stdlib.

The big win is wiring `ebook-convert` as a fallback extractor for the ebook
family + RTF: ~2,630 files recovered, coverage 84% → ~92%.

## Deferred (the wall)
- `.zip`/`.7z`/`.bz2` archives — ambiguous contents, can be huge; needs a
  separate design (recurse-and-index members vs skip).
- `empty` results — most are image-only scanned PDFs; recovering them needs OCR
  (Tesseract), a heavy dependency. Out of scope here.
- `.djvu` (needs `djvutxt`, not installed), spreadsheets (low value), corrupt
  PDFs (unrecoverable).

## Done when
- `extract_text` handles the ebook family, `.rtf`, `.mht`/`.mhtml`, `.pptx`, and
  the misc-text formats above.
- Audio/image extensions are in `NOISE_EXTENSIONS` and no longer indexed.
- New unit tests cover each added path; `ruff`/`pyright`/`pyrefly`/`pytest` pass.
- `tech.md` updated to mention `ebook-convert` as a folder-corpus extractor.
