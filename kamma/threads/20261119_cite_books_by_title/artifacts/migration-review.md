# Migration review (task 4.2, 2026-11-19)

The script's own report is `migration-dry-run.md` (counts, every unresolved number with its line, per-note summary). This file records what was read and judged before `--apply`.

## Final dry run

- 360 notes considered, 334 changed, 157 with at least one run dossier. Dossiers are matched by the `**Vault note:**` header; 203 notes have none on this machine (no dossier names them, by header or slug), so their own `library_refs` are their only title source.
- Actions: 2,288 `library_refs` prefixes dropped; 3,013 footnote labels renamed `[^lib-<k>]`; 5,158 numbers deleted beside a title the line already names; 2,155 numbers replaced by their title; 6 numbers inside a `library_refs` entry and 4 inside another frontmatter list deleted; 838 unresolved and 2 ambiguous numbers removed.
- Simulated validation of the migrated texts (in memory, before any write): 0 `library-number` findings in 360 notes. Against `validate-baseline.json` per note and kind: 96 `invalid-library-ref` findings go away (entries now quoted); `undefined-footnote` unchanged per note (the same missing definitions under their new labels); `long-sentence` warnings fall by 12 and rise by 8 in 7 notes, where a number that was part of a sentence became a title (warnings only, listed in the plan).
- Every changed line keeps its URLs byte for byte (0 mismatches over 9,296 changed lines), and every note keeps its line count.
- A title from a dossier is never inserted where the note's own `library_refs` paired that number with a title: the resolver returns the `library_refs` title alone when it has one.

## The unresolved list, read

840 entries (838 unresolved, 2 ambiguous) in 99 notes; 783 in notes with no dossier. Sorted into three kinds and read:

- **Table rows (503).** Almost all are "Sources Investigated, Not Used" rows that name the work in plain words: "Liao Fan's Four Lessons (Calibre #9363)", "Della Santina (Calibre #4557)", "Anālayo encyclopedia entries (Calibre #434, #436, …)". Removing the number keeps the row's meaning.
- **Id lists (99).** Consolidated rows and paragraphs that list ids only ("IDs: Calibre #301, Calibre #1366, …", "Document IDs: calibre #137, …"). Removing them leaves the consolidated row, which is what the spec intends; the cleanup removes the emptied "IDs:" label and the commas.
- **Prose and bullets (238).** Nearly all are a number beside a title the line already holds (bibliography entries, footnote definitions with `[[Title]]`, bullets with an italic title). A few lines name the work less fully ("Donald Hoffman's Interface Theory of Perception (Calibre #15237)"); one number inside a sentence leaves "bibliography entry in; JBE review" (2026-11-12 five-aggregates-six-doors-biology-check), as no title exists for it.

Resolving these from today's index by id was considered and rejected: the ids may have moved since those runs, and inserting a wrong title is worse than removing a number.

## Faults found while reading, fixed before the final run

Each has a regression test in `test_migrate.py` (21 tests, all from real lines):

- "(canonical copy: #696)" became "(canonical copy: )": a bare number was judged against a title the script had just inserted. Naming is now judged on the line as written.
- "Duplicate file of Calibre #1275, already cited" became "Duplicate file of, already cited": a number inside a sentence is now replaced by its title even when the line names the book elsewhere; only a number set aside (brackets, after a comma or semicolon, at a line or cell start) is deleted.
- A number ending a table cell left "Unbound*, | T3"; a list of separately prefixed ids left ",,,,"; an emptied "Document IDs:" label stayed; "(Calibre #5046.)" left "(.)".
- "[[The Mystery of the Breath Nimitta]]" did not count as naming "The Mystery of the Breath Nimitta or The Case of the Missing Simile"; the first three title words in order now count.
- "library id 14956" and "document id 35290" escaped both the migration and the validator; numbers inside a `library_refs` entry, and a book listed under `canon_refs`, were missed.
- The validator's `index` pattern flagged "Stanford HAI AI Index 2025"; `index` now needs a `#`.
