## Thread
- **ID:** 20261119_cite_books_by_title
- **Objective:** Cite library books by title and author, never by index number, in notes and in every check that compares a note with a run.

## Files Changed
- `tools/library_folders.py` — Calibre libraries one folder down; `calibre_books` title table (no schema bump); `cite_as` on hits and reads; no Calibre number in the FTS prefix; an unreadable catalogue keeps stored titles.
- `tools/scratch.py` — title matcher; coverage check and Phase 7 gate by title; index-text look-up; volume rule; number regexes removed.
- `tools/note_audit.py` — number branch removed from `check-bibliography`.
- `tools/note_checks.py` — hard `library-number` validator check.
- `tests/` — four test files changed, `test_library_title_match.py` new; fixtures copied from real notes and run logs.
- `skill/vicaya/SKILL.md`, `skill/vicaya-quick/SKILL.md`, `kamma/tech.md` — citation format and rationale.
- `<vault>/Vicaya` — 334 notes migrated, PDFs regenerated (uncommitted; one-off script and records in `artifacts/`).

## Findings
| # | Severity | Location | What | Why | Fix |
|---|----------|----------|------|-----|-----|
| 1 | major | `tools/scratch.py` gate flags | "does not read X as" flagged a read book | false gate refusal | "not read"/"unread" flag only unread books — fixed |
| 2 | major | `tools/scratch.py` `_hits_cited` | text look-up ignored volume numbers | refusal naming the wrong volume | volume check in the look-up — fixed |
| 3 | major | `tools/scratch.py` refs, merge, translator, rejection rows, one-word labels | blank-line lists, stale extraction status, other translation counted as read, markers leaking across a row, exact label missed | wrong gate results | all fixed with tests |
| 4 | minor | `tools/note_checks.py` | non-library numbers ("Loeb Classical Library 237") flagged | false validator error | id marker required — fixed |
| 5 | nit | `tools/note_checks.py` | refs title starting "84000:" is flagged | rare | deferred |

Earlier rounds (subagent audit, CodeRabbit ×2) and every finding's disposition: `artifacts/reviews.md`.

## Fixes Applied
- All blocking/major findings from three review rounds, each with a regression test; two key fixes revert-checked (test fails without the fix).

## Test Evidence
- `uv run pytest -q` (scope: whole project, all 822 tests) → pass
- `uv run pytest artifacts/test_migrate.py -q` (scope: the migration script, 22 tests from real lines) → pass
- ruff, ruff format, pyright, pyrefly (scope: all 13 touched `.py` files) → clean
- Validator over every note in the three vault folders (scope: 395 notes) → 0 `library-number`
- Matcher measure (scope: 1,328 real `library_refs` entries in 152 notes) and end-to-end old/new comparison (scope: the 20 most recent runs) → `artifacts/matcher-measure.md`, `artifacts/e2e.md`

## Not Verified
- Matcher accuracy is measured, not perfect: about 10% of judged cases wrong, mostly data problems; a miss lets the gate pass a citation (it never refuses).
- Resumed runs across an index rebuild (stale ids): accepted risk in the spec.
- The live `/vicaya` workflow end to end with a new run: not run.
- The vault brahma note was hit by a sync pull during review; rebuilt from the other committer's version and migrated, but git still marks it unmerged and keeps an "autostash" stash (needs the user).

## Verdict
PASSED
- Review date: 2026-11-19
- Reviewer: independent read-only subagent plus CodeRabbit; fixes and this file by the implementing session, model: claude-opus-5-5
- Independence: full for the findings (separate context); reduced for the fixes and verdict (same session as implementer)
