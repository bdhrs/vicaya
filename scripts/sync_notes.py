"""Synchronize Vicaya notes with the remote repository: pull, commit, and push."""
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


def run_git(args: list[str], repo_path: Path) -> subprocess.CompletedProcess:
    cmd = ["git", "-C", str(repo_path)] + args
    return subprocess.run(cmd, check=True, capture_output=True, text=True)


def main():
    parser = argparse.ArgumentParser(description="Pull, commit, and push Vicaya notes.")
    parser.add_argument("filename", nargs="?", help="Note filename to commit and push (relative to Vicaya/ folder).")
    args = parser.parse_args()

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

    try:
        rprint("[cyan]Git pull...[/cyan]", end=" ")
        run_git(["pull", "--rebase"], notes_repo)
        rprint("[green]ok[/green]")

        if args.filename:
            filename = args.filename
            if filename.startswith("Vicaya/"):
                filename = filename[7:]

            note_path = notes_repo / filename
            if not note_path.exists():
                rprint(f"[red]Error: Note file not found: {note_path}[/red]")
                sys.exit(1)

            rprint("[cyan]Git add...[/cyan]", end=" ")
            run_git(["add", filename], notes_repo)
            rprint("[green]ok[/green]")

            status = run_git(["status", "--porcelain"], notes_repo)
            if status.stdout.strip():
                slug = Path(filename).stem
                rprint("[cyan]Git commit...[/cyan]", end=" ")
                run_git(["commit", "-m", f"note: {slug}"], notes_repo)
                rprint("[green]ok[/green]")
            else:
                rprint("[yellow]Nothing to commit[/yellow]")

            rprint("[cyan]Git push...[/cyan]", end=" ")
            run_git(["push", "origin", "HEAD"], notes_repo)
            rprint("[green]ok[/green]")

            rprint(f"[green]Successfully synced {filename}[/green]")
        else:
            rprint("[yellow]No filename provided, only pull performed.[/yellow]")

    except subprocess.CalledProcessError as e:
        rprint("[red]failed[/red]")
        rprint(f"[red]Git command failed: git {' '.join(e.cmd)}[/red]")
        if e.stdout:
            print(e.stdout)
        if e.stderr:
            print(e.stderr)
        sys.exit(e.returncode)
    except Exception as e:
        rprint(f"[red]An unexpected error occurred: {e}[/red]")
        sys.exit(1)


if __name__ == "__main__":
    main()
