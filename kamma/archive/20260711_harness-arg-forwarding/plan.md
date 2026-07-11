# Plan: harness-arg-forwarding — fix dropped question arguments in vicaya-quick / vicaya-pre across Pi and OpenCode

## Architecture Decisions
- OpenCode fix mirrors the already-correct `vicaya.md` pattern exactly: an
  `args:` frontmatter block + `{{args}}` interpolation in the body. No new
  mechanism, just applying the existing one to the two files that were missed.
- Pi gets small tracked stub files under a new `config/pi/prompts/` directory
  (mirroring `config/opencode/commands/`) rather than symlinking Pi's prompt
  slot straight at each `SKILL.md`. The stub delegates to the real skill and
  captures `$ARGUMENTS`; SKILL.md content is never duplicated.
- Pi's `~/.pi/agent/skills/<name>` symlinks (the `/skill:name` mechanism) are
  untouched — only `~/.pi/agent/prompts/<name>.md` gets re-pointed, since only
  the bare `/name <args>` form is broken.
- README gets a fourth harness block (Pi), matching the existing OpenCode /
  Antigravity / Claude Code structure: a skill-symlink loop plus a
  prompt-stub-symlink loop.

---

## Phase 1: Fix OpenCode argument forwarding

- [x] Task 1.1: Fix `config/opencode/commands/vicaya-quick.md`
  Add frontmatter:
  ```yaml
  args:
    - name: question
      description: The research question
      required: true
  ```
  Change body to: `Load the skill at \`~/.agents/skills/vicaya-quick/SKILL.md\` and execute it with the research question \`{{args}}\`.`
  → verify: `grep -q "args:" config/opencode/commands/vicaya-quick.md && grep -q '{{args}}' config/opencode/commands/vicaya-quick.md`

- [x] Task 1.2: Fix `config/opencode/commands/vicaya-pre.md`
  Same treatment, `name: topic` (matches README's `/vicaya-pre <topic>`).
  → verify: `grep -q "args:" config/opencode/commands/vicaya-pre.md && grep -q '{{args}}' config/opencode/commands/vicaya-pre.md`

- [x] Phase 1 verification: confirm `vicaya.md` and `vicaya-improve.md` are unchanged (`git diff --stat` shows only the two edited files in this phase).
  → verify: `git diff --stat config/opencode/commands/` lists only `vicaya-quick.md` and `vicaya-pre.md` — CONFIRMED (only vicaya-pre.md and vicaya-quick.md changed)

---

## Phase 2: Add Pi prompt stubs

- [x] Task 2.1: Create `config/pi/prompts/vicaya.md`
  Frontmatter: `description` (copy from SKILL.md), `argument-hint: "<question>"`.
  Body: `Load the skill at `skill/vicaya/SKILL.md` and execute it with the research question: $ARGUMENTS`
  → verify: `test -f config/pi/prompts/vicaya.md && grep -q '\$ARGUMENTS' config/pi/prompts/vicaya.md`

- [x] Task 2.2: Create `config/pi/prompts/vicaya-quick.md`
  Same shape, `argument-hint: "<question>"`.
  → verify: `test -f config/pi/prompts/vicaya-quick.md && grep -q '\$ARGUMENTS' config/pi/prompts/vicaya-quick.md`

- [x] Task 2.3: Create `config/pi/prompts/vicaya-pre.md`
  Same shape, `argument-hint: "<topic>"`.
  → verify: `test -f config/pi/prompts/vicaya-pre.md && grep -q '\$ARGUMENTS' config/pi/prompts/vicaya-pre.md`

- [x] Task 2.4: Create `config/pi/prompts/vicaya-improve.md`
  No `argument-hint`, no `$ARGUMENTS` — body just says to load and execute the skill (matches its OpenCode sibling, which also takes no argument).
  → verify: `test -f config/pi/prompts/vicaya-improve.md && ! grep -q '\$ARGUMENTS' config/pi/prompts/vicaya-improve.md`

- [x] Task 2.5: Re-point this machine's live Pi prompt symlinks
  For each of the four names: `ln -sf "$(pwd)/config/pi/prompts/$name.md" ~/.pi/agent/prompts/$name.md` (replacing the existing direct-to-SKILL.md symlinks).
  → verify: `readlink ~/.pi/agent/prompts/vicaya-quick.md` ends in `config/pi/prompts/vicaya-quick.md`, same for the other three; `readlink ~/.pi/agent/skills/vicaya-quick` is unchanged (still points at `skill/vicaya-quick`)

- [x] Phase 2 verification: manual smoke test in Pi — type `/vicaya-quick what is anatta` (bare form) and confirm the question text appears in the agent's resulting context/first message (not silently dropped).
  → verify: observed directly by the user in a live Pi session; note the outcome in `plan.md` before moving on
  CONFIRMED by user: "yeah that worked." (after re-applying the symlinks a second
  time — see Phase 5, the first pass was clobbered by `just sync`).

---

## Phase 3: Document Pi in the README

- [x] Task 3.1: Add Pi to the quick-setup skill/command loops
  In `README.md`'s Setup section, add a **Pi coding agent** block after the existing Claude Code block: a skill-symlink loop (`~/.pi/agent/skills/$skill`) and a prompt-stub-symlink loop (`~/.pi/agent/prompts/$cmd.md` → `config/pi/prompts/$cmd.md`).
  → verify: `grep -c "Pi coding agent" README.md` returns at least `1`; `grep -q '.pi/agent/prompts' README.md` succeeds

---

## Phase 5: Fix the real regression source — `justfile`'s `sync` recipe (discovered mid-thread)

**Drift note:** after the Phase 2 smoke test initially failed, investigation
found that `justfile`'s `sync` recipe (`justfile:37-50`) is the actual,
user-facing mechanism for wiring skills into Pi — advertised in `just --list`
as "re-run to pick up newly added skills." It walks every `skill/*/SKILL.md`
and symlinks `~/.pi/agent/prompts/<name>.md` **directly at SKILL.md**,
unconditionally. Any future `just sync` run silently undoes the Phase 2 fix.
It also affects `align` (`/align <phrase>`), which was outside the original
spec's scope but has the identical bug in Pi and is walked by this same loop.
This phase is a required fix, not optional polish — without it the bug
reappears on the user's very next `just sync`.

- [x] Task 5.1: Add `config/pi/prompts/align.md`
  Same stub shape as the other four: `description` copied from
  `skill/align/SKILL.md`, `argument-hint: "<phrase>"`, body loads
  `~/.pi/agent/skills/align/SKILL.md` and executes it with `$ARGUMENTS`.
  → verify: `test -f config/pi/prompts/align.md && grep -q '\$ARGUMENTS' config/pi/prompts/align.md`

- [x] Task 5.2: Fix `justfile`'s `sync` recipe
  Change the prompt-symlink line so it prefers a tracked stub when one exists
  for that skill name, falling back to the direct-to-SKILL.md symlink only for
  skills that don't have one yet (so a brand-new future skill without a stub
  still gets *something* wired up, matching the recipe's "pick up newly added
  skills" promise):
  ```bash
  stub="$(pwd)/config/pi/prompts/$name.md"
  if [ -f "$stub" ]; then
      ln -sfn "$stub" "$prompts_dir/$name.md"
  else
      ln -sfn "${dir}SKILL.md" "$prompts_dir/$name.md"
  fi
  ```
  → verify: `grep -q 'config/pi/prompts' justfile`

- [x] Task 5.3: Re-run `just sync` and confirm it no longer regresses
  CONFIRMED — all 5 prompt symlinks (`vicaya`, `vicaya-quick`, `vicaya-pre`,
  `vicaya-improve`, `align`) now point at `config/pi/prompts/*.md`.
  → verify: after `just sync`, `readlink ~/.pi/agent/prompts/vicaya-quick.md` (and `vicaya`, `vicaya-pre`, `vicaya-improve`, `align`) point at `config/pi/prompts/*.md`, not `skill/*/SKILL.md`

- [x] Task 5.4: Simplify the README Pi block to reference `just sync`
  Task 3.1 wrote out a manual `ln -sf` for-loop for Pi, duplicating what
  `justfile`'s `sync` recipe already does correctly (post-Task-5.2). Replace
  the prompt-symlink for-loop in the README's Pi block with a pointer to
  `just sync`, keeping only the skills-symlink loop (which `just sync` also
  now handles — consider replacing that loop too, collapsing the whole Pi
  block to "run `just sync`" plus a one-line explanation of what it does).
  → verify: README's Pi block mentions `just sync`; no direct
  `~/.pi/agent/prompts/$cmd.md` for-loop remains in the README

---

## Phase 4: Final verification pass

- [x] Task 4.1: Run every `→ verify:` check above in sequence and confirm each passes as written.
  → verify: all checks above produce the expected output; any failure is fixed before the thread is marked done
  ALL CHECKS CONFIRMED, including Phase 5's `just sync` durability re-run
  (twice, no regression) and the user's live Pi smoke test.
