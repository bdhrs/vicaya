## Thread
- **ID:** 20260711_harness-arg-forwarding
- **Objective:** Fix `/vicaya-quick <question>` (and siblings) silently dropping the typed question in Pi coding agent and OpenCode.

## Files Changed
- `config/opencode/commands/vicaya-quick.md` — added `args:`/`{{args}}` forwarding
- `config/opencode/commands/vicaya-pre.md` — added `args:`/`{{args}}` forwarding
- `config/pi/prompts/{vicaya,vicaya-quick,vicaya-pre,vicaya-improve,align}.md` — new Pi prompt stubs forwarding `$ARGUMENTS`
- `justfile` — `sync` recipe now prefers a `config/pi/prompts/<name>.md` stub over a direct `SKILL.md` symlink
- `README.md` — Pi setup block added to both the human Setup section and the Autonomous agent setup section (fixed during review, see Findings #2)

## Findings
| # | Severity | Location | What | Why | Fix |
|---|----------|----------|------|-----|-----|
| 1 | minor | `AGENTS.md` | Working tree has an unrelated "Database edits" section, added externally (by the user), sitting alongside this thread's changes. | Not part of this thread's scope; would muddy the commit if swept in. | Excluded from this thread's commit — staged separately or left for the user to commit on their own. Not reverted. |
| 2 | minor | `README.md` "Autonomous agent setup" § 5 | The machine-oriented setup path had no Pi/`just sync` mention at all — only the human-facing Setup section got it. | Undercuts this thread's own stated goal that a fresh setup shouldn't reproduce the bug. | Fixed: added a Pi block + `readlink` verification lines to § 5, mirroring the OpenCode/Claude Code blocks there. |
| 3 | nit | `config/opencode/commands/*.md` vs `config/pi/prompts/*.md` | OpenCode wraps `{{args}}` in backticks; Pi stubs don't wrap `$ARGUMENTS`. | Cosmetic only; OpenCode's backtick-wrapping is pre-existing precedent from `vicaya.md`, not introduced here. | Deferred — not required, no behavior difference. |

## Fixes Applied
- README's Autonomous agent setup section updated with a Pi block and verification lines (Finding #2).
- `AGENTS.md` confirmed excluded from this thread's `git add` (Finding #1) — see commit message below.
- Finding #3 deferred, no action.

## Test Evidence
- No `.py` files touched — ruff/pyright/pyrefly scope doesn't apply per `kamma/tech.md`.
- All `spec.md`/`plan.md` "how we'll know it's done" checks re-verified live: `grep` checks on both `config/opencode/commands/*.md` files, `test -f` + `$ARGUMENTS` grep on all 5 Pi stubs, `justfile` grep.
- `just sync` executed twice (once by the implementer, once independently by the reviewer) — both times all 5 `~/.pi/agent/prompts/<name>.md` symlinks resolved to `config/pi/prompts/<name>.md`, and `~/.pi/agent/skills/<name>` symlinks were confirmed unchanged.
- Live smoke test in an actual Pi session, confirmed by the user: `/vicaya-quick <question>` now carries the question through instead of the agent asking for it.
- Edge cases reviewed: empty-argument invocation (no crash, `$ARGUMENTS` resolves to empty string, matches pre-existing behavior), multi-word/quoted arguments (confirmed handled correctly by Pi's own arg-joining and the live smoke test).

## Verdict
PASSED
- Review date: 2026-07-11
- Reviewer: independent subagent (general-purpose), spawned per Kamma's independence-escalation step (this session did the implementation, so an independent reviewer was used per protocol)
