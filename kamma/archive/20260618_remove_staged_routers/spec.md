# Spec — Remove staged-router subskills (vicaya-0/1/2/3)

## Overview
The repo currently ships four "staged router" skills — `vicaya-0-scope`,
`vicaya-1-gather`, `vicaya-2-synthesize-review`, `vicaya-3-complete` — that
extract sections from the canonical `skill/vicaya/SKILL.md` by exact heading
text, for use in lower-context multi-session runs. The canonical skill has
since moved to a single-session-with-sub-agent-dispatch architecture (see
`skill/vicaya/SKILL.md` "Sub-agent dispatch" section, ~line 948), making the
staged routers redundant. They are no longer wanted and must be deleted
along with every reference to them in live documentation, tests, config, and
skill symlinks.

## What it should do
Remove, completely and mechanically:
1. The four skill directories: `skill/vicaya-0-scope/`,
   `skill/vicaya-1-gather/`, `skill/vicaya-2-synthesize-review/`,
   `skill/vicaya-3-complete/`.
2. The four OpenCode command files:
   `config/opencode/commands/vicaya-0-scope.md`,
   `config/opencode/commands/vicaya-1-gather.md`,
   `config/opencode/commands/vicaya-2-synthesize-review.md`,
   `config/opencode/commands/vicaya-3-complete.md`.
3. The test file `tests/test_skill_routes.py` (it exists solely to guard the
   staged routers' route lists — no content survives their removal).
4. The four dangling Claude Code skill symlinks in `~/.claude/skills/`:
   `vicaya-0-scope`, `vicaya-1-gather`, `vicaya-2-synthesize-review`,
   `vicaya-3-complete`.
5. All references to these four skill names in living docs:
   `README.md`, `kamma/project.md`, `kamma/tech.md`,
   `skill/vicaya-improve/SKILL.md`.

## Assumptions & uncertainties
- **Historical records are out of scope** (confirmed with user): do NOT edit
  `runs/TODO.md` or anything under `kamma/archive/**` — these are closed-issue
  logs and archived thread records that name the staged skills as historical
  fact. Leave them exactly as-is.
- `skill/vicaya/SKILL.md` (canonical) and `skill/vicaya/README.md` contain no
  references to the four staged skills (verified by grep) — no edit needed
  there.
- `skill/vicaya-improve/SKILL.md` has a whole section, "## Canonical-skill
  sync gate" (lines ~126–147 as of this writing), that exists only to keep
  the staged routers in sync with the canonical skill. Since the routers are
  gone, this entire section is dead and must be deleted, along with the one
  sentence in "## Phase 6" that points to it.
- No `.json` config, settings, or plugin manifest references these skill
  names (verified by grep) — nothing to change there.
- `~/.claude/skills/vicaya-pre`, `~/.claude/skills/vicaya-prep`, and
  `~/.claude/skills/vicaya-improve` are unrelated skills and must NOT be
  touched.
- This is a deletion/cleanup chore with no new behavior, so "done" is defined
  by absence of the removed names from live files and a clean test/lint run.

## Constraints
- Do not modify `runs/TODO.md` or `kamma/archive/**`.
- Do not touch `skill/vicaya/SKILL.md`'s "Sub-agent dispatch" section or any
  other canonical-skill content — only remove dead references to the staged
  routers (there are none in this file, verified by grep).
- Do not delete or modify `skill/vicaya`, `skill/vicaya-improve`,
  `skill/vicaya-prep`, or any of their symlinks.
- Removing `~/.claude/skills/*` symlinks is a change outside the git repo
  (home directory) — treat as a plain `rm` of dangling symlinks, not a git
  operation.

## How we'll know it's done
- `grep -rl "vicaya-0-scope\|vicaya-1-gather\|vicaya-2-synthesize-review\|vicaya-3-complete" .` from repo root returns only `runs/TODO.md` and paths under `kamma/archive/`.
- `skill/vicaya-0-scope/`, `skill/vicaya-1-gather/`,
  `skill/vicaya-2-synthesize-review/`, `skill/vicaya-3-complete/` no longer
  exist on disk.
- `config/opencode/commands/vicaya-0-scope.md` and its three siblings no
  longer exist on disk.
- `tests/test_skill_routes.py` no longer exists.
- `ls ~/.claude/skills/ | grep -i 'vicaya-[0-3]'` returns nothing.
- `uv run pytest tests/ -q` passes (no failures, no import errors from the
  deleted test file).
- `uv run ruff check .` shows no new errors.

## What's not included
- No changes to `runs/TODO.md` or `kamma/archive/**`.
- No changes to the canonical `skill/vicaya/SKILL.md` content (it has no
  references to remove).
- No changes to `skill/vicaya-improve/SKILL.md` beyond removing the dead
  sync-gate section and its one cross-reference sentence.
- No new tests are added; one obsolete test file is removed.
