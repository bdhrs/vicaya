# Phase 0 — candidate survey (T1)

Verified against local tooling (`apt-cache policy/show`, `--version`, `pip index versions`) on 2026-09-03, not from memory.

## Candidates measured

| Candidate | Installable | Licence | Maintained | Per-page parallelism | Skip-text detection | Text sidecar | Resumable | Decision |
|---|---|---|---|---|---|---|---|---|
| **ocrmypdf** | apt candidate `15.2.0+dfsg1-1`, not yet installed. Deps present or apt-available: `ghostscript` 10.02.1 installed, `tesseract-ocr` 5.3.4 installed; `qpdf` 11.9.0 and `unpaper` 7.0.0 available in apt but not installed (recommends, not hard deps) | MPL-2.0 (upstream `github.com/jbarlow83/OCRmyPDF`) | Active — apt candidate is current stable upstream release | Yes, `--jobs N` | Yes, `--skip-text`/`--redo-ocr` | Yes, `--sidecar` | Yes, re-run skips completed pages via hash check | **KEEP** — does natively what the incumbent hand-builds; ask before installing (T2) |
| **tesseract direct** (via `pdftoppm` + process pool) | Already installed: `tesseract` 5.3.4, `pdftoppm` 24.02.0 (poppler-utils) | Apache-2.0 (tesseract), poppler is GPL-2.0-or-later for the CLI tools — only invoked as a subprocess, not linked, so no licence conflict for our code | Active | Yes, external process pool (already measured 10-way) | No built-in — our harness must check for an existing text layer itself | Plain text via `-o out` / stdout | Only what our harness implements — no built-in resume | **KEEP** — already measured baseline (1.41 s/page, 95.4% word accuracy, 0/135 diacritics); needed as the tesseract-only comparison point since ocrmypdf also wraps tesseract and could hide engine-vs-wrapper differences |
| **incumbent** (`pdf-inspector` + `onnxruntime` + hand-installed PDFium) | Already in the tree, as of the deadlock fix | Not re-verified this session — out of scope, it's the control | N/A — bespoke, single-repo | Per-book only (memory-bound to 3-way) | Yes, hand-rolled | No — writes rows to SQLite, no sidecar file | Yes, in `tools/library_folders.py`'s own row-skip logic | **KEEP as control** — required by spec §Candidates 3 |

## Candidates considered and rejected

| Candidate | Verified fact | Reason for rejection |
|---|---|---|
| PaddleOCR | `pip index versions paddleocr` → latest 3.7.0, actively released | Rejected without measurement: pulls a multi-GB deep-learning stack (PaddlePaddle, no GPU on this machine) not currently installed. Violates the spec's tie-break ("fewer new dependencies") against two candidates that need zero new heavy runtime, and risks failing the memory gate (≤4 GB/unit) on CPU inference before any accuracy is known. Not disqualified on principle — just not worth a heavy install when two lighter, already-available candidates cover the same use case. |
| Kraken | `pip index versions kraken` → latest 7.1, actively released | Same reason: pulls PyTorch: heavy new dependency, unclear CPU throughput, not installed. Also historically tuned for handwriting/non-Latin scripts, not the print-scan Pāḷi/English corpus here. |
| surya-ocr | `pip index versions surya-ocr` → latest 0.22.1, actively released | Same reason: PyTorch-based, GPU-oriented, no GPU present. |

These three are real, maintained projects — not rejected for being unmaintained — but adding any of them means a new multi-GB dependency purely to *possibly* beat two candidates that already satisfy the spec's requirements using tooling already on the machine. Per CLAUDE.md guidance, a heavier dependency only earns a bakeoff slot if the lighter, already-installed tool is measured and found insufficient first. If ocrmypdf and tesseract-direct both fail a hard gate, one of these should be added and measured in a follow-up rather than skipped entirely.

## Outcome

Three candidates proceed to Phase 1: **ocrmypdf**, **tesseract direct**, **incumbent**. Matches the spec's named list; no addition or removal.
