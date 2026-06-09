# Vicaya task recipes. Run `just` to list them.
#
# These wrap the folder-corpus subcommands of tools/research_sources.py.
# Multiple source trees (including Calibre libraries) are indexed together into
# one SQLite FTS5 database. Paths come from .env (VICAYA_FOLDER_CORPUS_SOURCES /
# _INDEX / _EXCLUDE). Only fc-refresh touches the source trees; the rest are read-only.

# List all recipes.
default:
    @just --list

# Read-only preflight: report config and index health (run before refreshing).
fc-check:
    uv run tools/research_sources.py folder-corpus-check

# Build/update the index by walking and extracting the source tree (skips unchanged files; slow first run; add --limit N to bound it).
fc-refresh *args:
    uv run tools/research_sources.py folder-corpus-refresh {{args}}

# Like fc-refresh, but also re-extracts previously-failed files (run after adding extractor support, e.g. new ebook formats).
fc-refresh-retry *args:
    uv run tools/research_sources.py folder-corpus-refresh --retry-failed {{args}}

# Full-text search the index, e.g. `just fc-search "dhamma" --limit 5`.
fc-search query *args:
    uv run tools/research_sources.py search-folder-corpus "{{query}}" {{args}}

# Read-only duplicate diagnostic, e.g. `just fc-dups --samples 10`.
fc-dups *args:
    uv run tools/research_sources.py folder-corpus-duplicates {{args}}
