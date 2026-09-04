# Plan: swap the OCR backend to ocrmypdf + wire in diacritic restoration

Spec: `spec.md`. Evidence: `kamma/threads/20260903_ocr_bakeoff/measurements.md` and `swap_scope.md`. No GitHub issue.

## Architecture Decisions

- **Replace the body, keep the seam.** `_extract_pdf_ocr_fallback(path) -> ExtractedText | None` stays as the entry point with the same name and signature. Everything behind it is replaced. This keeps the refresh loop, the status contract and the kill switch untouched, so the diff is confined to one function's implementation plus deletions.
- **Delete rather than disable.** The worker subprocess, framed stdout protocol, per-chunk timeouts and reader thread exist only to contain a deadlock in a library being removed. Leaving them dormant leaves the next reader wondering which path is live.
- **Restoration is a separate module on the quote path.** It does not touch extraction, the index, or `library_folders.py`. Search never needed it; only quoting does. Keeping it separate means the swap can ship without it and vice versa.
- **The status vocabulary is a cross-file contract.** `skill/vicaya/SKILL.md`, `README.md` and the `justfile` all read the `ocr` statuses. Any change to what statuses are emitted updates all of them in the same commit.
- **No mocks near a timeout, stall, or failure path.** The original deadlock passed 452 tests because a fake `close()` returned immediately. New failure-path tests spawn real processes.

## Model Strategy

| Phase | Tier | Reason |
|---|---|---|
| 1 — swap the backend | **Fast** | mechanical: replace one function body, delete mapped symbols, fix tests. The scope note already did the judgement. |
| 2 — the two safety behaviours | **Fast** | both fixes are specified and one is already verified working. |
| 3 — verify on real books | **Fast** | run commands, record numbers. |
| 4 — restoration design | **Pro** | genuinely undesigned, and it puts model output in front of a researcher as if it were the page. Needs judgement and a user conversation. |
| 5 — review | **Pro** | independent pass briefed to attack the result. |

⚠️ MODEL SWITCH REQUIRED (Pro tier) at Phase 4.

## Phase 1 — swap the backend ⚠️ Fast

- [x] T1 — Re-verify `swap_scope.md`'s 14 symbols and line numbers. **Done by independent audit — see `scope_audit.md`.** All 14 symbols confirmed at the exact stated lines; both keep-decisions, the justfile/README/SKILL refs and the dependency claims verified. The audit found 4 BLOCKING and 4 SERIOUS gaps in the *readers* sweep, all folded into the tasks below.
- [ ] T2 — Replace `_extract_pdf_ocr_fallback`'s body with an `ocrmypdf` call: `--jobs 4 --sidecar <tmp> --output-type pdf`, read the sidecar, return `ExtractedText`. Keep the name, signature, kill switch and status prefixes. Three requirements the audit added, all acceptance criteria not afterthoughts:
  - **A whole-book timeout.** Pass `subprocess.run(..., timeout=...)` with a kill on `TimeoutExpired`. The literal plan replaced three layered bounds with an unbounded call — the exact unkillable-wait shape the deleted machinery existed to contain (`scope_audit.md` BLOCKING 2). Keep `OCR_SUBPROCESS_TIMEOUT = 1800` or rename it; do not drop it.
  - **A monkeypatchable binary seam.** Expose the executable as a module-level constant (`OCRMYPDF_BIN = "ocrmypdf"`) or a `_ocrmypdf_command()` helper, so T8 can point it at a hanging stub. Without this the hung-subprocess test has nothing to substitute (`scope_audit.md` SERIOUS 7).
  - **Every emitted status must contain the substring `ocr`.** `skill/vicaya/SKILL.md:1504` and `1521` branch on it; lose it and the research agent is sent to the `pdftotext` dead end those lines exist to prevent.
  → verify: one scanned book from the bake-off corpus extracts real text through the normal refresh path; the timeout and the seam are both exercised by tests.
- [ ] T2a — Replace the engine-availability probe. `swap_scope.md` and this spec both claimed a missing binary "degrades gracefully via the existing kill switch" — it does not. `OCR_KILL_SWITCH_ENV` is an explicit user opt-out (`tools/library_folders.py:566`); the thing that actually handles an absent engine is the `except ImportError: return None` at 568–571, which the swap deletes along with `pdf-inspector`. Returning `None` there is what makes the caller keep pdftotext's own status instead of writing an OCR error over every scanned PDF in the library. Mirror the sibling pattern already in the file (`shutil.which("pdftotext")` at line 408): `if shutil.which("ocrmypdf") is None: return None` — **`None`, not an `unsupported:` status** (`scope_audit.md` BLOCKING 3). → verify: with the binary masked, a scanned PDF keeps its pdftotext status and no OCR error is written; covered by the carried-forward test at line 1339.
- [ ] T3 — Delete the bespoke machinery per `swap_scope.md`: worker snippet, reply marker, reply parser, chunk generator, outcome dataclass, reader-thread collector, the ONNX dylib locator, and the four timeout constants. Keep `OCR_KILL_SWITCH_ENV` and `extraction_succeeded`. Also drop the two imports that become unused (`queue`, and `Iterator` from `collections.abc`) — the pre-commit hook runs `ruff` and `pyright` and will fail on them. Delete `tests/test_library_folders.py:1190` (`_OVER_CAP = library_folders.OCR_PAGE_CAP * 2 + 78`) **in the same edit** as the constant: it is module scope, so removing the constant alone breaks collection for the entire test file, not just the OCR tests (`scope_audit.md` SERIOUS 6). → verify: `rg --hidden` finds no live reader of any deleted symbol outside `kamma/` and archived threads; the test module still collects.
- [ ] T4 — Drop `pdf-inspector` and `onnxruntime` from `pyproject.toml` **and add `pikepdf`** in the same change, then regenerate the lock with `uv sync` and check `.venv/bin` shebangs still point at the project venv. Report that `PDFIUM_LIB_PATH` is now unused — do **not** edit `.env`.
  **`pikepdf` is a new dependency, not a free one.** The bake-off claimed it was "already present as an ocrmypdf dependency"; that is true of the apt package and false of the venv the code runs in — `.venv/pyvenv.cfg` has `include-system-site-packages = false` and `.venv/bin/python3 -c "import pikepdf"` raises `ModuleNotFoundError` (`scope_audit.md` BLOCKING 1). Without this, T6's fix for 43 books cannot import its own library.
  → verify: `.venv/bin/python3 -c "import pikepdf"` succeeds; `uv run pytest tests/test_library_folders.py -q` collects and runs; no import of the removed packages remains.
- [ ] T5 — Decide the **whole status vocabulary**, not just the page cap (assumption A3). Two decisions, both with cross-file consequences:
  - `OCR_PAGE_CAP`: if removed, `ok: ocr truncated …` goes with it. Migration hazard measured against the live index and currently nil — **0 rows** match `ok: ocr truncated%` (the OCR pass never reached the cap); record that it was checked, not assumed.
  - **`partial:` cannot survive as-is.** The incumbent emits it because the worker streams text per 10-page chunk, so a stall leaves real text. ocrmypdf writes its sidecar once at the end, so a killed run leaves *no* text and there is nothing for `partial:` to describe. The live index holds **23 `partial:` rows**. Either retire the status and update all its readers, or define what it now means (`scope_audit.md` SERIOUS 5).
  Carriers to update in the same commit: **`kamma/tech.md` (lines 13, 22–98, 110–129 — missed entirely by `swap_scope.md`, and line 111 is the project's install instruction, which becomes actively wrong once OCR needs an apt package `uv sync` will not install)**, `skill/vicaya/SKILL.md:1504, 1517, 1519–1521`, `README.md:187–195`, `justfile:9–11, 26, 30–48`, and `extraction_succeeded`'s own docstring. There are **seven** emitted OCR statuses, not the three in the note — enumerate them all before editing (`scope_audit.md` BLOCKING 4, SERIOUS 8, MINOR 9).
  → verify: both decisions recorded in `Deviations` with the row counts and every carrier updated.

## Phase 2 — the two measured safety behaviours ⚠️ Fast

- [ ] T6 — Pre-decrypt encrypted PDFs with `pikepdf` before OCR. 43 of 1,735 books are affected; the fix is verified working on `Chanakya - Yagya Sharma.pdf`. → verify: both encrypted books from the bake-off corpus (`Chanakya`, `A History of Indian Literature Vol. 2`) now extract real text where they previously returned rc=8.
- [ ] T7 — Detect implausibly short output and give it a distinguishable status rather than a bare `ok`. **Decide what happens to a flagged book, because after this swap there is no second engine** — the bake-off's stated remedy ("re-run through the incumbent's engine") is impossible once `pdf-inspector`/`onnxruntime`/PDFium are deleted, so flagging alone leaves a permanently unindexed hole (`review.md` BLOCKING 2). Either retain a minimal second-engine path for flagged books, or state plainly that they stay unindexed and bound the rate: a 100-book sample costs ~1.8 h at 0.433 s/page against a 1.32-day full run. → verify: `Survey of Vinaya Literature. Vol. I` — 85 pages, 84 characters from ocrmypdf — is flagged, not recorded as success. Threshold stated with its rationale; the status is added to the vocabulary contract in all three files that read it.
- [ ] T8 — Real-subprocess tests for both new behaviours, plus a *partial* equivalent of the deleted deadlock regression test (`tests/test_library_folders.py:1955`). The audit split it honestly:
  - **Achievable and required**: bounded kill of a genuinely hung `ocrmypdf` (a stub that sleeps past the timeout, via T2's seam), asserting recovery well inside the deadline.
  - **Not achievable**: the original also asserted *partial text retained* from a stalled book. ocrmypdf produces no sidecar until it finishes, so there is no equivalent. Assert a bounded kill and a retryable non-`ok` status with empty text instead, and **record partial-text retention as a capability the swap gives up** in `Deviations` (`scope_audit.md` SERIOUS 7).
  Also carry forward `test_pdf_ocr_fallback_keeps_original_status_without_pdf_inspector` (line 1339), rewritten against a **missing binary** — see T2a — and rewrite `test_pdf_ocr_fallback_kill_switch` (line 1351) against the new seam, since its `pdf_inspector` stub becomes inert and the test would pass while proving nothing. 29 test functions die in total; the audit lists them by line. No mocks on any failure path. → verify: each test fails when its behaviour is removed.

## Phase 3 — verify on real books ⚠️ Fast

- [ ] T9 — Run the bake-off's full 22-book corpus through the new backend at 4 books × `--jobs 4`. → verify: measured s/page stated beside the bake-off's 0.433; zero unrecoverable failures; both stallers and both encrypted books complete. Fails the spec's robustness gate if not.
- [ ] T10 — Measure assumption A1: `--optimize 0`, and dropping `--force-ocr`. Neither was measured in the bake-off. → verify: a before/after rate for each, adopted only if faster with identical extracted text.
- [ ] T11 — Full suite. → verify: 452 passed / 1 skipped or better, with the real-subprocess coverage from T8 present and the numbers stated.

## Phase 4 — diacritic restoration on the quote path ⚠️ Pro

- [ ] T12 — Run the memorisation control the bake-off skipped (its T20, assumption A4): can the model reproduce the fixture passages unprompted, and how does it score on invented Pāḷi-shaped nonsense? → verify: a yes/no per passage; the 98.2 % figure recomputed without any passage the model can recite, or the claim downgraded.
- [ ] T13 — **Ask the user how restoration should appear before writing it.** Undesigned per `spec.md`: is a restored quote marked as model output, shown alongside the raw text, or silent? Restoration puts generated letters where the page's own letters are expected, so this is the user's call. → verify: the answer recorded here before any code.
- [ ] T14 — Implement restoration as a standalone module on the quote path: DPD + `data/scratch/` frequency prior as the candidate source, model with sentence context for the choice. It must not write to the index.
  **Model tier is a real cost decision, not a detail.** Measured on the same slice through the same harness: Opus **99.7 %** (CI 98.1–99.9), DeepSeek V4 Flash 85.6 %, Sonnet 84.7 %, Haiku 80.7 %. Only the frontier tier clears the ≥95 % gate; everything cheaper ships a ~15 % error rate on quoted text. Decide with the user which, and if it is not the frontier tier, the residual rate must be stated wherever a restored quote appears. → verify: the bake-off fixture scores ≥ 95 % through the shipped code path, not just the harness.
- [ ] T15 — Wire it into the research/quote flow per T13's answer, and update `skill/vicaya/SKILL.md` so the research agent knows when a quote is restored and when it is raw. → verify: one real quote restored end-to-end through the actual flow, not a script.

## Phase 5 — review ⚠️ Pro

- [ ] T16 — Independent review briefed to attack the result, plus `coderabbit review --agent` on the diff (`--dir` scoped, `--include-untracked` for new files). → verify: findings recorded and addressed; `review.md` carries a verdict.

## Deviations

- 2026-09-04 — Created from the bake-off's `swap_scope.md` (its T15) after Phase 6 measured diacritic loss as recoverable, which removed the last argument for keeping the incumbent. Restoration was added to this thread's scope for the same reason; the bake-off deliberately did not implement it.
