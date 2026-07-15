---
date: 2026-07-15
question_original: "how does the visudhimagga go in a different direction from suttas. use the previous research notes to list all major changes in direction, novelties and new ideas"
question_polished: "What do the Early Buddhist Texts say about the Visuddhimagga's novelties and departures from the suttas?"
note_path: Vicaya/What the Suttas Say About/2026-07-15 - what-the-suttas-say-about-visuddhimagga-novelties-and-departures.md
duration_min: 75
---

## Retrospective
- [POSITIVE] Evidence: The existing 14 vault notes on jhāna, vipassanā-ñāṇas, vitakka-vicāra evolution, bhavaṅga, two-truths, momentariness, kasiṇa, pīti, and the path-terms-development note provided a ready seed list of 20 candidate departures (A–T), so the Phases 2–4 searches were targeted confirmation rather than discovery-from-zero. Cause: strong prior vault coverage of individual Vism departure points written across many separate notes. Fix: preserve — the series note format successfully aggregates scattered findings into one catalogue. Scope: local.
- [POSITIVE] Evidence: The 0-hit canon confirmations (upacārasamādhi, appanāsamādhi, sammutisacca, paramatthasacca, sukkhavipassaka, bhavaṅga, khaṇika — all absent from `s*_mul`) provide the strongest form of evidence (confirmed absence) and appear for 7 of 17 departure entries. Cause: the Phase 2 agent methodically ran both the Vism-search and the sutta-novelty-check search for each term. Fix: this confirms the value of explicit "search for the term in suttas and expect 0 hits" as a check step. Scope: global.
- [WORKFLOW] Evidence: The Phase 4a sub-agent's gate refused at first because it ran in parallel with Phase 3 (whose gate hadn't been written yet). Cause: parallel dispatch of gather sub-agents creates a gate-ordering race. Fix: after all parallel agents returned, I wrote the 4a gate manually since the prerequisite (Phase 3 gate) was now present. Lesson: always verify sibling-gate status after parallel dispatch and backfill any refused gates. Scope: local.
- [BEHAVIOR] Evidence: The self-review caught two issues: (1) the Vism entry #5 Pāḷi quote was a garbled DB hit concatenation, and (2) entry #12 said "Vism introduces the chariot simile" when SN 5.10 is the actual origin — Vism repurposes it. Cause: the Vism quote was pasted from a noisy search result; the chariot claim conflated Vism's two-truths framework with the simile's invention. Fix: replaced the garbled quote with a clean passage; changed "introduces" to "repurposes…from SN 5.10." Lesson: always verify verbatim quotes against the source and check simile origins against the canon. Scope: global.
- [BUG] Evidence: The cross-check helper returned the SELF_REVIEW sentinel (opencode/agy chain unavailable). Cause: harness environment without the configured cross-check providers. Fix: self-review fallback worked as designed; the 5-point checklist was applied and two corrections made. Scope: local.
- [DOC] Evidence: The skill's sub-agent dispatch model assumes Claude-Code-style agents; in pi the available agents (planner/reviewer/scout/worker) are generic, so the gather phases were delegated as worker agents. Cause: harness mismatch — pi agents lack the vicaya SKILL.md context. Fix: the Phase 2 agent ran all 25+ canon searches successfully despite having to read the SKILL sections; Phase 3 ran all 21 library searches; Phase 4a was partially limited (no web search tool). The pi worker model worked adequately with detailed prompts. Scope: local.
- [NOTE] Evidence: scratch-check-coverage flagged 262 gathered library hits with 5+ unaccounted — Ajahn Teean (sammuti-paramattha terminology), Alexander Wynne (Polak citation), and several others. Cause: these are tangential sources whose content was captured through higher-priority authors (Karunadasa for two-truths, Bucknell/Polak for jhāna). Fix: none needed — the coverage check is advisory; the note's primary claims rest on the key scholarly sources cited. Scope: local.

## Improvement suggestions
- Suggest: When a note draws heavily on existing vault notes (14 cross-referenced here), add a run-phase shortcut that skips Phase 2–4 gather in favour of vault-note extraction. The canon searches were still needed for verbatim quotes, but the library and web work was substantially redundant with the existing notes.
- Suggest: Add a Phase 1 step to explicitly list the existing notes and the departure points they document, so the gather agents can focus on gaps rather than re-confirming what's already written. This was done informally but a structured "seed map" would reduce duplication.
- Suggest: The two-truths Vism passage (chariot simile) was hard to locate via keyword search — a direct structural index of Vism chapters XVIII–XXIII key paragraphs would speed Phases 2 and 5.

## Channel tuning
- Promote to trusted: none
- Demote to excluded: none
- New probationary channels seen: none (Phase 4b YouTube skipped — textual comparison question)
