# Handoff - notes-push

Session saved on 2026-06-04 after discovering an approval-policy mismatch in
Vicaya Phase 7 publishing.

## Latest User Direction

The user wants vault-note GitHub publishing and run-report publishing treated
the same: both should run without an explicit user approval prompt after a
successful Vicaya completion.

Exact issue:

- Current `skill/vicaya/SKILL.md` section `### GitHub push (user-triggered)`
  requires asking the user whether to push the saved research note to
  `bdhrs/vicaya-notes`.
- Current Phase 7 exit requires `uv run scripts/sync_run_report.py` and treats
  run-report publishing as pre-approved.
- The user wants the note-push path to be equally automatic/pre-approved, not
  gated by `AskUserQuestion` / Yes-No approval.

## Source Lines To Inspect

- `skill/vicaya/SKILL.md` lines around 1814-1827:
  `### GitHub push (user-triggered)`, user prompt, and `sync_notes.py`.
- `skill/vicaya/SKILL.md` line around 1833:
  Phase 7 exit requires `scratch-gate 7`, then
  `uv run scripts/sync_run_report.py`.
- `scripts/sync_notes.py`:
  confirm exact side effects before changing the skill wording.
- `scripts/sync_run_report.py`:
  use as the model for pre-approved publishing language.

## Desired Change

Update Vicaya Phase 7 so that after the note is written, validated, PDF
generated, and Phase 7 gated, the agent automatically runs:

```text
uv run scripts/sync_notes.py "Vicaya/${TODAY} - ${SLUG}.md"
```

without asking for explicit user approval, matching the current treatment of
`sync_run_report.py`.

Keep the existing safety framing:

- `sync_notes.py` is the allowed publishing script for the notes repo.
- A sync failure is not fatal because the note is already saved locally.
- Agents still must not run arbitrary git/publish commands outside the approved
  script.

## Suggested Implementation

1. Read `scripts/sync_notes.py` and `scripts/sync_run_report.py` and document
   their material side effects before editing.
2. Edit `skill/vicaya/SKILL.md`:
   replace `### GitHub push (user-triggered)` with automatic/pre-approved
   note sync wording.
3. Check whether staged routers or README docs mention the old approval prompt.
   Update only directly related references.
4. Add or update narrow tests only if existing tests cover Phase 7 instructions
   or script behavior.

## Current Related Context

This came from the `domanassa-akusala-jhana` Vicaya completion run. The note was
saved and validated locally, but was not pushed to GitHub because the current
skill text required explicit approval. The user challenged that asymmetry and
asked for this handoff.

The run-report sync was attempted automatically, as required, but failed for
environmental reasons: the main worktree had unrelated unstaged edits, and a
clean temporary clone could not resolve `github.com`.

## Validation For This Handoff

No implementation was done in this handoff. Validate future implementation with
the smallest relevant checks, likely:

```text
uv run ruff check skill/vicaya/SKILL.md scripts/sync_notes.py scripts/sync_run_report.py
```

Only run Python tests if a code path changes.

## Worktree Caution

The repo already had unrelated dirty files during the prior run, including
`skill/vicaya/SKILL.md`, `tools/research_sources.py`, and Kamma/staged-skill
files. Do not revert or overwrite unrelated edits. Read diffs before editing.
