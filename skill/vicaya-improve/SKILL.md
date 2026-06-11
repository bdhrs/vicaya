---
name: vicaya-improve
description: Process accumulated run retrospectives in runs/ into the prioritized improvement backlog (runs/TODO.md), apply channel tuning, archive processed runs, and present the top 5 issues for the user to pick one to work on. Invoke when the user types /vicaya-improve or asks to "process the runs", "triage run feedback", or "what should we improve next".
---

# Vicaya improvement loop

Turn run retrospectives into prioritized skill improvements. Every `/vicaya`
run writes a retrospective to `runs/<timestamp>.md`; this skill compiles them
into `runs/TODO.md`, archives them, and hands the user a ranked shortlist.

All paths are relative to the vicaya project root (the directory containing
`runs/` and `skill/`).

## Phase 1 — Inventory

List unprocessed runs: every `runs/*.md` except `TODO.md`. If there are none,
report "no unprocessed runs", show the current top 5 from `runs/TODO.md`
(Phase 6), and stop.

Read `runs/TODO.md` in full before extracting anything — you need the Done
table and the existing issue list to dedupe against.

## Phase 2 — Extract (batched, compaction-safe)

Create a working file `temp/run-triage-<YYYYMMDD>.md`. Process runs in
batches of ~15 files. For each batch, read the files and append to the
working file, then move to the next batch. Never hold extraction results
only in context.

From each run, extract:

- **Findings**: every Retrospective bullet with `Scope: global`. Record as
  `- <run-id> [TAG] <one-line summary of evidence + proposed fix>`.
  Skip `Scope: local` items and empty bullets ("Evidence: nothing").
  `[POSITIVE]` globals go under a separate `## Working well` heading —
  they are preserve-signals, not issues.
- **Changes already made**: if "What I changed this run" is not "nothing",
  record it — it may already resolve findings from other runs.
- **Channel tuning**: any promote/demote action, and the names of new
  probationary channels (to tally repeat sightings).

Runs with non-standard format (older or hand-named files): extract whatever
maps onto the categories above; don't force the template.

## Phase 3 — Merge into runs/TODO.md

**Staleness gate first.** The vicaya skill changes fast — features get
removed, renamed, or rewritten between runs, so old findings are often
about code that no longer exists. Before merging anything:

1. Run `git log --oneline --since=<date of oldest unprocessed run>` to see
   what changed while these runs accumulated.
2. For each finding, check the component it names against the current
   codebase (helper subcommands, SKILL.md sections, tools/). If the
   component was removed or rewritten after the run's date, **drop the
   finding** with a one-line note in the working file ("stale: Calibre
   removed in 888be14"). If a fix commit postdates the run, drop it too —
   unless a *newer* run re-reports it, which means the fix didn't take.
3. Apply the same check to existing Remaining items in TODO.md whose
   evidence is entirely older than a relevant refactor: mark them
   `(stale — verify)` or drop with a note rather than letting dead issues
   inflate the backlog.

Recency outranks raw frequency: one finding from yesterday's run beats the
same complaint in five runs that predate a rewrite of that area.

Then, for each surviving finding, in order:

1. **Matches a Done item** → check the run's date against when the fix
   landed. If the run postdates the fix, this is a **regression**: move the
   issue back to Remaining at High severity, tagged `REGRESSION`, with the
   run IDs as evidence. If it predates the fix, drop it.
2. **Matches a Remaining item** → append the run ID to its evidence and
   bump its count.
3. **New** → add it under the right severity section with the next free
   issue number.

Every Remaining issue must carry an evidence line:
`(seen in N runs: <id>, <id>, …)` — list at most 5 IDs, then `+K more`.
Frequency is the primary priority signal within a severity band.

Severity guide: High = wrong results reach the user or a phase cannot
complete; Medium = workaround exists but costs time/context every run;
Low = cosmetic, rare, or environment-specific.

Add `[POSITIVE]` patterns worth keeping to a short `## Working well —
preserve` section (create it if absent; merge duplicates).

Update the "Notes for the next session" section if the new evidence changes
the picture; otherwise leave it.

## Phase 4 — Apply channel tuning

In `data/youtube_channels.md`:
- Apply every explicit promote/demote action from the runs.
- For probationary channels seen in 3+ runs with consistently relevant
  results, propose promotion to the user later (note it in the Phase 6
  summary); don't auto-promote on sightings alone.

## Phase 5 — Archive

Only after `runs/TODO.md` is written and saved: `mv` every processed run
file into `runs/processed/`. Use plain `mv`, not git commands. Do not move
`TODO.md`. Delete the `temp/run-triage-*.md` working file.

## Phase 6 — Present top 5 and pick

Rank the Remaining issues by: severity band first, then run-count weighted
toward recent runs (post-refactor reports count full, older ones less), with
a tie-break bonus for quick wins (small, self-contained fixes). Issues
marked `(stale — verify)` rank below everything verified. Present a
table:

| # | Issue | Severity | Runs | Why now |

Below the table, report in one or two lines: runs processed, new issues,
regressions, channel-tuning actions applied.

Then ask the user to pick one (AskUserQuestion, top 4 as options with the
"Why now" as description; the 5th and the rest are reachable via Other).
Work on the chosen issue in the normal way. If the fix touches
`skill/vicaya/SKILL.md`, the canonical-skill sync gate below is part of the
fix — not an optional follow-up.

## Canonical-skill sync gate

`skill/vicaya/SKILL.md` is canonical; the staged skills (`vicaya-0-scope`
… `vicaya-3-complete`) are section routers into it (kamma/project.md,
Maintenance). Each router's Route List names exact headings, and a routed
section is read only up to the next same-or-higher-level heading (or the
next separately routed one). Any fix that edits `skill/vicaya/SKILL.md` is
incomplete until this audit passes:

1. **Heading added** → content under an unlisted heading is invisible to
   staged runs, even when it sits between two routed headings. Decide which
   stage(s) own it and add it to those Route Lists. If the new content is
   load-bearing for a stage (a gate requirement, a hard rule), also pin it
   with a guard test in `tests/test_skill_routes.py`.
2. **Heading renamed or removed** → update every Route List that names it.
3. **Behavioral text stays canonical** — never copy rules into a router;
   routers carry only route lists, stage boundaries, and context-break
   guards.
4. Run `uv run -m pytest tests/test_skill_routes.py`. It catches dead route
   entries (routed heading no longer in SKILL.md), **not** new unrouted
   headings — check additions by hand against each router's extraction
   rule.

## Phase 7 — Close the loop (automatic, do not wait to be asked)

Finishing the fix INCLUDES the TODO bookkeeping and, for canonical skill
edits, the sync gate above. As soon as the fix is implemented and its tests
pass — before reporting completion to the user — update `runs/TODO.md` in
the same breath:

1. Move the issue's row from Remaining to the Done table, with the commit
   subject (use the proposed subject if not yet committed).
2. If only part of the issue was fixed, move the fixed part to Done and
   leave the residue as a new numbered issue with the unfixed sub-points
   and their original run-ID evidence.
3. Re-read "Notes for the next session" and fix any line that still
   describes the issue as pending.

The completion report to the user must mention that TODO.md was updated.
Never end the session with a fixed issue still listed under Remaining.

The completion report must end with a ready-to-use commit block (do NOT
run any git commands — the user commits):

1. **Commit message** — one short GitHub-friendly subject line,
   conventional-commit style (`fix:`/`feat:`/`docs:` …, ≤72 chars,
   imperative mood). Use the same subject recorded in the Done table.
2. **Commit description** — bullet points, as many as needed. Each bullet
   ≤72 characters so it never wraps, one clause only — no "and"-chains,
   semicolons, or parentheticals. Go down the page, not across it. Include
   before/after numbers only if measured.
3. **Changed files** — a plain list of every file created, modified, or
   moved this session (including `runs/TODO.md` and archived runs).

## Style rules for TODO.md

- Keep the existing structure: `## Done` table, `## Remaining — prioritized`
  with High/Medium/Low subsections, `## Working well — preserve`,
  `## Notes for the next session`.
- One issue = one bold-numbered paragraph, concrete fix suggestion included
  when the runs propose one.
- Never delete an issue without moving it to Done or noting why it was
  dropped (e.g. "predates fix", "duplicate of #N").
