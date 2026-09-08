---
date: 2026-09-08
slug: saccanurakkhana-speech-ethics
question_original: "When we present the Dhamma in conversation — either teaching, or conversation with co-monastics, or in the public — in order to not reveal attainments indirectly, we should not change the way we speak about the Dhamma right? Or else people can detect, 'you used to speak like this, now you speak differently, it seems that you have attained something.' Then how applicable is this sutta on qualifying our statements? When we say 'parinibbana is the cessation of everything', do we have to put qualifiers, like based on sutta, based on my faith, etc? There's another sutta which has a lay person doesn't believe 2nd Jhana exist, because he knows personally 2nd Jhana exist. So clearly if one says 'I believe parinibbana is the cessation of everything,', that pattern of speech cannot cross over to after attainments. From MN95, formulate a good vicaya question for me"
note: "vault/Vicaya/2026-09-08 - saccanurakkhana-speech-ethics.md"
pdf: "vault/Vicaya/PDF/2026-09-08 - saccanurakkhana-speech-ethics.pdf"
gates: [0, 1, 2, "2.5", 3, "3b", 4, "4b", "4c", 5, 6, 7]
agent: "Claude Sonnet 4.6 (Claude Code)"
---

# Run reflection — saccanurakkhana-speech-ethics

## What worked well

**The question was perfectly canonical.** The user identified a genuine tension that is actually in the suttas, and the three seeds they gave (MN95, SN41.8, and Pārājika 4) were exactly the right starting points. The parallel search for AN8.2 was the single most valuable discovery of the run — the "addhā ayamāyasmā jānaṃ jānāti passaṃ passatī" passage is a canonical recognition that fellow practitioners *correctly* infer attainment from behavioral patterns including noble silence. This completely reframes the user's question: the canon is not trying to prevent this inference; it expects it.

**Phase-per-phase scratch discipline held.** Context compaction fired during the gather phases but the scratch file was well-populated at each phase boundary and no findings were lost.

**The three-audience structure** (A: within the Sangha — expected recognition; B: to laypeople — normative caution; C: to the Buddha — udānas validated) emerged naturally from the canon evidence and significantly clarified the scope of the answer.

## Key finding

The saccānurakkhana formula in MN95 applies specifically to *indirect/inherited* knowledge (the five categories: saddhā, ruci, anussava, ākāraparivitakka, diṭṭhinijjhānakkhanti). SN41.8 shows that using faith-language for what one knows directly would misrepresent one's epistemic state. AN8.2 shows the monastic community is expected to correctly infer attainment from behavioral patterns — the canon presents this inference as correct (addhā), not as a problem to suppress. Pārājika 4 prohibits false claims only (anabhijānaṃ); the speech-pattern change question is primarily a Sangha-context question, and the canon doesn't try to hide this signal — it treats it as appropriate community recognition.

## Limitations

- **Papañcasūdanī** (MN aṭṭhakathā) search on saccānurakkhana returned 0 hits. The commentarial interpretation remains unconfirmed.
- **Cross-check timed out** after 300s (opencode:deepseek/deepseek-v4-pro). Self-review was thorough but a second-opinion review would have been valuable given the interpretive load.
- The **saccānurakkhana → indirect knowledge only** claim is interpretive inference from the five categories listed, not an explicit sutta statement. The inverse ("this does not apply when you know directly") is not in the text. This is flagged in Critical Gaps.

## Improvement suggestions

- The cross-check chain needs a fallback model that responds in under 300s for a prompt of this length. The deepseek-v4-pro entry consistently times out on long review prompts.
- The Papañcasūdanī search should try ṭīkā (`s0202a_tik`) and alternative search stems for saccānurakkhana if future runs revisit this topic.

## Process notes

- Gates 4, 4b, 4c were written by orchestrator backfill after Phase 3 completed (sub-agents completed their work but couldn't self-gate because the gate sequence was blocked; sequential backfill resolved this).
- Phase 3b gate initially refused because Phase 3 was not yet gated — resolved by waiting for Phase 3 sub-agent to complete.
- Noble silence fallback search: when vault search returned JSON errors (Obsidian update banner), `rg` over `$VICAYA_EBC_VAULT_PATH` was used successfully.
