## Thread
- **ID:** 20260602_dpd-db-instructions
- **Objective:** Add a concise "DPD dictionary database" section to the Vicaya SKILL.md documenting the two main lookup paths.

## Files Changed
- `skill/vicaya/SKILL.md` — new `## DPD dictionary database` section (+77 lines); Setup-list bullet; stem-rule cross-reference.

## Findings
| # | Severity | Location | What | Why | Fix |
|---|----------|----------|------|-----|-----|
| 1 | nit | SKILL.md Way 2 example | `grammar`/`deconstructor` inline comments show illustrative values (deconstructor sample is from a different word) | Could read as `dukkhassa`'s literal output | Left as-is — comments are clearly format illustrations ("e.g."), and verbatim output would bloat the example |

## Fixes Applied
- None (only a nit, deliberately retained for brevity).

## Test Evidence
- All three `sqlite3` examples re-run against live `dpd.db` → return rows (pass)
- `grep -n "DPD dictionary database"` → heading at line 140 (pass)
- `grep -n "VICAYA_DPD_DB"` → Setup bullet + section refs (pass)
- stem-rule cross-reference present at line 1023 (pass)
- `~/.claude/skills/vicaya` is a symlink to the repo → no second copy to sync (pass)

## Verdict
PASSED
- Review date: 2026-06-02
- Reviewer: kamma (inline)
