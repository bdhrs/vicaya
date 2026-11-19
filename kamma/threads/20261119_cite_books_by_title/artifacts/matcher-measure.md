# Matcher measure (task 2.1, 2026-11-19)

Script: `artifacts/measure_matcher.py`. It reads every run dossier in `data/scratch/` whose `**Vault note:**` names an existing note, takes that note's `library_refs` entries (the `<n>:` prefix stripped), and runs `library_title_matches` against every library hit logged in that dossier. Read-only. One full run takes 7 s.

Scope: 152 notes in all three vault folders that have a dossier with library hits; 1,328 `library_refs` entries. 1,054 of the entries carry an old number that is a logged hit in their dossier, which gives a rough cross-check ("agreement": the matcher accepts the hit the old number named). The old numbers are often wrong (spec: 29% right overall), so agreement can never reach 100%.

"Two or more book folders" counts entries whose matched hits sit in more than one Calibre book folder or file. Most are copies of one book in several libraries, which the spec counts as one book; each run's new cases were read by eye.

## Runs

| Run | Change | Matched | Unmatched | 2+ folders | Agreement |
|---|---|---|---|---|---|
| 1 | Spec rule: 80% of citation title words in `cite_as` + title + whole path | 1,069 | 259 | 232 | 906 |
| 2 | Drop bracketed notes; cut words and plurals; numbers count; main title before a colon | 1,129 | 199 | 307 | 961 |
| 3 | Only file name and its folder count (category folders matched unrelated books); looser tries need 3 words | 1,091 | 237 | 240 | 936 |
| 4 | Two-way match: one of the hit's titles must also be found in the citation | 999 | 329 | 146 | 856 |
| 5 | Short main titles allowed on the hit side when the author is named; long digit ids dropped | 1,071 | 257 | 172 | 923 |
| 6 | Letters and digits split; author veto; Calibre author after the last " - " | 1,054 | 274 | 166 | 915 |
| 7 | Author typos tolerated; " - " is an author sign only inside Calibre; shortened hit title must sit in the citation's main title | 1,075 | 253 | 190 | 935 |
| 8 | Calibre file name minus author is the title (the author's name had filled the share) | 1,065 | 263 | 182 | 926 |
| 9 | One title starting the other, word for word | 1,079 | 249 | 192 | 941 |
| 10 | Same, both ways, cut last word allowed; file extension stripped from citations | 1,101 | 227 | 202 | 965 |
| 11 | A cut fragment under 3 letters still ends the title | 1,101 | 227 | 201 | 965 |
| 12 | Two-word titles equal on both sides count without an author; one-word equality no longer does | 1,103 | 225 | 195 | 967 |
| 13 | Folders above a non-Calibre file may back an author (never veto one) | 1,098 | 230 | 206 | 965 |
| 14 | Author after the last " — "; a plain " - " author backs but never vetoes; word-order rule needs 2 words | 1,105 | 223 | 198 | 970 |
| 15 | Leading author words skipped in a file name ("Neelis-ed-Early-…") | 1,107 | 221 | 198 | 972 |

Every run after run 2 was compared entry by entry with the one before; each lost and each newly matched entry was read. Wrong matches that later runs removed include: "Pāli Literature" matching any book with both words; "The Embodied Mind" matching "Mind Embodied, Mind Bodified"; "Merit" matching "Ten Ways Of Making Merit"; "The Gospel of Judas" matching "Reading Judas"; every Yoga Sutras translation matching Bryant's; Oberlies's "Pali Grammar" volumes matching his "Pāli: A Grammar of the Language…"; "The Role of the Brahmavihara in Cu…" matching another Weber article; Anālayo's one-word encyclopedia entries ("Satipatthana", "Mara", "Brahma") matching his books; "Udana — Bhikkhu Analayo" matching Masefield's translation; "Christian Ethics — A Very Short Introduction" matching "Christian Ethics (Blackwell)".

## Second round (runs 16–22, same day, at the user's request)

| Run | Change | Matched | Unmatched | 2+ folders | Agreement |
|---|---|---|---|---|---|
| 16 | Number words become digits; a Roman numeral after "Vol./Part/Chapter" or ending a title becomes a digit; "vol", "volume", "part", "chapter" stop counting; a whole shorter hit title with no author may not start a longer citation; any part after an old plain dash may hold the author | 1,107 | 221 | 194 | 973 |
| 17 | Neighbouring words also count joined ("NIBBĀNA GĀMINIPAŢIPADĀ" = "Nibbānagāminīpaṭipadā") | 1,108 | 220 | 194 | 973 |
| 18 | "page", "pages" stop counting | 1,109 | 219 | 194 | 974 |
| 19 | Typo in a word of 8+ letters (similarity ≥ 0.93, which keeps Dhammapada/Dhammapāla apart) forgiven when the authors agree; an author name leading a file name counts as the author agreeing | 1,115 | 213 | 197 | 982 |
| 20 | Main titles must fit one within the other (too strict: lost 16 right matches, Piya Tan's numbered files among them) | 1,106 | 222 | 188 | 974 |
| 21–22 | Softened: main titles must share a word, author names aside | 1,114 | 214 | 196 | 981 |

Removed as wrong in this round: Oberlies "Pali Grammar Part I" against Part II; Abhidharmakośabhāṣyam Vol. I against Vol. II (both ways); Lotus Sutra ch. 19 against chapters 11 and 12; three Pali-English Dictionary letter volumes; Keyes's "Flourishing: Positive Psychology…" against Compton's "Positive Psychology: … Flourishing". Gained as right: Mahāvastu I and III, "Journal - Sayagyi U Ba Khin", Hansen's "Uconscious", Sharf's "Buddhist Modernism", Compton's "Psycholog_", Armstrong's "History of God", Ñāṇamoli's "Comentary", "MuditaThe Buddha's Teaching", the Pa-Auk vol. 4 file. One unclear removal: "Satipatthana — The Direct Path to Realization" against Anālayo's "Satipattana - The Direct Path To Nibbana" (possibly another edition).

### Read after run 22

- The 27 tuned note/dossier pairs: 89 cases, 6 wrong (6.7%). All 27 multi-folder matches right. Wrong: Lutz, Prebish, WIB slides (no title in the file name), Cousins (article inside a volume), "Expolring" (Calibre typo, similarity 0.89), "Loka,dhamma Sutta 2" (note typo plus extra words).
- A fresh random 10 pairs never read before (seed 59): 23 cases, 5 wrong (22%). Wrong: "Easy Steps to Yoga" (file `Sivananda easysteps.pdf`), "Vijnaptimatratasiddhi Sastra" (Calibre typo plus extra subtitle words), "Kaccayana and Kaccayanavutti — Ole Holten Pind" (Calibre stores the reviewer Falques as author), "Pride and the Path" (a talk inside "ePublished Dhamma Talks II"), "Dhammaniti - a Pali handbook…" (one-word title, no author). One unclear: "Self-Compassion in Early Buddhism" against "From Compassion to Self-Compassion…".
- Together: 112 cases, 11 wrong (9.8%). Nine of the eleven are data problems (no title in the file 3, chapter inside a book 2, spelling or author errors in Calibre or the note 4); two are rule limits.

### Looking the book up in the index (the user's suggestion, probed read-only)

The index holds each book's full text. For the seven hard misses, the cited title was searched in the book's indexed text (found by its file path, since old numbers move):

| Citation | Title words in first 3,000 chars | Exact title phrase at offset |
|---|---|---|
| Regulation of the Neural Circuitry of Emotion… (Lutz) | 6/6 | 0 |
| The Implications of the New Dating of the Buddha (Prebish) | 4/4 | 97 |
| Women in Buddhism lecture slides (Anālayo) | 2/4 | not found (the citation describes, it does not quote) |
| The 'Five Points' and the Origins of the Buddhist Schools (Cousins) | 5/5 | 1,074 (the volume's contents) |
| Easy Steps to Yoga (Sivananda) | 3/3 | 0 |
| Pride and the Path (Thanissaro) | 0/2 | not found (a talk deep in a collection) |
| Dhammaniti | 1/1 | 16 |

Five of seven would be recovered. Task 2.1b adds this as a fallback in the checkers.

## Final read (run 15)

The 27 note/dossier pairs from three random samples of 10 notes each (seeds 11, 23, 41, overlapping) were read in full under the final matcher: every unmatched entry and every entry matching two or more book folders. 92 cases (run 14 read 93; run 15 then matched Neelis's book, which leaves the unmatched list).

| Class | Cases | Right | Wrong |
|---|---|---|---|
| Two or more folders | 28 | 27 (copies, volumes or parts of one work) | 1 |
| Unmatched, book never logged in this dossier | 56 | 56 | 0 |
| Unmatched, book logged | 8 | 0 | 8 |
| **Total** | **92** | **83** | **9** |

Wrong cases, each read:

- "The Wisdom of the Lotus Sutra, ch. 19" also matches the chapter 11 and 12 files of the same work (non-Calibre folder title; "ch." is too short to count and "19" is spelt "Nineteen").
- "Regulation of the Neural Circuitry of Emotion by Compassion Meditation — Antoine Lutz": the file is `2008_LutzA_PlosOne{CompassionMeditation}.pdf`. The title is not in the file name.
- "The Implications of the New Dating of the Buddha — Charles S. Prebish": the file is `prebish-article.pdf`. The title is not in the file name.
- "Women in Buddhism lecture slides (2015) — Bhikkhu Anālayo": the file is `WIB04.pdf`. The title is not in the file name.
- "The 'Five Points' and the Origins of the Buddhist Schools — L.S. Cousins": an article inside "The Buddhist Forum Volume II". The file names the volume, not the article.
- "Exploring the Saddaniti — E.G. Kahrs": Calibre's own title is misspelt "Expolring".
- "sd.42.3 Loka,dhamma Sutta 2 (AN 8.6) — Piya Tan": the note misspells "Lokadhamma".
- "Journal - Sayagyi U Ba Khin - S.N. Goenka": two plain dashes, so the author read is Goenka and the one-word title "Journal" has no author support.
- "The Mahāvastu, Vol. I — trans. J.J. Jones" against `73180057-Mahāvastu-I.pdf`: the one-letter numeral "I" does not count, so only "Mahāvastu" is left.

## Verdict against the plan's 5% rule

9 of 92 read cases are wrong: 9.8%, above the 5% the plan set. The plan's remedy (adjust and re-measure) was applied 14 times above. Four of the nine cannot be fixed by any title rule: the file name does not hold the cited title (3), or the cited work is a chapter inside another book (1). Two are spelling errors in the source data. Loosening the rules far enough to catch the remaining three (a one-word title without an author, a volume numeral, a chapter number) brought back the false matches recorded for runs 2 and 3.

What a miss costs, by checker:

- Phase 7 gate: a citation that matches no logged hit cannot be checked, so the gate passes it. That is the same as today, where a cited number that is not a logged hit is ignored. A miss never refuses a run.
- Coverage: the hit is listed as unaccounted and the citation as cited but not gathered. Both lists are advisory.
- New runs: hits now carry `cite_as`, and the skill tells the agent to copy it into the note. A copied `cite_as` matches its own hit by construction (the file-name-only titles above included), so these misses come from old dossiers and from citations an agent rewrites.

The tests in `tests/test_library_title_match.py` hold 15 matching and 7 non-matching pairs, every string copied from a real note and its dossier (paths checked against the logged hits).

## Index-text look-up in the checkers (task 2.1b, runs 23–26)

- Run 23 removed folder names outside Calibre as titles (a category folder "Library" let any line with that word name the hit). It lost 13 right matches whose folder is the book ("Sutta Nipata", "The path of purification") and was undone. Run 24 fixed the real fault instead: a folder word cannot be author evidence for a title made of that same word. 1,113 matched.
- Run 25 (`--with-text`): a citation that names no hit by name is looked up in the logged hits' indexed text. 38 more entries matched, about 7 wrong: other books naming the title in an "Also by" list or a reference ("Manual of Insight" naming "The Progress of Insight", Gombrich's "What the Buddha Thought" naming "How Buddhism Began", Anālayo's books naming "Satipaṭṭhāna"). The found phrase sat within the first 60 words in nearly every right case and at word 91–418 in the wrong ones.
- Run 26: the title must have 3+ title words, start within the first 60 words, and the cited author must appear on that page. 19 more entries matched (1,132 in all): 17 right (Prebish, Lutz, Easy Steps, Frauwallner, Cuevas, Davidson, Ireland in Buddhist Studies Review 12.1, …), 1 wrong (the front matter of "Perspectives on Satipatthana" lists "Satipaṭṭhāna: The Direct Path to Realization"), 1 unclear ("kaccayana - Unknown"). Measure run time with the look-up: 11.6 s.
