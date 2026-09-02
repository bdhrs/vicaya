# Plan: PDF extraction — drop -layout, add pdf-inspector OCR fallback

## Architecture Decisions
- Hybrid extraction: pdftotext (plain mode) stays the fast path; pdf-inspector
  OCR engages only when pdftotext yields no text. Rationale: 10–60x speed on
  the text-based majority; OCR only pays for the scan tail.
- OCR deps (pdf-inspector, onnxruntime) are MAIN dependencies, not an
  optional extra. Changed mid-thread with evidence: bare `uv sync` (routine,
  documented in this repo's workflows) silently strips extras, so OCR
  capability would silently vanish; the VICAYA_LIBRARY_FOLDERS_OCR=0 kill
  switch is the opt-out instead.
- OCR runs in a dedicated subprocess per file with OCR_SUBPROCESS_TIMEOUT=600:
  process_pdf_with_ocr deadlocked without bound twice in live testing (a
  150-page single call, and a 10-page chunk inside a folder refresh) at 0% CPU
  in futex_wait. In-process chunking alone did not remove the hang; a
  killable subprocess converts it into a recorded error status. Mirrors the
  existing subprocess+timeout pattern used for pdftotext.
- Fallback lives inside `_extract_pdf` so .pdf members inside .zip/.7z archives
  get it for free (all extraction routes through the same dispatch).
- Page cap (150) plus subprocess timeout: a page cap bounds per-file work
  (~1 s/page measured on dense scans); the timeout bounds a wedged engine.

## Phase 1 — Fast path: drop -layout
- [x] Remove `-layout` from the pdftotext argv in `_extract_pdf`
      (tools/library_folders.py:379); update the docstring/comment to say
      reading-order mode.
  → verify: `uv run pytest tests/test_library_folders.py -q` all pass
  → verify: plain pdftotext on Cone p100 shows sequential columns (reference
    output: /tmp/pdftest/plain.txt — left column completes before right)
- [x] Scoped checks on touched file: `uv run ruff check tools/library_folders.py`,
      `uv run pyright tools/library_folders.py`,
      `uv run pyrefly check --search-path . tools/library_folders.py`
  → verify: all three exit clean

## Phase 2 — OCR fallback via pdf-inspector
- [x] Add `pdf-ocr` optional dependency group to pyproject.toml
      (`pdf-inspector>=1.17,<2` — originally pinned `>=0.2,<1`, which silently
      installed OCR-less 0.2.7: the PyPI package versions 1.x even though the
      GitHub Rust crate badges 0.2.x).
  → verify: `uv run --extra pdf-ocr python -c "import pdf_inspector"` works
- [x] Implement `_extract_pdf_ocr_fallback(path)` in tools/library_folders.py:
      kill-switch check; lazy import with graceful "unsupported" passthrough;
      process_pdf_with_ocr in a timeout-bounded subprocess (1800 s) with the
      first-150-pages page_numbers in 10-page chunks; return
      ExtractedText(text=joined, status="ok") when non-empty else original
      status. Wire it into `_extract_pdf` when the pdftotext result has no text.
      (Implementation note: OCR entry points resolved via getattr so older
      wheels without the OCR API degrade to "unavailable" instead of crashing.)
  → verify: unit tests below pass (stubbed module, no network/PDFium)
- [x] Add tests to tests/test_library_folders.py (stub `pdf_inspector` in
      sys.modules): (a) empty pdftotext + scanned classification + OCR text →
      status ok with text; (b) ImportError → original "empty" status kept;
      (c) kill switch env set → fallback not called; (d) page cap passed to
      page_numbers; (e) ORT_DYLIB_PATH auto-set helper; (f) OCR exception →
      "error: ..." status with the failure message.
  → verify: `uv run pytest tests/test_library_folders.py -q` all pass
- [x] Scoped checks: ruff/pyright/pyrefly on both touched .py files
  → verify: all three exit clean

## Phase 3 — Real-file smoke + docs
- [x] Real-file smoke with the extra installed and PDFIUM_LIB_PATH set:
      `_extract_pdf` on Malalasekera DPPN p101-area returns ok + diacritics;
      Cone returns non-interleaved text; one normal text PDF unchanged.
  → verify: run python snippet against the three real files; expected outputs
    match /tmp/pdftest findings
  (Result: Malalasekera ok — 297K chars, 3052 pali diacritics, 150 pages in
  154 s; Cone ok sequential; Harris ok unchanged; kill switch restores
  "empty". First smoke attempt exposed a deadlock in a single 150-page
  process_pdf_with_ocr call — fixed with 10-page chunking, OCR_CHUNK_PAGES.)
- [x] Update kamma/tech.md: extraction paragraph (plain-mode pdftotext, OCR
      fallback, page cap, kill switch), plus install steps (uv sync --extra
      pdf-ocr, first-use model download, PDFIUM_LIB_PATH setup), update steps
      (uv lock --upgrade-package …, PDFium re-download), and the
      --retry-failed note for picking up scan-tail rows.
  → verify: a fresh reader can install, verify, and update OCR from tech.md
    alone (self-check against the three subsections)
- [x] Final scoped suite: pytest + ruff + pyright + pyrefly on all touched files
  → verify: all green; report pre-existing skips as pre-existing
  (Result: 70 passed, 0 skipped [the old weasyprint skip was the broken
  .venv shebang, fixed]; ruff, pyright, pyrefly all 0 errors)
