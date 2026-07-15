# Plan — Vicaya PDF folder cleanup + misplacement fix

Retrospective record: all tasks below were already executed in-session before
this thread file was created. Status reflects actual completed work.

## Phase 1 — Audit and confirm

- [x] List files in `Vicaya/PDF/` and `Vicaya/What the Suttas Say About/PDF/`,
      identify the 32 misplaced "what the suttas say" PDFs by filename pattern.
- [x] For each misplaced file, diff byte content against the correct-folder
      counterpart; for the 4 that differed, extract text with `pdftotext` and
      compare against the note's own edit timestamp to determine which copy
      was current.
- [x] Present the full list and per-file resolution (delete vs. promote) to
      the user for confirmation before touching any file.

## Phase 2 — Apply the file moves

- [x] Delete the 29 byte-identical (or trivially re-rendered, e.g. `marana`)
      misplaced duplicates from `Vicaya/PDF/`.
- [x] Overwrite the stale correct-folder PDF with the newer misplaced content
      for `kayagatasati`, `pancindriya-pancabala`, and `jati`, then delete the
      misplaced copies.
- [x] Verify `Vicaya/PDF/` has zero remaining "what the suttas say" files.

## Phase 3 — Fix the root cause

- [x] Locate the generator: `scripts/generate_note_pdf.py` was writing every
      PDF to a single `VICAYA_PDF_PATH` directory regardless of the note's
      actual vault subfolder.
- [x] Change output directory derivation to `note_path.parent / "PDF"`.
- [x] Update `scripts/sync_notes.py`'s independent PDF-path lookup (used to
      stage the PDF for commit alongside the note) to the same derivation.
- [x] Update `README.md` and `.env.example` to document `VICAYA_PDF_PATH` as
      an on/off toggle, not an output path.
- [x] Add a regression test
      (`test_generate_note_pdf_writes_into_notes_own_subfolder`) proving a
      series-subfolder note's PDF lands in its own `PDF/` dir and not the
      vault-root one.
- [x] Update the existing output-path assertion in
      `test_generate_note_pdf_derives_output_path_and_strips_frontmatter` to
      match the new derivation.
- [x] Run `tests/test_generate_note_pdf.py` and `tests/test_sync_notes.py` —
      6 passed.
- [x] Run the full suite — 276 passed.

## Phase 4 — Full vault PDF coverage

- [x] Scan every `.md` under the vault for a missing sibling PDF in its own
      `PDF/` subfolder.
- [x] Generate the 6 missing PDFs (`README.md`, `summary-vicaya.md`, two DPD
      feedback trackers, one orange-feedback note, and one research note,
      `three-turnings-buddhist-wheel-evolution.md`, that had never gotten one)
      using `generate_note_pdf.py` unchanged.
- [x] Re-scan and confirm zero `.md` files remain without a matching PDF.

## Phase 5 — Retrospective + close-out

- [x] Write this thread (`spec.md` + `plan.md`) as the durable record.
- [x] Review the thread.
- [x] Finalize the thread (archive, update project docs if warranted).
