"""Install pre-push git hooks in the vicaya project repo and the notes vault repo."""

import os
import sys
import stat
from pathlib import Path
from rich import print as rprint

project_root = Path(__file__).resolve().parent.parent

HOOK_PROJECT = """\
#!/bin/sh
# Block direct git push; allow the sync scripts (VICAYA_SYNC), and allow anyone
# who has opted in with: git config --global vicaya.allowpush true
if [ -n "$VICAYA_SYNC" ]; then exit 0; fi
if [ "$(git config --bool vicaya.allowpush 2>/dev/null)" = "true" ]; then exit 0; fi
echo "Direct git push is restricted in this repo." >&2
echo "Use: uv run scripts/sync_notes.py <file>  or  uv run scripts/sync_run_report.py" >&2
exit 1
"""

HOOK_NOTES = """\
#!/bin/sh
# Block direct git push; allow the sync scripts (VICAYA_SYNC), and allow anyone
# who has opted in with: git config --global vicaya.allowpush true
if [ -n "$VICAYA_SYNC" ]; then exit 0; fi
if [ "$(git config --bool vicaya.allowpush 2>/dev/null)" = "true" ]; then exit 0; fi
echo "Direct git push is restricted in this repo." >&2
echo "Use: uv run scripts/sync_notes.py <file>" >&2
exit 1
"""


def load_dotenv(path: Path) -> None:
    if not path.exists():
        return
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, val = line.partition("=")
        os.environ.setdefault(key.strip(), val.strip().strip('"').strip("'"))


def install_hook(hook_path: Path, content: str, label: str) -> None:
    hook_path.write_text(content, encoding="utf-8")
    hook_path.chmod(
        hook_path.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH
    )
    rprint(f"[green]Installed[/green] {label} → {hook_path}")


def main() -> None:
    load_dotenv(project_root / ".env")

    errors = 0

    # 1. Project repo hook
    project_hooks = project_root / ".git" / "hooks"
    if not project_hooks.exists():
        rprint(f"[red]Error: {project_hooks} not found — is this a git repo?[/red]")
        errors += 1
    else:
        install_hook(project_hooks / "pre-push", HOOK_PROJECT, "project repo pre-push")

    # 2. Notes vault repo hook
    vault_path_raw = os.environ.get("VICAYA_VAULT_PATH")
    if not vault_path_raw:
        rprint("[red]Error: VICAYA_VAULT_PATH not set in .env[/red]")
        errors += 1
    else:
        notes_hooks = Path(vault_path_raw).expanduser() / "Vicaya" / ".git" / "hooks"
        if not notes_hooks.exists():
            rprint(
                f"[red]Error: {notes_hooks} not found — is the notes vault a git repo?[/red]"
            )
            errors += 1
        else:
            install_hook(notes_hooks / "pre-push", HOOK_NOTES, "notes vault pre-push")

    if errors:
        sys.exit(1)
    rprint("[green]All hooks installed.[/green]")


if __name__ == "__main__":
    main()
