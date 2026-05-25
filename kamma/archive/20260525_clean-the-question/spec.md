# Spec — Clean the Question

## Overview
The vicaya skill passes the user's raw research question directly into the note's `topic:` frontmatter field. Sometimes the phrasing is informal, has poor grammar, or carries preconceived framing ("the politically incorrect Buddha", "critique of X", "against cessationism"). Since the notes are read publicly, the question as it appears in the note should read as a mature, neutral, well-formed English sentence or question — without any conclusions already embedded in it. The research body shows the facts; the question just names the topic.

Two things need to happen:
1. Add a question-sanitization step to `SKILL.md` so all future runs clean the question before using it in the note.
2. Reword the `topic:` (or `title:`) field in all 41 existing vault notes to match the same standard.
3. Re-export all updated notes to PDF so the PDFs stay in sync.

## What it should do

### SKILL.md change
- In the `## Inputs` section, after receiving the raw question, add a step: rewrite the question as a proper English sentence or question before using it in the note's `topic:` field.
- Rules: complete sentence, correct grammar, question mark where the phrasing calls for it, no loaded or leading language, no strong preconceived position embedded in the wording.
- The verbatim user input is preserved in the run reflection's `question:` field only.

### Vault note rewording
- Update the `topic:` or `title:` frontmatter field in each of the 41 vault notes.
- Light-touch rewording only: fix bad English, neutralize loaded framing, add question marks where appropriate.
- Do not change any other content, filename, or field.

### PDF re-export
- Re-run PDF generation for every updated note so the PDF folder matches.

## Assumptions & uncertainties
- Some notes use `topic:`, others use `title:`. Both will be updated in-place (field name unchanged).
- All 41 `.md` files in `~/MyFiles/Obsidian/Vicaya/` (excluding README.md and the PDF subfolder) are in scope.
- PDF generation uses the existing weasyprint script from SKILL.md.
- `VICAYA_PDF_PATH` is set in `.env`.

## Constraints
- SKILL.md change: one small addition to the Inputs section only.
- Vault notes: only the `topic:`/`title:` field value changes.
- No filename changes, no content changes beyond that one field.

## How we'll know it's done
- SKILL.md Inputs section includes a clear question-sanitization instruction.
- All 41 vault notes have clean, neutral, well-formed `topic:`/`title:` values.
- PDFs in `Vicaya/PDF/` have been regenerated for all updated notes.

## What's not included
- Changing note filenames or slugs
- Changing any body content
- Changing field names (topic vs. title)
- Retroactive changes to the run reflections
