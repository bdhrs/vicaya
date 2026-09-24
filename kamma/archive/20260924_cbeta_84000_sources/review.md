## Thread
- **ID:** 20260924_cbeta_84000_sources
- **Objective:** Add the CBETA Chinese canon and the 84000 Tibetan-canon translations as local vicaya sources for "what do other schools say about X", plus Chinese text for Āgama parallels.

## Files Changed
- `tools/research_sources.py` — `search_chinese`, `search_84000`, the Āgama html fallback in `sc_parallels`, and the `search-chinese` / `search-84000` subcommands.
- `tools/scratch.py` — the Phase 3b dossier label and checklist item now say "Other canons".
- `tests/test_research_sources.py` — 32 tests for the Chinese, 84000 and parallels code, built on the real XML shapes; one old MA 115 test repointed (see plan 3.2).
- `skill/vicaya/SKILL.md` — Phase 3b "Other canons", helper rows, return shapes, angles 2 and 16, citation formats, evidence tiers.
- `skill/vicaya-quick/SKILL.md` — triage line for "what do other schools say".
- `README.md`, `.env.example` — download sections, discovery steps, and the two env vars.
- `kamma/tech.md`, `kamma/project.md` — source notes, measured speeds, CBETA and 84000 traps.

## Findings
| # | Severity | Location | What | Why | Fix |
|---|----------|----------|------|-----|-----|
| 1 | blocking | `research_sources.py` `_CBETA_G_RE` | `<g ref>glyph</g>` doubled every rare character | False absences (`波羅㮈國` → 0) | Replace the whole element |
| 2 | major | `_cbeta_flatten` | X reprint-edition `<lb>` numbered lines | Wrong citations | Only the file's own `ed` counts |
| 3 | major | `search_chinese` | Wrong input returned a genuine-looking zero | A fake zero reads as a real absence | Normalise ids; raise `ValueError`; CLI exits 1 |
| 4 | major | `search_chinese` pool | An unguarded script crashed the pool | Scripted use broke | Serial fallback, plus a skill note |
| 5 | major | `search_84000` | Snippets were the paragraph head (180/333 lacked the match) | Match not quotable | Window around the match |
| 6 | major | `search_84000` notes | Self-closing `<note/>` swallowed text | Missed hits (Toh 555) | Regex refuses to cross `<note` |
| 7 | minor | `_cbeta_flatten` | Comments with inner tags leaked | Junk text | Drop comments first |
| 8 | minor | `search_84000` | Front matter not labelled | Intro could be cited as canon | `section` field |
| 9 | minor | `sc_parallels` | Fallback beyond Āgamas; footer and `t-juan` anchors leaked | Bloat, noise | Āgama-only, strip both |
| 10 | minor | docs | Stale shape and speed wording | Misleads agents | Updated |
| 11 | nit | various | Full-width titles, entity offsets, linear lookup, dead code, log args, `/` collection, `<textClass`, `Toh 297` | Small errors | Fixed |
| 12 | major | `_cbeta_flatten` (found while fixing #1) | Siddham glyphs split dhāraṇī phrases; 69,699 private-use chars | False absences | Drop `sa…` `cb:t` and SD-/RJ- glyphs |

## Fixes Applied
- All 12 were fixed. Evidence and before/after numbers are in `plan.md` under "Review fixes" (R1–R12). Each fix has a test that fails when the fix is reverted, checked one fix at a time with the code restored after each. The self-closing-note rule was deleted as redundant: the nested-note regex already covers it, so no test could guard it.

## Test Evidence
- `uv run pytest -q` (scope: whole project) → 495 passed, 0 warnings.
- `uv run ruff check` / `pyright` / `pyrefly check --search-path .` on `tools/research_sources.py tools/scratch.py tests/test_research_sources.py` → clean (pyrefly: 12 suppressed, the same as the baseline).
- Real-corpus reproductions for every finding (scope: the specific texts named in plan R1–R12) → fixed.
- Whole-Taishō flatten scan (scope: all 2,459 T files) → 0 stray `<`/`>`, 0 private-use characters, every file has line marks.
- Speed (scope: 涅槃, median of 3 after warm-up, load 0.7) → Taishō 2.98 s, all collections 6.67 s.
- Live `/vicaya-quick` run by a helper agent (scope: one question, before the review fixes) → both searches used and cited.

## Not Verified
- CodeRabbit: unavailable (403, no seat assigned in the linked organization).
- Snippet quality beyond T (full scan) and spot checks of X, J and A. The other 22 collections were not read by eye.
- macOS and Windows start methods (the `spawn` path is untested).
- No live `/vicaya-quick` rerun after the review fixes.
- The Phase 3b label on a dossier created before the rename: covered by reading `_append_under_phase`, not by running it.
- Pre-existing and not caused by this thread: helper calls and pytest runs log into whichever research dossier is active, so parallel runs collide.

## Verdict
PASSED
- Review date: 2026-09-24
- Reviewer: independent fresh-context Claude agent (findings); fixes and re-verification by the implementing session
