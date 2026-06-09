# Plan - Folder Corpus Exclusion List

## Architecture Decisions

- Exclusion is configured the same way as every other folder-corpus path:
  through `.env`, parsed in `default_config()`, carried on the frozen
  `FolderCorpusConfig` dataclass.
- A new optional field `FolderCorpusConfig.exclude: tuple[Path, ...] = ()`.
  Default empty tuple keeps the dataclass backward compatible with existing
  call sites and tests that construct `FolderCorpusConfig(root=..., index=...)`.
- Parsing: comma-separated `VICAYA_FOLDER_CORPUS_EXCLUDE`, each entry
  `expanduser`'d and wrapped in `Path`; blanks dropped.
- Pruning happens inside `_iter_files` by mutating `dirnames[:]` during
  `os.walk`, so excluded subtrees are never descended into. A directory is
  excluded if `child.is_relative_to(excluded)` for any configured excluded path
  (covers both the exact folder and any nested folder).
- `refresh()` passes `config.exclude` into `_iter_files`. No change to the
  delete-missing logic: excluded files simply never enter `seen_rel_paths`, so
  an unbounded refresh prunes their stale rows for free.
- `check()` adds an `exclude_paths` field for visibility.

## Phase 1 - Implement exclusion (Fast)

- [x] Add `exclude` field to `FolderCorpusConfig` and parse it in
  `default_config()`.
  -> verify: `uv run python -c "..."` with the env var set returns a config whose
  `exclude` holds the expanded paths; unset returns `()`.

- [x] Add directory pruning to `_iter_files(root, limit, exclude=())` and pass
  `config.exclude` from `refresh()`.
  -> verify: fixture tree with an excluded subfolder indexes only non-excluded
  files.

- [x] Report `exclude_paths` in `check()`.
  -> verify: `check()` output lists the configured excludes.

- [x] Tests in `tests/test_folder_corpus.py`:
  - config parses comma-separated, `~`-expanded excludes; unset → `()`.
  - refresh skips an excluded subfolder.
  - unbounded refresh removes rows for a newly-excluded, previously-indexed
    subfolder.
  - `check()` reports excludes.
  -> verify: `uv run pytest tests/test_folder_corpus.py -q` passes.

- [x] Update docs: `.env.example`, `README.md` folder-corpus section,
  `kamma/tech.md` folder-corpus line + resources.
  -> verify: `rg -n "FOLDER_CORPUS_EXCLUDE" .env.example README.md kamma/tech.md`.

- [x] Scoped validation bundle.
  -> verify: ruff, pyright, pyrefly, pytest on the changed `.py` files all pass.

## Phase 2 - Configure the user's environment (Fast)

- [x] Add `VICAYA_FOLDER_CORPUS_EXCLUDE` to the live `.env` excluding
  `~/MyFiles/2_Resources/Libraries/Bodhirasa eBook Library` (user-approved env
  edit).
  -> verify: `folder-corpus-check` reports the exclude and `root_available: true`.

## Suggested Commit Message

`feat(folder-corpus): add VICAYA_FOLDER_CORPUS_EXCLUDE folder exclusion list`
