# Spec — obsidian-cli-fix

## Problem

Every `/vicaya` run reports:

> Note: Obsidian CLI couldn't connect even after launching the app — the note was written directly to disk.

Two compounding bugs cause this:

**Bug 1 — SKILL.md Hard Rule 4 launches the CLI, not the app.**
On Linux, `~/.local/bin/obsidian` (the CLI) shadows `/usr/bin/obsidian` (the desktop app) in
`$PATH`. The skill's recovery line `setsid obsidian …` therefore re-runs the CLI binary, which
immediately exits with "unable to find Obsidian". The app is never started.

**Bug 2 — `search_vault` silently swallows the "app not running" error.**
The Obsidian CLI exits 0 and prints plaintext on stdout when not connected. The guard at
`research_sources.py:189` passes exit-0 through, then `json.loads()` raises `JSONDecodeError`,
which is caught and returns `[]`. The caller cannot distinguish "0 hits" from "CLI not
connected". This also affects any future `create` calls made via the same pattern.

The two bugs interact: even if Bug 2 were fixed with auto-launch-and-retry, it would use the
broken launch command from Bug 1 and still fail.

## Solution

### Part 1 — `tools/research_sources.py`: stop swallowing the error

In `search_vault` (and the `obsidian create` invocation at note-write time), detect a non-JSON
response from the CLI as a CLI error, not a "0 hits" result:

- If the CLI output is non-empty but not valid JSON → it's a CLI error message.
  - Raise `RuntimeError` with the CLI's message so the caller can react (or let it propagate).
  - Do **not** return `[]` silently.
- Keep `return []` only for a parsed empty JSON list (genuine 0 hits).

### Part 2 — `skill/vicaya/SKILL.md`: fix the launch command (Hard Rule 4)

Replace the bare `obsidian` launch with a per-OS command that bypasses `$PATH` and reaches
the actual desktop app:

- **Linux:** `xdg-open "obsidian://" >/dev/null 2>&1 &`
- **macOS:** `open -a Obsidian` *(already correct — leave unchanged)*
- **Windows:** `start "" "obsidian://"` *(add; not currently mentioned)*

The `obsidian://` URI handler is registered by every standard Obsidian install across all
three OSes, regardless of install method (apt, AppImage, flatpak, dmg, installer).

## Scope

- `tools/research_sources.py` — `search_vault` function only
- `skill/vicaya/SKILL.md` — Hard Rule 4 launch command
- Tests: add/update a test for the non-JSON / error-exit path in `search_vault`

## Out of scope

- The note-write `obsidian create` path (same pattern but low-priority; the note is already
  written to disk as a fallback — safe to leave for a follow-up)
- Staged sibling skills (`skill/vicaya-0-scope` etc.) — no route-list or stage-boundary
  changes are involved
