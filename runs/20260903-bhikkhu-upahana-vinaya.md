---
date: 2026-09-03
question_original: "I need a strictly mula Vinaya perspective on the Bhikkhu wearing shoes, outside of the middle Ganges with various occasions: inside the monastery vs in the inhabited area vs while going to Piṇḍacāra."
question_polished: "What does the mūla Vinaya prescribe regarding bhikkhus wearing shoes (upāhanā/pādukā) in the border territories (paccantimā janapadā) outside the middle Ganges region, distinguishing the three contexts of: inside the monastery, in the inhabited area, and while going on piṇḍacāra?"
note_path: "Vicaya/2026-09-03 - bhikkhu-upahana-vinaya.md"
duration_min: 195
---

## Retrospective

- [POSITIVE] Evidence: The central finding — that guṇaṅguṇūpāhana (§259) modifies sandal TYPE, not sandal LOCATION — is unambiguous from the Pāḷi grammar. The three-context structure (monastery/village/piṇḍacāra) emerged cleanly from the canon with a dedicated passage for each (§248, §256-cont., §368). Cause: clear scope (mūla only, three named contexts) allowed focused targeted search. Fix: preserve this scope-first approach for Vinaya questions. Scope: local.

- [BUG] Evidence: Phase 2 sub-agent missed the guṇaṅguṇūpāhana allowance entirely, reporting "no explicit footwear exemption for paccantimā janapadā found." The passage (§258-259) is the central borderland allowance and is unambiguous. Cause: sub-agent searched vin02m2_mul with "upāhana paccantima" but the borderland passage uses "guṇaṅguṇūpāhana" — a compound term distinct from bare "upāhana" and from "paccantima". Fix: for Vinaya borderland questions, always include the technical compound term variants as search terms, not just the two component words separately. Scope: global — whenever a Vinaya allowance is known to have a technical name, add that name as a parallel search query.

- [WORKFLOW] Evidence: Phase 4c sub-agent correctly deferred gating because Phase 2 was not yet gated when it finished. Backfilling gates in ascending order (3, 4, 4b, 4c) after all agents completed worked without error. Cause: by-design gate ordering validation. Fix: none — behavior is correct. Scope: local.

- [BUG] Evidence: The SQL UNION ALL ... ORDER BY syntax error occurred when ORDER BY was placed inside a subquery. Fixed by removing ORDER BY from subqueries and sorting in Python. Cause: SQLite does not allow ORDER BY in a UNION subquery. Fix: never place ORDER BY inside a UNION ALL subquery; sort in the outermost query or in post-processing. Scope: global.

- [BUG] Evidence: cross-check timed out (opencode:deepseek/deepseek-v4-pro, 300s). Self-review substituted. Cause: likely server-side slowness; no code error. Fix: retry once on same chain entry before accepting self-review; consider adding a faster fallback model to the chain. Scope: global.

- [TEXTUAL NOTE] Evidence: Tension between §248 (monastery prohibition, ajjhārāme) and §368 (forest monk wearing sandals in senāsana before descending) is real and unresolved in the mūla. This is correctly flagged as a critical gap requiring T2 commentary. Cause: the mūla records rules and procedures without always harmonizing them explicitly. Fix: always check whether a procedural passage (Vattakkhandhaka) aligns or conflicts with a rule passage (Cammakkhandhaka) when both address the same behavior. Scope: local.

- [POSITIVE] Evidence: Per-phase scratch logging per CLAUDE.md discipline was followed — context compaction during a long two-session run did not lose any findings. Cause: Phase 2-4c findings logged to scratch at each gate boundary before moving on. Fix: preserve; this is the correct behavior. Scope: global.

## Improvement suggestions

- Suggest: For Vinaya compound-allowance terms (guṇaṅguṇūpāhana, guṇaṅguṇū, etc.), add to the sub-agent prompt a note that the allowance may use a single technical compound term rather than both component words separately — otherwise the sub-agent searches the component words and misses the compound.
- Suggest: cross-check chain fallback: add a faster model (glm-5.3:off or similar) as a second chain entry so that if the first entry times out, the review still completes in the same session without falling back to self-review.

## Channel tuning

- Promote to trusted: none
- Demote to excluded: none
- New probationary channels seen: none (Vinaya primary source run — no web/YouTube channels engaged)
