# Plan: Move vicaya-pre into repo, make portable, match symlink convention

## Architecture Decisions
- New skill file lives at `skill/vicaya-pre/SKILL.md`, matching the layout
  of the other 6 vicaya-family skills (auto-discovered by Claude Code /
  OpenCode / Antigravity from any `skill/<name>/SKILL.md`, no manifest
  needed).
- The only content change vs. the current global copy is removing the
  hardcoded `cd ~/Documents/dps/vicaya` line in Step 1 of the skill body,
  per the project's documented rule (`skill/vicaya/SKILL.md`: "Agents do
  not hard-code paths; use the helpers and CLI"). Nothing else in the
  skill body changes.
- README is updated to add `vicaya-pre` to the **skill**-symlink loops
  only, not the slash-command loops — there is no
  `config/opencode/commands/vicaya-pre.md`, and creating one is out of
  scope for this thread.
- We do not touch the live `~/.agents`, `~/.gemini`, or `~/.claude`
  directories. Current real state (verified during planning):
  - `~/.agents/skills/vicaya-pre/` is a **real directory** containing the
    actual `SKILL.md` (this is the thing to retire).
  - `~/.claude/skills/vicaya-pre` and `~/.gemini/skills/vicaya-pre` are
    symlinks pointing at `~/.agents/skills/vicaya-pre` (not at the repo).
  - This differs from `vicaya`/`vicaya-improve`, where each agent's skills
    dir symlinks **directly** to `skill/<name>` in this repo.
  Removing a real directory and re-pointing live symlinks outside the repo
  is destructive and machine-specific, so the plan only *produces the
  exact commands* (Phase 3) — it does not execute them.

---

## Phase 1: Add skill to repo and fix portability

- [x] Task 1.1: Create `skill/vicaya-pre/SKILL.md`
  - Read `~/.agents/skills/vicaya-pre/SKILL.md` (this is the real file —
    not `~/.claude/skills/vicaya-pre`, which is a symlink chain to the
    same content but use the real path for clarity).
  - Create the directory `skill/vicaya-pre/` if it doesn't exist.
  - Write `skill/vicaya-pre/SKILL.md` with **identical content**, except:
    in the fenced bash block that currently reads:
    ```bash
    cd ~/Documents/dps/vicaya
    uv run tools/research_sources.py search-vault "<term>" --folder Vicaya --limit <N>
    ```
    delete the `cd ~/Documents/dps/vicaya` line entirely, leaving just:
    ```bash
    uv run tools/research_sources.py search-vault "<term>" --folder Vicaya --limit <N>
    ```
    Do not change anything else — frontmatter, wording, other code blocks,
    and the `rg` fallback commands stay exactly as-is.
  → verify: `diff <(grep -v '^cd ~/Documents/dps/vicaya$' ~/.agents/skills/vicaya-pre/SKILL.md) skill/vicaya-pre/SKILL.md` produces no output (i.e. the new file equals the old one with only that one line removed)

- [x] Task 1.2: Confirm the path is fully gone
  → verify: `grep -n "Documents/dps/vicaya" skill/vicaya-pre/SKILL.md` returns no matches (exit code 1 / empty output)

---

## Phase 2: Update README symlink instructions

- [x] Task 2.1: Add `vicaya-pre` to the quick "## Setup" section's skill loops (around README.md lines 49–73)
  Make exactly 3 edits, one per agent code block. In each, insert
  `vicaya-pre` into the `for skill in ...` list immediately after
  `vicaya-improve`. Do **not** touch the separate `for cmd in ...` loop in
  the OpenCode block — leave it unchanged.

  1. OpenCode block — old line:
     `for skill in vicaya vicaya-improve vicaya-0-scope vicaya-1-gather vicaya-2-synthesize-review vicaya-3-complete; do`
     new line:
     `for skill in vicaya vicaya-improve vicaya-pre vicaya-0-scope vicaya-1-gather vicaya-2-synthesize-review vicaya-3-complete; do`
     (this exact line appears 3 times in the file — for the OpenCode skill
     loop, the Antigravity loop, and the Claude Code loop — since all
     three currently use the identical skill list. Replace **all three**
     occurrences with the new line; this is fine, since the desired result
     is the same updated list in every block. Use `replace_all` if your
     edit tool supports it, otherwise repeat the same single-occurrence
     edit 3 times.)

  → verify: `grep -c "for skill in vicaya vicaya-improve vicaya-pre vicaya-0-scope" README.md` returns `3`, and `grep "for cmd in" README.md` does not contain `vicaya-pre`

- [x] Task 2.2: Add `vicaya-pre` to the detailed walkthrough's "### 5 — Symlink the skill" section (around README.md lines 302–340)
  Three separate single-occurrence edits (these lines are NOT duplicated
  elsewhere, unlike Task 2.1):

  1. After the line `ln -sf "$(pwd)/skill/vicaya-improve" ~/.agents/skills/vicaya-improve`
     insert a new line directly below it:
     `ln -sf "$(pwd)/skill/vicaya-pre" ~/.agents/skills/vicaya-pre`

  2. After the line `ln -sf "$(pwd)/skill/vicaya-improve" ~/.claude/skills/vicaya-improve`
     insert a new line directly below it:
     `ln -sf "$(pwd)/skill/vicaya-pre" ~/.claude/skills/vicaya-pre`

  3. In the "**Verification:**" code block:
     - after `ls ~/.agents/skills/vicaya-improve/SKILL.md` insert:
       `ls ~/.agents/skills/vicaya-pre/SKILL.md`
     - after `ls ~/.claude/skills/vicaya-improve/SKILL.md` insert:
       `ls ~/.claude/skills/vicaya-pre/SKILL.md`

  → verify: `sed -n '300,345p' README.md` shows `vicaya-pre` symlink lines in both the `~/.agents/skills` and `~/.claude/skills` blocks, and in both verification `ls` groups

---

## Phase 3: Manual cleanup instructions + handoff

- [x] Task 3.1: Write `kamma/threads/20260618_move_vicaya_pre_skill/handoff.md`
  Create the file with this content (context sentence, then one fenced
  bash block with exactly these 7 commands in this order):

  > The old `vicaya-pre` skill lives at `~/.agents/skills/vicaya-pre/` as a
  > **real directory** (not a symlink) — `~/.claude/skills/vicaya-pre` and
  > `~/.gemini/skills/vicaya-pre` are symlinks pointing at it. Remove the
  > real directory and the two symlinks first, then re-create all three as
  > direct symlinks to the repo (matching how `vicaya`/`vicaya-improve`
  > are set up). Open a fresh agent session afterward — skill discovery
  > happens at session start.

  ```bash
  rm ~/.claude/skills/vicaya-pre
  rm ~/.gemini/skills/vicaya-pre
  rm -rf ~/.agents/skills/vicaya-pre
  ln -sf "/Users/deva/Documents/dps/vicaya/skill/vicaya-pre" ~/.agents/skills/vicaya-pre
  ln -sf "/Users/deva/Documents/dps/vicaya/skill/vicaya-pre" ~/.gemini/skills/vicaya-pre
  ln -sf "/Users/deva/Documents/dps/vicaya/skill/vicaya-pre" ~/.claude/skills/vicaya-pre
  ls -la ~/.agents/skills/vicaya-pre ~/.gemini/skills/vicaya-pre ~/.claude/skills/vicaya-pre
  ```

  → verify: `test -f kamma/threads/20260618_move_vicaya_pre_skill/handoff.md && grep -q "rm -rf ~/.agents/skills/vicaya-pre" kamma/threads/20260618_move_vicaya_pre_skill/handoff.md` succeeds

- [x] Task 3.2: Print the same command block to the user in chat
  In your response for this task, output the exact fenced bash block from
  Task 3.1 verbatim (all 7 commands), preceded by one sentence: "Run these
  manually to retire the old global copy and switch to the repo-backed
  skill:". This is in addition to the file — the user asked for it to be
  visibly printed, not just stored.
  → verify: manual — confirm your own chat response in this task contains the fenced bash block verbatim

---

## Phase 4: End-of-phase verification

- [x] Task 4.1: Full verification pass
  Run all of the following and confirm every check passes:
  - `test -f skill/vicaya-pre/SKILL.md && echo OK`
  - `grep -n "Documents/dps/vicaya" skill/vicaya-pre/SKILL.md || echo CLEAN` → must print `CLEAN`
  - `grep -c "for skill in vicaya vicaya-improve vicaya-pre vicaya-0-scope" README.md` → must print `3`
  - `grep -c "ln -sf \"\$(pwd)/skill/vicaya-pre\"" README.md` → must print `2`
  - `grep -c "ls .*skills/vicaya-pre/SKILL.md" README.md` → must print `2`
  - `test -f kamma/threads/20260618_move_vicaya_pre_skill/handoff.md && echo OK`
  - `grep -q "ln -sf \"/Users/deva/Documents/dps/vicaya/skill/vicaya-pre\"" kamma/threads/20260618_move_vicaya_pre_skill/handoff.md && echo OK`
  If any check fails, fix the corresponding task and re-run before marking
  this task complete.
  → verify: all seven checks above produce their expected output with no errors
