# YouTube channel allowlist

Source of truth for which YouTube channels the `/vicaya` skill trusts, treats
provisionally, or filters out. Edited by hand; parsed by
`tools/research_sources.py::load_channel_allowlist`.

## Format

```
## trusted
- Display Name
- Display Name | UCxxxxxxxxxxxxxxxxxxxxxx

## probationary
- ...

## excluded
- ...
```

- One channel per line, prefixed with `- ` (Markdown bullet).
- Channel ID (the stable `UC…` part of the URL) is optional but recommended,
  since display names can change. Separate name and ID with a single ` | `.
- Tier matching is case-insensitive on name; exact on ID. ID wins if both match.
- Unknown headings are ignored.

## Tier semantics

- **trusted** — proven good across multiple research runs. Quotes from these
  channels may be used with normal care (still: never quote Pāḷi from
  auto-captions). New entries here require concrete evidence noted in a run
  reflection.
- **probationary** — surfaced in searches, not yet evaluated, OR seen and
  judged fine but not yet validated across topics. **Default tier for any new
  channel.** Pass through unfiltered.
- **excluded** — known noise (AI-narrated, clickbait, off-topic, low-quality
  summaries). Filtered out of results. Promotion to exclusion requires
  concrete evidence noted in a run reflection — never exclude on hunch.

## Maintenance

After every research run, the reflection template prompts: "which channels
seen this run worth promoting / demoting?" Apply those decisions here.
Prune dead links periodically.

---

## trusted
- Buddhist Insights @ Empty Cloud
- Bhikkhu Dhammānanda
- Yuttadhammo Bhikkhu
- Doug's Dharma | UCPIyEJzvW7SsbiIrooixjNA
- Amaravati Buddhist Monastery | UCsgmmAelfZ2kfXZ08xlHpDw
- Guru Viking
- Yongey Mingyur Rinpoche
- Ajahn Anan Dhamma
- Buddhist Society of Western Australia | UC6M_EhnSSdTG_SXUp6IAWmQ

## probationary
- Clear Mountain Monastery Project
- Candana Bhikkhu
- Jansen Stovicek
- Lotus Lift
- TWIM - Dhamma Sukha Meditation Center
- Sutta Meditation Series
- Learning Buddhism in English with Dhammadharani
- Plum Village App
- Dharma robe
- Wisdom Park
- Theravada Buddhism Learning
- Culture Exchange Blog
- Buddha Tube
- Mind Podcast (Buddhism)
- Awaken Consciousness
- Regain Awareness
- Ego (buddhism podcast)
- Buddha Speaks
- Buddha's Wisdom
- Buddhism Podcast

## excluded
