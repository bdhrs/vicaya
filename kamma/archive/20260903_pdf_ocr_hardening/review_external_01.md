# External review 01 — of the first draft of spec.md and plan.md

Reviewed 2026-09-03 by an external reviewer at the user's request. Verdict: **BLOCKED**. Recorded here verbatim in substance; the spec and plan were re-baselined in response.

## Verdict

The documents are stale — they describe a repository state that was destroyed after they were written. They need re-baselining before any Phase 1/2 work proceeds. The thinking and honesty behind them are genuinely good; the problem is they no longer describe reality.

## Finding 1 — BLOCKING: the spec and plan describe a change set that no longer exists

The thread files were written at 05:06–06:02 on 2026-09-03. Later that morning (09:57–09:58) the repo was reset and re-committed, and neither document was updated.

| Spec claims | Reality |
|---|---|
| "5 commits plus an uncommitted working tree" | 6 commits, working tree clean except `kamma/threads/` |
| C1 (`e22ef34`, OCR feature) — "sound in structure" | Reverted by `8a5952a`; no OCR code, no worker subprocess, no kill switch; `_extract_pdf` is back to plain `pdftotext -layout` |
| U1–U7 "uncommitted — written by me today" | Wiped by the reset; none are in the file |
| C3 (`f5328e0`, index-wipe fix) | Re-committed as `2b1a99a` (same content, new hash) |
| C4 (`7b85607`, lf-refresh-text recipe) | Wiped by the reset and never re-created |
| Archived thread `kamma/archive/20260902_pdf_ocr_fallback/` | Deleted by the revert commit |
| "full test suite passes at 431 tests" | 410 collected (the revert removed the OCR tests) |

Why it matters: the entire Phase 1 decision set was asking the user to keep or revert code that had already been reverted. An implementer following the plan would be deciding the fate of a phantom change set.

## Finding 2 — MAJOR: the revert reorders the priorities

The spec ranked refresh durability as the most serious problem on the grounds that OCR made runs 100× longer. That reasoning depended on OCR being present. The spec itself conceded that before OCR "a two-minute rebuild is effectively atomic", so in the current tree the severity collapses. The OCR escalation and page-cap questions are moot while there is no OCR path; extractor versioning and the health check remain live.

## Finding 3 — MAJOR: Phase 0/1 contains tasks that are now impossible or moot

Running a corrupt PDF through the OCR path cannot be done — there is no OCR path. The decisions about the seven follow-up changes are moot, since all seven are gone. The commit reference for the wipe-fix cleanup should be `2b1a99a`, not `f5328e0` — though the underlying concern was confirmed still present.

## Finding 4 — MINOR: D7 is referenced but never defined

The non-goals, assumption 7, and a plan task all refer to "D7", but the open-problems list only enumerated D1–D6.

## Finding 5 — MINOR: verified facts mix past and present tense as if both are current

Statements about the OCR path being exercised end-to-end, and about the worker subprocess re-importing from disk, read as current but were superseded by the revert.

## What is genuinely good (keep through any rewrite)

- The "Corrections to my earlier review" section is exemplary — explicitly retracting two false claims and correcting them against the original spec is the right discipline and rare.
- The boldly-stated assumptions section is the single best part: 11 falsifiable items, with Phase 0 correctly built to close the cheap ones first.
- The confidence score with named reasons is honest and actionable.
- The phase gates and per-task verify clauses match the project workflow; the fails-before/passes-after regression discipline is right.
- The observation that the truncation status and the skip-logic change must be decided together is sharp.

## Recommended path forward

1. Re-baseline the spec against the post-revert state.
2. Re-rank the problems given OCR is absent.
3. Rewrite Phase 0/1 to drop the moot decisions and re-scope the OCR test task.
4. Fix the dangling label, the stale commit hashes, and the test count.

## Response

Findings 1, 3, 4 and 5 accepted in full and implemented in the re-baselined documents.

Finding 2 accepted with one correction, recorded in the spec under "Correction to the review": the "two-minute rebuild" figure was my own unverified claim, which the review inherited. The committed run report describes a full refresh on this ~122 GB library running past 16 minutes before being killed. Durability is therefore not moot — its severity is unknown and measurable, and that measurement is now the first task in the plan.
