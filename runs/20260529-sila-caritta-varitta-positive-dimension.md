# Run Reflection — 2026-05-29 — sila-caritta-varitta-positive-dimension

**Question original:** Sīla - How canonical is supported to interpret this as a virtue - Not only in the aspect of abstaining from unwholesome - But also the aspect of the positive doing wholesome

**Question polished:** How canonically supported is it to interpret sīla as encompassing both the negative dimension of abstaining from unwholesome actions (vāritta) and the positive dimension of actively performing wholesome ones (cāritta)?

**Vault note:** `2026-05-29 - sila-caritta-varitta-positive-dimension.md`

---

## Summary

The dual-dimension interpretation of sīla (cāritta + vāritta) is strongly supported at every evidence tier. The research found six independent canonical lines of evidence, confirming this is not a commentarial imposition but a structural feature of the mūla texts themselves.

## Files Changed

- **Created:** `/Vicaya/2026-05-29 - sila-caritta-varitta-positive-dimension.md`
- **Scratch:** `data/scratch/sila-virtue-positive-negative.md` (all phases gated 0–7)

## Key Findings

### T1 Canon — Six converging lines

1. **Ovādapātimokkha (DN14 §90, DHP183):** *kusalassa upasampadā* as second limb = active undertaking of wholesome. Nettippakarana §31 glosses this as "action, doing, accomplishment" of the eight rightnesses.
2. **DN2 §194 sīla formula:** positive qualities *lajjī, dayāpanno, sabbapāṇabhūtahitānukampī viharati* named inside the sīla section — not a separate category.
3. **AN8.39 §39 (Abhisandasuttaṃ):** sīla framed as *deti* (actively giving) fearlessness to all beings — structurally positive.
4. **TH239 §591 (Theragāthā):** *cārittaṃ atha vārittaṃ* pairing in a gāthā — both named as "befitting for a recluse." Canonical use of the cāritta/vāritta pair, pre-dating the Visuddhimagga.
5. **DN34 §360 kusalakammapathā:** last three items (anabhijjhā, abyāpādo, sammādiṭṭhi) are positive mental qualities, not abstentions; the whole set is *visesabhāgiyā*.
6. **KN17 §39 (Paṭisambhidāmagga):** primary definition of sīla = *cetanā* (volition) and *cetasika* — inherently active/intentional.

### T2 Commentary — Formalizes the mūla

- **Visuddhimagga §11:** explicit cāritta/vāritta terminology: "This should be done" vs. "This should not be done"
- **Dhammapāla's Cariyapitaka commentary:** "Virtue is twofold as avoidance (vāritta) and performance (cāritta)"
- **Nettippakarana §31:** *kusalassa upasampadā* = action and accomplishment of rightnesses (note: para-canonical status in Burmese vs. Sri Lankan tradition)

### T3 Academic/Modern

- **Bhikkhu Bodhi:** explicit statement of dual aspect; cāritta = "positive performance"
- **Y. Karunadasa:** alobha/adosa/amoha encode generosity, loving-kindness, wisdom despite negative form
- **George D. Bond:** Theravāda ethics of virtue; kusalakammapathā as the positive sīla formulation (adibrahmacariyaka-sīla)

## Issues and Errors

- **Context compaction mid-run:** Phase 2 was partially complete when compaction fired. Recovery was successful via `scratch-resume` guidance. DN34 kusalakammapatha citation was pending and was resolved in the resumed session.
- **SC offline archive not available:** SC_DATA_PATH not configured; sc-parallels and sc-search returned empty. Compensated with EBC vault parallels.
- **Sanskrit corpus not configured:** VICAYA_GRETIL_PATH not set; Phase 3b skipped.
- **DHP183 and Thag 591 "[REJECTED — not in sutta_info]"** in cross-check output: these are database lookup gaps, not actual rejections. The cross-check explicitly confirmed both citations as authentic canonical texts.
- **Cross-check hallucination:** Suggested "Theragāthā v. 637 (Bākula)" as additional cāritta/vāritta evidence — verified against canon DB and not found. Only one such verse exists (TH239 §591). Rejected.
- **Nettippakarana canonical status:** originally labeled T1; cross-check correctly noted it is para-canonical (accepted in Burmese but not Sri Lankan canon). Label adjusted to "para-canonical" in vault note.

## Test Evidence

- All 10 phases gated (scratch-verify exit 0 before Phase 5)
- Cross-check verified all major T1 claims; found no misattributions in T1 evidence
- Vault note committed and pushed to `bdhrs/vicaya-notes` (commit `64db2ad`)
