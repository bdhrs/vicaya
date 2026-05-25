# Plan — Clean the Question

## Architecture Decisions
- SKILL.md: add question sanitization right after the existing "Topic / question" input description in `## Inputs`. No new section needed — one short paragraph.
- Vault notes: edit each file in-place with the Edit tool. Batch sequentially through all 41 notes.
- PDF re-export: write a batch script using the same weasyprint code from SKILL.md; run it once for all 41 notes.

---

## Phase 1 — Update SKILL.md

- [ ] Add question-sanitization instruction to the `## Inputs` section of `skill/vicaya/SKILL.md`, directly under the existing topic/question bullet.
  → verify: read lines 27–35 of SKILL.md and confirm the sanitization rule is present

---

## Phase 2 — Reword vault note topics

For each note, only the `topic:` or `title:` frontmatter value changes.

**Current → New (light touch):**

1. `apannaka-safe-bet-rebirth-wager.md`
   - current: `"Apaṇṇakasutta: the Buddha's safe-bet argument for rebirth and moral causality"`
   - new: `"What is the Buddha's safe-bet argument in the Apaṇṇakasutta, and how does it apply to rebirth and moral causality?"`

2. `arahant-must-experience-all-kamma.md`
   - current: `"Does an arahant have to experience all accumulated kamma before death?"` ✓ keep

3. `bhante-vimalaramsi-twim-deep-dive.md`
   - current: `"Bhante Vimalaraṃsi and TWIM: A Comprehensive Deep Dive into Sutta Alignment, Popular Appeal, and Critical Rebuttals"`
   - new: `"How does Bhante Vimalaraṃsi's TWIM method align with the Pāḷi suttas, and what are the main scholarly responses?"`

4. `consciousness-after-nibbana-thai-forest-vs-suttas.md`
   - current: `"Consciousness after Nibbāna: the Thai Forest reading vs. the Pāḷi suttas"`
   - new: `"What do the Pāḷi suttas say about consciousness after Nibbāna, and how does the Thai Forest tradition interpret this?"`

5. `interpretations-of-paticcasamuppada.md`
   - current: `"Interpretations of Paṭiccasamuppāda Across Buddhist Traditions"`
   - new: `"How is Paṭiccasamuppāda interpreted across the major Buddhist traditions?"`

6. `jhana-positions-survey.md`
   - current: `"Jhāna: A Survey of Positions across the Suttas, Later Canon, Visuddhimagga, and Modern Scholarship"`
   - new: `"What is jhāna? A survey of positions across the suttas, later canon, the Visuddhimagga, and modern scholarship."`

7. `meditation-subjects-in-the-pali-canon.md`
   - current: `"Meditation Subjects in the Pāḷi Canon: Frequency, Sutta Description, and Later Evolution"`
   - new: `"What are the meditation subjects described in the Pāḷi canon, how frequently do they appear, and how did they evolve in later texts?"`

8. `mettā-evolution-comprehensive-research.md`
   - current: `"The Evolution of Mettā: From Sutta Radiation to Commentarial Sequencing and Modern Revival"`
   - new: `"How did the understanding and practice of mettā evolve from the early suttas through the commentarial tradition to modern times?"`

9. `nibbana-existence-cessation-debate.md`
   - current: `"Nibbāna: Existence or Cessation? A Survey of Sources and Positions"`
   - new: `"Is Nibbāna a form of existence or complete cessation? A survey of canonical sources and interpretive positions."`

10. `vimalaramsi-twim-reinvented-dhamma-critique.md`
    - current: `"Bhante Vimalaraṃsi and TWIM: A Comprehensive Analysis of Doctrine, Methodology, and Controversy"`
    - new: `"How does Bhante Vimalaraṃsi's TWIM teaching compare with the Pāḷi canonical sources on doctrine and method?"`

11. `yuganaddha-sutta-an-4-170.md`
    - current: `"Yuganaddha Sutta (AN 4.170): Four Paths to Arahantship and the Samatha-Vipassanā Debate"`
    - new: `"What are the four paths to arahantship described in the Yuganaddha Sutta (AN 4.170), and what do they reveal about the samatha-vipassanā relationship?"`

12. `attupanayika-reciprocity-metta-basis.md`
    - current: `"Attūpanāyika: Reciprocity as the Basis for Mettā and the Divine Abiding"`
    - new: `"What is attūpanāyika, and how does the principle of reciprocity relate to mettā and the divine abiding?"`

13. `five-meditation-sets-kasinas-vimokkhas-abhibhayatanas-aruppas-brahmaviharas.md`
    - current: `"Five EBT Meditation Sets Compared: Kasiṇas, Vimokkhas, Abhibhāyatanas, Aruppas, Brahmavihāras"`
    - new: `"How do the five EBT meditation sets — kasiṇas, vimokkhas, abhibhāyatanas, aruppas, and brahmavihāras — compare with each other?"`

14. `nibbana-existence-ontology.md`
    - current: `"Nibbāna's Ontological Status: Does It Exist, Not Exist, or Transcend Both?"` ✓ keep

15. `vitakka-vicara-semantic-evolution.md`
    - current: `"Vitakka/Vicāra: Semantic Evolution from Thinking to Applied Attention"`
    - new: `"How did the meaning of vitakka and vicāra evolve from ordinary thinking to the technical sense of applied and sustained attention?"`

16. `buddhism-explosive-growth.md`
    - current: `"Explosive Growth of Early Buddhism: Canon vs. History, Archaeology, and the Sociology of Mass Religion"`
    - new: `"What accounts for the rapid growth of early Buddhism? A comparison of canonical accounts with historical, archaeological, and sociological evidence."`

17. `simile-of-the-saw-anapanasati.md`
    - current: `"Kakacūpamā and Ānāpānassati: tracing the saw simile for mindfulness of breathing"`
    - new: `"What is the saw simile (Kakacūpamā) and how does it relate to mindfulness of breathing (Ānāpānassati)?"`

18. `monks-bowl-sizes.md` (uses `title:`)
    - current: `"Monk Bowl Sizes: Canonical Measurements, Commentary, and Modern Comparison"`
    - new: `"What are the canonical measurements for monks' bowls, and how do they compare with the commentarial tradition and modern practice?"`

19. `vedana-sanna-relationship.md`
    - current: `"Vedanā and Saññā: Causal, Conjoined, or Co-Arising?"` ✓ keep

20. `bhavanirodho-semantics-cessation-of-becoming.md`
    - current: `"Bhavanirodho: Can the Cessation of Becoming Mean Something Other Than Total Annihilation?"`
    - new: `"What does bhavanirodha mean in the Pāḷi canon, and how is the cessation of becoming interpreted across different traditions?"`

21. `immanent-transcendent-stream-entry.md`
    - current: `"Immanent and Transcendent in Early Teaching: Stream-Entry and the Fire Simile"`
    - new: `"How do the concepts of the immanent and transcendent appear in early Buddhist teaching, particularly in relation to stream-entry and the fire simile?"`

22. `an107-sn1268-bhavanirodho-insight-or-experience.md`
    - current: `"AN10.7 and SN12.68: Is 'Bhavanirodho Nibbānan'ti' Knowledge or Transcendental Experience?"`
    - new: `"In AN10.7 and SN12.68, does 'bhavanirodho nibbānan'ti' describe an act of knowledge or a transcendental experience?"`

23. `atthi-hoti-nibbana-grammar.md`
    - current: `"atthi vs. hoti: Grammatical Roots and the Phenomenological Reading of Nibbāna in Udāna 8.3"`
    - new: `"What is the grammatical difference between atthi and hoti, and how does it affect the reading of Nibbāna in Udāna 8.3?"`

24. `ayya-khema-jhana-definition.md`
    - current: `"Ayya Khemā's Definition of Jhāna: Absorption, Language, and Comparable Teachers"`
    - new: `"How does Ayya Khemā define jhāna, and how does her understanding of absorption compare with other teachers?"`

25. `body-awareness-meditation-states.md`
    - current: `"Body Awareness and Meditative States: Somatic Progression from Access to Absorption"`
    - new: `"How does body awareness change across meditative states, from access concentration through to full absorption?"`

26. `fire-physics-nibbana-argument.md`
    - current: `"Fire Physics and Nibbāna: The Vedic Latency Argument Against Cessationism"`
    - new: `"What is the relationship between Vedic fire physics and the meaning of Nibbāna, and does the concept of latency inform interpretations of cessation?"`

27. `fourth-jhana-no-breathing.md`
    - current: `"No Breathing in the Fourth Jhāna: Canon, Commentary, and Modern Debate"` ✓ keep

28. `nibbana-vs-brahman-absolute.md`
    - current: `"Nibbāna and the Absolute: Comparison with Brahman/Ātman — Aspects That Can and Cannot Be Compared"`
    - new: `"In what ways can Nibbāna be compared to the Brahman/Ātman concept, and where do such comparisons break down?"`

29. `buddha-political-incorrectness.md` (uses `title:`)
    - current: `"The Politically Incorrect Buddha: Shock, Satire, and Skilful Provocation in the Early Texts"`
    - new: `"How does the Buddha use shock, satire, and provocative language in the early texts, and what is the purpose of such teaching?"`

30. `dana-giving-generosity.md` (uses `title:`)
    - current: `"Dāna: Giving, Generosity, and Merit — Comprehensive Survey"`
    - new: `"What does the Pāḷi canon say about dāna — giving, generosity, and merit?"`

31. `early-buddhism-christianity-judaism-dialogue.md`
    - current: `"Common Themes and Metaphysical Divergences: Early Buddhism, Christianity, and Judaism in Dialogue"`
    - new: `"What are the areas of common ground and metaphysical divergence between early Buddhism, Christianity, and Judaism?"`

32. `early-buddhism-islam-dialogue.md`
    - current: `"Common Ground and Honest Difference: Early Buddhism and Islam in Interreligious Dialogue"`
    - new: `"What are the areas of common ground and significant difference between early Buddhism and Islam in interreligious dialogue?"`

33. `hindu-sects-early-buddhism-comparison.md`
    - current: `"Hindu Sects and Early Buddhism: A Comparative Study for Interreligious Dialogue"`
    - new: `"How do the major Hindu sects compare with early Buddhism, and what are the key areas of convergence and divergence?"`

34. `madhupindaka-mind-simulation-b.md` (uses `title:`)
    - current: `"The Mind-Generated World: papañca, Yogācāra, and the Constructed Nature of Reality"`
    - new: `"What is the relationship between papañca in early Buddhism and Yogācāra philosophy on the mind-constructed nature of reality?"`

35. `madhupindaka-mind-simulation.md`
    - current: `"The Buddhist Simulation Theory: Papañca and the Mind-Constructed World (Madhupiṇḍaka Sutta MN18)"`
    - new: `"What is papañca in the Madhupiṇḍaka Sutta (MN18), and how does the idea of a mind-constructed world compare with modern philosophical ideas?"`

36. `memory-impermanence-reconstruction.md`
    - current: `"Memory, Impermanence, and Reconstruction: Buddhist Philosophy Meets Neuroscience"`
    - new: `"What does Buddhist philosophy say about memory and impermanence, and how does this compare with neuroscientific accounts of memory reconstruction?"`

37. `nanananda-nibbana-minimal-right-view.md`
    - current: `"Ñāṇananda on Nibbāna: Position, Argument, and Minimal Right View for Stream Entry"`
    - new: `"What is Ñāṇananda's position on Nibbāna, and what does he consider the minimal right view required for stream-entry?"`

38. `nibbida-viraga-nirodha-disenchantment-dispassion-cessation.md`
    - current: `"Nibbidā, Virāga, Nirodha: Disenchantment, Dispassion, and Cessation across Historical Strata and Traditions"`
    - new: `"What are nibbidā, virāga, and nirodha? A study of disenchantment, dispassion, and cessation across historical strata and traditions."`

39. `two-truths-sammuti-paramattha.md`
    - current: `"Two Truths in Buddhism: Sammuti, Paramattha, and the 'One Truth' of the Suttanipāta"` ✓ keep

40. `arupa-vedananupassa-goenka-critique.md` (uses `title:`)
    - current: `"Arūpa as Basis for Vedanānupassanā: Sutta Evidence and Critique of Goenka's Method"`
    - new: `"What is the sutta evidence for arūpa as a basis for vedanānupassanā, and how does this compare with Goenka's method?"`

41. `bhavanga-development-and-comparative-gap.md`
    - current: `"Bhavaṅga: development, canonical absence, and the comparative gap it fills"`
    - new: `"What is bhavaṅga, how did it develop in Theravāda Abhidhamma, and what canonical gap does it fill?"`

- [ ] Apply all rewording edits above (skipping ✓ keep items)
  → verify: grep all `topic:` and `title:` fields across the vault and confirm each is a complete sentence with proper punctuation

---

## Phase 3 — Re-export PDFs

- [ ] Write batch PDF export script to `temp/batch_pdf_export.py` using the same weasyprint code from SKILL.md
- [ ] Run it: `uv run temp/batch_pdf_export.py`
  → verify: confirm PDF count in `Vicaya/PDF/` is 41 and all timestamps updated

---

## Phase verification

End of Phase 1: SKILL.md sanitization rule is present and readable.
End of Phase 2: all 41 notes have updated topic/title values; no `grep` for the old loaded phrasings returns results.
End of Phase 3: PDF folder contains 41 files, all regenerated today.
