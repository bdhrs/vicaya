# Handoff - vicaya-staged-skills-section-router

Session saved on 2026-06-04 after live staged-skill testing and context-control
revisions.

## Latest User Direction

The user asked to save the current history in this handoff and will start the
next session with the next issue. Do not proactively continue research,
review, finalize, or implement adjacent changes unless the next user message
asks for it.

When the user is ready to review/finalize this Kamma thread, continue with:

```text
/kamma:3-review @kamma/threads/20260602_vicaya-staged-skills-section-router/
```

Do not finalize before a fresh review. The prior review predates the user
revisions in Phases 9.5-9.10.

The stale `review.md` from the earlier pass has been intentionally deleted so
the next agent must run a fresh `/kamma:3-review`.

The staged workflow is currently in live testing. The user may return in the
next session with additions, issues, or behavior reports from running the new
staged skills before the thread is reviewed/finalized.

## Current State Snapshot

- Phase 9.10 in `plan.md` is complete: Stage 3 now uses a scratch-local
  Phase 7 draft file instead of one-pass final-note rendering.
- `skill/vicaya/SKILL.md` was not edited in the Stage 3 draft-file session.
  It is still dirty from earlier staged-router work in this thread.
- Current live research scratch:
  `data/scratch/moha-amoha-avijja-vijja.md`.
- Pinned resume state for that run: last gate `6`, next phase `7`.
- Stage 3 draft file to create/resume:
  `data/scratch/moha-amoha-avijja-vijja.phase7-draft.md`.
- The draft file is a scratch-local artifact only. The vault must receive only
  the complete audited note.

## What Changed This Session

- Converted staged context-break handling from soft/advisory wording into a
  binding staged-mode contract.
- Split extensive Stage 1 gathering into narrower source-block hard stops after
  live testing showed the broad Pass A/B/C split could resume into too much
  remaining research.
- Replaced one-pass Stage 3 final-note rendering with a scratch-local Phase 7
  draft-file workflow for section-by-section note writing.
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
- `data/scratch/moha-amoha-avijja-vijja.md`

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
  planned completion pass, then hard stop at the safe completion boundary.
  For large final notes, it uses a scratch-local draft file under
  `data/scratch/`, saves each section there, and logs only concise section
  status in the main scratch. The vault receives only the complete audited
  note.

Model-tier recommendations do not override a recorded context plan.

## Live Research Scratch Patched

The current research run is:

```text
data/scratch/moha-amoha-avijja-vijja.md
```

It has completed Phase 0 through Phase 6. Phase 7 has not written a vault note
yet. Pinned `scratch-resume` reports:

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

That completion session should create or resume
`data/scratch/moha-amoha-avijja-vijja.phase7-draft.md`, write sections into it,
log section status in the main scratch, and stop only at a saved section boundary
if context pressure rises.

## Validation Run

Checks run during this session:

- `rg` checks confirmed the active staged skill files contain binding hard-stop
  wording and `context-plan-opt-out` handling.
- `rg` checks confirmed Stage 1, Stage 2, and Stage 3 context guards are present.
- `rg -n "[ \t]$"` over staged skill files, README, project docs, and thread
  spec/plan found no trailing whitespace.
- `git diff --check -- skill/vicaya/README.md kamma/project.md
  kamma/threads/20260602_vicaya-staged-skills-section-router/spec.md
  kamma/threads/20260602_vicaya-staged-skills-section-router/plan.md` passed.
- `UV_CACHE_DIR=/private/tmp/uv-cache VICAYA_SCRATCH=/Users/deva/Documents/dps/vicaya/data/scratch/moha-amoha-avijja-vijja.md uv run tools/research_sources.py scratch-resume moha-amoha-avijja-vijja`
  confirmed the run is at next phase `7`.

Note: staged skill directories are currently untracked in this worktree, so
`git diff --check` does not cover those files. I used direct whitespace checks
for them.

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

- `git status --short` still shows unrelated dirty Python files:
  - `tests/test_research_sources.py`
  - `tools/research_sources.py`
  These were not part of this session's context-break edits.
- `skill/vicaya/SKILL.md` is still dirty from earlier staged-router work in this
  thread. This session did not edit it.
- The thread history still contains earlier Phases 3-6 literal-router text.
  Later Phases 9.5-9.10 intentionally supersede the pure-router constraint only
  for bounded staged context controls.
