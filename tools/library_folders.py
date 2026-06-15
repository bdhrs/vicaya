"""Manage a local SQLite index for one or more library folders."""

from __future__ import annotations

import bz2
import hashlib
import io
import os
import re
import shutil
import sqlite3
import subprocess
import sys
import tarfile
import tempfile
import time
import unicodedata
import zipfile
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Callable
from xml.etree import ElementTree

from tqdm import tqdm

_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from tools._common import (  # noqa: E402
    REPO_ROOT as _REPO_ROOT,
    env_path as _env_path,
    load_dotenv as _load_dotenv,
    strip_xml as _strip_xml,
)

SOURCES_ENV = "VICAYA_LIBRARY_FOLDERS"
INDEX_ENV = "VICAYA_LIBRARY_FOLDERS_INDEX"
EXCLUDE_ENV = "VICAYA_LIBRARY_FOLDERS_EXCLUDE"
SCHEMA_VERSION = "2"
TEXT_EXTENSIONS = {".txt", ".md", ".json", ".jsonl", ".py"}
HTML_EXTENSIONS = {".htm", ".html", ".shtml", ".xhtml", ".xht", ".xml"}
EPUB_EXTENSIONS = {".epub"}
MHTML_EXTENSIONS = {".mht", ".mhtml"}
EBOOK_CONVERT_EXTENSIONS = {
    ".mobi",
    ".azw3",
    ".azw",
    ".prc",
    ".lit",
    ".pdb",
    ".chm",
    ".rtf",
}
FILENAME_HINT_STOP_NAMES = {"metadata", "picasa", "index", "contents", "cover", "title"}
FILENAME_HINT_SKIP_EXTENSIONS = {".ini", ".opf"}

NOISE_EXTENSIONS = {
    ".aac",
    ".apnx",
    ".avi",
    ".bmp",
    ".class",
    ".css",
    ".dat",
    ".db",
    ".dll",
    ".ds_store",
    ".exe",
    ".flac",
    ".gif",
    ".ico",
    ".idx",
    ".jpeg",
    ".jpg",
    ".jpg-old",
    ".js",
    ".lnk",
    ".m4a",
    ".map",
    ".mkv",
    ".mov",
    ".mp3",
    ".mp4",
    ".ogg",
    ".opf",
    ".png",
    ".pyc",
    ".ram",
    ".svg",
    ".tif",
    ".tiff",
    ".ttf",
    ".wav",
    ".webp",
    ".wma",
    ".wmv",
    ".woff",
    ".woff2",
}

ARCHIVE_EXTENSIONS = {".zip", ".bz2", ".7z"}
ARCHIVE_MAX_MEMBERS = 5000
ARCHIVE_MAX_UNCOMPRESSED = 2 * 1024**3
ARCHIVE_MAX_WALLCLOCK = 300.0


_load_dotenv()


@dataclass(frozen=True)
class LibraryFoldersConfig:
    roots: list[Path]
    index: Path | None
    missing: tuple[str, ...] = ()
    exclude: tuple[Path, ...] = ()

    @property
    def available(self) -> bool:
        return not self.missing

    @property
    def status(self) -> str:
        return "configured" if self.available else "unavailable"


@dataclass(frozen=True)
class ExtractedText:
    text: str
    status: str


def _env_sources(key: str) -> list[Path]:
    value = os.environ.get(key)
    if not value:
        return []
    return [
        Path(os.path.expanduser(entry.strip()))
        for entry in value.split("|")
        if entry.strip()
    ]


def _env_excludes(key: str) -> tuple[Path, ...]:
    value = os.environ.get(key)
    if not value:
        return ()
    return tuple(
        Path(os.path.expanduser(entry.strip()))
        for entry in value.split(",")
        if entry.strip()
    )


def default_config() -> LibraryFoldersConfig:
    roots = _env_sources(SOURCES_ENV)
    index = _env_path(INDEX_ENV)
    missing = tuple(
        key
        for key, ok in ((SOURCES_ENV, bool(roots)), (INDEX_ENV, index is not None))
        if not ok
    )
    return LibraryFoldersConfig(
        roots=roots,
        index=index,
        missing=missing,
        exclude=_env_excludes(EXCLUDE_ENV),
    )


def _strip_diacritics(text: str) -> str:
    return "".join(
        c for c in unicodedata.normalize("NFD", text) if unicodedata.category(c) != "Mn"
    )


def _utc_now() -> str:
    return datetime.now(UTC).isoformat()


def initialize_schema(conn: sqlite3.Connection) -> None:
    try:
        version = conn.execute(
            "SELECT value FROM index_meta WHERE key = 'schema_version'"
        ).fetchone()
        if version is None or version[0] != SCHEMA_VERSION:
            conn.executescript("""
                DROP TABLE IF EXISTS documents;
                DROP TABLE IF EXISTS document_fts;
                DROP TABLE IF EXISTS index_meta;
                DROP INDEX IF EXISTS idx_documents_content_hash;
                DROP INDEX IF EXISTS idx_documents_text_hash;
            """)
    except sqlite3.OperationalError:
        pass
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS documents (
            id INTEGER PRIMARY KEY,
            source_root TEXT NOT NULL,
            source_path TEXT NOT NULL UNIQUE,
            rel_path TEXT NOT NULL,
            filename TEXT NOT NULL,
            extension TEXT NOT NULL,
            category_path TEXT NOT NULL,
            size INTEGER NOT NULL,
            mtime REAL NOT NULL,
            content_hash TEXT NOT NULL,
            text_hash TEXT,
            extraction_status TEXT NOT NULL,
            indexed_at TEXT NOT NULL
        );

        CREATE VIRTUAL TABLE IF NOT EXISTS document_fts
        USING fts5(text, tokenize="unicode61 remove_diacritics 2");

        CREATE TABLE IF NOT EXISTS index_meta (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL
        );

        CREATE INDEX IF NOT EXISTS idx_documents_content_hash
        ON documents(content_hash);

        CREATE INDEX IF NOT EXISTS idx_documents_text_hash
        ON documents(text_hash);
        """
    )
    conn.execute(
        "INSERT OR IGNORE INTO index_meta(key, value) VALUES ('schema_version', ?)",
        (SCHEMA_VERSION,),
    )
    conn.commit()


def fts5_available() -> bool:
    try:
        with sqlite3.connect(":memory:") as conn:
            conn.execute(
                'CREATE VIRTUAL TABLE fts_probe USING fts5(text, tokenize="unicode61 remove_diacritics 2")'
            )
    except sqlite3.Error:
        return False
    return True


def _document_count(index: Path) -> tuple[bool, int | None, str | None]:
    try:
        with sqlite3.connect(f"file:{index}?mode=ro", uri=True) as conn:
            row = conn.execute("SELECT count(*) FROM documents").fetchone()
    except sqlite3.Error as e:
        return False, None, str(e)
    return True, int(row[0] if row else 0), None


def _connect_readonly(index: Path) -> sqlite3.Connection:
    return sqlite3.connect(f"file:{index}?mode=ro", uri=True)


def check(config: LibraryFoldersConfig | None = None) -> dict[str, Any]:
    config = config or default_config()
    index = config.index
    roots_info = [
        {
            "path": str(r),
            "available": r.is_dir(),
            "calibre": (r / "metadata.db").exists(),
        }
        for r in config.roots
    ]
    any_root_available = any(ri["available"] for ri in roots_info)
    index_exists = bool(index is not None and index.exists())
    index_available = False
    document_count = None
    index_error = None
    if index_exists and index is not None:
        index_available, document_count, index_error = _document_count(index)
    return {
        "status": "ok" if config.available and any_root_available else "unavailable",
        "source_roots": roots_info,
        "index_path": str(index) if index is not None else None,
        "missing": list(config.missing),
        "index_exists": index_exists,
        "index_available": index_available,
        "index_error": index_error,
        "fts5": fts5_available(),
        "exclude_paths": [str(path) for path in config.exclude],
        "document_count": document_count,
    }


def _accepted_file(path: Path) -> bool:
    return path.is_file() and path.suffix.lower() not in NOISE_EXTENSIONS


def _is_excluded(path: Path, exclude: tuple[Path, ...]) -> bool:
    return any(path.is_relative_to(excluded) for excluded in exclude)


def _iter_files(
    roots: list[Path],
    limit: int | None,
    exclude: tuple[Path, ...] = (),
) -> list[tuple[Path, Path]]:
    """Return (source_root, path) pairs across all roots."""
    files: list[tuple[Path, Path]] = []
    for root in roots:
        if not root.is_dir():
            continue
        for dirpath, dirnames, filenames in os.walk(root):
            dirnames[:] = sorted(
                d
                for d in dirnames
                if not d.startswith(".")
                and not _is_excluded(Path(dirpath) / d, exclude)
            )
            for filename in sorted(filenames):
                if filename.startswith("."):
                    continue
                path = Path(dirpath) / filename
                if not _accepted_file(path):
                    continue
                files.append((root, path))
                if limit is not None and len(files) >= limit:
                    return files
    return files


def _hash_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _unreadable_content_hash(source_path: str, size: int, mtime: float) -> str:
    value = f"unreadable\x00{source_path}\x00{size}\x00{mtime}"
    return f"unreadable:{hashlib.sha256(value.encode('utf-8')).hexdigest()}"


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def _xmlish_text(data: bytes) -> str:
    raw = data.decode("utf-8", errors="replace")
    try:
        root = ElementTree.fromstring(raw)
    except ElementTree.ParseError:
        return _strip_xml(raw)
    return re.sub(r"\s+", " ", " ".join(t.strip() for t in root.itertext())).strip()


def _extract_zip_members(
    path: Path,
    accept: Callable[[str], bool],
) -> ExtractedText:
    try:
        with zipfile.ZipFile(path) as archive:
            parts = [
                _xmlish_text(archive.read(name))
                for name in sorted(archive.namelist())
                if accept(name) and not name.endswith("/")
            ]
    except zipfile.BadZipFile:
        return ExtractedText(text="", status="error: bad zip")
    text = re.sub(r"\s+", " ", " ".join(part for part in parts if part)).strip()
    return ExtractedText(text=text, status="ok" if text else "empty")


def _extract_pdf(path: Path) -> ExtractedText:
    if shutil.which("pdftotext") is None:
        return ExtractedText(text="", status="unsupported: pdftotext not found")
    try:
        result = subprocess.run(
            ["pdftotext", "-layout", str(path), "-"],
            capture_output=True,
            encoding="utf-8",
            errors="replace",
            timeout=60,
            check=False,
        )
    except subprocess.TimeoutExpired:
        return ExtractedText(text="", status="error: pdftotext timed out")
    if result.returncode != 0:
        message = (result.stderr or "pdftotext failed").strip().splitlines()[:1]
        return ExtractedText(text="", status=f"error: {message[0]}")
    text = result.stdout
    return ExtractedText(text=text, status="ok" if text.strip() else "empty")


def _run_doc_extractor(command: list[str], label: str) -> ExtractedText:
    try:
        result = subprocess.run(
            command,
            capture_output=True,
            encoding="utf-8",
            errors="replace",
            timeout=60,
            check=False,
        )
    except subprocess.TimeoutExpired:
        return ExtractedText(text="", status=f"error: {label} timed out")
    if result.returncode != 0:
        message = (result.stderr or f"{label} failed").strip().splitlines()[:1]
        return ExtractedText(text="", status=f"error: {message[0]}")
    text = result.stdout
    return ExtractedText(text=text, status="ok" if text.strip() else "empty")


def _extract_doc(path: Path) -> ExtractedText:
    if sys.platform == "darwin" and shutil.which("textutil") is not None:
        return _run_doc_extractor(
            ["textutil", "-convert", "txt", "-stdout", str(path)],
            "textutil",
        )
    if shutil.which("antiword") is not None:
        return _run_doc_extractor(["antiword", str(path)], "antiword")
    if shutil.which("catdoc") is not None:
        return _run_doc_extractor(["catdoc", str(path)], "catdoc")
    return ExtractedText(text="", status="unsupported: doc extractor not found")


def _extract_mhtml(path: Path) -> ExtractedText:
    import email
    from email import policy

    try:
        with path.open("rb") as fh:
            message = email.message_from_binary_file(fh, policy=policy.default)
    except Exception as e:
        return ExtractedText(text="", status=f"error: {e}")
    parts: list[str] = []
    for part in message.walk():
        if part.get_content_type() not in ("text/html", "text/plain"):
            continue
        try:
            content = part.get_content()
        except Exception:
            continue
        if isinstance(content, bytes):
            content = content.decode("utf-8", errors="replace")
        parts.append(content)
    text = _strip_xml("\n".join(parts))
    return ExtractedText(text=text, status="ok" if text.strip() else "empty")


def _extract_ebook(path: Path) -> ExtractedText:
    if shutil.which("ebook-convert") is None:
        return ExtractedText(text="", status="unsupported: ebook-convert not found")
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp) / "out.txt"
        try:
            result = subprocess.run(
                ["ebook-convert", str(path), str(out)],
                capture_output=True,
                encoding="utf-8",
                errors="replace",
                timeout=180,
                check=False,
            )
        except subprocess.TimeoutExpired:
            return ExtractedText(text="", status="error: ebook-convert timed out")
        if result.returncode != 0:
            message = (result.stderr or "ebook-convert failed").strip().splitlines()
            detail = message[-1] if message else "ebook-convert failed"
            return ExtractedText(text="", status=f"error: {detail}")
        try:
            text = (
                out.read_text(encoding="utf-8", errors="replace")
                if out.exists()
                else ""
            )
        except OSError as e:
            return ExtractedText(text="", status=f"error: {e}")
    return ExtractedText(text=text, status="ok" if text.strip() else "empty")


def _skip_member(extension: str) -> bool:
    return (
        not extension
        or extension in NOISE_EXTENSIONS
        or extension in ARCHIVE_EXTENSIONS
    )


def _route_member_bytes(name: str, data: bytes) -> str:
    """Extract text from one archive member by routing it through ``extract_text``."""
    extension = Path(name).suffix.lower()
    if _skip_member(extension):
        return ""
    with tempfile.TemporaryDirectory() as tmp:
        member_path = Path(tmp) / f"member{extension}"
        try:
            member_path.write_bytes(data)
            return extract_text(member_path).text
        except OSError:
            return ""


def _archive_result(parts: list[str]) -> ExtractedText:
    text = re.sub(r"\s+", " ", " ".join(part for part in parts if part)).strip()
    return ExtractedText(text=text, status="ok" if text else "empty")


def _extract_zip_archive(path: Path) -> ExtractedText:
    start = time.monotonic()
    parts: list[str] = []
    member_count = 0
    total_uncompressed = 0
    try:
        with zipfile.ZipFile(path) as archive:
            for info in archive.infolist():
                if info.is_dir() or info.flag_bits & 0x1:
                    continue
                if _skip_member(Path(info.filename).suffix.lower()):
                    continue
                member_count += 1
                total_uncompressed += info.file_size
                if (
                    member_count > ARCHIVE_MAX_MEMBERS
                    or total_uncompressed > ARCHIVE_MAX_UNCOMPRESSED
                ):
                    return ExtractedText(text="", status="error: archive too large")
                if time.monotonic() - start > ARCHIVE_MAX_WALLCLOCK:
                    return ExtractedText(text="", status="error: archive timed out")
                try:
                    data = archive.read(info)
                except Exception:
                    continue
                text = _route_member_bytes(info.filename, data)
                if text:
                    parts.append(text)
    except zipfile.BadZipFile:
        return ExtractedText(text="", status="error: bad zip")
    return _archive_result(parts)


def _extract_bz2(path: Path) -> ExtractedText:
    start = time.monotonic()
    try:
        with bz2.open(path, "rb") as handle:
            data = handle.read(ARCHIVE_MAX_UNCOMPRESSED + 1)
    except (OSError, EOFError, ValueError):
        return ExtractedText(text="", status="error: bad bz2")
    if len(data) > ARCHIVE_MAX_UNCOMPRESSED:
        return ExtractedText(text="", status="error: archive too large")
    try:
        with tarfile.open(fileobj=io.BytesIO(data)) as tar:
            parts: list[str] = []
            member_count = 0
            for member in tar.getmembers():
                if not member.isfile():
                    continue
                if _skip_member(Path(member.name).suffix.lower()):
                    continue
                member_count += 1
                if member_count > ARCHIVE_MAX_MEMBERS:
                    return ExtractedText(text="", status="error: archive too large")
                if time.monotonic() - start > ARCHIVE_MAX_WALLCLOCK:
                    return ExtractedText(text="", status="error: archive timed out")
                handle = tar.extractfile(member)
                if handle is None:
                    continue
                text = _route_member_bytes(member.name, handle.read())
                if text:
                    parts.append(text)
        return _archive_result(parts)
    except tarfile.TarError:
        return _archive_result([_route_member_bytes(path.stem, data)])


def _extract_7z(path: Path) -> ExtractedText:
    seven_zip = shutil.which("7z")
    if seven_zip is None:
        return ExtractedText(text="", status="unsupported: 7z not found")
    start = time.monotonic()
    with tempfile.TemporaryDirectory() as tmp:
        try:
            result = subprocess.run(
                [seven_zip, "x", "-y", "-bd", f"-o{tmp}", str(path)],
                capture_output=True,
                encoding="utf-8",
                errors="replace",
                timeout=ARCHIVE_MAX_WALLCLOCK,
                check=False,
            )
        except subprocess.TimeoutExpired:
            return ExtractedText(text="", status="error: archive timed out")
        if result.returncode != 0:
            message = (result.stderr or "7z failed").strip().splitlines()
            detail = message[-1] if message else "7z failed"
            return ExtractedText(text="", status=f"error: {detail}")
        parts: list[str] = []
        member_count = 0
        total_uncompressed = 0
        for member_path in sorted(Path(tmp).rglob("*")):
            if not member_path.is_file():
                continue
            if _skip_member(member_path.suffix.lower()):
                continue
            member_count += 1
            try:
                total_uncompressed += member_path.stat().st_size
            except OSError:
                continue
            if (
                member_count > ARCHIVE_MAX_MEMBERS
                or total_uncompressed > ARCHIVE_MAX_UNCOMPRESSED
            ):
                return ExtractedText(text="", status="error: archive too large")
            if time.monotonic() - start > ARCHIVE_MAX_WALLCLOCK:
                return ExtractedText(text="", status="error: archive timed out")
            try:
                extracted = extract_text(member_path)
            except Exception:
                continue
            if extracted.text.strip():
                parts.append(extracted.text)
    return _archive_result(parts)


def extract_text(path: Path) -> ExtractedText:
    extension = path.suffix.lower()
    if extension in TEXT_EXTENSIONS:
        text = _read_text(path)
        return ExtractedText(text=text, status="ok" if text.strip() else "empty")
    if extension in HTML_EXTENSIONS:
        text = _strip_xml(_read_text(path))
        return ExtractedText(text=text, status="ok" if text.strip() else "empty")
    if extension in EPUB_EXTENSIONS:
        return _extract_zip_members(
            path,
            lambda name: name.lower().endswith((".htm", ".html", ".xhtml", ".xml")),
        )
    if extension == ".docx":
        return _extract_zip_members(
            path,
            lambda name: (
                name.lower().startswith("word/") and name.lower().endswith(".xml")
            ),
        )
    if extension == ".pptx":
        return _extract_zip_members(
            path,
            lambda name: (
                name.lower().startswith("ppt/slides/") and name.lower().endswith(".xml")
            ),
        )
    if extension == ".odt":
        return _extract_zip_members(path, lambda name: name.lower() == "content.xml")
    if extension == ".pdf":
        return _extract_pdf(path)
    if extension == ".doc":
        return _extract_doc(path)
    if extension in MHTML_EXTENSIONS:
        return _extract_mhtml(path)
    if extension in EBOOK_CONVERT_EXTENSIONS:
        return _extract_ebook(path)
    if extension == ".zip":
        return _extract_zip_archive(path)
    if extension == ".bz2":
        return _extract_bz2(path)
    if extension == ".7z":
        return _extract_7z(path)
    return ExtractedText(text="", status=f"unsupported: {extension or 'no extension'}")


def _normalized_text_hash(text: str) -> str | None:
    normalized = re.sub(r"\s+", " ", text).strip()
    if not normalized:
        return None
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def _safe_fts_query(query: str) -> str:
    terms = re.findall(r"[\w-￿]+", query, flags=re.UNICODE)
    if not terms:
        return query
    return " ".join(f'"{term.replace('"', '""')}"' for term in terms)


def _build_calibre_metadata_lookup(calibre_root: Path) -> dict[str, str]:
    """Return {absolute_file_path: metadata_prefix} for all files in a Calibre library."""
    metadata_db = calibre_root / "metadata.db"
    if not metadata_db.exists():
        return {}
    try:
        with sqlite3.connect(f"file:{metadata_db}?mode=ro", uri=True) as conn:
            authors_by_book: dict[int, list[str]] = {}
            for book_id, name in conn.execute(
                "SELECT bal.book, a.name FROM books_authors_link bal JOIN authors a ON bal.author = a.id"
            ).fetchall():
                authors_by_book.setdefault(int(book_id), []).append(str(name))
            tags_by_book: dict[int, list[str]] = {}
            for book_id, name in conn.execute(
                "SELECT btl.book, t.name FROM books_tags_link btl JOIN tags t ON btl.tag = t.id"
            ).fetchall():
                tags_by_book.setdefault(int(book_id), []).append(str(name))
            lookup: dict[str, str] = {}
            for book_id, book_path, file_name, fmt in conn.execute(
                "SELECT b.id, b.path, d.name, d.format FROM books b JOIN data d ON b.id = d.book"
            ).fetchall():
                book_id = int(book_id)
                file_path = str(
                    calibre_root / str(book_path) / f"{file_name}.{fmt.lower()}"
                )
                authors = ", ".join(authors_by_book.get(book_id, []))
                tags = ", ".join(tags_by_book.get(book_id, []))
                parts = [f"Calibre #{book_id}"]
                if authors:
                    parts.append(f"Authors: {authors}")
                if tags:
                    parts.append(f"Tags: {tags}")
                lookup[file_path] = "[" + " | ".join(parts) + "]"
    except sqlite3.Error:
        return {}
    return lookup


def _upsert_document(
    conn: sqlite3.Connection,
    *,
    source_root: Path,
    path: Path,
    stat_result: os.stat_result | None = None,
    content_hash: str,
    extracted: ExtractedText,
    indexed_at: str,
) -> int:
    stat = stat_result or path.stat()
    source_path = str(path)
    rel_path = path.relative_to(source_root).as_posix()
    category_path = path.relative_to(source_root).parent.as_posix()
    category_path = "" if category_path == "." else category_path
    text_hash = _normalized_text_hash(extracted.text)
    existing = conn.execute(
        "SELECT id FROM documents WHERE source_path = ?",
        (source_path,),
    ).fetchone()
    values = {
        "source_root": str(source_root),
        "source_path": source_path,
        "rel_path": rel_path,
        "filename": path.name,
        "extension": path.suffix.lower(),
        "category_path": category_path,
        "size": stat.st_size,
        "mtime": stat.st_mtime,
        "content_hash": content_hash,
        "text_hash": text_hash,
        "extraction_status": extracted.status,
        "indexed_at": indexed_at,
    }
    if existing:
        doc_id = int(existing[0])
        conn.execute(
            """
            UPDATE documents
            SET source_root = :source_root,
                rel_path = :rel_path,
                filename = :filename,
                extension = :extension,
                category_path = :category_path,
                size = :size,
                mtime = :mtime,
                content_hash = :content_hash,
                text_hash = :text_hash,
                extraction_status = :extraction_status,
                indexed_at = :indexed_at
            WHERE id = :id
            """,
            values | {"id": doc_id},
        )
        return doc_id
    cursor = conn.execute(
        """
        INSERT INTO documents (
            source_root, source_path, rel_path, filename, extension, category_path,
            size, mtime, content_hash, text_hash, extraction_status, indexed_at
        )
        VALUES (
            :source_root, :source_path, :rel_path, :filename, :extension, :category_path,
            :size, :mtime, :content_hash, :text_hash, :extraction_status, :indexed_at
        )
        """,
        values,
    )
    doc_id = cursor.lastrowid
    if doc_id is None:
        raise sqlite3.DatabaseError("insert did not return a document id")
    return int(doc_id)


def _replace_fts_text(conn: sqlite3.Connection, doc_id: int, text: str) -> None:
    conn.execute("DELETE FROM document_fts WHERE rowid = ?", (doc_id,))
    if text.strip():
        conn.execute(
            "INSERT INTO document_fts(rowid, text) VALUES (?, ?)",
            (doc_id, text),
        )


def _should_skip(
    conn: sqlite3.Connection,
    *,
    source_path: str,
    size: int,
    mtime: float,
    retry_failed: bool,
) -> bool:
    row = conn.execute(
        "SELECT size, mtime, extraction_status FROM documents WHERE source_path = ?",
        (source_path,),
    ).fetchone()
    if row is None:
        return False
    if int(row[0]) != size or float(row[1]) != mtime:
        return False
    if retry_failed and row[2] != "ok":
        return False
    return True


def _delete_missing_documents(
    conn: sqlite3.Connection, seen_source_paths: set[str]
) -> int:
    deleted = 0
    for doc_id, source_path in conn.execute(
        "SELECT id, source_path FROM documents"
    ).fetchall():
        if source_path in seen_source_paths:
            continue
        conn.execute("DELETE FROM document_fts WHERE rowid = ?", (doc_id,))
        conn.execute("DELETE FROM documents WHERE id = ?", (doc_id,))
        deleted += 1
    return deleted


def refresh(
    config: LibraryFoldersConfig | None = None,
    *,
    limit: int | None = None,
    retry_failed: bool = False,
) -> dict[str, Any]:
    config = config or default_config()
    if not config.roots or config.index is None:
        return {
            "status": "unavailable",
            "reason": f"missing config: {', '.join(config.missing)}",
            "indexed": 0,
        }
    available_roots = [r for r in config.roots if r.is_dir()]
    if not available_roots:
        return {
            "status": "unavailable",
            "reason": "no source roots are available",
            "indexed": 0,
        }
    index = config.index
    index.parent.mkdir(parents=True, exist_ok=True)
    indexed_at = _utc_now()
    calibre_lookup: dict[str, str] = {}
    for root in available_roots:
        calibre_lookup.update(_build_calibre_metadata_lookup(root))
    files = _iter_files(available_roots, limit, config.exclude)
    extracted_count = 0
    metadata_only = 0
    skipped = 0
    written = 0
    deleted = 0
    errors: list[dict[str, str]] = []
    seen_source_paths: set[str] = set()
    with sqlite3.connect(index) as conn:
        initialize_schema(conn)
        progress = tqdm(
            files,
            desc="library-folders refresh",
            unit="file",
            smoothing=0,
            disable=not sys.stderr.isatty(),
        )
        for source_root, path in progress:
            source_path = str(path)
            rel_path = path.relative_to(source_root).as_posix()
            try:
                stat = path.stat()
            except OSError as e:
                errors.append({"relative_path": rel_path, "error": f"stat failed: {e}"})
                continue
            seen_source_paths.add(source_path)
            if _should_skip(
                conn,
                source_path=source_path,
                size=stat.st_size,
                mtime=stat.st_mtime,
                retry_failed=retry_failed,
            ):
                skipped += 1
                continue
            try:
                content_hash = _hash_file(path)
            except OSError as e:
                content_hash = _unreadable_content_hash(
                    source_path, stat.st_size, stat.st_mtime
                )
                extracted = ExtractedText(
                    text="", status=f"error: file read failed: {e}"
                )
                errors.append({"relative_path": rel_path, "error": extracted.status})
            else:
                try:
                    extracted = extract_text(path)
                except Exception as e:
                    extracted = ExtractedText(
                        text="", status=f"error: extraction failed: {e}"
                    )
                    errors.append(
                        {"relative_path": rel_path, "error": extracted.status}
                    )
            doc_id = _upsert_document(
                conn,
                source_root=source_root,
                path=path,
                stat_result=stat,
                content_hash=content_hash,
                extracted=extracted,
                indexed_at=indexed_at,
            )
            written += 1
            prefix = calibre_lookup.get(source_path, "")
            fts_text = (
                (prefix + "\n\n" + extracted.text).strip() if prefix else extracted.text
            )
            _replace_fts_text(conn, doc_id, fts_text)
            if fts_text.strip():
                extracted_count += 1
            else:
                metadata_only += 1
        if limit is None:
            deleted = _delete_missing_documents(conn, seen_source_paths)
        conn.execute(
            """
            INSERT INTO index_meta(key, value) VALUES ('last_refresh', ?)
            ON CONFLICT(key) DO UPDATE SET value = excluded.value
            """,
            (indexed_at,),
        )
        conn.commit()
    return {
        "status": "ok",
        "source_roots": [str(r) for r in available_roots],
        "index_path": str(index),
        "indexed": len(files),
        "written": written,
        "skipped": skipped,
        "deleted": deleted,
        "text_extracted": extracted_count,
        "metadata_only": metadata_only,
        "error_count": len(errors),
        "errors": errors[:20],
        "limited": limit is not None and len(files) >= limit,
        "retry_failed": retry_failed,
    }


def _search_rows(
    conn: sqlite3.Connection,
    query: str,
    limit: int,
) -> list[sqlite3.Row]:
    conn.row_factory = sqlite3.Row
    sql = """
        SELECT
            d.id,
            d.source_root,
            d.source_path,
            d.rel_path,
            d.filename,
            d.extension,
            d.extraction_status,
            snippet(document_fts, 0, '[', ']', ' ... ', 18) AS snippet
        FROM document_fts
        JOIN documents d ON d.id = document_fts.rowid
        WHERE document_fts MATCH ?
        ORDER BY bm25(document_fts)
        LIMIT ?
    """
    try:
        return list(conn.execute(sql, (query, limit)).fetchall())
    except sqlite3.OperationalError:
        return list(conn.execute(sql, (_safe_fts_query(query), limit)).fetchall())


def _find(parent: dict[int, int], value: int) -> int:
    root = value
    while parent[root] != root:
        root = parent[root]
    while parent[value] != value:
        value, parent[value] = parent[value], root
    return root


def _union(parent: dict[int, int], left: int, right: int) -> None:
    left_root = _find(parent, left)
    right_root = _find(parent, right)
    if left_root != right_root:
        parent[right_root] = left_root


def _exact_duplicate_map(
    conn: sqlite3.Connection,
) -> dict[int, list[tuple[int, str, str]]]:
    rows = conn.execute(
        "SELECT id, source_path, rel_path, content_hash, text_hash FROM documents"
    ).fetchall()
    parent = {int(row["id"]): int(row["id"]) for row in rows}
    source_paths = {int(row["id"]): str(row["source_path"]) for row in rows}
    rel_paths = {int(row["id"]): str(row["rel_path"]) for row in rows}
    for key in ("content_hash", "text_hash"):
        groups: dict[str, list[int]] = {}
        for row in rows:
            value = row[key]
            if value is None:
                continue
            groups.setdefault(str(value), []).append(int(row["id"]))
        for ids in groups.values():
            if len(ids) < 2:
                continue
            first = ids[0]
            for other in ids[1:]:
                _union(parent, first, other)
    components: dict[int, list[int]] = {}
    for doc_id in parent:
        components.setdefault(_find(parent, doc_id), []).append(doc_id)
    duplicate_map: dict[int, list[tuple[int, str, str]]] = {}
    for ids in components.values():
        if len(ids) < 2:
            continue
        members = sorted(
            ((doc_id, source_paths[doc_id], rel_paths[doc_id]) for doc_id in ids),
            key=lambda item: item[1],
        )
        for doc_id in ids:
            duplicate_map[doc_id] = members
    return duplicate_map


def _normalize_title_key(filename: str) -> str:
    stem = Path(filename).stem
    folded = _strip_diacritics(stem).casefold()
    return re.sub(r"\s+", " ", re.sub(r"[\W_]+", " ", folded)).strip()


def _normalize_filename_key(filename: str) -> str:
    key = _normalize_title_key(filename)
    for pattern in (
        r"\s+(?:copy|duplicate)(?:\s+\d+)?$",
        r"\s+(?:v|ver|version)\s*\d+$",
    ):
        key = re.sub(pattern, "", key).strip()
    return key


def _filename_hint_key(filename: str, extension: str) -> str:
    if extension.lower() in FILENAME_HINT_SKIP_EXTENSIONS:
        return ""
    key = _normalize_filename_key(filename)
    if key in FILENAME_HINT_STOP_NAMES:
        return ""
    return key


def _weak_duplicate_hints(
    conn: sqlite3.Connection,
    exact_duplicate_map: dict[int, list[tuple[int, str, str]]],
) -> dict[int, list[dict[str, Any]]]:
    rows = conn.execute(
        "SELECT id, source_path, filename, extension FROM documents"
    ).fetchall()
    source_paths = {int(row["id"]): str(row["source_path"]) for row in rows}
    exact_sets = {
        doc_id: {member_id for member_id, *_ in members}
        for doc_id, members in exact_duplicate_map.items()
    }
    grouped: dict[tuple[str, str], list[int]] = {}
    for row in rows:
        doc_id = int(row["id"])
        values = {
            "normalized_filename": _filename_hint_key(
                str(row["filename"]),
                str(row["extension"]),
            ),
        }
        for signal, value in values.items():
            if value:
                grouped.setdefault((signal, value), []).append(doc_id)
    signals_by_doc: dict[int, dict[int, set[str]]] = {}
    for (signal, _), ids in grouped.items():
        if len(ids) < 2:
            continue
        for doc_id in ids:
            for other_id in ids:
                if other_id == doc_id or other_id in exact_sets.get(doc_id, set()):
                    continue
                signals_by_doc.setdefault(doc_id, {}).setdefault(other_id, set()).add(
                    signal
                )
    hints: dict[int, list[dict[str, Any]]] = {}
    for doc_id, candidates in signals_by_doc.items():
        ordered = sorted(candidates.items(), key=lambda item: source_paths[item[0]])
        hints[doc_id] = [
            {
                "source_path": source_paths[other_id],
                "signals": sorted(signals),
            }
            for other_id, signals in ordered[:10]
        ]
    return hints


def _duplicate_cluster_summary(
    clusters: dict[str, list[sqlite3.Row]],
    samples: int,
) -> dict[str, Any]:
    duplicate_clusters = {
        key: rows for key, rows in clusters.items() if key and len(rows) > 1
    }
    ordered = sorted(
        duplicate_clusters.items(),
        key=lambda item: (-len(item[1]), item[0]),
    )
    return {
        "cluster_count": len(duplicate_clusters),
        "file_count": sum(len(rows) for rows in duplicate_clusters.values()),
        "samples": [
            {
                "key": key,
                "paths": sorted(str(row["source_path"]) for row in rows),
            }
            for key, rows in ordered[:samples]
        ],
    }


def _group_rows(
    rows: list[sqlite3.Row],
    key_name: str,
) -> dict[str, list[sqlite3.Row]]:
    grouped: dict[str, list[sqlite3.Row]] = {}
    for row in rows:
        value = row[key_name]
        if value is None:
            continue
        grouped.setdefault(str(value), []).append(row)
    return grouped


def duplicates(
    config: LibraryFoldersConfig | None = None,
    *,
    samples: int = 5,
) -> dict[str, Any]:
    config = config or default_config()
    if config.index is None or not config.index.exists():
        return {
            "status": "unavailable",
            "reason": "index not found",
            "index_path": str(config.index) if config.index is not None else None,
            "groups": {},
            "non_text_extracted_duplicate_candidates": {
                "file_count": 0,
                "by_extension": {},
            },
        }
    with _connect_readonly(config.index) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            """
            SELECT id, source_path, filename, extension, size, content_hash, text_hash
            FROM documents
            """
        ).fetchall()
    rows_list = list(rows)
    grouped = {
        "content_hash": _group_rows(rows_list, "content_hash"),
        "text_hash": _group_rows(rows_list, "text_hash"),
        "normalized_filename": {},
        "normalized_filename_size": {},
        "size": _group_rows(rows_list, "size"),
    }
    for row in rows_list:
        filename_key = _normalize_filename_key(str(row["filename"]))
        if filename_key:
            grouped["normalized_filename"].setdefault(filename_key, []).append(row)
            grouped["normalized_filename_size"].setdefault(
                f"{filename_key}|{row['size']}",
                [],
            ).append(row)
    groups = {
        key: _duplicate_cluster_summary(value, max(samples, 0))
        for key, value in grouped.items()
    }
    candidate_ids: set[int] = set()
    for clusters in grouped.values():
        for cluster_rows in clusters.values():
            if len(cluster_rows) > 1:
                candidate_ids.update(int(row["id"]) for row in cluster_rows)
    non_text_rows = [
        row
        for row in rows_list
        if int(row["id"]) in candidate_ids and row["text_hash"] is None
    ]
    by_extension: dict[str, int] = {}
    for row in non_text_rows:
        extension = str(row["extension"]) or "(none)"
        by_extension[extension] = by_extension.get(extension, 0) + 1
    return {
        "status": "ok",
        "index_path": str(config.index),
        "document_count": len(rows_list),
        "groups": groups,
        "non_text_extracted_duplicate_candidates": {
            "file_count": len(non_text_rows),
            "by_extension": dict(sorted(by_extension.items())),
        },
    }


def search(
    query: str,
    config: LibraryFoldersConfig | None = None,
    *,
    limit: int = 20,
    include_duplicates: bool = False,
) -> list[dict[str, Any]]:
    if limit <= 0:
        return []
    config = config or default_config()
    if config.index is None or not config.index.exists():
        return []
    candidate_limit = limit if include_duplicates else max(limit * 10, limit + 50)
    with _connect_readonly(config.index) as conn:
        try:
            conn.row_factory = sqlite3.Row
            duplicate_map = _exact_duplicate_map(conn)
            weak_hints = _weak_duplicate_hints(conn, duplicate_map)
            rows = _search_rows(conn, query, candidate_limit)
        except sqlite3.Error:
            return []
    hits: list[dict[str, Any]] = []
    for row in rows:
        duplicate_members = duplicate_map.get(int(row["id"]), [])
        if (
            not include_duplicates
            and duplicate_members
            and row["source_path"] != duplicate_members[0][1]
        ):
            continue
        hits.append(
            {
                "document_id": int(row["id"]),
                "title": row["filename"],
                "source_root": row["source_root"],
                "relative_path": row["rel_path"],
                "source_path": row["source_path"],
                "extension": row["extension"],
                "snippet": row["snippet"],
                "extraction_status": row["extraction_status"],
                "duplicate_count": len(duplicate_members) if duplicate_members else 1,
                "duplicate_paths": [rel for _, _src, rel in duplicate_members],
                "possible_duplicate_of": weak_hints.get(int(row["id"]), []),
                "source_available": Path(row["source_path"]).exists(),
            }
        )
        if len(hits) >= limit:
            break
    return hits
