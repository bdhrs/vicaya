# Reviews — task 5.3

## Independent subagent audit (2026-11-19)

A context-free subagent read the spec, the plan and the uncommitted change, ran the five changed test files (512 passed, 1 skipped) and probed the gate, the matcher, the validator and the applied migration with throwaway scripts outside the repo. Each finding below is marked fixed or not fixed, with the reason.

1. **High — fixed.** The Phase 7 gate refused runs on ordinary prose and on books named only in a rejection reason. A body line with "not read" or "unread" named a hit through its file code, so "We should not read the Visuddhimagga as a meditation manual." flagged the Calibre book `Visuddhimagga - Buddhaghosa.pdf`: a one-word code skipped the rule that a one- or two-word title counts only beside its author. A Not Used row was matched on its whole text, so a row rejecting a web essay "Snippet shows it only repeats Bodhi's A Comprehensive Manual of Abhidhamma" asked for the Bodhi book to be read. Fix in `tools/scratch.py`: gate lines no longer match file codes (`_line_names_hit(..., codes=False)` from `_hits_named_in_line`; coverage keeps them), and a rejection row is matched on its first cell plus any library footnote marker in the row. Tests: `test_unread_library_citations_ignores_a_book_named_in_a_rejection_reason`, `test_unread_library_citations_ignores_a_one_word_title_in_prose` (which also checks that "Buddhaghosa's Visuddhimagga was snippet-only." still flags the book). Both failed before the fix and pass after it.
2. **Medium — fixed.** Citing the translator refused a book that was read. With a read Calibre copy "The Path of Purification — Buddhaghosa" and an unread plain copy "The Path of Purification.pdf", the citation "The Path of Purification — Bhikkhu Ñāṇamoli" was ruled out of the read copy by the author check but matched the authorless copy, so the gate listed it under `cited_not_read`. This broke the spec's rule that copies of one book count as that book. Fix: `_read_under_own_author` treats a citation (or a rejection row's first cell) as read when a read hit matches its title under that hit's own author. Test: `test_unread_library_citations_reading_a_copy_under_its_author_reads_it` (failed before, passes after; the unread case is still refused).
3. **Medium — not fixed, latent.** The validator's `doc`/`document`/`library` + number pattern also matches non-library text: "Damascus Document 4Q266", "Loeb Classical Library 75", "Nag Hammadi Library 1977", "Library 2.0". The migration's pattern would have damaged such text ("Damascus Q266"). Checked: all 840 unresolved migration removals carry a library lead word, and no note in the vault holds such text today, so nothing was damaged. Left for a later thread: any narrower pattern also lets real forms through ("document 11839" without `#` is a real note form).
4. **Low — not fixed.** `_HitNames` splits a hit's `cite_as` at the first " — " while `_split_citation` splits a citation at the last one. A Calibre title holding " — " puts title words into the hit's author words, which loosens the author check. Causes misses, not refusals.
5. **Low — not fixed.** Volumes of one series match each other ("A Comparative Study of the Majjhima-nikāya, Vol. 1" against "Vol. 2": 4 of 5 words is exactly 80%). Causes misses, not refusals.
6. **Low — not fixed.** `_build_calibre_metadata_lookup` returns nothing on any SQLite error (as before this thread), and the refresh then deletes that root's `calibre_books` rows, so a locked `metadata.db` silently drops its titles until the next refresh.
7. **Low — not fixed, latent.** The migration's `--from-head` reads committed notes through `subprocess.run(text=True)`, which turns CRLF into LF. Checked: no vault note has CRLF, and every changed note kept its line count. The script is a one-off and already applied.
8. **Tests.** No gate test covered plain prose or a non-library rejection row; findings 1 and 2 now have tests. The renumbering test uses fixtures without a Calibre `metadata.db`, so it does not exercise stored Calibre titles; not changed.

Checked and fine: URLs in changed note lines are byte-identical (24 before, 24 after), every changed note kept its line count, no CRLF anywhere, and the docs match the code.

After the fixes: ruff, ruff format, pyright and pyrefly clean on `tools/scratch.py` and `tests/test_research_sources.py`; full suite 805 passed.

Process note: the subagent was briefed read-only but went on to edit `tools/scratch.py`, `tests/test_research_sources.py` and this file after reporting. The main session diffed its edits against the pre-review copy, kept them (they fix real refusals), and re-ran every check: 805 passed, all checkers clean, vault untouched.

## CodeRabbit (`coderabbit review --agent --fresh --uncommitted --include-untracked`, 2026-11-19)

19 findings; `validate-baseline.json` was not reviewed (diff too large). Each checked against the code:

1. Migration: a year after an unmarked number could be read as an id if an id with that value resolved. **Not fixed:** the migration is applied and one-off; the year test covers the common case.
2. Migration: `~~~` fences were not skipped. **Not fixed:** applied one-off; no note holds a library number inside a tilde fence (the post-migration validator over all notes found 0 numbers).
3. Migration: two dossiers mapping one id to different titles keep the first. **Not fixed:** applied one-off; the note's own `library_refs` win before any dossier.
4. vicaya-quick: `cite_as` of a non-Calibre file has no author. **Fixed:** the skill says to take the author from the book.
5. Coverage: a footnote that fails the citation match because the authors disagree can still be credited by the line rule. **Not fixed:** coverage is advisory; the gate keeps the author check.
6. A non-Calibre category folder can act as a title. **Not fixed:** it can only clear a citation (a miss); measured runs showed such folders are mostly the book's own folder ("Sutta Nipata", "The path of purification").
7. Validator: "Library 101 — Jane Smith" is flagged. **Not fixed, latent:** same class as the subagent's finding 3; no note holds such a title.
8. A document id reused after a rebuild can clear an unread citation. **Not fixed:** accepted risk in the spec (resumed runs across a rebuild).
9. An authorless one-word label ("Dune") does not match its own citation. **Not fixed:** a miss, not a refusal.
10. Validator: a body `library_refs:` example enters the list rule. **Not fixed:** latent, a false finding only in that odd shape.
11. Gate: `library_refs` read outside the frontmatter. **Fixed:** only the opening frontmatter counts. Test: `test_unread_library_citations_reads_library_refs_from_frontmatter_only`.
12. Gate: a book named in the reason cell cleared or caused a rejection. **Fixed** by the subagent (first cell only).
13. Gate: in a grouped rejection row, reading one book cleared all. **Fixed:** each book in the first cell (split on ";") is checked alone. Test: `test_unread_library_citations_checks_each_book_in_a_grouped_rejection`.
14. A failed `metadata.db` read wiped that root's stored titles. **Fixed:** an unreadable catalogue returns None and its root keeps its stored titles. Test: `test_an_unreadable_catalogue_keeps_the_stored_titles`.
15. Old FTS rows can still hold a "Calibre #" prefix. **Not fixed:** this index never had the prefix (0 of 46,456 rows, spec); new rows get the number-free prefix.
16. Validator: a `library_refs` entry of only a number passed. **Fixed.** Test: `test_a_library_ref_holding_only_a_number_is_reported`.
17. Matcher: Vol. 1 matched Vol. 2. **Fixed:** when a citation gives a volume, part or chapter number, a hit giving a different one is rejected ("Nikaya 2" as a trailing number counts). Test: `test_a_cited_volume_matches_only_that_volume`. Measure re-run: exactly three wrong-volume matches removed, none lost.
18. Gate: the text look-up skips copies when one copy matched by name. **Not fixed:** a miss; reading the name-matched copy clears the gate.
19. Gate: read handles from an old dossier may be stale after a rebuild. **Not fixed:** accepted risk in the spec.

After all fixes: full suite 810 passed; migration tests 22 passed; ruff, ruff format, pyright and pyrefly clean on all touched files.


## Kamma review round (2026-11-19): independent reviewer and CodeRabbit again

Independent read-only subagent (this time it stayed read-only) and a fresh CodeRabbit run (13 findings) on the code after the round above. Fixed, each with a test that fails when the fix is reverted (two of them revert-checked):

- **Major — "not read" as "interpret".** "Gombrich's *What the Buddha Thought* does not read anattā as …" flagged a book the run had read. "Not read"/"unread" now flag only a book the run did not read; "snippet-only" and "could not be read" still flag any readable book, and "unmounted" every book.
- **Major — volume rule skipped by the index-text look-up.** A "Vol. 2" citation was matched to Vol. 1 through its title page. The look-up now applies the same volume check.
- **Major — blank line after `library_refs:`** stopped the gate reading the list. Blank lines are skipped (gate and validator).
- **Major — latest extraction status.** A document re-extracted later in the run kept its first `empty` status; the latest logged status now wins.
- **Major — another translation counted as read.** The translator rule applies only when every copy the citation matches has no known author.
- **Major — footnote markers across a rejection row.** Each part of the first cell is matched with its own markers only; markers in the reason cell no longer count.
- **Major — exact one-word label.** An authorless file's exact label ("Buddhavacana") now names it.
- **Minor, fixed:** fenced footnote examples are not citations; coverage no longer re-credits a sibling volume through a citation line; validator patterns for "Loeb Classical Library 237", "Damascus Document 4Q266", body examples of `library_refs`.
- **Not fixed:** migration resolver keeping a number inside a refs title (applied one-off; post-migration validation found 0 numbers); old "Calibre #" FTS prefixes (this index never had them); a `library_refs` title starting with digits and a colon ("84000: …", nit, rare); folder hints in the three-word title-start rule (nit).

Final: full suite 822 passed; migration tests 22 passed; all checkers clean; 0 library numbers over 395 notes.
