"""Sync today's Vicaya run reports to origin/main."""

import os
import subprocess
import sys
from datetime import datetime, timezone
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
        os.environ.setdefault(key.strip(), val.strip().strip('"').strip("'"))


def run_git(args: list[str], repo_path: Path) -> subprocess.CompletedProcess:
    cmd = ["git", "-C", str(repo_path)] + args
    return subprocess.run(cmd, check=True, capture_output=True, text=True)


def today_reports(repo_path: Path, today: str) -> list[str]:
    status = run_git(["status", "--porcelain", "--", "runs"], repo_path)
    reports = []
    for line in status.stdout.splitlines():
        path = line[3:]
        name = Path(path).name
        if path.startswith("runs/") and name.startswith(today) and name.endswith(".md"):
            reports.append(path)
    return sorted(set(reports))


def main() -> None:
    os.environ["VICAYA_SYNC"] = "1"
    load_dotenv(project_root / ".env")
    today = datetime.now(timezone.utc).strftime("%Y%m%d")

    user = os.environ.get("VICAYA_USER")
    if not user:
        rprint("[red]Error: VICAYA_USER not found in .env[/red]")
        sys.exit(1)

    try:
        rprint("[cyan]Git pull --rebase...[/cyan]", end=" ")
        run_git(["pull", "--rebase", "--autostash", "origin", "main"], project_root)
        rprint("[green]ok[/green]")

        reports = today_reports(project_root, today)
        if not reports:
            rprint(
                f"[yellow]No uncommitted run reports for {today}; nothing to push.[/yellow]"
            )
            return

        rprint(f"[cyan]Git add {len(reports)} run report(s)...[/cyan]", end=" ")
        run_git(["add", *reports], project_root)
        rprint("[green]ok[/green]")

        rprint("[cyan]Git commit...[/cyan]", end=" ")
        run_git(["commit", "-m", f"chore: update runs {user}"], project_root)
        rprint("[green]ok[/green]")

        rprint("[cyan]Git push...[/cyan]", end=" ")
        run_git(["push", "origin", "HEAD"], project_root)
        rprint("[green]ok[/green]")
        rprint(
            f"[green]Successfully synced {len(reports)} run report(s) for {today}[/green]"
        )
    except subprocess.CalledProcessError as e:
        rprint("[red]failed[/red]")
        rprint(f"[red]Git command failed: git {' '.join(e.cmd)}[/red]")
        if e.stdout:
            print(e.stdout)
        if e.stderr:
            print(e.stderr)
        sys.exit(e.returncode)


if __name__ == "__main__":
    main()
