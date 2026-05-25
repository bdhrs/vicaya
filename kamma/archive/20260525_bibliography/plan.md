# Plan — Bibliography

## Architecture Decisions

- Bibliography section appended after `## Critical Gaps` — keeps note body clean;
  footnotes (locators) remain immediately after the footer, as now.
- Subsections only emitted if non-empty — agents must check before writing headers.
- Calibre ID retained in parentheses as a Vicaya-specific addition to Chicago N-B.
  Not part of the published standard, but makes the reference immediately actionable.
- Phase 5 is the right place to accumulate bibliography entries — sources are
  evaluated for inclusion during synthesis.
- New "## Bibliography" section in SKILL.md goes after Evidence Tiers, before Phase 0.

---

## Phase 1 — Add bibliography system spec to SKILL.md

- [x] Add a new "## Bibliography" section to SKILL.md after the Evidence Tiers table,
  explaining: adopted system (Chicago N-B), alternatives comparison, and format rules
  for all five source types, with worked examples.
  → verify: section present in SKILL.md; all five source-type formats shown

## Phase 2 — Update Phase 5 synthesis guidance

- [x] Add a bibliography accumulation block to Phase 5 in SKILL.md:
  as sources are finalized, write their full Chicago N-B entry into the scratchpad
  under `## Bibliography (accumulating)`. Also add this block to the scratchpad
  init template.
  → verify: Phase 5 section explicitly mentions bibliography accumulation

## Phase 3 — Update Phase 7 note template

- [x] Add `## Bibliography` section to the Phase 7 template after `## Critical Gaps`
  and before the `---` footer, with all five subsections and placeholder entries.
  → verify: Phase 7 markdown template block includes Bibliography section with
    correct format for each subsection type
