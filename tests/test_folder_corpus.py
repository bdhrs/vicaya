"""Exercise the unmanaged folder-corpus index helpers."""

from __future__ import annotations

import json
import os
import shutil
import sqlite3
import subprocess
import sys
import time
import zipfile
from pathlib import Path

import pytest

from tools import folder_corpus
from tools.folder_corpus import (
    INDEX_ENV,
    ROOT_ENV,
    FolderCorpusConfig,
    check,
    default_config,
    duplicates,
    initialize_schema,
    refresh,
    search,
)


REPO_ROOT = Path(__file__).resolve().parents[1]


def _doc_extractor_available() -> bool:
    return (
        (sys.platform == "darwin" and shutil.which("textutil") is not None)
        or shutil.which("antiword") is not None
        or shutil.which("catdoc") is not None
    )


def test_default_config_reports_missing_values(monkeypatch):
    monkeypatch.setenv(ROOT_ENV, "")
    monkeypatch.setenv(INDEX_ENV, "")

    config = default_config()

    assert config.root is None
    assert config.index is None
    assert config.status == "unavailable"
    assert config.missing == (ROOT_ENV, INDEX_ENV)


def test_default_config_expands_home(monkeypatch):
    monkeypatch.setenv(ROOT_ENV, "~/folder-corpus-source")
    monkeypatch.setenv(INDEX_ENV, "~/folder-corpus-index.sqlite")

    config = default_config()

    assert config.root == Path.home() / "folder-corpus-source"
    assert config.index == Path.home() / "folder-corpus-index.sqlite"
    assert config.available


def test_initialize_schema_creates_public_tables():
    conn = sqlite3.connect(":memory:")

    initialize_schema(conn)

    names = {
        row[0]
        for row in conn.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table'"
        ).fetchall()
    }
    assert {"documents", "document_fts", "index_meta"} <= names


def test_check_reports_missing_root_without_creating_index(tmp_path):
    root = tmp_path / "missing"
    index = tmp_path / "folder.sqlite"
    config = FolderCorpusConfig(root=root, index=index)

    report = check(config)

    assert report["status"] == "unavailable"
    assert report["root_path"] == str(root)
    assert report["index_path"] == str(index)
    assert report["root_available"] is False
    assert report["index_exists"] is False
    assert report["fts5"] is True
    assert report["document_count"] is None
    assert not index.exists()


def test_check_counts_documents_in_existing_index(tmp_path):
    root = tmp_path / "root"
    root.mkdir()
    index = tmp_path / "folder.sqlite"
    with sqlite3.connect(index) as conn:
        initialize_schema(conn)
        conn.execute(
            """
            INSERT INTO documents (
                source_path, rel_path, filename, extension, category_path,
                size, mtime, content_hash, text_hash, extraction_status, indexed_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                str(root / "a.txt"),
                "a.txt",
                "a.txt",
                ".txt",
                "",
                3,
                1.0,
                "abc",
                "def",
                "ok",
                "2026-06-08T00:00:00+00:00",
            ),
        )
        conn.commit()

    report = check(FolderCorpusConfig(root=root, index=index))

    assert report["status"] == "ok"
    assert report["root_available"] is True
    assert report["index_exists"] is True
    assert report["index_available"] is True
    assert report["document_count"] == 1


def test_refresh_indexes_text_html_and_metadata_only_files(tmp_path):
    root = tmp_path / "root"
    root.mkdir()
    (root / "plain.txt").write_text("plain nibbana text", encoding="utf-8")
    (root / "page.html").write_text(
        "<html><body><p>html dhamma text</p></body></html>",
        encoding="utf-8",
    )
    (root / "book.pdf").write_bytes(b"%PDF metadata only")
    index = tmp_path / "folder.sqlite"

    report = refresh(FolderCorpusConfig(root=root, index=index))

    assert report["indexed"] == 3
    assert report["text_extracted"] == 2
    assert report["metadata_only"] == 1
    with sqlite3.connect(index) as conn:
        docs = conn.execute(
            """
            SELECT rel_path, extraction_status, text_hash IS NOT NULL
            FROM documents
            ORDER BY rel_path
            """
        ).fetchall()
        fts_text = [row[0] for row in conn.execute("SELECT text FROM document_fts")]
    assert docs[0][0] == "book.pdf"
    assert docs[0][1].startswith(("unsupported:", "error:"))
    assert docs[0][2] == 0
    assert docs[1:] == [
        ("page.html", "ok", 1),
        ("plain.txt", "ok", 1),
    ]
    assert "html dhamma text" in fts_text


def test_refresh_records_hash_read_errors_without_crashing(tmp_path, monkeypatch):
    root = tmp_path / "root"
    root.mkdir()
    bad = root / "bad.txt"
    bad.write_text("unreadable target text", encoding="utf-8")
    index = tmp_path / "folder.sqlite"
    original_hash_file = folder_corpus._hash_file

    def fail_hash(path: Path) -> str:
        if path == bad:
            raise OSError(22, "Invalid argument")
        return original_hash_file(path)

    monkeypatch.setattr(folder_corpus, "_hash_file", fail_hash)

    report = refresh(FolderCorpusConfig(root=root, index=index))

    assert report["status"] == "ok"
    assert report["written"] == 1
    assert report["metadata_only"] == 1
    assert report["error_count"] == 1
    assert report["errors"][0]["relative_path"] == "bad.txt"
    with sqlite3.connect(index) as conn:
        row = conn.execute(
            "SELECT content_hash, text_hash, extraction_status FROM documents"
        ).fetchone()
    assert row[0].startswith("unreadable:")
    assert row[1] is None
    assert row[2].startswith("error: file read failed:")


def test_incremental_refresh_skips_unchanged_and_deletes_missing(tmp_path):
    root = tmp_path / "root"
    root.mkdir()
    keep = root / "keep.txt"
    remove = root / "remove.txt"
    keep.write_text("keep text", encoding="utf-8")
    remove.write_text("remove text", encoding="utf-8")
    index = tmp_path / "folder.sqlite"
    config = FolderCorpusConfig(root=root, index=index)

    refresh(config)
    with sqlite3.connect(index) as conn:
        first_stamps = dict(conn.execute("SELECT rel_path, indexed_at FROM documents"))
    time.sleep(0.001)
    second = refresh(config)
    with sqlite3.connect(index) as conn:
        second_stamps = dict(conn.execute("SELECT rel_path, indexed_at FROM documents"))
    remove.unlink()
    third = refresh(config)
    with sqlite3.connect(index) as conn:
        remaining = [row[0] for row in conn.execute("SELECT rel_path FROM documents")]

    assert second["skipped"] == 2
    assert second["written"] == 0
    assert first_stamps == second_stamps
    assert third["deleted"] == 1
    assert remaining == ["keep.txt"]


def test_refresh_unavailable_root_mutates_nothing(tmp_path):
    root = tmp_path / "root"
    root.mkdir()
    (root / "keep.txt").write_text("keep text", encoding="utf-8")
    index = tmp_path / "folder.sqlite"
    refresh(FolderCorpusConfig(root=root, index=index))

    report = refresh(FolderCorpusConfig(root=tmp_path / "missing", index=index))

    assert report["status"] == "unavailable"
    with sqlite3.connect(index) as conn:
        rows = conn.execute("SELECT rel_path FROM documents").fetchall()
    assert rows == [("keep.txt",)]


def test_search_returns_text_hits_and_html_snippets_without_tags(tmp_path):
    root = tmp_path / "root"
    root.mkdir()
    (root / "plain.txt").write_text("nibbana target", encoding="utf-8")
    (root / "page.html").write_text("<p>dhamma target</p>", encoding="utf-8")
    index = tmp_path / "folder.sqlite"
    config = FolderCorpusConfig(root=root, index=index)
    refresh(config)

    text_hits = search("nibbana", config)
    html_hits = search("dhamma", config)

    assert [hit["relative_path"] for hit in text_hits] == ["plain.txt"]
    assert [hit["relative_path"] for hit in html_hits] == ["page.html"]
    assert "<p>" not in html_hits[0]["snippet"]
    assert "dhamma" in html_hits[0]["snippet"]


def test_search_is_diacritic_insensitive_both_directions(tmp_path):
    root = tmp_path / "root"
    root.mkdir()
    (root / "diacritic.txt").write_text("paṭiccasamuppāda appears", encoding="utf-8")
    (root / "ascii.txt").write_text("paticcasamuppada appears", encoding="utf-8")
    index = tmp_path / "folder.sqlite"
    config = FolderCorpusConfig(root=root, index=index)
    refresh(config)

    ascii_query_paths = {hit["relative_path"] for hit in search("paticcasamuppada", config)}
    diacritic_query_paths = {
        hit["relative_path"] for hit in search("paṭiccasamuppāda", config)
    }

    assert ascii_query_paths == {"ascii.txt", "diacritic.txt"}
    assert diacritic_query_paths == {"ascii.txt", "diacritic.txt"}


def test_search_marks_unavailable_source_from_existing_index(tmp_path):
    root = tmp_path / "root"
    root.mkdir()
    (root / "offline.txt").write_text("offline nibbana target", encoding="utf-8")
    index = tmp_path / "folder.sqlite"
    config = FolderCorpusConfig(root=root, index=index)
    refresh(config)
    root.rename(tmp_path / "offline-root")

    hits = search("nibbana", config)

    assert hits
    assert hits[0]["source_available"] is False


def test_search_collapses_exact_content_and_text_duplicates(tmp_path):
    root = tmp_path / "root"
    root.mkdir()
    (root / "a-identical.txt").write_text("identical duplicate text", encoding="utf-8")
    (root / "b-identical.txt").write_text("identical duplicate text", encoding="utf-8")
    (root / "c-normalized.txt").write_text("normalized duplicate text", encoding="utf-8")
    (root / "d-normalized.txt").write_text(
        "normalized duplicate text\n\n",
        encoding="utf-8",
    )
    config = FolderCorpusConfig(root=root, index=tmp_path / "folder.sqlite")
    refresh(config)

    identical_hits = search("identical", config)
    normalized_hits = search("normalized", config)

    assert len(identical_hits) == 1
    assert identical_hits[0]["duplicate_count"] == 2
    assert set(identical_hits[0]["duplicate_paths"]) == {
        "a-identical.txt",
        "b-identical.txt",
    }
    assert len(normalized_hits) == 1
    assert normalized_hits[0]["duplicate_count"] == 2
    assert set(normalized_hits[0]["duplicate_paths"]) == {
        "c-normalized.txt",
        "d-normalized.txt",
    }


def test_search_include_duplicates_returns_all_exact_members(tmp_path):
    root = tmp_path / "root"
    root.mkdir()
    (root / "a.txt").write_text("duplicate visibility target", encoding="utf-8")
    (root / "b.txt").write_text("duplicate visibility target", encoding="utf-8")
    config = FolderCorpusConfig(root=root, index=tmp_path / "folder.sqlite")
    refresh(config)

    collapsed = search("visibility", config)
    expanded = search("visibility", config, include_duplicates=True)

    assert [hit["relative_path"] for hit in collapsed] == ["a.txt"]
    assert {hit["relative_path"] for hit in expanded} == {"a.txt", "b.txt"}
    assert all(hit["duplicate_count"] == 2 for hit in expanded)


def test_search_surfaces_weak_duplicate_hints_without_suppressing(tmp_path):
    root = tmp_path / "root"
    root.mkdir()
    (root / "Maha Book.txt").write_text("target alpha content", encoding="utf-8")
    (root / "Maha Book copy.txt").write_text(
        "target beta content differs",
        encoding="utf-8",
    )
    config = FolderCorpusConfig(root=root, index=tmp_path / "folder.sqlite")
    refresh(config)

    hits = search("target", config)

    assert {hit["relative_path"] for hit in hits} == {
        "Maha Book.txt",
        "Maha Book copy.txt",
    }
    assert all(hit["duplicate_count"] == 1 for hit in hits)
    assert all(hit["possible_duplicate_of"] for hit in hits)
    assert all(
        hint["signals"] == ["normalized_filename"]
        for hit in hits
        for hint in hit["possible_duplicate_of"]
    )


def test_search_does_not_hint_for_size_only_matches(tmp_path):
    root = tmp_path / "root"
    root.mkdir()
    (root / "alpha.txt").write_text("target one", encoding="utf-8")
    (root / "bravo.txt").write_text("target two", encoding="utf-8")
    config = FolderCorpusConfig(root=root, index=tmp_path / "folder.sqlite")
    refresh(config)

    hits = search("target", config)

    assert {hit["relative_path"] for hit in hits} == {"alpha.txt", "bravo.txt"}
    assert all(hit["possible_duplicate_of"] == [] for hit in hits)


def test_junk_filename_hints_are_filtered(tmp_path):
    root = tmp_path / "root"
    (root / "book-a").mkdir(parents=True)
    (root / "book-b").mkdir()
    (root / "book-a" / "metadata.opf").write_text("metadata one", encoding="utf-8")
    (root / "book-b" / "metadata.opf").write_text("metadata two", encoding="utf-8")
    (root / "book-a" / "Picasa.ini").write_text("picasa one", encoding="utf-8")
    (root / "book-b" / "Picasa.ini").write_text("picasa two", encoding="utf-8")
    index = tmp_path / "folder.sqlite"
    config = FolderCorpusConfig(root=root, index=index)
    refresh(config)

    with sqlite3.connect(index) as conn:
        conn.row_factory = sqlite3.Row
        hints = folder_corpus._weak_duplicate_hints(
            conn,
            folder_corpus._exact_duplicate_map(conn),
        )

    assert hints == {}


def test_duplicates_diagnostic_reports_clusters_and_missing_index(tmp_path):
    root = tmp_path / "root"
    root.mkdir()
    (root / "same-a.txt").write_text("same content target", encoding="utf-8")
    (root / "same-b.txt").write_text("same content target", encoding="utf-8")
    (root / "name.txt").write_text("name target one", encoding="utf-8")
    (root / "name copy.txt").write_text("name target two", encoding="utf-8")
    (root / "asset-a.pdf").write_bytes(b"pdf-bytes")
    (root / "asset-b.pdf").write_bytes(b"pdf-bytes")
    config = FolderCorpusConfig(root=root, index=tmp_path / "folder.sqlite")
    refresh(config)

    report = duplicates(config, samples=2)
    missing = duplicates(
        FolderCorpusConfig(root=root, index=tmp_path / "missing.sqlite"),
        samples=2,
    )

    assert report["groups"]["content_hash"]["cluster_count"] >= 2
    assert report["groups"]["text_hash"]["cluster_count"] >= 1
    assert report["groups"]["normalized_filename"]["cluster_count"] >= 1
    assert report["non_text_extracted_duplicate_candidates"]["by_extension"][".pdf"] == 2
    assert missing["status"] == "unavailable"


def test_zip_based_extractors_index_epub_docx_and_odt(tmp_path):
    root = tmp_path / "root"
    root.mkdir()
    with zipfile.ZipFile(root / "book.epub", "w") as archive:
        archive.writestr(
            "OEBPS/chapter.xhtml",
            "<html><body><p>epub dharma target</p></body></html>",
        )
    with zipfile.ZipFile(root / "book.docx", "w") as archive:
        archive.writestr(
            "word/document.xml",
            '<w:document xmlns:w="urn"><w:body><w:p><w:r>'
            "<w:t>docx target text</w:t>"
            "</w:r></w:p></w:body></w:document>",
        )
    with zipfile.ZipFile(root / "book.odt", "w") as archive:
        archive.writestr(
            "content.xml",
            '<office:document xmlns:office="urn" xmlns:text="urn">'
            "<office:body><text:p>odt target text</text:p></office:body>"
            "</office:document>",
        )
    config = FolderCorpusConfig(root=root, index=tmp_path / "folder.sqlite")
    refresh(config)

    assert [hit["relative_path"] for hit in search("epub", config)] == ["book.epub"]
    assert [hit["relative_path"] for hit in search("docx", config)] == ["book.docx"]
    assert [hit["relative_path"] for hit in search("odt", config)] == ["book.odt"]


def test_pdf_extraction_uses_pdftotext_when_available(tmp_path):
    if shutil.which("pdftotext") is None:
        pytest.skip("pdftotext not installed")
    try:
        from weasyprint import HTML
    except ImportError:
        pytest.skip("weasyprint not installed")
    root = tmp_path / "root"
    root.mkdir()
    HTML(string="<p>pdf target text</p>").write_pdf(root / "book.pdf")
    config = FolderCorpusConfig(root=root, index=tmp_path / "folder.sqlite")

    refresh(config)

    assert [hit["relative_path"] for hit in search("pdf", config)] == ["book.pdf"]


def test_doc_extraction_uses_available_optional_tool(tmp_path):
    if not _doc_extractor_available():
        pytest.skip("no .doc extractor installed")
    root = tmp_path / "root"
    root.mkdir()
    (root / "a.doc").write_text("doc duplicate target", encoding="utf-8")
    (root / "b.doc").write_text("\n\ndoc duplicate target\n", encoding="utf-8")
    config = FolderCorpusConfig(root=root, index=tmp_path / "folder.sqlite")

    refresh(config)

    hits = search("doc", config)
    assert len(hits) == 1
    assert hits[0]["duplicate_count"] == 2
    assert set(hits[0]["duplicate_paths"]) == {"a.doc", "b.doc"}


def test_folder_corpus_cli_commands_return_expected_json(tmp_path):
    root = tmp_path / "root"
    root.mkdir()
    (root / "plain.txt").write_text("cli target text", encoding="utf-8")
    (root / "plain copy.txt").write_text("cli target differs", encoding="utf-8")
    index = tmp_path / "folder.sqlite"
    env = os.environ.copy()
    env[ROOT_ENV] = str(root)
    env[INDEX_ENV] = str(index)

    def run_cli(*args: str):
        result = subprocess.run(
            [sys.executable, "tools/research_sources.py", *args],
            cwd=REPO_ROOT,
            env=env,
            capture_output=True,
            text=True,
            check=True,
        )
        return json.loads(result.stdout)

    check_report = run_cli("folder-corpus-check")
    refresh_report = run_cli("folder-corpus-refresh", "--limit", "10")
    hits = run_cli("search-folder-corpus", "cli", "--limit", "5")
    duplicate_report = run_cli("folder-corpus-duplicates", "--samples", "2")

    assert check_report["root_available"] is True
    assert refresh_report["indexed"] == 2
    assert {hit["relative_path"] for hit in hits} == {"plain.txt", "plain copy.txt"}
    assert {"document_id", "snippet", "duplicate_count", "possible_duplicate_of"} <= set(
        hits[0]
    )
    assert duplicate_report["status"] == "ok"
    assert "normalized_filename" in duplicate_report["groups"]
