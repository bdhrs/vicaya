# Spec — Integrate PRs #5 and #6

## Overview
Integrate two open pull requests from Devamitta Bhikkhu into main. Both are standalone
bug fixes with no conflicts. Review each for correctness, apply, then close the PRs.

## GitHub Issues / PRs
- PR #5: `fix/pdf-weasyprint-macos` — weasyprint macOS DYLD_LIBRARY_PATH self-exec fix
- PR #6: `fix/calibre-timeouts-and-gitignore` — TimeoutExpired handling for calibredb + gitignore cleanup

## What it should do

### PR #5 — `skill/vicaya/SKILL.md`
- Convert the inline `uv run python3 - << 'PDFEOF'` heredoc in the PDF generation section
  to a proper temp-file approach: write the script to `temp/gen_pdf_run.py` then execute
  with `uv run temp/gen_pdf_run.py`
- Add macOS DYLD_LIBRARY_PATH self-exec block at the top of the script: detects Darwin,
  re-execs itself with `/opt/homebrew/lib` prepended to DYLD_LIBRARY_PATH — no-op on Linux

### PR #6 — `tools/research_sources.py`
- Wrap `_calibre_fts_available`: add try/except TimeoutExpired around subprocess.run,
  return False on timeout
- Wrap `_calibre_fts_search`: add try/except TimeoutExpired, return [] on timeout
- Wrap `_calibre_metadata_search`: add try/except TimeoutExpired, return [] on timeout
- `gemini_cross_check`: add `--approval-mode plan` flag to suppress interactive prompts

### PR #6 — `.gitignore`
- Add `temp/` — temp scripts should not be committed
- Add `.claude/settings.local.json` — per-machine Claude config
- Add `vault` — local Obsidian vault clone

## Assumptions & uncertainties
- Both PRs are authored by the same contributor (Devamitta Bhikkhu) and appear intended
  for direct merge — no merge conflicts detected between them
- `vault` in .gitignore is unanchored (matches any `vault` path); the PR adds it without
  a leading `/` — preserved as-is per PR intent
- The macOS fix is only needed when running on Darwin; Linux behavior unchanged

## Constraints
- Do NOT commit — user handles git
- Preserve existing indentation and formatting in all files
- Only touch lines explicitly changed by the PRs

## How we'll know it's done
- All three files match the expected post-PR state
- PR comments posted, PRs closed
- `python -c "import ast; ast.parse(open('tools/research_sources.py').read())"` passes
