# Spec: vicaya-quick — deep research, fast cited answer, no note

## Overview
A new sibling skill `vicaya-quick` that reuses all of `vicaya`'s research
mechanisms (the `research_sources.py` helpers + EBC + DPD + web/YouTube) but
drops the artifact machinery — no vault note, no gates, no Devil's Advocate, no
mandatory cross-check, no PDF/sync/run-report/self-improvement. The end is a
**cited answer in chat**, scaled to the question.

The one piece of `vicaya` machinery deliberately kept is the **scratch dossier**:
`vicaya-quick` runs `scratch-init` at the start so every helper call auto-logs
into a recyclable dossier. This costs one command and a gitignored file, and it
makes every quick run losslessly **promotable** — a follow-up `/vicaya` can
`scratch-resume <slug>` and build a full note on top of the work already done,
rather than re-searching. It also survives context compaction.

## What it should do
- `skill/vicaya-quick/SKILL.md`, short (~100 lines). For tool mechanics it
  **references** `skill/vicaya/SKILL.md` sections (Setup, Calling the helpers,
  Helper return shapes, DPD, EBC, Investigation angles) rather than duplicating
  them — the self-improvement loop only edits `vicaya/SKILL.md`, so duplication
  would drift.
- Three-step workflow: (1) understand the question + adaptive in-head triage of
  which source channels apply; (2) run only those searches in one session
  (parallel where possible); (3) answer in chat — direct answer first, then key
  evidence with citations, then a one-line honesty note on gaps.
- Adaptive depth: a term lookup hits DPD + canon only; a doctrinal question fans
  to canon + EBC parallels + library + web. No fixed full-breadth sweep.
- Keep the correctness rules that prevent *wrong answers*: citations mandatory,
  Pāḷi spelling conventions, `resolve-citation` before trusting a CST paranum,
  the auto-caption caveat, the `eval "$(... env)"` prefix, launching Obsidian
  before vault search.
- Start every run with `scratch-init <slug> --question-original/--question-polished/
  --scope-assumptions/--ambiguity` so auto-logging is on and gate 0 is clean. Do
  **not** call any `scratch-gate`, `scratch-verify`, or `scratch-self-audit`.
- End every run with a promotion suggestion: the dossier slug, the source counts,
  and a copy-ready line to promote via `/vicaya` resuming that slug.
- Register the skill: `config/opencode/commands/vicaya-quick.md`, README symlink
  sections (both the quick Setup loops and the detailed walkthrough +
  verification), and the active `~/.claude/skills/vicaya-quick` symlink.

## Assumptions & uncertainties
- Decided in planning (user-confirmed): adaptive single-pass; reference
  `vicaya/SKILL.md`; no verify step before answering; always create the dossier
  (not lazy) so promotion survives compaction.
- On promotion, `/vicaya`'s Phase 5 `scratch-verify` will find gates 1–4
  unwritten and backfill them ascending — already documented recovery in
  `vicaya/SKILL.md`, not a redesign.
- All quick-run searches auto-log under the post-init active phase (1); that is
  fine — `/vicaya` reads the whole dossier via `cat` regardless of phase bucket.

## Constraints
- No absolute, user-specific paths in `skill/vicaya-quick/SKILL.md`.
- `vicaya-quick` must never write to the vault, never call a gate, never run the
  OpenRouter cross-check, never produce a PDF / run report / retrospective.
- No edits to `vicaya/SKILL.md` behavior — `vicaya-quick` only *references* it.

## How we'll know it's done
- `skill/vicaya-quick/SKILL.md` exists, references `vicaya/SKILL.md` for
  mechanics, contains the 3-step workflow + scratch-init + promotion suggestion,
  and contains no `scratch-gate`/`scratch-verify`/note/sync instruction.
- `config/opencode/commands/vicaya-quick.md` exists matching the sibling pattern.
- README's symlink loops and walkthrough mention `vicaya-quick` like `vicaya-pre`.
- `~/.claude/skills/vicaya-quick` resolves to `skill/vicaya-quick`.

## What's not included
- Any change to `vicaya`'s research/output behavior.
- A separate "promote" command — promotion is just `/vicaya` resuming the slug.
- Touching `~/.agents` / `~/.gemini` skill dirs (additive symlink commands are
  handed to the user, not run) beyond the active `~/.claude` one.
