# Vicaya task recipes. Run `just` to list them.
#
# These wrap the library-folders subcommands of tools/research_sources.py.
# Multiple source trees (including Calibre libraries) are indexed together into
# one SQLite FTS5 database. Paths come from .env (VICAYA_LIBRARY_FOLDERS /
# _INDEX / _EXCLUDE). Only the lf-refresh* recipes touch the source trees; the rest are read-only.
#
# A full rebuild is `just lf-rebuild-from-scratch`, which runs these in order:
#   1. `just lf-refresh-text`  — every file, OCR off. Fast. Scanned PDFs land as `empty`.
#   2. `just lf-refresh-retry` — only the rows the text pass could not read, OCR on. Slow (hours).
#   3. `just lf-refresh-retry` again — an OCR failure can be intermittent, so a second pass recovers them.
# Running pass 2 first would work but would hold the whole library hostage to the scans.
#
# OCR needs the `ocrmypdf` binary (`sudo apt install ocrmypdf`). `uv sync` does
# not install it, and without it passes 2 and 3 quietly do nothing.

# List all recipes.
default:
    @just --list

# Read-only preflight: report config and index health (run before refreshing).
lf-check:
    uv run tools/research_sources.py library-folders-check

# Build/update the index by walking and extracting the source tree (skips unchanged files; slow first run; add --limit N to bound it).
lf-refresh *args:
    uv run tools/research_sources.py library-folders-refresh {{args}}

# Full rebuild in one command: the text pass, the OCR pass, then one more OCR pass for books that stalled. Takes hours — run it in its own terminal, not inside an agent session.
lf-rebuild-from-scratch *args:
    #!/usr/bin/env bash
    set -euo pipefail
    command -v ocrmypdf >/dev/null || echo "!! ocrmypdf not installed — passes 2 and 3 will not OCR anything. sudo apt install ocrmypdf"
    echo "==> pass 1/3 text-only, OCR off  $(date +%H:%M:%S)"
    VICAYA_LIBRARY_FOLDERS_OCR=0 uv run tools/research_sources.py library-folders-refresh {{args}}
    echo "==> pass 2/3 OCR what pass 1 could not read  $(date +%H:%M:%S)"
    uv run tools/research_sources.py library-folders-refresh --retry-failed {{args}}
    # Kept deliberately. The new engine showed no stall across 22 books, but
    # that is 0 of 20 attempts — a 16 % upper bound at 95 % confidence, which is
    # not a basis for dropping a recovery pass. It also re-tries genuinely
    # unextractable files, which is wasted but bounded.
    echo "==> pass 3/3 retry books that stalled  $(date +%H:%M:%S)"
    uv run tools/research_sources.py library-folders-refresh --retry-failed {{args}}
    echo "==> done  $(date +%H:%M:%S)"
    uv run tools/research_sources.py library-folders-check

# Rebuild pass 1 of 3: every file, OCR fallback off. Fast; scanned PDFs stay `empty` for pass 2 to pick up.
lf-refresh-text *args:
    VICAYA_LIBRARY_FOLDERS_OCR=0 uv run tools/research_sources.py library-folders-refresh {{args}}

# Rebuild pass 2 (and 3) of 3: re-extract only the rows the previous pass could not read, PDF OCR fallback on. Slow — hours on a large library. Also the recipe to run after adding extractor support (e.g. new ebook formats).
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

# Symlink every skill under skill/ into every coding agent installed on this machine (Claude Code, opencode, agy, Pi, Codex, …) plus their command stubs. Content auto-updates via the symlink; re-run to pick up newly added skills.
sync:
    #!/usr/bin/env bash
    set -euo pipefail
    src="$(pwd)/skill"
    oc_stubs="$(pwd)/config/opencode/commands"

    # ~/.agents/skills is the shared hub: opencode (~/.config/opencode/skills) and
    # agy (~/.gemini/antigravity-cli/skills) are symlinks to it, so one link there
    # registers the skill in both.
    skills_dirs=(
        "$HOME/.claude/skills"
        "$HOME/.agents/skills"
        "$HOME/.pi/agent/skills"
        "$HOME/.codex/skills"
        "$HOME/.kilocode/skills"
        "$HOME/.qwen/skills"
        "$HOME/.cline/skills"
    )
    oc_commands="$HOME/.config/opencode/command"

    linked=()
    for d in "${skills_dirs[@]}"; do
        # Only touch agents that are actually installed — a missing parent means
        # the agent isn't on this machine, and creating its config dir would
        # leave litter that looks like a real install.
        [ -d "$(dirname "$d")" ] || continue
        mkdir -p "$d"
        linked+=("$d")
    done

    for dir in "$src"/*/; do
        name="$(basename "$dir")"
        [ -f "$dir/SKILL.md" ] || continue
        for d in "${linked[@]}"; do
            ln -sfn "${dir%/}" "$d/$name"
        done

        # Pi needs no prompt stub: /skill:name forwards arguments natively,
        # so ~/.pi/agent/skills is the only Pi registration (no bare /name
        # form — it duplicated every skill in the command menu).
        if [ -d "$(dirname "$oc_commands")" ]; then
            mkdir -p "$oc_commands"
            if [ -f "$oc_stubs/$name.md" ]; then
                ln -sfn "$oc_stubs/$name.md" "$oc_commands/$name.md"
            else
                echo "  warn: no opencode stub for $name (/$name unavailable there)"
            fi
        fi
        echo "synced: $name"
    done
    echo "skills dirs: ${linked[*]}"
