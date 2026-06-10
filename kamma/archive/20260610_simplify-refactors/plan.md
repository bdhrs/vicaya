# Plan — Simplification refactors (thread: 20260610_simplify-refactors)

Spec: see `spec.md` in this thread. Source analysis:
`kamma/threads/suggestions/handoff.md`. No GitHub issue.

## Architecture Decisions
- **`tools/_common.py` as the shared-utility home** — smallest module that
  removes the three duplicate dotenv/env/strip-xml implementations under
  `tools/`. The read-only sqlite idiom is NOT moved (it exists only in
  `library_folders.py`). The `scripts/` dotenv copies are NOT touched
  (scripts deliberately don't import `tools`).
- **`tools/scratch.py` via re-export, not import rewiring** — `research_sources.py`
  re-imports the moved public names so all 13 `scratch-*` CLI references in
  `skill/vicaya/SKILL.md` and all test imports keep working unchanged.
  Mirrors the existing library-folders delegation pattern (`kamma/tech.md`).
- **Item D scoped to hardening, not a flip** — process-keying stays the
  primary auto-log mechanism (SKILL.md l.376–384 documents why: `export`
  doesn't survive between Bash calls). We only cache the `ps` call and skip
  state-file access when `VICAYA_SCRATCH` already answers the lookup.
  No SKILL.md edits anywhere in this thread.
- **`note_checks.load_dotenv(path) -> dict` keeps its signature** as a thin
  wrapper over the shared parser — `generate_note_pdf.py` loads `note_checks`
  by file path, so changing the API fails at runtime, not import time.
- **Validation is scoped per project rules**: per-file pytest +
  ruff/pyright/pyrefly on touched files only. Never bare `uv run pytest`.
- **No separate root agent-note layer** — owner correction 2026-06-10: move
  the short validation/finalization rules into Kamma docs, remove the obsolete
  root note plus tool-specific symlink aliases, and remove their `.gitignore`
  entries.

## Phase 1 — Kill the live network test
- [x] Mock the `gemini` CLI in `TestGeminiCrossCheck::test_trivial_prompt_returns_text`
      (`tests/test_research_sources.py:191`). Monkeypatch
      `tools.research_sources.subprocess.run` to return a fixed stdout string,
      following the existing pattern in `tests/test_cross_check.py`.
  → verify: `uv run pytest tests/test_research_sources.py -q` — all pass,
    wall time drops from ~30–100 s to seconds.
- [x] Phase verification: `uv run ruff check tests/test_research_sources.py`
      + `uv run pyright tests/test_research_sources.py`
      + `uv run pyrefly check --search-path . tests/test_research_sources.py`.
  → verify: all clean.

## Phase 2 — Extract `tools/_common.py`
- [x] Create `tools/_common.py` (one-sentence purpose docstring first) with:
      `REPO_ROOT`, a dotenv parser, `load_dotenv(path)` (sets `os.environ`,
      no-overwrite semantics identical to current `_load_dotenv`),
      `env_path(key, default=None)`, `strip_xml(s)`. Behavior must match the
      current implementations exactly (compare the three before writing).
  → verify: `uv run ruff check tools/_common.py` + pyright + pyrefly clean.
- [x] Rewire `tools/research_sources.py` (delete `_strip_xml` l.34,
      `_load_dotenv` l.52, `_env_path` l.70, `_REPO_ROOT`; import from
      `tools._common`; keep module-level dotenv-load call site semantics).
  → verify: `uv run pytest tests/test_research_sources.py tests/test_cross_check.py -q` — all pass.
- [x] Rewire `tools/library_folders.py` (same: l.93–174 duplicates).
  → verify: `uv run pytest tests/test_library_folders.py -q` — 47 passed, 3 skipped.
- [x] Rewire `tools/note_checks.py` — keep public `load_dotenv(path) -> dict`
      signature as a wrapper over the shared parser.
  → verify: `uv run pytest tests/test_note_checks.py tests/test_validate_note.py tests/test_generate_note_pdf.py -q` — all pass.
- [x] Phase verification: scoped ruff/pyright/pyrefly bundle on all four
      touched `tools/*.py` files; confirm exactly one dotenv implementation
      remains under `tools/`
      (`grep -rn "def.*load_dotenv\|def _load_dotenv" tools/`).
  → verify: all clean; grep shows only `_common.py` (+ the `note_checks` wrapper).

## Phase 3 — Extract `tools/scratch.py`
- [x] Move the scratch-dossier block (`tools/research_sources.py`
      ~l.1505–1996: header comment, `_SCRATCH_DIR`, `_AUTO_SKIP_PHASES`,
      `_run_key`, `_state_file`, `_file_lock`, `_read_state`, `_write_state`,
      `_SCRATCH_PHASES`, `_PHASE_INDEX`, `_next_worked_phase`, `_scratch_path`,
      `_run_class`, `scratch_init/log/gate/verify/resume/which`, and the
      auto-log helper) wholesale into `tools/scratch.py` (purpose docstring
      first). Pure move — no logic edits in this phase.
      NOTE: test monkeypatch targets updated from tools.research_sources._SCRATCH_DIR /
      _run_key to tools.scratch._SCRATCH_DIR / _run_key (functions now live in scratch.py).
  → verify: `uv run ruff check tools/scratch.py` + pyright + pyrefly clean.
- [x] In `tools/research_sources.py`, re-import the public scratch names
      (including `_write_state`, used by tests) so existing imports and the
      `scratch-*` CLI subcommands work unchanged.
  → verify: `uv run pytest tests/test_research_sources.py -q` — 67 passed (pre-existing
    Obsidian failure unchanged), test imports untouched.
- [x] CLI smoke: `uv run tools/research_sources.py scratch-init plan-smoke`,
      `scratch-gate 0` (expect refusal or pass per evidence), `scratch-which`,
      then delete `data/scratch/plan-smoke.md` and its state/lock files.
  → verify: commands behave as before the move (same outputs/exit codes).
- [x] Phase verification: scoped bundle on `tools/scratch.py` +
      `tools/research_sources.py`.
  → verify: all clean.

## Phase 4 — Scratch run-key hardening (item D, scoped)
- [x] In `tools/scratch.py`: cache `_run_key()` per process
      (`functools.cache`); short-circuit state-file reads when
      `VICAYA_SCRATCH` (and `VICAYA_PHASE`, for phase lookups) already
      answer the question — no `ps` spawn on the env-pinned path. Update
      docstrings to name the env pin as the deterministic override.
  → verify: `uv run pytest tests/test_research_sources.py -q` — 67 passed, all clean.
- [x] Phase verification: scoped bundle on `tools/scratch.py`.
  → verify: all clean.

## Phase 5 — Registry CLI dispatch
- [x] Convert `_cli()` in `tools/research_sources.py`: attach
      `set_defaults(func=...)` per subparser, replace the 24-branch
      `elif args.cmd == ...` chain with one `args.func(args)` call.
      Output formatting and exit codes byte-identical.
  → verify: `uv run pytest tests/test_research_sources.py tests/test_cross_check.py -q`
    — 81 passed, 1 failed, 11 skipped; failure is the pre-existing
    Obsidian-unavailable `TestSearchVault.test_search_returns_list` from
    handoff.md. Control rerun with `-k 'not test_search_returns_list'`:
    81 passed, 11 skipped, 1 deselected. `uv run tools/research_sources.py --help`
    lists all 24 subcommands. `scratch-which` no-state path exits 1 with the
    expected no-scratch message; env-pinned success path exits 0 and prints the
    pinned path. One env-pinned retry needed `UV_CACHE_DIR=/private/tmp/vicaya-uv-cache`
    because uv tried to initialize `/Users/deva/.cache/uv` and the sandbox refused it.
- [x] Phase verification: scoped bundle on `tools/research_sources.py`.
  → verify: `uv run ruff check tools/research_sources.py`,
    `uv run pyright tools/research_sources.py`, and
    `uv run pyrefly check --search-path . tools/research_sources.py` all clean.

## Phase 6 — Fold root agent notes into Kamma docs + thread wrap-up
- [x] Read the root agent note (~1 KB) and confirm the contents belong in
      `kamma/tech.md` / `kamma/workflow.md`, not a separate tracked agent file.
  → verify: content reviewed; validation-scope policy belongs in
    `kamma/tech.md`, and Kamma cleanup guidance belongs in `kamma/workflow.md`.
- [x] Move the root agent-note instructions into Kamma docs:
      validation-scope policy to `kamma/tech.md`; Kamma finalization cleanup
      guidance to `kamma/workflow.md`.
  → verify: both instruction sets are present in Kamma docs.
- [x] Remove the obsolete root agent note, its tool-specific symlink aliases,
      and their `.gitignore` entries.
  → verify: root files/symlinks are absent; `.gitignore` has no entries for
    those names; active thread docs plus `kamma/tech.md`, `kamma/workflow.md`,
    and `.gitignore` have no stale root-agent filename references;
    `git diff --check` clean.
- [x] Final verification: run the full per-file pytest bundle
      (`test_cross_check`, `test_research_sources`, `test_library_folders`,
      `test_note_checks`, `test_validate_note`, `test_generate_note_pdf`)
      plus the scoped ruff/pyright/pyrefly bundle over every touched file.
  → verify: full pytest bundle: 150 passed, 1 failed, 14 skipped; the failure
    is the pre-existing Obsidian-unavailable
    `TestSearchVault.test_search_returns_list` from handoff.md. Control run
    with only that test deselected: 150 passed, 14 skipped, 1 deselected.
    Scoped ruff, pyright, and pyrefly over all touched `.py` files are clean.
    No live Gemini/network test remains.
- [x] Draft the commit message(s) for the user (agent does not commit) —
      suggested split: `test(research): mock live gemini cross-check call`,
      `refactor(tools): extract _common.py and scratch.py; registry CLI dispatch`,
      `docs(kamma): fold agent instructions into Kamma docs`.
  → verify: draft present here; nothing committed by the agent.
    - `test(research): mock live gemini cross-check call`
    - `refactor(tools): extract common helpers and scratch dossier module`
    - `refactor(tools): convert research_sources CLI to registry dispatch`
    - `docs(kamma): fold agent instructions into Kamma docs`
