# Handoff — Simplification refactors (20260610_simplify-refactors)

Date: 2026-06-10. Phases 1–6 implementation complete. Awaiting user testing
before `/kamma:3-review`.

---

## Completed this session

### Phase 1 — Mock live Gemini test ✅
- `tests/test_research_sources.py`: removed `@gemini_available` from `TestGeminiCrossCheck`, added `monkeypatch` to mock `tools.research_sources.subprocess.run`, returns `_Result(returncode=0, stdout="pong")`.
- Suite: 67 passed, 0.74 s (no live call).

### Phase 2 — Extract `tools/_common.py` ✅
- Created `tools/_common.py` with `REPO_ROOT`, `_parse_dotenv`, `load_dotenv`, `env_path`, `strip_xml`.
- All three files rewired: `research_sources.py`, `library_folders.py`, `note_checks.py`.
- Critical detail: all three files need a sys.path insertion before the `from tools._common import` line (marked `# noqa: E402`) because `research_sources.py` is run as a script, setting `sys.path[0]` to `tools/`, so `tools._common` wouldn't resolve otherwise.
- `note_checks.load_dotenv(path) -> dict` is preserved as a thin wrapper over `_common._parse_dotenv`.
- `library_folders._env_path` had no `default` param; `_common.env_path(key, default=None)` covers both call sites.
- Linters: all clean on all touched files.

### Phase 3 — Extract `tools/scratch.py` ✅
- Moved the entire scratch-dossier block (~473 lines) from `research_sources.py` to `tools/scratch.py`.
- `research_sources.py` re-imports everything via `from tools.scratch import ... # noqa: E402, F401`.
- Also removed now-unused `import fcntl` and `from contextlib import contextmanager` from `research_sources.py`.
- **Critical test fix**: tests used `monkeypatch.setattr("tools.research_sources._SCRATCH_DIR", ...)` and `monkeypatch.setattr("tools.research_sources._run_key", ...)`. After the move, those names refer to re-exported bindings, not the live module globals that the functions use. Updated all test monkeypatches to target `tools.scratch._SCRATCH_DIR` and `tools.scratch._run_key` instead.
- CLI smoke (`scratch-init plan-smoke`, `scratch-gate 0`, `scratch-which`) passed, artifacts cleaned up.

### Phase 4 — Scratch run-key hardening ✅
- Added `@functools.cache` to `_run_key()` in `scratch.py` — `ps` spawns once per process.
- Refactored `_maybe_autolog` to check `VICAYA_SCRATCH` + `VICAYA_PHASE` env vars before calling `_read_state()` — no state-file read on the env-pinned path.
- Updated `_run_key` docstring to describe env pin as the deterministic override.
- Tests: 67 passed, all clean.

### Phase 5 — Registry CLI dispatch ✅
- Converted `_cli()` in `tools/research_sources.py` from the hand-written
  branch chain to `set_defaults(func=...)` handlers plus one `args.func(args)`
  dispatch call.
- `uv run tools/research_sources.py --help` lists all 24 subcommands.
- `scratch-which` no-state and env-pinned paths were checked.

### Phase 6 — Root agent notes folded into Kamma docs ✅
- Moved validation-scope policy into `kamma/tech.md`.
- Moved Kamma finalization cleanup guidance into `kamma/workflow.md`.
- Removed the obsolete root note and its tool-specific symlink aliases.
- Removed the stale `.gitignore` entries for those root files.

---

## State of files touched

| File | Change |
|---|---|
| `tools/_common.py` | Created — shared REPO_ROOT, dotenv, env_path, strip_xml |
| `tools/scratch.py` | Created — entire scratch-dossier subsystem |
| `tools/research_sources.py` | Rewired: imports from `_common` + `scratch`; removed inline duplicates; removed `fcntl`/`contextmanager` imports |
| `tools/library_folders.py` | Rewired: imports from `_common`; removed inline duplicates |
| `tools/note_checks.py` | Rewired: `load_dotenv` is thin wrapper over `_common._parse_dotenv` |
| `tests/test_research_sources.py` | Phase 1 mock; monkeypatch targets updated to `tools.scratch.*` |
| `kamma/tech.md` | Now owns validation-scope policy |
| `kamma/workflow.md` | Now owns Kamma finalization cleanup guidance |
| `.gitignore` | Root agent-note entries removed |

---

## Remaining work

- User manual test/confirmation.
- Then run `/kamma:3-review` in a fresh session.

---

## Constraints for next session

- No SKILL.md edits anywhere.
- Validation is per-file only (never bare `uv run pytest`).
- Agent does not commit; draft commit messages only at Phase 6.
- Phase 3 note: monkeypatch targets for scratch are `tools.scratch.*`, NOT `tools.research_sources.*`.
- The sys.path insertion pattern (before `from tools._common import` / `from tools.scratch import`) is intentional and marked with `# noqa: E402`.

---

## Test baseline

Pre-existing failure (unrelated to this thread): `tests/test_research_sources.py::TestSearchVault::test_search_returns_list` — requires Obsidian app running, not fixable here.

Current counts:
- `test_research_sources.py`: 67 passed, 1 failed (pre-existing), 11 skipped
- `test_cross_check.py`: 14 passed
- `test_library_folders.py`: 47 passed, 3 skipped
- `test_note_checks.py` + `test_validate_note.py` + `test_generate_note_pdf.py`: 22 passed
