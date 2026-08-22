"""Tests for the final-note PDF generation command-line script."""

from __future__ import annotations

from pathlib import Path

import pytest

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


def test_render_pdf_produces_a_pdf_with_footnotes_in_the_body(
    tmp_path: Path,
) -> None:
    """A footnote marker in the body must render into a real PDF, not raw
    `[^id]` text — the defect this change fixes."""
    try:
        import weasyprint  # noqa: F401
    except ImportError:
        pytest.skip("weasyprint not installed")
    body = (
        "Claim one.[^s0101m-17] Claim two in a table cell:\n\n"
        "| Angle | Ref |\n"
        "| --- | --- |\n"
        "| x | [^web-1] |\n\n"
        "> A quoted line.[^s0101m-17]\n\n"
        "[^s0101m-17]: DN1 Brahmajālasuttaṃ para 17 — db: s0101m_mul, para 17\n"
        "[^web-1]: [Pali](https://en.wikipedia.org/wiki/Pali) — retrieved 2026-08-18\n"
    )
    output_path = tmp_path / "note.pdf"

    generate_note_pdf.render_pdf(body, output_path)

    pdf_bytes = output_path.read_bytes()
    assert output_path.exists()
    assert pdf_bytes.startswith(b"%PDF")


def test_place_footnotes_at_page_foot_moves_definitions_to_the_call_site() -> None:
    """Each footnote's definition text moves to sit at its calling marker,
    wrapped for WeasyPrint's page-footnote float, and the trailing
    definitions list — which would otherwise print twice — is removed."""
    import markdown

    body = (
        "Claim one.[^a] Claim two.[^b]\n\n[^a]: First locator.\n[^b]: Second locator.\n"
    )
    html = markdown.markdown(body, extensions=["tables", "fenced_code", "footnotes"])

    placed = generate_note_pdf._place_footnotes_at_page_foot(html)

    assert "[^a]" not in placed
    assert '<span class="pagefn">First locator.</span>' in placed
    assert '<span class="pagefn">Second locator.</span>' in placed
    assert '<div class="footnote">' not in placed
    assert "fnref" not in placed


def test_place_footnotes_at_page_foot_repeats_the_full_note_on_repeat_citation() -> (
    None
):
    """A source cited twice prints its full note both times — no lookup back
    to an earlier page, which is the whole point of page-bottom notes."""
    import markdown

    body = "Claim one.[^a] Claim two, same source.[^a]\n\n[^a]: The locator.\n"
    html = markdown.markdown(body, extensions=["tables", "fenced_code", "footnotes"])

    placed = generate_note_pdf._place_footnotes_at_page_foot(html)

    assert placed.count('<span class="pagefn">The locator.</span>') == 2


def test_place_footnotes_at_page_foot_keeps_every_paragraph_of_a_definition() -> None:
    """A footnote definition spanning more than one paragraph must keep all
    of them — the earlier version silently dropped everything past the
    first `</p>`."""
    import markdown

    body = (
        "Claim.[^a]\n\n"
        "[^a]: First paragraph of the note.\n"
        "\n"
        "    Second paragraph, indented continuation.\n"
    )
    html = markdown.markdown(body, extensions=["tables", "fenced_code", "footnotes"])

    placed = generate_note_pdf._place_footnotes_at_page_foot(html)

    assert "First paragraph of the note." in placed
    assert "Second paragraph, indented continuation." in placed


def test_place_footnotes_at_page_foot_flags_a_dangling_marker() -> None:
    """A `[^id]` with no matching `[^id]: ...` definition must render as a
    visibly wrong marker, not a silently blank note."""
    body = 'Claim.<sup id="fnref:ghost"><a class="footnote-ref" href="#fn:ghost">1</a></sup>'

    placed = generate_note_pdf._place_footnotes_at_page_foot(body)

    assert "missing footnote: ghost" in placed
    assert "fnref" not in placed


def test_pdf_css_floats_footnotes_to_the_page_they_are_cited_on() -> None:
    css = generate_note_pdf.PDF_CSS
    assert "@footnote" in css
    assert "float: footnote" in css
    assert "::footnote-call" in css


def test_pdf_css_does_not_zero_the_footnote_call_line_height() -> None:
    """`line-height: 0` on a footnote-call marker once made WeasyPrint emit a
    zero-height link annotation Rect elsewhere in this file — a real link
    nothing could click. Regression guard: keep line-height off this rule
    too, even though this marker isn't itself a link."""
    css = generate_note_pdf.PDF_CSS
    rule = css[css.index("::footnote-call") : css.index("::footnote-call") + 200]
    assert "line-height" not in rule
