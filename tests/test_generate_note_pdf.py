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

    output_path = vault_path / "Vicaya" / "PDF" / "2099-01-01 - sample.pdf"
    output = capsys.readouterr().out
    assert exit_code == 0
    assert rendered["output_path"] == output_path
    assert str(output_path) in output
    assert "---" not in str(rendered["markdown_body"]).splitlines()[0]
    assert "## Question" in str(rendered["markdown_body"])


def test_generate_note_pdf_mirrors_note_subfolder_under_the_pdf_tree(
    monkeypatch,
    tmp_path: Path,
) -> None:
    """All PDFs live under one Vicaya/PDF tree whose subfolders mirror the
    notes' own subfolders, so a series note in `What the Suttas Say About/`
    lands in `PDF/What the Suttas Say About/` — not in a PDF/ dir beside the
    note, and not flattened into the PDF tree root."""
    monkeypatch.chdir(tmp_path)
    vault_path = tmp_path / "vault"
    note_path = (
        vault_path / "Vicaya" / "What the Suttas Say About" / "2099-01-01 - sample.md"
    )
    note_path.parent.mkdir(parents=True)
    note_path.write_text(valid_note_text(), encoding="utf-8")
    monkeypatch.setenv("VICAYA_VAULT_PATH", str(vault_path))
    monkeypatch.setenv("VICAYA_PDF_PATH", "1")

    def fake_render_pdf(_markdown_body: str, output_path: Path) -> None:
        output_path.write_bytes(b"%PDF-1.4\n")

    monkeypatch.setattr(generate_note_pdf, "render_pdf", fake_render_pdf)

    exit_code = generate_note_pdf.main(
        ["Vicaya/What the Suttas Say About/2099-01-01 - sample.md"]
    )

    pdf_tree = vault_path / "Vicaya" / "PDF"
    expected_path = pdf_tree / "What the Suttas Say About" / "2099-01-01 - sample.pdf"
    assert exit_code == 0
    assert expected_path.exists()
    assert not (note_path.parent / "PDF").exists()
    assert not (pdf_tree / "2099-01-01 - sample.pdf").exists()


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


def test_pdf_css_keeps_images_within_the_page_width() -> None:
    """Wide inline images must scale down to the content width, otherwise they
    overflow the page edge in the generated PDF."""
    css = generate_note_pdf.PDF_CSS
    assert "img" in css
    assert "max-width: 100%" in css
    assert "height: auto" in css
