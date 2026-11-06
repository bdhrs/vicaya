"""Pull the vicaya repo and the notes repo before a skill run (best effort)."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
PULL_TIMEOUT = 120


def load_dotenv(path: Path) -> None:
    """Set .env values as defaults, without overriding the real environment."""
    if not path.exists():
        return
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, val = line.partition("=")
        os.environ.setdefault(key.strip(), val.strip().strip('"').strip("'"))


def git(repo: Path, *args: str) -> subprocess.CompletedProcess:
    """Run git in `repo` without ever prompting for credentials."""
    return subprocess.run(
        ["git", "-C", str(repo), *args],
        capture_output=True,
        text=True,
        timeout=PULL_TIMEOUT,
        env={**os.environ, "GIT_TERMINAL_PROMPT": "0"},
    )


def _git_dir(repo: Path) -> Path | None:
    r = git(repo, "rev-parse", "--absolute-git-dir")
    return Path(r.stdout.strip()) if r.returncode == 0 else None


def _blocking_state(git_dir: Path) -> str | None:
    """Name the in-progress operation that makes a pull unsafe, if any."""
    markers = {
        "rebase-merge": "rebase",
        "rebase-apply": "rebase",
        "MERGE_HEAD": "merge",
        "CHERRY_PICK_HEAD": "cherry-pick",
    }
    for marker, name in markers.items():
        if (git_dir / marker).exists():
            return name
    return None


def _last_line(text: str) -> str:
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    return lines[-1] if lines else ""


def sync_repo(label: str, repo: Path) -> str:
    """Pull one repo and return a one-line status; never raises on git failure."""
    if not repo.is_dir():
        return f"{label}: skipped (not found: {repo})"

    top = git(repo, "rev-parse", "--show-toplevel")
    if top.returncode != 0 or Path(top.stdout.strip()).resolve() != repo.resolve():
        return f"{label}: skipped (not a git repository: {repo})"

    git_dir = _git_dir(repo)
    if git_dir is None:
        return f"{label}: skipped (not a git repository: {repo})"

    blocked = _blocking_state(git_dir)
    if blocked:
        return f"{label}: skipped ({blocked} in progress: {repo})"

    branch_ref = git(repo, "symbolic-ref", "--short", "-q", "HEAD")
    branch = branch_ref.stdout.strip()
    if branch_ref.returncode != 0 or not branch:
        return f"{label}: skipped (detached HEAD: {repo})"

    upstream = git(
        repo, "rev-parse", "--abbrev-ref", "--symbolic-full-name", f"{branch}@{{u}}"
    )
    target: list[str] = []
    if upstream.returncode != 0 or not upstream.stdout.strip():
        remotes = git(repo, "remote").stdout.split()
        if "origin" not in remotes:
            return f"{label}: skipped (no upstream or origin remote: {repo})"
        target = ["origin", branch]

    before = git(repo, "rev-parse", "HEAD").stdout.strip()

    try:
        pull = git(repo, "pull", "--rebase", "--autostash", "--quiet", *target)
    except subprocess.TimeoutExpired:
        return f"{label}: warning (pull timed out after {PULL_TIMEOUT}s; continuing)"

    if pull.returncode != 0:
        # Never leave a half-finished rebase behind for the next command.
        if _blocking_state(git_dir) == "rebase":
            git(repo, "rebase", "--abort")
        reason = _last_line(pull.stderr) or _last_line(pull.stdout)
        reason = reason or f"exit {pull.returncode}"
        return f"{label}: warning (pull failed, continuing: {reason})"

    after = git(repo, "rev-parse", "HEAD").stdout.strip()
    if before == after:
        return f"{label}: up to date ({branch})"
    return f"{label}: pulled ({branch}, {before[:7]}..{after[:7]})"


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if argv and argv[0] in {"-h", "--help"}:
        print(
            "usage: sync_repos.py\n\n"
            "Pull the vicaya repo and $VICAYA_VAULT_PATH/Vicaya before a skill run.\n"
            "Best effort: repo-less dirs, offline remotes and mid-merge states are\n"
            "skipped or warned about, never fatal."
        )
        return 0
    if argv:
        print(f"sync_repos: ignoring unknown arguments: {' '.join(argv)}")

    load_dotenv(PROJECT_ROOT / ".env")

    print(sync_repo("vicaya", PROJECT_ROOT))

    vault_raw = os.environ.get("VICAYA_VAULT_PATH", "").strip()
    if vault_raw:
        notes_repo = Path(os.path.expanduser(vault_raw)) / "Vicaya"
        print(sync_repo("notes", notes_repo))
    else:
        print("notes: skipped (VICAYA_VAULT_PATH is not set in .env)")

    # A pull failure is never fatal: the run must proceed on the local checkout.
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
