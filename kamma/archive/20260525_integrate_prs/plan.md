# Plan — Integrate PRs #5 and #6

## Architecture Decisions
- Apply PR #6 first (Python + gitignore) then PR #5 (SKILL.md) — independent, order doesn't matter
  but separating them keeps verification clean
- Apply changes via Edit tool, not by checking out PR branches — avoids merge commits and keeps
  the diff minimal

## Phase 1 — Apply PR #6: tools/research_sources.py + .gitignore

- [ ] Wrap `_calibre_fts_available` subprocess call in try/except TimeoutExpired (return False)
  → verify: `python -c "import ast; ast.parse(open('tools/research_sources.py').read())"` exits 0

- [ ] Wrap `_calibre_fts_search` subprocess call in try/except TimeoutExpired (return [])
  → verify: same ast.parse check

- [ ] Wrap `_calibre_metadata_search` subprocess call in try/except TimeoutExpired (return [])
  → verify: same ast.parse check

- [ ] Add `--approval-mode plan` to `gemini_cross_check` subprocess args
  → verify: grep confirms `["gemini", "--approval-mode", "plan", "-p", prompt]` present

- [ ] Add `temp/`, `.claude/settings.local.json`, `vault` to `.gitignore`
  → verify: grep confirms all three lines present in .gitignore

- [ ] Phase 1 verification: `python -c "import ast; ast.parse(open('tools/research_sources.py').read())"`
  → verify: exits 0 with no output

## Phase 2 — Apply PR #5: skill/vicaya/SKILL.md

- [ ] Replace inline heredoc PDF block with temp-file approach + macOS DYLD_LIBRARY_PATH block
  → verify: SKILL.md contains `temp/gen_pdf_run.py` and `DYLD_LIBRARY_PATH`; does NOT contain `PDFEOF`

- [ ] Phase 2 verification: grep confirms no `PDFEOF` in SKILL.md; `temp/gen_pdf_run.py` present twice
  (once in the write instruction, once in the execute instruction)

## Phase 3 — Close PRs

- [ ] Post comment on PR #5 summarising the fix, then close it
  → verify: `gh pr view 5 --json state` shows `CLOSED`

- [ ] Post comment on PR #6 summarising the fix, then close it
  → verify: `gh pr view 6 --json state` shows `CLOSED`
