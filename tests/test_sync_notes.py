"""Tests for the Vicaya note commit-and-push sync script."""

from __future__ import annotations

import subprocess
from pathlib import Path

from scripts import sync_notes


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


def _make_remote_and_clone(tmp_path: Path) -> tuple[Path, Path]:
    """A bare remote on `main` with one initial commit, plus a working clone."""
    remote = tmp_path / "remote.git"
    remote.mkdir()
    _git(remote, "init", "--bare", "--initial-branch=main")

    seed = tmp_path / "seed"
    _git(tmp_path, "clone", str(remote), str(seed))
    _init_identity(seed)
    (seed / "README.md").write_text("seed\n", encoding="utf-8")
    _git(seed, "add", "README.md")
    _git(seed, "commit", "-m", "seed")
    _git(seed, "push", "origin", "main")
    return remote, seed


def _advance_remote(tmp_path: Path, remote: Path) -> None:
    """Push an unrelated commit so the remote is ahead of the notes repo."""
    other = tmp_path / "other"
    _git(tmp_path, "clone", str(remote), str(other))
    _init_identity(other)
    (other / "other.md").write_text("other run\n", encoding="utf-8")
    _git(other, "add", "other.md")
    _git(other, "commit", "-m", "other run")
    _git(other, "push", "origin", "main")


def _setup_vault(tmp_path: Path, remote: Path, monkeypatch) -> Path:
    """Clone the remote as the vault's Vicaya repo and point the env at it."""
    vault = tmp_path / "vault"
    notes_repo = vault / "Vicaya"
    _git(tmp_path, "clone", str(remote), str(notes_repo))
    _init_identity(notes_repo)
    monkeypatch.setenv("VICAYA_VAULT_PATH", str(vault))
    return notes_repo


def test_push_succeeds_when_remote_advanced(tmp_path: Path, monkeypatch) -> None:
    remote, _ = _make_remote_and_clone(tmp_path)
    notes_repo = _setup_vault(tmp_path, remote, monkeypatch)
    _advance_remote(tmp_path, remote)

    note = notes_repo / "2099-01-01 - sample.md"
    note.write_text("# note\n", encoding="utf-8")

    sync_notes.main(["2099-01-01 - sample.md"])

    # The note commit reached the remote — it was not stranded locally.
    remote_log = _git(remote, "log", "--name-only", "--pretty=format:%s", "main")
    assert "2099-01-01 - sample.md" in remote_log
    assert "other run" in remote_log


def test_dirty_tree_does_not_block_push(tmp_path: Path, monkeypatch) -> None:
    remote, _ = _make_remote_and_clone(tmp_path)
    notes_repo = _setup_vault(tmp_path, remote, monkeypatch)
    _advance_remote(tmp_path, remote)

    note = notes_repo / "2099-01-02 - sample.md"
    note.write_text("# note\n", encoding="utf-8")
    # Another in-flight vault edit dirties the working tree during the sync.
    (notes_repo / "draft.md").write_text("work in progress\n", encoding="utf-8")

    sync_notes.main(["2099-01-02 - sample.md"])

    remote_log = _git(remote, "log", "--name-only", "--pretty=format:%s", "main")
    assert "2099-01-02 - sample.md" in remote_log
    # The unrelated dirty file survived the autostash and is still uncommitted.
    assert (notes_repo / "draft.md").read_text(encoding="utf-8") == "work in progress\n"
    assert "draft.md" not in remote_log
