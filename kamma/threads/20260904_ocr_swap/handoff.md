# Handoff: implement the OCR backend swap

Written 2026-09-04 by the agent that ran the bake-off. You are writing the code; the decision is already made and reviewed.

## Start here

1. `spec.md` and `plan.md` in this thread — both already corrected by review, so trust them over the older scope note.
2. `scope_audit.md` in this thread — an independent audit of the deletion plan. **4 BLOCKING, 4 SERIOUS findings, all already folded into `plan.md`.** It is the most useful file you have: exact line numbers, exact test-by-test impact.
3. `kamma/archive/20260903_ocr_bakeoff/` — the evidence. `measurements.md` for numbers, `review.md` for what was wrong with them, `swap_scope.md` for the deletion map (it carries an audit banner naming its own gaps).

**Begin at T2.** T1 is done — the audit verified all 14 deletion symbols at their exact stated lines.

## The decision, in one line

Replace `pdf-inspector` + `onnxruntime` + PDFium behind a bespoke subprocess worker with a call to the `ocrmypdf` binary. Measured: **1.32 days** projected for 263,524 pages vs the incumbent's 4.31, on **488 MB** per worker vs 5.0 GB, with **0 stalls observed** vs 4 of 22.

## Four things that will bite you if you skip the audit

1. **`pikepdf` is not importable in the venv.** `.venv/pyvenv.cfg` has `include-system-site-packages = false`. The bake-off's "already present" claim was verified against system Python. Add it to `pyproject.toml` in the same change that removes the two old deps, or the fix for 43 encrypted books cannot import its library.
2. **Keep a whole-book timeout.** The literal plan replaced three layered bounds with an unbounded `subprocess` call — the exact unkillable-wait shape the deleted machinery existed to contain. Keep `OCR_SUBPROCESS_TIMEOUT = 1800` and pass it.
3. **The kill switch is not the availability probe.** `VICAYA_LIBRARY_FOLDERS_OCR` is a user opt-out. What actually handles a missing engine is the `except ImportError: return None` you are deleting. Replace it with `shutil.which("ocrmypdf") is None → return None` (not an `unsupported:` status), mirroring the `pdftotext` pattern already in the file. Returning `None` is what stops an OCR error being written over every scanned PDF in the library.
4. **`kamma/tech.md` is the biggest missed carrier** — a 110-line architecture section plus the project's install steps. Line 111 says "`uv sync` — OCR deps are main dependencies; nothing extra needed", which becomes actively wrong the moment OCR needs an apt package. Also `skill/vicaya/SKILL.md`, `README.md`, `justfile`, and `extraction_succeeded`'s docstring.

## Two design decisions the plan asks you to make, not guess

- **`partial:` cannot survive as-is.** The incumbent emits it because its worker streams text per 10-page chunk, so a stall leaves real text. ocrmypdf writes its sidecar once at the end — a killed run leaves nothing to describe. The live index holds 23 `partial:` rows. Retire the status and update its five readers, or define what it now means (plan T5).
- **A flagged book has nowhere to go.** One 85-page book returned 84 characters while reporting rc=0. After this swap there is no second engine to re-run it through, so flagging alone leaves a permanently unindexed hole (plan T7).

## Restoration (Phase 4) — ask before building

Measured on the same slice through the same harness: **Opus 99.7 %** (CI 98.1–99.9), DeepSeek V4 Flash 85.6 %, Sonnet 84.7 %, Haiku 80.7 %. Only the frontier tier clears the ≥95 % gate.

Two things not settled, both plan tasks:
- **T12 — the memorisation control was never run.** The fixture is a published book, and 99.7 % is exactly what recall would produce. Close this before promising the number to the user.
- **T13 — nobody has decided what a researcher *sees*.** Restoration puts generated letters where the page's own letters are expected. Ask the user; do not pick silently.

Restoration goes on the **quote path only**. The FTS index already folds diacritics on both sides of a query, so search never needed it, and it must not be written back into the index.

## Numbers to treat with suspicion

- **0.433 s/page was one unreplicated run.** A 3× replication was started and killed after rep 1, which came in at **0.528 s/page** — 22 % slower, which would drop the like-for-like margin to 2.68× against a self-imposed 3× bar. The swap is still clearly worth doing (memory and robustness don't depend on it), but do not quote 0.433 as settled. Re-measure on the real implementation in T9.
- **"Zero stalls" is 0/20, one attempt each** — 95 % upper bound 16 %. Do **not** retire the justfile's third retry pass on this.
- **The findability gate is method-limited for all three candidates** — type-weighted, on a dictionary, violating two traps the bake-off's own spec names.

## Tree state — nothing is committed

```
 M AGENTS.md                              (CLAUDE.md is a symlink to it)
?? kamma/archive/20260903_ocr_bakeoff/
?? kamma/threads/20260904_ocr_swap/
```

`kamma/lessons.md` is gitignored (`.gitignore:32`), so its new lines won't appear in `git status`. `HEAD` is `cdbca58`. Full suite: **452 passed, 1 skipped** — that is your baseline, and `spec.md` gates on matching it.

**No production code has been touched yet.** The bake-off deliberately changed none.

## Constraints that bit the last agent

- Never edit `.env`. Report `PDFIUM_LIB_PATH` as unused and let the user remove it.
- Shared tree — other sessions commit here. No `git stash`, no whole-tree reset. The deadlock fix that was uncommitted at the bake-off's start was committed by another session mid-thread as `cdbca58`.
- Verify imports with `.venv/bin/python3`, never bare `python3`.
- `pkill` fails silently in the sandbox (exit 1, processes alive). Verify a kill by re-listing processes.
- 29 test functions die with the deleted code; the audit lists them by line. Two must be carried forward rewritten: the missing-engine degradation test (line 1339) and the kill-switch test (1351, which would otherwise pass while proving nothing).
