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

# Symlink every skill under skill/ into every coding agent installed on this machine (Claude Code, opencode, agy, Pi, Codex, …) plus their command stubs. Content auto-updates via the symlink; re-run to pick up newly added skills.
sync:
    #!/usr/bin/env bash
    set -euo pipefail
    src="$(pwd)/skill"
    pi_stubs="$(pwd)/config/pi/prompts"
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
    pi_prompts="$HOME/.pi/agent/prompts"
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

        # Prompt/command-template forms (bare /name <args>) only substitute
        # $ARGUMENTS-style placeholders, which SKILL.md files don't contain — a
        # stub is required to forward the typed argument instead of silently
        # dropping it. Claude Code needs no stub: it passes arguments to the
        # skill itself.
        if [ -d "$pi_prompts" ] || [ -d "$(dirname "$pi_prompts")" ]; then
            mkdir -p "$pi_prompts"
            if [ -f "$pi_stubs/$name.md" ]; then
                ln -sfn "$pi_stubs/$name.md" "$pi_prompts/$name.md"
            else
                ln -sfn "${dir}SKILL.md" "$pi_prompts/$name.md"
                echo "  warn: no Pi stub for $name (arguments will be dropped)"
            fi
        fi
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
