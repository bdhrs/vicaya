# Spec (draft)

## GitHub Reference
PR #29 — "Vicaya pre skill" (branch `vicaya-pre-skill` → `main`), reviewed by `bdhrs` (changes requested).

## Overview
Branch `vicaya-pre-skill` adds the `/vicaya-pre` skill but was cut before PR #28 merged. PR #28 deleted the staged-router subskills (`vicaya-0-scope`, `vicaya-1-gather`, `vicaya-2-synthesize-review`, `vicaya-3-complete`) and stripped their references from `README.md`. The reviewer requested three fixes before this PR can merge: resolve the merge conflict (don't resurrect deleted staged-skill references), fix a macOS-only command for portability, and complete the OpenCode integration to match how `vicaya-improve` is wired up. This thread merges `origin/main` into `vicaya-pre-skill`, applies the three fixes, and leaves the branch ready to push/merge (push itself is out of scope — user pushes manually).

## What it should do
1. **Resolve merge conflict, favoring main's cleanup.** Merge `origin/main` into `vicaya-pre-skill`. Resolve `README.md` so:
   - All `vicaya-0-scope`/`vicaya-1-gather`/`vicaya-2-synthesize-review`/`vicaya-3-complete` references stay deleted (as on `main`), including the "if you use staged runs, symlink the staged sibling folders too…" prose paragraphs (currently reintroduced near README.md lines ~44-46 and ~302-308 on this branch).
   - `vicaya-pre` is added to README wherever `vicaya-improve` appears (symlink loops for OpenCode/Antigravity/Claude Code, the manual symlink/verification sections, and the directory tree comment), matching the pattern this branch already uses for `vicaya-pre` minus the staged-skill entries.
   - The OpenCode command loop (`for cmd in …` near line ~54 on main) reads exactly `vicaya vicaya-improve vicaya-pre` — no staged-skill entries.
   - Verify via `rg -n "vicaya-0-scope|vicaya-1-gather|vicaya-2-synthesize|vicaya-3-complete" README.md` → no output.

2. **Fix portability bug in `skill/vicaya-pre/SKILL.md` Step 0.** Replace the macOS-only:
   ```bash
   open -a Obsidian && sleep 5
   ```
   with the OS-branched pattern already used in `skill/vicaya/SKILL.md:36-40`:
   - Linux: `setsid xdg-open "obsidian://" >/dev/null 2>&1 &`
   - macOS: `open -a Obsidian`
   - Windows: `start "" "obsidian://"`
   - Keep a ~5s wait after launching, for all variants. Follow the same instructive framing as `skill/vicaya/SKILL.md` point 4 (launch only if a `search-vault` command fails with "app may not be running"; never bare `obsidian`).

3. **Complete OpenCode integration for `vicaya-pre`.**
   - Add `config/opencode/commands/vicaya-pre.md`, mirroring `config/opencode/commands/vicaya-improve.md`'s frontmatter/body pattern (a `description:` front-matter line summarizing the skill, then a one-line body: `Load the skill at ~/.agents/skills/vicaya-pre/SKILL.md and execute it.`). Use the existing `vicaya-pre` `SKILL.md` description for the front matter.
   - Ensure `vicaya-pre` appears in the README's OpenCode command symlink loop (the `for cmd in …` line) alongside `vicaya` and `vicaya-improve` (this is the same edit as in item 1's command-loop fix — listed separately here because it's the reviewer's fix 3b, but implemented as one edit to the same line).

## Assumptions & uncertainties
- The merge will be a real `git merge origin/main` (not rebase) since the reviewer's suggested fix snippet uses `git merge origin/main`. If conflicts appear outside `README.md`, resolve in favor of `main`'s deletions plus this branch's `vicaya-pre` additions, using the same principle (staged skills stay gone, `vicaya-pre` stays).
- `config/opencode/commands/vicaya-pre.md` doesn't exist yet on this branch — confirmed via `ls config/opencode/commands/`. It will be a new file.
- Test baseline: `uv run -m pytest -q` should show 227 passing with 7 pre-existing/environmental failures in `test_research_sources.py` (missing `dpd-db` sibling repo, fails on `main` too). These 7 are out of scope and should be ignored, not fixed.
- Per user direction, this thread only prepares local commits on `vicaya-pre-skill`; it does not push to `origin/vicaya-pre-skill` or otherwise touch GitHub/PR #29 (no auto-push, no PR comment, no re-requesting review). The user will push manually.
- No other files are assumed to need changes beyond `README.md`, `skill/vicaya-pre/SKILL.md`, and the new `config/opencode/commands/vicaya-pre.md`.

## Constraints
- Don't reintroduce any reference to the deleted staged-router skills.
- Don't hardcode a single OS in the Obsidian launch step.
- Match existing patterns exactly (`vicaya-improve`'s command-stub style, `skill/vicaya/SKILL.md`'s OS-branch style) rather than inventing new conventions.
- No push, no PR comment, no commit beyond what's needed for these fixes.

## How we'll know it's done
- `git status` on `vicaya-pre-skill` shows the merge completed (no conflict markers) and fix commits applied.
- `rg -n "vicaya-0-scope|vicaya-1-gather|vicaya-2-synthesize|vicaya-3-complete" README.md` returns nothing.
- `skill/vicaya-pre/SKILL.md` Step 0 uses the OS-branched launch pattern, no longer assumes macOS.
- `config/opencode/commands/vicaya-pre.md` exists and mirrors `vicaya-improve.md`'s pattern.
- README's OpenCode `for cmd in …` loop includes `vicaya-pre`.
- `uv run -m pytest -q` passes at the same baseline as `main` (227 pass; the 7 pre-existing `test_research_sources.py` failures are unchanged/ignored).

## What's not included
- Pushing the branch or commenting on/re-requesting review for PR #29.
- Any change to `vicaya-improve`, `vicaya`, or other skills beyond what's needed to mirror their existing patterns.
- Fixing the 7 pre-existing `test_research_sources.py` failures.
