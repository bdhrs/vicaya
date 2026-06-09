# Plan — Folder Corpus: extract more file types

> Status: COMPLETE — reviewed (review.md, ACCEPTED), finalized 2026-06-09.

## Phase 1 — Misc text & HTML-ish formats (easiest)
- [x] Add `.json`, `.jsonl`, `.py` to plain-text extraction
- [x] Add `.shtml`, `.xhtml`, `.xht`, `.xml` to HTML/XML strip extraction

## Phase 2 — Reclassify audio/image as noise
- [x] Add audio (`.mp3`, `.ram`, `.m4a`, `.wav`, `.flac`, `.aac`, `.ogg`, `.wma`)
      and image/video (`.tif`, `.tiff`, `.jpg-old`, `.mp4`, `.avi`, `.mkv`,
      `.mov`, `.wmv`) to `NOISE_EXTENSIONS`

## Phase 3 — MHTML web archives
- [x] `_extract_mhtml`: stdlib `email` parse, collect text/html + text/plain
      parts, strip HTML. Wire `.mht`/`.mhtml` in `extract_text`

## Phase 4 — PPTX
- [x] Wire `.pptx` through `_extract_zip_members` (`ppt/slides/*.xml`)

## Phase 5 — Ebook family via ebook-convert (the big win)
- [x] `_extract_ebook`: convert to temp `.txt` via `ebook-convert`, read it back;
      graceful `unsupported`/`error`/timeout handling
- [x] Wire `.mobi`, `.azw3`, `.azw`, `.prc`, `.lit`, `.pdb`, `.chm`, `.rtf`

## Phase 6 — Tests & docs
- [x] Unit tests for each added path (skip ebook test if `ebook-convert` absent)
- [x] `uv run ruff check` / `pyright` / `pyrefly check` / `pytest` — all pass
- [x] Update `kamma/tech.md` extractor line

## Phase 7 — Re-extraction path (the bug a plain refresh exposed)
- [x] A normal refresh skips files whose size+mtime are unchanged, so existing
      `unsupported:`/`error:`/`empty` rows are NEVER retried after extractor
      improvements — first live refresh gave `written: 0, text_extracted: 0`
      (only `deleted: 365` noise pruning worked).
- [x] Added `retry_failed` to `refresh()` + `_should_skip()` (skips only when
      unchanged AND status == "ok"); steady-state refresh stays instant.
- [x] CLI: `folder-corpus-refresh --retry-failed`
- [x] Test `test_retry_failed_reextracts_unchanged_failed_documents`

## Verification
- Full check bundle green: ruff clean, pyright 0 errors, pyrefly 0 errors,
  pytest 35 passed / 1 skipped (pre-existing weasyprint PDF test).
- Spot-checked integrated `extract_text` on real corpus files: `.mobi`/`.azw3`/
  `.azw`/`.prc`/`.lit`/`.rtf`/`.mht`/`.pptx`/`.json`/`.shtml` all return text;
  `.chm` degrades to `empty` gracefully on a text-less sample.
- Expected recovery on next full refresh: ~2,680 files (84% → ~92% coverage).
  No new dependencies.

## Wall (deferred — not this thread)
- `.zip`/`.7z`/`.bz2` archive recursion (~1,213 files)
- `empty` image-only PDFs needing OCR (~764)
- `.djvu`, spreadsheets, corrupt PDFs (~40)
