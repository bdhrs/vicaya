# Project — Vicaya

## What it is and why
Vicaya is a multi-source research workflow for Pāḷi and Buddhist topics,
invoked as `/vicaya <question>` inside Claude Code (or any agent that reads
a Markdown skill file). Lower-context staged runs use the sibling skills
`vicaya-0-scope`, `vicaya-1-gather`, `vicaya-2-synthesize-review`, and
`vicaya-3-complete`, which route back to exact sections in the main skill. It
queries the user's Obsidian vault, a local CST canon SQLite database, the Early
Buddhist Connections (EBC) reference vault, their Calibre library, a local
GRETIL Sanskrit corpus, YouTube Dhamma talks, and the open web — in that order
— cross-checks the synthesis with a second model, and writes a single
structured Markdown note into the vault. The goal is to make deep Pāḷi research
fast, citation-complete, and cumulative.

## Who it's for
A single user: a practitioner with a local Obsidian vault, a Calibre
library of Buddhist texts, and the CST canon database.

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
- `skill/vicaya/SKILL.md` is the canonical full-run skill. When editing it,
  check the staged sibling skills for affected route lists, stage boundaries,
  handoff labels, and bounded context-break guards.
- When editing `skill/vicaya-0-scope`, `skill/vicaya-1-gather`,
  `skill/vicaya-2-synthesize-review`, or `skill/vicaya-3-complete`, verify the
  edited staged skill still routes to exact headings in `skill/vicaya/SKILL.md`
  and does not silently fork canonical workflow behavior.
- The staged sibling skills are section routers, not alternate workflow
  documents. Do not copy behavioral rules into them, do not restore summarized
  shared references under `skill/vicaya/shared/`, and verify every routed
  heading still exists after canonical skill heading changes.
