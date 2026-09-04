# Spec: OCR bake-off — pick a real solution by measurement

**Goal:** decide, from numbers, which OCR solution indexes 1,739 scanned books in hours rather than days — and delete whatever loses.

Baseline `134e25f` plus an uncommitted deadlock fix. Handoff context: `handoff.md` in this thread. No GitHub issue.

## The problem

The hand-rolled incumbent (`pdf-inspector` + `onnxruntime` + PDFium behind a bespoke subprocess protocol) is running at a **user-observed six days** for the remaining 1,739 books. Earlier agent estimates of 86 h and 230 h were both wrong and both too optimistic. Six days is the number to beat.

The incumbent was never compared against the tool built for this job. `ocrmypdf` is in apt at 15.2.0 and does natively what the incumbent hand-builds: skip pages that already have text, parallelise per page, emit a text sidecar, isolate per-page failures, resume by re-running.

## What this thread decides

One question: **which OCR backend does the library refresh call?** Everything else follows from the answer.

## Decision rule — committed before any measurement

A candidate wins on **projected wall clock for all 1,739 books at its best safe parallelism**, subject to hard gates. Gates are pass/fail; a candidate failing any gate is out regardless of speed.

| Gate | Threshold | Why |
|---|---|---|
| Search quality | ≥ 90 % word accuracy against ground truth after diacritic folding | below this the index stops being trustworthy for research |
| Findability of diacritic-bearing words | ≥ 85 % after folding | the corpus is Pāḷi; measured incumbent 81.8 %, tesseract 87.9 % |
| Robustness | ≤ 5 % of books unrecoverably failed, and no failure costing > 5 min | the incumbent's 17 % stall rate and 30-min timeouts are what made it unusable |
| Memory | peak ≤ 4 GB per concurrent unit at the chosen parallelism | 30 GB machine, ~15 GB free; the incumbent's 5 GB/book is what capped it at three |
| Resumability | killing mid-run redoes ≤ 1 book of work | a multi-hour job must survive interruption |

**Tie-break, in order:** fewer moving parts in our code; fewer new dependencies; better diacritic preservation in stored text.

### Amendment, 2026-09-04 — diacritic restoration is now part of the rule

Added at the user's direction after Phases 0–4 completed and before the thread closed. **The winner is not final until this is measured.**

The bake-off scored diacritics as an irreversible property of an engine's output: tesseract-based candidates lose 100 % of IAST diacritics, the incumbent keeps 74 %, and the rule chose findability-after-folding over quote fidelity. That framing assumes the loss is permanent. It may not be — the diacritic-bearing tokens in this corpus are Pāḷi technical terms and proper names, and correctly-spelled forms of exactly those words are already on disk in resources this project owns: 1.28 M inflected forms in the DPD lexicon, and **1.77 M correctly-diacriticized Pāḷi tokens (100 k types, with real usage frequencies) across 260 prior research dossiers in `data/scratch/`**.

If flattened ASCII can be restored to correct IAST at high enough accuracy, the incumbent's one remaining advantage disappears and the decision is unambiguous. If it cannot, the diacritic cost stands as stated and the user must accept or reject that trade knowingly.

**Committed before measuring, per the same discipline as the original rule:**

| Restoration accuracy on diacritic-bearing tokens | Consequence for the decision |
|---|---|
| **≥ 95 %** | Diacritic loss is recoverable. Quote fidelity ceases to be a cost; ocrmypdf wins outright and the tie-break's third clause is void. |
| **85–95 %** | Partial recovery. ocrmypdf still wins on speed and robustness, but the swap must ship restoration, and quotes carry a stated residual error rate. |
| **< 85 %** | Restoration is not a fix. The original finding stands: ocrmypdf wins on the committed rule, and the diacritic loss is a real, permanent cost the user accepts explicitly. |

**Baseline to beat: 0 %.** That is what ocrmypdf stores today. Any restoration is an improvement; the thresholds above decide whether it is enough to change the *decision*.

**Traps this measurement must not fall into** — each has already produced a wrong number once in this thread or its predecessor:

- **Memorisation, not restoration.** A model asked to restore diacritics in a canonical sutta may simply recall the text. Ground truth must be prose the model is unlikely to have memorised, and any candidate passage the model can reproduce *unprompted* is void as evidence.
- **Circular ground truth.** The scratch dossiers quote canon text directly. Using a canon book as the answer key while using the dossiers as the restoration resource scores the resource against itself. Ground truth must be scholarly prose *about* the material, not the material.
- **Type-level statistics.** A dictionary-only pass looked like 92.1 % accurate per word type and measured **15.1 %** token-weighted, because rare long compounds are unambiguous and frequent short words are not. Every figure must be token-weighted, with the type-level number reported separately if at all.
- **Fixture bias.** The first ceiling measurement used pages of a Pāḷi *dictionary* — isolated headwords with no disambiguating context, the worst possible case. Restoration must be measured on running prose.

**Scope note:** restoration is only needed for *quoting*, not for search — the FTS index already folds diacritics on both sides of a query, verified. So restoration may be applied lazily to the handful of passages a researcher cites rather than to all 263,524 pages, and its cost per token is close to irrelevant. Throughput of the restorer is therefore **not** a gate; accuracy is.

**Keeping the incumbent is a valid outcome** — but only if it wins under this rule, not by argument. If no candidate clears the gates, the recommendation is the fastest gate-passing candidate at reduced quality, stated as such.

**Kill condition:** if the leading candidate does not beat six days by at least 3x on the projection, stop and report that the problem is inherent, rather than shipping a marginal change.

## Candidates

1. **ocrmypdf** (apt 15.2.0, wraps tesseract 5.3.4, ghostscript present). Per-page parallelism, sidecar text output, skip-text detection, resumable.
2. **tesseract direct**, via `pdftoppm` per page with a process pool. Already measured: 1.41 s/page at 10-way, 95.4 % word accuracy, 0/135 diacritics.
3. **The incumbent**, as it stands after the deadlock fix. The control.

The executing agent must verify what else is currently available and maintained rather than trusting this list — and must verify installability and licence before adding a candidate. Do not add a candidate on the strength of a name.

## Assumptions & uncertainties

Established by measurement, do not re-derive:

- 1,739 scanned PDFs; median 94 pages, mean 153, max 1,678; 266,429 pages.
- Incumbent: 1.18 s/page warm and unloaded, 2.9 s/page in production, 5.0 GB per book mostly private, 2 of 12 books stalled per attempt, stalls intermittent.
- Tesseract loses 0/135 IAST diacritics; incumbent keeps 134/135. The FTS tokenizer folds diacritics on both sides of a query, verified.
- The library text pass is done: 44,380 of 46,427 documents indexed.

Assumed and **not** verified — each must be measured, not argued:

- **B1** that ocrmypdf's per-page parallelism beats the incumbent's per-book parallelism in wall clock on real books.
- **B2** that ocrmypdf's memory per job is well under the incumbent's 5 GB, making higher parallelism possible.
- **B3** that ocrmypdf does not inherit the same intermittent stalls, since the failure may live in PDFium or the page images rather than the engine.
- **B4** that sidecar text is directly usable as FTS input without a cleanup pass.
- **B5** that no candidate's quality falls below the gates on this corpus specifically — Pāḷi diacritics, 19th-century scans, two-column journals.

## Constraints

- The user runs any long job in their own terminal. Agent-run measurement must be bounded to finish inside one session.
- The live index is read-only to this thread. A six-day run may be in progress.
- Never modify `.env`. Installing `ocrmypdf` is a system change — ask first.
- Shared tree: no `git stash`, no whole-tree checkout or reset, no commits unless asked.
- No mock-based evidence for any timeout, stall or concurrency claim. Real hung and real crashing processes only.

## How we'll know it's done

- A results table: every candidate, every metric in the decision rule, with n stated.
- A named winner, chosen by the committed rule, with the numbers that chose it and the numbers that would have chosen differently.
- A projection for all 1,739 books at the winner's best safe parallelism, and the measured basis for it.
- If the winner is not the incumbent: a follow-up thread scoped to swapping the backend and **deleting** the bespoke worker, framed protocol, per-chunk timeout, reader thread and page cap.

## What's not included

- Implementing the winner. This thread measures and decides; a separate thread swaps.
- Training or fine-tuning any OCR model, including for IAST.
- Improving the incumbent. It is the control, not a subject.
- Re-measuring anything listed above as established.

## Confidence

6 of 10 on predicting the winner; 8 of 10 that the rule picks correctly given honest execution. The risk is not the design, it is discipline during execution — every failure in the preceding thread came from accepting weak evidence, so the gates and the no-mocks rule are the load-bearing parts.
