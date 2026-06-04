# Plan - Notes push auto-sync

## Architecture Decisions

- **Instruction-only change.** The existing scripts already provide the
  required side effects and boundaries; changing code would add unnecessary
  risk.
- **Keep the publishing boundary explicit.** `sync_notes.py` becomes
  automatically invoked, but only as the approved notes-repo publishing script.
  Agents still must not run arbitrary git/publish commands.

## Phase 1 - Update Phase 7 note publishing instructions
- [x] Replace the old `GitHub push (user-triggered)` text in
  `skill/vicaya/SKILL.md` with automatic/pre-approved note sync wording.
  Include the exact `uv run scripts/sync_notes.py "Vicaya/${TODAY} -
  ${SLUG}.md"` command, side effects, non-fatal failure note, and arbitrary-git
  boundary.
  -> verify: `rg -n "AskUserQuestion|Should I push|only after user approval|user-triggered" skill/vicaya/SKILL.md` returns no live old prompt wording.
- [x] Update the Setup bullet that currently says notes publish only after user
  approval.
  -> verify: `rg -n "user approval|approves publishing|Should I push|AskUserQuestion" skill/vicaya/SKILL.md skill/vicaya/README.md` returns no old live note-publishing approval instruction.
- [x] Re-read the edited Phase 7 context for ordering and safety clarity.
  -> verify: `sed -n '1790,1830p' skill/vicaya/SKILL.md` shows validate -> PDF -> note sync -> Phase 7 exit/run-report sync.

## Phase 2 - Review and validation
- [x] Run narrow search verification across live skill docs and scripts for old
  note-publish approval wording.
  -> verify: no conflicting live references remain.
- [x] Run the smallest relevant local checks. Since this is a Markdown-only
  instruction change, do not run Python tests unless a Python file changes.
  -> verify: targeted `rg` checks pass; if running Ruff, scope it to Python
  scripts only.
- [x] Write `review.md` with findings, validation evidence, and verdict.
  -> verify: review records files changed and any residual risk.
