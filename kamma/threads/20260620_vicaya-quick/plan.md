# Plan: vicaya-quick — deep research, fast cited answer, no note

## Architecture Decisions
- New skill lives at `skill/vicaya-quick/SKILL.md`, auto-discovered like the
  other vicaya-family skills.
- Tool mechanics are **referenced**, not copied: the skill points to named
  sections of `skill/vicaya/SKILL.md`. Single source of truth; no drift.
- The scratch dossier is the recycle substrate. `scratch-init` is the only
  scratch command the skill issues; auto-logging does the rest. No
  `scratch-gate`/`scratch-verify`/`scratch-set-note`/`scratch-self-audit`.
- Promotion is not a new command — it is `/vicaya` + `scratch-resume <slug>`.
  The skill prints the exact line at the end of each run.
- Registration mirrors the `vicaya-pre` precedent (thread
  `20260618_move_vicaya_pre_skill`): opencode command file + README loops +
  walkthrough. Only the active `~/.claude` symlink is created automatically;
  the `~/.agents`/`~/.gemini` ones are offered as commands.

---

## Phase 1: Author the skill

- [x] Task 1.1: Write `skill/vicaya-quick/SKILL.md`
  Frontmatter (`name: vicaya-quick`, description with triggers), Purpose,
  "What this skill does NOT do" list, the 3-step workflow (triage → adaptive
  search → cited chat answer), kept correctness rules, scratch-init usage, and
  the end-of-run promotion suggestion block. Reference `skill/vicaya/SKILL.md`
  sections for all tool mechanics. No absolute home/checkout paths.
  → verify: the only ceremony terms present are the 3 intentional *negative*
    references (lines 35–36 "does NOT do" list + line 123 promotion handoff
    describing `/vicaya`'s behavior) — confirmed none is a workflow instruction;
    the workflow issues only `scratch-init` / `scratch-log`.
    `grep -q "scratch-init" skill/vicaya-quick/SKILL.md` succeeds;
    `grep -q "skill/vicaya/SKILL.md" skill/vicaya-quick/SKILL.md` succeeds.
    (Original `== 0` assertion was wrong — the skill correctly *names* the
    dropped ceremony to document its absence.)

- [x] Task 1.2: No hardcoded user paths
  → verify: `grep -nE "/home/|/Users/|~/Documents" skill/vicaya-quick/SKILL.md` returns no matches — CLEAN

---

## Phase 2: Register the skill

- [x] Task 2.1: Create `config/opencode/commands/vicaya-quick.md`
  Match the `vicaya-pre.md` shape: frontmatter `description`, body
  "Load the skill at `~/.agents/skills/vicaya-quick/SKILL.md` and execute it."
  → verify: `test -f config/opencode/commands/vicaya-quick.md`

- [x] Task 2.2: Add `vicaya-quick` to README quick-Setup loops
  In the three `for skill in vicaya vicaya-improve vicaya-pre;` loops and the
  one `for cmd in vicaya vicaya-improve vicaya-pre;` loop, append `vicaya-quick`.
  → verify: `grep -c "vicaya-pre vicaya-quick" README.md` returns `4`

- [x] Task 2.3: Add `vicaya-quick` to README detailed walkthrough + verification
  After each `vicaya-pre` `ln -sf` line (`~/.agents`, `~/.claude`) add a
  `vicaya-quick` line; after each `vicaya-pre/SKILL.md` `ls` line add a
  `vicaya-quick/SKILL.md` line.
  → verify: `grep -c "skill/vicaya-quick\"" README.md` returns `2`; `grep -c "skills/vicaya-quick/SKILL.md" README.md` returns `2`

---

## Phase 3: Activate + verify

- [x] Task 3.1: Create the active Claude Code symlink
  `ln -sf "$(pwd)/skill/vicaya-quick" ~/.claude/skills/vicaya-quick`
  → verify: `test -f ~/.claude/skills/vicaya-quick/SKILL.md`

- [x] Task 3.2: Full verification pass
  Run every `→ verify:` check above and confirm each passes.
  → verify: all checks above produce expected output
