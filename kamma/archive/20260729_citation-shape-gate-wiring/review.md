# Review — Wire the citation shape check into Phase 7, and fix the 18 known defects

## Outcome: complete except publishing, which needs user approval.

All 18 defects corrected across six notes, corpus re-verified clean (0 findings across 260 notes), gate wired as a hard failure, two regression tests added, suite green at 341.

## The result worth keeping

**`SN 1.4.6` was not a formatting error — it was the wrong sutta.**

The plan assumed all four three-part SN references were PTS `volume.saṃyutta.sutta` and would correct by dropping the volume. That held for three. For the fourth, searching the canon for the quoted phrase `khaṇo vo mā upaccagā` returned no hit under any reading of `SN 1.4.6`. The phrase is in **SN 35.135 Khaṇasuttaṃ** — a sutta named for the very word the passage discusses.

A purely structural check with no database access surfaced a substantive citation error, because a malformed shape turns out to be a reliable marker of a reference nobody verified. That is a better argument for the gate than its precision number.

The plan's rule against inventing corrections is what produced this. A pattern-based rewrite would have silently turned a wrong citation into a well-formed wrong citation.

## Corrections made

| note | change |
|---|---|
| bojjhanga-definitions | `[^MN118.150]` → `[^MN118-para150]` etc., anchors and definitions renamed together |
| bojjhanga-complete-ebt-reference | `(MN118.150)` → `(MN118 §150)` |
| pali-prosody-study-guide | `Khp 5.10` → `Khp 5, v. 10` |
| gnostic-indian-parallels | `DN2.244` / `DN 2.244` → `DN2 §244` |
| nibbidā-disgust-revulsion | `SN 5.46.20` → `SN 46.20`, `SN 4.35.45` → `SN 35.45`, `SN 5.51.4` → `SN 51.4` |
| what-the-suttas-say-…-abhidhamma | `SN 1.4.6` → `SN 35.135 *Khaṇasuttaṃ*` |

## Severity was not uniform, contrary to how it was first reported

7 of the 18 findings were footnote **anchors** (`[^MN118.150]`), which are identifiers and never render — the reader never saw them, so the fix there is machine-readability, not a reader-facing correction. The other 11 were rendered prose and genuinely misleading. The "18 real defects" framing overstated the first group; corrected here.

## Fixed in form, not in substance

The three nibbidā references now verify as real suttas and the PTS volume mapping is consistent. But the source note itself records `Pāḷi: [Not directly retrieved but referenced in sources]` against each. **Whether those suttas support the nibbidā claims made about them was never checked** — not by the original run, not here. Pre-existing gap, recorded so it is not mistaken for verified.

## Not done

**Phase 3 (publish) was not executed.** The six corrected notes are saved locally and unpublished; pushing to the public `bdhrs/vicaya-notes` repo needs explicit user approval, which was not given during the thread. The corrections are committed to the vault repo but not pushed.
