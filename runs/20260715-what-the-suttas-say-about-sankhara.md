---
date: 2026-07-15
question_original: "Research and compile what the Early Buddhist Texts (EBTs) say about Saṅkhārā. Fixed series format: What the suttas say about saṅkhārā — two sections, one quote per idea, surface contradictions, earliest strata only in Section 1."
question_polished: "What do the Early Buddhist Texts say about saṅkhārā?"
note_path: Vicaya/What the Suttas Say About/2026-07-15 - what-the-suttas-say-about-sankhara.md
duration_min: 55
---

## Retrospective
- [POSITIVE] Evidence: The existing [[2026-05-27 - sankhara-khandha-cetana]] note + the [[2026-07-14 - what-the-suttas-say-about-avijja]] sibling provided an exact format model and a ready cross-reference for the predecessor DO link, so the new note slotted cleanly into the series. Cause: strong prior vault coverage of the DO/khandha cluster. Fix: preserve — the series is now densely cross-linked. Scope: local.
- [POSITIVE] Evidence: GRETIL Udānavarga parallels landed immediately (saṃskāra-upaśamam sukham ≈ Iti 43; bhava-saṃskāram avāsṛjan muniḥ ≈ DN16 āyusaṅkhāra), giving cross-recension confirmation with one search. Cause: the Sanskrit phase is high-value-low-cost for EBT doctrinal terms. Fix: keep Phase 3b default-on for sutta-anchored doctrinal questions. Scope: global.
- [WORKFLOW] Evidence: Phase 5 and Phase 6 gates were initially refused because I drafted straight to the vault without first gating Phase 5 (synthesis) — had to backfill scratch-log 5 then gate. Cause: the skill puts the draft in scratch then gates 5, but I wrote to the vault first. Fix: none needed — backfill worked, but note that scratch-gate 5 must be written before scratch-gate 6 regardless of where the draft lives. Scope: local.
- [BEHAVIOR] Evidence: I initially cited a Yoga-Sūtra 4.28 verse from training memory in Section 2 entry 4; the self-review (SELF_REVIEW fallback) caught it as unverifiable, and GRETIL did not surface it. Cause: citing a non-Buddhist comparative verse from memory rather than from a verified source. Fix: applied — replaced with GRETIL-attested vāsanākṣaya vocabulary. Lesson: never cite a specific verse number from memory; verify against GRETIL or soften to tradition-level attribution. Scope: global.
- [BUG] Evidence: The cross-check helper returned the SELF_REVIEW sentinel (opencode/deepseek-v4-pro unavailable) after ~165s of background wait. Cause: the cross-check chain entry failed (opencode not authenticated or model unavailable). Fix: none during the run — self-review fallback worked as designed; user may want to check opencode auth for future runs. Scope: local.
- [DOC] Evidence: The skill's dispatch model assumes Claude-Code-style sub-agents; in pi the available agents (planner/reviewer/scout/worker) are generic with no vicaya context, so I ran all gather phases inline. Cause: harness mismatch. Fix: ran inline per the skill's explicit "run that one phase inline" allowance; for pi, an inline-by-default orchestrator is the pragmatic path. Scope: local.

## Improvement suggestions
- Suggest: Document that scratch-gate 5 (synthesis) must be written before scratch-gate 6 even when the draft is written directly to the vault rather than to the scratch — a one-line note in the Phase 5/6 transition would prevent the backfill loop.
- Suggest: Add a short "citation from memory" guardrail to the Hard Rules or Phase 5 Devil's Advocate: any non-canon verse or page reference not verified via a helper (GRETIL/search-canon/verify-citation) during the run must be softened to tradition-level attribution before the note is written.
- Suggest: Note in the cross-check section that on pi the opencode/agy chain may be unavailable; the SELF_REVIEW fallback is already well-specified, but a one-line "this is expected on some hosts" would reduce uncertainty.

## Channel tuning
- Promote to trusted: none
- Demote to excluded: none
- New probationary channels seen: Sutta Workshops by Āyasmā (sankhara content), Dhamma Talks at Dhammagiri (sankhara content) — both appeared as probationary; not promoted (no transcript pulled, textual question)
