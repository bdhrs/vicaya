"""Migrate .env from the folder-corpus/Calibre layout to library-folders.

Run once after pulling the rename commit:

    uv run scripts/migrate_env.py
    uv run scripts/migrate_env.py --dry-run   # preview without writing

What it does
------------
1. Renames VICAYA_FOLDER_CORPUS_SOURCES → VICAYA_LIBRARY_FOLDERS
2. Renames VICAYA_FOLDER_CORPUS_INDEX   → VICAYA_LIBRARY_FOLDERS_INDEX
3. Renames VICAYA_FOLDER_CORPUS_EXCLUDE → VICAYA_LIBRARY_FOLDERS_EXCLUDE
4. Removes VICAYA_CALIBRE_LIBRARY (Calibre is now just a library folder — no
   separate env var needed; its metadata.db is auto-detected by the indexer).
5. Leaves every other line untouched.

A timestamped backup (.env.bak.YYYYMMDDHHMMSS) is written before any change.
"""

from __future__ import annotations

import argparse
import re
import shutil
import sys
from datetime import datetime
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent
_ENV_PATH = _REPO_ROOT / ".env"

_RENAMES: list[tuple[str, str]] = [
    ("VICAYA_FOLDER_CORPUS_SOURCES", "VICAYA_LIBRARY_FOLDERS"),
    ("VICAYA_FOLDER_CORPUS_INDEX",   "VICAYA_LIBRARY_FOLDERS_INDEX"),
    ("VICAYA_FOLDER_CORPUS_EXCLUDE", "VICAYA_LIBRARY_FOLDERS_EXCLUDE"),
]
_REMOVE = {"VICAYA_CALIBRE_LIBRARY"}

_KEY_RE = re.compile(r"^([A-Za-z_][A-Za-z0-9_]*)\s*=")


def _migrate_lines(lines: list[str]) -> tuple[list[str], list[str]]:
    """Return (new_lines, log_messages)."""
    rename_map = {old: new for old, new in _RENAMES}
    out: list[str] = []
    log: list[str] = []
    for line in lines:
        m = _KEY_RE.match(line)
        if not m:
            out.append(line)
            continue
        key = m.group(1)
        if key in _REMOVE:
            log.append(f"  removed  {key}")
            continue
        if key in rename_map:
            new_key = rename_map[key]
            new_line = new_key + line[len(key):]
            out.append(new_line)
            log.append(f"  renamed  {key} → {new_key}")
        else:
            out.append(line)
    return out, log


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true", help="Print changes without writing")
    parser.add_argument("--env", default=str(_ENV_PATH), help="Path to .env file")
    args = parser.parse_args()

    env_path = Path(args.env)
    if not env_path.exists():
        print(f"No .env found at {env_path} — nothing to migrate.")
        sys.exit(0)

    original = env_path.read_text(encoding="utf-8")
    lines = original.splitlines(keepends=True)
    new_lines, log = _migrate_lines(lines)

    if not log:
        print("Nothing to migrate — .env already uses the new variable names.")
        sys.exit(0)

    print("Changes:")
    for msg in log:
        print(msg)

    if args.dry_run:
        print("\n(dry-run — .env not modified)")
        sys.exit(0)

    backup = env_path.with_suffix(f".bak.{datetime.now().strftime('%Y%m%d%H%M%S')}")
    shutil.copy2(env_path, backup)
    print(f"\nBackup written to {backup}")

    env_path.write_text("".join(new_lines), encoding="utf-8")
    print(f"Updated {env_path}")
    print("\nNext steps:")
    print("  • If VICAYA_LIBRARY_FOLDERS is blank, set it to your library root(s).")
    print("  • If you had VICAYA_CALIBRE_LIBRARY set, add that path to VICAYA_LIBRARY_FOLDERS.")
    print("    The indexer auto-detects Calibre's metadata.db — no separate variable needed.")
    print("  • Run: uv run tools/research_sources.py library-folders-check")


if __name__ == "__main__":
    main()
