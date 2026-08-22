"""Tests for the note/PDF twin audit and repair script."""

from __future__ import annotations

from pathlib import Path

from scripts import sync_note_pdfs


def _vault(tmp_path: Path, monkeypatch) -> Path:
    """A vault whose PDF tree already mirrors one root note and one Digest note."""
    notes_root = tmp_path / "vault" / "Vicaya"
    for relative in ("2099-01-01 - root.md", "Digest/2099-01-02 - digest.md"):
        note = notes_root / relative
        note.parent.mkdir(parents=True, exist_ok=True)
        note.write_text("---\ntopic: x\n---\n## Question\n\nBody.\n", encoding="utf-8")
        pdf = notes_root / "PDF" / relative.replace(".md", ".pdf")
        pdf.parent.mkdir(parents=True, exist_ok=True)
        pdf.write_bytes(b"%PDF-1.4\n")
    monkeypatch.setenv("VICAYA_VAULT_PATH", str(tmp_path / "vault"))
    monkeypatch.chdir(tmp_path)
    return notes_root


def _fake_render(monkeypatch) -> list[Path]:
    rendered: list[Path] = []

    def fake_render_pdf(_markdown_body: str, output_path: Path) -> None:
        rendered.append(output_path)
        output_path.write_bytes(b"%PDF-1.4\n")

    monkeypatch.setattr(sync_note_pdfs.generate_note_pdf, "render_pdf", fake_render_pdf)
    return rendered


def test_matched_tree_is_clean(tmp_path: Path, monkeypatch, capsys) -> None:
    _vault(tmp_path, monkeypatch)

    assert sync_note_pdfs.main([]) == 0
    assert "holds nothing else" in capsys.readouterr().out


def test_find_notes_ignores_the_pdf_tree_and_dot_dirs(
    tmp_path: Path, monkeypatch
) -> None:
    notes_root = _vault(tmp_path, monkeypatch)
    (notes_root / ".git").mkdir()
    (notes_root / ".git" / "hook.md").write_text("x", encoding="utf-8")
    (notes_root / "PDF" / "stray.md").write_text("x", encoding="utf-8")

    names = [p.name for p in sync_note_pdfs.find_notes(notes_root)]

    assert names == ["2099-01-01 - root.md", "2099-01-02 - digest.md"]


def test_check_reports_missing_and_orphans_without_touching_disk(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    notes_root = _vault(tmp_path, monkeypatch)
    (notes_root / "PDF" / "2099-01-01 - root.pdf").unlink()
    orphan = notes_root / "PDF" / "Digest" / "gone.pdf"
    orphan.write_bytes(b"%PDF-1.4\n")

    exit_code = sync_note_pdfs.main([])

    output = capsys.readouterr().out
    assert exit_code == 1
    assert "missing PDF: PDF/2099-01-01 - root.pdf" in output
    assert "orphan: PDF/Digest/gone.pdf" in output
    assert "1 missing, 1 orphaned" in output
    # A bare check must not create or remove anything.
    assert orphan.exists()
    assert not (notes_root / "PDF" / "2099-01-01 - root.pdf").exists()


def test_a_non_pdf_file_in_the_tree_is_an_orphan(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    """The tree holds note twins and nothing else, so a stray render of any
    other type is an orphan too — regression for leftover .html files."""
    notes_root = _vault(tmp_path, monkeypatch)
    (notes_root / "PDF" / "2099-01-01 - root.html").write_bytes(b"<html>")

    exit_code = sync_note_pdfs.main([])

    assert exit_code == 1
    assert "orphan: PDF/2099-01-01 - root.html" in capsys.readouterr().out


def test_fix_generates_missing_and_deletes_orphans(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    notes_root = _vault(tmp_path, monkeypatch)
    missing = notes_root / "PDF" / "Digest" / "2099-01-02 - digest.pdf"
    missing.unlink()
    orphan = notes_root / "PDF" / "gone.pdf"
    orphan.write_bytes(b"%PDF-1.4\n")
    rendered = _fake_render(monkeypatch)

    exit_code = sync_note_pdfs.main(["--fix"])

    output = capsys.readouterr().out
    assert exit_code == 0
    assert rendered == [missing]
    assert missing.exists()
    assert not orphan.exists()
    assert "1 generated, 0 regenerated, 1 deleted" in output
    # The tree is a mirror again.
    assert sync_note_pdfs.audit(notes_root).clean


def test_fix_renders_the_body_without_frontmatter(tmp_path: Path, monkeypatch) -> None:
    notes_root = _vault(tmp_path, monkeypatch)
    (notes_root / "PDF" / "2099-01-01 - root.pdf").unlink()
    bodies: list[str] = []

    def fake_render_pdf(markdown_body: str, output_path: Path) -> None:
        bodies.append(markdown_body)
        output_path.write_bytes(b"%PDF-1.4\n")

    monkeypatch.setattr(sync_note_pdfs.generate_note_pdf, "render_pdf", fake_render_pdf)

    assert sync_note_pdfs.main(["--fix"]) == 0
    assert bodies == ["## Question\n\nBody.\n"]


def test_fix_prunes_a_subfolder_left_empty(tmp_path: Path, monkeypatch) -> None:
    notes_root = _vault(tmp_path, monkeypatch)
    stale = notes_root / "PDF" / "Removed Series"
    stale.mkdir()
    (stale / "gone.pdf").write_bytes(b"%PDF-1.4\n")
    _fake_render(monkeypatch)

    assert sync_note_pdfs.main(["--fix"]) == 0
    assert not stale.exists()
    assert (notes_root / "PDF").is_dir()


def test_rebuild_regenerates_every_existing_pdf_too(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    """--rebuild exists so a PDF-rendering change (e.g. turning on footnote
    handling) reaches PDFs that already exist, not just missing ones."""
    notes_root = _vault(tmp_path, monkeypatch)
    rendered = _fake_render(monkeypatch)

    exit_code = sync_note_pdfs.main(["--fix", "--rebuild"])

    output = capsys.readouterr().out
    assert exit_code == 0
    assert sorted(rendered) == sorted(
        notes_root / "PDF" / relative
        for relative in ("2099-01-01 - root.pdf", "Digest/2099-01-02 - digest.pdf")
    )
    assert "0 generated, 2 regenerated, 0 deleted" in output


def test_rebuild_without_fix_is_a_no_op(tmp_path: Path, monkeypatch) -> None:
    _vault(tmp_path, monkeypatch)
    rendered = _fake_render(monkeypatch)

    exit_code = sync_note_pdfs.main(["--rebuild"])

    assert exit_code == 0
    assert rendered == []


def test_missing_vault_path_is_an_error(tmp_path: Path, monkeypatch, capsys) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("VICAYA_VAULT_PATH", "")

    exit_code = sync_note_pdfs.main([])

    assert exit_code == 2
    assert "VICAYA_VAULT_PATH is required" in capsys.readouterr().out
