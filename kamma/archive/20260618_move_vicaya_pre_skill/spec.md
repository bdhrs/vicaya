# Spec: Move vicaya-pre into repo, make portable, match symlink convention

## Overview
`vicaya-pre` currently exists only as a real (non-symlinked) directory at
`~/.agents/skills/vicaya-pre/`, with `~/.claude/skills/vicaya-pre` and
`~/.gemini/skills/vicaya-pre` symlinked to it. This is inconsistent with
`vicaya` and `vicaya-improve`, which are version-controlled in this repo at
`skill/<name>/` and symlinked *directly* from each agent's skills directory
to the repo (per README's "Symlink the skill" sections). This thread:
1. Adds `skill/vicaya-pre/SKILL.md` to the repo, with the one hardcoded
   path removed so it works for any user who clones the repo.
2. Updates `README.md` so `vicaya-pre` is documented in the symlink setup
   instructions alongside `vicaya-improve`.
3. Produces exact manual commands (not run automatically — see below) for
   the user to remove the old real directory and re-point all symlinks at
   the repo, and ensures those commands are easy to find after this thread
   is finalized.

## What it should do
- Create `skill/vicaya-pre/SKILL.md`, content based on the current
  `~/.agents/skills/vicaya-pre/SKILL.md`, with `cd ~/Documents/dps/vicaya`
  removed from Step 1 (the skill already states "All commands run from the
  vicaya repo root" — the explicit `cd` hardcodes one user's checkout path).
- Update `README.md`:
  - In the top "Setup" section (step 4, the three agent code blocks for
    OpenCode/`~/.agents`, Antigravity/`~/.gemini`, Claude Code/`~/.claude`),
    add `vicaya-pre` to the loop/list alongside `vicaya-improve` as an
    optional standalone skill (not part of the staged-run set).
  - In the detailed walkthrough's "### 5 — Symlink the skill" section, add
    `vicaya-pre` to the `ln -sf` commands and the verification `ls` commands
    for both the `~/.agents/skills` block and the `~/.claude/skills` block,
    matching how `vicaya-improve` is already included.
- Do **not** touch the user's actual `~/.agents`, `~/.gemini`, or
  `~/.claude` skill directories during implementation — removing
  `~/.agents/skills/vicaya-pre/` (a real directory with content) and
  re-pointing live symlinks is a destructive, machine-specific action
  outside the repo, which per global rules requires explicit user
  confirmation at the time it happens, not silent execution during a
  planning/build thread.
- Instead, the last implementation task writes the exact removal +
  re-symlink commands (for `~/.agents/skills`, `~/.gemini/skills`, and
  `~/.claude/skills`) into `kamma/threads/<thread_id>/handoff.md`, and
  prints that same block to the user in chat. Because `kamma:4-finalize`
  copies the whole thread directory into `kamma/archive/<thread_id>/`
  before deleting the active thread, `handoff.md` survives finalize and
  stays discoverable afterward — satisfying "printed after I finalize the
  thread" and "saved in the handoff."

## Assumptions & uncertainties
- The global `kamma:4-finalize` skill itself is not part of this repo (it's
  a shared cross-project plugin) and won't be modified to auto-print
  anything special — the instructions are made durable via `handoff.md` and
  a direct chat print at the end of implementation instead.
- `$VICAYA_VAULT_PATH` references in the skill body are already portable
  (resolved from `.env`) — no change needed there.
- No other file references `vicaya-pre`, so no other cross-references need
  updating.

## Constraints
- `skill/vicaya-pre/SKILL.md` must contain no absolute path tied to one
  user's home directory or checkout location.
- No live changes to `~/.agents`, `~/.gemini`, or `~/.claude` directories —
  commands are handed to the user, not executed automatically.

## How we'll know it's done
- `skill/vicaya-pre/SKILL.md` exists in the repo with the hardcoded `cd`
  removed.
- `README.md`'s symlink sections (both the quick Setup list and the
  detailed walkthrough) mention `vicaya-pre` exactly like `vicaya-improve`.
- `kamma/threads/<thread_id>/handoff.md` contains the exact manual cleanup
  + re-symlink commands, and the same block was printed to the user in
  chat at the end of implementation.

## What's not included
- Running the removal/symlink commands ourselves.
- Any change to the skill's actual research/search behavior or output.
- Modifying the global `kamma:4-finalize` skill.
- Registering the skill in any plugin/marketplace manifest.
