# Handoff - vicaya-staged-skills-section-router

Session saved on 2026-06-04 after live staged-skill testing, Phase 9.14
`1 + 4 + 2 + 3` hard-stop redistribution, a post-merge route-anchor fix after
merging `main` into `sub-skills`, and a Phase 9.15 sync of the user's
unfinished scratch runs.

## Latest User Direction

The current design target is the balance between research cost and context
safety. The user does not want many unnecessary micro-sessions, but also never
wants staged passes to hit or exceed the 200k context limit. Treat passes near
188k-195k as too close to the limit even if they technically fit; treat any
pass over 200k as a design failure requiring action. The practical target
should be enough margin that normal variance does not push a pass past 200k.
The user clarified that only predetermined hard stops are working. Do not rely
on model judgement such as "context seems comfortable", "context pressure is
high", "the dossier is manageable", or conditional/adaptive continuation. The
model cannot reliably calculate current context usage. Hard stops must be
placed ahead of time at phase/source-section boundaries using observed token
statistics.

Golden rule for the latest revision: do not introduce any new research logic.
`skill/vicaya/SKILL.md` remains the source of the actual research workflow,
quality standard, evidence rules, gates, helper behavior, final-note
requirements, and self-improvement loop. This thread's job is only to
redistribute the same canonical work across fixed fresh-context sessions. The
quality bar must remain exactly the same as the original skill.

The user supplied live-run token statistics:

- `vicaya-1-gather`
  - Stage 2-2.5 Pass B: 195k tokens, barely under 200k and needs improvement.
  - Stage 3/3b Pass C: 144k tokens, acceptable.
  - Stage 4a/4b/4c Pass D: 131k tokens, acceptable.
- `vicaya-2-synthesize-review`
  - Phase 5: 188k tokens, upper limit and should be tightened.
  - Phase 6: 122k tokens, good.
- `vicaya-3-complete`
  - Run 1: 83.6k tokens, underused.
  - Run 2: 204k tokens, over the limit and needs action.
  - Run 3: 102k tokens, good.

Implemented latest revision target: `1 + 4 + 2 + 3` fixed-session split,
meaning 10 total staged invocations including Stage 0. This replaces the
earlier conservative `1 + 5 + 3 + 3` suggestion because cost efficiency still
matters.

- Stage 0: 1 invocation. Phase 0 scope/context plan only, then hard stop.
- Stage 1: keep 4 invocations and rebalance work, rather than adding stops:
  1. Phase 1 vault/EBC context, angle triage, and perspective map plus Phase 2
     root-canon mūla/sutta research; hard stop at a scratch-logged Phase 2
     in-progress checkpoint if commentary/ṭīkā research remains.
  2. Phase 2 commentary/exegesis only; write the Phase 2 gate when all
     canonical Phase 2 obligations are complete, then hard stop.
  3. Phase 2.5 SuttaCentral/offline parallel research when applicable plus
     Phase 3 library research and Phase 3b Sanskrit source research when
     applicable; stop after the Phase 3b gate when applicable, otherwise after
     the latest applicable gate.
  4. Phase 4a web research, Phase 4b YouTube research when applicable, and
     Phase 4c WisdomLib research; stop after the Phase 4c gate.
- Stage 2: keep 2 invocations and rebalance the heavy Phase 5 pass into the
  lighter Phase 6 pass without adding a stop:
  1. Canonical Phase 5 entry verification, scratch review, source/angle
     completeness checks, Devil's Advocate answers, bibliography/source
     allocation review, and a concise Phase 5 drafting plan; hard stop at a
     scratch-logged Phase 5 in-progress checkpoint before full drafting.
  2. Finish Phase 5 drafting/integration and Phase 5 gate, then run Phase 6
     second-pass review and Phase 6 gate; hard stop and hand off to
     `vicaya-3-complete`.
- Stage 3: keep 3 invocations and rebalance the over-limit Run 2 into the
  underused Run 1:
  1. Writer brief, scratch-local draft file setup, title/slug/outline/source
     allocation/frontmatter targets, `## Question`, `## Findings`, and the
     heaviest early evidence sections, especially Canon Evidence and
     Commentary Evidence; then hard stop.
  2. Remaining evidence/support sections, bibliography, footnotes,
     frontmatter `canon_refs` confirmation, and completion audit; then hard
     stop before any vault write.
  3. Vault write, validation, PDF, Phase 7 gate, note/run-report sync, final
     report, and self-improvement loop.

The staged skills, spec, plan, and handoff have been updated for this approved
`1 + 4 + 2 + 3` hard-stop redistribution. A fresh review currently exists at
`kamma/threads/20260602_vicaya-staged-skills-section-router/review.md` with
verdict `PASSED`.

Earlier user direction still applies: the monolithic `skill/vicaya/SKILL.md`
Phase 5 "Deferred-draft pattern" self-improvement hunk was intentionally
reverted because the staged sub-skills already cover that protection. Do not
reintroduce that main-skill hunk unless the user explicitly asks.

Prior revision: the user asked to unite extensive `vicaya-1-gather` source
blocks to reduce research cost. Stage 1 now defaults to four grouped sessions
instead of the previous nine-block micro-split.

When the user is ready to finalize this Kamma thread, continue with:

```text
/kamma:4-finalize @kamma/threads/20260602_vicaya-staged-skills-section-router/
```

Because Phase 9.15 changed handoff text and ignored scratch run state after the
current `PASSED` review, run a fresh review or focused review check first if
strict Kamma finalization requires every post-review handoff change to be
covered. No staged skill behavior changed in Phase 9.15.

The staged workflow is currently in live testing. The user may return in the
next session with additions, issues, or behavior reports from running the new
staged skills before the thread is finalized.

Earlier completed user direction: after the `main` merge, audit whether
anything important to this thread was overwritten; then apply the minimal
approved fix for the one stale route anchor, update this handoff, suggest a
commit message, and restart in fresh context.

## Post-Merge Audit And Fix - 2026-06-04

The merge commit was `1a51a90` (`Merge branch 'main' into sub-skills`). It
introduced intentional `main` changes to the canonical Vicaya skill from the
archived `parallel-scratch-state`, `notes-push`, and `calibre-ro-sqlite`
threads. The staged skill files themselves were not overwritten by the merge.

One relevant breakage was found: `main` renamed the canonical Phase 7 heading
from `### GitHub push (user-triggered)` to
`### GitHub note sync (pre-approved)`, but `vicaya-3-complete` and this
thread's route-list docs still pointed at the old heading. That would make
Stage 3 stop because it cannot find every listed routed canonical section.

Applied minimal approved fix:

- `skill/vicaya-3-complete/SKILL.md`: Stage 3 route list now uses
  `### GitHub note sync (pre-approved)`.
- `kamma/threads/20260602_vicaya-staged-skills-section-router/spec.md`: Stage
  3 required route list now uses the same heading.
- `kamma/threads/20260602_vicaya-staged-skills-section-router/plan.md`: Phase
  6 literal router list now uses the same heading.
- `skill/vicaya/SKILL.md` was not edited for this fix.

Verification after the fix:

- `rg -n "GitHub push \(user-triggered\)" skill/vicaya-3-complete/SKILL.md
  kamma/threads/20260602_vicaya-staged-skills-section-router/spec.md
  kamma/threads/20260602_vicaya-staged-skills-section-router/plan.md` returned
  no matches.
- A route-anchor audit confirmed all four staged route lists resolve to real
  non-fenced canonical headings in `skill/vicaya/SKILL.md`.
- `rg -n "GitHub note sync \(pre-approved\)" ...` shows the canonical heading
  and the three updated route-list references.
- `git diff --check -- skill/vicaya-3-complete/SKILL.md
  kamma/threads/20260602_vicaya-staged-skills-section-router/spec.md
  kamma/threads/20260602_vicaya-staged-skills-section-router/plan.md` passed.

Tracked dirty files at the time of the post-merge fix were:

- `skill/vicaya-3-complete/SKILL.md`
- `kamma/threads/20260602_vicaya-staged-skills-section-router/spec.md`
- `kamma/threads/20260602_vicaya-staged-skills-section-router/plan.md`
- `kamma/threads/20260602_vicaya-staged-skills-section-router/handoff.md`

Historical suggested commit message for that post-merge fix:

```text
docs(vicaya): align staged completion route with note sync heading
```

Current restart prompt for the next session:

```text
Continue @kamma/threads/20260602_vicaya-staged-skills-section-router. Read handoff.md first. The staged router design is reviewed with verdict PASSED, and Phase 9.15 synced the two unfinished scratch runs to Phase 9.14 hard-stop logic. Recheck git status, handle any new user-reported staged test issue, then proceed toward /kamma:4-finalize when ready. Do not reintroduce the monolithic Phase 5 deferred-draft hunk; that was intentionally reverted.
```

`review.md` currently exists with verdict `PASSED`. Because Phase 9.15 changed
only handoff text and ignored scratch run state after that review, run a fresh
review or focused review check only if strict finalization requires it.

## Current State Snapshot

- Phase 9.12 in `plan.md` is complete: extensive Stage 3 completion now uses
  mandatory three-run passes rather than adaptive "continue while context is
  healthy" wording.
- Phase 9.13 in `plan.md` is complete: extensive Stage 1 gathering now uses
  four bundled cost-control sessions.
- Phase 9.14 in `plan.md` is complete: extensive staged mode now uses the
  fixed `1 + 4 + 2 + 3` hard-stop redistribution, with no adaptive
  context-usage judgement and no new research logic.
- Phase 9.15 in `plan.md` is complete: the two unfinished user-named research
  scratches were patched with latest Phase 9.14 supersession notes, and this
  handoff was corrected after checking the current `PASSED` review.
- `skill/vicaya/SKILL.md` currently has no diff from this Stage 3 change.
- Earlier Stage 1/Stage 3 revisions touched `skill/vicaya-0-scope/SKILL.md`,
  `skill/vicaya-1-gather/SKILL.md`, and `skill/vicaya-3-complete/SKILL.md`,
  plus this thread's `spec.md`, `plan.md`, and `handoff.md`.
- Current token-budget feedback has been implemented in the staged skill
  behavior, `spec.md`, `plan.md`, and this handoff.
- Existing extensive runs that previously had Phase 9.12/9.13 supersession
  notes now also have Phase 9.14 supersession notes for their unfinished
  stages:
  - `data/scratch/papanca-canon-usage.md`
  - `data/scratch/vicikiccha-hindrance-vs-fetter.md`
- The scratch-local Phase 7 draft file remains a completion artifact only. The
  vault must receive only the complete audited note.

## What Changed This Session

- Converted staged context-break handling from soft/advisory wording into a
  binding staged-mode contract.
- Split extensive Stage 1 gathering into narrower source-block hard stops after
  live testing showed the broad Pass A/B/C split could resume into too much
  remaining research, then re-bundled those stops into four cost-control
  sessions after the user clarified that nine Stage 1 sessions defeated the
  cost reason for staged mode.
- Replaced one-pass Stage 3 final-note rendering with a scratch-local Phase 7
  draft-file workflow for section-by-section note writing.
- Tightened extensive Stage 3 completion to mandatory three-run passes:
  1. writer brief plus `## Question` and `## Findings`;
  2. remaining evidence/support sections plus frontmatter canon-ref
     confirmation and completion audit;
  3. vault write, validation, PDF, Phase 7 gate, note/run-report sync, final
     report, and self-improvement loop.
- Earlier patches added Phase 9.12/9.13 supersession notes to the two
  pre-existing extensive scratch dossiers. Phase 9.15 added newer Phase 9.14
  supersession notes so the current unfinished runs follow the final
  `1 + 4 + 2 + 3` redistribution.
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
- Current thread review exists and is `PASSED`:
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

Phase 9.15 additionally touched:

- `kamma/threads/20260602_vicaya-staged-skills-section-router/plan.md`
- `kamma/threads/20260602_vicaya-staged-skills-section-router/handoff.md`
- `data/scratch/papanca-canon-usage.md`
- `data/scratch/vicikiccha-hindrance-vs-fetter.md`

Tracked files changed by the final Phase 9.13 session are:

- `skill/vicaya-0-scope/SKILL.md`
- `skill/vicaya-1-gather/SKILL.md`
- `kamma/threads/20260602_vicaya-staged-skills-section-router/spec.md`
- `kamma/threads/20260602_vicaya-staged-skills-section-router/plan.md`
- `kamma/threads/20260602_vicaya-staged-skills-section-router/handoff.md`

Ignored run-state file changed by the final Phase 9.13 session:

- `data/scratch/vicikiccha-hindrance-vs-fetter.md`

## Current Staged Semantics

`vicaya-0-scope` now decides whether a staged run is extensive.

If it records `stage-1-context-plan`, `stage-2-context-plan`, or
`stage-3-context-plan` in scratch, those plans are binding for later staged
skills unless the user explicitly opts out before Stage 1 begins and a
`context-plan-opt-out` note is logged in scratch.

Later staged skills must not re-decide whether the planned split is optional:

- `vicaya-1-gather`: if `stage-1-context-plan` exists, run exactly one next
  grouped source block, then hard stop at the planned safe boundary. The
  default grouped split is four Stage 1 sessions: Phase 1 plus Phase 2
  root-canon mūla/sutta research; Phase 2 commentary/exegesis only; Phase 2.5
  plus Phase 3 plus Phase 3b when applicable; and Phase 4a plus Phase 4b plus
  Phase 4c. A prior hard stop is only a handoff checkpoint, not completion of
  the whole Stage 1 plan. Heavy Phase 2 can pause after root-canon mūla/sutta
  research with a scratch in-progress note before commentary/exegesis; Phase 2
  gate is written only after all canonical Phase 2 obligations are complete.
- `vicaya-2-synthesize-review`: if `stage-2-context-plan` exists, run only the
  next planned synthesis/review pass, then hard stop at the planned scratch
  checkpoint or canonical gate. The default split is two Stage 2 sessions:
  Phase 5 entry verification, scratch review, source/angle checks, Devil's
  Advocate preparation, bibliography/source allocation review, and a concise
  Phase 5 drafting plan before full drafting; then Phase 5 drafting/integration
  plus Phase 5 gate and Phase 6 review plus Phase 6 gate.
- `vicaya-3-complete`: if `stage-3-context-plan` exists, run only the next
  planned completion pass, then hard stop at the safe completion boundary. For
  extensive notes, the default planned split is exactly three runs:
  1. writer brief plus `## Question`, `## Findings`, Canon Evidence, and
     Commentary Evidence;
  2. remaining evidence/support sections plus frontmatter canon-ref
     confirmation and completion audit, stopping before vault write;
  3. vault write, validation, PDF, Phase 7 gate, note/run-report sync, final
     report, and self-improvement loop. The vault receives only the complete
     audited note.

Model-tier recommendations do not override a recorded context plan.

## Existing Runs Patched For Phase 9.14

The user's two unfinished research runs now have Phase 0 scratch supersession
notes for the latest fixed hard-stop logic. These notes were added with the
canonical `scratch-log` helper and do not change any completed gates or source
evidence.

`data/scratch/papanca-canon-usage.md` now has:

- `stage-2-context-plan phase-9.14-supersedes`
- `stage-3-context-plan phase-9.14-supersedes`

Current gate state by read-only marker audit: Phase 5 is gated; Phase 6 is not
gated. There are older helper logs inside the Phase 6 section, but no
`PHASE 6 EXIT GATE`; do not treat those logs as a completed cross-check. This
run stopped after Phase 5 under the older Stage 2 split. Next research command:

```text
/vicaya-2-synthesize-review papanca-canon-usage
```

Expected next work: run canonical Phase 6 cross-check and `scratch-gate 6`,
then hand off to `vicaya-3-complete`. Do not repeat Phase 5, and do not keep
using the older rule that every extensive Stage 2 run must hard-stop after a
full Phase 5 gate.

When this run reaches Stage 3, use the Phase 9.14 three-run completion split:
Run 1 writes `## Question`, `## Findings`, Canon Evidence, and Commentary
Evidence into `data/scratch/papanca-canon-usage.phase7-draft.md`; Run 2 writes
the remaining draft sections and audits before vault write; Run 3 writes only
the complete audited note to the vault, validates, gates, syncs, reports, and
runs self-improvement.

`data/scratch/vicikiccha-hindrance-vs-fetter.md` now has:

- `stage-1-context-plan phase-9.14-supersedes`
- `stage-2-context-plan phase-9.14-supersedes`
- `stage-3-context-plan phase-9.14-supersedes`

Current gate state by read-only marker audit: Phase 3 is gated; Phase 3b, 4,
4b, and 4c are not gated. Next research command:

```text
/vicaya-1-gather vicikiccha-hindrance-vs-fetter
```

Expected next work: follow routed canonical skip rules for thematic Phase 3b,
then run the final Stage 1 block as one grouped invocation: Phase 4a web,
Phase 4b YouTube when applicable, and Phase 4c WisdomLib; stop after the Phase
4c gate and hand off to `vicaya-2-synthesize-review`. Do not split Phase 4a,
Phase 4b, and Phase 4c into separate resumes because of older notes.

When `vicikiccha-hindrance-vs-fetter` reaches Stage 2 and Stage 3, use the
same Phase 9.14 Stage 2 two-pass drafting-plan/checkpoint split and Stage 3
three-run draft/vault-write split described above.

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
Phase 9.14 rebalanced fixed three-run split documented above and in `plan.md`.

## Validation Run

Checks run during this session:

- `rg` checks confirmed the active staged skill files contain the Phase 9.14
  `1 + 4 + 2 + 3` fixed hard-stop redistribution and no active adaptive
  context-usage control wording.
- `rg` checks confirmed the active `vicaya-0-scope` and `vicaya-1-gather`
  files contain the Phase 9.14 four-pass Stage 1 split:
  1. Phase 1 plus Phase 2 root-canon mūla/sutta research;
  2. Phase 2 commentary/exegesis only;
  3. Phase 2.5 plus Phase 3 plus Phase 3b;
  4. Phase 4a plus Phase 4b plus Phase 4c.
- `rg` checks confirmed the active `vicaya-2-synthesize-review` file contains
  the two-pass Stage 2 split: Phase 5 drafting-plan checkpoint, then Phase 5
  drafting/gate plus Phase 6 review/gate.
- `rg` checks confirmed the active `vicaya-3-complete` file contains the
  rebalanced three-run Stage 3 split: Run 1 includes `## Question`,
  `## Findings`, Canon Evidence, and Commentary Evidence; Run 2 writes the
  remaining sections and audits before vault write; Run 3 handles vault
  write/validation/PDF/sync/final report/self-improvement.
- `git diff --check -- skill/vicaya-0-scope/SKILL.md
  skill/vicaya-3-complete/SKILL.md
  kamma/threads/20260602_vicaya-staged-skills-section-router/spec.md
  kamma/threads/20260602_vicaya-staged-skills-section-router/plan.md` passed.
- `git diff --check -- skill/vicaya-0-scope/SKILL.md
  skill/vicaya-1-gather/SKILL.md
  kamma/threads/20260602_vicaya-staged-skills-section-router/spec.md
  kamma/threads/20260602_vicaya-staged-skills-section-router/plan.md
  kamma/threads/20260602_vicaya-staged-skills-section-router/handoff.md
  data/scratch/vicikiccha-hindrance-vs-fetter.md` passed.
- `git diff -- skill/vicaya/SKILL.md` returned no diff, confirming the
  monolithic-skill Phase 5 self-improvement hunk is not present.
- `rg` confirmed `phase-9.14-supersedes` entries were written to
  `data/scratch/papanca-canon-usage.md` and
  `data/scratch/vicikiccha-hindrance-vs-fetter.md`.
- A read-only gate-marker audit confirmed `papanca-canon-usage` has Phase 5
  gated and no Phase 6 gate; the next work is Phase 6 cross-check/gate.
- A read-only gate-marker audit confirmed
  `vicikiccha-hindrance-vs-fetter` has Phase 3 gated and no Phase 3b/4/4b/4c
  gates; the next work is the grouped Phase 4a/4b/4c source block after any
  routed thematic Phase 3b skip.
- `git check-ignore -v` confirmed the scratch files under `data/scratch/` are
  intentionally ignored run state. Scratch updates must be reported explicitly
  because they do not appear in normal `git status --short` output.

## Failed Attempts / Workarounds

- The first attempt to patch all Phase 9.13 files in one `apply_patch` call
  failed because the handoff paragraph used as context no longer matched the
  file exactly. No files were changed by that failed patch. I reran smaller
  patches against the current text.
- The first attempt to append to scratch failed because `uv` tried to use
  `/Users/deva/.cache/uv`, which is outside the sandbox:
  `failed to open file /Users/deva/.cache/uv/sdists-v9/.git`.
- Rerun succeeded with:

```text
UV_CACHE_DIR=/private/tmp/uv-cache
VICAYA_SCRATCH=/Users/deva/Documents/dps/vicaya/data/scratch/moha-amoha-avijja-vijja.md
```

## Remaining Work For This Kamma Thread

- Account for any new user-reported issues from the live staged-skill test run
  before finalization.
- If resuming `papanca-canon-usage`, run `vicaya-2-synthesize-review` for
  Phase 6 cross-check/gate, then hand off to `vicaya-3-complete`.
- If resuming `vicikiccha-hindrance-vs-fetter`, run `vicaya-1-gather` for the
  remaining grouped Stage 1 block: routed Phase 3b skip if applicable, then
  Phase 4a/4b/4c and Phase 4c gate.
- If no further staged-skill design changes are made, proceed toward
  `/kamma:4-finalize`. `review.md` is currently `PASSED`; rerun review or a
  focused review check first only if strict finalization should cover the
  post-review Phase 9.15 handoff/scratch sync.

## Known Caveats

- The thread history still contains earlier Phases 3-6 literal-router text.
  Later Phases 9.5-9.15 intentionally supersede the pure-router constraint only
  for bounded staged context controls and scratch/handoff synchronization.
