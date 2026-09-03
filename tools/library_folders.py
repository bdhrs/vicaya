"""Manage a local SQLite index for one or more library folders."""

from __future__ import annotations

import bz2
import hashlib
import io
import json
import os
import queue
import re
import shutil
import sqlite3
import subprocess
import sys
import tarfile
import tempfile
import threading
import time
import unicodedata
import zipfile
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from collections.abc import Iterator
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
OCR_KILL_SWITCH_ENV = "VICAYA_LIBRARY_FOLDERS_OCR"
# 1000, measured across all 1,739 PDFs in the library that have no text layer
# (median 94 pages, mean 153, max 1,678). Coverage and serial cost by cap:
# 150 -> 54% in 47 h, 500 -> 93% in 81 h, 1000 -> 99% in 86 h. The last step
# buys 6 points of coverage for 5 hours, so the cap is set where it stops
# binding on real books while still bounding a pathological scan.
OCR_PAGE_CAP = 1000
OCR_CHUNK_PAGES = 10
OCR_CHUNK_TIMEOUT = 120
# The first chunk also pays interpreter startup, the pdf_inspector import, ONNX
# runtime init, the PDFium load, and on a machine that has never run OCR a
# one-time model download. Every measured timing was warm-start, so this grace
# is generous on purpose.
OCR_FIRST_CHUNK_TIMEOUT = 600
OCR_SUBPROCESS_TIMEOUT = 1800
REFRESH_COMMIT_SECONDS = 30.0
SCHEMA_VERSION = "3"
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
    # Write-ahead logging so a search can read the index while a refresh is
    # part-way through writing it, and so a killed refresh leaves the
    # already-committed files behind instead of rolling the whole walk back.
    try:
        conn.execute("PRAGMA journal_mode=WAL")
    except sqlite3.OperationalError:
        pass
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
    result = _extract_pdf_pdftotext(path)
    if result.status == "ok":
        return result
    return _extract_pdf_ocr_fallback(path) or result


def _extract_pdf_pdftotext(path: Path) -> ExtractedText:
    if shutil.which("pdftotext") is None:
        return ExtractedText(text="", status="unsupported: pdftotext not found")
    try:
        # Reading-order mode (no -layout): keeps two-column books in column
        # sequence instead of interleaving them line-by-line.
        result = subprocess.run(
            ["pdftotext", str(path), "-"],
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


def _ort_dylib_path() -> str | None:
    """Return the onnxruntime shared library path, when the wheel is installed."""
    try:
        import onnxruntime
    except ImportError:
        return None
    capi = Path(onnxruntime.__file__).resolve().parent / "capi"
    for candidate in sorted(capi.glob("libonnxruntime.so.*")):
        return str(candidate)
    return None


def _ocr_worker_chunks(path: str) -> Iterator[dict[str, Any]]:
    """Yield one reply per OCR'd chunk of a PDF, newest work last.

    Runs inside a dedicated subprocess (see _extract_pdf_ocr_fallback) because
    process_pdf_with_ocr has been observed to deadlock without bound on some
    scanned books; a subprocess turns that hang into a killable timeout.

    Yields a "meta" reply first, then a "chunk" reply per completed chunk.
    Emitting per chunk is what lets the caller bound each chunk separately and
    keep the pages that finished: a stall was measured on 2 of 12 real scanned
    books (2026-09-03), and one of them had already OCR'd 130 of 150 pages.
    """
    import pdf_inspector  # noqa: PLC0415 - optional dependency, lazy import

    detect = getattr(pdf_inspector, "detect_pdf", None)
    process_with_ocr = getattr(pdf_inspector, "process_pdf_with_ocr", None)
    if detect is None or process_with_ocr is None:
        yield {"kind": "unsupported", "detail": "pdf-inspector lacks OCR API"}
        return
    if not os.environ.get("ORT_DYLIB_PATH"):
        dylib = _ort_dylib_path()
        if dylib is not None:
            os.environ["ORT_DYLIB_PATH"] = dylib
    detection = detect(path)
    page_count = int(detection.page_count)
    last_page = min(page_count, OCR_PAGE_CAP)
    yield {"kind": "meta", "page_count": page_count, "last_page": last_page}
    # Chunked calls: a single multi-hundred-page process_pdf_with_ocr call
    # deadlocks (observed on 150 dense pages); 10-page chunks return in
    # seconds each.
    for start in range(1, last_page + 1, OCR_CHUNK_PAGES):
        chunk = list(range(start, min(start + OCR_CHUNK_PAGES, last_page + 1)))
        ocr = process_with_ocr(path, page_numbers=chunk)
        yield {
            "kind": "chunk",
            "through_page": chunk[-1],
            "text": ocr.markdown or "",
        }


def extraction_succeeded(status: str) -> bool:
    """Whether an extraction_status counts as done and needs no re-extraction.

    The vocabulary is a prefix contract, relied on by _should_skip, the two
    just recipes, README.md, kamma/tech.md and skill/vicaya/SKILL.md:

      "ok"           full text extracted
      "ok: ..."      a success with a note (OCR stopped at OCR_PAGE_CAP);
                     re-running would redo identical pages, so it is done
      "partial: ..." some text, but the attempt did not finish and a retry
                     is expected to do better (an intermittent OCR stall)
      everything else ("empty", "unsupported: ...", "error: ...") failed
    """
    return status == "ok" or status.startswith("ok:")


def _ocr_status(text: str, page_count: int, pages_done: int) -> str:
    """The extraction status for OCR that reached pages_done of page_count."""
    if not text:
        return "empty"
    # finding 6: page_count 0 means the meta reply never arrived, so how far
    # the OCR actually got is unknown — never claim a complete "ok" from it.
    if page_count > 0 and pages_done >= page_count:
        return "ok"
    # An "ok: ..." status is a success with a note: the row is queryable and
    # _should_skip leaves it alone on --retry-failed, because re-running would
    # redo the same pages. Finishing it means a deliberate re-run at a raised
    # cap.
    if pages_done >= OCR_PAGE_CAP:
        return f"ok: ocr truncated at {OCR_PAGE_CAP} of {page_count} pages"
    # A stall is not deterministic: both books measured as stalling on
    # 2026-09-03 completed cleanly on the next attempt. So a stalled row keeps
    # the pages it got but stays retryable — anything not starting with "ok"
    # is re-extracted by --retry-failed, and a retry will usually finish it.
    return f"partial: ocr stalled at page {pages_done} of {page_count}"


# The worker's stdout also carries whatever pdf-inspector, onnxruntime and
# PDFium print; every reply is framed so noise cannot be mistaken for one.
_OCR_REPLY_MARKER = "__VICAYA_OCR_REPLY__"
_OCR_WORKER_SNIPPET = (
    "import json, sys\n"
    "from tools.library_folders import _OCR_REPLY_MARKER, _ocr_worker_chunks\n"
    "for reply in _ocr_worker_chunks(sys.argv[1]):\n"
    "    sys.stdout.write('\\n' + _OCR_REPLY_MARKER + json.dumps(reply) + '\\n')\n"
    "    sys.stdout.flush()\n"
)


def _parse_ocr_worker_reply(line: str) -> dict[str, Any] | None:
    """Pull a framed JSON reply out of one line of worker stdout, or None."""
    marker_at = line.rfind(_OCR_REPLY_MARKER)
    if marker_at < 0:
        return None
    try:
        payload = json.loads(line[marker_at + len(_OCR_REPLY_MARKER) :].strip())
    except json.JSONDecodeError:
        return None
    return payload if isinstance(payload, dict) else None


def _extract_pdf_ocr_fallback(path: Path) -> ExtractedText | None:
    """OCR PDFs whose text layer is empty, broken, or unreadable by pdftotext.

    Uses pdf-inspector's selective OCR (pdf-inspector + onnxruntime are main
    dependencies; needs PDFIUM_LIB_PATH pointing at a PDFium shared library).
    Returns None when OCR is disabled or unavailable, so the caller can keep
    the pdftotext result unchanged.

    The OCR runs in a dedicated subprocess because process_pdf_with_ocr can
    deadlock without bound. The worker streams one framed reply per chunk and
    each chunk is bounded separately (OCR_CHUNK_TIMEOUT, or
    OCR_FIRST_CHUNK_TIMEOUT for the first, which also pays startup and any
    one-time model download); OCR_SUBPROCESS_TIMEOUT remains a whole-file
    backstop. Bounding per chunk is what keeps the pages a stalled book had
    already finished — measured 2026-09-03, 2 of 12 real scanned books stalled
    mid-book and the previous whole-file timeout discarded up to 130 completed
    pages each time.

    Work per file is capped at the first OCR_PAGE_CAP pages. Statuses follow
    the extraction_succeeded contract: "ok: ocr truncated ..." for a cap that
    cut a book short (deterministic, so it is not retried) and
    "partial: ocr stalled ..." for a stall (intermittent, so it is).
    """
    if os.environ.get(OCR_KILL_SWITCH_ENV) == "0":
        return None
    try:
        import pdf_inspector  # noqa: F401,PLC0415 - availability probe only
    except ImportError:
        return None
    env = dict(os.environ)
    existing_path = os.environ.get("PYTHONPATH", "")
    env["PYTHONPATH"] = (
        f"{_REPO_ROOT}{os.pathsep}{existing_path}" if existing_path else str(_REPO_ROOT)
    )
    with tempfile.TemporaryFile("w+", encoding="utf-8", errors="replace") as errfile:
        try:
            proc = subprocess.Popen(
                [sys.executable, "-c", _OCR_WORKER_SNIPPET, str(path)],
                stdout=subprocess.PIPE,
                stderr=errfile,
                encoding="utf-8",
                errors="replace",
                cwd=str(_REPO_ROOT),
                env=env,
            )
        except OSError as exc:
            return ExtractedText(text="", status=f"error: pdf ocr subprocess: {exc}")
        outcome = None
        try:
            outcome = _collect_ocr_chunks(proc)
        finally:
            # Kill before touching the pipe: a stalled reader thread is blocked
            # in readline() and only the child's death unblocks it.
            if proc.poll() is None:
                proc.kill()
            proc.wait()
            if outcome is not None and outcome.reader is not None:
                outcome.reader.join(timeout=5.0)
            if proc.stdout is not None:
                try:
                    proc.stdout.close()
                except OSError:
                    pass
        errfile.seek(0)
        stderr = errfile.read().strip()
    # _collect_ocr_chunks either returns or raises, so the finally above cannot
    # leave this unbound; the None start exists only so that block can see it.
    assert outcome is not None

    if outcome.unsupported:
        return None
    text = "\n\n".join(part for part in outcome.parts if part).strip()
    if text:
        if not outcome.stalled and proc.returncode != 0:
            # Keep the pages that landed, but do not call a crash a stall.
            return ExtractedText(
                text=text,
                status=(
                    f"partial: ocr worker died at page {outcome.pages_done} "
                    f"of {outcome.page_count}"
                ),
            )
        return ExtractedText(
            text=text,
            status=_ocr_status(text, outcome.page_count, outcome.pages_done),
        )
    if outcome.stalled:
        return ExtractedText(
            text="",
            status=(
                "error: pdf ocr stalled before any pages "
                f"(no chunk in {OCR_CHUNK_TIMEOUT}s)"
            ),
        )
    if outcome.junk is not None:
        return ExtractedText(
            text="", status=f"error: pdf ocr worker returned junk: {outcome.junk}"
        )
    if proc.returncode != 0:
        message = stderr.splitlines()[-1] if stderr else "pdf ocr subprocess failed"
        return ExtractedText(text="", status=f"error: {message}")
    return ExtractedText(text="", status="empty")


@dataclass
class _OcrOutcome:
    parts: list[str]
    page_count: int
    pages_done: int
    stalled: bool
    unsupported: bool
    junk: str | None
    reader: threading.Thread | None = None


def _collect_ocr_chunks(proc: subprocess.Popen[str]) -> _OcrOutcome:
    """Read framed chunk replies, bounding each chunk rather than the file.

    A whole-file timeout throws away every completed chunk when one hangs, and
    charges the full OCR_SUBPROCESS_TIMEOUT for a book that produced nothing.
    Bounding each chunk instead turns a hang into a ~OCR_CHUNK_TIMEOUT cost
    with the finished pages kept.
    """
    parts: list[str] = []
    page_count = 0
    pages_done = 0
    stalled = False
    unsupported = False
    junk: str | None = None

    assert proc.stdout is not None
    stdout = proc.stdout
    # A reader thread rather than a poll on the pipe: a wedged worker leaves
    # the read blocked forever, and only a separate thread lets the deadline
    # below still fire. It also keeps this readable from any file-like object.
    inbox: queue.Queue[str | None] = queue.Queue()

    def pump() -> None:
        try:
            for line in iter(stdout.readline, ""):
                inbox.put(line)
        except (OSError, ValueError):
            pass
        finally:
            inbox.put(None)

    reader = threading.Thread(target=pump, daemon=True)
    reader.start()

    started = time.monotonic()
    last_progress = started
    while True:
        now = time.monotonic()
        deadline = OCR_CHUNK_TIMEOUT if pages_done else OCR_FIRST_CHUNK_TIMEOUT
        if now - last_progress > deadline:
            stalled = True
            break
        if now - started > OCR_SUBPROCESS_TIMEOUT:
            stalled = True
            break
        try:
            line = inbox.get(timeout=0.2)
        except queue.Empty:
            continue
        if line is None:
            break
        reply = _parse_ocr_worker_reply(line)
        if reply is None:
            if junk is None and line.strip():
                junk = line.strip()[:120]
            continue
        junk = None
        last_progress = time.monotonic()
        kind = reply.get("kind")
        if kind == "unsupported":
            unsupported = True
            break
        if kind == "meta":
            page_count = int(reply.get("page_count") or 0)
        elif kind == "chunk":
            parts.append(str(reply.get("text") or ""))
            pages_done = int(reply.get("through_page") or pages_done)

    # Deliberately no stdout.close() or reader.join() here. On a stall the
    # reader thread is blocked in readline() holding the buffered-reader lock,
    # so closing from this thread deadlocks against it (observed 2026-09-03:
    # a refresh sat for over two hours with the stall already detected). The
    # child must be killed first, which is the caller's finally block; only
    # then does readline() return and the pipe become safe to close.
    return _OcrOutcome(
        parts=parts,
        page_count=page_count,
        pages_done=pages_done,
        stalled=stalled,
        unsupported=unsupported,
        junk=junk,
        reader=reader,
    )


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
    if retry_failed and not extraction_succeeded(str(row[2])):
        return False
    return True


def _delete_missing_documents(
    conn: sqlite3.Connection,
    seen_source_paths: set[str],
    roots: list[Path],
) -> int:
    """Delete stale rows, scoped to the roots this refresh actually walked.

    A narrowed-root refresh must never touch rows under other roots: deleting
    index-wide based on a partial walk wiped the whole index (2026-09-02).
    """
    deleted = 0
    root_strs = {str(root) for root in roots}
    for doc_id, source_root, source_path in conn.execute(
        "SELECT id, source_root, source_path FROM documents"
    ).fetchall():
        if source_root not in root_strs:
            continue
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
    last_commit = time.monotonic()
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
            # A full OCR pass runs for hours; commit on a clock rather than a
            # file count so an interruption costs at most one interval either
            # way — thousands of instant text files or one slow scanned book.
            if time.monotonic() - last_commit >= REFRESH_COMMIT_SECONDS:
                conn.commit()
                last_commit = time.monotonic()
        if limit is None:
            deleted = _delete_missing_documents(
                conn, seen_source_paths, available_roots
            )
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


class LibraryFoldersSearchTimeout(RuntimeError):
    """Raised when an FTS5 search exceeds its wall-clock time budget.

    A single common term (a stopword, or one word of an unquoted multi-word
    phrase) can force SQLite to score and sort a large fraction of a
    multi-gigabyte index before ORDER BY/LIMIT can trim it, which blocks for
    minutes instead of seconds. We abort via ``set_progress_handler`` rather
    than let the caller (an agent's foreground shell call) hang past its own
    timeout with no diagnostic.
    """


_SEARCH_TIMEOUT_SECONDS = 20.0
_SEARCH_PROGRESS_STEPS = 1000


def _search_rows(
    conn: sqlite3.Connection,
    query: str,
    limit: int,
    *,
    timeout: float | None = _SEARCH_TIMEOUT_SECONDS,
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

    def _run(match_query: str) -> list[sqlite3.Row]:
        timed_out = False
        if timeout is not None:
            deadline = time.monotonic() + timeout

            def _check_deadline() -> int:
                nonlocal timed_out
                if time.monotonic() >= deadline:
                    timed_out = True
                    return 1
                return 0

            conn.set_progress_handler(_check_deadline, _SEARCH_PROGRESS_STEPS)
        try:
            return list(conn.execute(sql, (match_query, limit)).fetchall())
        except sqlite3.OperationalError:
            if timed_out:
                raise LibraryFoldersSearchTimeout(
                    f"search timed out after {timeout:.0f}s — query "
                    f"{match_query!r} is too broad (a stopword or common short "
                    "phrase forces a full scan of a large index); narrow the "
                    "query to more specific or additional terms"
                ) from None
            raise
        finally:
            if timeout is not None:
                conn.set_progress_handler(None, 0)

    try:
        return _run(query)
    except LibraryFoldersSearchTimeout:
        raise
    except sqlite3.OperationalError:
        return _run(_safe_fts_query(query))


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


_SOURCE_PROBE_TIMEOUT = 2.0


def _exists_probe(path: Path, timeout: float) -> bool | None:
    """`path.exists()` bounded by a wall clock. None means the probe hung.

    A stat against an offline or hung network mount blocks for the mount's own
    timeout, which no SQLite-level guard can bound — the probe runs in a daemon
    thread so a stuck stat cannot hold up the caller.
    """
    result: list[bool | None] = []

    def _probe() -> None:
        try:
            result.append(path.exists())
        except FileNotFoundError:
            result.append(False)
        except OSError:
            # EACCES/EIO/ESTALE on a flaky mount says the volume is unhappy,
            # not that the file is gone — report unknown rather than absent.
            result.append(None)

    thread = threading.Thread(target=_probe, daemon=True)
    thread.start()
    thread.join(timeout)
    if thread.is_alive():
        return None
    return result[0] if result else False


def _source_availability(
    rows: list[sqlite3.Row], timeout: float
) -> dict[str, bool | None]:
    """Probe each distinct source root once, not once per hit.

    Returns root → reachable (None when the probe timed out). The per-hit stat
    is only safe once its root is known to answer; on an unreachable volume a
    broad search would otherwise stat every candidate row in turn and block for
    minutes with no diagnostic (the FTS timeout guard covers only the query).
    """
    state: dict[str, bool | None] = {}
    for row in rows:
        root = str(row["source_root"])
        if root not in state:
            state[root] = _exists_probe(Path(root), timeout)
    return state


def _hit_source_available(
    row: sqlite3.Row, root_reachable: dict[str, bool | None], timeout: float
) -> bool | None:
    """Is this hit's file on disk? None when its volume can't be reached.

    The per-hit stat is bounded too, not just the root probe: a mount that
    answered a moment ago can drop mid-loop, which would otherwise put us back
    to blocking once per hit. A hit whose own stat times out demotes its root
    for the rest of the call, so the worst case stays one timeout per root
    rather than one per row.
    """
    root = str(row["source_root"])
    reachable = root_reachable.get(root)
    if reachable is None:
        return None
    if reachable is False:
        return False
    available = _exists_probe(Path(str(row["source_path"])), timeout)
    if available is None:
        root_reachable[root] = None
    return available


def search(
    query: str,
    config: LibraryFoldersConfig | None = None,
    *,
    limit: int = 20,
    include_duplicates: bool = False,
    timeout: float | None = _SEARCH_TIMEOUT_SECONDS,
    source_timeout: float = _SOURCE_PROBE_TIMEOUT,
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
            rows = _search_rows(conn, query, candidate_limit, timeout=timeout)
        except sqlite3.Error:
            return []
    root_reachable = _source_availability(rows, source_timeout)
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
                "source_available": _hit_source_available(
                    row, root_reachable, source_timeout
                ),
            }
        )
        if len(hits) >= limit:
            break
    return hits
