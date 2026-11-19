# Handoff — cite books by title (2026-11-19, end of implementation)

## State

- Every task in `plan.md` is done and verified, including the independent reviews (5.3, `artifacts/reviews.md`). Next step: the user tests, then `/kamma:3-review` in a fresh session, then `/kamma:4-finalize`.
- Nothing is committed, in this repo or in the vault. Committing needs the user's explicit go-ahead.
- Repo changes: `tools/library_folders.py`, `tools/scratch.py`, `tools/note_audit.py`, `tools/note_checks.py`, four changed test files plus the new `tests/test_library_title_match.py`, `skill/vicaya/SKILL.md`, `skill/vicaya-quick/SKILL.md`, `kamma/tech.md`, and this thread folder.
- Vault (`<vault>/Vicaya`, its own git repo): 334 notes migrated and their PDFs regenerated, all uncommitted for review. Validator over all 360 notes: 0 library numbers. `git -C <vault>/Vicaya diff` shows every change.
- Final checks: full suite 810 passed; migration tests 22 passed; ruff, ruff format, pyright and pyrefly clean on all touched files.

## Things a reviewer should know

- The title matcher went through 28 measured versions (`artifacts/matcher-measure.md`); its last judged read had 9.8% wrong, mostly from data problems (file names without titles, chapters inside books, typos in Calibre or the notes). A miss lets the gate pass a citation; it never refuses a run.
- The review subagent broke its read-only brief and edited `tools/scratch.py` and the research-sources tests; its edits were diffed, kept and re-verified (recorded in `reviews.md`).
- Revert proofs ran in a plain code copy in the session scratchpad, not a git worktree, because the user's rules forbid git write commands unless asked.
- The migration was applied twice: the second run (`--from-head`, reading committed notes with a read-only `git show`) fixed two faults found in the end-to-end check. Details in plan 4.4.
- Known open items, all recorded with reasons in `reviews.md`: latent validator false positives ("Damascus Document 4Q266", "Library 101"), stale ids across an index rebuild in resumed runs (accepted risk in the spec), and matcher misses on descriptive citations.

## Constraints still in force

- Prefix every helper and pytest call with `VICAYA_SCRATCH=/dev/null/none`.
- No commit, push or `sync_notes.py` without the user's go-ahead.
