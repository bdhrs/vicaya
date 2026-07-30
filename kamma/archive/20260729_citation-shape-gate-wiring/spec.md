# Spec — Wire the citation shape check into Phase 7, and fix the 18 known defects

## Overview

`check-citation-shape` earned its place: precision 1.00 over 260 notes, 6 notes affected, 18 real defects, zero false positives (see `20260729_citation-gate-backtest`, `temp/citation-backtest/verdicts.md`). That thread deliberately left `SKILL.md` untouched and left the defects in place. This thread does both jobs.

## What it should do

### 1. Fix the 18 defects in the vault

Six notes, all the same error class — a paragraph number glued onto a sutta number:

| note | refs |
|---|---|
| `2026-05-27 - bojjhanga-definitions.md` | `MN118.150` ×2, `MN118.152` ×2, `DN22.385` ×3 |
| `2026-06-20 - bojjhanga-complete-ebt-reference.md` | `MN118.150` |
| `2026-05-27 - pali-prosody-study-guide.md` | `Khp 5.10` |
| `2026-06-06 - nibbidā-disgust-revulsion-meaning-usage-pali-canon.md` | `SN 5.46.20` ×2, `SN 4.35.45` ×2, `SN 5.51.4` ×2 |
| `2026-07-24 - gnostic-indian-parallels.md` | `DN 2.244`, `DN2.244` |
| `2026-07-15 - what-the-suttas-say-about-the-differences-between-the-sutta-and-the-abhidhamma.md` | `SN 1.4.6` |

The MN/DN/Khp cases have their correct form stated in their own footnotes (`MN118 … para 150`), so the fix is mechanical: `MN118.150` → `MN118 §150`, and the footnote anchor renamed to match.

**The four three-part SN references are not mechanical.** `SN 5.46.20` must be resolved to its real two-part reference against the canon DB before rewriting — do not guess that the last two numbers are the saṃyutta and sutta. Verify each with `resolve-citation` / `verify_citation` and cite what the passage actually is.

These notes are already published to `bdhrs/vicaya-notes`. Corrections must be synced after the fix, using the pre-approved `sync_notes.py` path only.

### 2. Wire the check into Phase 7

Add `check-citation-shape` to the Phase 7 exit sequence in `skill/vicaya/SKILL.md`, between `scratch-set-note` and `scratch-self-audit`, as a **hard** failure — findings block the run, matching the `[REJECTED]` treatment. The class it catches is unambiguous and the false-positive rate measured zero, so advisory treatment (as `scratch-check-coverage` uses) is not warranted.

Keep the SKILL.md addition to a few lines. The check's semantics belong in its `--help` and docstring, not in a 2,557-line skill file.

### 3. Regression-protect the corpus

Add `temp/`-independent coverage: a test that runs the check over a fixture note built from the six real defect shapes, so the class cannot silently return.

## Explicitly out of scope

- The `verify_citation` Vinaya and full-collection-name gaps. The user chose to leave these alone.
- Second-segment range errors (`SN17.99`, `SN48.471–477`, `AN 3.375`). Out of reach of a structural check; `verify_citation` already flags them.
- Any other Phase 7 consolidation.

## Assumptions and uncertainties

1. **The four SN references can be resolved.** If a passage cannot be identified confidently from the note's surrounding text, leave the reference alone and report it rather than inventing a correction — a wrong citation is worse than a malformed one.
2. Whether a hard gate is right, or whether it should start advisory for one cycle. Precision was 1.00 on historical notes, but historical notes are not adversarial; a new note format could produce a shape the check misreads. Starting hard is defensible given zero measured false positives, and the check is one flag to relax if it misfires.

## Confidence

**8/10.** The gate wiring is small and the evidence behind it is measured rather than argued. The uncertainty is entirely in the four SN references, which need real research to correct rather than a find-and-replace.
