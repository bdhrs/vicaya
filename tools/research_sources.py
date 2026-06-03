"""Source helpers for the /vicaya skill.

Five functions that the skill calls in sequence:
    search_vault         - Obsidian vault full-text search
    search_canon         - SQL search across CST + translations
    resolve_citation     - Book-code + paranum -> human-readable sutta reference
    search_calibre       - Calibre library search (metadata always, FTS if indexed)
    gemini_cross_check   - Pipe a synthesis to Gemini for a second opinion

Each helper subprocesses the relevant CLI tool. Returns plain Python data; no printing.
Empty lists on no-results. Raises on tool-missing.
"""

from __future__ import annotations

import fcntl
import fnmatch
import json
import os
import re as _re
import sqlite3
import subprocess
import unicodedata
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Literal


def _strip_diacritics(s: str) -> str:
    """Strip combining marks. Used for Calibre searches (ASCII Pāḷi convention).

    Canon db and Obsidian vault retain exact diacritics; do not strip there.
    """
    return "".join(
        c for c in unicodedata.normalize("NFD", s) if not unicodedata.combining(c)
    )


# CST text columns carry inline TEI/XML markup (<hi rend="...">, <pb/>, <note>, etc.)
# Strip all tags, decode common entities, and collapse whitespace before returning hits.
_XML_TAG_RE = _re.compile(r"<[^>]+>")
_XML_ENTITY_MAP = {"&amp;": "&", "&lt;": "<", "&gt;": ">", "&quot;": '"', "&apos;": "'"}


def _strip_xml(s: str) -> str:
    if not s:
        return s
    out = _XML_TAG_RE.sub("", s)
    for k, v in _XML_ENTITY_MAP.items():
        out = out.replace(k, v)
    return _re.sub(r"\s+", " ", out).strip()


# ---------- Configuration ----------
#
# All user-specific paths are configurable via environment variables.
# A `.env` file in the project root is loaded automatically (KEY=value lines, no
# quotes required, # for comments). See `.env.example` for the full schema.

_REPO_ROOT = Path(__file__).resolve().parent.parent


def _load_dotenv(path: Path = _REPO_ROOT / ".env") -> None:
    if not path.exists():
        return
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            continue
        key, _, val = line.partition("=")
        key = key.strip()
        val = val.strip().strip('"').strip("'")
        os.environ.setdefault(key, val)


_load_dotenv()


def _env_path(key: str, default: str | None = None) -> Path | None:
    val = os.environ.get(key, default)
    return Path(os.path.expanduser(val)) if val else None


DEFAULT_VAULT_NAME = os.environ.get("VICAYA_VAULT_NAME", "Obsidian")
DEFAULT_VAULT_PATH = _env_path("VICAYA_VAULT_PATH", "~/Obsidian")
DEFAULT_CALIBRE_LIBRARY = _env_path("VICAYA_CALIBRE_LIBRARY")
DEFAULT_CANON_DB = _env_path("VICAYA_CANON_DB")
DEFAULT_DPD_DB = _env_path("VICAYA_DPD_DB")
DEFAULT_EBC_VAULT_PATH = _env_path(
    "VICAYA_EBC_VAULT_PATH",
    "~/MyFiles/2_Resources/Early Buddhist Connections",
)
DEFAULT_GRETIL_PATH = _env_path(
    "VICAYA_GRETIL_PATH",
    "~/MyFiles/2_Resources/gretil",
)
DEFAULT_SC_DATA_PATH = _env_path("VICAYA_SC_DATA_PATH")

# CST text-type suffix → label used in fallback citations.
_TEXT_TYPE_LABELS: dict[str, str] = {
    "mul": "mūla",
    "att": "aṭṭhakathā",
    "tik": "ṭīkā",
    "nrf": "non-canonical",
}

# Fallback prefix map for when sutta_info lookup is unavailable.
_PITAKA_PREFIX_MAP: dict[str, str] = {
    "vin": "Vinaya",
    "s01": "DN",
    "s02": "MN",
    "s03": "SN",
    "s04": "AN",
    "s05": "KN",
    "abh": "Abh",
    "e": "Extra",
}


@dataclass
class VaultHit:
    path: str
    snippet: str
    line: int | None = None


@dataclass
class CanonHit:
    book_code: str
    paranum: str
    pali: str
    english: str


@dataclass
class Citation:
    machine: str
    human: str
    pitaka: str
    text_type: str
    paranum: str


@dataclass
class CalibreHit:
    book_id: int
    title: str
    authors: str
    tags: list[str]
    location: str = ""
    snippet: str = ""


@dataclass
class YouTubeHit:
    video_id: str
    title: str
    channel: str
    channel_id: str
    duration: float | None
    url: str
    tier: str = "probationary"  # trusted | probationary | excluded


@dataclass
class YouTubeTranscript:
    video_id: str
    lang: str
    is_auto: bool
    segments: list[dict]  # [{"start": float, "duration": float, "text": str}, ...]
    fetched: str  # ISO-8601 date


@dataclass
class EBCOverview:
    code: str
    path: str
    pts: str = ""
    titles: list[str] = None  # type: ignore[assignment]
    nikaya: list[str] = None  # type: ignore[assignment]
    chapter: list[str] = None  # type: ignore[assignment]
    themes: list[str] = None  # type: ignore[assignment]
    topics: list[str] = None  # type: ignore[assignment]
    training: list[str] = None  # type: ignore[assignment]
    formula: list[str] = None  # type: ignore[assignment]
    audience: list[str] = None  # type: ignore[assignment]
    teacher: list[str] = None  # type: ignore[assignment]
    parallels_agama: list[str] = None  # type: ignore[assignment]
    parallels_partial: list[str] = None  # type: ignore[assignment]


# ---------- Vault search ----------


def search_vault(
    query: str,
    vault: str = DEFAULT_VAULT_NAME,
    folder: str | None = None,
    limit: int = 20,
) -> list[VaultHit]:
    """Run `obsidian search:context` and parse JSON output.

    Returns up to `limit` hits, each with file path and a snippet of matching context.
    """
    cmd = ["obsidian", f"vault={vault}", "search:context", f"query={query}", "format=json"]
    if folder:
        cmd.append(f"path={folder}")
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
    if result.returncode != 0 or not result.stdout.strip():
        return []
    try:
        data = json.loads(result.stdout)
    except json.JSONDecodeError:
        return []
    hits: list[VaultHit] = []
    # Output shape: list of {file, matches: [{line, text}, ...]}
    if isinstance(data, list):
        for item in data:
            if isinstance(item, dict):
                # Obsidian CLI uses 'file'; tolerate 'path' too.
                path = item.get("file") or item.get("path", "")
                matches = item.get("matches") or [
                    {"text": item.get("snippet", ""), "line": None}
                ]
                for m in matches:
                    hits.append(
                        VaultHit(path=path, snippet=m.get("text", ""), line=m.get("line"))
                    )
                    if len(hits) >= limit:
                        return hits
    return hits[:limit]


# ---------- Canon search ----------


def _list_canon_tables(db_path: Path) -> list[str]:
    with sqlite3.connect(db_path) as conn:
        rows = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
        ).fetchall()
    return [r[0] for r in rows]


def _resolve_books(books: list[str] | None, db_path: Path) -> list[str]:
    """Expand book specifiers to actual table names.

    Specifiers may be:
    - Exact table names (e.g. 's0101m_mul')
    - Prefix patterns ending in '*' (e.g. 's*' = all sutta tables, 's02*' = all MN tables)
    - None -> default to all sutta mula tables (`s*_mul`)
    """
    all_tables = _list_canon_tables(db_path)
    if books is None:
        return [t for t in all_tables if t.startswith("s") and t.endswith("_mul")]
    out: list[str] = []
    for spec in books:
        if "*" in spec or "?" in spec:
            out.extend(t for t in all_tables if fnmatch.fnmatchcase(t, spec))
        elif spec in all_tables:
            out.append(spec)
    # Dedupe, preserve order.
    seen: set[str] = set()
    result: list[str] = []
    for t in out:
        if t not in seen:
            seen.add(t)
            result.append(t)
    return result


def search_canon(
    query: str,
    books: list[str] | None = None,
    lang: Literal["pali", "english", "any"] = "pali",
    limit: int = 20,
    db_path: Path | None = None,
) -> list[CanonHit]:
    """Federated LIKE search across CST tables.

    `lang` controls which column(s) are searched. Returns up to `limit` hits.
    """
    db_path = db_path or DEFAULT_CANON_DB
    if db_path is None or not db_path.exists():
        return []
    tables = _resolve_books(books, db_path)
    if not tables:
        return []

    if lang == "any":
        cols = ["pali_text", "english_translation"]
    elif lang == "pali":
        cols = ["pali_text"]
    elif lang == "english":
        cols = ["english_translation"]
    else:
        raise ValueError(f"unknown lang: {lang}")

    pattern = f"%{query}%"
    hits: list[CanonHit] = []
    with sqlite3.connect(db_path) as conn:
        for table in tables:
            where = " OR ".join(f"{c} LIKE ?" for c in cols)
            sql = (
                f"SELECT paranum, pali_text, english_translation "
                f"FROM {table} WHERE {where} LIMIT ?"
            )
            remaining = limit - len(hits)
            if remaining <= 0:
                break
            params = [pattern] * len(cols) + [remaining]
            try:
                rows = conn.execute(sql, params).fetchall()
            except sqlite3.OperationalError:
                continue
            for paranum, pali, english in rows:
                hits.append(
                    CanonHit(
                        book_code=table,
                        paranum=str(paranum or ""),
                        pali=_strip_xml(pali or ""),
                        english=_strip_xml(english or ""),
                    )
                )
                if len(hits) >= limit:
                    break
    return hits


# ---------- Citation resolution ----------


def _book_code_parts(book_code: str) -> tuple[str, str]:
    """Split 's0202m_mul' → ('s0202m', 'mul'). Returns ('', '') on no match."""
    for tt in _TEXT_TYPE_LABELS:
        suffix = f"_{tt}"
        if book_code.endswith(suffix):
            return book_code[: -len(suffix)], tt
    return book_code, ""


def _lookup_sutta_info(
    cst_stem: str, cst_type: str, paranum_int: int, db_path: Path
) -> tuple[str, str] | None:
    """Query sutta_info for the DPD code and sutta name at a given paranum.

    Returns (dpd_code, sutta_name) e.g. ('MN60', 'Apaṇṇakasuttaṃ'), or None.
    Prefers single-sutta entries (shortest dpd_code) over book-range entries.
    """
    if not db_path.exists():
        return None
    pattern = f"%{cst_stem}.{cst_type}%"
    sql = """
        SELECT dpd_code, cst_sutta
        FROM sutta_info
        WHERE cst_file LIKE ?
          AND CAST(cst_paranum AS INTEGER) <= ?
        ORDER BY CAST(cst_paranum AS INTEGER) DESC, LENGTH(dpd_code) ASC
        LIMIT 1
    """
    try:
        with sqlite3.connect(db_path) as conn:
            row = conn.execute(sql, (pattern, paranum_int)).fetchone()
    except sqlite3.Error:
        return None
    if not row:
        return None
    dpd_code, raw_sutta = row
    # Strip leading ordinal: "10. Apaṇṇakasuttaṃ" → "Apaṇṇakasuttaṃ"
    sutta_name = _re.sub(r"^\d+\.\s+", "", raw_sutta or "").strip()
    return dpd_code, sutta_name


def _fallback_human(stem: str, text_type: str, paranum: str) -> tuple[str, str]:
    """Produce a fallback (human_label, pitaka) when sutta_info is unavailable."""
    matched_prefix = ""
    nikaya_label = ""
    pitaka_label = ""
    for prefix, label in _PITAKA_PREFIX_MAP.items():
        if stem.startswith(prefix) and len(prefix) > len(matched_prefix):
            matched_prefix = prefix
            if prefix.startswith("s") and len(prefix) > 1:
                nikaya_label = label
                pitaka_label = "Sutta"
            elif prefix == "vin":
                pitaka_label = "Vinaya"
            elif prefix == "abh":
                pitaka_label = "Abhidhamma"
            elif prefix == "e":
                pitaka_label = "Extra"
    rest = stem[len(matched_prefix):] if matched_prefix else stem
    digits = ""
    for ch in rest:
        if ch.isdigit():
            digits += ch
        else:
            break
    short_label = nikaya_label or pitaka_label or "?"
    book_num = digits or rest or ""
    core = f"{short_label} {book_num} §{paranum}" if book_num else f"{short_label} §{paranum}"
    tt_label = _TEXT_TYPE_LABELS.get(text_type, "")
    human = f"{core} ({tt_label})" if tt_label and tt_label != "mūla" else core
    return human, pitaka_label or "Unknown"


def resolve_citation(
    book_code: str, paranum: str, dpd_db: Path | None = None
) -> Citation:
    """Map a CST table name + paranum to a human-readable reference.

    Uses the sutta_info table in dpd.db for precise sutta names and DPD codes.
    Falls back to a basic label when the DB is unavailable or the lookup misses.

    Examples:
        ('s0202m_mul', '97')   → 'MN60 Apaṇṇakasuttaṃ para 97'
        ('s0402m2_mul', '66')  → 'AN3.65 Kesamuttisuttaṃ para 66'
        ('s0202a_att', '92')   → 'MNa60 para 92'
    """
    machine = f"{book_code}:{paranum}"
    stem, text_type = _book_code_parts(book_code)
    db_path = dpd_db or DEFAULT_DPD_DB

    # Parse paranum: may be "97", "97-99", or "_subhead" etc.
    para_match = _re.match(r"(\d+)(?:-(\d+))?", paranum)
    if para_match and db_path is not None:
        first_para = int(para_match.group(1))
        para_display = paranum.replace("-", "–")  # en-dash for ranges

        tt_label = _TEXT_TYPE_LABELS.get(text_type, text_type)

        if text_type == "mul":
            result = _lookup_sutta_info(stem, "mul", first_para, db_path)
            if result:
                dpd_code, sutta_name = result
                human = f"{dpd_code} {sutta_name} para {para_display}"
                return Citation(
                    machine=machine, human=human,
                    pitaka="Sutta", text_type=tt_label, paranum=paranum,
                )

        elif text_type in ("att", "tik"):
            # Derive sutta from the mūla equivalent (same stem, replace a→m or t→m)
            mula_stem = stem[:-1] + "m" if stem[-1] in ("a", "t") else stem
            result = _lookup_sutta_info(mula_stem, "mul", first_para, db_path)
            if result:
                dpd_code, _ = result
                suffix = "a" if text_type == "att" else "t"
                nikaya = _re.match(r"([A-Z]+)", dpd_code)
                sutta_num = dpd_code[len(nikaya.group(1)):] if nikaya else ""
                commentary_code = f"{nikaya.group(1)}{suffix}{sutta_num}" if nikaya else f"{dpd_code}{suffix}"
                human = f"{commentary_code} para {para_display}"
                return Citation(
                    machine=machine, human=human,
                    pitaka="Commentary", text_type=tt_label, paranum=paranum,
                )

    # Fallback
    human, pitaka = _fallback_human(stem, text_type, paranum)
    return Citation(
        machine=machine, human=human,
        pitaka=pitaka, text_type=_TEXT_TYPE_LABELS.get(text_type, ""), paranum=paranum,
    )


# ---------- Calibre search ----------


class CalibreUnavailable(RuntimeError):
    """Calibre CLI call failed in a way distinct from "no results".

    Common causes: library locked by the desktop GUI, another `calibredb`
    process holding it, the binary missing, or a timeout. Callers can catch
    this to retry, fall back, or surface a clear error rather than silently
    treating it as zero hits.
    """


_CALIBRE_LOCK_HINTS = (
    "another calibre",
    "is being used by",
    "is locked",
    "database is locked",
    "could not be opened",
)

_CALIBRE_LOCK_FILE = Path("/tmp/vicaya-calibre.lock")
_CALIBRE_FTS_TIMEOUT = 20


def _is_calibre_lock_error(stderr: str) -> bool:
    s = (stderr or "").lower()
    return any(h in s for h in _CALIBRE_LOCK_HINTS)


@contextmanager
def _calibre_serialize(warn_after: float = 30.0, give_up_after: float = 120.0):
    """Cross-process mutex so concurrent vicaya agents don't collide on calibredb.

    calibredb refuses to run if another calibredb (or the Calibre GUI) is active.
    An OS-level flock on a shared sentinel file queues agents fairly — the lock
    is released automatically if a holder crashes.

    Non-blocking poll loop so we can:
      - log the holding PID to stderr once we've waited > `warn_after` seconds,
        making contention visible rather than silent;
      - raise CalibreUnavailable after `give_up_after` seconds rather than
        hanging forever if calibredb is genuinely stuck.
    """
    import sys
    import time
    _CALIBRE_LOCK_FILE.touch(exist_ok=True)
    with open(_CALIBRE_LOCK_FILE, "r+") as fh:
        start = time.monotonic()
        warned = False
        while True:
            try:
                fcntl.flock(fh.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                break
            except BlockingIOError:
                waited = time.monotonic() - start
                if waited > give_up_after:
                    holder = (fh.read() or "").strip() or "unknown"
                    raise CalibreUnavailable(
                        f"calibredb lock held by PID {holder} for >{give_up_after:.0f}s; giving up"
                    )
                if not warned and waited > warn_after:
                    fh.seek(0)
                    holder = (fh.read() or "").strip() or "unknown"
                    print(
                        f"[vicaya] waiting on calibredb lock held by PID {holder} "
                        f"(>{warn_after:.0f}s)…",
                        file=sys.stderr,
                    )
                    warned = True
                time.sleep(0.25)
        try:
            fh.seek(0)
            fh.truncate()
            fh.write(str(os.getpid()))
            fh.flush()
            yield
        finally:
            fh.seek(0)
            fh.truncate()
            fcntl.flock(fh.fileno(), fcntl.LOCK_UN)


def _run_calibre(
    cmd: list[str], timeout: int, retries: int = 3, *, raise_timeout: bool = False
) -> subprocess.CompletedProcess:
    """Run a calibredb command with retry/backoff on lock-style failures.

    Raises CalibreUnavailable on persistent failure (timeout, missing binary,
    or lock not released after retries). Returns the CompletedProcess on
    success — an empty stdout is a legitimate "no results" answer, not an error.
    """
    import time
    delay = 0.5
    last_err = ""
    with _calibre_serialize():
        for attempt in range(retries):
            try:
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
            except FileNotFoundError as e:
                raise CalibreUnavailable(f"calibredb not found: {e}") from e
            except subprocess.TimeoutExpired as e:
                if raise_timeout:
                    raise
                last_err = f"timeout after {timeout}s"
                if attempt + 1 < retries:
                    time.sleep(delay)
                    delay *= 2
                    continue
                raise CalibreUnavailable(last_err) from e
            if result.returncode == 0:
                return result
            last_err = (result.stderr or "").strip().splitlines()[-1:] or ["non-zero exit"]
            last_err = last_err[0] if isinstance(last_err, list) else last_err
            if _is_calibre_lock_error(result.stderr) and attempt + 1 < retries:
                time.sleep(delay)
                delay *= 2
                continue
            raise CalibreUnavailable(last_err)
        raise CalibreUnavailable(last_err or "calibredb failed")


def calibre_library_available(library: Path | None = None) -> tuple[bool, str]:
    """Probe Calibre reachability without invoking FTS snippet search.

    Returns (ok, message). `ok=False` means a search would fail right now —
    typically because the GUI or another agent holds the lock. `ok=True` means
    the library is reachable, not that FTS snippets are available: a broken or
    timed-out FTS index degrades gracefully to metadata search in
    `search_calibre`, so the probe deliberately does not exercise FTS.
    """
    library = library or DEFAULT_CALIBRE_LIBRARY
    if library is None or not library.exists():
        return False, f"library path not set or missing: {library}"
    try:
        cmd = [
            "calibredb",
            "list",
            "--search",
            "*",
            "--fields",
            "id",
            "--for-machine",
            "--limit",
            "1",
            "--library-path",
            str(library),
        ]
        _run_calibre(cmd, timeout=15, retries=1)
        return True, "ok"
    except CalibreUnavailable as e:
        return False, str(e)


def _calibre_fts_available(library: Path) -> bool:
    """Return True only if indexing is enabled AND complete (all books indexed).

    Output format from `calibredb fts_index status`:
        FTS Indexing is enabled
        N of TOTAL books files indexed
    Indexing is complete when N == TOTAL.
    """
    try:
        with _calibre_serialize():
            result = subprocess.run(
                ["calibredb", "fts_index", "status", "--library-path", str(library)],
                capture_output=True,
                text=True,
                timeout=30,
            )
    except subprocess.TimeoutExpired:
        return False
    if result.returncode != 0:
        return False
    out = result.stdout
    if "enabled" not in out.lower():
        return False
    import re
    m = re.search(r"(\d+)\s+of\s+(\d+)", out)
    if not m:
        return False
    indexed, total = int(m.group(1)), int(m.group(2))
    return total > 0 and indexed == total


def search_calibre(
    query: str,
    tags: list[str] | None = None,
    library: Path | None = None,
    limit: int = 20,
    timeout: int | None = None,
) -> list[CalibreHit]:
    """Search the Calibre library.

    If `tags` is given, scope to books with any of those tags (OR).
    If FTS is enabled, run a full-text search; if that exceeds the bounded
    FTS budget, fall back to metadata search without snippets.

    Diacritics are stripped from the query — the Calibre library uses ASCII Pāḷi.
    `timeout` overrides the per-call subprocess budget (used by the fast preflight
    probe); None keeps the generous search defaults.

    Raises CalibreUnavailable on a CLI error (e.g. library locked by the GUI
    or another agent). An empty list means the search ran but matched nothing.
    """
    library = library or DEFAULT_CALIBRE_LIBRARY
    if library is None or not library.exists():
        return []
    query = _strip_diacritics(query)
    metadata_timeout = timeout or 60
    if _calibre_fts_available(library):
        try:
            return _calibre_fts_search(
                query, tags, library, limit, timeout=timeout or _CALIBRE_FTS_TIMEOUT
            )
        except subprocess.TimeoutExpired:
            import sys

            print(
                "[vicaya] Calibre FTS timed out; returned metadata hits without snippets",
                file=sys.stderr,
            )
            return _calibre_hits_without_snippets(
                _calibre_metadata_search(
                    query, tags, library, limit, timeout=metadata_timeout
                )
            )
    return _calibre_metadata_search(query, tags, library, limit, timeout=metadata_timeout)


def _build_tag_search(tags: list[str] | None) -> str:
    if not tags:
        return ""
    # 'tags:"=Buddhism" or tags:"=Pali"' style — exact match on tag name.
    return " or ".join(f'tags:"={t}"' for t in tags)


def _calibre_hits_without_snippets(hits: list[CalibreHit]) -> list[CalibreHit]:
    return [
        CalibreHit(
            book_id=hit.book_id,
            title=hit.title,
            authors=hit.authors,
            tags=list(hit.tags),
            location=hit.location,
            snippet="",
        )
        for hit in hits
    ]


def _calibre_fts_search(
    query: str, tags: list[str] | None, library: Path, limit: int, timeout: int = 120
) -> list[CalibreHit]:
    cmd = [
        "calibredb",
        "fts_search",
        query,
        "--output-format",
        "json",
        "--include-snippets",
        "--library-path",
        str(library),
    ]
    tag_search = _build_tag_search(tags)
    if tag_search:
        cmd.extend(["--restrict-to", f"search:{tag_search}"])
    result = _run_calibre(cmd, timeout=timeout, retries=3, raise_timeout=True)
    if not result.stdout.strip():
        return []
    try:
        rows = json.loads(result.stdout)
    except json.JSONDecodeError:
        return []
    hits: list[CalibreHit] = []
    for row in rows[:limit]:
        hits.append(
            CalibreHit(
                book_id=int(row.get("book_id", 0)),
                title=row.get("title", ""),
                authors=row.get("authors", ""),
                tags=row.get("tags", []) if isinstance(row.get("tags"), list) else [],
                location=str(row.get("formats", row.get("book_id", ""))),
                snippet=row.get("text", row.get("snippet", "")),
            )
        )
    return hits


def _calibre_metadata_search(
    query: str, tags: list[str] | None, library: Path, limit: int, timeout: int = 60
) -> list[CalibreHit]:
    # Calibre's default free-text search hits all fields. Compose as `query (tags:X or tags:Y)`.
    parts: list[str] = []
    if query:
        parts.append(query)
    tag_search = _build_tag_search(tags)
    if tag_search:
        parts.append(f"({tag_search})")
    search_expr = " ".join(parts) if parts else "*"
    cmd = [
        "calibredb",
        "list",
        "--search",
        search_expr,
        "--fields",
        "id,title,authors,tags,comments",
        "--for-machine",
        "--limit",
        str(limit),
        "--library-path",
        str(library),
    ]
    result = _run_calibre(cmd, timeout=timeout)
    if not result.stdout.strip():
        return []
    try:
        rows = json.loads(result.stdout)
    except json.JSONDecodeError:
        return []
    hits: list[CalibreHit] = []
    for row in rows[:limit]:
        hits.append(
            CalibreHit(
                book_id=int(row.get("id", 0)),
                title=row.get("title", ""),
                authors=", ".join(row.get("authors", []))
                if isinstance(row.get("authors"), list)
                else row.get("authors", ""),
                tags=row.get("tags", []) if isinstance(row.get("tags"), list) else [],
                location="",
                snippet=(row.get("comments") or "")[:300],
            )
        )
    return hits


# ---------- YouTube search + transcripts ----------

DEFAULT_CHANNELS_FILE = _REPO_ROOT / "data" / "youtube_channels.md"
DEFAULT_YT_CACHE = _REPO_ROOT / "data" / "youtube_cache"


def load_channel_allowlist(
    path: Path = DEFAULT_CHANNELS_FILE,
) -> dict[str, list[dict]]:
    """Parse the channel allowlist Markdown into three tier lists.

    Returns `{"trusted": [...], "probationary": [...], "excluded": [...]}` where
    each entry is `{"name": str, "channel_id": str | ""}`. Entries in the file
    look like `- Display Name` or `- Display Name | UCxxxxxxxxxxxxxxxxxxxxxx`.
    Unknown headings are ignored; missing file returns empty lists.
    """
    tiers: dict[str, list[dict]] = {"trusted": [], "probationary": [], "excluded": []}
    if not path.exists():
        return tiers
    current: str | None = None
    in_fence = False
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if line.startswith("```"):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        if line.startswith("## "):
            heading = line[3:].strip().lower()
            current = heading if heading in tiers else None
            continue
        if current is None or not line.startswith("- "):
            continue
        body = line[2:].strip()
        if "|" in body:
            name, cid = (s.strip() for s in body.split("|", 1))
        else:
            name, cid = body, ""
        if name:
            tiers[current].append({"name": name, "channel_id": cid})
    return tiers


def _classify_channel(
    channel: str, channel_id: str, allowlist: dict[str, list[dict]]
) -> str:
    """Return tier for a hit. New channels default to 'probationary'."""
    name_lc = (channel or "").strip().lower()
    cid = (channel_id or "").strip()
    for tier in ("excluded", "trusted", "probationary"):
        for entry in allowlist.get(tier, []):
            ename = (entry.get("name") or "").strip().lower()
            ecid = (entry.get("channel_id") or "").strip()
            if ecid and cid and ecid == cid:
                return tier
            if ename and name_lc and ename == name_lc:
                return tier
    return "probationary"


def search_youtube(
    query: str,
    channels: dict[str, list[dict]] | None = None,
    limit: int = 20,
) -> list[YouTubeHit]:
    """Search YouTube via `yt-dlp ytsearchN:`.

    Queries should be in English with Pāḷi sutta names + numeric references as
    anchor terms (see SKILL.md). Channels in the `excluded` tier are filtered
    out; `trusted` and `probationary` pass through with their tier on the hit.

    Pass `channels=load_channel_allowlist()` explicitly or let the helper load
    the default file. Pass `channels={}` to disable filtering entirely.
    """
    allowlist = channels if channels is not None else load_channel_allowlist()
    cmd = [
        "yt-dlp",
        "--flat-playlist",
        "--no-warnings",
        "--print",
        "%(id)s|||%(title)s|||%(channel)s|||%(channel_id)s|||%(duration)s",
        f"ytsearch{int(limit)}:{query}",
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    except subprocess.TimeoutExpired:
        return []
    if result.returncode != 0:
        return []
    hits: list[YouTubeHit] = []
    for line in result.stdout.splitlines():
        parts = line.split("|||")
        if len(parts) < 5:
            continue
        vid, title, channel, channel_id, duration = parts[:5]
        if not vid:
            continue
        try:
            dur = float(duration) if duration and duration != "NA" else None
        except ValueError:
            dur = None
        tier = _classify_channel(channel, channel_id, allowlist)
        if tier == "excluded":
            continue
        hits.append(
            YouTubeHit(
                video_id=vid,
                title=title,
                channel=channel,
                channel_id=channel_id,
                duration=dur,
                url=f"https://youtu.be/{vid}",
                tier=tier,
            )
        )
    return hits


def fetch_youtube_transcript(
    video_id: str,
    cache_dir: Path = DEFAULT_YT_CACHE,
    languages: tuple[str, ...] = ("en",),
) -> YouTubeTranscript | None:
    """Fetch a YouTube transcript, caching to disk.

    Returns the cached transcript if `<cache_dir>/<video_id>.json` exists;
    otherwise fetches via `youtube-transcript-api` and writes the cache.

    Returns `None` if the video has no transcript in any requested language.
    """
    cache_dir.mkdir(parents=True, exist_ok=True)
    cache_file = cache_dir / f"{video_id}.json"
    if cache_file.exists():
        data = json.loads(cache_file.read_text(encoding="utf-8"))
        return YouTubeTranscript(**data)

    try:
        from youtube_transcript_api import YouTubeTranscriptApi
    except ImportError:
        return None

    api = YouTubeTranscriptApi()
    try:
        fetched_list = api.list(video_id)
        # Prefer human-uploaded over auto-generated, in language preference order.
        chosen = None
        is_auto = False
        for lang in languages:
            try:
                chosen = fetched_list.find_manually_created_transcript([lang])
                is_auto = False
                break
            except Exception:
                pass
        if chosen is None:
            for lang in languages:
                try:
                    chosen = fetched_list.find_generated_transcript([lang])
                    is_auto = True
                    break
                except Exception:
                    pass
        if chosen is None:
            return None
        snippets = chosen.fetch()
        segments = [
            {"start": s.start, "duration": s.duration, "text": s.text}
            for s in snippets
        ]
        lang_code = getattr(chosen, "language_code", languages[0])
    except Exception:
        return None

    import datetime as _dt
    transcript = YouTubeTranscript(
        video_id=video_id,
        lang=lang_code,
        is_auto=is_auto,
        segments=segments,
        fetched=_dt.date.today().isoformat(),
    )
    from dataclasses import asdict
    cache_file.write_text(
        json.dumps(asdict(transcript), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return transcript


# ---------- EBC (Early Buddhist Connections) vault ----------

# Nikāya prefixes seen in EBC sutta codes. Used to locate the overview-card
# directory `+Suttas/Overviews Suttas/<NIK>/`. Longest prefixes first so
# `THAG` is matched before `T`.
_EBC_NIKAYA_PREFIXES: tuple[str, ...] = (
    "PDHP", "THAG", "THIG",
    "SNP", "DHP", "ITI",
    "MN", "DN", "SN", "AN",
    "UD",
    "MA", "DA", "EA", "SA",
    "T",
)


def _normalise_sutta_code(s: str) -> str:
    """`mn 10`, `MN-10`, `mn10` → `MN10`. Idempotent on already-normalised codes."""
    return s.strip().upper().replace(" ", "").replace("-", "").replace("_", "")


def _ebc_nikaya_for(code: str) -> str | None:
    for prefix in _EBC_NIKAYA_PREFIXES:
        if code.startswith(prefix):
            return prefix
    return None


def _find_ebc_overview_path(code: str, vault: Path) -> Path | None:
    nik = _ebc_nikaya_for(code)
    if not nik:
        return None
    base = vault / "+Suttas" / "Overviews Suttas" / nik
    if not base.exists():
        return None
    for match in base.rglob(f"{code}.md"):
        return match
    return None


def _parse_ebc_yaml(text: str) -> dict[str, str | list[str]]:
    """Parse the leading `---\\n...\\n---` block.

    Supports scalar `key: "value"` and one-level lists rendered as
    `key:\\n  - "a"\\n  - "b"`. Strips surrounding quotes. Skips everything else.
    """
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return {}
    out: dict[str, str | list[str]] = {}
    current_key: str | None = None
    current_list: list[str] | None = None
    for line in lines[1:]:
        if line.strip() == "---":
            break
        if line.startswith("  - "):
            if current_list is not None:
                current_list.append(line[4:].strip().strip('"').strip("'"))
            continue
        if current_list is not None and current_key is not None:
            out[current_key] = current_list
            current_list = None
            current_key = None
        if ":" not in line:
            continue
        key, _, val = line.partition(":")
        key = key.strip()
        val = val.strip()
        if val == "":
            current_key = key
            current_list = []
        else:
            out[key] = val.strip('"').strip("'")
    if current_list is not None and current_key is not None:
        out[current_key] = current_list
    return out


def _split_parallel_refs(raw: str) -> list[str]:
    """Extract sutta codes from a `parallels_*` value like
    `"[[EA12.1]]; [[MA98]], [[MA31]]"`. Returns a de-duplicated list preserving order.
    """
    if not raw:
        return []
    out: list[str] = []
    seen: set[str] = set()
    buf = ""
    for ch in raw:
        if ch == "[":
            buf = ""
        elif ch == "]":
            ref = buf.strip()
            if ref and ref not in seen:
                seen.add(ref)
                out.append(ref)
            buf = ""
        else:
            buf += ch
    if not out:
        for token in raw.replace(";", ",").split(","):
            ref = token.strip().strip("[]")
            if ref and ref not in seen:
                seen.add(ref)
                out.append(ref)
    return out


def _as_list(v) -> list[str]:
    if v is None:
        return []
    if isinstance(v, list):
        return [str(x) for x in v if str(x).strip()]
    s = str(v).strip()
    return [s] if s else []


def get_ebc_overview(
    code: str,
    vault: Path | None = DEFAULT_EBC_VAULT_PATH,
) -> EBCOverview | None:
    """Return the structured overview card for an EBC sutta, or None if missing."""
    if vault is None:
        return None
    normalised = _normalise_sutta_code(code)
    path = _find_ebc_overview_path(normalised, vault)
    if path is None:
        return None
    yaml = _parse_ebc_yaml(path.read_text(encoding="utf-8"))
    return EBCOverview(
        code=str(yaml.get("sutta_code") or normalised),
        path=str(path),
        pts=str(yaml.get("sutta_pts") or ""),
        titles=_as_list(yaml.get("sutta_title")),
        nikaya=_as_list(yaml.get("nikaya")),
        chapter=_as_list(yaml.get("sutta_chapter")),
        themes=_as_list(yaml.get("sutta_theme")),
        topics=_as_list(yaml.get("sutta_topic")),
        training=_as_list(yaml.get("sutta_training")),
        formula=_as_list(yaml.get("sutta_formula")),
        audience=_as_list(yaml.get("sutta_audience")),
        teacher=_as_list(yaml.get("sutta_teacher")),
        parallels_agama=_split_parallel_refs(str(yaml.get("parallels_agama") or "")),
        # EBC frontmatter uses the (sic) key `parallels_partilal`.
        parallels_partial=_split_parallel_refs(str(yaml.get("parallels_partilal") or "")),
    )


def search_ebc(
    query: str,
    folder: str | None = None,
    vault: Path | None = DEFAULT_EBC_VAULT_PATH,
    limit: int = 20,
) -> list[VaultHit]:
    """Recursive fixed-string grep across the EBC vault (markdown files only).

    Uses `grep -rn -F --include='*.md'` so no ripgrep dependency. ~40ms on
    the full 22k-file vault for a typical Pāḷi query.
    """
    if vault is None or not vault.exists():
        return []
    root = vault / folder if folder else vault
    if not root.exists():
        return []
    cmd = [
        "grep", "-rn", "-F", "-a",
        "--include=*.md",
        "--", query, str(root),
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
    # grep exits 1 when there are no matches; only treat >1 as an error.
    if result.returncode > 1:
        return []
    hits: list[VaultHit] = []
    for line in result.stdout.splitlines():
        # `path:line:text` — `grep -n` always emits two colons before the text.
        parts = line.split(":", 2)
        if len(parts) < 3:
            continue
        path, lineno, text = parts
        snippet = text.strip()
        if len(snippet) > 300:
            snippet = snippet[:297] + "..."
        try:
            line_int: int | None = int(lineno)
        except ValueError:
            line_int = None
        hits.append(VaultHit(path=path, snippet=snippet, line=line_int))
        if len(hits) >= limit:
            break
    return hits


# ---------- Sanskrit (GRETIL) search ----------


def search_sanskrit(
    query: str,
    folder: str | None = None,
    path: Path | None = None,
    limit: int = 20,
) -> list[VaultHit]:
    """Fixed-string grep across the local GRETIL corpus (.htm files, Unicode IAST).

    Use `Path(hit.path).stem` to derive the text name from the file path
    (e.g. `avs___u.htm` → `avs___u`). Files contain IAST text with light HTML
    markup; grep matches cleanly against the text lines.
    Returns [] silently when VICAYA_GRETIL_PATH is unset or the path doesn't exist.
    """
    root_path = path or DEFAULT_GRETIL_PATH
    if root_path is None or not root_path.exists():
        return []
    root = root_path / folder if folder else root_path
    if not root.exists():
        return []
    cmd = [
        "grep", "-rn", "-F", "-a",
        "--include=*.htm",
        "--", query, str(root),
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
    if result.returncode > 1:
        return []
    hits: list[VaultHit] = []
    for line in result.stdout.splitlines():
        parts = line.split(":", 2)
        if len(parts) < 3:
            continue
        hit_path, lineno, text = parts
        snippet = text.strip()
        if len(snippet) > 300:
            snippet = snippet[:297] + "..."
        try:
            line_int: int | None = int(lineno)
        except ValueError:
            line_int = None
        hits.append(VaultHit(path=hit_path, snippet=snippet, line=line_int))
        if len(hits) >= limit:
            break
    return hits


# ---------- SuttaCentral offline archive ----------
#
# Layout under VICAYA_SC_DATA_PATH:
#   relationship/parallels.json          — list of {"parallels": [refs...]}.
#     `~` prefix on a ref means "resemblance" (loose parallel).
#     `#a.b-#c.d` suffix is a paragraph range.
#   sc_bilara_data/root/<lang>/...       — root texts keyed "<uid>:<seg>" → text.
#       langs: pli (Pāḷi), lzh (Literary Chinese / Āgamas), san, pra, en, misc.
#   sc_bilara_data/translation/en/<author>/... — English translations, same keys.
#
# Coverage is partial: MA holds ~15 suttas, EA almost nothing, SA mostly present.
# `sc_parallels` always reports what parallels.json says; text retrieval is
# best-effort and explicitly flags missing texts in `text_gaps`.

_SC_REF_RE = _re.compile(r"^([a-z-]+)(\d+(?:\.\d+)?)?")


@dataclass
class SCParallel:
    ref: str                              # e.g. "ma115" or "ea40.10"
    resemblance: bool = False             # True if listed with `~` prefix
    paragraph_range: str = ""             # e.g. "16.1-18.1" if present, else ""
    text_pali: str = ""
    text_lzh: str = ""
    text_san: str = ""
    text_pra: str = ""
    translation_en: str = ""
    text_gaps: list[str] = None           # type: ignore[assignment]


def _sc_parse_ref(raw: str) -> tuple[str, bool, str]:
    """Split a parallels.json ref into (uid, resemblance, paragraph_range)."""
    resemblance = raw.startswith("~")
    body = raw.lstrip("~")
    if "#" in body:
        uid, _, prange = body.partition("#")
    else:
        uid, prange = body, ""
    return uid.strip(), resemblance, prange.strip()


def _sc_collection_for_uid(uid: str) -> str | None:
    """Guess the collection folder for a uid (e.g. 'ma115' → 'ma', 'mn18' → 'mn')."""
    m = _SC_REF_RE.match(uid)
    if not m:
        return None
    return m.group(1).rstrip("-") or None


def _sc_find_root_file(uid: str, lang: str, sc_root: Path) -> Path | None:
    """Locate a root-text JSON file for a uid under root/<lang>/.

    Tries the most common SC layout: sc_bilara_data/root/<lang>/<source>/sutta/<coll>/<uid>_*.json
    and falls back to any *<uid>_root-<lang>*.json under root/<lang>/.
    """
    base = sc_root / "sc_bilara_data" / "root" / lang
    if not base.exists():
        return None
    coll = _sc_collection_for_uid(uid)
    candidates: list[Path] = []
    if coll:
        for parent in base.rglob(f"sutta/{coll}"):
            candidates.extend(parent.glob(f"{uid}_root-{lang}-*.json"))
            candidates.extend(parent.glob(f"{uid}_root-*.json"))
    if not candidates:
        candidates.extend(base.rglob(f"{uid}_root-{lang}-*.json"))
        candidates.extend(base.rglob(f"{uid}_root-*.json"))
    return candidates[0] if candidates else None


def _sc_find_translation_file(uid: str, sc_root: Path, lang: str = "en") -> Path | None:
    base = sc_root / "sc_bilara_data" / "translation" / lang
    if not base.exists():
        return None
    matches = list(base.rglob(f"{uid}_translation-{lang}-*.json"))
    return matches[0] if matches else None


def _sc_read_segments(path: Path | None) -> str:
    if path is None:
        return ""
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return ""
    if not isinstance(data, dict):
        return ""
    return "\n".join(str(v).strip() for v in data.values() if str(v).strip())


def _sc_load_parallels_index(sc_root: Path) -> dict[str, list[list[str]]]:
    """Read parallels.json and index by bare uid for cheap lookup."""
    path = sc_root / "relationship" / "parallels.json"
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    index: dict[str, list[list[str]]] = {}
    for entry in data:
        refs = entry.get("parallels") if isinstance(entry, dict) else None
        if not isinstance(refs, list):
            continue
        for raw in refs:
            uid, _, _ = _sc_parse_ref(raw)
            index.setdefault(uid, []).append(refs)
    return index


def sc_parallels(
    citation: str,
    sc_root: Path | None = None,
    include_text: bool = True,
) -> list[SCParallel]:
    """Look up parallels for a SuttaCentral-style citation (e.g. 'mn18').

    Returns one SCParallel per parallel ref *other than* the query itself.
    parallels.json coverage is comprehensive; text retrieval is best-effort —
    the archive holds only a partial sample of Chinese Āgamas, so unread
    languages are recorded in `text_gaps` rather than silently omitted.

    `citation` is normalised (lowercased, whitespace stripped). On unknown
    archive path or empty match, returns [].
    """
    sc_root = sc_root or DEFAULT_SC_DATA_PATH
    if sc_root is None or not sc_root.exists():
        return []
    target = (citation or "").strip().lower()
    if not target:
        return []
    index = _sc_load_parallels_index(sc_root)
    groups = index.get(target, [])
    out: list[SCParallel] = []
    seen: set[str] = set()
    for refs in groups:
        for raw in refs:
            uid, resemblance, prange = _sc_parse_ref(raw)
            if uid == target or uid in seen:
                continue
            seen.add(uid)
            parallel = SCParallel(
                ref=uid,
                resemblance=resemblance,
                paragraph_range=prange,
                text_gaps=[],
            )
            if include_text:
                for lang, attr in (("pli", "text_pali"), ("lzh", "text_lzh"),
                                   ("san", "text_san"), ("pra", "text_pra")):
                    if _sc_collection_for_uid(uid) is None:
                        continue
                    p = _sc_find_root_file(uid, lang, sc_root)
                    if p is None:
                        continue
                    setattr(parallel, attr, _sc_read_segments(p))
                t = _sc_find_translation_file(uid, sc_root, "en")
                parallel.translation_en = _sc_read_segments(t)
                if not any([parallel.text_pali, parallel.text_lzh,
                            parallel.text_san, parallel.text_pra]):
                    parallel.text_gaps.append(
                        "no root text in offline archive"
                    )
                if not parallel.translation_en:
                    parallel.text_gaps.append("no en translation in offline archive")
            out.append(parallel)
    return out


def sc_search(
    query: str,
    lang: str = "pli",
    sc_root: Path | None = None,
    limit: int = 20,
) -> list[VaultHit]:
    """Fixed-string grep across SuttaCentral root texts in one language.

    `lang` is the directory under `sc_bilara_data/root/` (pli, lzh, san, pra,
    en, misc). Returns VaultHit-shaped results (path + snippet + line). Hits
    files holding JSON segment dicts — the snippet is the matched line as-is.
    """
    sc_root = sc_root or DEFAULT_SC_DATA_PATH
    if sc_root is None or not sc_root.exists():
        return []
    root = sc_root / "sc_bilara_data" / "root" / lang
    if not root.exists():
        return []
    cmd = ["grep", "-rn", "-F", "-a", "--include=*.json", "--", query, str(root)]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
    except subprocess.TimeoutExpired:
        return []
    if result.returncode > 1:
        return []
    hits: list[VaultHit] = []
    for line in result.stdout.splitlines():
        parts = line.split(":", 2)
        if len(parts) < 3:
            continue
        hit_path, lineno, text = parts
        snippet = text.strip()
        if len(snippet) > 300:
            snippet = snippet[:297] + "..."
        try:
            line_int: int | None = int(lineno)
        except ValueError:
            line_int = None
        hits.append(VaultHit(path=hit_path, snippet=snippet, line=line_int))
        if len(hits) >= limit:
            break
    return hits


# ---------- Gemini cross-check ----------


def gemini_cross_check(prompt: str, timeout: int = 120) -> str:
    """Send a prompt to `gemini -p` and return the text response.

    Returns a '# ERROR: ...' line on timeout or failure so the caller can
    distinguish a rate-limit / quota error from a genuine empty response.
    """
    try:
        result = subprocess.run(
            ["gemini", "--approval-mode", "plan", "-p", prompt],
            capture_output=True,
            text=True,
            timeout=timeout,
        )
    except subprocess.TimeoutExpired:
        return "# ERROR: gemini timed out"
    if result.returncode != 0:
        lines = result.stderr.strip().splitlines()
        # Prefer the human-readable message line if present
        msg_line = next((ln.strip() for ln in lines if ln.strip().startswith("message:")), None)
        reason = msg_line or (lines[-1].strip() if lines else "non-zero exit")
        return f"# ERROR: {reason}"
    return result.stdout.strip()


# ---------- Cross-check (OpenRouter model chain) ----------

_OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
_OPENROUTER_MODELS_PATH = _REPO_ROOT / "data" / "openrouter_models.json"
_OPENROUTER_MAX_MODELS = 3  # OpenRouter API caps the `models` array at 3.
_OPENCODE_AUTH_PATH = Path.home() / ".local" / "share" / "opencode" / "auth.json"


def _load_openrouter_models() -> list[str]:
    try:
        with _OPENROUTER_MODELS_PATH.open("r", encoding="utf-8") as f:
            models = json.load(f).get("models")
        if isinstance(models, list) and all(isinstance(m, str) and m for m in models):
            return models[:_OPENROUTER_MAX_MODELS]
    except (OSError, json.JSONDecodeError):
        pass
    return []


def _load_openrouter_key() -> str | None:
    key = os.environ.get("OPENROUTER_API_KEY")
    if key:
        return key
    try:
        with _OPENCODE_AUTH_PATH.open("r", encoding="utf-8") as f:
            entry = json.load(f).get("openrouter")
    except (OSError, json.JSONDecodeError):
        return None
    if isinstance(entry, dict):
        k = entry.get("key")
        if isinstance(k, str) and k:
            return k
    return None


_SELF_REVIEW_SENTINEL = """# SELF_REVIEW: OpenRouter cross-check unavailable.

Run the Phase 6 checklist on your own synthesis before writing the note.
For each item, either fix the synthesis or note "no issue":

1. Perspective coverage — Are named positions underrepresented or
   mischaracterised? Are major schools, teachers, or scholarly voices
   missing from this topic entirely?
2. Tier integrity — Is any claim attributed to the root canon (mūla) that
   actually originates in the commentarial tradition (aṭṭhakathā / ṭīkā)?
   Is any teacher's interpretation presented as if it were canonical?
3. Citation quality — Are citations precise (book, chapter, paragraph,
   page where applicable)? Any "as the Buddha said" without a sutta ref?
4. Internal consistency — Do the evidence and the analysis agree? Any
   conclusion that the cited passages do not actually support?
5. Overreach — Any claim stated more strongly than the sources warrant?
   Any speculation presented as established fact?
"""


# ---------- Citation verification ----------
#
# Cross-checkers (Phase 6 AI reviewers) sometimes fabricate sutta references or
# misread them. verify_citation queries the sutta_info table in dpd.db to confirm
# a human reference exists. Existence only — no claim about whether the cited
# content matches what the model said about it (that is Phase 2 work).


_CITATION_RE = _re.compile(
    r"\b(DN|MN|SN|AN|SNP|Snp?|Dhp|Ud|Iti|Thag|Thig|Vv|Pv|Bv|Ja|Mil)"
    r"\s?(\d+(?:\.\d+)?(?:-\d+)?)\b",
    _re.IGNORECASE,
)


def _normalise_citation(ref: str) -> list[str]:
    """Return one or more canonical sc_code candidates for an input ref.

    Scholarly convention:
      - `SN` (all caps)      → Saṃyutta Nikāya only.
      - `Sn` / `sn` / `sN`   → ambiguous: Saṃyutta or Suttanipāta. Return both.
      - `Snp` / `SNP` / etc. → Suttanipāta only (any case, since the `p` disambiguates).
    Other prefixes are uppercased verbatim.
    """
    s = "".join(ref.split())
    m = _CITATION_RE.match(s)
    if not m:
        return [s.upper()]
    prefix, tail = m.group(1), m.group(2)
    lo = prefix.lower()
    if prefix == "SN":
        return [f"SN{tail}"]
    if lo == "sn":
        return [f"SN{tail}", f"SNP{tail}"]
    return [f"{lo.upper()}{tail}"]


def verify_citation(ref: str, dpd_db: Path | None = None) -> dict:
    """Confirm that `ref` (a human sutta reference) exists in dpd.db sutta_info.

    Returns {ref, normalised, exists, matches: [...]}. Each match has the
    fields {sc_code, cst_code, sc_eng_sutta, dpd_sutta, cst_file}. Multiple
    matches when the ref is ambiguous (e.g. "Sn 4.8" → both SN and SNP).
    Existence-only — does NOT claim the content matches the reviewer's gloss.
    """
    db_path = dpd_db or DEFAULT_DPD_DB
    if db_path is None or not db_path.exists():
        return {"ref": ref, "normalised": [], "exists": False,
                "matches": [], "error": "dpd.db not available"}
    candidates = _normalise_citation(ref)
    # Query across all five coding systems present in sutta_info:
    # sc_code (SuttaCentral), cst_code (CST Pāḷi), dpd_code (DPD — sometimes
    # book-range like DN1-13, sometimes sutta-code), dpr_code (Digital Pali
    # Reader), bjt_sutta_code (Buddha Jayanthi). A ref may resolve under any.
    sql = (
        "SELECT sc_code, cst_code, dpd_code, dpr_code, bjt_sutta_code, "
        "       sc_eng_sutta, dpd_sutta, cst_file "
        "FROM sutta_info "
        "WHERE sc_code = ? OR cst_code = ? OR dpd_code = ? "
        "   OR dpr_code = ? OR bjt_sutta_code = ?"
    )
    matches: list[dict] = []
    seen: set[tuple] = set()
    try:
        with sqlite3.connect(db_path) as conn:
            for cand in candidates:
                for row in conn.execute(sql, (cand, cand, cand, cand, cand)):
                    key = (row[0], row[1])
                    if key in seen:
                        continue
                    seen.add(key)
                    matches.append({
                        "sc_code": row[0],
                        "cst_code": row[1],
                        "dpd_code": row[2],
                        "dpr_code": row[3],
                        "bjt_sutta_code": row[4],
                        "sc_eng_sutta": row[5],
                        "dpd_sutta": row[6],
                        "cst_file": row[7],
                    })
    except sqlite3.Error as e:
        return {"ref": ref, "normalised": candidates, "exists": False,
                "matches": [], "error": str(e)}
    return {
        "ref": ref,
        "normalised": candidates,
        "exists": bool(matches),
        "matches": matches,
    }


def annotate_citations(text: str, dpd_db: Path | None = None) -> str:
    """Stamp every Pāḷi sutta citation in `text` with [VERIFIED] or [REJECTED].

    The label is existence-only — `[VERIFIED]` means the citation exists in
    sutta_info, NOT that the reviewer's content claim about it is correct.
    Pāḷi-quote verification is separate (deferred Phase 2 work).
    """
    cache: dict[str, bool] = {}

    def _stamp(m: _re.Match) -> str:
        raw = m.group(0)
        if raw in cache:
            label = "[VERIFIED]" if cache[raw] else "[REJECTED — not in sutta_info]"
            return f"{raw} {label}"
        result = verify_citation(raw, dpd_db=dpd_db)
        exists = result.get("exists", False)
        cache[raw] = exists
        if exists:
            return f"{raw} [VERIFIED]"
        return f"{raw} [REJECTED — not in sutta_info]"

    return _CITATION_RE.sub(_stamp, text)


def cross_check(prompt: str, timeout: int = 180) -> str:
    """Cross-check `prompt` via OpenRouter's model chain.

    Returns the model's text on success. On any failure (no key, all models
    unreachable, network error, bad response shape) returns the
    `# SELF_REVIEW:` sentinel so the calling agent can run the checklist on
    its own synthesis instead.

    Model list lives in `data/openrouter_models.json` — edit freely;
    OpenRouter routes server-side via the `models: [...]` field, so the
    first reachable entry wins.
    """
    import urllib.request

    key = _load_openrouter_key()
    models = _load_openrouter_models()
    if not key or not models:
        return _SELF_REVIEW_SENTINEL

    body = json.dumps({
        "models": models,
        "messages": [{"role": "user", "content": prompt}],
    }).encode("utf-8")
    req = urllib.request.Request(
        _OPENROUTER_URL,
        data=body,
        headers={"Authorization": f"Bearer {key}",
                 "Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            payload = json.loads(r.read().decode("utf-8"))
        text = (payload["choices"][0]["message"]["content"] or "").strip()
    except Exception:
        return _SELF_REVIEW_SENTINEL
    if not text:
        return _SELF_REVIEW_SENTINEL
    return annotate_citations(text)


# ---------- CST book translator (sibling dpd-db) ----------

_DPD_REPO_CANDIDATES = (
    _REPO_ROOT.parent / "dpd-db",
    Path.home() / "MyFiles" / "3_Active" / "dpd-db",
)
_cst_translator_module = None


def _load_cst_translator():
    """Import dpd-db's cst_book_translator live from the sibling repo.

    Loaded by file path under a unique module name to avoid colliding with
    vicaya's own `tools` package.
    """
    global _cst_translator_module
    if _cst_translator_module is not None:
        return _cst_translator_module

    import importlib.util
    import sys
    import types

    tried = []
    for repo in _DPD_REPO_CANDIDATES:
        target = repo / "tools" / "cst_book_translator.py"
        tried.append(str(target))
        if not target.exists():
            continue

        # The translator imports `from tools.paths import ProjectPaths`, used
        # only in the `cst_xml_path` property which lookup_book never calls.
        # Inject a stub so the import works regardless of which `tools` package
        # is currently on sys.path (vicaya's, dpd-db's, or none).
        original_tools = sys.modules.get("tools")
        original_tools_paths = sys.modules.get("tools.paths")
        shim_tools = types.ModuleType("tools")
        shim_tools.__path__ = []
        shim_paths = types.ModuleType("tools.paths")
        setattr(shim_paths, "ProjectPaths", lambda *a, **kw: None)  # never called
        sys.modules["tools"] = shim_tools
        sys.modules["tools.paths"] = shim_paths
        try:
            spec = importlib.util.spec_from_file_location(
                "_dpd_cst_book_translator", target
            )
            if spec is None or spec.loader is None:
                continue
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)
        except Exception as e:
            tried[-1] = f"{target}: {e}"
            continue
        finally:
            if original_tools is not None:
                sys.modules["tools"] = original_tools
            else:
                sys.modules.pop("tools", None)
            if original_tools_paths is not None:
                sys.modules["tools.paths"] = original_tools_paths
            else:
                sys.modules.pop("tools.paths", None)
        _cst_translator_module = mod
        return mod

    raise RuntimeError(
        "cst_book_translator not found. Expected dpd-db as a sibling of vicaya. "
        "Looked in:\n  " + "\n  ".join(tried)
    )


def lookup_book(value: str) -> list[dict]:
    """Translate any CST book identifier into the other forms.

    Accepts cst_filename (s0101m.mul), vicaya SQLite-table form (s0101m_mul),
    cst_book_name (Pāḷi title), gui_book_code (dn1), or dpd_book_code (DN/DNa).
    Returns a list of dicts; empty list on no match.
    """
    if not value:
        return []
    translator = _load_cst_translator()

    # The 217 books are identified two equivalent ways:
    #   dot form:        's0101m.mul'  — XML filename stem; what the translator uses.
    #   underscore form: 's0101m_mul'  — what vicaya uses (SQL table names can't contain dots).
    # 1:1 mapping, no semantic difference. Convert underscore input before lookup.
    query = value
    if "." not in value and "_" in value:
        stem, _, suffix = value.rpartition("_")
        if suffix in ("mul", "att", "tik", "nrf") and stem:
            query = f"{stem}.{suffix}"

    matches = translator.translate(query)
    return [
        {
            "cst_filename": b.cst_filename,
            "cst_table": b.cst_filename.replace(".", "_"),
            "cst_book_name": b.cst_book_name,
            "gui_book_code": b.gui_book_code,
            "dpd_book_code": b.dpd_book_code,
        }
        for b in matches
    ]


# ---------- Scratch dossier ----------
#
# Compaction defence: every helper call appends a structured entry to the run's
# scratch file. Phase-end gates are hard-coded checklists; scratch-verify refuses
# to advance past a missing gate. Agents never craft scratch markdown by hand.


_SCRATCH_DIR = Path(__file__).resolve().parents[1] / "data" / "scratch"

# Phases auto-skipped for thematic (non-sutta-anchored) runs.
_AUTO_SKIP_PHASES = ("2.5", "3b")


def _read_state() -> dict:
    try:
        return json.loads((_SCRATCH_DIR / ".active").read_text(encoding="utf-8"))
    except Exception:
        return {}


def _write_state(scratch=None, phase=None) -> None:
    """Persist the active scratch path / phase so they survive between shell calls."""
    try:
        _SCRATCH_DIR.mkdir(parents=True, exist_ok=True)
        state = _read_state()
        if scratch is not None:
            state["scratch"] = str(scratch)
        if phase is not None:
            state["phase"] = str(phase)
        (_SCRATCH_DIR / ".active").write_text(json.dumps(state), encoding="utf-8")
    except Exception:
        pass


# (phase_id, title, expected_evidence)
_SCRATCH_PHASES: list[tuple[str, str, list[str]]] = [
    ("0", "Phase 0 — Request understanding", [
        "question_polished recorded",
        "scope_assumptions recorded",
        "ambiguity_status set (clear|minor_uncertainty|unclear)",
    ]),
    ("1", "Phase 1 — Vault / EBC", [
        "Angle triage recorded (applicable + not-applicable with reasons)",
        "Vault hits list logged",
        "Perspective map: 2–5 positions named (or 'no interpretive dispute')",
        "Counter-perspective search targets logged",
    ]),
    ("2", "Phase 2 — Canon", [
        "Mūla searches logged per applicable Nikāya/text class",
        "Every hit has full pali + english + resolve-citation reference",
        "0-hit queries logged with stems tried",
        "Commentary/ṭīkā searched where doctrinal question",
    ]),
    ("2.5", "Phase 2.5 — SC Parallels", [
        "sc-parallels called for each sutta-anchored citation",
        "text_gaps logged explicitly",
    ]),
    ("3", "Phase 3 — Library", [
        "calibre-check called at phase start",
        "Tag-scoped searches per applicable angle",
        "Author searches for named scholars in perspective map",
        "0-hit queries logged",
    ]),
    ("3b", "Phase 3b — Sanskrit", [
        "GRETIL searched where comparative-religion angle applies (or 'not applicable')",
    ]),
    ("4", "Phase 4 — Web", [
        "Web sources fetched with date + URL + summary",
        "Wisdomlib / SuttaCentral / 84000 checked where applicable",
    ]),
    ("4b", "Phase 4b — YouTube", [
        "Trusted-tier channels queried where modern-teacher angle applies",
        "Transcript segments logged with timestamps",
        "is_auto flagged per transcript",
    ]),
    ("4c", "Phase 4c — WisdomLib", [
        "Terms looked up with tradition + source labels",
    ]),
    ("5", "Phase 5 — Synthesis", [
        "scratch-verify exit 0 confirmed before drafting",
        "Draft pasted under '## Phase 5 — Synthesis draft'",
    ]),
    ("6", "Phase 6 — Cross-check", [
        "Cross-check raw output pasted verbatim (citations pre-annotated)",
        "Every [REJECTED] claim dropped — not integrated",
        "Integrations logged with source attribution",
    ]),
    ("7", "Phase 7 — Note written", [
        "Vault path recorded (sets the path for the [REJECTED] hard gate)",
        "PDF path or 'skipped' recorded",
        "Zero [REJECTED] tags anywhere in the vault note (enforced by gate)",
    ]),
]

_PHASE_INDEX = {pid: (i, title, evidence) for i, (pid, title, evidence) in enumerate(_SCRATCH_PHASES)}


def _scratch_path(slug: str | None = None) -> Path:
    """Resolve the scratch path. Env override > active-state file > slug > error."""
    env = os.environ.get("VICAYA_SCRATCH")
    if env:
        return Path(env)
    state = _read_state().get("scratch")
    if state:
        return Path(state)
    if slug:
        return _SCRATCH_DIR / f"{slug}.md"
    raise ValueError("no scratch path: set VICAYA_SCRATCH, run scratch-init, or pass a slug")


def _run_class(text: str) -> str:
    m = _re.search(r"\*\*Run class:\*\*\s*(\S+)", text)
    return m.group(1) if m else "sutta-anchored"


def scratch_init(slug: str, run_class: str = "sutta-anchored") -> Path:
    """Create the scratch file with header + section skeleton. Idempotent — refuses to overwrite."""
    _SCRATCH_DIR.mkdir(parents=True, exist_ok=True)
    path = _SCRATCH_DIR / f"{slug}.md"
    if path.exists():
        _write_state(path)
        return path
    lines = [
        f"# Vicaya dossier — {slug}",
        "**Question original:** <fill in>",
        "**Question polished:** <fill in>",
        "**Scope assumptions:** <fill in>",
        "**Ambiguity status:** <clear|minor_uncertainty|unclear>",
        f"**Slug:** {slug}",
        f"**Run class:** {run_class}",
        "**Vault note:** <set at Phase 7>",
        "",
        "## Phase log",
        "",
    ]
    for _, title, _ in _SCRATCH_PHASES:
        lines.append(f"## {title}")
        lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")
    _write_state(path, "0")
    return path


def _phase_section_header(phase: str) -> str:
    if phase not in _PHASE_INDEX:
        raise ValueError(f"unknown phase {phase!r}; valid: {list(_PHASE_INDEX)}")
    return f"## {_PHASE_INDEX[phase][1]}"


def _append_under_phase(path: Path, phase: str, block: str) -> None:
    """Append `block` immediately under the named phase's section heading."""
    text = path.read_text(encoding="utf-8")
    header = _phase_section_header(phase)
    if header not in text:
        text = text.rstrip() + f"\n\n{header}\n\n{block.rstrip()}\n"
        path.write_text(text, encoding="utf-8")
        return
    # Insert at the end of the section (before the next "## " or EOF).
    lines = text.splitlines(keepends=True)
    out: list[str] = []
    i = 0
    while i < len(lines):
        out.append(lines[i])
        if lines[i].rstrip() == header:
            i += 1
            # find end of this section
            section_end = i
            while section_end < len(lines) and not lines[section_end].startswith("## "):
                section_end += 1
            # copy section body, then append our block
            out.extend(lines[i:section_end])
            if out and not out[-1].endswith("\n"):
                out.append("\n")
            out.append(block.rstrip() + "\n\n")
            i = section_end
            continue
        i += 1
    path.write_text("".join(out), encoding="utf-8")


def scratch_log(
    phase: str,
    tool: str,
    args: list[str] | None = None,
    summary: str | None = None,
    results_file: Path | None = None,
    hits: int | None = None,
    scratch: Path | None = None,
) -> Path:
    """Append a single structured entry under the named phase."""
    import datetime as _dt
    path = scratch or _scratch_path()
    if not path.exists():
        raise FileNotFoundError(f"scratch not initialised: {path}; run scratch-init <slug>")
    ts = _dt.datetime.now().isoformat(timespec="seconds")
    body = [f"### {ts} · {tool}"]
    if args:
        body.append(f"- args: `{' '.join(args)}`")
    if hits is not None:
        body.append(f"- hits: {hits}")
    if summary:
        body.append(f"- summary: {summary}")
    if results_file is not None and Path(results_file).exists():
        body.append("- results:")
        body.append("```json")
        body.append(Path(results_file).read_text(encoding="utf-8").rstrip())
        body.append("```")
    _append_under_phase(path, phase, "\n".join(body))
    return path


def _gate_marker(phase: str) -> str:
    return f"### PHASE {phase} EXIT GATE"


def scratch_gate(phase: str, scratch: Path | None = None) -> dict:
    """Append the canonical exit-gate checklist for `phase`.

    Refuses if any earlier phase's gate is missing — returns {ok: False, missing: ...}
    without writing.
    """
    import datetime as _dt
    path = scratch or _scratch_path()
    if not path.exists():
        raise FileNotFoundError(f"scratch not initialised: {path}; run scratch-init <slug>")
    if phase not in _PHASE_INDEX:
        raise ValueError(f"unknown phase {phase!r}")
    text = path.read_text(encoding="utf-8")
    idx = _PHASE_INDEX[phase][0]
    # Thematic (non-sutta-anchored) runs auto-skip SC-parallels (2.5) and Sanskrit
    # (3b): inapplicable, so the agent shouldn't hand-log empty searches to pass them.
    if _run_class(text) == "thematic":
        for skip_id in _AUTO_SKIP_PHASES:
            if _PHASE_INDEX[skip_id][0] < idx and _gate_marker(skip_id) not in text:
                stitle = _PHASE_INDEX[skip_id][1]
                _append_under_phase(
                    path, skip_id,
                    f"{_gate_marker(skip_id)}\n- AUTO-SKIPPED (thematic run): "
                    f"{stitle} not applicable to a non-sutta-anchored question.",
                )
                text = path.read_text(encoding="utf-8")
    # Verify every prior phase has a gate.
    for prev_id, prev_title, prev_expected in _SCRATCH_PHASES[:idx]:
        if _gate_marker(prev_id) not in text:
            return {
                "ok": False,
                "missing_phase": prev_id,
                "missing_title": prev_title,
                "expected_evidence": prev_expected,
                "message": (
                    f"cannot write Phase {phase} gate: Phase {prev_id} "
                    f"({prev_title}) gate is missing"
                ),
            }
    # Already gated?
    if _gate_marker(phase) in text:
        return {"ok": True, "phase": phase, "note": "gate already present; not duplicated"}
    # Phase 7 hard gate: scan the vault note for [REJECTED] tags.
    if phase == "7":
        vault_match = _re.search(r"\*\*Vault note:\*\*\s*(.+)", text)
        if vault_match:
            raw = vault_match.group(1).strip()
            if raw and not raw.startswith("<"):
                vault_path = Path(raw)
                if vault_path.exists():
                    note_text = vault_path.read_text(encoding="utf-8")
                    if "[REJECTED" in note_text:
                        offending = [
                            line.strip() for line in note_text.splitlines()
                            if "[REJECTED" in line
                        ][:5]
                        return {
                            "ok": False,
                            "phase": "7",
                            "reason": "vault note contains [REJECTED] tags",
                            "vault_note": str(vault_path),
                            "offending_lines": offending,
                            "message": (
                                "Phase 7 gate refused: the vault note contains "
                                "[REJECTED] citation tags. Remove those claims and "
                                "the inline tags before gating."
                            ),
                        }
    ts = _dt.datetime.now().isoformat(timespec="seconds")
    _, title, evidence = _PHASE_INDEX[phase]
    block_lines = [_gate_marker(phase), f"- timestamp: {ts}", f"- title: {title}"]
    for item in evidence:
        block_lines.append(f"- [ ] {item}")
    _append_under_phase(path, phase, "\n".join(block_lines))
    # Advance the active phase so the next phase's searches auto-log correctly
    # without the agent re-exporting VICAYA_PHASE. Thematic runs skip over the
    # auto-skipped phases so logs land on the next phase actually worked.
    nxt = idx + 1
    if _run_class(text) == "thematic":
        while nxt < len(_SCRATCH_PHASES) and _SCRATCH_PHASES[nxt][0] in _AUTO_SKIP_PHASES:
            nxt += 1
    if nxt < len(_SCRATCH_PHASES):
        _write_state(phase=_SCRATCH_PHASES[nxt][0])
    return {"ok": True, "phase": phase, "title": title}


def scratch_verify(through: str | None = None, scratch: Path | None = None) -> dict:
    """Verify that every phase up to `through` (or the highest gate written) has its gate.

    Returns {ok, missing: [{phase, title, expected_evidence}]}.
    """
    path = scratch or _scratch_path()
    if not path.exists():
        return {"ok": False, "error": f"scratch not initialised: {path}"}
    text = path.read_text(encoding="utf-8")
    # Determine the boundary.
    if through is not None:
        if through not in _PHASE_INDEX:
            return {"ok": False, "error": f"unknown phase {through!r}"}
        upper = _PHASE_INDEX[through][0] + 1
    else:
        upper = 0
        for i, (pid, _, _) in enumerate(_SCRATCH_PHASES):
            if _gate_marker(pid) in text:
                upper = i + 1
    missing = []
    for pid, title, expected in _SCRATCH_PHASES[:upper]:
        if _gate_marker(pid) not in text:
            missing.append({
                "phase": pid,
                "title": title,
                "expected_evidence": expected,
            })
    return {"ok": not missing, "checked_through": upper, "missing": missing}


def scratch_resume(slug: str | None = None, scratch: Path | None = None) -> dict:
    """Print the last gate written and suggest the next phase."""
    path = scratch or _scratch_path(slug)
    if not path.exists():
        return {"ok": False, "error": f"scratch not found: {path}"}
    text = path.read_text(encoding="utf-8")
    last = None
    next_phase = _SCRATCH_PHASES[0][0]
    for i, (pid, title, _) in enumerate(_SCRATCH_PHASES):
        if _gate_marker(pid) in text:
            last = {"phase": pid, "title": title}
            if i + 1 < len(_SCRATCH_PHASES):
                next_phase = _SCRATCH_PHASES[i + 1][0]
            else:
                next_phase = None
    return {"ok": True, "path": str(path), "last_gate": last, "next_phase": next_phase}


def _maybe_autolog(cmd: str, argv: list[str], result_obj) -> None:
    """Append a one-entry log for this helper invocation to the active scratch.

    Scratch path and phase come from VICAYA_SCRATCH/VICAYA_PHASE if set, else the
    active-state file written by scratch-init/scratch-gate. Failures are swallowed —
    auto-logging must never break a search.
    """
    state = _read_state()
    scratch = os.environ.get("VICAYA_SCRATCH") or state.get("scratch")
    if not scratch:
        return
    if cmd in {"scratch-init", "scratch-log", "scratch-gate",
               "scratch-verify", "scratch-resume", "lookup-book"}:
        return
    try:
        import datetime as _dt
        import json as _json
        from dataclasses import asdict as _asdict, is_dataclass as _is_dc
        path = Path(scratch)
        if not path.exists():
            return
        phase = os.environ.get("VICAYA_PHASE") or state.get("phase") or "?"
        ts = _dt.datetime.now().isoformat(timespec="seconds")
        hits: int | None = None
        if isinstance(result_obj, list):
            hits = len(result_obj)
        body = [f"### {ts} · {cmd}"]
        if argv:
            body.append(f"- args: `{' '.join(argv)}`")
        if hits is not None:
            body.append(f"- hits: {hits}")

        def _default(o):
            if _is_dc(o) and not isinstance(o, type):
                return _asdict(o)
            return str(o)
        try:
            payload = _json.dumps(result_obj, ensure_ascii=False, indent=2, default=_default)
            body.append("- results:")
            body.append("```json")
            body.append(payload)
            body.append("```")
        except Exception:
            pass
        if phase in _PHASE_INDEX:
            _append_under_phase(path, phase, "\n".join(body))
        else:
            # Unknown phase: append at end of file.
            with open(path, "a", encoding="utf-8") as fh:
                fh.write("\n" + "\n".join(body) + "\n")
    except Exception:
        return


# ---------- CLI ----------
#
# Thin argparse wrapper so agents can call helpers without `python -c` quoting hell.
# Every subcommand prints a JSON array (or object) to stdout. Errors -> stderr, exit 1.
#
# Examples:
#     uv run tools/research_sources.py search-canon "paṭiccasamuppāda" --books "s*_mul" --limit 10
#     uv run tools/research_sources.py resolve-citation s0201m_mul 23
#     uv run tools/research_sources.py search-vault "paṭiccasamuppāda" --limit 5
#     uv run tools/research_sources.py search-calibre "dependent origination" --tags Buddhism
#     echo "review this synthesis: ..." | uv run tools/research_sources.py gemini-cross-check


def _dump(obj) -> None:
    import sys
    from dataclasses import asdict, is_dataclass

    def _default(o):
        if is_dataclass(o) and not isinstance(o, type):
            return asdict(o)
        raise TypeError(f"not serialisable: {type(o)}")

    json.dump(obj, sys.stdout, ensure_ascii=False, indent=2, default=_default)
    sys.stdout.write("\n")


def _cli() -> int:
    import argparse
    import sys

    p = argparse.ArgumentParser(prog="research_sources")
    sub = p.add_subparsers(dest="cmd", required=True)

    pv = sub.add_parser("search-vault")
    pv.add_argument("query")
    pv.add_argument("--folder", default=None)
    pv.add_argument("--limit", type=int, default=20)

    pc = sub.add_parser("search-canon")
    pc.add_argument("query")
    pc.add_argument("--books", nargs="*", default=None,
                    help="Book specifiers, e.g. 's*_mul' '*_att'. Default: sutta mūla.")
    pc.add_argument("--lang", choices=["pali", "english", "any"], default="pali")
    pc.add_argument("--limit", type=int, default=20)

    pr = sub.add_parser("resolve-citation")
    pr.add_argument("book_code")
    pr.add_argument("paranum")

    pl = sub.add_parser("search-calibre")
    pl.add_argument("query")
    pl.add_argument("--tags", nargs="*", default=None)
    pl.add_argument("--limit", type=int, default=20)

    pg = sub.add_parser("gemini-cross-check",
                        help="Reads prompt from stdin to avoid shell quoting issues.")
    pg.add_argument("--timeout", type=int, default=120)

    pcc = sub.add_parser("cross-check",
                         help="OpenRouter cross-check; falls back to a "
                              "# SELF_REVIEW: sentinel if unreachable. "
                              "Reads prompt from stdin.")
    pcc.add_argument("--timeout", type=int, default=180)

    py = sub.add_parser("search-youtube")
    py.add_argument("query")
    py.add_argument("--limit", type=int, default=20)
    py.add_argument("--no-filter", action="store_true",
                    help="Disable channel allowlist filtering (mostly for debug).")

    pt = sub.add_parser("fetch-transcript")
    pt.add_argument("video_id")
    pt.add_argument("--lang", nargs="*", default=["en"])

    pb = sub.add_parser("lookup-book",
                        help="Translate any CST book identifier into the others.")
    pb.add_argument("value",
                    help="cst_filename (s0101m.mul), table name (s0101m_mul), "
                         "Pāḷi title, gui code (dn1), or DPD code (DN/DNa).")

    peo = sub.add_parser("get-ebc-overview",
                         help="Parse the EBC per-sutta overview card for SUTTA_CODE.")
    peo.add_argument("code", help="Sutta code, e.g. MN10, mn-10, mn 10, DN22, MA98.")

    pes = sub.add_parser("search-ebc",
                         help="Fixed-string grep across the Early Buddhist Connections vault.")
    pes.add_argument("query")
    pes.add_argument("--folder", default=None,
                     help="Restrict to a subfolder of the EBC vault.")
    pes.add_argument("--limit", type=int, default=20)

    pss = sub.add_parser("search-sanskrit",
                         help="Fixed-string grep across the local GRETIL Sanskrit corpus (.txt files).")
    pss.add_argument("query")
    pss.add_argument("--folder", default=None,
                     help="Restrict to a subfolder of the GRETIL corpus (e.g. '1_veda').")
    pss.add_argument("--limit", type=int, default=20)

    sub.add_parser("calibre-check",
                   help="Probe the Calibre library; reports ok or the specific failure "
                        "(e.g. locked by GUI or another agent). Use as a Phase 3 preflight.")

    psp = sub.add_parser("sc-parallels",
                         help="SuttaCentral offline archive: list parallels for a citation "
                              "(e.g. 'mn18') and return text + en translation where present.")
    psp.add_argument("citation")
    psp.add_argument("--no-text", action="store_true",
                     help="Skip text retrieval; report parallel refs only.")

    pscs = sub.add_parser("sc-search",
                          help="Fixed-string grep across SuttaCentral offline root texts.")
    pscs.add_argument("query")
    pscs.add_argument("--lang", default="pli",
                      help="Root-text language: pli, lzh (Chinese Āgamas), san, pra, en, misc.")
    pscs.add_argument("--limit", type=int, default=20)

    psi = sub.add_parser("scratch-init",
                         help="Create the scratch dossier file for a run.")
    psi.add_argument("slug")
    psi.add_argument("--class", dest="run_class", default="sutta-anchored",
                     choices=["sutta-anchored", "thematic"],
                     help="thematic = non-sutta-anchored; auto-skips Phase 2.5/3b gates.")

    psl = sub.add_parser("scratch-log",
                         help="Append a manual entry to the scratch dossier under a phase.")
    psl.add_argument("phase", help="Phase id: 0, 1, 2, 2.5, 3, 3b, 4, 4b, 4c, 5, 6, 7")
    psl.add_argument("tool", help="Tool/source name (free text).")
    psl.add_argument("rest", nargs="*", help="Free-form args / query string (logged verbatim).")
    psl.add_argument("--summary", default=None)
    psl.add_argument("--results", default=None, type=Path,
                     help="Path to a JSON file whose contents will be embedded verbatim.")
    psl.add_argument("--hits", default=None, type=int)

    psg = sub.add_parser("scratch-gate",
                         help="Append the canonical exit-gate checklist for a phase.")
    psg.add_argument("phase")

    psv = sub.add_parser("scratch-verify",
                         help="Verify every prior phase has its exit gate. Exits 1 on failure.")
    psv.add_argument("--through", default=None,
                     help="Check gates through this phase id; default = highest gate written.")

    psr = sub.add_parser("scratch-resume",
                         help="Print the last gate written and the suggested next phase.")
    psr.add_argument("slug", nargs="?", default=None,
                     help="Slug for the scratch file; omit if VICAYA_SCRATCH is set.")

    pvc = sub.add_parser("verify-citation",
                         help="Confirm a human sutta reference exists in dpd.db sutta_info.")
    pvc.add_argument("ref", help='Reference, e.g. "SN 46.42", "MN60", "Sn 4.8".')

    args = p.parse_args()

    result_for_autolog = None
    autolog_argv: list[str] = []

    if args.cmd == "search-vault":
        result_for_autolog = search_vault(args.query, folder=args.folder, limit=args.limit)
        autolog_argv = [args.query] + (["--folder", args.folder] if args.folder else []) + ["--limit", str(args.limit)]
        _dump(result_for_autolog)
    elif args.cmd == "search-canon":
        result_for_autolog = search_canon(args.query, books=args.books, lang=args.lang, limit=args.limit)
        autolog_argv = [args.query] + (["--books"] + list(args.books) if args.books else []) + ["--lang", args.lang, "--limit", str(args.limit)]
        _dump(result_for_autolog)
    elif args.cmd == "resolve-citation":
        result_for_autolog = resolve_citation(args.book_code, args.paranum)
        autolog_argv = [args.book_code, str(args.paranum)]
        _dump(result_for_autolog)
    elif args.cmd == "search-calibre":
        autolog_argv = [args.query] + (["--tags"] + list(args.tags) if args.tags else []) + ["--limit", str(args.limit)]
        try:
            result_for_autolog = search_calibre(args.query, tags=args.tags, limit=args.limit)
        except CalibreUnavailable as e:
            result_for_autolog = {"status": "unavailable", "reason": str(e), "hits": []}
            _dump(result_for_autolog)
            _maybe_autolog(args.cmd, autolog_argv, result_for_autolog)
            return 1
        _dump(result_for_autolog)
    elif args.cmd == "search-youtube":
        channels = {} if args.no_filter else None
        result_for_autolog = search_youtube(args.query, channels=channels, limit=args.limit)
        autolog_argv = [args.query, "--limit", str(args.limit)]
        _dump(result_for_autolog)
    elif args.cmd == "fetch-transcript":
        tr = fetch_youtube_transcript(args.video_id, languages=tuple(args.lang))
        if tr is None:
            print("error: no transcript available", file=sys.stderr)
            return 1
        result_for_autolog = tr
        autolog_argv = [args.video_id, "--lang"] + list(args.lang)
        _dump(tr)
    elif args.cmd == "lookup-book":
        _dump(lookup_book(args.value))
    elif args.cmd == "gemini-cross-check":
        prompt = sys.stdin.read()
        if not prompt.strip():
            print("error: empty prompt on stdin", file=sys.stderr)
            return 1
        text = gemini_cross_check(prompt, timeout=args.timeout)
        result_for_autolog = {"output": text}
        autolog_argv = ["<stdin>"]
        sys.stdout.write(text + "\n")
    elif args.cmd == "cross-check":
        prompt = sys.stdin.read()
        if not prompt.strip():
            print("error: empty prompt on stdin", file=sys.stderr)
            return 1
        text = cross_check(prompt, timeout=args.timeout)
        result_for_autolog = {"output": text}
        autolog_argv = ["<stdin>"]
        sys.stdout.write(text + "\n")
    elif args.cmd == "get-ebc-overview":
        result = get_ebc_overview(args.code)
        if result is None:
            print(f"error: no EBC overview for {args.code!r}", file=sys.stderr)
            return 1
        result_for_autolog = result
        autolog_argv = [args.code]
        _dump(result)
    elif args.cmd == "search-ebc":
        result_for_autolog = search_ebc(args.query, folder=args.folder, limit=args.limit)
        autolog_argv = [args.query] + (["--folder", args.folder] if args.folder else []) + ["--limit", str(args.limit)]
        _dump(result_for_autolog)
    elif args.cmd == "search-sanskrit":
        result_for_autolog = search_sanskrit(args.query, folder=args.folder, limit=args.limit)
        autolog_argv = [args.query] + (["--folder", args.folder] if args.folder else []) + ["--limit", str(args.limit)]
        _dump(result_for_autolog)
    elif args.cmd == "calibre-check":
        ok, msg = calibre_library_available()
        result_for_autolog = {"ok": ok, "message": msg}
        autolog_argv = []
        _dump(result_for_autolog)
        _maybe_autolog(args.cmd, autolog_argv, result_for_autolog)
        return 0 if ok else 1
    elif args.cmd == "sc-parallels":
        result_for_autolog = sc_parallels(args.citation, include_text=not args.no_text)
        autolog_argv = [args.citation] + (["--no-text"] if args.no_text else [])
        _dump(result_for_autolog)
    elif args.cmd == "sc-search":
        result_for_autolog = sc_search(args.query, lang=args.lang, limit=args.limit)
        autolog_argv = [args.query, "--lang", args.lang, "--limit", str(args.limit)]
        _dump(result_for_autolog)
    elif args.cmd == "scratch-init":
        path = scratch_init(args.slug, run_class=args.run_class)
        _dump({
            "ok": True, "path": str(path), "slug": args.slug, "class": args.run_class,
            "pin_for_parallel_runs": f"export VICAYA_SCRATCH={path}",
        })
    elif args.cmd == "scratch-log":
        path = scratch_log(
            args.phase,
            args.tool,
            args=args.rest or None,
            summary=args.summary,
            results_file=args.results,
            hits=args.hits,
        )
        _dump({"ok": True, "path": str(path), "phase": args.phase, "tool": args.tool})
    elif args.cmd == "scratch-gate":
        result = scratch_gate(args.phase)
        _dump(result)
        return 0 if result.get("ok") else 1
    elif args.cmd == "scratch-verify":
        result = scratch_verify(through=args.through)
        _dump(result)
        return 0 if result.get("ok") else 1
    elif args.cmd == "scratch-resume":
        result = scratch_resume(slug=args.slug)
        _dump(result)
        return 0 if result.get("ok") else 1
    elif args.cmd == "verify-citation":
        result = verify_citation(args.ref)
        _dump(result)
        return 0 if result.get("exists") else 1

    _maybe_autolog(args.cmd, autolog_argv, result_for_autolog)
    return 0


if __name__ == "__main__":
    raise SystemExit(_cli())
