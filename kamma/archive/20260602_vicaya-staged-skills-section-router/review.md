## Thread
- **ID:** 20260602_vicaya-staged-skills-section-router
- **Objective:** Rebuild Vicaya staged skills as exact section routers into `skill/vicaya/SKILL.md`.

## Files Changed
- `skill/vicaya-0-scope/SKILL.md` - routes Phase 0 and records risk-triggered staged hard-stop plans when needed.
- `skill/vicaya-1-gather/SKILL.md` - routes Phase 1 through Phase 4c and applies binding Stage 1 source-block checkpoints when recorded.
- `skill/vicaya-2-synthesize-review/SKILL.md` - routes Phase 5 and Phase 6 and keeps synthesis/review payloads scratch-local.
- `skill/vicaya-3-complete/SKILL.md` - routes completion sections and uses scratch-local Phase 7 draft handling before vault write.
- `skill/vicaya/SKILL.md` - adds the staged-router pointer; current canonical temp handling is repo-local/scratch-local.
- `README.md`, `skill/vicaya/README.md` - preserve main-skill docs and add concise staged-router references.
- `kamma/project.md`, `kamma/tech.md` - document canonical/staged maintenance coupling.
- `kamma/threads/20260602_vicaya-staged-skills-section-router/{spec.md,plan.md,handoff.md}` - record router design, context controls, durable artifacts, no-global-temp rules, and README criteria.

## Findings
| # | Severity | Location | What | Why | Fix |
|---|----------|----------|------|-----|-----|
| 1 | minor | `README.md:13` | Root README named staged skills without also saying they route to exact sections in `skill/vicaya/SKILL.md` and that the canonical skill remains behavioral source of truth. | Phase 9.19 requires README staged references to make that relationship explicit while preserving restored README content. | Added one concise sentence to the existing staged-skill mention. |

## Fixes Applied
- Added the missing exact-routing/source-of-truth sentence to `README.md`.
- Did not apply CodeRabbit's inline-code suggestion for `skill/vicaya-0-scope/SKILL.md`; the current fully-backticked source-of-truth line matches the thread's required exact statement.

## Test Evidence
- Read `spec.md`, `plan.md`, `handoff.md`, `workflow.md`, `project.md`, and `tech.md`; no GitHub issue is associated with this thread.
- Reviewed `git diff main...HEAD` plus current working-tree diffs; no Python files changed.
- Fence-aware route-anchor/boundary audit with `uv run python - <<'PY' ...` -> pass; all staged route headings resolve to real non-fenced canonical headings, including Phase 7 and self-improvement fenced-template cases.
- `test ! -e skill/vicaya/shared` -> pass.
- Stale shared-reference search over README/project/tech/staged skills -> pass; only the allowed no-shared guard line appears in staged skills.
- Active skill-root symlink inspection -> pass for `/Users/deva/.agents/skills` and `/Users/deva/.claude/skills`; `/Users/deva/.codex/skills` has no monolithic `vicaya`, so no staged links are required there.
- Checks for adaptive context wording, copied command syntax in staged skills, scratch-local draft/review handling, and repo-local temp cleanup -> pass.
- `git diff --check -- README.md skill/vicaya/SKILL.md skill/vicaya-*/SKILL.md skill/vicaya/README.md kamma/project.md kamma/tech.md kamma/threads/20260602_vicaya-staged-skills-section-router/{spec.md,plan.md,handoff.md}` -> pass.
- `coderabbit review --agent` -> completed in limited/free CLI mode; one minor suggestion reviewed and rejected as contrary to the required exact source-of-truth line.

## Verdict
PASSED
- Review date: 2026-06-05
- Reviewer: Codex
