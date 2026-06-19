## Thread
- **ID:** 20260618_remove_staged_routers
- **Objective:** Remove the four staged-router subskills (vicaya-0-scope, vicaya-1-gather, vicaya-2-synthesize-review, vicaya-3-complete) and every live reference to them.

## Files Changed
- `skill/vicaya-{0-scope,1-gather,2-synthesize-review,3-complete}/SKILL.md` — deleted (staged-router skills, redundant after canonical skill's sub-agent-dispatch rework)
- `config/opencode/commands/vicaya-{0-scope,1-gather,2-synthesize-review,3-complete}.md` — deleted (OpenCode command shims for the above)
- `tests/test_skill_routes.py` — deleted (guarded only the staged routers' route lists)
- `~/.claude/skills/vicaya-{0-scope,1-gather,2-synthesize-review,3-complete}` — dangling symlinks removed (outside repo)
- `README.md` — removed staged-run symlink instructions/loops in setup steps 4 and 5
- `kamma/project.md` — removed staged-run mention and three "Maintenance" bullets that existed only to keep staged routers in sync
- `kamma/tech.md` — removed two Constraints bullets ("Maintenance coupling", "Staged sibling skills") with the same sync-only purpose
- `skill/vicaya-improve/SKILL.md` — removed the cross-reference sentence in Phase 6 and the entire "Canonical-skill sync gate" section in Phase 7, since both existed solely to keep the now-deleted staged routers aligned with the canonical skill

## Findings
No findings.

User raised a question during review about whether the `skill/vicaya-improve/SKILL.md` edit removed more than necessary. Verified against spec.md/plan.md: the deleted "Canonical-skill sync gate" section's entire content (heading-add/rename audit steps, guard-test pointer) was procedural logic for syncing the staged routers — none of it has any function once the routers are gone. This whole-section removal was explicitly flagged in spec.md's "Assumptions & uncertainties" and confirmed with the user before implementation, so it was planned, not incidental over-deletion.

Residual/non-issue: `kamma/project.md`'s historical "Assumptions" text references a `vicaya-prep` skill that was never actually installed (only `vicaya`, `vicaya-improve`, `vicaya-pre` exist under `~/.claude/skills/`). Pre-existing, unrelated to this thread — not touched.

## Fixes Applied
None.

## Test Evidence
- `grep -rl "vicaya-0-scope\|vicaya-1-gather\|vicaya-2-synthesize-review\|vicaya-3-complete" .` (excluding `.git`) → only `runs/TODO.md`, `kamma/archive/**` (explicitly out of scope), and this thread's own `spec.md`/`plan.md` — matches plan's expected output.
- `ls ~/.claude/skills/ | grep -i vicaya` → `vicaya`, `vicaya-improve`, `vicaya-pre` only; no `vicaya-[0-3]*` entries.
- `uv run ruff check .` → all checks passed.
- Project-wide `pytest` is blocked by `kamma/tech.md` policy (scoped runs only); not required here since no `.py` files were modified (only one test file deleted, with no remaining references to it).

## Verdict
PASSED
- Review date: 2026-06-18
- Reviewer: Claude (same agent that implemented — review is not independent)
