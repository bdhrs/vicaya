# Run: what-suttas-say-comparative
**Date:** 2026-08-24
**Slug:** what-suttas-say-comparative
**Class:** thematic (meta-audit of the Vicaya corpus)
**Question:** Which ideas identified as canonical across the Vicaya corpus lack support in comparative Āgama studies, and may therefore represent later Theravāda Pāli sutta developments rather than pan-Buddhist early teaching?
**Vault note:** `Vicaya/2026-08-24 - what-suttas-say-comparative.md`

## Summary of findings

Corpus-audit across ~256 notes (47 "What the suttas say" + 219 dated + subfolders), triaged into class A (Pāli-specific risk, ≈80), B (pan-Buddhist stable, ≈74), C (non-doctrinal, ≈14).

Three-tier answer:

1. **Five sutta mūla discourses with no Āgama parallel** (verified via EBC `parallels_agama=[]` + SuttaCentral live API `{}` + offline `sc-parallels`): MN 111 *Anupada*, MN 48 *Kosambiya*, SN 48.40 *Uppaṭipāṭika*, AN 10.48 *Pabbajitaabhiṇha* (Netti-only echo), AN 4.184 *Abhaya*.
2. **Recensional divergences within paralleled suttas**: MN 44 *cittassa ekaggatā* gloss, *nāma* 5-factor vs SĀ 4-aggregate, *upādāna* link, AN 4.170 *dhammuddhacca* fourth mode absent from SĀ 560.
3. **Abhidhamma/commentarial stratum** (T1b/T2): *bhavaṅga*, *khaṇavāda*, two-truths, 40-*kammaṭṭhāna*, *vipassanā-ñāṇa* ladder, six-*carita*.

Negative control: core doctrines survive cross-recension (anattā SĀ 34, four truths SĀ 379/MĀ 31, DO, embodied jhāna MĀ 2, ānāpānasati SĀ 803, satipaṭṭhāna MĀ 98/EĀ 12.1, bojjhaṅgā EĀ 12.1).

## Phases completed
- Phase 0–1: corpus mining via catalog-by-topics + 8 parallel sub-agents (168 doctrinal notes); claim ledger built
- Phase 2: parallel verification (get-ebc-overview + sc-parallels) — confirmed/refuted candidate suttas
- Phase 3: library — Anālayo *Comparative Study of the MN*, Anālayo Anupada article, Bucknell
- Phase 4: web — SuttaCentral live parallels API corroboration (mn10 sanity-checked)
- Phase 4b/4c: skipped (text-critical question; no load-bearing talk/encyclopedia value)
- Phase 5: synthesis; Phase 6: SELF_REVIEW (chain subprocess unavailable); Phase 7: note written, validated, PDF, gates, synced

## Improvement suggestions

- `cross-check` returned `# SELF_REVIEW` because the `opencode run -m` subprocess timed out inside the sandbox — worth a shorter default or a non-interactive fallback flag on macOS
- The EBC `get-ebc-overview` covers MN/DN/SN/AN but `parallels_agama` is only as complete as the curated EBC cards; a direct CBETA/Taishō parallel table would let future audits distinguish "no parallel" from "parallel not yet catalogued"
- The corpus catalog (`catalog-by-topics.md`) predates several recent notes (e.g. what-was-the-buddhas-name); a periodic catalog rebuild would make corpus audits complete without a separate glob pass
