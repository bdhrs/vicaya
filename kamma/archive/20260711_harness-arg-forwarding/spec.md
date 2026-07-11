# Spec: harness-arg-forwarding — fix dropped question arguments in vicaya-quick / vicaya-pre across Pi and OpenCode

## Overview
`/vicaya-quick <question>` and `/vicaya-pre <topic>` silently drop the user's
typed argument in two harnesses: Pi coding agent (bare `/vicaya-quick <q>`
form) and OpenCode. The question text never reaches the agent, so the skill
runs with no idea what to research.

Root cause, confirmed by reading source:

- **Pi**: `~/.pi/agent/prompts/vicaya-quick.md` is symlinked straight to
  `skill/vicaya-quick/SKILL.md`. Pi's bare `/vicaya-quick <question>` form goes
  through its **prompt-template** engine (`substituteArgs()` in
  `@earendil-works/pi-agent-core`), which only replaces literal `$1`, `$2`,
  `$@`, `$ARGUMENTS`, `${@:N}` tokens in the template body. SKILL.md has none
  of these, so the typed question is discarded — the expanded prompt is just
  the SKILL.md text. (Pi's *other* invocation form, `/skill:vicaya-quick
  <question>`, appends `User: <args>` and is unaffected — confirmed against
  Pi's own docs.)
- **OpenCode**: `config/opencode/commands/vicaya.md` was written correctly —
  it declares `args: [{name: question, required: true}]` and interpolates
  `{{args}}` into the body. Its siblings `vicaya-quick.md` and `vicaya-pre.md`
  were never given this treatment (visible in `git show ffb6a8b` and the
  current file contents) — both are just "Load the skill... and execute it,"
  no argument forwarding. `vicaya-improve.md` correctly takes no argument and
  needs no change.

## What it should do

1. **Fix OpenCode** (`config/opencode/commands/`):
   - `vicaya-quick.md`: add `args: [{name: question, description: The research question, required: true}]` frontmatter and interpolate `{{args}}` into the body, mirroring `vicaya.md`.
   - `vicaya-pre.md`: same fix, with `name: topic`.
   - `vicaya.md`, `vicaya-improve.md`: no change (already correct).

2. **Fix Pi** (new tracked stubs + symlink change):
   - Add `config/pi/prompts/vicaya.md`, `vicaya-quick.md`, `vicaya-pre.md`,
     `vicaya-improve.md` — small stub files (not the full SKILL.md) with
     `description` + `argument-hint` frontmatter, whose body says to load the
     real skill at `skill/<name>/SKILL.md` and execute it with the question
     `$ARGUMENTS` (omit the argument sentence for `vicaya-improve`, which takes
     none).
   - Re-point `~/.pi/agent/prompts/<name>.md` from a direct symlink-to-SKILL.md
     to a symlink-to-the-new-stub, for all four skills, on this machine.
   - `~/.pi/agent/skills/<name>` symlinks (the `/skill:name` mechanism) are
     unaffected and stay pointed at the real skill directories — they already
     forward arguments correctly.

3. **Document Pi in the README** alongside the existing OpenCode / Antigravity
   / Claude Code setup blocks: skill symlinks (unchanged pattern) plus the new
   prompt-stub symlinks, so a fresh machine setup doesn't silently reproduce
   this bug.

## Drift note (discovered mid-implementation)
`justfile`'s `sync` recipe (`justfile:37-50`) is the actual mechanism the user
runs to wire skills into Pi (advertised in `just --list`: "re-run to pick up
newly added skills"). It unconditionally symlinks
`~/.pi/agent/prompts/<name>.md` straight at each skill's `SKILL.md` for every
directory under `skill/` — including `align`, which was outside the original
scope. Any `just sync` run undoes the Pi fix. This must be fixed at the
recipe level (prefer a `config/pi/prompts/<name>.md` stub when one exists),
not just by re-running `ln -sf` by hand, or the bug returns on the next sync.
`align` (`/align <phrase>`) gets the same stub treatment as a result, since
it's walked by the same loop and has the identical class of bug.

## Assumptions & uncertainties
- Pi's `$ARGUMENTS` token (all args, space-joined) is the right analogue for
  OpenCode's `{{args}}` — both forward the full typed argument string
  unmodified. Confirmed by reading Pi's `docs/prompt-templates.md` and its
  `substituteArgs()` source directly.
- `config/pi/prompts/` is a new directory in this repo — chosen to mirror
  `config/opencode/commands/` naming (each subfolder named after the harness,
  containing that harness's command/prompt file convention).
- The stale `kamma/threads/20260620_vicaya-quick` thread (all tasks `[x]` but
  never finalized/archived, no `review.md`) is out of scope for this thread —
  not touched here.
- No GitHub issue is tied to this work.

## Constraints
- Don't touch `.env`/`.ini` files (global rule).
- Pi stub files must not duplicate SKILL.md content — they delegate to it, per
  the existing OpenCode command-file pattern in this repo.
- Symlink changes under `~/.pi/agent/` are on this machine only, outside the
  repo; they're an "activation" step like Phase 3 of the
  `20260620_vicaya-quick` thread precedent (which created the live
  `~/.claude/skills/vicaya-quick` symlink).

## How we'll know it's done
- `grep -c "args:" config/opencode/commands/vicaya-quick.md config/opencode/commands/vicaya-pre.md` each show the new `args` block; `grep -q "{{args}}"` succeeds on both.
- `test -f config/pi/prompts/vicaya.md` (and the other three) succeed.
- Each new Pi stub contains `$ARGUMENTS` (except `vicaya-improve.md`, which shouldn't).
- `readlink ~/.pi/agent/prompts/vicaya-quick.md` (and siblings) point at the new repo stub files, not directly at `SKILL.md`.
- `readlink ~/.pi/agent/skills/vicaya-quick` (and siblings) are unchanged.
- README shows a Pi setup block analogous to the OpenCode one.
- Manual smoke test: in Pi, `/vicaya-quick what is anatta` (bare form) actually carries the question into the expanded prompt (visible before submission, or verified by the agent's first message referencing the question).

## What's not included
- No change to `/skill:vicaya-quick <question>` behavior in Pi (already correct).
- No change to Claude Code or Antigravity (`agy`) — they don't use a
  templated-argument slash-command mechanism; the model receives the typed
  text verbatim alongside skill invocation.
- No finalize/archive of the stale `20260620_vicaya-quick` thread.
- No change to `skill/*/SKILL.md` content itself.
