---
date: 2026-09-05
question_original: "In the Vinaya mūla (especially the Khandhakas and Nissaggiya Pācittiya rules), and then in the commentaries (Samantapāsādikā, sub-commentaries), are there any examples or rulings showing that a bhikkhu may borrow or temporarily use light items (lahuparikkhārā or similar) that belong to the Sangha — without the item first having to be formally distributed to him by an appointed distributor (bhājanaka, vissajjaka, appamattakavissajjaka, or similar officer)?"
question_polished: "Does the Vinaya mūla or the commentaries (Samantapāsādikā) permit a bhikkhu to borrow or temporarily use light items (lahuparikkhārā) belonging to the Sangha without first receiving them through formal distribution by an appointed distributor?"
note_path: "Vicaya/2026-09-05 - sangha-light-item-borrow.md"
scratch_path: "data/scratch/2026-09-05-sangha-light-item-borrow.md"
duration_min: 180
---

## Retrospective

### What went well

- **Correction of previous session's error**: The prior vicaya-quick run conflated garubhaṇḍa and lahubhaṇḍa. The user correctly identified the error, and this run explicitly corrected it with canonical evidence.

- **Tāvakālikaggāha pathway clearly established**: vin01m_mul §125–127 (six-condition offense structure for all three tiers), §131 (anāpatti verse with tāvakālika), and §156 (Vinītavatthu case of a monk using sangha wood temporarily for his own dwelling — no offense) together form a clean canonical argument. §156 is the key case: undistributed sangha property, used without distribution, no theyyacitta, no offense.

- **Vissāsaggāha limitation confirmed**: §146 shows vissāsa operated on already-distributed goods held individually by the companion monk, not on undistributed sangha stock. This closes the vissāsa pathway cleanly.

- **Commentary evidence solid**: vin02a3_att §321 (bhājanīya list: needle, ear cleaner, key, small knife) and §324 (gīvā liability for puggalikaparibhogena vs. no liability for saṅghikaparibhogena) are high-quality commentary evidence.

- **BMC2 informal distribution argument**: The Vibhaṅga to BU-PC13 citation in BMC2 ch.18 provides the strongest canonical basis for informal distribution without appointed officers.

- **Case studies answered from first principles**: Both case studies (poor-Vinaya monastery; visiting monks' obligations) answered from the canonical evidence without speculative extrapolation.

### What was hard

- **Obsidian CLI update banner (issue #68 recurrence)**: Obsidian updated to 1.13.7, and the banner output broke search-vault. Fallback to rg worked; vault write via sync_notes.py was unaffected. The banner persisted through an app relaunch (the update was loading, not yet applied). Fix required: update and fully restart Obsidian, not just relaunch.

- **Promoted vicaya-quick run — phase gate mismatch**: All evidence was logged under Phase 1 (vicaya-quick convention). Promoting to a full vicaya run required manually logging summary entries under Phases 2–4c before the gate system would pass. The promoted-run guidance in the SKILL references scratch-verify's "backfill" but this only works when evidence exists under the correct phase sections — it does not move Phase 1 entries. The workaround (VICAYA_PHASE=2 scratch-log 2 canon "summary...") is functional but requires documentation.

- **Context compaction across multiple sessions**: This run spanned three sessions. The CLAUDE.md scratch-file discipline rule prevented evidence loss, but the gate state was not advanced between sessions, requiring reconstruction of which phases had been completed.

### Improvement suggestions for `/vicaya-improve`

- **[DOC]** Promoted vicaya-quick runs: scratch-verify's "backfill" does NOT move Phase 1 evidence into Phase 2–4c sections. The correct procedure is: use `VICAYA_PHASE=N scratch-log N <tool> '<summary of Phase 1 evidence for this phase>'` to create minimal entries in each required phase, then gate. Document this explicitly in the vicaya-quick Promotion section and in SKILL.md's Phase 5 entry.

- **[BUG / KNOWN #68]** Obsidian update banner: app relaunch does not immediately clear the banner while an update is being loaded. The banner clears only after the update completes and the app fully restarts. The workaround (fall back to rg for vault searches; use sync_notes.py directly for writes) is reliable. Suggest adding an explicit note in SKILL.md: "If relaunch does not clear the banner, wait 30 seconds for the update to finish installing, then relaunch again."

- **[DOC]** The canonical case for tāvakālikaggāha on sangha property (vin01m_mul §156) is the clearest answer to "can sangha goods be used without distribution?" — it belongs as a T1 anchor example in the SKILL's property-law investigation checklist.
