# Spec — Calibre search guidelines + Pāḷi/English translation conventions

## Overview
Two doc-only improvements to `skill/vicaya/SKILL.md`. No code changes to
`tools/research_sources.py` — the helper logic is sound; what was missing was
agent-facing guidance for (a) Calibre searches that frequently miss, and
(b) consistent rendering of Pāḷi/English in the vault note.

## Repo context discovered
- Calibre library lives at `$VICAYA_CALIBRE_LIBRARY` =
  `~/MyFiles/2_Resources/Libraries/Bodhirasa eBook Library`. 12,501 books.
- 2,140 tags, 6,042 author entries, 607 series, 21 languages.
- Top tags by book count (sample): Academic 2085, Buddhism 957, English
  Translation 893, History 808, Psychology 668, Philosophy 631, !tagme 621,
  Meditation 574, Pali Canon (Tipitaka) 552, Tibetan Buddhism 538, Pali Text
  514, dhamma talk 434, Doctrine 415, Mindfulness 390, Pali 1167 (loose).
- Top authors: Piya Tan 1293, Bhikkhu Anālayo 410, Unknown 346, Vipassana
  Research Institute 249, Pali Text Society 114, Anandajoti Bhikkhu 104,
  Bhikkhu Bodhi 79, Thanissaro Bhikkhu 76.
- Title formats coexist: "Bhikkhu X" (58), "X Bhikkhu" (25), "Ajahn X" (38),
  "X Sayadaw" (22), "Ven. X" (98), "Dr. X" (56).
- Tag noise: `!tagme` (621), `!name me` (230), `Readme!` (93).
- Tag vocabulary fragmentation, observed live: `Pali Canon`, `Pāli Canon`,
  `Pali Canon (Tipitaka)`, `Pali Canon (About)`; `Nibbana` (52), `Parinibbana`
  (7), `Nibbida` (3), `Nibbāna` (1, stray diacritic).
- Calibre `--search` is **case- and diacritic-insensitive** by default.
  Verified: `title:paticcasamuppada`, `title:Paticcasamuppada`, and
  `title:paṭiccasamuppāda` all return the same 13 hits. The existing
  `_strip_diacritics(query)` call in `search_calibre` is harmless but the
  SKILL's tone overstates the brittleness — agent over-corrects queries.
- Tag matching: helper uses **exact match** (`tags:"=Nibbana"` → 52 hits).
  Loose match (`tags:Nibbana`) → 60 (pulls in `Parinibbana`). Decision: leave
  helper as exact; document loose as a fallback the agent can widen to.
- Series field (607 entries, e.g. *Wheel Publication*, *BDK English Tripiṭaka
  Series*, *Journal of the Pali Text Society*) is currently undocumented and
  unused by the agent.

## User decisions
- Tag-matching default stays exact (`tags:"=X"`); loose documented as
  fallback.
- Translation formatting conventions apply to the **vault note only**, not
  the terminal report.

## What it should do

### A. Calibre search guidelines (Phase 3 of SKILL.md)
A new self-contained block inside *Phase 3 — Library search* containing:

1. **`--search` syntax cheat sheet** — free-text vs. field-scoped
   (`title:`, `authors:`, `tags:`, `series:`, `publisher:`, `comments:`,
   `languages:`), boolean joins (`and`/`or`/`not`), exact-match prefix `=`,
   quoted phrases.
2. **Diacritic / case correction.** Calibre metadata search is already
   case- and diacritic-insensitive. The helper still strips diacritics for
   safety; both forms work. Don't waste a search round trying both.
3. **Tag matching: exact vs. loose.** Helper uses exact. To widen, the
   agent can call the helper with a related-tag list, or fall back to a
   free-text query and post-filter.
4. **Tag vocabulary reference clusters.** Common groups: Pali Canon
   variants, nikāya tags, doctrinal cluster (`Anatta`, `Anapanasati`,
   `Satipatthana`, `Jhana`, `Vipassana`, `Mindfulness`, `Meditation`,
   `Rebirth`, `Death & Dying`), tradition cluster (`Theravada`, `Thai Forest
   Tradition`, `Sri Lankan Tradition`, `Myanmar Tradition`, `Tibetan
   Buddhism`, `Zen Buddhism`, `Mahayana`, `Madhyamaka`), plus the noise
   tags to ignore.
5. **Author naming conventions.** Title-stripping rule: search the
   distinguishing element, not the title. `authors:Analayo` beats
   `authors:"Bhikkhu Analayo"`. Also: corporate/canon "authors" exist
   (`Samyutta Nikaya`, `Pali Text Society`, `Vipassana Research Institute`,
   `Wikipedia`) and are good seed entries.
6. **Series field.** When a topic implies a known imprint, scope with
   `series:`.
7. **Search ladder** (5 rungs) for when hits are thin: tag-scoped phrase →
   free-text phrase → drop tag → synonym tag cluster → known-author search.

### B. Pāḷi/English presentation (Style notes section)
A new "Pāḷi/English presentation (vault note only)" block covering:

1. **Sentence/paragraph quotations.** Each quoted Pāḷi sentence/paragraph
   in a markdown blockquote, blank line, then the English translation in a
   second blockquote.
2. **Inline Pāḷi inside English prose.** All Pāḷi words italicised
   (`*paṭiccasamuppāda*`). English gloss in round brackets on **first**
   appearance per section: `*paṭiccasamuppāda* (dependent origination)`.
   Subsequent uses in the same section: italics only.
3. Additional conventions:
   - Sutta names italicised in Pāḷi form (`*Apaṇṇakasutta*`), but the
     citation tag stays roman (`MN60`).
   - Keep IAST diacritics exactly as the canon db returns them.
   - Use stem form in prose (`dukkha`), inflected form only when quoting
     verbatim (`dukkhaṃ`).
   - English-loaned terms stay roman after first introduction: Dhamma,
     Buddha, Nibbāna, sutta, Sangha.
   - Verse: preserve line breaks inside the blockquote.

A short cross-reference at the top of Phase 5 (Synthesis) points to this
block so the agent encounters the rules while drafting.

## Constraints
- Edits limited to `skill/vicaya/SKILL.md`. Helper code untouched.
- No new comments in code.
- All numeric examples cited verbatim from this thread's live measurements.
- Don't contradict Hard Rule 3 — refine it, don't replace it.

## How we'll know it's done
- Phase 3 contains the Calibre guidelines block with all seven items.
- Style notes contains the Pāḷi/English presentation block with all
  conventions and a worked example.
- Phase 5 has a one-line cross-reference to the presentation block.
- `rg -n "diacritic|Calibre|italics|blockquote" skill/vicaya/SKILL.md`
  surfaces all the new content in coherent context.

## What's not included
- Refactoring `search_calibre` / `_calibre_metadata_search`.
- Flipping the helper's tag-match default.
- Editing the embedded book code map.
- Rewriting any existing research notes to the new style.
