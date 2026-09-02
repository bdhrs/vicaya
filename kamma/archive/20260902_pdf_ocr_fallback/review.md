# Review: 20260902_pdf_ocr_fallback

## Thread
- **ID:** 20260902_pdf_ocr_fallback
- **Objective:** Hybrid PDF extraction — keep pdftotext (drop -layout), add pdf-inspector OCR fallback for scans/broken layers.

## Files Changed
- `tools/library_folders.py` — plain-mode pdftotext; OCR fallback via timeout-bounded subprocess worker (`_ocr_worker_main`, 10-page chunks, 150-page cap, 1800s timeout); kill switch env; ORT dylib auto-location.
- `tests/test_library_folders.py` — 13 new tests: worker (chunking, cap, unsupported API), subprocess boundary (spawn, timeout, crash, junk/unsupported payload), kill switch, no-pdf-inspector passthrough, ORT dylib helper.
- `pyproject.toml` — pdf-inspector>=1.17,<2 + onnxruntime as main dependencies (extra tried, removed: bare `uv sync` strips extras).
- `uv.lock` — resolves pdf-inspector 1.17.0, onnxruntime 1.29.0.
- `kamma/tech.md` — extraction paragraph + PDF OCR fallback lifecycle (install/update/verify), venv-shebang gotcha.

## Findings
| # | Severity | Location | What | Why | Fix |
|---|----------|----------|------|-----|-----|
| 1 | minor | kamma/tech.md | Stale 600s timeout text after code raised to 1800 | Wrong number for fresh readers | Fixed |
| 2 | minor | tools/library_folders.py | Docstring still said "optional pdf-ocr extra" | Deps moved to main mid-thread | Fixed |
| 3 | minor | tests | Junk-JSON path untested | Contract untested | Fixed (test added) |
| 4 | nit | tools/library_folders.py | Non-dict JSON payload would AttributeError | Unreachable in practice | Fixed (isinstance guard) |

Reviewed by independent subagent (read-only harness; pytest run by requester). No blocking/major findings. Scope creep: none ("What's not included" respected).

## Fixes Applied
- Findings 1-4 above; plus mid-thread (pre-review): version pin 0.2.7→1.17 (OCR API absent in 0.2.x), extra→main deps, subprocess+timeout isolation after two observed engine deadlocks, 600→1800 timeout after live run killed mid-OCR.
- Environment fix (pre-existing, outside thread scope but required for verification): `.venv/bin/*` console-script shebangs pointed at research-hub's venv → tests ran under wrong interpreter; reinstalled owning packages. This also eliminated the old "pre-existing weasyprint skip".

## Test Evidence
- `uv run pytest tests/test_library_folders.py -q` (whole library_folders suite, all OCR paths stubbed network/PDFium-free) → 70 passed.
- `uv run ruff check / pyright / pyrefly check` on touched files → all 0 errors.
- Live: `_extract_pdf` on Malalasekera DPPN (1180p scan) → ok, 297K chars, 3052 Pāḷi diacritics (smoke v3, pre-chunking); Cone (2-col) → sequential order; Harris (text PDF) → unchanged; kill switch → old behavior. Live refresh on the scan: engine wedged → subprocess killed at 600s → clean `error:` status recorded, refresh exit 0, index written — the boundedness contract verified in the wild.

## Not Verified
- No live confirmation that this specific book OCRs to "ok" within 1800s (engine flaky run-to-run: 154s in smoke, wedged in refresh); `--retry-failed` re-attempts errored rows, so a later run can land it.
- Full-library effect (1,739 empty + ~20 error PDFs) not run — user-invoked long job; per-book behavior bounded and verified.

## Verdict
PASSED
- Review date: 2026-09-02
- Reviewer: kamma (inline) + independent reviewer subagent
