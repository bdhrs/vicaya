# Plan — Remove staged-router subskills (vicaya-0/1/2/3)

## Architecture Decisions
- Deletion-only chore, no new abstractions. Every task is either `rm` of a
  known path or a verbatim find/replace given in full below — no judgment
  calls required.
- Historical files (`runs/TODO.md`, `kamma/archive/**`) are explicitly out of
  scope per the confirmed spec — do not touch them even though they contain
  the strings being removed elsewhere.
- Every "Old text" block below is copied verbatim from the file as it exists
  today. If a file's content does not match the "Old text" block exactly
  (whitespace included), STOP and report the mismatch instead of guessing —
  do not improvise a different edit.
- Use the `Edit` tool (exact string replacement) for every doc edit, not
  `sed`/`awk`, to avoid partial-match accidents across the four similar
  command-line strings in README.md.

## Phase 1 — Delete skill directories and command files

- [ ] Delete the four staged-router skill directories.
  → Run: `rm -rf skill/vicaya-0-scope skill/vicaya-1-gather skill/vicaya-2-synthesize-review skill/vicaya-3-complete`
  → verify: `ls skill/ | grep -E 'vicaya-[0-3]-'` outputs nothing.

- [ ] Delete the four OpenCode command files.
  → Run: `rm -f config/opencode/commands/vicaya-0-scope.md config/opencode/commands/vicaya-1-gather.md config/opencode/commands/vicaya-2-synthesize-review.md config/opencode/commands/vicaya-3-complete.md`
  → verify: `ls config/opencode/commands/ | grep -E 'vicaya-[0-3]-'` outputs nothing.

- [ ] Delete the obsolete route-list guard test.
  → Run: `rm -f tests/test_skill_routes.py`
  → verify: `ls tests/test_skill_routes.py` reports "No such file or directory".

- [ ] Remove the four dangling Claude Code skill symlinks (outside the repo,
  in the user's home directory — plain filesystem `rm`, not a git operation).
  → Run: `rm -f ~/.claude/skills/vicaya-0-scope ~/.claude/skills/vicaya-1-gather ~/.claude/skills/vicaya-2-synthesize-review ~/.claude/skills/vicaya-3-complete`
  → Do NOT touch `~/.claude/skills/vicaya`, `~/.claude/skills/vicaya-improve`,
    `~/.claude/skills/vicaya-pre`, or `~/.claude/skills/vicaya-prep` — these
    are unrelated and must remain.
  → verify: `ls ~/.claude/skills/ | grep -i 'vicaya-[0-3]'` outputs nothing,
    AND `ls ~/.claude/skills/ | grep -i vicaya` still lists `vicaya`,
    `vicaya-improve`, `vicaya-pre`, `vicaya-prep`.

- [ ] Phase 1 verification (automatic, end of phase).
  → verify: `git status --short` shows the four `skill/vicaya-{0-scope,1-gather,2-synthesize-review,3-complete}` directories and the four `config/opencode/commands/vicaya-{0-scope,1-gather,2-synthesize-review,3-complete}.md` files and `tests/test_skill_routes.py` as deleted (`D` or untracked-removed). No other paths should appear yet.

## Phase 2 — Edit README.md (two blocks)

- [ ] Edit README.md block A — Setup step 4 (symlink instructions + three
  per-tool code fences).

  Old text (must match exactly, including the four-space code fence
  indentation under the numbered list item):
  ```
  4. Symlink the main skill folder into your agents' skills directories. Using
     symlinks ensures that changes made in this repository are immediately
     reflected in all agents. If you use staged runs, symlink the staged sibling
     folders too: `vicaya-0-scope`, `vicaya-1-gather`,
     `vicaya-2-synthesize-review`, and `vicaya-3-complete`. If you use the
     retrospective improvement loop, symlink `vicaya-improve` too.

     **OpenCode:**
     ```bash
     # Symlink skills
     for skill in vicaya vicaya-improve vicaya-0-scope vicaya-1-gather vicaya-2-synthesize-review vicaya-3-complete; do
       ln -sf "$(pwd)/skill/$skill" ~/.agents/skills/$skill
     done
     # Symlink slash commands (for autocomplete)
     for cmd in vicaya vicaya-improve vicaya-0-scope vicaya-1-gather vicaya-2-synthesize-review vicaya-3-complete; do
       ln -sf "$(pwd)/config/opencode/commands/$cmd.md" ~/.config/opencode/commands/$cmd.md
     done
     ```

     **Antigravity CLI (`agy`):**
     ```bash
     for skill in vicaya vicaya-improve vicaya-0-scope vicaya-1-gather vicaya-2-synthesize-review vicaya-3-complete; do
       ln -sf "$(pwd)/skill/$skill" ~/.gemini/skills/$skill
     done
     ```

     **Claude Code:**
     ```bash
     for skill in vicaya vicaya-improve vicaya-0-scope vicaya-1-gather vicaya-2-synthesize-review vicaya-3-complete; do
       ln -sf "$(pwd)/skill/$skill" ~/.claude/skills/$skill
     done
     ```
  ```

  New text (replace the whole block above with this):
  ```
  4. Symlink the main skill folder into your agents' skills directories. Using
     symlinks ensures that changes made in this repository are immediately
     reflected in all agents. If you use the retrospective improvement loop,
     symlink `vicaya-improve` too.

     **OpenCode:**
     ```bash
     # Symlink skills
     for skill in vicaya vicaya-improve; do
       ln -sf "$(pwd)/skill/$skill" ~/.agents/skills/$skill
     done
     # Symlink slash commands (for autocomplete)
     for cmd in vicaya vicaya-improve; do
       ln -sf "$(pwd)/config/opencode/commands/$cmd.md" ~/.config/opencode/commands/$cmd.md
     done
     ```

     **Antigravity CLI (`agy`):**
     ```bash
     for skill in vicaya vicaya-improve; do
       ln -sf "$(pwd)/skill/$skill" ~/.gemini/skills/$skill
     done
     ```

     **Claude Code:**
     ```bash
     for skill in vicaya vicaya-improve; do
       ln -sf "$(pwd)/skill/$skill" ~/.claude/skills/$skill
     done
     ```
  ```
  → verify: `grep -n "vicaya-0-scope\|vicaya-1-gather\|vicaya-2-synthesize-review\|vicaya-3-complete" README.md` no longer matches anything inside the Setup section (lines roughly 1–75).

- [ ] Edit README.md block B — "### 5 — Symlink the skill" intro paragraph.

  Old text (must match exactly):
  ```
  To make the main skill available across all your agents while keeping it in
  sync with this repository, create symlinks in the following locations. If you
  use staged runs, create matching symlinks for `skill/vicaya-0-scope`,
  `skill/vicaya-1-gather`, `skill/vicaya-2-synthesize-review`, and
  `skill/vicaya-3-complete`. Also symlink `skill/vicaya-improve` if you want
  the retrospective improvement loop available as an agent skill.
  ```

  New text:
  ```
  To make the main skill available across all your agents while keeping it in
  sync with this repository, create symlinks in the following locations. Also
  symlink `skill/vicaya-improve` if you want the retrospective improvement
  loop available as an agent skill.
  ```
  → verify: `grep -c "vicaya-0-scope\|vicaya-1-gather\|vicaya-2-synthesize-review\|vicaya-3-complete" README.md` returns `0`.

## Phase 3 — Edit kamma/project.md

- [ ] Edit the "What it is and why" paragraph.

  Old text (must match exactly):
  ```
  Vicaya is a multi-source research workflow for Pāḷi and Buddhist topics,
  invoked as `/vicaya <question>` inside Claude Code (or any agent that reads
  a Markdown skill file). Lower-context staged runs use the sibling skills
  `vicaya-0-scope`, `vicaya-1-gather`, `vicaya-2-synthesize-review`, and
  `vicaya-3-complete`, which route back to exact sections in the main skill. It
  queries the user's Obsidian vault, a local CST canon SQLite database, the Early
  ```

  New text:
  ```
  Vicaya is a multi-source research workflow for Pāḷi and Buddhist topics,
  invoked as `/vicaya <question>` inside Claude Code (or any agent that reads
  a Markdown skill file). It queries the user's Obsidian vault, a local CST
  canon SQLite database, the Early
  ```

  Note: the sentence "Buddhist Connections (EBC) reference vault, ..." that
  follows on the next line is unchanged — only the lines shown above change.
  → verify: `sed -n '1,15p' kamma/project.md` reads as one coherent paragraph
  with no dangling "Lower-context staged runs" sentence.

- [ ] Edit the "Maintenance" section's second and third bullets.

  Old text (must match exactly):
  ```
  - `skill/vicaya/SKILL.md` is the canonical full-run skill. When editing it,
    check the staged sibling skills for affected route lists, stage boundaries,
    handoff labels, and bounded context-break guards.
  - When editing `skill/vicaya-0-scope`, `skill/vicaya-1-gather`,
    `skill/vicaya-2-synthesize-review`, or `skill/vicaya-3-complete`, verify the
    edited staged skill still routes to exact headings in `skill/vicaya/SKILL.md`
    and does not silently fork canonical workflow behavior.
  - The staged sibling skills are section routers, not alternate workflow
    documents. Do not copy behavioral rules into them, do not restore summarized
    shared references under `skill/vicaya/shared/`, and verify every routed
    heading still exists after canonical skill heading changes.
  ```

  New text:
  ```
  - `skill/vicaya/SKILL.md` is the canonical full-run skill.
  ```
  → verify: `grep -c "vicaya-0-scope\|vicaya-1-gather\|vicaya-2-synthesize-review\|vicaya-3-complete" kamma/project.md` returns `0`.

- [ ] Phase 3 verification (automatic, end of phase).
  → verify: `cat kamma/project.md` reads cleanly start to end with no broken
  sentences or orphaned bullet fragments around the two edits above.

## Phase 4 — Edit kamma/tech.md

- [ ] Edit the "Maintenance coupling" and "Staged sibling skills" bullets in
  the Constraints section.

  Old text (must match exactly):
  ```
  - Maintenance coupling: `skill/vicaya/SKILL.md` is the canonical full-run
    skill. Edits to it must check the staged sibling skills
    (`skill/vicaya-0-scope`, `skill/vicaya-1-gather`,
    `skill/vicaya-2-synthesize-review`, `skill/vicaya-3-complete`) for affected
    route lists, stage boundaries, handoff labels, and bounded context-break
    guards. Edits to any staged sibling must verify exact routing back to
    `skill/vicaya/SKILL.md` and must not silently fork canonical workflow
    behavior.
  - Staged sibling skills are router-only technical artifacts. They must not
    contain behavioral summaries or depend on `skill/vicaya/shared/`; after any
    canonical heading or staged route-list change, run a focused route-heading
    audit before review or finalize.
  ```

  New text:
  ```
  - `skill/vicaya/SKILL.md` is the canonical full-run skill.
  ```
  → verify: `grep -c "vicaya-0-scope\|vicaya-1-gather\|vicaya-2-synthesize-review\|vicaya-3-complete" kamma/tech.md` returns `0`.

- [ ] Phase 4 verification (automatic, end of phase).
  → verify: `cat kamma/tech.md` reads cleanly with no broken bullet list
  around the Constraints section.

## Phase 5 — Edit skill/vicaya-improve/SKILL.md

- [ ] Remove the cross-reference sentence at the end of "## Phase 6 — Present
  top 5 and pick".

  Old text (must match exactly):
  ```
  Then ask the user to pick one (AskUserQuestion, top 4 as options with the
  "Why now" as description; the 5th and the rest are reachable via Other).
  Work on the chosen issue in the normal way. If the fix touches
  `skill/vicaya/SKILL.md`, the canonical-skill sync gate below is part of the
  fix — not an optional follow-up.
  ```

  New text:
  ```
  Then ask the user to pick one (AskUserQuestion, top 4 as options with the
  "Why now" as description; the 5th and the rest are reachable via Other).
  Work on the chosen issue in the normal way.
  ```

- [ ] Remove the entire "## Canonical-skill sync gate" section (it sits
  between "## Phase 6" and "## Phase 7").

  Old text (must match exactly, including the blank line before and after):
  ```

  ## Canonical-skill sync gate

  `skill/vicaya/SKILL.md` is canonical; the staged skills (`vicaya-0-scope`
  … `vicaya-3-complete`) are section routers into it (kamma/project.md,
  Maintenance). Each router's Route List names exact headings, and a routed
  section is read only up to the next same-or-higher-level heading (or the
  next separately routed one). Any fix that edits `skill/vicaya/SKILL.md` is
  incomplete until this audit passes:

  1. **Heading added** → content under an unlisted heading is invisible to
     staged runs, even when it sits between two routed headings. Decide which
     stage(s) own it and add it to those Route Lists. If the new content is
     load-bearing for a stage (a gate requirement, a hard rule), also pin it
     with a guard test in `tests/test_skill_routes.py`.
  2. **Heading renamed or removed** → update every Route List that names it.
  3. **Behavioral text stays canonical** — never copy rules into a router;
     routers carry only route lists, stage boundaries, and context-break
     guards.
  4. Run `uv run -m pytest tests/test_skill_routes.py`. It catches dead route
     entries (routed heading no longer in SKILL.md), **not** new unrouted
     headings — check additions by hand against each router's extraction
     rule.

  ## Phase 7 — Close the loop (automatic, do not wait to be asked)
  ```

  New text (the section is deleted; "## Phase 7" heading stays, immediately
  following "## Phase 6"'s content with one blank line, same as the
  convention used between every other phase heading in this file):
  ```

  ## Phase 7 — Close the loop (automatic, do not wait to be asked)
  ```

- [ ] Update the "Finishing the fix INCLUDES..." sentence at the start of
  Phase 7, which still references "the sync gate above".

  Old text (must match exactly):
  ```
  Finishing the fix INCLUDES the TODO bookkeeping and, for canonical skill
  edits, the sync gate above. As soon as the fix is implemented and its tests
  pass — before reporting completion to the user — update `runs/TODO.md` in
  the same breath:
  ```

  New text:
  ```
  Finishing the fix INCLUDES the TODO bookkeeping. As soon as the fix is
  implemented and its tests pass — before reporting completion to the user —
  update `runs/TODO.md` in the same breath:
  ```
  → verify: `grep -c "vicaya-0-scope\|vicaya-1-gather\|vicaya-2-synthesize-review\|vicaya-3-complete\|sync gate\|Canonical-skill sync" skill/vicaya-improve/SKILL.md` returns `0`.

- [ ] Phase 5 verification (automatic, end of phase).
  → verify: `grep -n "^## " skill/vicaya-improve/SKILL.md` shows phases in
  unbroken order: Phase 1, Phase 2, Phase 3, Phase 4, Phase 5, Phase 6,
  Phase 7, "Style rules for TODO.md" — with no "Canonical-skill sync gate"
  heading remaining and no gap or duplicate numbering.

## Phase 6 — Full-repo verification

- [ ] Confirm no live references remain outside the two excluded historical
  locations.
  → Run: `grep -rl "vicaya-0-scope\|vicaya-1-gather\|vicaya-2-synthesize-review\|vicaya-3-complete" . 2>/dev/null | grep -v '^\./\.git/'`
  → verify: output is exactly these paths and nothing else:
    `runs/TODO.md`
    `kamma/archive/obsidian-cli-fix/spec.md`
    `kamma/archive/20260602_vicaya-staged-skills-section-router/plan.md`
    `kamma/archive/20260602_vicaya-staged-skills-section-router/review.md`
    `kamma/archive/20260602_vicaya-staged-skills-section-router/handoff.md`
    `kamma/archive/20260602_vicaya-staged-skills-section-router/spec.md`
  If any other path appears, go back and fix it before continuing.

- [ ] Run the full test suite.
  → Run: `uv run pytest tests/ -q`
  → verify: all tests pass or are skipped (skipped only for optional tools
  not installed). Zero failures. No `ModuleNotFoundError` or collection
  error referencing `test_skill_routes`.

- [ ] Lint the changed Python footprint (only `tests/test_skill_routes.py`
  was touched, and it was deleted, so this should be a no-op, but run it to
  confirm nothing else broke).
  → Run: `uv run ruff check .`
  → verify: no new errors introduced (pre-existing unrelated errors, if any,
  are out of scope — only check for errors caused by this change).

- [ ] Phase 6 verification (automatic, end of phase — final gate for the
  whole thread).
  → verify: `git status --short` shows only the expected deletions
  (`skill/vicaya-0-scope/`, `skill/vicaya-1-gather/`,
  `skill/vicaya-2-synthesize-review/`, `skill/vicaya-3-complete/`,
  `config/opencode/commands/vicaya-{0-scope,1-gather,2-synthesize-review,3-complete}.md`,
  `tests/test_skill_routes.py`) and modifications
  (`README.md`, `kamma/project.md`, `kamma/tech.md`,
  `skill/vicaya-improve/SKILL.md`). No other file appears in the diff.
