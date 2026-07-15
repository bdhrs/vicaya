"""Tests for the final-note PDF generation command-line script."""

from __future__ import annotations

from pathlib import Path

from scripts import generate_note_pdf
from tests.test_note_checks import valid_note_text


def test_generate_note_pdf_skips_when_pdf_path_is_unset(
    capsys,
    monkeypatch,
    tmp_path: Path,
) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("VICAYA_PDF_PATH", raising=False)

    exit_code = generate_note_pdf.main(["Vicaya/2099-01-01 - missing.md"])

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "PDF generation skipped" in output
    assert "Vicaya/2099-01-01 - missing.md" in output


def test_generate_note_pdf_derives_output_path_and_strips_frontmatter(
    capsys,
    monkeypatch,
    tmp_path: Path,
) -> None:
    monkeypatch.chdir(tmp_path)
    vault_path = tmp_path / "vault"
    pdf_path = tmp_path / "pdf"
    note_path = vault_path / "Vicaya" / "2099-01-01 - sample.md"
    note_path.parent.mkdir(parents=True)
    note_path.write_text(valid_note_text(), encoding="utf-8")
    monkeypatch.setenv("VICAYA_VAULT_PATH", str(vault_path))
    monkeypatch.setenv("VICAYA_PDF_PATH", str(pdf_path))
    rendered: dict[str, object] = {}

    def fake_render_pdf(markdown_body: str, output_path: Path) -> None:
        rendered["markdown_body"] = markdown_body
        rendered["output_path"] = output_path
        output_path.write_bytes(b"%PDF-1.4\n")

    monkeypatch.setattr(generate_note_pdf, "render_pdf", fake_render_pdf)

    exit_code = generate_note_pdf.main(["Vicaya/2099-01-01 - sample.md"])

    output_path = note_path.parent / "PDF" / "2099-01-01 - sample.pdf"
    output = capsys.readouterr().out
    assert exit_code == 0
    assert rendered["output_path"] == output_path
    assert str(output_path) in output
    assert "---" not in str(rendered["markdown_body"]).splitlines()[0]
    assert "## Question" in str(rendered["markdown_body"])


def test_generate_note_pdf_writes_into_notes_own_subfolder(
    monkeypatch,
    tmp_path: Path,
) -> None:
    """Series notes live in a vault subfolder; their PDF must land in that
    subfolder's own PDF/ dir, not in the vault-root PDF/ dir — regression for
    notes being written to the wrong folder when VICAYA_PDF_PATH pointed at a
    single flat directory regardless of the note's location."""
    monkeypatch.chdir(tmp_path)
    vault_path = tmp_path / "vault"
    note_path = (
        vault_path / "Vicaya" / "What the Suttas Say About" / "2099-01-01 - sample.md"
    )
    note_path.parent.mkdir(parents=True)
    note_path.write_text(valid_note_text(), encoding="utf-8")
    monkeypatch.setenv("VICAYA_VAULT_PATH", str(vault_path))
    monkeypatch.setenv("VICAYA_PDF_PATH", "1")

    def fake_render_pdf(markdown_body: str, output_path: Path) -> None:
        output_path.write_bytes(b"%PDF-1.4\n")

    monkeypatch.setattr(generate_note_pdf, "render_pdf", fake_render_pdf)

    exit_code = generate_note_pdf.main(
        ["Vicaya/What the Suttas Say About/2099-01-01 - sample.md"]
    )

    expected_path = note_path.parent / "PDF" / "2099-01-01 - sample.pdf"
    wrong_path = vault_path / "Vicaya" / "PDF" / "2099-01-01 - sample.pdf"
    assert exit_code == 0
    assert expected_path.exists()
    assert not wrong_path.exists()


def test_generate_note_pdf_reports_missing_note(
    capsys,
    monkeypatch,
    tmp_path: Path,
) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("VICAYA_VAULT_PATH", str(tmp_path / "vault"))
    monkeypatch.setenv("VICAYA_PDF_PATH", str(tmp_path / "pdf"))

    exit_code = generate_note_pdf.main(["Vicaya/2099-01-01 - missing.md"])

    output = capsys.readouterr().out
    assert exit_code == 2
    assert "note not found" in output
