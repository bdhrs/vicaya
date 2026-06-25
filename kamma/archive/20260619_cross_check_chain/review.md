## Thread
- **ID:** 20260619_cross_check_chain
- **Objective:** Replace the hardwired OpenRouter-HTTP cross-check (and legacy `gemini_cross_check`) with a single `VICAYA_CROSS_CHECK_CHAIN`-driven `app:model` dispatch over `opencode`/`agy` subprocesses.

## Files Changed
- `tools/research_sources.py` — new `_parse_cross_check_chain`, `_run_opencode`, `_run_agy`; `cross_check()` rewritten to dispatch over the chain; all OpenRouter-HTTP/`gemini_cross_check`/`gemini-cross-check` code removed.
- `data/openrouter_models.json` — deleted.
- `tests/test_cross_check.py` — rewritten around `monkeypatch.setattr(rs, "_run_opencode"/"_run_agy", ...)`; covers parsing, fallthrough, all-fail, unknown-app, sentinel-text-unchanged.
- `tests/test_research_sources.py` — `TestGeminiCrossCheck` and the `gemini_cross_check` import removed.
- `.env.example` — new `VICAYA_CROSS_CHECK_CHAIN` block (purpose, format, single- and multi-entry examples, pro-tier-model recommendation, blank-disables semantics).
- `README.md` — cross-check table row, setup step 2, dependency-check block updated to `opencode`/`agy`.
- `skill/vicaya/README.md` — dependency table: `gemini` CLI row replaced with `opencode`/`agy` rows.
- `skill/vicaya/SKILL.md` — env-vars bullet, subcommand table, auto-logging paragraph, Phase 6 mechanism paragraph, troubleshooting entry, Rule F5 host-app example all updated from OpenRouter/Gemini-CLI to the chain/`agy`; `gemini-cross-check` row and out-of-scope Antigravity/`gemini` CLI product references left untouched per spec.
- `kamma/tech.md` — **review fix:** Cross-check tech note still described the deleted OpenRouter-HTTP mechanism; rewrote it to describe the chain/subprocess mechanism (workflow.md requires tech.md kept in sync; this was missed during implementation).
- `_SELF_REVIEW_SENTINEL` in `tools/research_sources.py` — **review fix:** items 3-5 of the embedded checklist rewritten to match the external-review prompt's rubric (see Findings #4).
- `tests/test_cross_check.py` — **review fix:** `test_self_review_lists_all_checklist_items` updated to assert the new checklist labels.

## Findings

| # | Severity | Location | What | Why | Fix |
|---|----------|----------|------|-----|-----|
| 1 | minor | `kamma/tech.md:14` | Cross-check tech note still described OpenRouter-HTTP/`data/openrouter_models.json`, which this thread deleted | Stale tech doc misleads future agents about how `cross_check()` works | Fixed during review — rewrote to describe `VICAYA_CROSS_CHECK_CHAIN` subprocess dispatch |
| 2 | minor | `.env.example:68-77` | Block gave two single-entry examples but never showed the pipe-separated multi-entry chain format users actually need | User-reported: format/separator wasn't demonstrated | Fixed during review — added an explicit two-entry pipe-separated example, plus a recommendation to use a pro/flagship-tier model for cross-check quality (user request) |
| 3 | major | `tools/research_sources.py:1497-1526` (CodeRabbit) | `_run_opencode`/`_run_agy` caught only `subprocess.TimeoutExpired`/`FileNotFoundError`; other `OSError` variants (e.g. `PermissionError` on a non-executable binary) would propagate uncaught instead of falling through to the next chain entry / `# SELF_REVIEW:` | Defeats the documented "never let either propagate" fallback contract for any OS-level launch failure that isn't a plain missing-binary | Fixed during review — broadened both except clauses to `(subprocess.TimeoutExpired, OSError)`, a strict superset (`FileNotFoundError` is already an `OSError` subclass); ruff clean, all 16 cross-check tests still pass |
| 4 | major | `tools/research_sources.py:1534-1546` (CodeRabbit) | Embedded `# SELF_REVIEW:` checklist items 3-5 ("Citation quality", "Internal consistency", "Overreach") differ from the external-review prompt's items 3-5 ("Disputed consensus", "Factual accuracy", "General") in `skill/vicaya/SKILL.md:1648-1650` — items 1-2 already matched | Self-review fallback audited the synthesis against a different rubric than an actual external reviewer would, so it wasn't a true substitute when the chain is empty/all entries fail. Git history confirms the external prompt was deliberately sharpened in commit `8402d10` (2026-05-20); the sentinel, added 3 days later in `0499d74`, copied the older pre-sharpening wording instead — a stale-copy bug, not an intentional difference | Fixed during review (user-requested) — rewrote sentinel items 3-5 to match the external prompt verbatim; updated `tests/test_cross_check.py::test_self_review_lists_all_checklist_items` to assert the new labels; `# SELF_REVIEW:` prefix and items 1-2 untouched, so the trigger contract and chain-dispatch logic this thread built are unaffected |

## Fixes Applied
- `kamma/tech.md` cross-check description rewritten to match the new mechanism.
- `.env.example` cross-check block: added explicit multi-entry pipe-separated example and a pro-tier-model recommendation.
- `tools/research_sources.py`: `_run_opencode`/`_run_agy` now catch `OSError` (not just `FileNotFoundError`) alongside `TimeoutExpired`.
- `tools/research_sources.py`: `_SELF_REVIEW_SENTINEL` checklist items 3-5 realigned to match the external-review prompt's rubric; `tests/test_cross_check.py` updated to match.

## Test Evidence
- `uv run ruff check tools/research_sources.py tests/test_cross_check.py tests/test_research_sources.py` → pass
- `uv run pytest tests/test_cross_check.py -q` → 16 passed
- `uv run pytest tests/test_cross_check.py tests/test_research_sources.py -q` → 157 passed, 7 skipped, 1 failed (`TestSearchVault::test_search_returns_list` — pre-existing, unrelated: requires Obsidian desktop app running, documented in `plan.md` Task 3.4)
- `uv run python3 -c "import tools.research_sources"` → imports cleanly, no leftover symbol references
- `grep -rn "OPENROUTER|gemini_cross_check|gemini-cross-check|openrouter_models" tools/research_sources.py` → no matches
- `grep -rn "openrouter_models.json|gemini-cross-check|OPENROUTER_API_KEY" .env.example skill/vicaya/SKILL.md README.md` → no matches
- `grep -n "Gemini CLI" skill/vicaya/SKILL.md skill/vicaya/README.md` → no matches; out-of-scope `README.md` Gemini-CLI-product lines confirmed untouched
- Live verification (Tasks 3.1/3.2, per plan.md): `agy` alone and `opencode`+OpenRouter alone both confirmed working with real subprocess calls/credentials; Task 3.3 (`opencode`+Gemini direct) explicitly skipped — no Google credential configured, user doesn't need this combination, documented in plan.md
- `coderabbit review --agent` → 2 findings, both fixed (`OSError` catch; self-review checklist rubric realignment)

## Verdict
PASSED
- Review date: 2026-06-25
- Reviewer: Claude (same agent that implemented — review independence is reduced; CodeRabbit run provides an independent second pass)
