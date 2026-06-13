---
name: align
description: Compare how different translators render a Pāḷi word or phrase, as an easy-to-scan Markdown table. Use when the user asks to compare/align translations of a Pāḷi term, or types /align <phrase>.
---

# Translation Aligner

Goal: given a Pāḷi word or phrase, produce one easy-to-scan Markdown table of how
different translators render *that* word or phrase. Nothing more.

This works standalone (the only thing a session needs) or as a block inside a
larger Vicaya note — it just prints a Markdown table.

## Procedure

1. **Run the tool** with the user's Pāḷi phrase (exact, with diacritics):

   ```bash
   uv run tools/align_translations.py --phrase "<pāḷi>"
   ```

   If the user already named a sutta, scope it: `--in MN1`.

2. **If the output starts with `AMBIGUOUS`** the phrase occurs in more than one
   sutta. **Do not guess.** Show the user the candidate suttas and ask which
   context they want, then re-run with `--in <ref>`.

3. **If the output is a table**, it already holds the deterministic, segment-
   aligned rows: the Pāḷi and every English Bilara translator. These are exact —
   keep them as-is.

4. **Fill the EBC rows.** For each file under "EBC sources to read", open it,
   find the passage matching the Pāḷi segment, and extract *that translator's
   rendering of the target word/phrase* — reading the context to isolate it.
   Append one row per English translator (skip Pāḷi-only sources). If a passage
   genuinely cannot be located, write `—`; do not invent a rendering.

5. **Present the combined table.** Translators as rows, the rendering as the
   cell. Drop it in chat, or into the note if this is part of a larger task.

## Rules

- Never guess which passage to compare — on ambiguity, always ask the user.
- Never fabricate a translator's rendering; use `—` when unknown.
- Keep the table focused on the word/phrase, not whole sentences where avoidable.
