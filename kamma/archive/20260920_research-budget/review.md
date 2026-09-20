## Thread
- **ID:** 20260920_research-budget
- **Objective:** Add an evidence budget plus a single absence/inference rule (Hard Rule 13) to `skill/vicaya/SKILL.md`, and build an OpenAlex scholarly-search channel (`search-openalex`).

## Files Changed
- `skill/vicaya/SKILL.md` — Hard Rule 13; Phase 0 `Target:` line + confirmation template; dispatch rules 2/3 + prompt-template TARGET line; Phase 2 whole-range ceiling; 0-hit concept-family step; `target_vs_actual` report frontmatter; Phase 4a `search-openalex` subsection.
- `skill/vicaya-what-the-suttas-say/SKILL.md` — series negative-claims rule now points at Hard Rule 13.
- `tools/research_sources.py` — `ScholarHit`, `search_openalex`, `_ascii_fold`, `_reconstruct_abstract`, `_openalex_fetch`, `openalex_terms`, `OpenAlexError`, CLI `search-openalex`.
- `tests/test_research_sources.py` — 12 OpenAlex tests (fake opener, no network).
- `data/youtube_channels.md` — unrelated pre-existing edit (see finding).

## Findings
| # | Severity | Location | What | Why | Fix |
|---|----------|----------|------|-----|-----|
| 1 | major | `tools/research_sources.py` `search_openalex` (`hits[:limit]`) | Final truncation runs over the merged list in term order, so when the first spelling alone fills `limit`, every later spelling — including the auto-derived ASCII fold — is silently dropped. Verified live: `search_openalex('brahmavihāra')` (default `limit=25`) returns 25 hits, all `matched_term == 'brahmavihāra'`; the folded `brahmavihara` spelling's 24 unique hits never surface. With the documented `--limit 40` and 4 spellings, the 3rd and 4th (`--also`) spellings are still dropped. | The spec's central requirement is that spellings are disjoint and must be *merged*; the auto-fold is a silent no-op by default. The plan's own headline ("81 unique works from four spellings") is the pre-truncation count — the shipped `hits[:limit]` returns at most `limit`. The guard test only asserts both spellings are *queried*, not that their results *survive*, so it stays green through the bug. | Round-robin/interleave per-term results before truncating, or cap each term at `ceil(limit / n_terms)`, or raise the default `limit`. Strengthen the test to assert hits from >1 spelling survive when the first spelling alone fills the limit. |
| 2 | minor | `data/youtube_channels.md` | Unrelated edit (International Focusing Institute channel) sits in the working tree. | Will be swept into the finalize commit unless separated. | Commit separately, or exclude from the thread commit. |
| 3 | nit | `tools/research_sources.py` `_handle_search_openalex` | Error path dumps `{"error": ...}` to stdout in addition to the stderr `error:` line + exit 1; sibling handlers emit nothing on stdout for errors. | Minor inconsistency for consumers keying off stdout JSON. | Drop the stdout dump or document it. |

## Fixes Applied
None — review only, per instruction.

## Test Evidence
- `uv run pytest tests/test_research_sources.py -q -k openalex` → 12 passed (scoped; fake opener, no network)
- `uv run pytest tests/ -q` → 455 passed, 1 skipped (full suite, re-run this review)
- `uv run ruff check tools/research_sources.py tests/test_research_sources.py` → clean
- `uv run pyright tools/research_sources.py tests/test_research_sources.py` → 0 errors
- Live `search-openalex "Tevijja" --limit 5` → real on-topic hits with reconstructed abstracts
- Structure: 135 headings, 152 code fences (even); "Six rules … state all six" still accurate (6 rules); Hard Rule 13 appended, rules 1–12 untouched; `Target:`/`target_vs_actual`/`search-openalex`/by-number refs all resolve.

## Not Verified
- Behavioural claim that runs get shorter / absence claims get checked — by design, deferred to `/vicaya-improve` reading `target_vs_actual` across real runs.
- The plan's 4-spelling live fan-out (81 unique works) was not independently reproduced; live single-term and auto-fold calls were, and they surfaced finding #1.

## Verdict
BLOCKED
- Review date: 2026-09-20
- Reviewer: pi (kamma-3-review, fresh session)

---

## Resolution (appended at finalize, 2026-09-20)

The BLOCKED verdict above stands as written — it was accurate against the code it reviewed. The blocking finding was fixed before this review was filed, by the parallel adversarial audit that found the same defect independently, and the fix is what that reviewer suggested: round-robin interleave the per-term results before truncating, and tighten the guard test.

Evidence the review predates the fix: it records 455 passed. The suite is now 469 — the fix added fourteen tests, two of which fail if the interleaving regresses.

The reviewer's own reproduction, re-run against current code: `search-openalex "brahmavihāra"` at the default limit returns 13 hits from the diacritic spelling and 12 from the auto-folded plain form, where it previously returned 25 and 0.

The two smaller findings: the stray `data/youtube_channels.md` edit is pre-existing, not this thread's, and is excluded from the suggested commit. The stdout-JSON-on-error nit was **declined with evidence** — it is this repo's established pattern, enforced by an existing test written for issue #87 ("callers parse stdout; a stderr-only diagnostic left them with empty stdout and a JSON decode error") and followed by four other handlers.

**This resolution is the implementer's own verification, not an independent re-review.** Finalized at the user's explicit direction. A fresh `/kamma:3-review` against current code would be the proper confirmation and has not been run.
