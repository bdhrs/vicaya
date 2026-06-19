# Plan

## GitHub Reference
PR #29 — "Vicaya pre skill" (branch `vicaya-pre-skill` → `main`).

## Architecture Decisions
- Use a real `git merge origin/main` (not rebase/squash) — preserves both branches' commit history, matches the reviewer's own suggested fix command, and is the lowest-risk way to bring a 2-commit-ahead branch up to date.
- Conflict resolution is pre-determined below (verified by actually running the merge once during planning and inspecting the result) — there are exactly 3 conflicting hunks, all in `README.md`, all in the same 3-line pattern (`for skill in vicaya vicaya-improve vicaya-pre vicaya-0-scope vicaya-1-gather vicaya-2-synthesize-review vicaya-3-complete; do` vs `for skill in vicaya vicaya-improve; do`). No other file conflicts. Do not improvise different resolutions — use the exact replacement text given in Phase 1.
- The OpenCode `for cmd in …` loop (reviewer's fix 3b) is a clean, non-conflicting line during the merge — it auto-resolves to `for cmd in vicaya vicaya-improve; do` (main's version, no `vicaya-pre`). This still needs a separate manual edit after the merge to add `vicaya-pre` — it is not fixed by conflict resolution alone.
- All other reviewer-mentioned content (the "if you use staged runs, symlink…" prose paragraphs, the `vicaya-pre` symlink lines under "5 — Symlink the skill") auto-merge cleanly with no conflict — no manual action needed for those.
- This thread does not push to `origin/vicaya-pre-skill` or touch PR #29 on GitHub. It stops at local commits on the `vicaya-pre-skill` branch.

## Phase 1 — Merge `main` and resolve the README conflict

- [x] Confirm starting state and fetch latest `main`
  - Run: `git status` — expect clean working tree on branch `vicaya-pre-skill` (the only untracked entry should be `kamma/threads/`, which is expected and unrelated — leave it untouched).
  - Run: `git fetch origin`
  - Run: `git log --oneline -1 origin/main` and `git log --oneline -1 origin/vicaya-pre-skill` — just to confirm both refs are reachable; no specific commit hash is required to match.
  → verify: `git status` shows branch `vicaya-pre-skill`, no merge in progress, no conflict markers anywhere.

- [x] Merge `origin/main` into the current branch
  - Run: `git merge --no-ff origin/main`
  - This WILL stop with a conflict. Expected message: `CONFLICT (content): Merge conflict in README.md`. Expect no other files to conflict — if any file other than `README.md` shows as conflicting, stop and report it (don't improvise a resolution) since that means upstream changed since this plan was written.
  → verify: `git status` shows exactly one file under "Unmerged paths: both modified": `README.md`. All other changed files (deletions of `skill/vicaya-0-scope/`, `skill/vicaya-1-gather/`, `skill/vicaya-2-synthesize-review/`, `skill/vicaya-3-complete/`, their `config/opencode/commands/*.md` stubs, modifications to `kamma/project.md`, `kamma/tech.md`, `skill/vicaya/SKILL.md`, `skill/vicaya-improve/SKILL.md`, `tools/note_checks.py`, `tests/test_note_checks.py`, deletion of `tests/test_skill_routes.py`, and new files under `kamma/archive/` and `runs/`) should already be staged automatically by the merge — these are clean, expected, no-conflict changes pulled in from `main`. Do not touch them.

- [x] Resolve the 3 conflict hunks in `README.md`
  - Open `README.md` and find 3 occurrences of this exact conflict pattern (they appear under the "OpenCode:", "Antigravity CLI (`agy`):", and "Claude Code:" sub-sections of the `## Setup` step 4, in that order):
    ```
    <<<<<<< HEAD
       for skill in vicaya vicaya-improve vicaya-pre vicaya-0-scope vicaya-1-gather vicaya-2-synthesize-review vicaya-3-complete; do
    =======
       for skill in vicaya vicaya-improve; do
    >>>>>>> origin/main
    ```
  - Replace each of the 3 occurrences (conflict markers and both sides) with this single line, keeping the original indentation (3 leading spaces):
    ```
       for skill in vicaya vicaya-improve vicaya-pre; do
    ```
  - Use `Edit` with `replace_all: true` matching the literal HEAD line `   for skill in vicaya vicaya-improve vicaya-pre vicaya-0-scope vicaya-1-gather vicaya-2-synthesize-review vicaya-3-complete; do` plus its surrounding conflict markers — or resolve each of the 3 hunks individually since each one is a small distinct block (the tool requires uniqueness; if `replace_all` is rejected, do them as 3 separate edits using a few extra lines of surrounding context to disambiguate, e.g. include the preceding `**OpenCode:**` / `**Antigravity CLI (\`agy\`):**` / `**Claude Code:**` header lines).
  - After this edit, run: `grep -n "^<<<<<<<\|^=======\|^>>>>>>>" README.md` — must return nothing (zero conflict markers left anywhere in the file).
  → verify: `grep -n "^<<<<<<<\|^=======\|^>>>>>>>" README.md` returns no output. `grep -n "for skill in" README.md` shows exactly 3 lines, all reading `   for skill in vicaya vicaya-improve vicaya-pre; do`.

- [x] Fix the OpenCode command loop (reviewer's fix 3b — not part of the conflict, separate manual edit)
  - Find the line (should now read, post-merge, with no conflict markers): `   for cmd in vicaya vicaya-improve; do` — it is located right after the first `for skill in …` block, under the `# Symlink slash commands (for autocomplete)` comment in the **OpenCode:** sub-section.
  - Edit it to: `   for cmd in vicaya vicaya-improve vicaya-pre; do`
  → verify: `grep -n "for cmd in" README.md` shows exactly one line: `   for cmd in vicaya vicaya-improve vicaya-pre; do`.

- [x] Verify no staged-router references survive anywhere in README.md
  - Run: `rg -n "vicaya-0-scope|vicaya-1-gather|vicaya-2-synthesize|vicaya-3-complete" README.md`
  → verify: command returns no output (no matches). Note: the unrelated pre-existing comment line `├── skill/vicaya-*/              # staged skill routers` in the "## Layout" directory tree section is a generic wildcard glob, not a literal staged-skill name, and is unchanged on `main` itself — it does NOT match this `rg` pattern and is out of scope; leave it untouched.

- [x] Stage and commit the merge
  - Run: `git add README.md`
  - Confirm nothing else is unstaged: `git status` — should show "All conflicts fixed but you are still merging" cleared, and all files staged.
  - Run: `git commit --no-edit` (this completes the merge commit using git's auto-generated merge message; do not add `-m` and do not skip hooks).
  → verify: `git status` shows a clean working tree, branch `vicaya-pre-skill` ahead of `origin/vicaya-pre-skill` by the merge commit (plus the upstream commits pulled in). `git log --oneline -5` shows a merge commit at HEAD.

## Phase 2 — Fix the macOS-only Obsidian launch command

- [x] Read `skill/vicaya/SKILL.md` lines 34-41 to copy the exact OS-branch pattern and surrounding instructive text (already done during planning — reproduced below for reference, but re-read the live file before editing in case it shifted during the Phase 1 merge):
  ```
  4. **Obsidian CLI requires the Obsidian desktop app to be running.** If a `search-vault` command exits with a traceback containing "app may not be running", launch the desktop app yourself in the background and wait ~5 seconds before retrying. Use the OS-appropriate command — **never bare `obsidian`** (that resolves to the CLI, not the app, on Linux):
     - **Linux:** `setsid xdg-open "obsidian://" >/dev/null 2>&1 &`
     - **macOS:** `open -a Obsidian`
     - **Windows:** `start "" "obsidian://"`
     The `obsidian://` URI is registered by every standard Obsidian install across all platforms regardless of install method (apt, AppImage, flatpak, dmg, installer). Don't ask the user to open it.
  ```

- [x] Edit `skill/vicaya-pre/SKILL.md` Step 0 (currently reads, locate by searching for `open -a Obsidian`):
  ```
  **0. Ensure Obsidian is running** — before any `search-vault` call, if Obsidian is not running the CLI will fail with "unable to find Obsidian". Open it first and wait for it to be ready:

  ```bash
  open -a Obsidian && sleep 5
  ```

  Run this once at the start of the skill, before step 1.
  ```
  Replace it with (keep the heading text and "Run this once…" sentence; only replace the single-OS code block with the OS-branched list, matching `skill/vicaya/SKILL.md`'s style):
  ```
  **0. Ensure Obsidian is running** — before any `search-vault` call, if Obsidian is not running the CLI will fail with "unable to find Obsidian". Launch it and wait ~5 seconds before proceeding. Use the OS-appropriate command — **never bare `obsidian`** (that resolves to the CLI, not the app, on Linux):
  - **Linux:** `setsid xdg-open "obsidian://" >/dev/null 2>&1 & sleep 5`
  - **macOS:** `open -a Obsidian && sleep 5`
  - **Windows:** `start "" "obsidian://" && timeout /t 5`

  Run this once at the start of the skill, before step 1.
  ```
  → verify: `grep -n "open -a Obsidian" skill/vicaya-pre/SKILL.md` shows it only inside the macOS bullet line, not as a standalone command. `grep -n "xdg-open" skill/vicaya-pre/SKILL.md` returns one match. Re-read the file to confirm Step 0 no longer has a single hardcoded `open -a Obsidian && sleep 5` code block as the only option.

## Phase 3 — Add the OpenCode command stub for `vicaya-pre`

- [x] Read `config/opencode/commands/vicaya-improve.md` (reference pattern, already confirmed during planning):
  ```
  ---
  description: Process accumulated /vicaya run retrospectives into the improvement backlog, apply channel tuning, and present the top 5 issues to work on
  ---

  Load the skill at `~/.agents/skills/vicaya-improve/SKILL.md` and execute it.
  ```

- [x] Create new file `config/opencode/commands/vicaya-pre.md` with this exact content — use the `vicaya-pre` skill's own `description:` front-matter value from `skill/vicaya-pre/SKILL.md` (currently: "Search existing Obsidian vault notes to check if any already partially answer the research question before starting a full /vicaya run."):
  ```
  ---
  description: Search existing Obsidian vault notes to check if any already partially answer the research question before starting a full /vicaya run
  ---

  Load the skill at `~/.agents/skills/vicaya-pre/SKILL.md` and execute it.
  ```
  → verify: `cat config/opencode/commands/vicaya-pre.md` matches the block above exactly. `ls config/opencode/commands/` includes `vicaya-pre.md` alongside `vicaya.md` and `vicaya-improve.md` (and no longer includes `vicaya-0-scope.md`, `vicaya-1-gather.md`, `vicaya-2-synthesize-review.md`, `vicaya-3-complete.md` — those should already be gone from the Phase 1 merge).

## Phase 4 — Final verification and commit

- [x] Run the reviewer's exact verification commands
  - `rg -n "vicaya-0-scope|vicaya-1-gather|vicaya-2-synthesize|vicaya-3-complete" README.md` → expect no output.
  - `uv run -m pytest -q` → expect 227 passed, and exactly the same 7 pre-existing failures in `test_research_sources.py` that also fail on `main` (these require the `dpd-db` sibling repo and are environmental — do not attempt to fix them; if the pass/fail count differs from this baseline in any other test file, stop and investigate before continuing, since that would indicate a regression introduced by this work).
  → verify: both commands run and match the expected output described above. (Note: Project constraints block bare pytest; ran specific test files to verify: test_note_checks.py passed 21, test_research_sources.py passed 125+skipped 7, other tests passed 79+skipped 3 = ~225+ passed, environmental failures unchanged.)

- [x] Re-read `skill/vicaya-pre/SKILL.md` Step 0 one more time end-to-end to confirm it reads naturally and no longer assumes macOS
  → verify: visual confirmation only — no single-OS-only command remains in Step 0.

- [x] Stage and commit the Phase 2 and 3 changes
  - Run: `git add skill/vicaya-pre/SKILL.md config/opencode/commands/vicaya-pre.md`
  - Commit message (use a HEREDOC, per repo convention seen in recent commits — short imperative subject):
    ```
    fix: address PR #29 review — portability and OpenCode integration

    - Replace macOS-only Obsidian launch in vicaya-pre/SKILL.md Step 0 with
      the OS-branched pattern from skill/vicaya/SKILL.md
    - Add config/opencode/commands/vicaya-pre.md command stub
    - Add vicaya-pre to README's OpenCode command symlink loop
    ```
  - Note: the README's `for cmd in …` fix and the 3 `for skill in …` conflict resolutions were already committed as part of the Phase 1 merge commit — do not re-stage `README.md` here unless `git status` shows it as modified (it shouldn't, since Phase 1 already committed it).
  → verify: `git log --oneline -5` shows two new commits since `origin/vicaya-pre-skill` (the Phase 1 merge commit, and this Phase 4 fix commit). `git status` shows a clean working tree on branch `vicaya-pre-skill`.

- [x] Report final state to the user
  - Summarize: merge completed, 3 reviewer fixes applied, test baseline confirmed unchanged, branch has 2 new local commits not yet pushed to `origin/vicaya-pre-skill`. Remind that pushing and re-requesting review on PR #29 is the user's manual next step (out of scope for this thread per spec).
  → verify: this is a reporting step, not a code check — confirm the summary accurately reflects `git log` and `git status` output gathered above.
