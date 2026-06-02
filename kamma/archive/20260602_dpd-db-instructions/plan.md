# Plan — DPD database instructions

## Architecture Decisions
- **Raw SQL via `sqlite3`, not the dpd-db SQLAlchemy ORM.** Rationale: read-only
  simple column reads; the ORM's value (JSON pack/unpack, display properties) is
  for building/editing the dictionary; importing it forces cross-repo venv
  coupling against a module that churns (release dated daily), whereas the
  table/column schema is stable; consistent with how the canon db is already
  documented (SKILL lines 786–790). The one ORM convenience we'd use —
  unpacking the `headwords` id array — is a single `json.loads()`.
- **Placement:** new top-level section between "Book-identifier lookups" and
  "EBC vault" — groups it with the other reference/lookup material.
- **Doc-only:** no helper subcommand, to keep it short/sweet/minimal per the
  request and avoid touching `research_sources.py`.

## Phase 1 — Write the section
- [x] Insert `## DPD dictionary database (\`dpd.db\`)` after line 137 (end of
  "Book-identifier lookups"), before `## EBC vault`. Content: env/location +
  unset instruction; Way 1 (headword) example; Way 2 (inflected/compound) example
  with the `json.loads` id-resolution step; 12-table reference; Vicaya use cases;
  spelling note; ORM-exists note.
  → verify: `grep -n "DPD dictionary database" skill/vicaya/SKILL.md` returns the
    heading; section contains both `dpd_headwords` and `lookup` examples.
- [x] Add a Setup-list bullet after the canon-db bullet (~line 64) referencing
  `$VICAYA_DPD_DB` and pointing to the new section.
  → verify: `grep -n "VICAYA_DPD_DB" skill/vicaya/SKILL.md` shows the Setup line.
- [x] Add a one-line cross-reference at the stem-truncation rule (~line 925)
  noting the `lookup` table resolves an inflected form to its headword(s).
  → verify: read line context, confirm pointer present.
- [x] Phase verification: re-read the inserted section start-to-end for prose
  consistency and correct markdown.
  → verify: section reads cleanly, tables render, no broken fences.

## Phase 2 — Verify examples against live db
- [x] Re-run every `sqlite3` example in the new section against
  `$VICAYA_DPD_DB` to confirm each returns rows.
  → verify: each command prints output.
