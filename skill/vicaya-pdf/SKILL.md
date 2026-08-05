---
name: vicaya-pdf
description: Audit and repair the Vicaya PDF tree so every note has exactly one PDF twin and the tree holds nothing else — generates the missing PDFs and deletes the orphans. Invoke when the user types /vicaya-pdf or asks to "check the PDFs", "fix the missing PDFs", "clean up the orphaned PDFs", or "make the PDFs match the notes".
---

# Vicaya PDF tree

Keep the vault's PDFs an exact mirror of its notes. One note, one PDF, nothing else.

## The folder standard

Every PDF lives under the single `Vicaya/PDF/` tree, whose subfolders mirror the notes' own subfolders. A PDF is never written beside its note.

```
Vicaya/
├── 2026-08-05 - some-question.md
├── Digest/
│   └── 2026-08-05 - some-topic.md
├── What the Suttas Say About/
│   └── 2026-08-05 - what-the-suttas-say-about-x.md
└── PDF/
    ├── 2026-08-05 - some-question.pdf
    ├── Digest/
    │   └── 2026-08-05 - some-topic.pdf
    └── What the Suttas Say About/
        └── 2026-08-05 - what-the-suttas-say-about-x.pdf
```

The rule in one line: `Vicaya/<subfolder>/<name>.md` → `Vicaya/PDF/<subfolder>/<name>.pdf`, and a note in the root goes straight into `Vicaya/PDF/`.

`tools/note_checks.resolve_pdf_path` owns this mapping. `generate_note_pdf.py` and `sync_notes.py` both derive the path from it, so a new note's PDF lands correctly without anyone passing an output path. Never hardcode a PDF path anywhere; if the layout ever needs to change, change that one function.

## Procedure

1. **Audit first.** This reports and touches nothing:

   ```bash
   uv run scripts/sync_note_pdfs.py
   ```

   It prints the note count, then one line per problem: `missing PDF: <path>` for a note with no twin, and `orphan: <path>` for anything in the tree that is not a twin. Exit code is `0` when the tree is already a mirror, `1` when it is not.

2. **Show the user the audit before repairing.** `--fix` deletes files. If the orphan list is longer than a handful, or contains anything the user might still want, name what will go and get a yes first.

3. **Repair.**

   ```bash
   uv run scripts/sync_note_pdfs.py --fix
   ```

   It generates every missing PDF from its note, deletes every orphan, and removes any subfolder left empty. Then it prints what it did.

4. **Confirm.** Re-run the bare audit — it must come back clean.

5. **Report the counts.** Notes, PDFs, generated, deleted. If nothing was wrong, say so plainly rather than inventing work.

## What counts as an orphan

Anything in the PDF tree that is not the twin of a current note:

- A PDF whose note was deleted or renamed.
- A PDF left at the old path after its note moved into a subfolder.
- A file that is not a PDF at all — a stray `.html` render, a scratch file.

All of it goes. The tree is twins and nothing else.

## Rules

- Never write a PDF beside its note, and never treat `$VICAYA_PDF_PATH` as an output directory — it is an on/off toggle only.
- Never delete anything outside `Vicaya/PDF/`. Notes are never this skill's to remove; a note with no PDF is a PDF to generate, not a note to delete.
- Do not hand-roll the audit with `find` and `diff`. The script is the definition of correct, and it is tested.
- The vault is a git repo. Deletions and additions show up as ordinary changes — commit them only when the user asks.
