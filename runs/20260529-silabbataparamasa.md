# Run Reflection — sīlabbataparāmāsa interpretations
**date:** 2026-05-29  
**slug:** silabbataparamasa-interpretations  
**question_original:** what are the various canonical and not only interpritation of sīlabbataparāmāsa  
**question_polished:** What are the various canonical, commentarial, and modern interpretations of *sīlabbataparāmāsa* (the fetter of adherence to rites and observances)?

## Output
- Vault note: `Vicaya/2026-05-29 - silabbataparamasa-interpretations.md`
- PDF: `~/Documents/Vicaya-PDFs/2026-05-29 - silabbataparamasa-interpretations.pdf`

## Sources Covered
- **T1 Canon**: MN2 §21, MN11 §143-144, MN57 §80, MN64 §130-131, SN45.175, SN45.180, AN6.89, Dhammasangani §1009/1122/1222/1124, Vibhaṅga §938
- **T2 Commentary**: Visuddhimagga XVII, Paṭisambhidāmagga, Nettippakaraṇa §32, aṭṭhakathā on MN57 and Dhammasangani
- **T3 Library (Calibre)**: Mahasi #637, Kariyawasam #1781, Story #2943, Dhammika #920, Bodhi #1558, Della Santina #1621, Nyanatiloka #2261, Chah #230, Analayo #371
- **T3 Web**: SuttaCentral forum, WisdomLib, Punnaji glossology
- **T4 Talks**: Ajahn Pasanno (YouTube auto-captions, paraphrased)

## Key Interpretive Positions Found
1. **Narrow canonical** (Abhidhamma): restricted to ascetics outside the dispensation (ito bahiddhā)
2. **Broad wrong-view** (Mahasi, Story): extends to Buddhist practice without insight
3. **Nettippakaraṇa causal analysis**: rooted in taṇhā (craving), not avijjā
4. **Visuddhimagga sequential**: self-view (attavādupādāna) → ritual self-purification (sīlabbatupādāna)
5. **Punnaji reinterpretation**: parāmāsa = "alienation" (external imposition), not clinging

## Central Tension Resolved
Abhidhamma's "ito bahiddhā" restriction vs. modern pastoral extension: not incompatible — canonical restriction preserves doctrinal precision (Buddhist sīla oriented to NEP cannot be this fetter by definition); modern teachers address attitude, not structure.

## Errors and Fixes
- `scratch-gate 2` failed on missing Phase 0 gate — fixed by running gates 0 → 1 → 2 in sequence
- `scratch-gate 3` failed on missing Phase 2.5 gate — fixed by running `sc-parallels` for mn57/mn11/mn2 (all empty), then `scratch-gate 2.5`
- `scratch-gate 6` failed on missing Phase 5 gate — fixed by running `scratch-gate 5` first
- CLAUDE.md hook blocked inline `python -c "..."` — fixed by writing scripts to `temp/`
- WebFetch failures: DhammaWheel (403), AngelFire (ECONNREFUSED), dhammatalks.org/MN57 (404) — worked around with other sources
- Large commentary JSON from `search-canon` on `s*_att` — filtered with `temp/filter_silabbata_att.py`
- Cross-check correctly flagged Nettippakaraṇa as T2 (not mūla sutta) — integrated silently

## What Worked Well
- `search-canon` on Abhidhamma books (`s*_abh`) returned precise Dhammasangani and Vibhaṅga definitions
- Calibre FTS active; snippet mode returned useful excerpts from Mahasi and Bodhi
- Cross-check (DeepSeek v4-flash) surfaced the Nettippakaraṇa causal distinction that the initial synthesis underemphasised

## What Could Be Improved
- Gate check should emit the missing gate name more prominently — it says "Phase 2.5 gate missing" but easy to miss in JSON output
- sc-parallels returning empty for core MN suttas (mn57/mn11/mn2) suggests offline SC archive lacks parallel data for these; document this as a known gap in skill notes
