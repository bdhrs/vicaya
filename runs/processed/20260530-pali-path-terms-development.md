# Run Reflection — Pāḷi Meditation and Path Terms Development
**date:** 2026-05-30  
**slug:** pali-path-terms-development  
**question_original:** I need an overview of the Pali terms specially, which are related to the path related to the meditation practice And related to a crucial understanding of the Buddha's teaching. I need the overview of development of those terms between the early suits and the later commentary literature, and how right now in Theravada it's understood. Basically from this research I need just list of those terms which definitely has been developed a lot with a summary of those development.  
**question_polished:** Which Pāḷi terms central to meditation practice and the Buddhist path underwent the most significant semantic and conceptual development between the early Nikāya suttas, the commentarial tradition (Visuddhimagga and aṭṭhakathā), and modern Theravāda understanding?

## Output
- Vault note: `Vicaya/2026-05-30 - pali-path-terms-development.md`
- PDF: `~/Documents/Vicaya-PDFs/2026-05-30 - pali-path-terms-development.pdf`

## Scope
Thematic overview (not anchored to a single sutta) — 11 Pāḷi meditation/path terms ordered by degree of development from early suttas through commentaries to modern Theravāda.

## Terms Covered (by degree of change)
1. **Upacāra/Appanā-samādhi** — Invented; absent from four Nikāyas entirely
2. **Nimitta** (meditation sign) — Major respecification; sutta word repurposed into 3-sign technical system
3. **Vipassanā-ñāṇa stages** — Major elaboration; 16-fold ladder is commentarial/late-canonical
4. **Jhāna** — Significant narrowing; nimitta requirement, parikamma/upacāra/appanā stages added, jhāna/vipassanā separated
5. **Vitakka/Vicāra** — Respecified from thinking to non-verbal "applied attention" (Abhidhamma momentariness driven)
6. **Samatha/Vipassanā as two paths** — Bifurcated into samathayānika/vipassanāyānika; sutta pairs them
7. **Sati** — Contested; memory root vs. present-moment awareness (modern Western goes furthest)
8. **Paṭiccasamuppāda** — Three-lifetime model is Abhidhamma/Visuddhimagga; synchronic reading contested
9. **Nibbāna** — Reified as real unconditioned dhamma in commentaries; ontological debate continues
10. **Kammaṭṭhāna** — Term invented by Buddhaghosa; content sutta-based but umbrella term is commentarial
11. **Sukkhavipassaka/Khaṇika-samādhi** — Both concepts post-canonical; foundation of Mahāsī tradition

## Sources Covered
- **T1 Canon**: DN2 para 226, DN1 para 96, AN2.22-32 para 32, AN4.92 para 92, MN6 para 65, KN17 §12 (Paṭisambhidāmagga)
- **T2 Commentary**: Visuddhimagga §57 (paṭibhāga-nimitta), §39 (upacāra/appanā definitions), XXII §107 (vipassanā-jhāna)
- **T3 Library (Calibre)**: Arbel #1336, Polak #3361, Sujato #905, Sujato #3363, Anālayo #385, Gunaratana #3172, PTS Dictionary #2162, Vimuttimagga #206, Wen #972
- **T3 Web**: Wikipedia (Dhyana in Buddhism), WisdomLib (sati, jhāna, nimitta, vitakka, vipassanā, samatha), Sujato's blog
- **T4 Talks**: Doug's Dharma YouTube (sati/memory, auto-captions, paraphrased)

## Errors and Fixes
- Phase 2.5 gate missing → logged skip reason (thematic overview, not sutta-anchored; SC parallels not applicable), then gated
- Phase 3b gate missing → logged skip reason (GRETIL path not configured; Sanskrit noted via Calibre), then gated  
- inline `python -c "..."` blocked by CLAUDE.md hook → used `grep -E` and `head` for output trimming instead
- Context compaction mid-run → resumed from scratch file with `scratch-resume`; no data lost
- **Cross-check factual error corrected**: "vipassanā-jhānas coined by U Paṇḍita" was incorrect — term appears in *Visuddhimagga* XXII §107 and *Paramatthamañjūsā*; U Paṇḍita popularized but did not coin it. Vault note corrected.

## What Worked Well
- `scratch-resume` after compaction correctly identified last gate (4c) and next phase (5)
- Calibre FTS active; returned quality snippets from Arbel, Polak, Anālayo
- Canon search returned the key Yuganaddha passage (AN4.170) confirming samatha/vipassanā "in tandem" — strong T1 evidence
- Cross-check (DeepSeek v4-flash) surfaced the Visuddhimagga vipassanā-jhāna attribution error and correctly confirmed Susīma Sutta, Levman, and vuṭṭhāya references
- Thematic structure (terms ordered by degree of change) works well as a reference map for follow-up research

## What Could Be Improved
- `gen_pdf_run.py` ignores TODAY and SLUG env vars — hardcodes them. Fixed this run; should be made permanent upstream.
- Balance: EBT-critical perspective dominates; traditional position (Bhikkhu Bodhi, Pa-Auk) is noted in Critical Gaps but not deeply evidenced — flagged for follow-up
- SC Parallels skip for thematic runs: there should be a more streamlined way to flag this class of run as "non-sutta-anchored" so Phase 2.5 skip is automatic rather than manual
