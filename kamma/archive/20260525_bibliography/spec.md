# Spec — Bibliography

## Overview

Add a proper academic bibliography to every Vicaya research note. The current
system has inline footnotes (locators) but no consolidated, properly-formatted
bibliography. This thread adds one.

## Bibliography system adopted — Chicago Notes-Bibliography (N-B)

**Why Chicago N-B over alternatives:**

| System | Used by | Verdict |
|---|---|---|
| Chicago Notes-Bibliography | JIABS, PTS publications, Oxford Journal of Buddhist Studies, Wisdom/U.Hawaii press | **Adopted** |
| Chicago Author-Date | Journal of Buddhist Ethics, Philosophy East and West | Good alternative, but doesn't suit primary-source-heavy notes |
| MLA | Comparative literature, some religion | Not used in Buddhist Studies |
| APA | Psychology/science | Wrong genre |
| SOAS/Oxford house style | Bulletin of SOAS | Variant of Chicago N-B; compatible |

Chicago N-B is the dominant style in academic Theravāda / Pāḷi Studies. It works
naturally with footnotes (which already exist) and handles primary sources
(canonical texts) cleanly as a separate section.

**AI research sessions:** excluded from bibliography. The agent footer already
records model identity and date.

## What it should do

1. Every Vicaya note ends with a `## Bibliography` section organized into five
   subsections:
   - **Primary Sources** — Pāḷi canon and parallel Āgama texts
   - **Secondary Sources** — library books (Calibre) and journal articles
   - **Online Sources** — web pages, SuttaCentral links
   - **Media Sources** — YouTube talks and Dhamma recordings
   - **Vault Sources Referenced** — internal Obsidian notes cited via wiki-link

2. Each entry is fully formatted in Chicago N-B style.

3. Footnotes remain as short locators (current system unchanged). The bibliography
   provides the full, sorted, publication-ready reference.

4. Phase 5 synthesis guidance is updated so the agent builds bibliography entries
   incrementally as sources are gathered — not in one go at Phase 7.

## Chicago N-B format rules (per source type)

### Primary sources (Pāḷi canon)

Standard form (CST access, no specific translator):
  *Majjhima Nikāya* 60 (*Apaṇṇakasuttaṃ*). Chaṭṭha Saṅgāyana Tipiṭaka.
  Accessed via tipitaka-translation-data.db (`s0201m_mul`).

With a translator (when using an EBC translation file):
  *Majjhima Nikāya* 10. Translated by Bhikkhu Sujato.
  In *Middle Length Discourses of the Buddha*. SuttaCentral, 2018.

Chinese Āgama parallels:
  *Madhyamāgama* 98 (*Zhongahanijing* T 26). Translated by Charles Patton.
  Accessed via EBC vault, `ma-patton/ma98-patton.md`.

### Secondary sources (library books)

Standard form:
  Last, First. *Title: Subtitle*. Place: Publisher, Year. (Calibre #NNNN)

Chapter in edited volume:
  Last, First. "Chapter Title." In *Book Title*, edited by First Last, pages.
  Place: Publisher, Year. (Calibre #NNNN)

Examples:
  Gethin, Rupert. "Bhavaṅga and Rebirth According to the Abhidhamma."
    In *The Buddhist Forum, vol. III*, edited by T. Skorupski and U. Pagel,
    11–35. London: SOAS, 1994. (Calibre #10228)

  Karunadasa, Y. *Theravāda Abhidhamma: Its Inquiry into the Nature of
    Conditioned Reality*. Hong Kong: University of Hong Kong, 2010. (Calibre #7335)

  Harvey, Peter. *The Selfless Mind: Personality, Consciousness and Nirvāṇa
    in Early Buddhism*. Richmond: Curzon Press, 1995. (Calibre #6294)

### Online sources

  Last, First (or Organisation). "Page Title." *Site Name*. Month Day, Year. URL.

  Example:
  Sujato, Bhikkhu. "What Is Bhavaṅga?" *SuttaCentral*. Accessed May 25, 2026.
  https://suttacentral.net/...

### Media sources (YouTube / Dhamma talks)

  Teacher/Channel. "Talk Title." *YouTube*. Month Day, Year. URL.
  [Human captions | auto-captions (paraphrase only)]

### Vault sources referenced

  [[Note Title]] — Vicaya research note, YYYY-MM-DD.

## Constraints

- No changes to the footnote system (they remain short locators).
- No changes to the YAML frontmatter (library_refs / canon_refs remain as-is).
- The bibliography section is placed after ## Critical Gaps and before the ---footer---.
- If a subsection has no entries, omit it entirely.

## How we'll know it's done

- SKILL.md has a "Bibliography" section with format rules and adopted system
- Phase 7 template includes `## Bibliography` with all subsections
- Phase 5 guidance instructs the agent to accumulate bibliography entries in the scratchpad
- An example entry is shown for each source type

## What's not included

- Upgrading footnotes to full Chicago N-B format (they stay as short locators)
- Retroactive reformatting of existing vault notes
- Automatic PDF bibliography export
