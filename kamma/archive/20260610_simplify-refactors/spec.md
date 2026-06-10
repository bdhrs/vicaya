# Spec — Simplification refactors from the 2026-06-10 full-repo analysis

Source: `kamma/threads/suggestions/handoff.md` (read-only analysis, 2026-06-10).
Thread type: chore/refactor. No GitHub issue.

## Overview
Implement the safe simplification items from the handoff: mock the one live
network test, consolidate duplicated utilities into `tools/_common.py`,
extract the scratch-dossier subsystem into `tools/scratch.py`, convert the
hand-written CLI dispatch to a registry, harden (not flip) the scratch
run-keying, and move the short root agent-note instructions into the Kamma
docs instead of keeping separate root note files. Same capability, no behavior
change.

## What it should do

1. **Mock the live Gemini test.**
   `TestGeminiCrossCheck::test_trivial_prompt_returns_text`
   (`tests/test_research_sources.py:192`) currently shells out to the real
   `gemini` CLI (27–99 s, network-dependent). Monkeypatch
   `tools.research_sources.subprocess.run` to return a fixed string —
   the same pattern `tests/test_cross_check.py` already uses. After this,
   no test in the suite performs live network/CLI calls.

2. **Extract `tools/_common.py`.**
   Consolidate: repo root constant, dotenv loader, `_env_path`, `_strip_xml`.
   Rewire the three copies in `tools/research_sources.py` (l.34–70),
   `tools/library_folders.py` (l.93–174), `tools/note_checks.py` (l.45).
   Corrections to the handoff:
   - The read-only sqlite-connect idiom exists only in `library_folders.py`
     (3 call sites) — it is not duplicated and stays where it is.
   - `scripts/sync_notes.py` / `scripts/sync_run_report.py` have their own
     small loaders but are deliberately standalone (scripts do not import
     `tools`; cf. the importlib dance in `generate_note_pdf.py`). Left alone.
   - `note_checks.load_dotenv(path) -> dict` is public API with a different
     signature (returns a dict, doesn't mutate `os.environ`); keep it as a
     thin wrapper over the shared parser — signature preserved for external
     callers (`generate_note_pdf.py` loads `note_checks` by file path).

3. **Extract `tools/scratch.py`.**
   Move the scratch-dossier subsystem (`research_sources.py` ~l.1505–1996:
   `_run_key`, `_state_file`, `_file_lock`, state read/write, `_SCRATCH_PHASES`,
   `scratch_init/log/gate/verify/resume/which`, auto-log hook) wholesale into
   `tools/scratch.py`. `research_sources.py` re-imports the public names so:
   - all 13 `research_sources.py scratch-*` CLI references in
     `skill/vicaya/SKILL.md` keep working unchanged, and
   - `tests/test_research_sources.py` imports keep working unchanged.
   This mirrors the existing delegation pattern (library-folders commands
   already delegate to `tools/library_folders.py` — see `kamma/tech.md`).

4. **Registry-based CLI dispatch.**
   Replace the 24 `elif args.cmd == ...` branches in `_cli()` with
   `subparser.set_defaults(func=handler)` + `args.func(args)`. Output and
   exit codes byte-identical.

5. **Scratch run-key hardening (item D, scoped down — owner confirmed
   2026-06-10).**
   The handoff proposed flipping `VICAYA_SCRATCH` to primary. Investigation
   shows path resolution *already* prefers the env pin
   (`_scratch_path`, l.1693–1703), and `skill/vicaya/SKILL.md` (l.376–384)
   documents process-keying as the deliberate design because `export` does
   not survive between Bash calls in agent harnesses. The full flip is
   rejected. Scoped version, behavior-preserving:
   - cache `_run_key()` per process (it currently spawns `ps` on every call;
     `_state_file()` is hit multiple times per CLI invocation);
   - when `VICAYA_SCRATCH` (and, where relevant, `VICAYA_PHASE`) already
     answer the lookup, skip the state-file read entirely — no `ps` spawn
     on the env-pinned path;
   - docstrings updated to describe the env pin as the deterministic override.
   No SKILL.md changes.

6. **Fold root agent notes into Kamma docs.**
   Owner correction (2026-06-10): the root agent note is not a separate
   project agent layer; it is Kamma process/validation policy. Move validation
   command scope into `kamma/tech.md`, move Kamma cleanup guidance into
   `kamma/workflow.md`, remove the obsolete root note and tool-specific
   symlink aliases, and remove their `.gitignore` entries. `runs/` stays
   exactly as-is (owner decision 2026-06-10).

## Assumptions & uncertainties
- Re-export from `research_sources` (rather than updating all import sites)
  is the right compatibility move — it keeps SKILL.md, the staged sibling
  skills, and the tests untouched. If the owner later prefers tests to import
  from `tools.scratch` directly, that's a one-line-per-test follow-up.
- `_env_path` signatures differ slightly (`research_sources` takes a default,
  `library_folders` doesn't); `_common.env_path(key, default=None)` covers both.
- Assumed no other repo consumers import the moved private helpers
  (`_run_key` etc.) — only `tests/test_research_sources.py` touches
  `_write_state`, which the re-export keeps available.

## Constraints
- No behavior change anywhere; this is a pure internal refactor.
- No edits to `skill/vicaya/SKILL.md` or the staged sibling skills.
- Library-folders index/search constraints in `kamma/tech.md` continue to hold.
- Validation is scoped per project rules: per-file pytest + ruff/pyright/
  pyrefly on touched files only. No bare `uv run pytest`.
- Agent does not commit; draft commit message(s) only.

## How we'll know it's done
- Full per-file test bundle green: `test_cross_check.py`,
  `test_research_sources.py`, `test_library_folders.py`, `test_note_checks.py`,
  `test_validate_note.py`, `test_generate_note_pdf.py` (≥135 passed, 0 failed;
  skips unchanged).
- `test_research_sources.py` completes in seconds (no live `gemini` call).
- Exactly one dotenv implementation remains under `tools/` (plus the
  signature-preserving `note_checks` wrapper).
- `tools/research_sources.py` shrinks by roughly the scratch block (~470
  lines) plus dispatch boilerplate; `tools/scratch.py` exists with the moved
  code.
- `uv run tools/research_sources.py scratch-which` (and a
  `scratch-init`/`scratch-gate` smoke sequence) behaves identically.
- The root agent note and tool-specific symlink aliases no longer exist in the
  working tree, and `.gitignore` no longer references them.
- Scoped ruff/pyright/pyrefly pass on every touched `.py` file.

## What's not included
- `runs/` gitignore/untracking (owner chose leave-as-is, 2026-06-10).
- SKILL.md phase pruning (item F) and low-usage source extraction (item G) —
  separately scoped threads needing owner input.
- The full `VICAYA_SCRATCH`-primary flip (rejected; see item 5).
- Touching `scripts/sync_notes.py` / `sync_run_report.py` dotenv copies.
- Further `research_sources.py` splits (`sources/`, `crosscheck.py`, …).
