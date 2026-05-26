"""Synchronize Vicaya notes with the remote repository: pull, commit, and push."""
import os
import subprocess
import sys
import argparse
from pathlib import Path

# Add project root to sys.path so we can import tools
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from tools import printer as pr

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
    """Run a git command in the specified repository."""
    cmd = ["git", "-C", str(repo_path)] + args
    return subprocess.run(cmd, check=True, capture_output=True, text=True)

def main():
    parser = argparse.ArgumentParser(description="Pull, commit, and push Vicaya notes.")
    parser.add_argument("filename", nargs="?", help="The note filename to commit and push (relative to Vicaya/ folder).")
    args = parser.parse_args()

    load_dotenv(project_root / ".env")

    vault_path_raw = os.environ.get("VICAYA_VAULT_PATH")
    if not vault_path_raw:
        pr.red("Error: VICAYA_VAULT_PATH not found in .env")
        sys.exit(1)

    vault_path = Path(vault_path_raw).expanduser()
    notes_repo = vault_path / "Vicaya"

    if not notes_repo.exists():
        pr.red(f"Error: Notes repository directory not found: {notes_repo}")
        sys.exit(1)

    try:
        # 1. Pull first
        pr.cyan_tmr("Git pull")
        run_git(["pull", "--rebase", "origin", "HEAD"], notes_repo)
        pr.yes("ok")

        if args.filename:
            filename = args.filename
            # The agent might pass "Vicaya/2026-05-26 - topic.md" or just "2026-05-26 - topic.md"
            if filename.startswith("Vicaya/"):
                filename = filename[7:]
            
            note_path = notes_repo / filename
            if not note_path.exists():
                pr.red(f"Error: Note file not found: {note_path}")
                sys.exit(1)

            # 2. Add
            pr.cyan_tmr("Git add")
            run_git(["add", filename], notes_repo)
            pr.yes("ok")

            # 3. Commit
            # Check if there are changes to commit
            status = run_git(["status", "--porcelain"], notes_repo)
            if status.stdout.strip():
                slug = Path(filename).stem
                pr.cyan_tmr("Git commit")
                run_git(["commit", "-m", f"note: {slug}"], notes_repo)
                pr.yes("ok")
            else:
                pr.amber("Nothing to commit")

            # 4. Push
            pr.cyan_tmr("Git push")
            run_git(["push", "origin", "HEAD"], notes_repo)
            pr.yes("ok")
            
            pr.green(f"Successfully synced {filename}")
        else:
            pr.amber("No filename provided, only pull performed.")

    except subprocess.CalledProcessError as e:
        pr.no("failed")
        pr.red(f"Git command failed: git {' '.join(e.cmd)}")
        if e.stdout:
            print(e.stdout)
        if e.stderr:
            print(e.stderr)
        sys.exit(e.returncode)
    except Exception as e:
        pr.red(f"An unexpected error occurred: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
