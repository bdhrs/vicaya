---
date: 2026-09-12
question_original: Study all suttas on nibbiddā virāga nirodha - what are all the things that lead to there - place in the path of enlightenement - full resaerch on this topic from every angle.
question_polished: "What do the suttas teach about nibbidā (disenchantment), virāga (dispassion), and nirodha (cessation): what objects do they take, what practices lead to them, and what is their place in the path to liberation?"
note_path: Vicaya/2026-05-24 - nibbida-viraga-nirodha-disenchantment-dispassion-cessation.md
duration_min: 150
---

## Retrospective
- [POSITIVE] Evidence: enrichment-mode detection (existing 2026-05-24 triad note + 2026-06-14 stream-entry note found in Phase 1) routed to in-place expansion; the old note's Critical Gaps table became the work plan and 4 of 5 gaps closed. Cause: vault search before scratch-init. Fix: none — preserve. Scope: global.
- [POSITIVE] Evidence: the complete ekantanibbidāya inventory (AN1.296, AN5.69, MN83, DN29, MN122, AN10.107/108, AN6.30, SN55.12, DN21) came from two stem searches plus resolve-citation on every paranum — no invented refs; all 17 verify-citation spot-checks passed first try. Cause: stem-truncation + resolve-before-naming discipline. Fix: none — preserve. Scope: global.
- [POSITIVE] Evidence: source-armed second reviewer caught 4 real errors the external reviewer missed or mis-shared (AN5.69 splice, DN19/DN21 duplication, SNa12.16/12.23 misaddress, Parivāra attribution) — every one verified real against the DB. Cause: read-only checker with helper access beats probabilistic reasoning. Fix: keep the two-reviewer shape. Scope: global.
- [BUG] Evidence: F1 — my AN5.69 blockquote spliced para 69's outcome onto para 70's list and exhibited it as verbatim. Cause: id-window pulls return continuation rows without paranums; I assembled adjacent rows into one quote. Fix: exhibit one paranum per blockquote; when a list lives under a twin sutta, quote both separately and label the join. Scope: global.
- [BUG] Evidence: F2 — DN19 blockquote showed DN21 text (both verified from the same devāsura-joy memory of the prior note, never re-resolved). Cause: trusted the prior note's exhibit instead of re-resolving. Fix: re-verify every citation carried over from a prior note (skill already says this; this run is the case study). Scope: global.
- [CONFUSION] Evidence: continuation-row addressing (quotes living under unnumbered rows) confused both reviewers and my own SQL LIKE queries (paranum-qualified LIKE silently returns nothing). Cause: CST stores body in paranum='' rows. Fix: id-window pulls by default for context; added a CST-addressing note to the vault note's T1 header. Scope: global.
- [WORKFLOW] Evidence: `search-library-folders "Path of Freedom"` timed out twice (stopword scan) while narrower "Upatissa Vimuttimagga Nanda" worked instantly. Cause: broad-phrase full-index scan. Fix: descend the search ladder (author/title token first) before retrying. Scope: local.
- [BEHAVIOR] Evidence: cross-check review file (91KB prompt) returned a substantive review via pi chain on first attempt (no SELF_REVIEW fallback). Cause: preflight probe + 300s timeout + background run. Fix: none — preserve. Scope: local.

## Improvement suggestions
- Suggest: consider a blockquote verifier that checks every Pāḷi blockquote in a phase5 draft against the canon DB before Phase 6 (would have caught F1/F2 mechanically).
- Suggest: document the continuation-row addressing convention (paranum='' body rows; search-canon backfills nearest paranum) in SKILL.md Phase 2, since it confused two reviewers and broke paranum-qualified SQL LIKE twice this run.

## Channel tuning
- Promote to trusted: none
- Demote to excluded: none
- New probationary channels seen: 1983dukkha (Ajahn Brahm excerpt), TheMindingCentre (Piya Tan 2-part) — left probationary (auto-captions/duplicative, not cited)
