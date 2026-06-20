---
name: vicaya-quick
description: Deeply research a specific Pāḷi/Buddhist question across the user's local sources (Obsidian vault, CST canon, DPD dictionary, library folders, EBC vault, SuttaCentral parallels) plus web/YouTube, and answer directly in chat with citations — no vault note, no gates, no ceremony. Invoke when the user types /vicaya-quick <question> or asks to "quickly research X", "just answer X from my sources", "what do the suttas say about X (don't write a note)", or any focused research question that wants a fast cited answer rather than a permanent note.
---

# Quick research skill

Answer one specific question, deeply but fast. This skill reuses every research
mechanism of the full `vicaya` skill, but its end product is a **cited answer in
chat** — not a vault note. It runs in a single session with no phase gates.

It keeps one small piece of `vicaya` machinery on purpose: a **scratch dossier**.
Every search auto-logs into it, so the run survives compaction and — more
importantly — can be **promoted to a full note later** without re-searching (see
*Promotion* at the end).

## Relationship to `vicaya` — read this once

All the tools, paths, and helper details live in `skill/vicaya/SKILL.md`. Do
**not** duplicate them here; read these sections of that file when you need them:

- **Setup — paths and tools** — the `eval "$(uv run tools/research_sources.py env)"`
  prefix for any direct shell command using `$VICAYA_*` paths; precondition env.
- **Calling the helpers** + **Helper return shapes** — every subcommand, its
  args, and the exact JSON field names (guessing them has crashed prior runs).
- **DPD dictionary database** — word meaning/grammar/root lookups and
  inflected-form resolution.
- **EBC vault** — `get-ebc-overview` → `get-agama`, translator comparison,
  Pātimokkha, the folder map and citation rules.
- **Investigation angles** — the standing checklist of evidentiary lenses; use it
  to decide *which* channels a given question needs (triage, Step 1 below).

## What this skill does NOT do

No vault note. No `scratch-gate` / `scratch-verify` / `scratch-self-audit`. No
Devil's Advocate pass. No OpenRouter cross-check. No PDF, no `sync_notes`, no run
report, no self-improvement loop, no retrospective. If the question genuinely
warrants a permanent note, *suggest promotion* — don't build the note here.

## Hard rules kept (these prevent wrong answers, not messy notes)

1. **Citations are non-negotiable.** Every claim carries a reference. A claim
   without a citation is a hallucination waiting to happen.
2. **CST paragraph numbers are book-global.** Always run `resolve-citation` to
   confirm which sutta a `paranum` belongs to before citing it — never assume the
   paranum matches a sutta number.
3. **Pāḷi spelling conventions differ per source** — canon/vault use exact
   diacritics with `ṃ` (not `ṁ`); library folders use ASCII. Search verbatim; on
   0 hits try edition spelling variants before concluding absence.
4. **Auto-captions mishear Pāḷi.** When a YouTube transcript's `is_auto` is true,
   paraphrase and link the timestamp — never quote Pāḷi verbatim from it.
5. **Don't ask the user to run shell commands you can run yourself** — read-only
   inspection, launching Obsidian, helper scripts via `uv run` are all yours.
6. **Obsidian must be running for `search-vault`.** If it fails with "app may not
   be running", launch it (Linux: `setsid xdg-open "obsidian://" >/dev/null 2>&1 &`;
   macOS: `open -a Obsidian`; Windows: `start "" "obsidian://"`), wait ~5s, retry.
   Never bare `obsidian` (that's the CLI, not the app).

All commands run from the vicaya repo root.

## Workflow — three steps, one session

### Step 1 — Understand and triage
Smooth the question into a clear sentence. Walk the **Investigation angles** list
from `vicaya/SKILL.md` once and pick only the channels that bear on *this*
question. Be adaptive, not exhaustive:

- A term/definition question → DPD + maybe one canon attestation.
- A sutta-anchored doctrinal question → canon (`s*_mul`), `sc-parallels` + EBC
  `get-ebc-overview`/`get-agama`, library folders, web.
- A practice/applied question → library (modern teachers) + canon + web/YouTube.

Then open the dossier so everything auto-logs (one command, no gates follow):

```bash
uv run tools/research_sources.py scratch-init <short-kebab-slug> \
  --question-original "<user's exact wording>" \
  --question-polished "<polished question>" \
  --scope-assumptions "<channels chosen + depth>" \
  --ambiguity clear   # or minor_uncertainty | unclear
# add --class thematic for non-sutta-anchored questions
```

Auto-logging is now on: every `search-*`, `sc-*`, `get-ebc-overview`,
`get-agama`, `fetch-transcript` call appends its full results to the dossier
automatically. For web fetches / Read excerpts you want kept, log manually:
`scratch-log 1 web "<url>" --summary "..."`. Do **not** advance phases or gate.

### Step 2 — Search the chosen channels
Run the picked helpers, in parallel where independent. Cast a wider net only if a
first pass is thin or surfaces a load-bearing source you haven't checked. Trust
the results and move on — there is no pre-answer verification pass beyond the
correctness rules above (always `resolve-citation` a CST paranum before citing).

### Step 3 — Answer in chat
Write the answer directly to the user, scaled to the question:

1. **Direct answer first** — lead with the conclusion, a few sentences.
2. **Evidence** — the key passages with citations: canon as
   `**MN60 Apaṇṇakasuttaṃ para 97** — "<pāḷi>" / "<english>"`, library as
   `[[Book]] — Author: "<snippet>"`, web as `[title](url)`, EBC translations
   cited to the translator (Bodhi/Sujato/Patton/…), never to "EBC".
3. **Honesty line** — one line on what's uncertain, contested, or not searched.

Keep it tight. This is an answer, not a dossier — depth lives in the sources you
cite, not in padding.

## Promotion — turning a quick answer into a full note

Because the dossier captured every search, a full `/vicaya` run can build the
permanent note on top of this work instead of starting over. End every run with a
suggestion like:

```
---
Answered from <N> sources (<a> canon, <b> library, <c> web). Dossier: <slug>
To turn this into a permanent linked vault note, run /vicaya and resume this
dossier:  scratch-resume <slug>
It reuses everything gathered here, adds commentary / parallel / cross-check
coverage, cross-links related vault notes, and writes the note.
```

(On promotion, `/vicaya`'s Phase 5 `scratch-verify` will backfill the unwritten
phase gates ascending — that recovery is already documented in `vicaya/SKILL.md`;
nothing extra is needed here.)

## When something fails
Same fallbacks as `vicaya/SKILL.md` (**When something fails** section): canon 0
hits → try `--lang any` and broader books; library 0 hits → looser terms / author
surname / `data/calibre_tags.csv`; `WebSearch` 403 → fall back to `WebFetch` on
constructed URLs; PDF garbled in `WebFetch` → `curl` to repo-local `temp/` then
`pdftotext`. If a path/tool is genuinely missing, tell the user — don't guess.
