## Thread
- **ID:** 20260618_vicaya_depth_gemini
- **Objective:** Fix Gemini under-quoting in Vicaya notes by adding Evidence Fidelity Rule (prompt) + mechanical under-quoted-evidence check (validator)

## Files Changed
- `skill/vicaya/SKILL.md` — Added Evidence Fidelity Rule in Phase 5 + Phase 7; enforcement-gap fix (read warnings, re-validate before PDF); `agent` frontmatter format changed from model-slug to host-app
- `tools/note_checks.py` — Added `under-quoted-evidence` check in `_validate_body` (footnote_defs >= 3 AND blockquote_lines < footnote_defs, severity=error); indented blockquote fix (`line.startswith(">")` → `line.lstrip().startswith(">")`)
- `tests/test_note_checks.py` — Added `test_under_quoted_evidence_error` and `test_under_quoted_evidence_counts_indented_blockquotes`
- `kamma/threads/20260618_vicaya_depth_gemini/spec.md` — Spec (new)
- `kamma/threads/20260618_vicaya_depth_gemini/plan.md` — Plan (new)
- `kamma/threads/20260618_vicaya_depth_gemini/handoff.md` — Live handoff tracking 6 empirical Gemini runs (new)

## Findings
| # | Severity | Location | What | Why | Fix |
|---|----------|----------|------|-----|-----|
| 1 | minor | `skill/vicaya/SKILL.md:1983-1985` | Enforcement instructions cite `under-quoted-evidence` as a `warning` example, but severity is now `error` | Stale example — misleading even though the prose instruction works for any warning | Update the example or rephrase to mention errors instead of warnings |
| 2 | minor | `plan.md:102-122` | Phase 4 checkboxes still `[ ]` despite handoff.md confirming completion across 6 runs | Plan.md is the source of truth per `workflow.md`; stale checkboxes misrepresent state | Mark Phase 4 sub-items as `[x]` |

## Fixes Applied
- `skill/vicaya/SKILL.md:1983-1987` — Updated enforcement instructions to reference errors (not just warnings), since `under-quoted-evidence` is now `severity="error"`
- `plan.md:102-122` — Marked Phase 4 checkboxes `[x]` with completion notes to reflect actual state per handoff.md

## Test Evidence
- `uv run pytest tests/test_note_checks.py -q` → 21 passed
- `uv run pytest tests/test_validate_note.py -q` → 4 passed
- `uv run ruff check tools/note_checks.py tests/test_note_checks.py` → All checks passed
- `uv run pyright tools/note_checks.py tests/test_note_checks.py` → 0 errors, 0 warnings
- `uv run pyrefly check --search-path . tools/note_checks.py tests/test_note_checks.py` → 0 errors
- Sibling route-list heading audit: `### Phase 5 — Synthesis` and `### Phase 7 — Write the note` resolve correctly in both `vicaya-2-synthesize-review` and `vicaya-3-complete` → verified

## Verdict
PASSED
- Review date: 2026-06-19
- Reviewer: Claude Sonnet 4.6 (via opencode /kamma:3-review)
