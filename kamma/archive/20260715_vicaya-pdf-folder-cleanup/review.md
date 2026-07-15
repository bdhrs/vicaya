# Review — Vicaya PDF folder cleanup + misplacement fix

## Verified against actual state

- `git status --short`: touched files match the plan exactly —
  `.env.example`, `README.md`, `scripts/generate_note_pdf.py`,
  `scripts/sync_notes.py`, `tests/test_generate_note_pdf.py`. No unrelated
  changes.
- `scripts/generate_note_pdf.py` diff: `pdf_dir` now derives from
  `note_path.parent / "PDF"` instead of the flat `VICAYA_PDF_PATH` value;
  the env var is only checked for truthiness. Matches spec.
- `scripts/sync_notes.py` diff: PDF lookup path derivation updated to the
  same `note_path.parent / "PDF"` rule, so the note-and-PDF commit pairing
  stays correct after the generator change. Matches spec.
- Full test suite: `uv run -m pytest -q` → 276 passed, including the new
  regression test and the updated output-path assertion.
- Vault check: `Vicaya/PDF/` has zero remaining "what the suttas say" stray
  files; every `.md` in the vault (recursively, all subfolders) has a
  matching PDF in its own `PDF/` subfolder.

## Judgment on the approach

- The root-cause fix (deriving output dir from the note's own path) is the
  right level to fix this at — it's a one-line change, uses no new
  dependency, and structurally can't reproduce the bug for any future
  subfoldered note type (climbs the laziness ladder correctly: reused
  existing structure rather than adding configuration).
- Keeping `VICAYA_PDF_PATH` as a toggle rather than removing it preserves
  the "skip PDF generation entirely" escape hatch some environments may
  rely on, without carrying forward the part of its old contract that was
  actually wrong (that it named a location).
- File-deletion decisions (28 identical, 1 trivial, 3 promoted) were
  confirmed with the user before any file was touched, consistent with the
  project's file-safety norms and the global "discuss before acting" rule.

## Outstanding gaps

None found. No blocking issues.

## Verdict

Accepted as complete. Ready to finalize.
