# Spec — Vicaya index maintenance

## Overview
`Vicaya/summary-vicaya.md` and `Vicaya/catalog-by-topics.md` (in the Obsidian
vault, `$VICAYA_VAULT_PATH/Vicaya/`) are hand-maintained index notes over the
research notes in `Vicaya/`. Neither is updated automatically after a run, so
both have drifted: `summary-vicaya.md` is missing 86 notes, `catalog-by-topics.md`
is missing 32. This thread backfills both and adds a step to the vicaya skill
so future runs keep them current.

## What it should do
1. Move `Vicaya/Christianity Comparative/Real Apologies vs Narcissist
   Apologies.md` (undated, uncited, plain-English — Digest style) into
   `Vicaya Digest/`. Keep only the dated research note
   (`2026-06-25 - real-apologies-vs-narcissist-apologies.md`) indexed.
2. Backfill `summary-vicaya.md`: add a dated row with a one-sentence
   description for each of the 86 missing notes (64 main-folder, 13 "What the
   Suttas Say About", 9 "Christianity Comparative"), in chronological order
   within their existing sections.
3. Backfill `catalog-by-topics.md`: add a wikilink under the matching (or a
   new) topic heading for each of the 32 missing main-folder notes.
4. Publish both via `uv run scripts/sync_notes.py "Vicaya/summary-vicaya.md"`
   and `uv run scripts/sync_notes.py "Vicaya/catalog-by-topics.md"`
   (pre-approved path).
5. Edit `skill/vicaya/SKILL.md` Phase 7 (the summary line under "Critical
   execution rules" and the detailed exit-sequence line) to add: after
   `sync_notes.py` publishes the note, add the note's row/wikilink to both
   index files and publish them the same way. `vicaya-what-the-suttas-say`
   inherits this via its stated hybridization with the main skill's Phase 7,
   so it needs no separate edit.

## Assumptions & uncertainties
- Categories in `summary-vicaya.md` (Dhamma, Meditation, Vinaya, Pāḷi,
  Critical, Comparative, Abhidhamma, Historical, Sutta Study, Academic, Meta)
  and topic headings in `catalog-by-topics.md` are reused as-is; a new
  catalog heading is added only when no existing one fits.
- Descriptions are one sentence, written from each note's frontmatter
  `topic` field plus a skim of its body, matching the existing style.

## Constraints
- Do not touch the two DPD-feedback triage notes (2026-07-01, 2026-07-09) —
  different genre, excluded per user decision.
- `vicaya-digest` output is a separate index; out of scope.
- Only `scripts/sync_notes.py` / `scripts/sync_run_report.py` are
  pre-approved to publish into the vault git repo.

## How we'll know it's done
- Re-running the missing-notes diff (vault file list vs. wikilinks in each
  index) returns zero gaps, except the two excluded DPD-feedback notes.
- `skill/vicaya/SKILL.md` Phase 7 includes the index-update step in both
  places it's described.

## What's not included
- No changes to `vicaya-digest`, `vicaya-quick`, `vicaya-align`, or
  `vicaya-pdf` skills.
- No new automation script — the update is a manual-but-mandated step in the
  skill, since categorization/description-writing needs judgment a script
  can't reliably do.
