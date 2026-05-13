## Thread
- **ID:** 20260513_skill_calibre_translation
- **Objective:** Two doc-only improvements to `skill/vicaya/SKILL.md` —
  Calibre search guidelines (Phase 3) and Pāḷi/English presentation
  conventions (Style notes), with a cross-reference from Phase 5.

## Files Changed
- `skill/vicaya/SKILL.md` — +190 lines, -1 line. Inserted Calibre search
  guidelines subsection at line 313; added Phase 5 cross-reference at line
  455; added "Pāḷi/English presentation (vault note only)" block at line
  677. Adjusted one line about tag-name matching style (line 303).

## Findings

| # | Severity | Location | What | Why | Fix |
|---|----------|----------|------|-----|-----|
| 1 | minor | `SKILL.md:18` (Hard Rule 3) | Rule 3 still says "Calibre library uses ASCII Pāḷi" verbatim. Verified live: at least one stray `Nibbāna` tag and many author names with macrons (e.g. `Bhikkhu Anālayo`) exist. The data is overwhelmingly ASCII but not exclusively. | Mildly inaccurate, but the practical search behaviour is unchanged (Calibre is diacritic-insensitive either way), and the new Phase 3 block already documents this. | Leave Rule 3 as-is — fixing it would expand scope beyond this thread. Future thread could soften "uses ASCII Pāḷi" → "mostly uses ASCII Pāḷi". |
| 2 | nit | `SKILL.md:42` | Old line still says "14k books, takes days" for FTS indexing. Live count is 12,501. | Cosmetic, was inherited; not part of this thread's scope. | Skip. |

No blocking or major findings.

## Fixes Applied
- None. The two findings are minor/nit and explicitly out of scope per the
  spec's "What's not included".

## Test Evidence
- `rg -n "Calibre search guidelines" skill/vicaya/SKILL.md` → 1 hit at
  line 313 (pass).
- `rg -n "Pāḷi/English presentation" skill/vicaya/SKILL.md` → 2 hits
  (Phase 5 cross-ref at line 455, Style block heading at line 677) (pass).
- `rg -n "12,501|2,140|607 series|1,293|410|Piya Tan" skill/vicaya/SKILL.md`
  → all expected numeric claims present, none drifted from the live
  Calibre measurements taken this run (pass).
- `git diff --stat` → 1 file changed, +190/-1 (matches doc-only scope).
- Worked example in the new block contains both a `>` blockquote pair
  (MN9 *Sammādiṭṭhisuttaṃ* Pāḷi + English) and an inline `*āhāra*
  (nutriments)` form (pass).
- No code changes; no Python tests to run.

## Verdict
PASSED
- Review date: 2026-05-13
- Reviewer: kamma (inline)
