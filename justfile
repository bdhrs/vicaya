# Vicaya task recipes. Run `just` to list them.
#
# These wrap the library-folders subcommands of tools/research_sources.py.
# Multiple source trees (including Calibre libraries) are indexed together into
# one SQLite FTS5 database. Paths come from .env (VICAYA_LIBRARY_FOLDERS /
# _INDEX / _EXCLUDE). Only lf-refresh touches the source trees; the rest are read-only.

# List all recipes.
default:
    @just --list

# Read-only preflight: report config and index health (run before refreshing).
lf-check:
    uv run tools/research_sources.py library-folders-check

# Build/update the index by walking and extracting the source tree (skips unchanged files; slow first run; add --limit N to bound it).
lf-refresh *args:
    uv run tools/research_sources.py library-folders-refresh {{args}}

# Like lf-refresh, but also re-extracts previously-failed files (run after adding extractor support, e.g. new ebook formats).
lf-refresh-retry *args:
    uv run tools/research_sources.py library-folders-refresh --retry-failed {{args}}

# Full-text search the index, e.g. `just lf-search "dhamma" --limit 5`.
lf-search query *args:
    uv run tools/research_sources.py search-library-folders "{{query}}" {{args}}

# Read-only duplicate diagnostic, e.g. `just lf-dups --samples 10`.
lf-dups *args:
    uv run tools/research_sources.py library-folders-duplicates {{args}}

# Migrate .env from folder-corpus/Calibre variable names to library-folders (run once after pulling the rename commit).
migrate-env *args:
    uv run scripts/migrate_env.py {{args}}
