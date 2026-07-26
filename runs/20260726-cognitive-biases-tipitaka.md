---
date: 2026-07-26
question_original: "20 Cognitive Biases with Examples & Antidotes — For each of the 20 Cognitive Biases find 3 examples from the tipitaka, also include the remedy from a tipitaka example."
question_polished: "What canonical Tipitaka passages illustrate each of 20 common cognitive biases, and what antidotes does the canon prescribe for each?"
note_path: "Vicaya/2026-07-26 - cognitive-biases-tipitaka.md"
duration_min: 120
---

## Retrospective
- [WORKFLOW] Evidence: run crossed a context-compaction boundary mid-session; all findings survived intact. Cause: large thematic run (20 topics × 3 examples + antidote). Fix: per-phase scratch writes held all Phase 2 canon hits, Phase 4a web entries, and Phase 4b/4c results across the compaction. CLAUDE.md discipline confirmed effective.
- [WORKFLOW] Evidence: Phase 3 library search blocked by PermissionError on all /Volumes/share2/ NFS paths. Cause: network volume access restriction during source-available check. Fix: Canon coverage (Phase 2: 60+ hits) was comprehensive for this topic; library skipped with full documentation. Scope: local environment issue.
- [WORKFLOW] Evidence: Obsidian CLI search-vault returned non-JSON output (startup messages prepended). Cause: Obsidian desktop CLI outputs "Loading updated app package…" etc. before JSON. Fix: rg fallback on $VICAYA_VAULT_PATH worked cleanly. Scope: persistent local issue — rg fallback is the correct approach.
- [WORKFLOW] Evidence: Phase 4b (YouTube) and 4c (WisdomLib) sub-agents ran in parallel; both completed on Haiku as mandated by CLAUDE.md. Phase 4c agent initially tried to log a Phase 4b prerequisite gate, but this was handled correctly by gating 4b first. Scope: coordination worked as designed.
- [POSITIVE] Evidence: All 15 canonical citations verified via resolve-citation and verify-citation before inclusion. Key citations: DN1, DN14, DN34, MN2, MN10, MN11, MN18, MN22, MN62, MN82, SN12, AN3.66, AN7.11, Dhp 21-32, Dhp 277. No speculative citations. Scope: global.
- [CONFUSION] Evidence: the Kālāmasutta is AN3.65 on SuttaCentral but AN3.66 (Kesamuttisuttaṃ) in the CST database used by this project. Cause: different sutta-numbering traditions. Fix: used CST number (AN3.66) for internal consistency; noted in self-audit. Scope: project-local.
- [BEHAVIOR] Evidence: cross-check tool unavailable (SELF_REVIEW sentinel). Cause: VICAYA_CROSS_CHECK_CHAIN not configured. Fix: manual Phase 6 self-review applied; 5-item checklist passed; all Pāḷi terms and citations verified against canon DB. Scope: local.
- [DOC] Evidence: nothing beyond above.

## Improvement suggestions
- Suggest: For thematic runs mapping modern psychological concepts to canonical Pāḷi, a Phase 1 step that pre-maps concept → Pāḷi-term → known sutta would accelerate Phase 2 canon searches significantly. The perspective map (produced in Phase 1 angle triage) already does this partially; making it explicit with canonical stems would reduce Phase 2 breadth searches.
- Suggest: The library NFS permission errors recur across runs. Consider checking or caching available-path status at Phase 0 so Phase 3 can plan around it from the start.

## Channel tuning
- Promote to trusted: none
- Demote to excluded: none
- New probationary channels seen: Patisota (papañca), Hillside Hermitage (Honeyball Sutta), Clear Mountain Monastery Project (MN18 summaries), Anukampa Bhikkhuni Project (MN18) — all returned relevant papañca/MN18 content
