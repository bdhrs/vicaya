# Spec - Notes push auto-sync

## Overview

Update Vicaya Phase 7 instructions so vault-note publishing uses the same
pre-approved automation model as run-report publishing. After a successful note
write, note validation, PDF generation, and Phase 7 gate, agents should run the
existing `scripts/sync_notes.py` command for the saved note without an extra
yes/no approval prompt.

## What it should do

1. Remove the `AskUserQuestion` approval step from the Phase 7 note-publishing
   instructions.
2. Keep `scripts/sync_notes.py` as the only allowed automation path for
   publishing Vicaya notes to `bdhrs/vicaya-notes`.
3. Keep the safety boundary explicit: agents must not run arbitrary git,
   publishing, deployment, sync, delete, or overwrite commands outside approved
   scripts.
4. Keep sync failure non-fatal because the note is already saved locally.
5. Update directly related live references that still describe note publishing
   as user-approved.

## Assumptions & uncertainties

- `scripts/sync_notes.py` already existed and is the approved note publishing
  script. It loads `.env`, targets `$VICAYA_VAULT_PATH/Vicaya/`, runs
  `git pull --rebase`, stages only the named note, commits only if needed, and
  pushes `origin HEAD`.
- `scripts/sync_run_report.py` remains the model for pre-approved publishing
  wording. It targets this project repo's `runs/*.md` reports for the current
  UTC date.
- No script behavior changes are required.

## Constraints

- Documentation/instruction change only.
- Do not modify `.env` or local machine configuration.
- Do not run the publishing scripts as part of this implementation.

## How we'll know it's done

- `skill/vicaya/SKILL.md` no longer instructs agents to ask whether to publish
  the saved note.
- The Phase 7 instructions explicitly run
  `uv run scripts/sync_notes.py "Vicaya/${TODAY} - ${SLUG}.md"` automatically.
- Safety wording still confines publishing to approved scripts and treats sync
  failure as non-fatal.
- Narrow verification confirms no old live approval-prompt references remain.
