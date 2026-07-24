---
date: 2026-07-24
slug: vassa-split-two-places
question_original: "Vinaya research- can monk determine and spend one vassa in 2 different places - half of the vassa in one place , and second half in another. Do not give solutions of entering the second vassa, do not give solutions of seven day business allowance."
question_polished: "Can a monk legitimately spend one vassa (rains retreat) in two different places — the first half in one location and the second half in another — according to Theravāda Vinaya, setting aside the option of entering a second vassa and the seven-day business allowance?"
run_class: thematic
note: "Vicaya/2026-07-24 - vassa-split-two-places.md"
pdf: skipped
phases_completed: [0, 1, 2, 3, "4a", "4b", "4c", 5, 6, 7]
gates_passed: [0, 1, 2, 3, "4a", "4b", "4c", 5, 6, 7]
agents_used:
  - orchestrator: "Claude Sonnet 4.6 (Claude Code)"
validate_pass: true
sync_status: ok
---

# Run Reflection — vassa-split-two-places

## Summary

Vinaya research on whether a monk can legitimately split one vassa between two residences (half here, half there) — excluding both the second vassa and seven-day allowance options. Research confirmed the answer is **no**, with three overlapping canonical prohibitions established from direct CST database queries and BMC2.

## Key findings

1. **Three canonical rules converge to block the strategy:**
   - **§185** (Mv 3, section 108) — general cārika prohibition: departing on tour mid-vassa before completing three months = dukkaṭa. Applies to every monk regardless of any commitment made.
   - **§207** (Mv 3, section 118, Paṭissavadukkaṭāpatti) — paṭissava rule: a monk who has formally committed to a vassa location and then splits vassa between two places incurs (a) vassa not counted (*purimikā na paññāyati*) and (b) dukkaṭa for broken undertaking. Pāḷi confirmed verbatim from DB.
   - **§364 continuation** (Mv 8, section 223) — ekādhippāya ruling: even if a monk ends up in two residences during vassa, he receives only one combined robe share, not two. Called "moghapurisa."

2. **The Upananda double-narrative:** Two separate incidents involving Ven. Upananda in vin02m2_mul supply the canonical basis — §206 (promise to King Pasenadi, broken by diverting to two robe-rich monasteries) in Mv 3, and §364 (collecting robe shares across multiple residences after vassa + dual-residence vassa for robes) in Mv 8. Both call Upananda "moghapurisa" (foolish man).

3. **BMC2 (Ṭhānissaro):** Explicitly confirms that the only "technical possibility" of entering vassa in two residences arises via the seven-day business allowance — the exact mechanism the user excluded. No other canonical path exists.

4. **Motivating incentive is self-defeating:** The robe-gain motivation for splitting vassa is defeated by the ekādhippāya ruling: one combined share, proportional to time spent, instead of two full shares.

## Process notes

- Run spanned two context windows — context compacted between Phases 3 and 4. The CLAUDE.md scratch-discipline requirement to write findings per phase prevented data loss: all Phase 2 canon hits and BMC2 passages were in the scratch file before compaction. Phase 4 resumed cleanly.
- EBC vault (Brahmali Mv3 and Deepseek Mv8 translations) were read directly and supplied key translation context for the canon DB queries.
- Library volumes offline (`source_available: false` for all library hits) — Calibre external volume not mounted. Did not affect the research since the primary source (BMC2) is available via EBC vault and dhammatalks.org.
- Samantapāsādikā (vin02a2_att) returned 0 hits for all vassa-related queries in the available DB configuration. This gap is noted in the vault note T2 section; no conclusions depend on it.
- Cross-check chain unavailable (SELF_REVIEW sentinel); self-review checklist run manually — no errors found.
- YouTube (Phase 4b) skipped: narrow procedural Vinaya question has no relevant trusted-tier transcript content.
- WisdomLib (Phase 4c) searched: only general definitions found, no rule content.

## Improvement suggestions

- The Samantapāsādikā (vin02a2_att) commentary on the Vassūpanāyika chapter was not retrievable via full-text search. If this commentary has content on the paṭissava rules (which BMC2 references), it would add depth. Worth investigating whether vin02a2_att is fully indexed in the DB or only partially.
- Para 207 (the explicit paṭissava rule) was not found by any of the keyword-based `search-canon` queries in Phase 2 — it was found via direct SQL using the known paranum from the Upananda narrative (§206). A future improvement: after finding a narrative (§206), auto-derive adjacent paragraphs for rule statements (§207 always immediately follows the origin story in Khandhaka format).
