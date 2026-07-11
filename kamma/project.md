# Project — Vicaya

## What it is and why
Vicaya is a multi-source research workflow for Pāḷi and Buddhist topics,
invoked as `/vicaya <question>` inside Claude Code (or any agent that reads
a Markdown skill file). It queries the user's Obsidian vault, a local CST
canon SQLite database, the Early
Buddhist Connections (EBC) reference vault, their library folders, a local
GRETIL Sanskrit corpus, YouTube Dhamma talks, and the open web — in that order
— cross-checks the synthesis with a second model, and writes a single
structured Markdown note into the vault. The goal is to make deep Pāḷi research
fast, citation-complete, and cumulative.

Two lighter-weight sibling modes exist: `/vicaya-quick <question>` answers
directly in chat with citations (no vault note, no gates), and
`/vicaya-pre <topic>` checks existing vault coverage first to recommend
which mode fits.

## Who it's for
A single user: a practitioner with a local Obsidian vault, library folders
of Buddhist texts, and the CST canon database.

## One-off or ongoing
Ongoing. Each research run adds a note to the vault; the corpus grows
and cross-links accumulate over time.

## What it produces
A Markdown note at `<vault>/Vicaya/YYYY-MM-DD - <slug>.md` with:
- YAML frontmatter (date, topic, canon_refs, library_refs, web_refs, tags)
- Sectioned findings with inline citations
- Wiki-links to related existing vault notes

## How we'll know it's working
- `/vicaya <question>` produces a note in under 30 minutes with ≥1 canon
  citation, ≥1 library citation, ≥1 web citation, and valid Obsidian
  frontmatter.
- A second run on a related topic links back to the first via `[[wiki-link]]`.
- All source helpers have passing pytest tests.

## Maintenance
- `skill/vicaya/SKILL.md` is the canonical full-run skill.
