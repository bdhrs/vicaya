# Migration — "folder corpus" → "library folders" rename

Steps for any second user pulling this branch.

## 1. Update your `.env`

| Old variable | New variable |
|---|---|
| `VICAYA_FOLDER_CORPUS_ROOT` | `VICAYA_LIBRARY_FOLDERS` |
| `VICAYA_FOLDER_CORPUS_INDEX` | `VICAYA_LIBRARY_FOLDERS_INDEX` |
| `VICAYA_FOLDER_CORPUS_EXCLUDE` | `VICAYA_LIBRARY_FOLDERS_EXCLUDE` |
| `VICAYA_CALIBRE_LIBRARY` | *(removed — delete this line)* |

Copy the values from your old `.env` into the new variable names. The semantics are unchanged; only the names differ.

## 2. Replace any shell aliases or scripts

If you have shell aliases, cron jobs, or external scripts that call the old CLI commands:

| Old command | New command |
|---|---|
| `search-folder-corpus` | `search-library-folders` |
| `folder-corpus-refresh` | `library-folders-refresh` |
| `folder-corpus-check` | `library-folders-check` |
| `folder-corpus-duplicates` | `library-folders-duplicates` |
| `search-calibre` | *(removed)* |
| `calibre-check` | *(removed)* |

## 3. Replace any justfile shorthand you use directly

| Old recipe | New recipe |
|---|---|
| `just fc-check` | `just lf-check` |
| `just fc-refresh` | `just lf-refresh` |
| `just fc-refresh-retry` | `just lf-refresh-retry` |
| `just fc-dupes` | `just lf-dupes` |

## 4. Python imports (if you imported the module directly)

| Old | New |
|---|---|
| `from tools.folder_corpus import ...` | `from tools.library_folders import ...` |
| `FolderCorpusConfig` | `LibraryFoldersConfig` |

## What else changed

- The standalone Calibre search subsystem (`calibredb fts_search`, `search-calibre`,
  `calibre-check`, `CalibreHit`, `_strip_diacritics`) has been removed entirely.
  Tag and author searches still work through the unified library-folders FTS index,
  which already prepends Calibre metadata to each book's text.
- `VICAYA_CALIBRE_LIBRARY` is no longer read by the code; remove it from your `.env`.
- The index file itself (`Libraries.sqlite` or whatever your `VICAYA_LIBRARY_FOLDERS_INDEX`
  points to) is unchanged — no re-index needed after the rename.
