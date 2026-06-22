"""Tests for the final-note validation command-line script."""

from __future__ import annotations

from pathlib import Path

from scripts import validate_note
from tests.test_note_checks import valid_note_text


def test_validate_note_exits_zero_for_valid_absolute_note(
    capsys,
    monkeypatch,
    tmp_path: Path,
) -> None:
    monkeypatch.chdir(tmp_path)
    note_path = tmp_path / "2099-01-01 - sample.md"
    note_path.write_text(valid_note_text(), encoding="utf-8")

    exit_code = validate_note.main([str(note_path)])

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "PASS" in output


def test_validate_note_exits_nonzero_for_invalid_note(
    capsys,
    monkeypatch,
    tmp_path: Path,
) -> None:
    monkeypatch.chdir(tmp_path)
    note_path = tmp_path / "2099-01-01 - sample.md"
    note_path.write_text("## Question\n\nNo frontmatter.\n", encoding="utf-8")

    exit_code = validate_note.main([str(note_path)])

    output = capsys.readouterr().out
    assert exit_code == 1
    assert str(note_path) in output
    assert "missing-frontmatter" in output


def test_validate_note_resolves_vicaya_relative_note(
    monkeypatch,
    tmp_path: Path,
) -> None:
    monkeypatch.chdir(tmp_path)
    vault_path = tmp_path / "vault"
    note_path = vault_path / "Vicaya" / "2099-01-01 - sample.md"
    note_path.parent.mkdir(parents=True)
    note_path.write_text(valid_note_text(), encoding="utf-8")
    monkeypatch.setenv("VICAYA_VAULT_PATH", str(vault_path))

    exit_code = validate_note.main(["Vicaya/2099-01-01 - sample.md"])

    assert exit_code == 0


def test_validate_note_requires_vault_path_for_relative_note(
    capsys,
    monkeypatch,
    tmp_path: Path,
) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("VICAYA_VAULT_PATH", raising=False)

    exit_code = validate_note.main(["Vicaya/2099-01-01 - sample.md"])

    output = capsys.readouterr().out
    assert exit_code == 2
    assert "VICAYA_VAULT_PATH is required" in output
