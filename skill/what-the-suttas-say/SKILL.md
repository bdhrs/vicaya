---
name: what-the-suttas-say
description: Run the full /vicaya workflow with the fixed "What the suttas say about X" series format — earliest-strata evidence vs later attributions, one quote per idea, written into the series subfolder of the vault. Invoke when the user types /what-the-suttas-say <X> or asks for a "what the suttas say about X" note.
---

# What the suttas say about X

A thin wrapper around the canonical `/vicaya` workflow. This file defines only the series conventions; every research mechanic — phases, gates, scratchpad, helpers, evidence tiers, validation, PDF, sync, run reflection — comes from `skill/vicaya/SKILL.md` in this repo and is deliberately not duplicated here.

## How to run

1. **X** = the user's topic, exactly as given (keep Pāḷi diacritics).
2. **Read `skill/vicaya/SKILL.md` in full and follow it as the workflow.** It is the only behavioral source of truth. Do not run any part of the workflow from memory of it.
3. Feed the workflow these series-fixed inputs:
   - `--question-original`: the user's verbatim input.
   - `--question-polished`: `What do the Early Buddhist Texts say about X?`
   - slug: `what-the-suttas-say-about-<x>` where `<x>` is X lowercased, ASCII-folded, hyphenated.
4. At Phase 7, the series spec below is the **caller-supplied fixed format** — the main skill's Phase 7 paragraph "Caller-supplied fixed formats" defines exactly how it hybridizes with the standard note shell (keep frontmatter, `## Question`, a short `## Findings` overview; series sections replace `## Canon Evidence (T1)`; keep the standard tail sections). Follow that paragraph; do not reinvent the hybrid.

## Series spec (the fixed format)

- **Task:** Research and compile what the Early Buddhist Texts (EBTs) say about X. Collect the evidence from the earliest strata and compile it into an easy-to-read reference note.

- **Title:** use exactly `What the suttas say about X` — verbatim, sentence case, no subtitle. This identical string is the note's H1 heading and its `topic:` frontmatter field, and its slug form is the filename slug. This is a fixed series format: do not rephrase, recase, expand, or polish it.

- **Structure:** two main sections.
    1. `## What the EBTs say about X` — ideas with clear support in the earliest strata.
    2. `## What the EBTs don't say about X` — ideas prominent in later Buddhism (or popularly attributed to the Buddha) with no basis in the earliest strata.

- **Entry format (both sections):** present every idea as a self-contained numbered entry (`### N. <idea>`), in this order.
    1. Pāḷi — one canonical quote as a blockquote, with its source reference (nikāya, sutta name/number).
    2. English translation as a blockquote.
    3. Summary — brief; opens with the bold citation (verbatim from `resolve-citation`); note where relevant how the idea connects with, supports, or contradicts others.

- **Rules:**
    - One quote per idea. When an idea recurs, pick the single most prominent passage and note where else it appears.
    - Surface contradictions. If the suttas contradict each other, include it and flag it explicitly — do not smooth it over.
    - Section 1 is earliest strata only — the main skill's **T1a** tier. Anything traceable to later strata (T1b, T2, or later school developments) goes in Section 2, with a note on which stratum it likely comes from.
    - Prefer primary textual evidence over interpretation; keep commentary brief and grounded in the quote.
    - Section 2's negative claims ("the EBTs don't say X", "image X is a later trope") are the highest-risk claims in the note — verify each against the canon DB before asserting it (stem + synonym absence search across all T1a books, including verse texts, with the Hard Rule 12 book-code check). A real run nearly called the mirage simile a later Mahāyāna development when SN22.95 uses it for saññā.

- Make sure to include **all** sutta information on this topic — no skimping. Sweep the whole T1a corpus (all four Nikāyas, the Suttavibhaṅga, and the early Khuddaka texts), not just the first hits.

## Output location

Series notes live in their own vault subfolder. Save, validate, PDF, record, and sync the note at:

```
Vicaya/What the Suttas Say About/${TODAY} - what-the-suttas-say-about-<x>.md
```

Pass this same path to `scratch-set-note`, `validate_note.py`, `generate_note_pdf.py`, and `sync_notes.py`.

Before starting, grep that subfolder — if a note for X already exists, tell the user and ask whether to redo or extend it rather than silently writing a duplicate.
