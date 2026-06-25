# Plan — Generalize cross-check to a configurable app/model chain

(See `spec.md` in this thread for full rationale, assumptions, and constraints.)

## Architecture Decisions

- **Dispatch, not registry.** `cross_check()` keeps its existing signature
  `cross_check(prompt: str, timeout: int = 180) -> str` so the one caller
  (`_handle_cross_check`) needs no changes. Internally it becomes a simple
  `if app == "opencode": ... elif app == "agy": ...` dispatch — no
  plugin/registry abstraction. Only two apps exist today; a registry would
  be premature.
- **Subprocess, not HTTP.** Both `opencode` and `agy` are invoked via
  `subprocess.run([...], capture_output=True, text=True, timeout=...)` with
  prompt/model passed as separate argv elements (never `shell=True`, never
  string-interpolated) — same shape as the `gemini_cross_check()` precedent
  being removed, just generalized to two binaries.
- **Config in `.env`, not a JSON file.** `VICAYA_CROSS_CHECK_CHAIN` is a
  single pipe-delimited (`|`) string of `app:model` entries, parsed with
  `split("|")` then `split(":", 1)` per entry. This matches the existing
  `VICAYA_LIBRARY_FOLDERS` pipe-delimited convention and satisfies the
  explicit requirement that this be `.env`-driven — `data/openrouter_models.json`
  is deleted, not repurposed.
- **Per-entry timeout, not a shared chain budget.** Each chain entry gets
  the full `timeout` value independently.
- **No API-key handling in vicaya.** Removing `_load_openrouter_key`,
  `_OPENCODE_AUTH_PATH`, etc. entirely — credential setup for `opencode`/`agy`
  is each app's own responsibility, outside this codebase.

## Model Strategy

Not used — this thread is implementation/doc-sync work with no
novel-architecture or 3+-interconnected-system design questions; mixed
Fast/Pro splitting would add overhead without benefit here. All phases run
on whichever model the user is already using.

---

## Phase 1 — Core dispatch implementation

- [x] **Task 1.1 — Implement the chain-dispatch `cross_check()`**
  In `tools/research_sources.py`:
  - Add `_parse_cross_check_chain() -> list[tuple[str, str]]`: read
    `os.environ.get("VICAYA_CROSS_CHECK_CHAIN", "")`, split on `|`, drop
    empty segments, split each remaining segment on `:` with `maxsplit=1`
    into `(app, model)`, strip whitespace from both, skip entries that
    don't contain a `:` or have an empty `app`/`model`. Return the ordered
    list (empty list if the var is unset/blank).
  - Add `_run_opencode(prompt: str, model: str, timeout: int) -> str | None`:
    `subprocess.run(["opencode", "run", "-m", model, prompt], capture_output=True, text=True, timeout=timeout)`.
    Return `result.stdout.strip()` if `returncode == 0` and stdout is
    non-empty after stripping; otherwise return `None`. Catch
    `subprocess.TimeoutExpired` and `FileNotFoundError`, returning `None`
    in both cases (do not let either propagate).
  - Add `_run_agy(prompt: str, model: str, timeout: int) -> str | None`:
    same shape, command
    `["agy", "--print", prompt, "--model", model]`.
  - Rewrite `cross_check(prompt, timeout=180)`:
    1. `chain = _parse_cross_check_chain()`.
    2. For `app, model` in `chain`: dispatch to `_run_opencode` or
       `_run_agy` based on `app` (any other `app` token → treat as a
       failed entry, continue to the next). If the call returns non-`None`
       text, return `annotate_citations(text)` immediately.
    3. If the loop exhausts without a hit (including when `chain` is
       empty), return `_SELF_REVIEW_SENTINEL` — unchanged.
  → verify: `uv run python3 -c "from tools import research_sources as rs; print(rs.cross_check('hi').startswith('# SELF_REVIEW'))"` prints `True` when `VICAYA_CROSS_CHECK_CHAIN` is unset in the shell env.

- [x] **Task 1.2 — Remove the legacy OpenRouter-HTTP and gemini-CLI paths**
  In `tools/research_sources.py`, delete entirely:
  - `_OPENROUTER_URL`, `_OPENROUTER_MODELS_PATH`, `_OPENROUTER_MAX_MODELS`,
    `_OPENCODE_AUTH_PATH` constants (around line 1491–1494).
  - `_load_openrouter_models()` and `_load_openrouter_key()` (around line
    1497–1521).
  - `gemini_cross_check()` (around line 1463–1486) and its
    `# ---------- Gemini cross-check ----------` section header.
  - The `# ---------- Cross-check (OpenRouter model chain) ----------`
    section header comment (replace with a comment matching the new
    mechanism, e.g. `# ---------- Cross-check (app/model chain) ----------`).
  - The `_handle_gemini_cross_check` function (around line 2115–2122).
  - The `pg = sub.add_parser("gemini-cross-check", ...)` block and its
    `pg.add_argument(...)` / `pg.set_defaults(...)` lines (around line
    2336–2341).
  - Delete the file `data/openrouter_models.json`.
  - `_SELF_REVIEW_SENTINEL` text stays exactly as-is — do not touch it.
  → verify: `grep -n "OPENROUTER\|gemini_cross_check\|gemini-cross-check\|openrouter_models" tools/research_sources.py` returns no matches; `test -f data/openrouter_models.json` exits non-zero (file gone).

- [x] **Task 1.3 — Rewrite `tests/test_cross_check.py`**
  Replace the whole file. Drop all `_load_openrouter_key` /
  `_load_openrouter_models` / `urllib` tests. Using `monkeypatch.setattr(rs, "_run_opencode", ...)` / `monkeypatch.setattr(rs, "_run_agy", ...)` (simpler and more
  direct than mocking `subprocess.run`), cover:
  - `_parse_cross_check_chain`: parses a two-entry chain correctly; returns
    `[]` for unset/blank env var; skips a malformed entry (no `:`).
  - `cross_check`: chain unset → `# SELF_REVIEW:` sentinel.
  - `cross_check`: single working `opencode:` entry → returns that text
    (annotated via `annotate_citations`, so assert on a prompt/response
    with no citations to keep the assertion simple, e.g. `"hello"` in →
    `"hello"` out).
  - `cross_check`: single working `agy:` entry → same, via `_run_agy`.
  - `cross_check`: first entry fails (`_run_opencode` returns `None`),
    second entry succeeds (`_run_agy` returns text) → returns the second
    entry's text, proving fallthrough.
  - `cross_check`: all entries fail → `# SELF_REVIEW:` sentinel.
  - `cross_check`: unknown `app` token in chain → treated as a failed
    entry (falls through / ends in `# SELF_REVIEW:` if it's the only
    entry).
  - Keep `test_self_review_lists_all_checklist_items` unchanged (sentinel
    text didn't change).
  → verify: `uv run pytest tests/test_cross_check.py -v` — all tests pass.

- [x] **Task 1.4 — Phase 1 verification**
  → verify: `uv run pytest tests/ -k "cross_check"` passes; `uv run python3 -c "import tools.research_sources"` imports cleanly with no `NameError`/leftover references to deleted symbols.

---

## Phase 2 — Documentation sync (`.env.example`, `SKILL.md`, `README.md`)

- [x] **Task 2.1 — `.env.example`**
  Add a new documented block (after the existing vars, matching the file's
  existing comment style) for `VICAYA_CROSS_CHECK_CHAIN`: explain it's a
  pipe-separated `app:model` list tried in order for the Phase 6
  cross-check, name the two supported `app` values (`opencode`, `agy`),
  give the two example entries from the spec
  (`opencode:openrouter/deepseek/deepseek-v4-flash` and
  `agy:Gemini 3.5 Flash (High)`), and note that leaving it blank falls back
  to self-review. State plainly that vicaya does not store any provider API
  keys itself — `opencode`/`agy` must already be authenticated.
  → verify: `grep -n "VICAYA_CROSS_CHECK_CHAIN" .env.example` shows the new block; `grep -i "openrouter_api_key" .env.example` returns nothing.

- [x] **Task 2.2 — `skill/vicaya/SKILL.md`**
  Make these edits (exact current text quoted so the edit is unambiguous):
  1. Replace the bullet (currently ~line 88):
     `- Cross-check uses an OpenRouter model chain (see Phase 6; current lead `deepseek/deepseek-v4-flash` — paid but ~$0.0001/call). Requires `OPENROUTER_API_KEY` in env / `.env`, or an OpenRouter key in `~/.local/share/opencode/auth.json`. When unavailable the helper returns a `# SELF_REVIEW:` sentinel and the agent runs the checklist on its own synthesis.`
     with wording describing `VICAYA_CROSS_CHECK_CHAIN` (app:model chain,
     tried in order, `# SELF_REVIEW:` fallback when empty/all fail).
  2. In the subcommand table (~line 118), replace the `cross-check` row's
     "Notes" cell — currently `OpenRouter model chain (see `data/openrouter_models.json`) → `# SELF_REVIEW:` sentinel on failure. Output is post-processed: ...` —
     to reference `VICAYA_CROSS_CHECK_CHAIN` instead of
     `data/openrouter_models.json`; keep the citation-stamping sentence
     unchanged.
  3. Delete the `gemini-cross-check` row entirely (~line 120):
     `| `gemini-cross-check` | `--timeout N`; **prompt on stdin** | Legacy direct gemini call. Not used in Phase 6; kept for ad-hoc use if you want a second opinion from a different provider. |`
  4. In the auto-logging paragraph (~line 402), remove `, and `gemini-cross-check`` from:
     `... `fetch-transcript`, `cross-check`, and `gemini-cross-check` call appends ...`
     → `... `fetch-transcript`, and `cross-check` call appends ...`
  5. In Phase 6 (~line 1642), replace the paragraph starting
     `The `cross-check` helper POSTs to OpenRouter (model list in `data/openrouter_models.json` — edit freely, read at runtime). OpenRouter routes server-side via `models: [...]`: the first reachable model wins, subsequent entries cover outages / rate-limits. On any failure (no key, all models down, network error) the helper returns the `# SELF_REVIEW:` sentinel.`
     with a description of the new mechanism: `cross-check` tries each
     `app:model` entry in `VICAYA_CROSS_CHECK_CHAIN` (env) in order via
     subprocess (`opencode run -m <model>` or `agy --print ... --model
     <model>`), returns the first one that succeeds, and falls back to
     `# SELF_REVIEW:` if the chain is empty or every entry fails. Keep the
     rest of that sentence (about reading the scratch-local review file)
     unchanged.
  6. In the troubleshooting list (~line 2077), replace:
     `- **`cross-check` returns `# SELF_REVIEW:`**: OpenRouter is unreachable. Run the embedded checklist on your own synthesis as described in Phase 6; do not retry the helper. Common root causes: no `OPENROUTER_API_KEY` set (check `.env`), an empty / malformed `data/openrouter_models.json`, or every free model in the chain simultaneously rate-limited (rare). (Note: the legacy `gemini-cross-check` subcommand returns a `# ERROR:` line on failure instead — same response: skip the section and continue.)`
     with: every configured chain entry failed (or `VICAYA_CROSS_CHECK_CHAIN`
     is unset/blank). Run the embedded checklist on your own synthesis as
     described in Phase 6; do not retry the helper. Common root causes: the
     chain var is empty, `opencode`/`agy` aren't on `$PATH`, or neither app
     has valid provider credentials configured.
  Leave the unrelated "Gemini CLI" self-identification example (~line 1911,
  inside Phase 7 agent-identity guidance) untouched — it's about an agent
  naming itself, not about the cross-check mechanism.
  → verify: `grep -n "openrouter_models.json\|gemini-cross-check\|OPENROUTER_API_KEY" skill/vicaya/SKILL.md` returns no matches.

- [x] **Task 2.3 — `README.md`**
  1. Line ~33: change
     `| **Gemini cross-check** | Second model reviews the draft before the note is written |`
     to describe the configurable chain, e.g.
     `| **Cross-check** | Second model (via `VICAYA_CROSS_CHECK_CHAIN`) reviews the draft before the note is written |`.
  2. Line ~39 (Setup step 2): change
     `2. Install whichever of these you want to use: `obsidian` CLI, `yt-dlp`, `sqlite3`, `gemini` CLI.`
     to replace `` `gemini` CLI `` with `` `opencode` CLI, `agy` `` (or
     whichever subset the user actually wants — keep the rest of the
     sentence intact).
  3. Line ~184 (dependency-check block): change
     `which gemini      # Gemini CLI — optional (cross-check model)`
     to two lines (aligned with the surrounding `which ...` block style):
     `which opencode    # opencode CLI — optional (cross-check chain)` and
     `which agy         # agy CLI — optional (cross-check chain)`.
  → verify: `grep -n "Gemini cross-check\|which gemini" README.md` returns no matches; `grep -n "opencode\|agy" README.md` shows the new lines.

- [x] **Task 2.4 — Rename "Gemini CLI" host-app references to `agy`**
  - In `skill/vicaya/SKILL.md` Rule F5 (~line 1930): in the host-app
    parenthetical list `(e.g. Claude Code, Antigravity, Codex CLI, Gemini
    CLI)`, replace `Gemini CLI` with `agy`.
  - Same file, example list (~line 1949):
    `- Gemini CLI: `"Gemini 2.5 Pro (Gemini CLI)"` or whatever the CLI reports as its own host name.`
    → `- agy: `"Gemini 2.5 Pro (agy)"` or whatever the CLI reports as its own host name.`
    Leave the adjacent Antigravity example (~line 1948,
    `Gemini running in Antigravity: "Gemini 3.5 Flash (Antigravity)"`)
    unchanged — that's the GUI app, a separate host from the `agy` CLI.
  - In `skill/vicaya/README.md` dependency table (line 67): replace
    `| `gemini` CLI | optional (cross-check) | `gemini --version` |`
    with two rows (matching the main README's Task 2.3 style):
    `| `opencode` CLI | optional (cross-check chain) | `opencode --version` |`
    and `| `agy` CLI | optional (cross-check chain) | `agy --version` |`.
  - Do **not** touch `README.md` lines ~202–203 (`npm install -g
    @google/gemini-cli`) or ~307/330 (`~/.agents/skills` shared by
    "Gemini CLI, OpenCode, and Codex") — these refer to the real Google
    `gemini` CLI product and an actual shared skill-directory convention
    unrelated to vicaya's cross-check mechanism; renaming would misstate
    which app reads which directory.
  → verify: `grep -n "Gemini CLI" skill/vicaya/SKILL.md skill/vicaya/README.md` returns no matches; `grep -n "npm install -g @google/gemini-cli\|Gemini CLI, OpenCode" README.md` still shows those two untouched lines.

- [x] **Task 2.5 — Phase 2 verification**
  → verify: `grep -rn "openrouter_models.json\|gemini-cross-check\|OPENROUTER_API_KEY" .env.example skill/vicaya/SKILL.md README.md` returns nothing; `grep -n "Gemini CLI" skill/vicaya/SKILL.md skill/vicaya/README.md` returns nothing.

---

## Phase 3 — Live verification (real credentials, no mocking)

Each task below is run from the repo root with a temporary, single-entry
`VICAYA_CROSS_CHECK_CHAIN` (don't permanently edit the user's `.env` — export
it inline for the test command, e.g.
`VICAYA_CROSS_CHECK_CHAIN="agy:Gemini 3.5 Flash (High)" uv run tools/research_sources.py cross-check <<< "Say OK."`).

- [x] **Task 3.1 — Live check: `agy` alone**
  Run with `VICAYA_CROSS_CHECK_CHAIN=agy:Gemini 3.5 Flash (High)` (or
  another model from `agy models`), prompt `"Reply with exactly: OK"`.
  → verify: stdout is real model text (not `# SELF_REVIEW:`, not an error/timeout); confirms the `agy` dispatch path works end-to-end.

- [x] **Task 3.2 — Live check: `opencode` + OpenRouter alone**
  Run with `VICAYA_CROSS_CHECK_CHAIN=opencode:openrouter/deepseek/deepseek-v4-flash`,
  same prompt. Requires `OPENROUTER_API_KEY` already present in `.env`
  (confirmed present).
  → verify: stdout is real model text. If it fails, capture the actual `opencode run` stderr (run it directly, not through the helper, to see the raw error) and determine the correct provider-id format opencode expects for OpenRouter — update Task 1.1/2.1's example model string if the assumed `openrouter/<vendor>/<model>` format is wrong, then re-run this check.

- [~] **Task 3.3 — Live check: `opencode` + Gemini direct alone** — SKIPPED: opencode has no Google credentials and user does not need this combination (agy covers Gemini, opencode covers OpenRouter/DeepSeek). Verified both dispatch paths independently via Tasks 3.1 and 3.2.
  `opencode auth list` currently shows only `openai`/`deepseek` — no Google
  credential exists yet. Before running the check: either run
  `opencode auth login` interactively and select the Google/Gemini provider
  (this step needs the user — flag it and wait rather than guessing at
  hidden env-var names), or confirm a `GEMINI_API_KEY` /
  `GOOGLE_GENERATIVE_AI_API_KEY` env var is enough by checking `opencode auth list`
  again after setting one. Once credentials exist, run with
  `VICAYA_CROSS_CHECK_CHAIN=opencode:google/<model>` (confirm the exact
  provider/model id via `opencode models` after auth succeeds — it will
  list Gemini models once authenticated).
  → verify: stdout is real model text. If blocked on missing credentials after asking the user, document the gap in `plan.md` under this task (per workflow.md "Document Deviations") rather than marking it done, and continue to Task 3.4 — this is not a blocker for the rest of the thread.

- [x] **Task 3.4 — Phase 3 / thread verification** — full suite: 245 passed, 10 skipped, 1 pre-existing failure (search_vault needs Obsidian running). All cross_check tests pass. Tasks 3.1 (agy) and 3.2 (opencode+OpenRouter) confirmed live. Task 3.3 skipped per user decision.
  → verify: `uv run pytest tests/` (full suite) passes; all of Tasks 3.1–3.3 are either confirmed working live or have a documented, specific reason they couldn't be (not a vague "didn't work").
