# Spec - Folder Corpus Exclusion List

## Overview

Add an optional folder-exclusion list to the unmanaged folder-corpus source
(`tools/folder_corpus.py`). The motivating case: the configured corpus root
`~/MyFiles/2_Resources/Libraries` overlaps with the Calibre library at
`~/MyFiles/2_Resources/Libraries/Bodhirasa eBook Library`. That subtree is
already searchable via `search-calibre`, so the user wants to exclude it from
the folder-corpus index to avoid duplicate indexing and a multi-hour redundant
extraction pass over Calibre's PDFs.

## What It Should Do

- Read an optional `.env` value `VICAYA_FOLDER_CORPUS_EXCLUDE`: a comma-separated
  list of folder paths to skip during refresh. `~` is expanded; entries are
  trimmed; empty entries ignored. Comma is the separator (folder paths may
  contain spaces, e.g. `Bodhirasa eBook Library`, but rarely commas).
- During `folder-corpus-refresh`, prune any directory that equals or sits under
  an excluded path. Pruning happens at the `os.walk` level so excluded subtrees
  are never descended into (no wasted hashing/extraction).
- Surface the resolved exclude list in `folder-corpus-check` output so the user
  can confirm what is excluded without walking the tree.
- On an unbounded refresh, files previously indexed under a now-excluded folder
  are removed from the index by the existing delete-missing pass (they are no
  longer "seen"). This is the desired behaviour; no separate cleanup is needed.

## What It Should Not Do

- No change to `search`, `duplicates`, or the CLI subcommand surface. Exclusion
  is a refresh-time concern; search reads the index and is automatically
  consistent.
- No new dependency. Pure stdlib (`pathlib`, `os.walk`).
- No exclusion-by-glob or by-extension in this thread — folder-path prefixes
  only. Extension noise filtering already exists (`NOISE_EXTENSIONS`).

## Configuration

```env
# Optional: comma-separated folders to skip during folder-corpus refresh.
VICAYA_FOLDER_CORPUS_EXCLUDE=~/MyFiles/2_Resources/Libraries/Bodhirasa eBook Library
```

Absent or empty → no exclusion (current behaviour, fully backward compatible).

## How We'll Know It's Done

- `default_config()` parses `VICAYA_FOLDER_CORPUS_EXCLUDE` into
  `FolderCorpusConfig.exclude` as a tuple of expanded `Path`s.
- A refresh over a fixture tree with an excluded subfolder indexes only the
  non-excluded files.
- A refresh that newly excludes a previously-indexed subfolder removes those
  rows on an unbounded run.
- `folder-corpus-check` reports the exclude list.
- `.env.example`, `README.md`, and `kamma/tech.md` document the new variable.
- Scoped validation passes: ruff, pyright, pyrefly, pytest on the changed files.

## Constraints

- Backward compatible: unset/empty exclude behaves exactly as today.
- Exclude paths are matched in the same path form as the configured root
  (absolute, post-`expanduser`); no symlink resolution.
- Follow project Python validation (ruff/pyright/pyrefly/pytest, scoped).
