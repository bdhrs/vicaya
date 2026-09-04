# Handoff: bake-off finished and reviewed. Ready to finalize.

2026-09-04. All tasks done (T1–T19, T22, T16) except T20/T21, deliberately deferred to the swap thread.

## Answer

**ocrmypdf.** 1.32 days for all 263,524 pages at 4 books × `--jobs 4`, against the incumbent's 4.31 — **3.27× like-for-like**, both sides OCR-only. Memory 488 MB/unit vs 5.0 GB, which is what capped the incumbent at 3-way. Zero stalls observed across 20 books vs the incumbent's 4 of 22.

Diacritic loss — the incumbent's last advantage — is recoverable at **99.7 %** (Opus, CI 98.1–99.9, measured through the harness on the same 303-token slice as every other model). Mid-tier models reach only ~85 %, so tier is a cost decision, not a detail.

## Reviewed

Two independent parallel passes, both briefed to attack:

- `review.md` — 16 findings, 2 BLOCKING. Verdict: winner stands, three headline numbers were overstated.
- `../20260904_ocr_swap/scope_audit.md` — 4 BLOCKING, 4 SERIOUS. All 14 deletion symbols verified exact; the *readers* sweep was incomplete.

Both blockers against this thread are closed. Everything from the scope audit is folded into the swap thread's spec and plan.

## What review changed, kept honest

- **98.2 % → 99.7 %.** The original figure was self-scored on a 57-token slice; review rejected it as non-comparable and was right. Re-measured blind through the harness on the same slice as the others: higher, and now comparable. Two of review's own supporting claims died in that run — Opus produced the five "unrestorable" abbreviation artefacts, and the single remaining error is a title the source book spells two ways.
- **Robustness gate corrected.** Finding 3 (a whole book returning 84 characters while reporting success) was not counted. Counted: 3/22 = 13.6 %, true population rate unknown. And the stated remedy — re-run through the incumbent's engine — is impossible once the swap deletes it. Now an explicit decision in swap T7.
- **"Zero stalls" restated as 0/20, one attempt each, 95 % upper bound 16.1 %** against a 5 % gate. The justfile's third retry pass therefore **stays**; retiring it was the thread's most consequential over-read.
- **Kill margin restated.** 3.27× like-for-like against the ≥3× bar, not 4.54× (mixed basis). Thin. The rate was also a single unreplicated run against T6's own median-of-3 rule — 3× replication was running at handoff; median goes in `measurements.md` T13a.
- **`pikepdf` is a new dependency.** "Already present" was verified against system Python; the venv has `include-system-site-packages = false`. Without adding it, the fix for 43 books cannot import its own library.
- **Findability gate is method-limited for all three candidates** — type-weighted, on a dictionary, violating two traps this thread's own spec names. It cuts both ways: it also undermines the incumbent's decisive 72.7 % FAIL.
- **The "same engine, therefore noise" argument is withdrawn.** Different rasteriser and DPI policy, and the gate is absolute not comparative. The legitimate basis is `spec.md`'s "if no candidate clears the gates" clause plus the fact that the 85 % threshold was calibrated against two figures Finding 4 later overturned.

## Biggest remaining hole

**T20, the memorisation control, was never run.** The fixture is a published book; 99.7 % is exactly what recall would produce. Carried into the swap thread as T12 — close it before promising the number to a user.

## Tree

`git status`: only `?? kamma/threads/`. **No production code changed** — by design. Full suite **452 passed, 1 skipped**, matching baseline. The harness is scratchpad-only and disposable.

## Next

1. `/kamma:4-finalize` this thread.
2. Implement in `kamma/threads/20260904_ocr_swap/` — spec and plan written and review-corrected, nothing implemented. Starts at T2 (T1 done by the audit).
3. Delete `kamma/threads/20260903_parallel_ocr/` — it parallelises the losing candidate.
