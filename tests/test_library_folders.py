"""Exercise the library folders index helpers."""

from __future__ import annotations

import bz2
import io
import json
import os
import shutil
import signal
import sqlite3
import subprocess
import sys
import tarfile
import time
import zipfile
from pathlib import Path
from typing import cast

import pytest

from tools import library_folders
from tools.library_folders import (
    EXCLUDE_ENV,
    INDEX_ENV,
    SOURCES_ENV,
    LibraryFoldersConfig,
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
    monkeypatch.setenv(SOURCES_ENV, "")
    monkeypatch.setenv(INDEX_ENV, "")

    config = default_config()

    assert config.roots == []
    assert config.index is None
    assert config.status == "unavailable"
    assert config.missing == (SOURCES_ENV, INDEX_ENV)


def test_default_config_expands_home(monkeypatch):
    monkeypatch.setenv(SOURCES_ENV, "~/library-folders-source")
    monkeypatch.setenv(INDEX_ENV, "~/library-folders-index.sqlite")

    config = default_config()

    assert config.roots == [Path.home() / "library-folders-source"]
    assert config.index == Path.home() / "library-folders-index.sqlite"
    assert config.available


def test_default_config_parses_comma_separated_excludes(monkeypatch):
    monkeypatch.setenv(SOURCES_ENV, "~/library-folders-source")
    monkeypatch.setenv(INDEX_ENV, "~/library-folders-index.sqlite")
    monkeypatch.setenv(EXCLUDE_ENV, "~/library-folders-source/skip , /abs/other ,")

    config = default_config()

    assert config.exclude == (
        Path.home() / "library-folders-source" / "skip",
        Path("/abs/other"),
    )


def test_default_config_without_excludes_is_empty(monkeypatch):
    monkeypatch.setenv(SOURCES_ENV, "~/library-folders-source")
    monkeypatch.setenv(INDEX_ENV, "~/library-folders-index.sqlite")
    monkeypatch.delenv(EXCLUDE_ENV, raising=False)

    assert default_config().exclude == ()


def test_refresh_skips_excluded_subfolders(tmp_path):
    root = tmp_path / "root"
    (root / "keep").mkdir(parents=True)
    (root / "skip" / "nested").mkdir(parents=True)
    (root / "keep" / "a.txt").write_text("keep target", encoding="utf-8")
    (root / "skip" / "b.txt").write_text("skip target", encoding="utf-8")
    (root / "skip" / "nested" / "c.txt").write_text("nested target", encoding="utf-8")
    index = tmp_path / "folder.sqlite"
    config = LibraryFoldersConfig(roots=[root], index=index, exclude=(root / "skip",))

    report = refresh(config)

    assert report["indexed"] == 1
    with sqlite3.connect(index) as conn:
        rel_paths = [row[0] for row in conn.execute("SELECT rel_path FROM documents")]
    assert rel_paths == ["keep/a.txt"]


def test_unbounded_refresh_removes_newly_excluded_rows(tmp_path):
    root = tmp_path / "root"
    (root / "keep").mkdir(parents=True)
    (root / "skip").mkdir()
    (root / "keep" / "a.txt").write_text("keep target", encoding="utf-8")
    (root / "skip" / "b.txt").write_text("skip target", encoding="utf-8")
    index = tmp_path / "folder.sqlite"

    refresh(LibraryFoldersConfig(roots=[root], index=index))
    with sqlite3.connect(index) as conn:
        before = {row[0] for row in conn.execute("SELECT rel_path FROM documents")}

    report = refresh(
        LibraryFoldersConfig(roots=[root], index=index, exclude=(root / "skip",))
    )
    with sqlite3.connect(index) as conn:
        after = [row[0] for row in conn.execute("SELECT rel_path FROM documents")]

    assert before == {"keep/a.txt", "skip/b.txt"}
    assert report["deleted"] == 1
    assert after == ["keep/a.txt"]


def test_check_reports_exclude_paths(tmp_path):
    root = tmp_path / "root"
    root.mkdir()
    config = LibraryFoldersConfig(
        roots=[root],
        index=tmp_path / "folder.sqlite",
        exclude=(root / "skip", Path("/abs/other")),
    )

    report = check(config)

    assert report["exclude_paths"] == [str(root / "skip"), "/abs/other"]


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
    config = LibraryFoldersConfig(roots=[root], index=index)

    report = check(config)

    assert report["status"] == "unavailable"
    assert report["source_roots"][0]["path"] == str(root)
    assert report["index_path"] == str(index)
    assert report["source_roots"][0]["available"] is False
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
                source_root, source_path, rel_path, filename, extension, category_path,
                size, mtime, content_hash, text_hash, extraction_status, indexed_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                str(root),
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

    report = check(LibraryFoldersConfig(roots=[root], index=index))

    assert report["status"] == "ok"
    assert report["source_roots"][0]["available"] is True
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

    report = refresh(LibraryFoldersConfig(roots=[root], index=index))

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
    original_hash_file = library_folders._hash_file

    def fail_hash(path: Path) -> str:
        if path == bad:
            raise OSError(22, "Invalid argument")
        return original_hash_file(path)

    monkeypatch.setattr(library_folders, "_hash_file", fail_hash)

    report = refresh(LibraryFoldersConfig(roots=[root], index=index))

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


def test_refresh_skips_binary_noise_extensions(tmp_path):
    root = tmp_path / "root"
    root.mkdir()
    (root / "keep.txt").write_text("keep target", encoding="utf-8")
    (root / "junk.exe").write_bytes(b"MZ binary")
    (root / "thumb.db").write_bytes(b"db bytes")
    (root / ".DS_Store").write_bytes(b"mac cruft")
    (root / "shortcut.lnk").write_bytes(b"lnk bytes")
    (root / "metadata.opf").write_text("<package/>", encoding="utf-8")
    index = tmp_path / "folder.sqlite"

    report = refresh(LibraryFoldersConfig(roots=[root], index=index))

    assert report["indexed"] == 1
    with sqlite3.connect(index) as conn:
        rel_paths = [row[0] for row in conn.execute("SELECT rel_path FROM documents")]
    assert rel_paths == ["keep.txt"]


def test_doc_extractor_tolerates_non_utf8_output():
    extracted = library_folders._run_doc_extractor(
        [sys.executable, "-c", r"import sys; sys.stdout.buffer.write(b'a\xedb')"],
        "stub",
    )

    assert extracted.status == "ok"
    assert extracted.text.startswith("a")


def test_refresh_continues_when_extraction_raises(tmp_path, monkeypatch):
    root = tmp_path / "root"
    root.mkdir()
    bad = root / "bad.doc"
    bad.write_text("bad doc bytes", encoding="utf-8")
    (root / "good.txt").write_text("good target text", encoding="utf-8")
    index = tmp_path / "folder.sqlite"
    original_extract = library_folders.extract_text

    def fail_extract(path: Path):
        if path == bad:
            raise UnicodeDecodeError(
                "utf-8", b"\xed", 0, 1, "invalid continuation byte"
            )
        return original_extract(path)

    monkeypatch.setattr(library_folders, "extract_text", fail_extract)

    report = refresh(LibraryFoldersConfig(roots=[root], index=index))

    assert report["status"] == "ok"
    assert report["indexed"] == 2
    assert report["error_count"] == 1
    assert report["errors"][0]["relative_path"] == "bad.doc"
    with sqlite3.connect(index) as conn:
        statuses = dict(
            conn.execute("SELECT rel_path, extraction_status FROM documents")
        )
    assert statuses["bad.doc"].startswith("error: extraction failed:")
    assert statuses["good.txt"] == "ok"


def test_incremental_refresh_skips_unchanged_and_deletes_missing(tmp_path):
    root = tmp_path / "root"
    root.mkdir()
    keep = root / "keep.txt"
    remove = root / "remove.txt"
    keep.write_text("keep text", encoding="utf-8")
    remove.write_text("remove text", encoding="utf-8")
    index = tmp_path / "folder.sqlite"
    config = LibraryFoldersConfig(roots=[root], index=index)

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


def test_narrowed_root_refresh_never_deletes_other_roots(tmp_path):
    root_a = tmp_path / "a"
    root_b = tmp_path / "b"
    root_a.mkdir()
    root_b.mkdir()
    (root_a / "a1.txt").write_text("alpha text", encoding="utf-8")
    (root_a / "a2.txt").write_text("alpha two text", encoding="utf-8")
    (root_b / "b1.txt").write_text("beta text", encoding="utf-8")
    index = tmp_path / "folder.sqlite"
    full = LibraryFoldersConfig(roots=[root_a, root_b], index=index)
    refresh(full)

    (root_a / "a2.txt").unlink()
    narrowed = LibraryFoldersConfig(roots=[root_a], index=index)
    result = refresh(narrowed)

    with sqlite3.connect(index) as conn:
        remaining = sorted(
            row[0] for row in conn.execute("SELECT rel_path FROM documents")
        )

    # only the missing file under the *walked* root is deleted; root_b survives
    assert result["deleted"] == 1
    assert remaining == ["a1.txt", "b1.txt"]


def test_retry_failed_reextracts_unchanged_failed_documents(tmp_path, monkeypatch):
    root = tmp_path / "root"
    root.mkdir()
    gap = root / "book.newfmt"
    gap.write_text("recoverable target text", encoding="utf-8")
    (root / "plain.txt").write_text("plain target text", encoding="utf-8")
    index = tmp_path / "folder.sqlite"
    config = LibraryFoldersConfig(roots=[root], index=index)

    refresh(config)
    with sqlite3.connect(index) as conn:
        status = conn.execute(
            "SELECT extraction_status FROM documents WHERE rel_path = 'book.newfmt'"
        ).fetchone()[0]
    assert status.startswith("unsupported:")

    real_extract = library_folders.extract_text

    def now_supported(path: Path):
        if path == gap:
            return library_folders.ExtractedText(text=gap.read_text(), status="ok")
        return real_extract(path)

    monkeypatch.setattr(library_folders, "extract_text", now_supported)

    plain_skip = refresh(config)
    assert plain_skip["skipped"] == 2
    assert not search("recoverable", config)

    retried = refresh(config, retry_failed=True)
    assert retried["skipped"] == 1
    assert retried["written"] == 1
    assert [hit["relative_path"] for hit in search("recoverable", config)] == [
        "book.newfmt"
    ]


def test_refresh_unavailable_root_mutates_nothing(tmp_path):
    root = tmp_path / "root"
    root.mkdir()
    (root / "keep.txt").write_text("keep text", encoding="utf-8")
    index = tmp_path / "folder.sqlite"
    refresh(LibraryFoldersConfig(roots=[root], index=index))

    report = refresh(LibraryFoldersConfig(roots=[tmp_path / "missing"], index=index))

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
    config = LibraryFoldersConfig(roots=[root], index=index)
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
    config = LibraryFoldersConfig(roots=[root], index=index)
    refresh(config)

    ascii_query_paths = {
        hit["relative_path"] for hit in search("paticcasamuppada", config)
    }
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
    config = LibraryFoldersConfig(roots=[root], index=index)
    refresh(config)
    root.rename(tmp_path / "offline-root")

    hits = search("nibbana", config)

    assert hits
    assert hits[0]["source_available"] is False


class _HangingPath:
    """Stands in for a path on a hung network mount."""

    def __init__(self, delay: float) -> None:
        self.delay = delay

    def exists(self) -> bool:
        time.sleep(self.delay)
        return True


def test_exists_probe_returns_none_when_stat_hangs():
    # Regression for #92: a stat against an offline/hung mount blocks for the
    # mount's own timeout, which the FTS query guard cannot bound.
    started = time.monotonic()
    result = library_folders._exists_probe(cast(Path, _HangingPath(30)), timeout=0.2)
    elapsed = time.monotonic() - started

    assert result is None
    assert elapsed < 5


def test_exists_probe_reports_real_answers():
    assert library_folders._exists_probe(Path(__file__), timeout=5) is True
    assert library_folders._exists_probe(Path("/no/such/path"), timeout=5) is False


class _ErroringPath:
    def __init__(self, exc: Exception) -> None:
        self.exc = exc

    def exists(self) -> bool:
        raise self.exc


def test_exists_probe_separates_missing_file_from_unhappy_volume():
    # A missing file is absent; EACCES/EIO on a flaky mount is unknown. The
    # NFS PermissionError several runs hit must not read as "book deleted".
    missing = cast(Path, _ErroringPath(FileNotFoundError()))
    denied = cast(Path, _ErroringPath(PermissionError()))

    assert library_folders._exists_probe(missing, timeout=5) is False
    assert library_folders._exists_probe(denied, timeout=5) is None


def test_per_hit_stat_is_bounded_and_demotes_its_root(tmp_path, monkeypatch):
    # The root probe can pass and the mount drop mid-loop; without a bounded
    # per-hit stat that is O(hits) hangs again. The first timeout demotes the
    # root so the rest of the loop stops statting.
    root = tmp_path / "root"
    root.mkdir()
    for i in range(4):
        (root / f"doc{i}.txt").write_text(f"nibbana target {i}", encoding="utf-8")
    index = tmp_path / "folder.sqlite"
    config = LibraryFoldersConfig(roots=[root], index=index)
    refresh(config)

    calls: list[str] = []
    real_probe = library_folders._exists_probe

    def _probe(path, timeout):
        calls.append(str(path))
        if str(path) == str(root):
            return real_probe(path, timeout)
        return None  # every file stat hangs

    monkeypatch.setattr(library_folders, "_exists_probe", _probe)
    hits = search("nibbana", config)

    assert len(hits) > 1
    assert all(h["source_available"] is None for h in hits)
    # One root probe + one file stat; the rest short-circuit on the demoted root.
    assert len(calls) == 2


def test_search_marks_source_unknown_when_volume_unreachable(tmp_path, monkeypatch):
    # An unreachable volume means the file's presence is *unknown*. Reporting
    # False there would read as "the book is gone" rather than "plug the drive
    # in", which is what five runs' worth of offline-volume confusion was.
    root = tmp_path / "root"
    root.mkdir()
    (root / "a.txt").write_text("nibbana target text", encoding="utf-8")
    index = tmp_path / "folder.sqlite"
    config = LibraryFoldersConfig(roots=[root], index=index)
    refresh(config)

    monkeypatch.setattr(library_folders, "_exists_probe", lambda _p, _t: None)
    hits = search("nibbana", config)

    assert hits
    assert all(h["source_available"] is None for h in hits)


def test_search_probes_each_root_once_not_each_hit(tmp_path, monkeypatch):
    # The hang was O(hits): a broad sweep stats every candidate row in turn.
    # One probe per distinct root bounds it regardless of how wide the sweep is.
    root = tmp_path / "root"
    root.mkdir()
    for i in range(5):
        # Distinct bodies so the duplicate collapser keeps them as separate hits.
        (root / f"doc{i}.txt").write_text(
            f"nibbana target text variant {i}", encoding="utf-8"
        )
    index = tmp_path / "folder.sqlite"
    config = LibraryFoldersConfig(roots=[root], index=index)
    refresh(config)

    probes: list[str] = []

    def _counting_probe(path, _timeout):
        probes.append(str(path))
        return True

    monkeypatch.setattr(library_folders, "_exists_probe", _counting_probe)
    hits = search("nibbana", config)

    assert len(hits) > 1
    # The root is probed once, not once per hit — that is what bounds the cost
    # of an unreachable volume. Healthy per-hit stats still happen (bounded),
    # so the total is 1 + one per returned hit.
    assert probes.count(str(root)) == 1
    assert len(probes) == 1 + len(hits)


def test_search_collapses_exact_content_and_text_duplicates(tmp_path):
    root = tmp_path / "root"
    root.mkdir()
    (root / "a-identical.txt").write_text("identical duplicate text", encoding="utf-8")
    (root / "b-identical.txt").write_text("identical duplicate text", encoding="utf-8")
    (root / "c-normalized.txt").write_text(
        "normalized duplicate text", encoding="utf-8"
    )
    (root / "d-normalized.txt").write_text(
        "normalized duplicate text\n\n",
        encoding="utf-8",
    )
    config = LibraryFoldersConfig(roots=[root], index=tmp_path / "folder.sqlite")
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
    config = LibraryFoldersConfig(roots=[root], index=tmp_path / "folder.sqlite")
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
    config = LibraryFoldersConfig(roots=[root], index=tmp_path / "folder.sqlite")
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
    config = LibraryFoldersConfig(roots=[root], index=tmp_path / "folder.sqlite")
    refresh(config)

    hits = search("target", config)

    assert {hit["relative_path"] for hit in hits} == {"alpha.txt", "bravo.txt"}
    assert all(hit["possible_duplicate_of"] == [] for hit in hits)


def test_search_times_out_on_too_broad_query(tmp_path, monkeypatch):
    root = tmp_path / "root"
    root.mkdir()
    (root / "a.txt").write_text("dhamma target one", encoding="utf-8")
    (root / "b.txt").write_text("dhamma target two", encoding="utf-8")
    config = LibraryFoldersConfig(roots=[root], index=tmp_path / "folder.sqlite")
    refresh(config)
    monkeypatch.setattr(library_folders, "_SEARCH_PROGRESS_STEPS", 1)

    with pytest.raises(library_folders.LibraryFoldersSearchTimeout, match="too broad"):
        search("dhamma", config, timeout=0)


def test_search_with_generous_timeout_still_returns_hits(tmp_path):
    root = tmp_path / "root"
    root.mkdir()
    (root / "a.txt").write_text("dhamma target", encoding="utf-8")
    config = LibraryFoldersConfig(roots=[root], index=tmp_path / "folder.sqlite")
    refresh(config)

    hits = search("dhamma", config, timeout=20.0)

    assert [hit["relative_path"] for hit in hits] == ["a.txt"]


def test_junk_filename_hints_are_filtered(tmp_path):
    root = tmp_path / "root"
    (root / "book-a").mkdir(parents=True)
    (root / "book-b").mkdir()
    (root / "book-a" / "metadata.opf").write_text("metadata one", encoding="utf-8")
    (root / "book-b" / "metadata.opf").write_text("metadata two", encoding="utf-8")
    (root / "book-a" / "Picasa.ini").write_text("picasa one", encoding="utf-8")
    (root / "book-b" / "Picasa.ini").write_text("picasa two", encoding="utf-8")
    index = tmp_path / "folder.sqlite"
    config = LibraryFoldersConfig(roots=[root], index=index)
    refresh(config)

    with sqlite3.connect(index) as conn:
        conn.row_factory = sqlite3.Row
        hints = library_folders._weak_duplicate_hints(
            conn,
            library_folders._exact_duplicate_map(conn),
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
    config = LibraryFoldersConfig(roots=[root], index=tmp_path / "folder.sqlite")
    refresh(config)

    report = duplicates(config, samples=2)
    missing = duplicates(
        LibraryFoldersConfig(roots=[root], index=tmp_path / "missing.sqlite"),
        samples=2,
    )

    assert report["groups"]["content_hash"]["cluster_count"] >= 2
    assert report["groups"]["text_hash"]["cluster_count"] >= 1
    assert report["groups"]["normalized_filename"]["cluster_count"] >= 1
    assert (
        report["non_text_extracted_duplicate_candidates"]["by_extension"][".pdf"] == 2
    )
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
    config = LibraryFoldersConfig(roots=[root], index=tmp_path / "folder.sqlite")
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
    config = LibraryFoldersConfig(roots=[root], index=tmp_path / "folder.sqlite")

    refresh(config)

    assert [hit["relative_path"] for hit in search("pdf", config)] == ["book.pdf"]


def test_doc_extraction_uses_available_optional_tool(tmp_path):
    if not _doc_extractor_available():
        pytest.skip("no .doc extractor installed")
    root = tmp_path / "root"
    root.mkdir()
    (root / "a.doc").write_text("doc duplicate target", encoding="utf-8")
    (root / "b.doc").write_text("\n\ndoc duplicate target\n", encoding="utf-8")
    config = LibraryFoldersConfig(roots=[root], index=tmp_path / "folder.sqlite")

    refresh(config)

    hits = search("doc", config)
    assert len(hits) == 1
    assert hits[0]["duplicate_count"] == 2
    assert set(hits[0]["duplicate_paths"]) == {"a.doc", "b.doc"}


def test_misc_text_and_html_extensions_are_indexed(tmp_path):
    root = tmp_path / "root"
    root.mkdir()
    (root / "data.json").write_text('{"k": "json target value"}', encoding="utf-8")
    (root / "lines.jsonl").write_text('{"k": "jsonl target"}\n', encoding="utf-8")
    (root / "page.shtml").write_text("<p>shtml target text</p>", encoding="utf-8")
    (root / "doc.xml").write_text(
        "<root><node>xml target text</node></root>", encoding="utf-8"
    )
    config = LibraryFoldersConfig(roots=[root], index=tmp_path / "folder.sqlite")
    refresh(config)

    assert [hit["relative_path"] for hit in search("json target value", config)] == [
        "data.json"
    ]
    assert [hit["relative_path"] for hit in search("jsonl", config)] == ["lines.jsonl"]
    shtml_hits = search("shtml", config)
    assert [hit["relative_path"] for hit in shtml_hits] == ["page.shtml"]
    assert "<p>" not in shtml_hits[0]["snippet"]
    assert [hit["relative_path"] for hit in search("xml target", config)] == ["doc.xml"]


def test_refresh_skips_audio_and_image_noise_extensions(tmp_path):
    root = tmp_path / "root"
    root.mkdir()
    (root / "keep.txt").write_text("keep target", encoding="utf-8")
    (root / "talk.mp3").write_bytes(b"ID3 audio bytes")
    (root / "stream.ram").write_bytes(b"rtsp://audio")
    (root / "scan.tif").write_bytes(b"II* image bytes")
    (root / "photo.jpg-old").write_bytes(b"jpeg bytes")
    index = tmp_path / "folder.sqlite"

    report = refresh(LibraryFoldersConfig(roots=[root], index=index))

    assert report["indexed"] == 1
    with sqlite3.connect(index) as conn:
        rel_paths = [row[0] for row in conn.execute("SELECT rel_path FROM documents")]
    assert rel_paths == ["keep.txt"]


def test_mhtml_extraction_strips_html(tmp_path):
    root = tmp_path / "root"
    root.mkdir()
    mhtml = (
        "From: <saved by browser>\n"
        "MIME-Version: 1.0\n"
        'Content-Type: multipart/related; boundary="BOUNDARY"\n'
        "\n"
        "--BOUNDARY\n"
        "Content-Type: text/html; charset=utf-8\n"
        "Content-Transfer-Encoding: quoted-printable\n"
        "\n"
        "<html><body><p>mhtml target text</p></body></html>\n"
        "--BOUNDARY--\n"
    )
    (root / "archive.mht").write_text(mhtml, encoding="utf-8")
    config = LibraryFoldersConfig(roots=[root], index=tmp_path / "folder.sqlite")

    refresh(config)

    hits = search("mhtml target", config)
    assert [hit["relative_path"] for hit in hits] == ["archive.mht"]
    assert "<p>" not in hits[0]["snippet"]


def test_pptx_extraction_reads_slide_xml(tmp_path):
    root = tmp_path / "root"
    root.mkdir()
    with zipfile.ZipFile(root / "deck.pptx", "w") as archive:
        archive.writestr(
            "ppt/slides/slide1.xml",
            '<p:sld xmlns:a="urn"><a:t>pptx target text</a:t></p:sld>',
        )
    config = LibraryFoldersConfig(roots=[root], index=tmp_path / "folder.sqlite")

    refresh(config)

    assert [hit["relative_path"] for hit in search("pptx target", config)] == [
        "deck.pptx"
    ]


def test_ebook_extraction_uses_ebook_convert_when_available(tmp_path):
    if shutil.which("ebook-convert") is None:
        pytest.skip("ebook-convert not installed")
    root = tmp_path / "root"
    root.mkdir()
    rtf = r"{\rtf1\ansi rtf target text\par}"
    (root / "book.rtf").write_text(rtf, encoding="utf-8")
    config = LibraryFoldersConfig(roots=[root], index=tmp_path / "folder.sqlite")

    refresh(config)

    assert [hit["relative_path"] for hit in search("rtf target", config)] == [
        "book.rtf"
    ]


def test_ebook_extraction_reports_missing_tool(monkeypatch, tmp_path):
    monkeypatch.setattr(library_folders.shutil, "which", lambda *_: None)

    extracted = library_folders._extract_ebook(tmp_path / "book.mobi")

    assert extracted.text == ""
    assert extracted.status == "unsupported: ebook-convert not found"


def test_library_folders_cli_commands_return_expected_json(tmp_path):
    root = tmp_path / "root"
    root.mkdir()
    (root / "plain.txt").write_text("cli target text", encoding="utf-8")
    (root / "plain copy.txt").write_text("cli target differs", encoding="utf-8")
    index = tmp_path / "folder.sqlite"
    env = os.environ.copy()
    env[SOURCES_ENV] = str(root)
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

    check_report = run_cli("library-folders-check")
    refresh_report = run_cli("library-folders-refresh", "--limit", "10")
    hits = run_cli("search-library-folders", "cli", "--limit", "5")
    duplicate_report = run_cli("library-folders-duplicates", "--samples", "2")

    assert check_report["source_roots"][0]["available"] is True
    assert refresh_report["indexed"] == 2
    assert {hit["relative_path"] for hit in hits} == {"plain.txt", "plain copy.txt"}
    assert {
        "document_id",
        "snippet",
        "duplicate_count",
        "possible_duplicate_of",
    } <= set(hits[0])
    assert duplicate_report["status"] == "ok"
    assert "normalized_filename" in duplicate_report["groups"]


def _write_zip(path: Path, members: dict[str, bytes | str]) -> None:
    with zipfile.ZipFile(path, "w") as archive:
        for name, payload in members.items():
            archive.writestr(name, payload)


def test_zip_extractor_indexes_text_member(tmp_path):
    root = tmp_path / "root"
    root.mkdir()
    _write_zip(root / "bundle.zip", {"notes.txt": "ziptext target word"})
    config = LibraryFoldersConfig(roots=[root], index=tmp_path / "folder.sqlite")

    refresh(config)

    assert [hit["relative_path"] for hit in search("ziptext", config)] == ["bundle.zip"]


def test_zip_extractor_filters_noise_members(tmp_path):
    root = tmp_path / "root"
    root.mkdir()
    _write_zip(
        root / "bundle.zip",
        {
            "page.html": "<html><body>htmldriven target</body></html>",
            "audio.mp3": "mp3onlyword should be ignored",
        },
    )
    config = LibraryFoldersConfig(roots=[root], index=tmp_path / "folder.sqlite")

    refresh(config)

    assert [hit["relative_path"] for hit in search("htmldriven", config)] == [
        "bundle.zip"
    ]
    assert search("mp3onlyword", config) == []


def test_zip_extractor_handles_bad_zip(tmp_path):
    bad = tmp_path / "broken.zip"
    bad.write_bytes(b"this is not a zip archive")

    extracted = library_folders.extract_text(bad)

    assert extracted.status == "error: bad zip"
    assert extracted.text == ""


def test_zip_extractor_enforces_member_count_cap(tmp_path, monkeypatch):
    monkeypatch.setattr(library_folders, "ARCHIVE_MAX_MEMBERS", 2)
    path = tmp_path / "many.zip"
    _write_zip(path, {f"file{i}.txt": f"word{i}" for i in range(3)})

    extracted = library_folders.extract_text(path)

    assert extracted.status == "error: archive too large"


def test_zip_extractor_enforces_size_cap(tmp_path, monkeypatch):
    monkeypatch.setattr(library_folders, "ARCHIVE_MAX_UNCOMPRESSED", 10)
    path = tmp_path / "big.zip"
    _write_zip(path, {"big.txt": "x" * 50})

    extracted = library_folders.extract_text(path)

    assert extracted.status == "error: archive too large"


def test_zip_extractor_enforces_wallclock_cap(tmp_path, monkeypatch):
    ticks = iter([0.0, 1000.0, 1000.0, 1000.0])
    monkeypatch.setattr(library_folders.time, "monotonic", lambda: next(ticks))
    path = tmp_path / "slow.zip"
    _write_zip(path, {"a.txt": "alpha", "b.txt": "beta"})

    extracted = library_folders.extract_text(path)

    assert extracted.status == "error: archive timed out"


def test_zip_extractor_skips_encrypted_members(tmp_path):
    if shutil.which("7z") is None:
        pytest.skip("7z not installed")
    src = tmp_path / "secret.txt"
    src.write_text("encrypted target", encoding="utf-8")
    path = tmp_path / "secret.zip"
    subprocess.run(
        ["7z", "a", "-tzip", "-psecret", "-mem=AES256", str(path), str(src)],
        check=True,
        capture_output=True,
    )

    extracted = library_folders.extract_text(path)

    assert extracted.status == "empty"
    assert extracted.text == ""


def test_zip_extractor_routes_pdf_member(tmp_path, monkeypatch):
    monkeypatch.setattr(
        library_folders,
        "_extract_pdf",
        lambda _path: library_folders.ExtractedText(
            text="pdfmember target", status="ok"
        ),
    )
    path = tmp_path / "withpdf.zip"
    _write_zip(path, {"doc.pdf": b"%PDF-1.4 fake bytes"})

    extracted = library_folders.extract_text(path)

    assert "pdfmember target" in extracted.text
    assert extracted.status == "ok"


def test_zip_extractor_does_not_recurse_into_nested_zips(tmp_path):
    inner = io.BytesIO()
    with zipfile.ZipFile(inner, "w") as nested:
        nested.writestr("hidden.txt", "nested target")
    path = tmp_path / "outer.zip"
    _write_zip(path, {"inner.zip": inner.getvalue()})

    extracted = library_folders.extract_text(path)

    assert extracted.status == "empty"
    assert "nested target" not in extracted.text


def test_zip_extractor_concatenates_multiple_text_members(tmp_path):
    path = tmp_path / "two.zip"
    _write_zip(
        path,
        {
            "one.html": "<html><body>firstword here</body></html>",
            "two.html": "<html><body>secondword here</body></html>",
        },
    )

    extracted = library_folders.extract_text(path)

    assert "firstword" in extracted.text
    assert "secondword" in extracted.text


def test_bz2_extractor_handles_inner_tar(tmp_path):
    buf = io.BytesIO()
    with tarfile.open(fileobj=buf, mode="w") as tar:
        payload = b"<html><body>tarbz target</body></html>"
        info = tarfile.TarInfo("doc.html")
        info.size = len(payload)
        tar.addfile(info, io.BytesIO(payload))
    path = tmp_path / "docs.bz2"
    path.write_bytes(bz2.compress(buf.getvalue()))

    extracted = library_folders.extract_text(path)

    assert extracted.status == "ok"
    assert "tarbz target" in extracted.text


def test_bz2_extractor_handles_single_file_fallback(tmp_path):
    path = tmp_path / "note.txt.bz2"
    path.write_bytes(bz2.compress(b"plainbz target word"))

    extracted = library_folders.extract_text(path)

    assert extracted.status == "ok"
    assert "plainbz target" in extracted.text


def test_7z_extractor_handles_inner_text(tmp_path):
    if shutil.which("7z") is None:
        pytest.skip("7z not installed")
    src = tmp_path / "payload.txt"
    src.write_text("sevenzip target word", encoding="utf-8")
    path = tmp_path / "bundle.7z"
    subprocess.run(
        ["7z", "a", str(path), str(src)],
        check=True,
        capture_output=True,
    )

    extracted = library_folders.extract_text(path)

    assert extracted.status == "ok"
    assert "sevenzip target" in extracted.text


def _empty_pdftotext(monkeypatch):
    monkeypatch.setattr(
        library_folders,
        "_extract_pdf_pdftotext",
        lambda _path: library_folders.ExtractedText(text="", status="empty"),
    )


def _stub_ocrmypdf(monkeypatch, tmp_path, body: str) -> dict[str, object]:
    """Point the ocrmypdf seam at a real Python child running `body`.

    A real subprocess, not a fake: the original deadlock passed 452 tests
    because a fake close() returned immediately. `body` receives the source
    PDF, the output PDF and the sidecar as argv[1:4].
    """
    stub = tmp_path / "stub_ocrmypdf.py"
    stub.write_text("import sys\n" + body, encoding="utf-8")
    seen: dict[str, object] = {}

    def command(source, out_pdf, sidecar):
        seen["source"] = Path(source)
        seen["sidecar"] = Path(sidecar)
        return [sys.executable, str(stub), str(source), str(out_pdf), str(sidecar)]

    # sys.executable is absolute, so the shutil.which availability probe finds
    # it — the seam still goes through the real probe rather than skipping it.
    monkeypatch.setattr(library_folders, "OCRMYPDF_BIN", sys.executable)
    monkeypatch.setattr(library_folders, "_ocrmypdf_command", command)
    return seen


_WRITE_SIDECAR = (
    "text = sys.argv[3]\nopen(text, 'w', encoding='utf-8').write(TEXT)\nsys.exit(RC)\n"
)


def _sidecar_stub(text: str, rc: int = 0, stderr: str = "") -> str:
    return (
        f"TEXT = {text!r}\nRC = {rc}\nsys.stderr.write({stderr!r})\n" + _WRITE_SIDECAR
    )


def test_ocr_fallback_returns_the_sidecar_text_as_ok(tmp_path, monkeypatch):
    seen = _stub_ocrmypdf(
        monkeypatch, tmp_path, _sidecar_stub("a real page of scanned text " * 20)
    )
    monkeypatch.setattr(library_folders, "_pdf_page_count", lambda _path: 1)
    _empty_pdftotext(monkeypatch)
    scan = tmp_path / "scan.pdf"
    scan.write_bytes(b"%PDF scanned")

    extracted = library_folders._extract_pdf(scan)

    assert extracted.status == "ok"
    assert extracted.text.startswith("a real page of scanned text")
    assert seen["source"] == scan


def test_ocr_fallback_flags_implausibly_short_output(tmp_path, monkeypatch):
    """rc=0 with almost no text is a measured tesseract failure mode.

    2026-09-03: an 85-page book returned 84 characters with a zero return
    code, on a book the previous engine read at 211,181 characters. A return
    code cannot catch it, so the character count per page is the only signal.
    """
    _stub_ocrmypdf(monkeypatch, tmp_path, _sidecar_stub("x" * 84))
    monkeypatch.setattr(library_folders, "_pdf_page_count", lambda _path: 85)
    _empty_pdftotext(monkeypatch)

    extracted = library_folders._extract_pdf(tmp_path / "scan.pdf")

    assert (
        extracted.status
        == "error: pdf ocr output implausibly short (84 chars from 85 pages)"
    )
    assert library_folders.extraction_succeeded(extracted.status) is False
    # Kept, so a human can see what came back, but never recorded as success.
    assert extracted.text == "x" * 84


def test_ocr_fallback_accepts_a_plausible_page_of_text(tmp_path, monkeypatch):
    """The short-output guard must not reject a genuinely thin but real book."""
    _stub_ocrmypdf(monkeypatch, tmp_path, _sidecar_stub("y" * 1701))
    monkeypatch.setattr(library_folders, "_pdf_page_count", lambda _path: 85)
    _empty_pdftotext(monkeypatch)

    assert library_folders._extract_pdf(tmp_path / "scan.pdf").status == "ok"


def test_ocr_fallback_reports_a_nonzero_return_code(tmp_path, monkeypatch):
    _stub_ocrmypdf(
        monkeypatch,
        tmp_path,
        _sidecar_stub("", rc=8, stderr="EncryptedPdfError: refusing\n"),
    )
    _empty_pdftotext(monkeypatch)

    extracted = library_folders._extract_pdf(tmp_path / "scan.pdf")

    assert extracted.status == "error: pdf ocr: EncryptedPdfError: refusing"
    assert extracted.text == ""


def test_ocr_fallback_names_an_empty_ocr_result(tmp_path, monkeypatch):
    """A scan that OCR'd to nothing must not read as a plain "empty" row.

    skill/vicaya tells the research agent never to hand-run pdftotext on a
    status mentioning "ocr". A bare "empty" loses that marker and sends the
    agent to the exact dead end — pdftotext returning nothing is why OCR ran.
    """
    _stub_ocrmypdf(monkeypatch, tmp_path, _sidecar_stub("   \n  "))
    _empty_pdftotext(monkeypatch)

    extracted = library_folders._extract_pdf(tmp_path / "scan.pdf")

    assert extracted.status == "empty: pdf ocr produced no text"
    assert "ocr" in extracted.status
    assert library_folders.extraction_succeeded(extracted.status) is False
    assert extracted.text == ""


def test_ocr_fallback_survives_a_missing_sidecar(tmp_path, monkeypatch):
    """ocrmypdf writing no sidecar at all must not raise."""
    _stub_ocrmypdf(monkeypatch, tmp_path, "sys.exit(0)\n")
    _empty_pdftotext(monkeypatch)

    extracted = library_folders._extract_pdf(tmp_path / "scan.pdf")

    assert extracted.status == "empty: pdf ocr produced no text"


def test_real_hanging_ocrmypdf_is_killed_within_the_timeout(tmp_path, monkeypatch):
    """Spawn a genuinely hung child, not a fake, and require prompt recovery.

    Carried forward from the deleted worker's regression test. The bespoke
    worker existed to contain an unkillable wait, so replacing it with an
    unbounded subprocess call would reintroduce exactly that shape. ocrmypdf
    writes its sidecar only at the end, so unlike the old worker there is no
    partial text to keep — the assertion is a bounded kill and a retryable
    status, not retained pages.
    """
    _stub_ocrmypdf(monkeypatch, tmp_path, "import time\ntime.sleep(600)\n")
    monkeypatch.setattr(library_folders, "OCR_SUBPROCESS_TIMEOUT", 3)
    _empty_pdftotext(monkeypatch)

    started = time.monotonic()
    extracted = library_folders._extract_pdf(tmp_path / "scan.pdf")
    elapsed = time.monotonic() - started

    assert extracted.status == "error: pdf ocr timed out after 3s"
    assert extracted.text == ""
    assert library_folders.extraction_succeeded(extracted.status) is False
    # The whole point: bounded. Unbounded, this never returns at all.
    assert elapsed < 30, f"took {elapsed:.1f}s — the timeout path is not bounded"


def test_a_timeout_kills_the_whole_child_pool_not_just_the_parent(
    tmp_path, monkeypatch
):
    """ocrmypdf drives a pool of tesseract workers.

    Killing only the parent orphans that pool, which then burns CPU for the
    rest of a multi-day refresh. The stub spawns a grandchild that would
    outlive its parent, and the test requires it dead.
    """
    marker = tmp_path / "grandchild.pid"
    _stub_ocrmypdf(
        monkeypatch,
        tmp_path,
        "import os, subprocess, time\n"
        "kid = subprocess.Popen([sys.executable, '-c', 'import time; time.sleep(600)'])\n"
        f"open({str(marker)!r}, 'w').write(str(kid.pid))\n"
        "time.sleep(600)\n",
    )
    monkeypatch.setattr(library_folders, "OCR_SUBPROCESS_TIMEOUT", 4)
    _empty_pdftotext(monkeypatch)

    extracted = library_folders._extract_pdf(tmp_path / "scan.pdf")

    assert extracted.status == "error: pdf ocr timed out after 4s"
    grandchild = int(marker.read_text(encoding="utf-8"))
    deadline = time.monotonic() + 10
    while time.monotonic() < deadline:
        try:
            os.kill(grandchild, 0)
        except OSError:
            break  # gone, as required
        time.sleep(0.1)
    else:
        os.kill(grandchild, 9)  # do not leak it out of the test run
        pytest.fail(f"grandchild {grandchild} survived the timeout kill")


def test_pdf_ocr_fallback_keeps_original_status_without_the_ocrmypdf_binary(
    tmp_path, monkeypatch
):
    """A missing apt package must not write an OCR error over every scan.

    ocrmypdf is a system package that `uv sync` will not install, so an absent
    binary is the normal state on a fresh machine. Returning None is what makes
    _extract_pdf keep pdftotext's own status.
    """
    monkeypatch.setattr(library_folders, "OCRMYPDF_BIN", "vicaya-no-such-binary")

    def boom(*_args, **_kwargs):
        raise AssertionError("OCR must not run without the binary")

    monkeypatch.setattr(library_folders, "_ocrmypdf_command", boom)
    _empty_pdftotext(monkeypatch)

    extracted = library_folders._extract_pdf(tmp_path / "scan.pdf")

    assert extracted.status == "empty"
    assert extracted.text == ""


def test_pdf_ocr_fallback_kill_switch(tmp_path, monkeypatch):
    def boom(*_args, **_kwargs):
        raise AssertionError("OCR fallback must not run when disabled")

    monkeypatch.setattr(library_folders, "_ocrmypdf_command", boom)
    monkeypatch.setenv(library_folders.OCR_KILL_SWITCH_ENV, "0")
    _empty_pdftotext(monkeypatch)

    extracted = library_folders._extract_pdf(tmp_path / "scan.pdf")

    assert extracted.status == "empty"
    assert extracted.text == ""


def test_pdf_ocr_fallback_not_tried_when_pdftotext_succeeds(tmp_path, monkeypatch):
    def boom(_path):
        raise AssertionError("OCR must only run as a fallback")

    monkeypatch.setattr(
        library_folders,
        "_extract_pdf_pdftotext",
        lambda _path: library_folders.ExtractedText(text="real layer", status="ok"),
    )
    monkeypatch.setattr(library_folders, "_extract_pdf_ocr_fallback", boom)

    extracted = library_folders._extract_pdf(tmp_path / "book.pdf")

    assert extracted.status == "ok"
    assert extracted.text == "real layer"


@pytest.mark.parametrize("original", ["empty", "error: pdftotext timed out"])
def test_pdf_ocr_fallback_escalates_from_every_non_ok_status(
    tmp_path, monkeypatch, original
):
    _stub_ocrmypdf(monkeypatch, tmp_path, _sidecar_stub("ocr text " * 30))
    monkeypatch.setattr(library_folders, "_pdf_page_count", lambda _path: 1)
    monkeypatch.setattr(
        library_folders,
        "_extract_pdf_pdftotext",
        lambda _path: library_folders.ExtractedText(text="", status=original),
    )

    extracted = library_folders._extract_pdf(tmp_path / "scan.pdf")

    assert extracted.status == "ok"
    assert extracted.text.startswith("ocr text")


def test_every_ocr_failure_status_mentions_ocr():
    """skill/vicaya branches on the substring, so losing it misroutes the agent.

    An OCR status that does not say "ocr" sends the research agent down the
    pdftotext dead end those SKILL.md passages exist to prevent.
    """
    for status in (
        f"error: pdf ocr timed out after {library_folders.OCR_SUBPROCESS_TIMEOUT}s",
        "error: pdf ocr subprocess: [Errno 2] No such file",
        "error: pdf ocr: EncryptedPdfError",
        "error: pdf ocr output implausibly short (84 chars from 85 pages)",
        "empty: pdf ocr produced no text",
    ):
        assert "ocr" in status
        assert library_folders.extraction_succeeded(status) is False


def _encrypted_pdf(path: Path) -> None:
    import pikepdf

    pdf = pikepdf.new()
    pdf.add_blank_page(page_size=(200, 200))
    pdf.save(path, encryption=pikepdf.Encryption(owner="owner", user=""))


def test_decrypted_pdf_strips_owner_only_encryption(tmp_path):
    """43 of 1,735 books carry an empty-user-password restriction.

    ocrmypdf refuses them outright with rc=8, so they are pre-decrypted. No
    credentials are involved: the user password is empty.
    """
    import pikepdf

    source = tmp_path / "locked.pdf"
    _encrypted_pdf(source)
    with pikepdf.open(source) as check_pdf:
        assert check_pdf.is_encrypted is True

    workdir = tmp_path / "work"
    workdir.mkdir()
    plain = library_folders._decrypted_pdf(source, workdir)

    assert plain != source
    with pikepdf.open(plain) as opened:
        assert opened.is_encrypted is False


def test_decrypted_pdf_passes_an_unencrypted_file_straight_through(tmp_path):
    import pikepdf

    source = tmp_path / "plain.pdf"
    pdf = pikepdf.new()
    pdf.add_blank_page(page_size=(200, 200))
    pdf.save(source)
    workdir = tmp_path / "work"
    workdir.mkdir()

    assert library_folders._decrypted_pdf(source, workdir) == source


def test_decrypted_pdf_leaves_an_unreadable_file_to_ocrmypdf(tmp_path):
    """A file pikepdf cannot parse is ocrmypdf's problem to report, not ours."""
    source = tmp_path / "broken.pdf"
    source.write_bytes(b"not a pdf at all")
    workdir = tmp_path / "work"
    workdir.mkdir()

    assert library_folders._decrypted_pdf(source, workdir) == source


def test_pdf_page_count_reads_pdfinfo(tmp_path):
    import pikepdf

    source = tmp_path / "three.pdf"
    pdf = pikepdf.new()
    for _ in range(3):
        pdf.add_blank_page(page_size=(200, 200))
    pdf.save(source)

    if shutil.which("pdfinfo") is None:
        pytest.skip("pdfinfo not installed")
    assert library_folders._pdf_page_count(source) == 3


def test_pdf_page_count_is_zero_when_it_cannot_be_determined(tmp_path):
    """A zero page count disables the short-output guard rather than guessing."""
    source = tmp_path / "broken.pdf"
    source.write_bytes(b"not a pdf at all")

    assert library_folders._pdf_page_count(source) == 0


def test_retry_failed_leaves_ok_with_a_note_documents_alone(tmp_path, monkeypatch):
    root = tmp_path / "root"
    root.mkdir()
    scan = root / "scan.pdf"
    scan.write_bytes(b"%PDF scanned")
    index = tmp_path / "folder.sqlite"
    config = LibraryFoldersConfig(roots=[root], index=index)
    noted = "ok: ocr with a note"

    monkeypatch.setattr(
        library_folders,
        "extract_text",
        lambda _path: library_folders.ExtractedText(text="the pages", status=noted),
    )
    refresh(config)
    with sqlite3.connect(index) as conn:
        assert (
            conn.execute(
                "SELECT extraction_status FROM documents WHERE rel_path = 'scan.pdf'"
            ).fetchone()[0]
            == noted
        )

    def must_not_reextract(_path):
        raise AssertionError("an ok-with-a-note row must not be re-OCR'd on retry")

    monkeypatch.setattr(library_folders, "extract_text", must_not_reextract)

    retried = refresh(config, retry_failed=True)

    assert retried["skipped"] == 1
    assert retried["written"] == 0


def test_index_uses_write_ahead_logging(tmp_path):
    root = tmp_path / "root"
    root.mkdir()
    (root / "a.txt").write_text("wal target text", encoding="utf-8")
    index = tmp_path / "folder.sqlite"

    refresh(LibraryFoldersConfig(roots=[root], index=index))

    with sqlite3.connect(index) as conn:
        assert conn.execute("PRAGMA journal_mode").fetchone()[0].lower() == "wal"


def test_interrupted_refresh_keeps_the_files_it_finished(tmp_path, monkeypatch):
    root = tmp_path / "root"
    root.mkdir()
    for name in ("a.txt", "b.txt", "c.txt", "d.txt"):
        (root / name).write_text(f"{name} durable target", encoding="utf-8")
    index = tmp_path / "folder.sqlite"
    config = LibraryFoldersConfig(roots=[root], index=index)

    monkeypatch.setattr(library_folders, "REFRESH_COMMIT_SECONDS", 0.0)
    real_extract = library_folders.extract_text
    seen: list[str] = []

    def die_part_way(path: Path):
        if len(seen) >= 2:
            raise KeyboardInterrupt("refresh killed part-way")
        seen.append(path.name)
        return real_extract(path)

    monkeypatch.setattr(library_folders, "extract_text", die_part_way)

    with pytest.raises(KeyboardInterrupt):
        refresh(config)

    with sqlite3.connect(index) as conn:
        kept = {row[0] for row in conn.execute("SELECT rel_path FROM documents")}
    assert kept == set(seen)

    monkeypatch.setattr(library_folders, "extract_text", real_extract)
    report = refresh(config)

    assert report["skipped"] == 2
    assert report["written"] == 2


def test_search_works_while_a_refresh_holds_an_open_write(tmp_path):
    root = tmp_path / "root"
    root.mkdir()
    (root / "a.txt").write_text("concurrent target text", encoding="utf-8")
    index = tmp_path / "folder.sqlite"
    config = LibraryFoldersConfig(roots=[root], index=index)
    refresh(config)

    writer = sqlite3.connect(index)
    try:
        initialize_schema(writer)
        writer.execute(
            "INSERT INTO index_meta(key, value) VALUES ('mid_refresh', '1')"
        )  # open write transaction, deliberately uncommitted

        hits = search("concurrent", config)
    finally:
        writer.rollback()
        writer.close()

    assert [hit["relative_path"] for hit in hits] == ["a.txt"]


def test_schema_version_change_drops_and_rebuilds_the_index(tmp_path, monkeypatch):
    root = tmp_path / "root"
    root.mkdir()
    (root / "a.txt").write_text("versioned target text", encoding="utf-8")
    index = tmp_path / "folder.sqlite"
    config = LibraryFoldersConfig(roots=[root], index=index)

    refresh(config)
    with sqlite3.connect(index) as conn:
        assert (
            conn.execute(
                "SELECT value FROM index_meta WHERE key = 'schema_version'"
            ).fetchone()[0]
            == library_folders.SCHEMA_VERSION
        )
    assert refresh(config)["skipped"] == 1

    # A new extractor ships as a schema bump: the old rows are dropped so
    # every file is re-extracted once rather than left as a silent mixture.
    monkeypatch.setattr(library_folders, "SCHEMA_VERSION", "next")
    report = refresh(config)

    assert report["skipped"] == 0
    assert report["written"] == 1
    with sqlite3.connect(index) as conn:
        assert (
            conn.execute(
                "SELECT value FROM index_meta WHERE key = 'schema_version'"
            ).fetchone()[0]
            == "next"
        )


def test_retry_failed_reextracts_a_timed_out_ocr_document(tmp_path, monkeypatch):
    """A timeout may be intermittent, so a timed-out row must stay retryable.

    Contrast test_retry_failed_leaves_ok_with_a_note_documents_alone: an
    "ok: ..." row is a success with a note and re-running it would redo
    identical work, but a book that hit the whole-book bound is worth another
    attempt — both books measured as stalling on 2026-09-03 completed on the
    next attempt.
    """
    root = tmp_path / "root"
    root.mkdir()
    (root / "scan.pdf").write_bytes(b"%PDF scanned")
    index = tmp_path / "folder.sqlite"
    config = LibraryFoldersConfig(roots=[root], index=index)

    monkeypatch.setattr(
        library_folders,
        "extract_text",
        lambda _path: library_folders.ExtractedText(
            text="", status="error: pdf ocr timed out after 1800s"
        ),
    )
    refresh(config)
    assert refresh(config)["skipped"] == 1  # a plain refresh still skips it

    monkeypatch.setattr(
        library_folders,
        "extract_text",
        lambda _path: library_folders.ExtractedText(text="all 150 pages", status="ok"),
    )
    retried = refresh(config, retry_failed=True)

    assert retried["written"] == 1
    assert retried["skipped"] == 0
    with sqlite3.connect(index) as conn:
        assert (
            conn.execute(
                "SELECT extraction_status FROM documents WHERE rel_path = 'scan.pdf'"
            ).fetchone()[0]
            == "ok"
        )


@pytest.mark.parametrize(
    ("status", "done"),
    [
        ("ok", True),
        ("ok: ocr with a note", True),
        ("empty", False),
        ("unsupported: pdftotext not found", False),
        ("error: pdf ocr timed out after 1800s", False),
        ("error: pdf ocr output implausibly short (84 chars from 85 pages)", False),
        # Retired with the bespoke worker: ocrmypdf writes its sidecar once at
        # the end, so a killed run leaves no text for "partial:" to describe.
        # The 25 rows already carrying it are re-extracted like any non-ok row.
        ("partial: ocr stalled at page 20 of 150", False),
    ],
)
def test_extraction_succeeded_contract(status, done):
    assert library_folders.extraction_succeeded(status) is done


def _spawn_ocr_child_then_signal(tmp_path: Path, sig: int) -> tuple[int, int]:
    """Run a real OCR call in a child process, signal it, return (rc, grandchild).

    A real process tree and a real signal. The OCR child is put in its own
    session so a timeout can kill its whole tesseract pool, which also means
    the terminal's signal never reaches it — so nothing but an actual signal
    delivered to an actual refresh proves the cleanup runs.
    """
    marker = tmp_path / "ocr_pid"
    stub = tmp_path / "slow_ocrmypdf.py"
    stub.write_text(
        "import os, sys, time\n"
        f"open({str(marker)!r}, 'w').write(str(os.getpid()))\n"
        "time.sleep(600)\n",
        encoding="utf-8",
    )
    driver = tmp_path / "driver.py"
    driver.write_text(
        "import sys\n"
        f"sys.path.insert(0, {str(REPO_ROOT)!r})\n"
        "from pathlib import Path\n"
        "from tools import library_folders as lf\n"
        f"lf.OCRMYPDF_BIN = sys.executable\n"
        f"lf._ocrmypdf_command = lambda src, out, sc: [sys.executable, {str(stub)!r}]\n"
        "lf._extract_pdf_pdftotext = lambda p: lf.ExtractedText(text='', status='empty')\n"
        f"lf._extract_pdf(Path({str(tmp_path / 'scan.pdf')!r}))\n",
        encoding="utf-8",
    )
    proc = subprocess.Popen([sys.executable, str(driver)])
    deadline = time.monotonic() + 30
    while time.monotonic() < deadline and not marker.exists():
        time.sleep(0.1)
    assert marker.exists(), "the OCR child never started"
    grandchild = int(marker.read_text(encoding="utf-8"))
    os.kill(proc.pid, sig)
    proc.wait(timeout=30)
    return proc.returncode, grandchild


def _wait_until_dead(pid: int, seconds: float) -> bool:
    deadline = time.monotonic() + seconds
    while time.monotonic() < deadline:
        try:
            os.kill(pid, 0)
        except OSError:
            return True
        time.sleep(0.1)
    return False


@pytest.mark.parametrize("sig", [signal.SIGINT, signal.SIGTERM])
def test_stopping_a_refresh_kills_the_ocr_child(tmp_path, sig):
    """Ctrl-C and `kill` must both take the OCR engine down with the refresh.

    Regression for 2026-09-04: `start_new_session=True` is required so a
    timeout can kill ocrmypdf's whole tesseract pool, but it also detaches the
    child from the terminal's process group. Without explicit cleanup, stopping
    an overnight refresh left ocrmypdf running at OCR_JOBS cores on a book
    nobody was waiting for — observed twice, once alongside a restarted run on
    the same book, which saturated the machine.
    """
    _, grandchild = _spawn_ocr_child_then_signal(tmp_path, sig)

    if not _wait_until_dead(grandchild, 15):
        os.kill(grandchild, signal.SIGKILL)  # do not leak it out of the test run
        pytest.fail(f"ocr child {grandchild} survived {signal.Signals(sig).name}")
