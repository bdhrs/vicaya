# Spec: PDF extraction — drop -layout, add pdf-inspector OCR fallback

## Overview
Vicaya's library index (tools/library_folders.py) extracts PDFs with a single
tool: `pdftotext -layout` (Poppler). A benchmark against firecrawl/pdf-inspector
on four hard books from the actual library (/tmp/pdftest, 2026-09-02) showed:

1. `-layout` interleaves two-column books line-by-line (Cone's Pali Dictionary:
   left/right column mixed on every line), destroying word adjacency for FTS.
   Plain `pdftotext` (no -layout) reads those columns sequentially; on
   single-column prose/verse the two modes are identical.
2. pdftotext extracts nothing from image-only scans (Malalasekera DPPN) and
   broken invisible text layers (Muller Six Systems) — a permanent hole today.
   pdf-inspector's selective OCR extracts these correctly (~2s/page warm) with
   right Pali diacritics, given PDFium + onnxruntime + one-time model download.
3. For text-based PDFs pdftotext is 10–60x faster, and pdf-inspector's markdown
   output injects **/*/table markup that would pollute FTS text.

Decision (user-approved): hybrid. Keep pdftotext as the fast path (drop
-layout); use pdf-inspector only as an OCR fallback when pdftotext yields no
text. Not a wholesale replacement.

## What it should do
1. `_extract_pdf` (tools/library_folders.py:374) drops the `-layout` flag so
   extraction follows reading order (fixes column interleaving for FTS).
2. When pdftotext returns no text (missing, error, or empty — covers scans,
   broken layers, corrupt files), `_extract_pdf` attempts a fallback:
   - env kill switch `VICAYA_LIBRARY_FOLDERS_OCR=0` disables the fallback
     (text-only refreshes stay fast);
   - lazy-import `pdf_inspector`; if not installed, return the original
     empty/error status unchanged (current behavior on machines without it);
   - if `ORT_DYLIB_PATH` is unset and `onnxruntime` is importable, auto-set it
     to the wheel's `capi/libonnxruntime.so.*`;
   - call `process_pdf_with_ocr(path, page_numbers=[...])` with a per-file
     page cap (first 150 pages) to bound refresh time (~2s/page measured);
   - return joined text with status "ok" if non-empty; original status
     otherwise. PDFium missing surfaces as an "error: ..." status like any
     other extraction failure — recorded, refresh moves on.
3. `pyproject.toml` gains `pdf-inspector>=1.17,<2` and `onnxruntime` as MAIN
   dependencies (originally an optional `pdf-ocr` extra with pin `>=0.2,<1`;
   both changed mid-thread — see plan Architecture Decisions).
4. `kamma/tech.md` documents the full OCR setup lifecycle:
   - **Install:** `uv sync` (OCR deps are main dependencies); one-time OCR
     model download happens automatically on the first routed page (needs
     network); PDFium: download the pdfium-linux-x64 tarball from
     bblanchon/pdfium-binaries releases, extract lib/libpdfium.so to a stable
     path, set `PDFIUM_LIB_PATH` in `.env`.
   - **Update:** `uv lock --upgrade-package pdf-inspector
     --upgrade-package onnxruntime && uv sync` keeps the Python side current
     within the `<1` pin; PDFium is not managed by uv — re-download the
     latest release tarball to the same path (and bump the `>=1.17,<2` pin
     in pyproject.toml deliberately when a major lands).
   - A short "checking it works" snippet (extract a known scanned file).
5. After implementation, `library-folders-refresh --retry-failed` re-extracts
   the scan-tail rows (documented flow in tech.md; run by user, not in tests).

## Assumptions & uncertainties
- Verified by reading source: `_extract_pdf` at library_folders.py:374;
  `.pdf` dispatch at :655; ExtractedText(status) vocabulary; 60s subprocess
  timeout pattern; archive members route through the same dispatch.
- Verified by test on real files (see Overview). Mojibake in Cone is in the
  PDF's own ToUnicode maps — no extractor can fix it; OCR on such files would
  actually recover correct diacritics but is out of scope (only empty-result
  files fall back; Cone extracts non-empty text natively).
- Assumption: page cap 150/file is an acceptable budget (≈5 min worst case per
  file). A partial OCR result is recorded as status "ok" — steady-state
  refresh will not re-attempt the un-OCR'd tail of capped files. Accepted
  trade-off; revisit if the tail matters.
- Assumption: plain-mode pdftotext is safe across the library (verified on
  two-column dictionary, single-column verse, OCR'd prose).
- Unknown: how many of the 20,428 PDFs are scan-only. The user sees the counts
  in the refresh summary when running --retry-failed.

## Constraints
- kamma/tech.md validation scope: only scoped checks on touched files
  (ruff/pyright/pyrefly/pytest), never project-wide runs.
- OCR runs at refresh time only (build-time), never at query time — like all
  extraction.
- (Originally: "no new hard dependencies" via an optional extra. Revised
  mid-thread — see plan Architecture Decisions: extras get silently stripped
  by routine `uv sync`, so OCR deps became main dependencies.)
- Tests must not require network, PDFium, or OCR models: the worker is tested
  with a stubbed `pdf_inspector` module; the subprocess boundary is tested by
  stubbing `subprocess.run`.

## How we'll know it's done
- Scoped checks green: ruff, pyright, pyrefly, pytest on touched files
  (baseline before thread: tests/test_library_folders.py 57 passed, 1 skipped).
- Real-file smoke: `_extract_pdf` on Malalasekera DPPN returns status "ok"
  with Pali diacritics (with PDFIUM_LIB_PATH set); on Cone returns sequential
  (non-interleaved) text; on a normal text PDF unchanged behavior.
- With `VICAYA_LIBRARY_FOLDERS_OCR=0` or pdf-inspector absent, empty PDFs
  produce exactly today's statuses.

## What's not included
- Not fixing the Cone-class mojibake (data flaw in those files).
- No wholesale switch of the primary extractor to pdf-inspector.
- No classification metadata stored in the index (pdf_type etc.).
- No OCR of mixed documents' scanned pages when pdftotext already returns
  some text (only fully-empty results fall back).
- No re-running of the full library refresh in this thread (user-invoked).
- No GitHub issue (none referenced).
