# Spec — Translation Aligner

**GitHub issue:** #23 — Pāḷi Translation Comparison / Aligner Tool

## Goal
Given a Pāḷi word or phrase, produce an easy-to-scan Markdown table showing how
different translators render *that word/phrase* — nothing more.

This is the issue's "query" idea, not segment-ref alignment. Input is a Pāḷi
term; output is a translator-comparison table.

## Why an independent tool
Sometimes a translation comparison is the *only* thing wanted from a session;
other times it is one part of a larger Vicaya note. So the capability lives in
its own standalone file with its own CLI, reusing existing helpers from
`research_sources.py`. It prints a Markdown table to stdout — which is both the
standalone deliverable and directly pasteable into a note. No coupling to the
note-writing pipeline.

## The easy/hard split (drives the design)
- **Easy — SuttaCentral / Bilara (deterministic, tool does it fully):** root
  Pāḷi and every English Bilara translator share identical segment keys
  (`mn1:52.1`). Grep the root Pāḷi for the phrase → segment key(s) → pull the
  *same keys* from each English author. Exact alignment, no guessing.
- **Hard — EBC translators (Bodhi, Thanissaro, Anīgha, …):** whole-sutta prose,
  no segment keys. Extracting the rendering needs reading comprehension. The
  tool does **not** guess these; it locates the sutta and lists the EBC
  translator files. The **agent** reads them and fills those rows.

## Behavior
1. CLI: `uv run tools/align_translations.py --phrase "<pāḷi>" [--in <ref>]`.
2. Grep Bilara root Pāḷi for the phrase → matching `(uid, segment_key)` pairs.
3. **Disambiguation (never guess):** if `--in` is absent and the phrase matches
   **more than one sutta**, print `AMBIGUOUS: …` listing the candidate suttas
   and stop. The user must supply the context via `--in`. If `--in` is given,
   filter to that uid.
4. **Deterministic Bilara rows:** for the matched segment key(s) in the chosen
   sutta, emit the Pāḷi text plus each English Bilara author's aligned text as
   table rows.
5. **EBC handoff:** print the EBC translator files that exist for that sutta
   (translator label = top folder under `+Suttas/Sutta Texts/`). The agent
   reads these and appends one row per translator.
6. No Bilara match → report no match (likely diacritics); no table.

## Output shape
```
Phrase: cakkāni   Sutta: an4.31   Segments: an4.31:1.1

| Translator | Rendering |
| :-- | :-- |
| **Pāḷi** | “Cattārimāni, bhikkhave, cakkāni, … |
| Sujato (Bilara) | “Mendicants, there are these four situations. … |

EBC sources to read for an4.31:
- Bodhi: .../Bodhi/an-bodhi/an4-bodhi/an4.31-bodhi.md
- Thanissaro notes: .../Thanissaro notes/an-thanissaro/an4-thanissaro/an4.31-thanissaro.md
```

Note: verse texts (Dhammapada, Theragāthā, Sutta Nipāta) are stored by
SuttaCentral in range-named files (`dhp279:1` lives in
`dhp273-289_root-pli-ms.json`), so the tool must locate the file from the grep
hit, not from the uid, or those rows come back empty.

## Out of scope (deliberately, per "A→B not XYZ")
- Segment-`--ref` mode (the issue's first interface).
- Source wiki-links (too hard to align; user does not want them).
- Heuristic EBC paragraph-scoring — the agent reads instead.
- CST canon row — agent can add via existing `search_canon` if ever wanted.

## Acceptance
- `--phrase` with a distinctive phrase prints a Bilara table + EBC file list.
- A phrase in >1 sutta with no `--in` prints `AMBIGUOUS` and no table.
- `--in` scopes to one sutta.
- New deterministic logic covered by `tests/test_align_translations.py`.
- Reuses `research_sources` helpers; no new dependencies; prints to stdout.
