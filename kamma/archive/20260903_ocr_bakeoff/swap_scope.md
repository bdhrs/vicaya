> **Audited 2026-09-04 — read `kamma/threads/20260904_ocr_swap/scope_audit.md` first.**
> The symbol table below was verified exact (all 14 at the stated lines). The *readers* sweep was not complete: it missed `kamma/tech.md` entirely (a 110-line architecture section plus the project's install steps), three emitted `ocr` statuses, two `SKILL.md` lines, and the actual missing-engine degradation mechanism. It also wrongly states pikepdf is already available in the venv. Four blockers; corrections are folded into that thread's spec and plan.

# Follow-up thread scope: swap the OCR backend to ocrmypdf (T15)

**Not implemented in this thread.** This is the scope note for the next thread, per the spec's "What's not included". Written 2026-09-04 after the bake-off named ocrmypdf the winner (see `measurements.md`).

Every symbol and file below was located with `rg --hidden`, and the sweep deliberately covered the non-obvious carriers (justfile, README, the research agent's `SKILL.md`, `pyproject.toml`, `.env`) — not just `tools/`, because the previous thread's status-vocabulary change missed exactly those.

## 1. Code to delete — `tools/library_folders.py`

The bespoke worker, framed protocol, per-chunk timeout, reader thread and page cap. Roughly lines 42–60 and 430–742, ~230 lines:

| Symbol | Line | What it is |
|---|---:|---|
| `_ort_dylib_path` | 430 | locates the onnxruntime shared library |
| `_ocr_worker_chunks` | 442 | the chunked OCR generator that runs inside the worker subprocess |
| `_ocr_status` | 498 | builds `ok: ocr truncated …` / `partial: ocr stalled …` statuses — **see §5, do not delete blindly** |
| `_OCR_REPLY_MARKER` | 521 | the stdout framing marker |
| `_OCR_WORKER_SNIPPET` | 522 | the `python -c` worker source string |
| `_parse_ocr_worker_reply` | 531 | pulls framed JSON out of worker stdout |
| `_extract_pdf_ocr_fallback` | 543 | the entry point; replace this body, keep the name and signature |
| `_OcrOutcome` | 648 | dataclass carrying the reader thread's result |
| `_collect_ocr_chunks` | 658 | the reader thread + per-chunk deadline loop (the deadlock site) |
| `OCR_PAGE_CAP` | 51 | 1000-page cap — exists because the incumbent got slower and heavier per page; **re-evaluate, likely deletable** |
| `OCR_CHUNK_PAGES` | 52 | 10 — chunking exists only to bound the incumbent's deadlock |
| `OCR_CHUNK_TIMEOUT` | 53 | 120 |
| `OCR_FIRST_CHUNK_TIMEOUT` | 58 | 600 |
| `OCR_SUBPROCESS_TIMEOUT` | 59 | 1800 — a whole-book backstop is still wanted, see §5 |

**Keep**: `OCR_KILL_SWITCH_ENV` (line 45, `VICAYA_LIBRARY_FOLDERS_OCR`) — the kill switch is referenced by the justfile and README and must survive. `extraction_succeeded` (482) is the status prefix contract and is unrelated to the engine.

## 2. Dependencies to drop

- `pyproject.toml:8` — `pdf-inspector>=1.17,<2`
- `pyproject.toml:9` — `onnxruntime`
- `.env` — `PDFIUM_LIB_PATH` (the only consumer is `tools/library_folders.py`). **Never edit `.env` directly** — tell the user the key is now unused and let them remove it.
- `uv.lock` — regenerates from the `pyproject.toml` change; do not hand-edit.

New requirement: `ocrmypdf` (apt 15.2.0, already installed on this machine) plus `pikepdf` (already present as an ocrmypdf dependency). Note that ocrmypdf is a **system** package, not a uv dependency — the follow-up thread must decide how that is declared and checked, since `uv sync` will not install it and a missing binary must degrade gracefully via the existing kill switch.

## 3. Two mandatory behaviours the new backend must carry

Both are measured findings from this thread, not speculation:

1. **Pre-decrypt encrypted PDFs.** ocrmypdf refuses them outright (`EncryptedPdfError`, rc=8); 43 of 1,735 pending books (2.5 %) are affected. Verified fix: open with `pikepdf` and save to a temp file first (these use an empty user password, so no credentials are involved), then OCR that. Without this, 43 books silently fail.
2. **Detect implausibly short output.** Both tesseract-based candidates returned 84 characters for the whole 85-page "Survey of Vinaya Literature. Vol. I" while reporting success (Finding 3) — a book PDFium read correctly. A return code cannot catch this. Add a check that flags any book whose character count is far too low for its page count, and record a distinguishable status for it rather than a bare `ok`.

## 4. Invocation the swap should use

Measured best safe parallelism: **4 books concurrent × `--jobs 4`** (0.433 s/page, CPU-bound; 488 MB per unit, 8.4× inside the memory gate). 8-way gave no improvement.

Flags used in measurement: `--jobs 4 --sidecar <txt> --force-ocr --output-type pdf <in> <out>`. Two easy wins were **not** measured and should be checked by the follow-up thread rather than assumed: `--optimize 0` (this pipeline only wants the sidecar text, so image optimisation is pure waste — the logs show a visible "Postprocessing/Image optimization" stage on every book) and dropping `--force-ocr` in favour of plain OCR, since these books have no text layer to force past. Both should only make it faster.

## 5. The status vocabulary is a cross-file contract — handle with care

This is the trap that caught the previous thread. The OCR statuses are not local to `library_folders.py`; they are read by the research agent and documented for users:

- `skill/vicaya/SKILL.md:1504, 1519, 1521` — instructs the research agent that `ok: ocr truncated at 1000 of 1678 pages` and `partial:` are usable, and explicitly **not** to hand-run `pdftotext` on a scanned PDF whose status mentions `ocr`. If the swap stops emitting statuses containing `ocr`, these three passages send the agent down the dead end they were written to prevent.
- `README.md:187–194` — documents the OCR fallback, the 1,000-page cap and the `ok: ocr truncated …` status.
- `justfile:9–11, 26, 30–46` — the whole three-pass rebuild (`lf-refresh-text`, then `lf-refresh-retry` **twice**) exists because *"OCR stalls are intermittent, so a second pass recovers them"*. ocrmypdf showed **zero** stalls across the full 22-book corpus, so the third pass loses its rationale — a real simplification, but it must be an explicit decision with the comments updated, not a silent leftover.

If `OCR_PAGE_CAP` is removed, the `ok: ocr truncated …` status disappears with it, and all three files above need updating in the same change.

## 6. Tests

`tests/test_library_folders.py` references every deleted symbol (`_ocr_worker_chunks`, `_OCR_REPLY_MARKER`, `_OCR_WORKER_SNIPPET`, `_collect_ocr_chunks`, `_ocr_status`, `_ort_dylib_path`, and all five timeout/cap constants). Those tests go with the code they cover.

**Carry forward the one that matters**: the uncommitted regression test from the deadlock fix spawns a *real* hung subprocess and requires bounded recovery. The new backend needs an equivalent — a genuinely hung/crashing `ocrmypdf` process, bounded and recovered — because a mock returning immediately is precisely how the original deadlock passed 452 tests. Add coverage for both §3 behaviours (an encrypted PDF, and a book whose OCR returns almost nothing).

## 7. What this thread deliberately leaves undecided

- **Quote fidelity regresses and there is no fix in this scope.** ocrmypdf preserves 0 % of IAST diacritics against the incumbent's 74.2 %; text pasted from the index into a research note will carry wrong letters (`Ākāśagarbha` → `Akasagarbha`). Search is unaffected — that is what the findability gate measured and why the rule still chose ocrmypdf — but the user should know this is the price, and it is worth asking whether it is acceptable before the swap lands.
- The unknown population rate of the Finding 3 silent-empty failure (n=1). §3.2's detector is the mitigation; the actual rate only becomes visible on a full run.

## 8. Supersedes

`kamma/threads/20260903_parallel_ocr/` — the thread for adding three-way concurrency to the incumbent. The incumbent lost; parallelising it is wasted work. Per this thread's own deviation note, that thread should now be deleted rather than executed.
