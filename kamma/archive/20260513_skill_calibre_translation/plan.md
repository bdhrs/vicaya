# Plan — Calibre guidelines + translation conventions

## Architecture decisions
- Single-file edit: `skill/vicaya/SKILL.md` only. No Python changes.
- Calibre guidelines: insert as a self-contained block inside *Phase 3 —
  Library search*, after the existing 4-line tag pointer and before the
  `uv run … search-calibre` example.
- Translation conventions: insert into the "Style notes" section near the
  end of the file (rules apply to the rendered vault note). Add a one-line
  cross-reference at the top of *Phase 5 — Synthesis* so the agent
  encounters it while drafting.
- Keep helper tag-matching as exact (`=X`). Document loose as fallback.
- Ground every claim in live measurements taken in this thread; no invented
  stats.

## Phase 1 — Calibre search guidelines
- [x] Edit `skill/vicaya/SKILL.md` Phase 3 to insert a "Calibre search
      guidelines" subsection containing: (1) `--search` syntax cheat sheet,
      (2) diacritic/case insensitivity note, (3) exact-vs-loose tag matching
      with 52-vs-60 Nibbana example, (4) tag cluster reference table,
      (5) author naming conventions with title-stripping rule, (6) series
      field pointer, (7) 5-rung search ladder.
  → verify: `rg -n "Calibre search guidelines" skill/vicaya/SKILL.md`
  returns 1 hit; read the inserted block end-to-end and confirm each
  numeric claim (12,501 books; 2,140 tags; 60-vs-52 Nibbana; 1,293 Piya
  Tan; 410 Anālayo; 607 series; title-position counts 58/25/38/22/98/56)
  matches spec.md.

## Phase 2 — Pāḷi/English presentation conventions
- [x] Edit `skill/vicaya/SKILL.md` Style notes section to add a
      "Pāḷi/English presentation (vault note only)" block: blockquote-pair
      rule, italics-with-brackets rule, and the five additional
      conventions (sutta names, IAST fidelity, stem-vs-inflected, loaned
      terms, verse line breaks). Include one worked example showing a canon
      hit rendered both as a blockquote pair and inline.
  → verify: `rg -n "Pāḷi/English presentation" skill/vicaya/SKILL.md`
  returns 1 hit; the worked example contains both a `>` blockquote pair
  and an inline `*pali* (english)` form.

- [x] Add a one-line cross-reference at the top of Phase 5 (Synthesis)
      pointing to the presentation block.
  → verify: `rg -n "presentation" skill/vicaya/SKILL.md` returns ≥2 hits
  including the Phase 5 pointer.

## Phase 3 — Whole-file sanity pass
- [x] Read the edited `SKILL.md` end-to-end. Check: no contradiction with
      Hard Rule 3 (Pāḷi spelling conventions per source); markdown tables
      still align; no orphaned cross-references; helper code references
      still match `tools/research_sources.py` reality.
  → verify: `rg -n "diacritic|Calibre|italics|blockquote|presentation"
  skill/vicaya/SKILL.md` — read every hit in context and confirm coherence.
