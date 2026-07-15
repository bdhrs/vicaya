# Spec — Vicaya PDF folder cleanup + misplacement fix

## Context

This thread is a retrospective record of work already carried out earlier in
the same session, at the user's direct request, so the decisions are on file.
Implementation happened before this thread was opened; the thread exists to
document it, not to plan new work.

## Problem

1. A large number of "What the suttas say about X" companion PDFs had
   accumulated in the vault-root `Vicaya/PDF/` folder instead of their series
   subfolder's own `Vicaya/What the Suttas Say About/PDF/`.
2. Root cause: `scripts/generate_note_pdf.py` always wrote every note's PDF
   into a single flat directory taken from `VICAYA_PDF_PATH`, regardless of
   which vault subfolder the source note actually lived in. This bug had
   already been flagged (but only worked around, not fixed) in a prior run
   retrospective, `runs/20260715-054645.md`.
3. Some `.md` notes in the vault had no corresponding PDF at all.

## Decisions

- **Misplaced-file resolution rule:** for each misplaced PDF, compare byte
  content against the same-named file already in the correct folder.
  - Identical → delete the misplaced copy, keep the correct-folder one.
  - Different → treat the one whose content matches the newer `.md` edit
    timestamp as authoritative, copy it into the correct folder (overwriting
    the stale copy), then delete the misplaced one.
  - Confirm the full list with the user before touching any file (per the
    user's explicit request and this project's file-safety norms).
- **Root-cause fix, not a one-off cleanup:** rather than only moving files,
  fix `generate_note_pdf.py` so PDF output directory is derived from the
  note's own path (`note_path.parent / "PDF"`), eliminating the flat-directory
  bug permanently. `sync_notes.py`, which independently re-derives the PDF
  path to commit it alongside the note, is updated to match.
- **`VICAYA_PDF_PATH` semantics change:** the env var stops being read as an
  output directory and becomes a pure on/off toggle (non-empty = generate
  PDFs). Documented this in `README.md` and `.env.example`.
- **Full vault PDF coverage:** as a follow-up ask, every `.md` file in the
  vault (not just series notes) was checked for a matching PDF in its own
  `PDF/` subfolder, and missing ones were generated with the existing
  `generate_note_pdf.py` tool — no new tooling.

## Non-goals

- No change to the note content itself, only PDF export artifacts.
- No change to `.env` (per global project rules, `.env` is never modified
  directly by an agent).
- No new PDF generation tool or pipeline — reused `generate_note_pdf.py`
  as-is (aside from the directory-derivation fix).

## Acceptance

- `/Vicaya/PDF/` contains no leftover "what the suttas say" stray PDFs.
- `/Vicaya/What the Suttas Say About/PDF/` holds the most up-to-date PDF for
  every series note.
- `generate_note_pdf.py` and `sync_notes.py` write/look up PDFs relative to
  the note's own folder, verified by a regression test.
- Every `.md` in the vault has a matching PDF.
- Full test suite green.
