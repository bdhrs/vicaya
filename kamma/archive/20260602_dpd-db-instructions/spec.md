# Spec — DPD database instructions

## Overview
Add a self-contained "DPD dictionary database" section to `skill/vicaya/SKILL.md`
documenting how a Vicaya run queries `dpd.db` (the Digital Pāḷi Dictionary
database from the dpd-db project) directly for Pāḷi word, grammar, and root
research. Today the skill only touches `dpd.db` indirectly via `sutta_info`
citation checks; there is no guidance for the dictionary's two primary lookup
paths.

## What it should do
1. New section `## DPD dictionary database (\`dpd.db\`)` placed after
   "Book-identifier lookups (`lookup-book`)" and before "## EBC vault".
2. State the env var `$VICAYA_DPD_DB` and path; if unset, instruct the user to
   add `VICAYA_DPD_DB=~/path/to/dpd-db/dpd.db` to `.env`.
3. Document **Way 1 — headword lookup** (`dpd_headwords`, query `lemma_1`) and
   **Way 2 — inflected/compound lookup** (`lookup` → resolve the JSON
   `headwords` id array against `dpd_headwords.id`), each with a working,
   verified `sqlite3` example.
4. Compact reference table of all 12 tables with one-line use cases.
5. Vicaya-specific use cases tying into existing skill workflows (verify a
   term's meaning before quoting; find the root family; locate commentarial
   glosses; resolve a canon inflected form to its dictionary entry — connects to
   the stem-truncation rule).
6. One-line spelling note (exact diacritics, `ṃ` niggahita).
7. Note that a SQLAlchemy model layer exists in dpd-db for programmatic access,
   but Vicaya runs use raw SQL.
8. Add one Setup-list bullet pointing to the section; add a one-line
   cross-reference at the stem-truncation rule.

## Assumptions & uncertainties
- `VICAYA_DPD_DB` already exists in `.env`/`.env.example` (verified) →
  `~/MyFiles/3_Active/dpd-db/dpd.db` (verified, 2.2 GB, read-only).
- `sqlite3` CLI is available and already used in the skill for the canon db
  (verified — documented at SKILL lines 786–790).
- Schema verified by direct query: 12 tables, column names exact. `lookup.headwords`
  is a JSON array of `dpd_headwords.id`; `lookup.grammar`/`deconstructor`/`roots`
  are JSON. `lemma_1` is sense-numbered (e.g. `dukkha 3`).

## Constraints
- Doc-only. No code, no helper changes, no new CLI subcommand, no `.env` edits.
- Decision (agreed with user): raw SQL via `sqlite3`, NOT the dpd-db SQLAlchemy
  ORM — read-only simple reads, zero cross-repo coupling, stable schema vs.
  churning module API, consistent with existing canon-db access.
- Match existing skill prose style. Read-only DB.

## How we'll know it's done
- New heading present; both `dpd_headwords` and `lookup` flows have verified
  examples; all 12 tables listed; Setup bullet + stem-rule cross-reference added;
  every `sqlite3` example re-run against the live db returns rows.

## What's not included
- New CLI subcommand or `research_sources.py` changes.
- `.env` modifications.
- Full per-column documentation of every table (one-line use case per table only;
  `dpd_headwords` and `lookup` get key-column detail).
