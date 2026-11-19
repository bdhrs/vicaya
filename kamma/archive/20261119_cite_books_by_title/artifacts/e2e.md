# End-to-end check on 20 real runs (task 5.1, 2026-11-19)

The 20 most recent run dossiers whose vault note was migrated. "Old" is the number-based checker (`tools/scratch.py` at HEAD) on the note as committed before the migration; "new" is the title-based checker on the migrated note. Both read the same dossier. Script in the session scratchpad (`e2e.py`); counts below are its output.

| Note | Hits | Unaccounted old → new | Cited not gathered old → new | Gate refusals old → new |
|---|---|---|---|---|
| 2026-11-15 - ethics-as-self-love-and-helping-oneself-first.md | 76 | 0 → 0 | 0 → 1 | 18 → 10 |
| 2026-11-12 - pali-sanskrit-indo-aryan-development.md | 123 | 90 → 72 | 0 → 0 | 14 → 14 |
| 2026-11-11 - mudita-vs-new-age-gratitude.md | 172 | 157 → 141 | 0 → 0 | 12 → 19 |
| 2026-11-10 - metta-karuna-modern-research-and-practice.md | 86 | 0 → 0 | 0 → 3 | 6 → 8 |
| 2026-11-10 - mudita-sympathetic-joy.md | 330 | 298 → 261 | 0 → 2 | 17 → 13 |
| 2026-11-09 - karuna-and-anuddaya-compassion.md | 110 | 63 → 44 | 0 → 0 | 30 → 29 |
| 2026-11-09 - sati-nanavira-hillside-hermitage.md | 74 | 58 → 46 | 0 → 0 | 9 → 15 |
| 2026-11-09 - vipassana-as-punna.md | 47 | 30 → 22 | 0 → 0 | 12 → 11 |
| 2026-11-08 - metta-daily-life.md | 36 | 0 → 0 | 0 → 0 | 5 → 5 |
| 2026-11-06 - teaching-the-dhamma-and-taking-students.md | 66 | 0 → 2 | 0 → 1 | 11 → 12 |
| 2026-11-02 - samasa-pali-compounds.md | 301 | 283 → 248 | 0 → 4 | 12 → 10 |
| 2026-10-30 - thai-chinabancha-chant-translation.md | 114 | 58 → 51 | 0 → 1 | 6 → 6 |
| 2026-10-28 - golden-rule-others-as-self.md | 59 | 43 → 35 | 0 → 0 | 11 → 9 |
| 2026-10-28 - udana-verses-and-stories-priority.md | 30 | 16 → 11 | 0 → 0 | 4 → 7 |
| 2026-10-22 - vinaya-offerings-to-bhikkhus.md | 10 | 0 → 0 | 0 → 0 | 0 → 0 |
| 2026-10-20 - vedic-injunctive-and-pali-ma-aorist.md | 72 | 26 → 22 | 2 → 2 | 15 → 12 |
| 2026-10-19 - temporary-ordination.md | 52 | 39 → 36 | 0 → 1 | 6 → 9 |
| 2026-10-19 - burnt-seed-impotent-seed-comparative.md | 444 | 431 → 397 | 1 → 0 | 13 → 16 |
| 2026-10-18 - dhp-278-279-sri-lanka-addition.md | 66 | 41 → 28 | 0 → 0 | 4 → 8 |
| 2026-10-17 - satipatthana-internal-external.md | 108 | 90 → 74 | 0 → 0 | 11 → 13 |

Gate refusal counts are entries: the old gate listed one entry per file id, the new one per cited book (copies folded together).

## Verdicts on every difference

**Unaccounted.** The new check leaves fewer hits unaccounted than the old one in 15 of 20 notes, the same number in 4, and more in 1 (a title in a Not Used row now counts even where the row gave no number). Hits the new check lists that the old one did not, read one by one:

- First pass: 21. Reading them found three checker gaps, fixed and tested before the final pass: a line holding the start of a file's title with its author ("Malalgoda, *Buddhism in Sinhalese Society*" for "Buddhism in Sinhalese Society 1"; "Mihita, 'Buddha as Progenitor of Pali'" for a cut Calibre name; "Piya Tan, *SD 2.7 Tirokudda Sutta*"; "Seeger, *The Bhikkhuni Ordination Controversy in Thailand*" for a Scribd file name); a file coded by name ("baum2", "pettit991", "Comparative-Dhammapada - Unknown"); and the cited author inside a hit's own name ("Aorist in Pali_Ruiz-Falques_…").
- Final pass: 6, all wrong by the checker and all known limits: Calibre's misspelt "Expolring the Saddaniti" (typo similarity 0.89, under the 0.93 floor that keeps Dhammapada/Dhammapāla apart); Piya Tan's "r.322.Schadenfreude (SJ.239)" against "Schadenfreude (SJ 239)"; "BMC II Correction" and "BMC II c - up to end" (two-word code names with no author); "204039101-indriya" (a Scribd file); "Magadhabhasa (Pali) Second Edition — Thanuttamo" cited as "— A. Bhikkhu" (the authors disagree, so the match is refused).

**Cited not gathered.** New entries are citations written as descriptions or in academic form rather than "Title — Author": "MN 45 Cūḷadhammasamādānasutta, trans. Thanissaro Bhikkhu", three academic-style footnotes in metta-karuna-modern-research ("Lutz, Brefczynski-Lewis, … 'Regulation of the Neural Circuitry …'"), "Pāli BA course notes, Samāsa chapter — ITBMU", "Muditā (Bodhi Leaves 93)", "Hartmann, 'Cultural Change Through Substitution'", "Vinaya Glossary — eVinaya". All advisory; none names a book the dossier holds under that title.

**Gate, refusals only the new gate makes** (each checked: the book is cited by `library_refs` or a library footnote, and no copy was read in that run): Dhammapada 195/196 (Mahinda), The Historical Value of the Pali Discourses (Anālayo), Studies in Pali Commentarial Literature (Endo), A Philological Approach to Buddhism (Norman) in dhp-278-279; Head and Heart Together (Thanissaro) in mudita-vs-new-age-gratitude; A Guide to the Bodhisattva Way of Life in karuna-and-anuddaya; Muditā and The Four Sublime States (Nyanaponika) in mudita-sympathetic-joy, now one entry per book across all copies; Nibbāna — The Mind Stilled in ethics-as-self-love. The old gate missed these because the note's number named another file. Flags only the new gate makes ("unread"/"snippet only" lines naming the book by title): the Yoga Sutra translations (Vivekananda, Bryant) in mudita-sympathetic-joy, Ñāṇananda's *Meanings* and Nyanaponika's *Heart of Buddhist Meditation* in sati-nanavira, *Little Buddhas* in temporary-ordination. Right.

**Gate, refusals only the old gate made** (22, each checked against the migrated note's citations and the dossier's reads):

- The old gate was wrong (the number named another book): The Essential Confucius and The Illustrated Encyclopedia of Confucianism in golden-rule (the note cites The Analects and Yao's Introduction); Magadhabhasa in thai-chinabancha.
- A body mention, not a citation: Goodman, Williams's *Altruism and Reality*, Emmanuel's *Companion*, and a 2011 mindfulness paper in ethics-as-self-love; Iyengar, *Inside the Yoga Sutras* and *Yoga and the Luminous* in mudita-sympathetic-joy. The old gate counted any number in the body as a citation; the new gate counts `library_refs` entries and library footnotes, as the plan specifies.
- Other copies of a book still refused under the new gate: "wh170 - Mudita", "wh006 - The Four Sublime States", two Kaccāyana Grammar files, the Scribd copy of Nibbāna — The Mind Stilled. Right.
- Misses (the citation is a description, not a title): "mn45"/"mn.045.than" cited as "MN 45 … trans. Thanissaro", "BL_93" as "Muditā (Bodhi Leaves 93)", Piya Tan's Schadenfreude, "Pali BA.B" and "Kaccayana4-Eng" as study-material descriptions, and Calibre's misspelt "Expolring the Saddaniti". Nine misses in all; each lets that citation pass the gate, as a number not logged in the run did before.

No listed title names a book the note does not cite, reject, flag or mention.
