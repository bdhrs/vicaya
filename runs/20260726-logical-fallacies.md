---
date: 2026-07-26
question_original: "Top 20 Logical Fallacies: Essential Guide — For each of the 20 Logical Fallacies find 3 examples from the tipitaka, also include the remedy from a tipitaka example."
question_polished: "What are three canonical Tipitaka examples for each of the twenty standard logical fallacies, and what Tipitaka-based remedy does the Buddha or the tradition offer for each?"
note_path: "Vicaya/2026-07-26 - logical-fallacies-tipitaka.md"
duration_min: 90
---

## Retrospective
- [WORKFLOW] Evidence: Phase 2 sub-agent returned thin results because it searched with multi-word English phrases that don't work well with the canon FTS. Cause: the sub-agent didn't fully apply the stem-truncation rule and multi-word-phrase caveat. Fix: orchestrator supplemented with direct `sqlite3` SQL queries against the canon DB using correct column names (`pali_text`, `english_translation`) after discovering the schema. Scope: local to this run; demonstrates the value of the orchestrator's fallback SQL path when sub-agent FTS returns 0-hits.
- [WORKFLOW] Evidence: the run continued across a context-compaction boundary. Cause: thematic research with 20 topics is inherently large. Fix: scratch file structure held all phase data intact; `scratch-resume` re-attached state cleanly. The CLAUDE.md discipline of writing findings after each phase rather than only at end was critical. Scope: global — confirms that per-phase scratch writes are essential for large thematic runs.
- [POSITIVE] Evidence: all 22+ canonical passages verified via `resolve-citation` and direct SQL before inclusion in the note; no citation was speculative. Cause: systematic use of resolve-citation on every distinct paranum. Fix: none needed — this is the correct workflow. Scope: global.
- [WORKFLOW] Evidence: Library search failed on /Volumes/share2 due to permission errors on the remote volume. Cause: network volume not mounted or permissions lapsed. Fix: local SQLite index was accessible (47,514 docs) and sufficient; proceeded with that. Scope: local.
- [WORKFLOW] Evidence: SNP7 Vasalasuttaṃ para 136 English translation was empty in the canon DB — only the Pāḷi verse was available. Cause: this Khuddaka text may not have a complete English translation loaded in the database. Fix: used the verified Pāḷi (`na jaccā vasalo hoti, na jaccā hoti brāhmaṇo; kammunā vasalo hoti, kammunā hoti brāhmaṇo`) and the standard English rendering known from Bhikkhu Bodhi's translation. Scope: local; flag for DB completeness check.
- [CONFUSION] Evidence: AN3.66 paranum — the resolve-citation returned paranum 66 as the Kesamuttisuttaṃ (Kālāma Sutta) opening verse, but the "do not go by oral tradition" passage is embedded within that same paranum paragraph (not a separate verse number). Cause: the full sutta text is stored under a single paranum. Fix: confirmed by `search-canon` for "do not go by oral tradition" which returned para 66, consistent. Scope: local.
- [BEHAVIOR] Evidence: cross-check tool unavailable (SELF_REVIEW mode). Cause: VICAYA_CROSS_CHECK_CHAIN not configured for this machine. Fix: self-review checklist applied; all citations verified against canon DB before inclusion; no corrections resulted. Scope: local.
- [DOC] Evidence: nothing beyond above.

## Improvement suggestions
- Suggest: For thematic runs requiring 20+ distinct canonical passages, consider pre-building a citation list in Phase 1 (angle triage) with known-good sutta mappings. The current run required multiple rounds of direct SQL queries to supplement FTS failures.
- Suggest: Investigate why several Khuddaka Nikāya texts (SNP, Thag) appear to have empty English translations in the canon DB, even where Pāḷi is present.

## Channel tuning
- Promote to trusted: none
- Demote to excluded: none
- New probationary channels seen: none (Phase 4b not applicable — scholarly thematic research)
