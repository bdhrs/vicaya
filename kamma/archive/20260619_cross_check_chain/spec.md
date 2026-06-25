# Spec — Generalize cross-check to a configurable app/model chain

## Overview
The Phase 6 cross-check ("a second model reviews the synthesis") is currently
hardwired to OpenRouter: `cross_check()` in `tools/research_sources.py` POSTs
directly to OpenRouter's HTTP API using a fixed 2-model fallback chain read
from `data/openrouter_models.json`, authenticated with `OPENROUTER_API_KEY`
(env or `~/.local/share/opencode/auth.json`). A separate legacy path,
`gemini_cross_check()` / the `gemini-cross-check` CLI subcommand, shells out
to the `gemini` CLI directly and is documented as an unused ad-hoc fallback.

This thread replaces both with a single generalized mechanism driven by a new
`.env` variable, so the user can route Phase 6 cross-check through whichever
local CLI agent/model they currently have credentials for — without editing
Python.

## What it should do
- Add a new `.env` variable, `VICAYA_CROSS_CHECK_CHAIN`, holding a
  pipe-separated (`|`) list of `app:model` entries, tried in order, e.g.:
  ```
  VICAYA_CROSS_CHECK_CHAIN=opencode:deepseek/deepseek-v4-flash|opencode:openrouter/deepseek/deepseek-v4-flash|agy:Gemini 3.5 Flash (High)
  ```
  This follows the existing pipe-separated convention already used by
  `VICAYA_LIBRARY_FOLDERS` in `.env.example`.
- Supported `app` values at launch: `opencode` and `agy` (both confirmed
  installed locally: `/opt/homebrew/bin/opencode`, `/Users/deva/.local/bin/agy`).
  - `opencode`: invoke `opencode run -m <model> <prompt>` (subprocess, no
    shell, prompt passed as the positional message argument — not via
    `python -c` style string interpolation, so no quoting risk). `<model>`
    is the *entire* string after the first `:` in the chain entry, passed
    through verbatim (it may itself contain `/`, e.g.
    `openrouter/deepseek/deepseek-v4-flash`).
  - `agy`: invoke `agy --print "<prompt>" --model "<model>"` (subprocess,
    no shell). `<model>` is passed through verbatim, e.g.
    `Gemini 3.5 Flash (High)`.
  - Vicaya does **not** manage API keys for either app. Each app is expected
    to already have its own provider credentials configured out-of-band
    (`opencode auth login`, or whatever `agy` uses) — confirmed `agy --help`
    exposes no API-key flag, and `opencode`'s own `auth.json` already has
    `openai`/`deepseek` entries independent of vicaya's `.env`.
- Rewrite `cross_check(prompt, timeout)` to:
  1. Parse `VICAYA_CROSS_CHECK_CHAIN` into an ordered list of `(app, model)`
     tuples. Empty/unset → skip straight to step 4 (no chain to try).
  2. For each tuple, in order: subprocess-run the matching command above,
     with the existing per-call `timeout` parameter applied per attempt
     (not divided across the chain).
  3. On the first tuple that returns exit code 0 with non-empty stdout
     (after `.strip()`), stamp it via the existing `annotate_citations()`
     and return it immediately — do not try later entries.
  4. If every tuple fails (unknown `app` token, non-zero exit, empty
     output, timeout, or the chain was empty/unset), return the existing
     `_SELF_REVIEW_SENTINEL` unchanged — same checklist text, same trigger
     contract callers already rely on (`# SELF_REVIEW:` prefix).
- Remove entirely (replaced, not deprecated):
  - `_load_openrouter_key`, `_load_openrouter_models`,
    `_OPENROUTER_URL`, `_OPENROUTER_MODELS_PATH`, `_OPENROUTER_MAX_MODELS`,
    `_OPENCODE_AUTH_PATH` constants/functions in `tools/research_sources.py`.
  - `data/openrouter_models.json`.
  - `gemini_cross_check()` and the `gemini-cross-check` CLI subcommand
    (`pg` parser, `_handle_gemini_cross_check`).
  - The direct-HTTP-to-OpenRouter code path (`urllib.request` call in
    `cross_check`).
- `annotate_citations()` (citation `[VERIFIED]`/`[REJECTED]` stamping) is
  unchanged and still applied to whichever app's output succeeds.
- The `cross-check` CLI subcommand (reads prompt from stdin, `--timeout`
  flag) keeps its name and interface — only its internal implementation
  changes.
- Update `.env.example`: replace any OpenRouter-specific commentary with the
  new `VICAYA_CROSS_CHECK_CHAIN` var, documented with the same style as
  other vars (purpose, format, example, "leave blank to disable" semantics
  for falling back to self-review).
- Update `README.md`:
  - Line 33 (`| **Gemini cross-check** | ... |`) — rename/reword to describe
    the configurable chain (e.g. "Second model reviews the draft, via
    whichever app/model is configured in `VICAYA_CROSS_CHECK_CHAIN`"), not
    Gemini specifically.
  - Line 39 (Setup step 2, "Install whichever of these you want to use:
    ... `gemini` CLI") — replace `gemini` CLI with `opencode` / `agy`
    (whichever the user configures), since `gemini` is no longer a
    supported cross-check backend.
  - Line 184 (`which gemini      # Gemini CLI — optional (cross-check
    model)`) in the dependency-check block — replace with `which opencode`
    / `which agy` (optional, cross-check chain) reflecting the new apps.
- Update `skill/vicaya/SKILL.md` wherever it currently describes the
  OpenRouter chain or `gemini-cross-check` (lines ~88, 118, 120, 402,
  1610–1657, 2077 per current grep) to describe the new chain
  mechanism instead. Keep the IRON RULE / no-attribution language and the
  `# SELF_REVIEW:` fallback behavior description unchanged — only the
  "how cross-check reaches a second model" mechanics change.
- **Also rename "Gemini CLI" as a host-app name to "agy"** wherever it
  appears as an app/CLI identity (not as a model-family name like "Gemini
  3.5 Flash"), since this thread removes the standalone `gemini` CLI app
  entirely in favor of `opencode`/`agy`:
  - `skill/vicaya/SKILL.md` Rule F5 (~line 1930): drop `Gemini CLI` from
    the host-app parenthetical example list (`Claude Code, Antigravity,
    Codex CLI, Gemini CLI`) and the standalone example line (~1949,
    `Gemini CLI: "Gemini 2.5 Pro (Gemini CLI)"`) — replace with an `agy`
    example, e.g. `agy: "Gemini 2.5 Pro (agy)"`. Keep the separate
    `Antigravity` example (~1948, `Gemini running in Antigravity:
    "Gemini 3.5 Flash (Antigravity)"`) as-is — that's the GUI app, a
    distinct host from the `agy` CLI.
  - `skill/vicaya/README.md` dependency table (line 67): change
    `| `gemini` CLI | optional (cross-check) | `gemini --version` |` to
    reference `opencode`/`agy` instead (matching the main `README.md`
    Task 2.3 dependency-block update).
  - **Explicitly out of scope:** `README.md` lines ~202–203 (`npm install
    -g @google/gemini-cli` setup instructions) and ~307/330
    (`~/.agents/skills` shared by "Gemini CLI, OpenCode, and Codex") —
    these describe the real Google `gemini` CLI product and an actual
    skill-directory convention unrelated to vicaya's cross-check
    mechanism. Do not touch them; renaming would misstate which app
    reads which directory (`agy`/Antigravity uses `~/.gemini`, not
    `~/.agents`, per `kamma/archive/20260618_move_vicaya_pre_skill`).
- Rewrite `tests/test_cross_check.py`: drop the OpenRouter-HTTP and
  auth.json-key tests; add tests that monkeypatch `subprocess.run` to cover:
  chain parsing, first-entry success, first-entry failure falling through
  to second entry, all-entries-failing → SELF_REVIEW, empty/unset chain →
  SELF_REVIEW, unknown `app` token in a chain entry → skipped/treated as
  failure for that entry. Keep `test_self_review_lists_all_checklist_items`
  (sentinel text itself is unchanged).

## Assumptions & uncertainties
- **Confirmed by inspection (not guesses):** `opencode run --help` shows
  `-m, --model` takes `provider/model` and runs one-shot, printing to stdout
  by default (no `-p/--print` flag needed/exists for `opencode run`). `agy
  --help` shows `--print`/`-p` and `--model`, and `agy models` lists exactly
  the example string from the request (`Gemini 3.5 Flash (High)`).
- **To be verified live, not just mocked** (see "How we'll know it's done"):
  whether `opencode run -m openrouter/<vendor>/<model>` is a valid provider
  id for OpenRouter-routed models, and whether `opencode` can reach Gemini
  directly. `opencode auth list` currently shows only `openai` and
  `deepseek` configured — there is **no Google/Gemini credential set up for
  opencode yet**. Getting `opencode with gemini api` working will require
  either `opencode auth login` for the Google provider, or a `GEMINI_API_KEY`
  / `GOOGLE_GENERATIVE_AI_API_KEY` env var opencode picks up automatically
  (unconfirmed which env var name opencode expects — to be determined during
  live verification, not assumed). This may require the user to do an
  interactive `opencode auth login` step that an agent cannot complete
  unattended.
- **Assumed:** chain entries are `app:model` with exactly one `:` separating
  app from model (model itself may contain `/` but is assumed not to contain
  a literal `:` — if it does, this thread does not handle escaping). Split
  on the *first* `:` only.
- **Assumed:** per-call timeout uses the existing `timeout` parameter
  (default currently 180s for `cross-check`) applied to each chain entry
  individually, not the whole chain — consistent with "try app A within Ns,
  then app B within Ns" rather than a shared budget.
- Not investigating whether `opencode`/`agy` are installed/on `$PATH` at
  call time beyond what `subprocess.run` naturally reports (a missing binary
  surfaces as `FileNotFoundError`, which the implementation must catch and
  treat as that entry's failure, falling through the chain).

## Constraints
- No shell=True / string-interpolated subprocess calls — pass prompt and
  model as separate argv list elements (matches existing `gemini_cross_check`
  precedent and avoids quoting injection).
- Do not change the `# SELF_REVIEW:` sentinel text/checklist — callers in
  `SKILL.md` Phase 6 key off the `# SELF_REVIEW:` prefix verbatim.
- Do not change the `cross-check` CLI subcommand's external interface
  (stdin prompt, `--timeout` flag, stdout output) — only its internals.

## How we'll know it's done
- `uv run pytest tests/test_cross_check.py` passes with the rewritten
  subprocess-based test suite.
- `VICAYA_CROSS_CHECK_CHAIN` unset → `cross_check("test")` returns the
  `# SELF_REVIEW:` sentinel (verified by test, not live call).
- A chain with one working entry (mocked) returns that entry's annotated
  text; a chain where entry 1 fails and entry 2 succeeds (mocked) returns
  entry 2's text, proving fallthrough.
- `data/openrouter_models.json`, `gemini_cross_check`, and
  `gemini-cross-check` no longer exist in the codebase (`grep` returns
  nothing outside `kamma/` history/specs).
- `.env.example`, `SKILL.md`, and `README.md` no longer reference
  `OPENROUTER_API_KEY` / the OpenRouter HTTP chain / the `gemini` CLI /
  `gemini-cross-check` in the cross-check context.
- **Live verification (real subprocess calls, real credentials, no
  mocking)** — run the CLI `cross-check` subcommand (or call `cross_check()`
  directly) against each of these three configurations and confirm each
  returns real model text (not `# SELF_REVIEW:`, not an error):
  1. `agy:<model>` alone in the chain (e.g. `agy:Gemini 3.5 Flash (High)`) —
     exercises the `agy` dispatch path.
  2. `opencode:openrouter/<vendor>/<model>` alone in the chain (e.g.
     `opencode:openrouter/deepseek/deepseek-v4-flash`) — exercises opencode
     routed through OpenRouter, using the existing `OPENROUTER_API_KEY`.
  3. `opencode:google/<model>` (or whatever provider id opencode actually
     uses for Gemini — to be confirmed live) alone in the chain — exercises
     opencode reaching Gemini directly. **This combination has no
     credentials configured yet** (`opencode auth list` shows only
     `openai`/`deepseek`); setting this up (interactive `opencode auth
     login` or a `GEMINI_API_KEY` env var) is a precondition for this check
     and may require the user, not the implementing agent.
  Each of the three is checked independently (one-entry chain at a time),
  not as a single combined chain.

## What's not included
- Support for any `app` value beyond `opencode` and `agy`.
- A UI/CLI for editing `VICAYA_CROSS_CHECK_CHAIN` — it's a plain `.env` edit.
- Changing how `OPENROUTER_API_KEY` (or other provider keys) are configured
  for `opencode`/`agy` themselves — that remains each app's own auth setup,
  outside vicaya's `.env`.
