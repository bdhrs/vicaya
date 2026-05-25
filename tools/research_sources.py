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

import fnmatch
import json
import os
import sqlite3
import subprocess
import unicodedata
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
    chinese: str = ""


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
    lang: Literal["pali", "english", "chinese", "any"] = "pali",
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
        cols = ["pali_text", "english_translation", "chinese_translation"]
    elif lang == "pali":
        cols = ["pali_text"]
    elif lang == "english":
        cols = ["english_translation"]
    elif lang == "chinese":
        cols = ["chinese_translation"]
    else:
        raise ValueError(f"unknown lang: {lang}")

    pattern = f"%{query}%"
    hits: list[CanonHit] = []
    with sqlite3.connect(db_path) as conn:
        for table in tables:
            where = " OR ".join(f"{c} LIKE ?" for c in cols)
            sql = (
                f"SELECT paranum, pali_text, english_translation, chinese_translation "
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
            for paranum, pali, english, chinese in rows:
                hits.append(
                    CanonHit(
                        book_code=table,
                        paranum=str(paranum or ""),
                        pali=pali or "",
                        english=english or "",
                        chinese=chinese or "",
                    )
                )
                if len(hits) >= limit:
                    break
    return hits


# ---------- Citation resolution ----------

import re as _re


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


def _calibre_fts_available(library: Path) -> bool:
    """Return True only if indexing is enabled AND complete (all books indexed).

    Output format from `calibredb fts_index status`:
        FTS Indexing is enabled
        N of TOTAL books files indexed
    Indexing is complete when N == TOTAL.
    """
    try:
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
) -> list[CalibreHit]:
    """Search the Calibre library.

    If `tags` is given, scope to books with any of those tags (OR).
    If FTS is enabled, run a full-text search; otherwise fall back to metadata search.

    Diacritics are stripped from the query — the Calibre library uses ASCII Pāḷi.
    """
    library = library or DEFAULT_CALIBRE_LIBRARY
    if library is None or not library.exists():
        return []
    query = _strip_diacritics(query)
    if _calibre_fts_available(library):
        return _calibre_fts_search(query, tags, library, limit)
    return _calibre_metadata_search(query, tags, library, limit)


def _build_tag_search(tags: list[str] | None) -> str:
    if not tags:
        return ""
    # 'tags:"=Buddhism" or tags:"=Pali"' style — exact match on tag name.
    return " or ".join(f'tags:"={t}"' for t in tags)


def _calibre_fts_search(
    query: str, tags: list[str] | None, library: Path, limit: int
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
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    except subprocess.TimeoutExpired:
        return []
    if result.returncode != 0 or not result.stdout.strip():
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
    query: str, tags: list[str] | None, library: Path, limit: int
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
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
    except subprocess.TimeoutExpired:
        return []
    if result.returncode != 0 or not result.stdout.strip():
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
        msg_line = next((l.strip() for l in lines if l.strip().startswith("message:")), None)
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
    return text or _SELF_REVIEW_SENTINEL


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
        shim_paths.ProjectPaths = lambda *a, **kw: None  # never called
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
        if is_dataclass(o):
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
    pc.add_argument("--lang", choices=["pali", "english", "chinese", "any"], default="pali")
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

    args = p.parse_args()

    if args.cmd == "search-vault":
        _dump(search_vault(args.query, folder=args.folder, limit=args.limit))
    elif args.cmd == "search-canon":
        _dump(search_canon(args.query, books=args.books, lang=args.lang, limit=args.limit))
    elif args.cmd == "resolve-citation":
        _dump(resolve_citation(args.book_code, args.paranum))
    elif args.cmd == "search-calibre":
        _dump(search_calibre(args.query, tags=args.tags, limit=args.limit))
    elif args.cmd == "search-youtube":
        channels = {} if args.no_filter else None
        _dump(search_youtube(args.query, channels=channels, limit=args.limit))
    elif args.cmd == "fetch-transcript":
        tr = fetch_youtube_transcript(args.video_id, languages=tuple(args.lang))
        if tr is None:
            print("error: no transcript available", file=sys.stderr)
            return 1
        _dump(tr)
    elif args.cmd == "lookup-book":
        _dump(lookup_book(args.value))
    elif args.cmd == "gemini-cross-check":
        prompt = sys.stdin.read()
        if not prompt.strip():
            print("error: empty prompt on stdin", file=sys.stderr)
            return 1
        text = gemini_cross_check(prompt, timeout=args.timeout)
        sys.stdout.write(text + "\n")
    elif args.cmd == "cross-check":
        prompt = sys.stdin.read()
        if not prompt.strip():
            print("error: empty prompt on stdin", file=sys.stderr)
            return 1
        text = cross_check(prompt, timeout=args.timeout)
        sys.stdout.write(text + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(_cli())
