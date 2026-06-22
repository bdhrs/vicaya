"""Commit a single Vicaya note and best-effort push it to the remote."""

import os
import subprocess
import sys
import argparse
from pathlib import Path
from rich import print as rprint

project_root = Path(__file__).resolve().parent.parent


def load_dotenv(path: Path) -> None:
    if not path.exists():
        return
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, val = line.partition("=")
        key = key.strip()
        val = val.strip().strip('"').strip("'")
        os.environ.setdefault(key, val)


def run_git(
    args: list[str], repo_path: Path, check: bool = True
) -> subprocess.CompletedProcess:
    cmd = ["git", "-C", str(repo_path)] + args
    return subprocess.run(cmd, check=check, capture_output=True, text=True)


def main(argv: list[str] | None = None):
    parser = argparse.ArgumentParser(description="Pull, commit, and push Vicaya notes.")
    parser.add_argument(
        "filename",
        nargs="?",
        help="Note filename to commit and push (relative to Vicaya/ folder).",
    )
    args = parser.parse_args(argv)

    load_dotenv(project_root / ".env")

    vault_path_raw = os.environ.get("VICAYA_VAULT_PATH")
    if not vault_path_raw:
        rprint("[red]Error: VICAYA_VAULT_PATH not found in .env[/red]")
        sys.exit(1)

    vault_path = Path(vault_path_raw).expanduser()
    notes_repo = vault_path / "Vicaya"

    if not notes_repo.exists():
        rprint(f"[red]Error: Notes repository directory not found: {notes_repo}[/red]")
        sys.exit(1)

    if not args.filename:
        rprint("[yellow]No filename provided; nothing to commit.[/yellow]")
        return

    filename = args.filename
    if filename.startswith("Vicaya/"):
        filename = filename[7:]

    note_path = notes_repo / filename
    if not note_path.exists():
        rprint(f"[red]Error: Note file not found: {note_path}[/red]")
        sys.exit(1)

    try:
        rprint("[cyan]Git add...[/cyan]", end=" ")
        run_git(["add", "--", filename], notes_repo)
        rprint("[green]ok[/green]")

        staged = run_git(
            ["diff", "--cached", "--quiet", "--", filename], notes_repo, check=False
        )
        if staged.returncode == 0:
            rprint("[yellow]Nothing to commit[/yellow]")
        else:
            slug = Path(filename).stem
            rprint("[cyan]Git commit...[/cyan]", end=" ")
            run_git(["commit", "-m", f"note: {slug}", "--", filename], notes_repo)
            rprint("[green]ok[/green]")
    except subprocess.CalledProcessError as e:
        rprint("[red]failed[/red]")
        rprint(f"[red]Git command failed: git {' '.join(e.cmd)}[/red]")
        if e.stdout:
            print(e.stdout)
        if e.stderr:
            print(e.stderr)
        sys.exit(e.returncode)

    branch = run_git(
        ["rev-parse", "--abbrev-ref", "HEAD"], notes_repo, check=False
    ).stdout.strip()
    if not branch or branch == "HEAD":
        branch = "main"

    # Rebase the local commit onto the latest remote before pushing, so a
    # remote that advanced on a multi-run day does not strand the commit.
    # --autostash keeps other in-flight vault edits from blocking the rebase.
    rprint("[cyan]Git pull --rebase...[/cyan]", end=" ")
    pull = run_git(
        ["pull", "--rebase", "--autostash", "origin", branch], notes_repo, check=False
    )
    if pull.returncode == 0:
        rprint("[green]ok[/green]")
    else:
        rprint("[yellow]rebase failed (commit saved locally)[/yellow]")
        if pull.stderr:
            print(pull.stderr)
        # Restore a clean state so the next run is not stuck mid-rebase.
        run_git(["rebase", "--abort"], notes_repo, check=False)
        rprint(f"[green]Committed {filename} locally[/green]")
        return

    # Push is best-effort: a remote failure must not undo the local commit.
    rprint("[cyan]Git push...[/cyan]", end=" ")
    push = run_git(
        ["push", "origin", f"HEAD:refs/heads/{branch}"], notes_repo, check=False
    )
    if push.returncode == 0:
        rprint("[green]ok[/green]")
        rprint(f"[green]Successfully synced {filename}[/green]")
    else:
        rprint("[yellow]push failed (commit saved locally)[/yellow]")
        if push.stderr:
            print(push.stderr)
        rprint(f"[green]Committed {filename} locally[/green]")


if __name__ == "__main__":
    main()
