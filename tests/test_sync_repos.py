"""Tests for the pre-run repo pull (project repo + notes repo)."""

from __future__ import annotations

import subprocess
from pathlib import Path

from scripts import sync_repos


def _git(repo: Path, *args: str) -> str:
    out = subprocess.run(
        ["git", "-C", str(repo), *args],
        check=True,
        capture_output=True,
        text=True,
    )
    return out.stdout


def _init_identity(repo: Path) -> None:
    _git(repo, "config", "user.email", "test@example.com")
    _git(repo, "config", "user.name", "Test")


def _make_remote_and_clone(tmp_path: Path, name: str) -> tuple[Path, Path]:
    """A bare remote on `main` with one commit, plus a clone that is level with it."""
    remote = tmp_path / f"{name}-remote.git"
    remote.mkdir()
    _git(remote, "init", "--bare", "--initial-branch=main")

    seed = tmp_path / f"{name}-seed"
    _git(tmp_path, "clone", str(remote), str(seed))
    _init_identity(seed)
    (seed / "README.md").write_text("seed\n", encoding="utf-8")
    _git(seed, "add", "README.md")
    _git(seed, "commit", "-m", "seed")
    _git(seed, "push", "origin", "main")

    clone = tmp_path / name
    _git(tmp_path, "clone", str(remote), str(clone))
    _init_identity(clone)
    return remote, clone


def _advance_remote(tmp_path: Path, remote: Path, name: str) -> None:
    """Push one commit so a clone of `remote` is behind it."""
    other = tmp_path / f"{name}-other"
    _git(tmp_path, "clone", str(remote), str(other))
    _init_identity(other)
    (other / f"{name}-new.md").write_text("new\n", encoding="utf-8")
    _git(other, "add", f"{name}-new.md")
    _git(other, "commit", "-m", f"{name} update")
    _git(other, "push", "origin", "main")


def test_pulls_new_commits(tmp_path: Path) -> None:
    remote, clone = _make_remote_and_clone(tmp_path, "proj")
    _advance_remote(tmp_path, remote, "proj")

    status = sync_repos.sync_repo("proj", clone)

    assert status.startswith("proj: pulled")
    assert (clone / "proj-new.md").exists()


def test_skips_non_git_directory(tmp_path: Path) -> None:
    plain = tmp_path / "plain"
    plain.mkdir()

    status = sync_repos.sync_repo("plain", plain)

    assert "skipped" in status
    assert "not a git repository" in status


def test_skips_missing_directory(tmp_path: Path) -> None:
    status = sync_repos.sync_repo("notes", tmp_path / "missing")

    assert "skipped" in status
    assert "not found" in status


def test_pull_failure_is_not_fatal(tmp_path: Path) -> None:
    remote, clone = _make_remote_and_clone(tmp_path, "proj")
    subprocess.run(["rm", "-rf", str(remote)], check=True)

    status = sync_repos.sync_repo("proj", clone)

    assert "warning" in status
    assert "continuing" in status


def test_main_reads_vault_path_from_dotenv(tmp_path: Path, monkeypatch, capsys) -> None:
    """The notes repo location comes from .env, not from a hard-coded path."""
    project_remote, project = _make_remote_and_clone(tmp_path, "proj")
    notes_remote, _ = _make_remote_and_clone(tmp_path, "notes")

    vault = tmp_path / "vault"
    vault.mkdir()
    _git(tmp_path, "clone", str(notes_remote), str(vault / "Vicaya"))

    _advance_remote(tmp_path, project_remote, "proj")
    _advance_remote(tmp_path, notes_remote, "notes")

    monkeypatch.setattr(sync_repos, "PROJECT_ROOT", project)
    monkeypatch.delenv("VICAYA_VAULT_PATH", raising=False)
    (project / ".env").write_text(f"VICAYA_VAULT_PATH={vault}\n", encoding="utf-8")

    assert sync_repos.main([]) == 0

    out = capsys.readouterr().out
    assert "vicaya: pulled" in out
    assert "notes: pulled" in out
    assert (vault / "Vicaya" / "notes-new.md").exists()
