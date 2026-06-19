## Thread
- **ID:** 20260618_move_vicaya_pre_skill
- **Objective:** Move `vicaya-pre` into the repo as `skill/vicaya-pre/SKILL.md` (portable), document it in README's symlink setup like `vicaya-improve`, and hand off exact manual commands to retire the old global copy — without touching live `~/.agents`, `~/.gemini`, `~/.claude` dirs.

## Files Changed
- `skill/vicaya-pre/SKILL.md` (new) — repo-tracked copy of the skill, with the hardcoded `cd ~/Documents/dps/vicaya` line removed.
- `README.md` — adds `vicaya-pre` to the 3 quick-setup skill loops and to the detailed walkthrough's symlink/verification commands.
- `kamma/threads/20260618_move_vicaya_pre_skill/handoff.md` (new) — exact manual rm/ln-sf commands for the user to run themselves.

## Findings
| # | Severity | Location | What | Why | Fix |
|---|----------|----------|------|-----|-----|
| 1 | nit (dismissed) | `handoff.md:9-11` | CodeRabbit flagged the absolute `/Users/deva/...` path in the `ln -sf` commands as non-portable | `handoff.md` is intentionally a one-time, machine-specific cleanup script for this user's own home directory, not a repo-portable artifact — spec explicitly scopes portability to `skill/vicaya-pre/SKILL.md` only | No fix needed; noted as out of scope per spec's "What's not included" |

No other findings.

## Fixes Applied
None needed.

## Test Evidence
- `diff <(grep -v '^cd ~/Documents/dps/vicaya$' ~/.agents/skills/vicaya-pre/SKILL.md) skill/vicaya-pre/SKILL.md` → pass (no diff)
- `grep -n "Documents/dps/vicaya" skill/vicaya-pre/SKILL.md` → pass (no matches, CLEAN)
- `grep -c "for skill in vicaya vicaya-improve vicaya-pre vicaya-0-scope" README.md` → pass (3)
- `grep "for cmd in" README.md` → pass (no `vicaya-pre`, slash-command loop correctly untouched)
- `grep -c 'ln -sf "$(pwd)/skill/vicaya-pre"' README.md` → pass (2)
- `grep -c "ls .*skills/vicaya-pre/SKILL.md" README.md` → pass (2)
- `test -f kamma/threads/.../handoff.md` → pass
- `grep -q 'ln -sf "/Users/deva/Documents/dps/vicaya/skill/vicaya-pre"' handoff.md` → pass
- `grep -rn "vicaya-pre"` repo-wide → pass (no orphaned/stale references outside expected files)
- `coderabbit review --agent` → 1 finding, reviewed and dismissed (see Findings)

## Verdict
PASSED
- Review date: 2026-06-18
- Reviewer: Claude (same agent that implemented — review is not fully independent)
