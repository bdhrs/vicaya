# Handoff - vicaya-staged-skills-section-router

Session saved on 2026-06-04 after live staged-skill testing and Stage 3
three-run context-control revisions.

## Latest User Direction

The user completed a live research run and asked to tighten extensive
`vicaya-3-complete` execution to a default three-run split. They also stated
that the monolithic `skill/vicaya/SKILL.md` Phase 5 "Deferred-draft pattern"
self-improvement hunk was intentionally reverted because the staged sub-skills
already cover that protection. Do not reintroduce that main-skill hunk unless
the user explicitly asks.

When the user is ready to review/finalize this Kamma thread, continue with:

```text
/kamma:3-review @kamma/threads/20260602_vicaya-staged-skills-section-router/
```

Do not finalize before a fresh review. The prior review predates the user
revisions in Phases 9.5-9.12.

The stale `review.md` from the earlier pass has been intentionally deleted so
the next agent must run a fresh `/kamma:3-review`.

The staged workflow is currently in live testing. The user may return in the
next session with additions, issues, or behavior reports from running the new
staged skills before the thread is reviewed/finalized.

Most recent user direction: save the current session in this handoff; the user
will restart with the next issue.

## Current State Snapshot

- Phase 9.12 in `plan.md` is complete: extensive Stage 3 completion now uses
  mandatory three-run passes rather than adaptive "continue while context is
  healthy" wording.
- `skill/vicaya/SKILL.md` currently has no diff from this Stage 3 change.
- Current staged-skill edits are limited to `skill/vicaya-0-scope/SKILL.md`
  and `skill/vicaya-3-complete/SKILL.md`, plus this thread's `spec.md`,
  `plan.md`, and `handoff.md`.
- Existing extensive runs started before Phase 9.12 were patched with
  superseding Phase 0 Stage 3 context-plan notes so they test the new three-run
  `vicaya-3-complete` behavior:
  - `data/scratch/papanca-canon-usage.md`
  - `data/scratch/vicikiccha-hindrance-vs-fetter.md`
- The scratch-local Phase 7 draft file remains a completion artifact only. The
  vault must receive only the complete audited note.

## What Changed This Session

- Converted staged context-break handling from soft/advisory wording into a
  binding staged-mode contract.
- Split extensive Stage 1 gathering into narrower source-block hard stops after
  live testing showed the broad Pass A/B/C split could resume into too much
  remaining research.
- Replaced one-pass Stage 3 final-note rendering with a scratch-local Phase 7
  draft-file workflow for section-by-section note writing.
- Tightened extensive Stage 3 completion to mandatory three-run passes:
  1. writer brief plus `## Question` and `## Findings`;
  2. remaining evidence/support sections plus frontmatter canon-ref
     confirmation and completion audit;
  3. vault write, validation, PDF, Phase 7 gate, note/run-report sync, final
     report, and self-improvement loop.
- Patched two pre-existing extensive scratch dossiers with a later
  `stage-3-context-plan phase-9.12-supersedes` entry, so their older
  render-complete-note-in-one-pass Stage 3 plans are superseded:
  - `data/scratch/papanca-canon-usage.md`
  - `data/scratch/vicikiccha-hindrance-vs-fetter.md`
- Kept `skill/vicaya/SKILL.md` unchanged during this session. The canonical
  analytical workflow still owns research behavior.
- Added/updated bounded context-management instructions in:
  - `skill/vicaya-0-scope/SKILL.md`
  - `skill/vicaya-1-gather/SKILL.md`
  - `skill/vicaya-2-synthesize-review/SKILL.md`
  - `skill/vicaya-3-complete/SKILL.md`
- Updated durable docs:
  - `skill/vicaya/README.md`
  - `kamma/project.md`
- Updated thread docs:
  - `kamma/threads/20260602_vicaya-staged-skills-section-router/spec.md`
  - `kamma/threads/20260602_vicaya-staged-skills-section-router/plan.md`
- Deleted stale thread review:
  - `kamma/threads/20260602_vicaya-staged-skills-section-router/review.md`
- Patched the live research scratch file:
  - `data/scratch/moha-amoha-avijja-vijja.md`

Files touched by these latest live-test revisions include:

- `skill/vicaya-0-scope/SKILL.md`
- `skill/vicaya-1-gather/SKILL.md`
- `skill/vicaya-3-complete/SKILL.md`
- `skill/vicaya/README.md`
- `kamma/project.md`
- `kamma/threads/20260602_vicaya-staged-skills-section-router/spec.md`
- `kamma/threads/20260602_vicaya-staged-skills-section-router/plan.md`
- `kamma/threads/20260602_vicaya-staged-skills-section-router/handoff.md`
- `data/scratch/papanca-canon-usage.md`
- `data/scratch/vicikiccha-hindrance-vs-fetter.md`

## Current Staged Semantics

`vicaya-0-scope` now decides whether a staged run is extensive.

If it records `stage-1-context-plan`, `stage-2-context-plan`, or
`stage-3-context-plan` in scratch, those plans are binding for later staged
skills unless the user explicitly opts out before Stage 1 begins and a
`context-plan-opt-out` note is logged in scratch.

Later staged skills must not re-decide whether the planned split is optional:

- `vicaya-1-gather`: if `stage-1-context-plan` exists, run exactly one next
  source block, then hard stop at the planned safe boundary. A prior hard stop
  is only a handoff checkpoint, not completion of the whole Stage 1 plan.
  Heavy Phase 2 can pause after root-canon mūla/sutta research with a scratch
  in-progress note before commentary/exegesis; Phase 2 gate is written only
  after all canonical Phase 2 obligations are complete.
- `vicaya-2-synthesize-review`: if `stage-2-context-plan` exists, run only the
  next planned synthesis/review pass, then hard stop at the planned gate or
  safe Phase 5 handoff point.
- `vicaya-3-complete`: if `stage-3-context-plan` exists, run only the next
  planned completion pass, then hard stop at the safe completion boundary. For
  extensive notes, the default planned split is exactly three runs:
  1. writer brief plus `## Question` and `## Findings`;
  2. remaining evidence/support sections plus frontmatter canon-ref
     confirmation and completion audit, stopping before vault write;
  3. vault write, validation, PDF, Phase 7 gate, note/run-report sync, final
     report, and self-improvement loop. The vault receives only the complete
     audited note.

Model-tier recommendations do not override a recorded context plan.

## Existing Runs Patched For Phase 9.12

Two existing extensive runs were started before the mandatory three-run Stage 3
implementation. They already had older `stage-3-context-plan` entries. I added
newer Phase 0 context-plan entries using the scratch helper:

- `data/scratch/papanca-canon-usage.md`, line 38:
  `stage-3-context-plan phase-9.12-supersedes`
- `data/scratch/vicikiccha-hindrance-vs-fetter.md`, line 66:
  `stage-3-context-plan phase-9.12-supersedes`

Those entries explicitly tell `vicaya-3-complete` to use the Phase 9.12
mandatory three-run split and not the older render-complete-note-in-one-pass
plan.

Verified resume state after patching:

```json
{
  "papanca-canon-usage": {
    "last_gate": {"phase": "3b", "title": "Phase 3b — Sanskrit"},
    "next_phase": "4"
  },
  "vicikiccha-hindrance-vs-fetter": {
    "last_gate": {"phase": "2.5", "title": "Phase 2.5 — SC Parallels"},
    "next_phase": "3"
  }
}
```

## Prior Live Research Scratch Patch

Earlier live testing patched this run:

```text
data/scratch/moha-amoha-avijja-vijja.md
```

At that time it had completed Phase 0 through Phase 6 and was ready for
Phase 7:

```json
{
  "last_gate": {"phase": "6", "title": "Phase 6 — Cross-check"},
  "next_phase": "7"
}
```

I appended Phase 0 scratch entries:

```text
2026-06-03T20:52:26 - context-plan-hard-stops
2026-06-03T21:20:21 - context-plan-source-block-hard-stops
2026-06-04T06:21:32 - stage3-draft-file-plan
```

Those entries supersede the earlier soft and broad context-plan wording and say:

- the run is extensive;
- the Stage 1, Stage 2, and Stage 3 context plans are binding hard stops;
- model-tier recommendations do not override the plan;
- only an explicit user opt-out before Stage 1 disables those hard stops;
- Stage 1 uses source-block checkpoints, not broad Pass A/B/C spans;
- the current next Stage 1 invocation must complete only the active Phase 3
  library/source block, write the Phase 3 gate, and hard stop;
- it must not proceed into Phase 4a web, Phase 4b YouTube, or Phase 4c WisdomLib
  in that same invocation;
- Stage 3 must use `data/scratch/moha-amoha-avijja-vijja.phase7-draft.md` as a
  scratch-local draft file for section-by-section note writing;
- Stage 3 must never write a partial/draft note to the vault.

The user's next research step is to resume completion in fresh context:

```text
/vicaya-3-complete moha-amoha-avijja-vijja
```

Pin the scratch path because `.active` may point to another run:

```text
VICAYA_SCRATCH=/Users/deva/Documents/dps/vicaya/data/scratch/moha-amoha-avijja-vijja.md
```

Those live-run instructions are historical. The current Stage 3 default is the
Phase 9.12 mandatory three-run split documented above and in `plan.md`.

## Validation Run

Checks run during this session:

- `rg` checks confirmed the active staged skill files contain the Phase 9.12
  mandatory three-run Stage 3 split.
- `git diff --check -- skill/vicaya-0-scope/SKILL.md
  skill/vicaya-3-complete/SKILL.md
  kamma/threads/20260602_vicaya-staged-skills-section-router/spec.md
  kamma/threads/20260602_vicaya-staged-skills-section-router/plan.md` passed.
- `git diff -- skill/vicaya/SKILL.md` returned no diff, confirming the
  monolithic-skill Phase 5 self-improvement hunk is not present.
- `rg` confirmed `phase-9.12-supersedes` entries were written to
  `data/scratch/papanca-canon-usage.md` and
  `data/scratch/vicikiccha-hindrance-vs-fetter.md`.
- `scratch-resume` confirmed the two patched scratch files retained their
  original resume state: `papanca-canon-usage` next phase `4`, and
  `vicikiccha-hindrance-vs-fetter` next phase `3`.

## Failed Attempts / Workarounds

- The first attempt to append to scratch failed because `uv` tried to use
  `/Users/deva/.cache/uv`, which is outside the sandbox:
  `failed to open file /Users/deva/.cache/uv/sdists-v9/.git`.
- Rerun succeeded with:

```text
UV_CACHE_DIR=/private/tmp/uv-cache
VICAYA_SCRATCH=/Users/deva/Documents/dps/vicaya/data/scratch/moha-amoha-avijja-vijja.md
```

## Remaining Work For This Kamma Thread

- Account for any user-reported issues from the live staged-skill test run
  before review/finalization.
- If the user resumes `papanca-canon-usage` or
  `vicikiccha-hindrance-vs-fetter`, continue their current phases normally.
  When they reach `vicaya-3-complete`, the superseding scratch entries should
  make them use the Phase 9.12 three-run Stage 3 split.
- Run a fresh `/kamma:3-review` for this thread.
- This should recreate
  `kamma/threads/20260602_vicaya-staged-skills-section-router/review.md`.
- The review must evaluate the current design, not the older pure-router-only
  assumption:
  - section routing still points to canonical headings;
  - bounded context-plan/context-break controls are the only staged behavioral
    additions;
  - recorded context plans are binding unless a scratch opt-out exists;
  - no canonical analytical workflow was changed for these context controls;
  - no new workflow state exists outside the canonical scratch system except
    the allowed scratch-local Phase 7 draft-file artifact for staged
    completion.
- If review passes, finalize with `/kamma:4-finalize`.

## Known Caveats

- The thread history still contains earlier Phases 3-6 literal-router text.
  Later Phases 9.5-9.12 intentionally supersede the pure-router constraint only
  for bounded staged context controls.
