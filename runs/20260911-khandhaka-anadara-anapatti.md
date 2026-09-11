---
date: 2026-09-11
question_original: "Which, if any, offenses in the Khandhakas (Mv and Cv) are only incurred when broken out of disrespect and also carry the general non-offenses that are found in the Vibhanga of the Sekhiyas (such as not knowing, gilana, unintentional, etc.)? Please check in 4 layers: Early Canonical Vinaya; the entire Canonical Vinaya (including Parivara); Canonical Vinaya including Commentaries and Sub-Commentaries; All of the above plus any other sources available."
question_polished: "Do any offenses in the Khandhakas (Mahāvagga and Cullavagga) share the double condition found in the Sekhiya rules: (1) incurred only when the act is performed out of disrespect (anādara), and (2) governed by the same general non-offense clauses found in the Sekhiya Vibhaṅga?"
note_path: /Users/resident/vicaya/vault/Vicaya/2026-09-11 - khandhaka-anadara-anapatti.md
duration_min: 120
---

## Retrospective

- [POSITIVE] Evidence: direct SQL against vin02m2_mul and vin02m3_mul immediately confirmed the two Khandhaka anādara rules (Mv para 240, Cv para 371) and established absence of ādikammiko/ummattako in Khandhaka mūla. Cause: the canon DB is the authoritative primary source; SQL is faster than helper searches for targeted term searches. Fix: in future Vinaya structural questions, front-load direct SQL to establish the hard facts before delegating gather phases. Scope: global.

- [ERROR-CATCH] Evidence: Phase 4a web-search sub-agent incorrectly attributed dozens of "anādariyaṃ paṭicca ... dukkaṭa" entries to the "Vatta Khandhaka (Cv.8)" — these were actually the Parivāra's Sekhiyakaṇḍa (para 150+), analyzing Sekhiya rules, not Khandhaka rules. The error was caught during orchestrator spot-check via direct SQL on vin02m4_mul showing the Sekhiyakaṇḍa subhead before para 150. Cause: the web agent was working from secondary sources (web descriptions of the Parivāra) that apparently mislabeled or merged the Parivāra sections. Fix: after every gather phase involving Parivāra or multi-section texts, run a direct SQL spot-check on the specific structural claim before integrating. Scope: global.

- [SCOPE-EXPANSION] Evidence: user mid-run expanded scope to (1) implicit cases and (2) practical monastic context. Both were integrated into the synthesis successfully. Cause: user added new analytical frames after seeing initial Phase 1 results. Fix: the pre-check prompting users to name all four layers was good; adding a prompt for implicit/explicit and practical-context angles at the outset would reduce mid-run pivots. Scope: local.

- [STRUCTURAL-FINDING] Evidence: both confirmed Khandhaka anādara rules (Mv 240, Cv 371) use warning-then-offense structure, making the Sekhiya anāpatti conditions (unknowing, unintentional) structurally redundant for them — the mechanics already require knowing persistence. This analysis is not present in any source layer; it emerged from comparing the rule structures. Fix: include structural compatibility analysis (would the conditions even apply if they were stated?) as a standard implicit-dimension check for Vinaya legislative questions. Scope: global.

- [CROSS-CHECK-FAILURE] Evidence: cross-check chain failed (opencode run syntax changed — "opencode run [message]" no longer accepts positional args in this form). Self-review applied instead. Fix: test the cross-check chain with `cross-check --preflight --timeout 60` before the gather phases, not only at Phase 6. Scope: global.

- [LIMITATION] Evidence: Vinaya Mukha (Vajiranāṇavarorasa) was not located in the library index; its handling of these specific rules is unknown. Cause: search too broad for FTS. Fix: try a title-specific library search for "Vinaya Mukha" first, then fallback to a web fetch of a reliable Vinaya Mukha source. Scope: local.

- [PHASE-GATE] Evidence: Phase 4c was blocked on 4b completion — the orchestrator gated 4c manually only after 4b completed. This caused a brief hold. Cause: sequential gating within sub-phases requires completion in order. Fix: when dispatching 4a/4b/4c in parallel, note in each agent prompt which phases must complete before they can gate, so agents know to log their findings and report even if they cannot gate. Scope: global.

## Improvement suggestions

- Suggest: add a "structural compatibility check" to the Vinaya implicit-dimension protocol: for each rule that uses an anādara condition, check whether the warning-then-offense structure makes the Sekhiya anāpatti clauses (unknowing, unintentional) structurally applicable or redundant — this turns absence of explicit clauses into a more nuanced finding.

- Suggest: add a check step before Phase 6: run `cross-check --preflight --timeout 60` at the end of Phase 5 (before synthesis is finalized) so a broken chain is discovered while corrections can still be integrated.

- Suggest: for questions involving the Parivāra, add a sub-step explicitly confirming which Parivāra section any anādariyaṃ paṭicca entries belong to (Pācittiya / Sekhiyakaṇḍa / Khandhakavatthu) before recording them as findings — the Parivāra's structure is not obvious from secondary descriptions.

## Channel tuning

- Promote to trusted: none
- Demote to excluded: none
