# 2026-06-11 — Temp directory cleanup correction

## Issue

After completing the Byron Katie / early Buddhist teaching Vicaya run, I left `data/tmp/vicaya-work-comparison/` in the repo because it contained citation dumps and the phase-6 cross-check review. The user correctly challenged this.

## Correction

That was inconsistent with the Vicaya workflow. Phase 7 explicitly cleans this run's disposable repo-local temp directory and says durable handoff material belongs in `data/scratch/`, while disposable extraction/work files belong under `temp/<scratch-slug>/`.

The specific Phase 7 cleanup snippet targets:

- `temp/$(basename "${SCRATCH%.md}")`

So using `data/tmp/` for run-local disposable artifacts was itself the mistake. The right convention is:

- durable research state: `data/scratch/<slug>.md`
- disposable run artifacts: `temp/<slug>/`
- not `data/tmp/<slug>/`

## Action Taken

Deleted only the untracked run-local directory:

- `data/tmp/vicaya-work-comparison/`

Left untouched:

- `data/scratch/early-buddhist-teaching-and-the-work.md`
- the saved vault note
- the generated PDF
- synced run reports

`git status --short` was clean afterward.

## Future Rule

For future Vicaya runs, put any disposable generated evidence, extraction output, prompts, cross-check transcripts, or command scratch files in `temp/<scratch-slug>/`. If material needs to survive compaction or handoff, summarize or link it in `data/scratch/<slug>.md` instead of inventing another temp location.
