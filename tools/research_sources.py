"""Source helpers for the /vicaya skill.

Five functions that the skill calls in sequence:
    search_vault         - Obsidian vault full-text search
    search_canon         - SQL search across CST + translations
    resolve_citation     - Book-code + paranum -> human-readable sutta reference
    gemini_cross_check   - Pipe a synthesis to Gemini for a second opinion

Each helper subprocesses the relevant CLI tool. Returns plain Python data; no printing.
Empty lists on no-results. Raises on tool-missing.
"""

from __future__ import annotations

import fnmatch
import json
import os
import re as _re
import sqlite3
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

# Ensure repo root is on sys.path so `tools._common` resolves when this file
# is executed directly as a script (not imported as part of the package).
_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from tools._common import (  # noqa: E402
    REPO_ROOT as _REPO_ROOT,
    env_path as _env_path,
    load_dotenv as _load_dotenv,
    strip_xml as _strip_xml,
)

_load_dotenv()


DEFAULT_VAULT_NAME = os.environ.get("VICAYA_VAULT_NAME", "Obsidian")
DEFAULT_VAULT_PATH = _env_path("VICAYA_VAULT_PATH", "~/Obsidian")
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
    if result.returncode != 0:
        raise RuntimeError(f"obsidian CLI exited {result.returncode}: {(result.stderr or result.stdout).strip()}")
    stdout = result.stdout.strip()
    if not stdout:
        return []
    try:
        data = json.loads(stdout)
    except json.JSONDecodeError:
        raise RuntimeError(f"obsidian CLI returned non-JSON (app may not be running): {stdout[:200]}")
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

_TAG_RE = _re.compile(r"<[^>]+>")
_WS_RE = _re.compile(r"\s+")


def _normalise_for_match(text: str) -> str:
    """Make canon text and queries comparable.

    CST rows embed TEI markup mid-phrase (`su<pb ed="V" n="1.0001" />taṃ`),
    store the niggahita as ṃ (queries often arrive with SuttaCentral's ṁ),
    and capitalise sentence-initial words. Raw LIKE silently misses all of
    these — "evaṃ me sutaṃ" matches 123 rows raw but 460 normalised.
    """
    import unicodedata
    text = unicodedata.normalize("NFC", text)
    text = _TAG_RE.sub("", text)
    text = text.replace("ṁ", "ṃ").replace("ŋ", "ṃ")
    return _WS_RE.sub(" ", text).strip().casefold()


def _match_normalised(text, needle: str) -> bool:
    """SQLite UDF: does `needle` (already normalised) occur in `text`?"""
    if not text:
        return False
    return needle in _normalise_for_match(str(text))


def _nearest_preceding_paranum(conn, table: str, row_id: int) -> str:
    """Continuation rows carry no paranum; the nearest preceding numbered
    row is the paragraph they belong to."""
    try:
        row = conn.execute(
            f"SELECT paranum FROM {table} "
            "WHERE id < ? AND paranum IS NOT NULL AND paranum != '' "
            "ORDER BY id DESC LIMIT 1",
            (row_id,),
        ).fetchone()
    except sqlite3.OperationalError:
        return ""
    return str(row[0]) if row and row[0] else ""


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
    """Federated substring search across CST tables on normalised text.

    Matching strips TEI markup, folds niggahita variants (ṁ/ŋ → ṃ),
    collapses whitespace, and ignores case on both the query and the stored
    text, so multi-word phrases match across embedded `<pb/>` tags and
    SuttaCentral-spelled queries match CST storage. Hits on continuation
    rows (no paranum of their own) carry the nearest preceding paranum —
    the paragraph they belong to — ready for `resolve_citation`.

    `lang` controls which column(s) are searched. Returns up to `limit`
    hits. The default book set (`s*_mul`, ~85k rows) scans in ~2-3s.
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

    needle = _normalise_for_match(query)
    if not needle:
        return []
    hits: list[CanonHit] = []
    with sqlite3.connect(db_path) as conn:
        conn.create_function(
            "vicaya_match", 2, _match_normalised, deterministic=True
        )
        for table in tables:
            where = " OR ".join(f"vicaya_match({c}, ?)" for c in cols)
            sql = (
                f"SELECT id, paranum, pali_text, english_translation "
                f"FROM {table} WHERE {where} LIMIT ?"
            )
            remaining = limit - len(hits)
            if remaining <= 0:
                break
            params = [needle] * len(cols) + [remaining]
            try:
                rows = conn.execute(sql, params).fetchall()
            except sqlite3.OperationalError:
                continue
            for row_id, paranum, pali, english in rows:
                paranum_str = str(paranum or "")
                if not paranum_str:
                    paranum_str = _nearest_preceding_paranum(conn, table, row_id)
                hits.append(
                    CanonHit(
                        book_code=table,
                        paranum=paranum_str,
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

# Āgama nikāya → (Dhamma-pearls folder stem, BDK folder stem or None).
# Longest prefixes must be checked first (handled by _EBC_NIKAYA_PREFIXES order).
_AGAMA_FOLDER_MAP: dict[str, tuple[str, str | None]] = {
    "MA": ("ma-patton", "ma-bdk"),
    "DA": ("da-patton", "da-bdk"),
    "EA": ("ea-patton", None),
    "SA": ("sa-patton", None),
    "T":  ("t-patton",  None),
}


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


def _find_agama_path(code: str, vault: Path) -> tuple[Path | None, str]:
    """Return (path, translator_label) for an Āgama code like MA98, EA12.1, SA104.

    Tries Patton (Dhamma pearls) first, then BDK. For SA sub-numbered refs
    (e.g. SA1.167) also checks sa-patton-1 where dots become underscores.
    Returns (None, "") when no file exists on disk.
    """
    nik = _ebc_nikaya_for(code)
    if nik not in _AGAMA_FOLDER_MAP:
        return None, ""
    code_lower = code.lower()
    agama_root = vault / "+Suttas" / "Sutta Texts"
    patton_stem, bdk_stem = _AGAMA_FOLDER_MAP[nik]

    candidates: list[tuple[Path, str]] = [
        (agama_root / "Agamas Dhamma pearls" / patton_stem / f"{code_lower}-patton.md", "Patton"),
    ]
    if nik == "SA" and "." in code_lower:
        code_underscore = code_lower.replace(".", "_")
        candidates.append((
            agama_root / "Agamas Dhamma pearls" / "sa-patton-1" / f"{code_underscore}-unknown.md",
            "Patton",
        ))
    if bdk_stem:
        candidates.append((
            agama_root / "Agamas BDK" / bdk_stem / f"{code_lower}-bdk.md",
            "BDK",
        ))
    for path, translator in candidates:
        if path.exists():
            return path, translator
    return None, ""


def get_agama_texts(
    sutta_code: str,
    vault: Path | None = DEFAULT_EBC_VAULT_PATH,
    max_parallels: int = 5,
) -> dict:
    """Fetch Āgama parallel translations for a sutta.

    Calls get_ebc_overview(), then resolves each parallels_agama code to its
    Patton or BDK file and reads the full text. Returns a dict with:
      sutta_code, parallels_found (list of dicts), parallels_missing (list of codes).
    Codes with no file on disk appear in parallels_missing — never silently dropped.
    """
    if vault is None or not vault.exists():
        return {
            "sutta_code": sutta_code,
            "parallels_found": [],
            "parallels_missing": [],
            "error": "EBC vault not configured",
        }
    overview = get_ebc_overview(sutta_code, vault=vault)
    if overview is None:
        return {
            "sutta_code": sutta_code,
            "parallels_found": [],
            "parallels_missing": [],
            "error": f"no EBC overview for {sutta_code!r}",
        }
    found: list[dict] = []
    missing: list[str] = []
    for code in (overview.parallels_agama or [])[:max_parallels]:
        path, translator = _find_agama_path(code, vault)
        if path is None:
            missing.append(code)
        else:
            found.append({
                "code": code,
                "path": str(path),
                "translator": translator,
                "text": path.read_text(encoding="utf-8"),
            })
    return {
        "sutta_code": overview.code,
        "parallels_found": found,
        "parallels_missing": missing,
    }


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
    r"\b(DN|MN|SN|AN|SNP|Snp?|Dhp|Ud|Iti|Thag|Thig|Vv|Pv|Bv|Ja|Mil|Khp|Kp)"
    r"\s?(\d+(?:\.\d+)?(?:-\d+)?)\b",
    _re.IGNORECASE,
)

# Books whose sutta_info codes carry a different prefix than the scholarly
# abbreviation (book_code column in parentheses).
_PREFIX_ALIASES = {
    "THAG": ["TH"],     # dpd_code uses TH1…TH264 (book_code TH)
    "THIG": ["THI"],
    "KP": ["KHP"],
    "KHP": ["KP"],
}

# Books cited by a global verse number that has no per-verse row in
# sutta_info (Dhp does — its codes are verse ranges — these don't).
_VERSE_NUMBERED_BOOKS = {"SNP", "THAG", "THIG"}

# citation prefix → sutta_info.book_code, for the range-containment scan.
_BOOK_CODE_FOR_PREFIX = {
    "DHP": "DHP", "AN": "AN", "SN": "SN", "MN": "MN", "DN": "DN",
    "SNP": "SNP", "THAG": "TH", "THIG": "THI", "ITI": "ITI", "UD": "UD",
    "JA": "JA", "PV": "PV", "VV": "VV", "KHP": "KHP", "KP": "KHP",
}

_RANGE_CODE_RE = _re.compile(r"^([A-Z]+)(?:(\d+)\.)?(\d+)-(\d+)$")
_SINGLE_CODE_RE = _re.compile(r"^([A-Z]+)(?:(\d+)\.)?(\d+)$")


def _normalise_citation(ref: str) -> list[str]:
    """Return one or more canonical sc_code candidates for an input ref.

    Scholarly convention:
      - `SN` (all caps)      → Saṃyutta Nikāya only.
      - `Sn` / `sn` / `sN`   → ambiguous: Saṃyutta or Suttanipāta. Return both.
      - `Snp` / `SNP` / etc. → Suttanipāta only (any case, since the `p` disambiguates).
    Other prefixes are uppercased verbatim. Prefix aliases (Thag→TH,
    Thig→THI, Kp↔Khp) are appended so refs match the codes sutta_info
    actually stores.
    """
    s = "".join(ref.split())
    m = _CITATION_RE.match(s)
    if not m:
        return [s.upper()]
    prefix, tail = m.group(1), m.group(2)
    lo = prefix.lower()
    if prefix == "SN":
        candidates = [f"SN{tail}"]
    elif lo == "sn":
        candidates = [f"SN{tail}", f"SNP{tail}"]
    else:
        candidates = [f"{lo.upper()}{tail}"]
    for cand in list(candidates):
        head = _re.match(r"^[A-Z]+", cand)
        if head and head.group(0) in _PREFIX_ALIASES:
            rest = cand[len(head.group(0)):]
            for alias in _PREFIX_ALIASES[head.group(0)]:
                candidates.append(f"{alias}{rest}")
    return candidates


def _range_end(start: int, end: int, end_str: str) -> int:
    """Repair truncated range ends like DHP90-00 (meaning 90–100)."""
    while end < start:
        end += 10 ** len(end_str)
    return end


def _row_to_match(row) -> dict:
    return {
        "sc_code": row[0],
        "cst_code": row[1],
        "dpd_code": row[2],
        "dpr_code": row[3],
        "bjt_sutta_code": row[4],
        "sc_eng_sutta": row[5],
        "dpd_sutta": row[6],
        "cst_file": row[7],
    }


_SUTTA_INFO_COLS = (
    "sc_code, cst_code, dpd_code, dpr_code, bjt_sutta_code, "
    "sc_eng_sutta, dpd_sutta, cst_file"
)


def _exact_matches(conn, cand: str) -> list[dict]:
    sql = (
        f"SELECT {_SUTTA_INFO_COLS} FROM sutta_info "
        "WHERE sc_code = ? OR cst_code = ? OR dpd_code = ? "
        "   OR dpr_code = ? OR bjt_sutta_code = ?"
    )
    return [_row_to_match(r) for r in conn.execute(sql, (cand,) * 5)]


def _containment_matches(conn, cand: str) -> list[dict]:
    """Match a single-sutta/verse ref against range-form codes.

    sutta_info stores some books as ranges — `DHP116-128`, `AN2.21-31`,
    `AN8.117-626` — so `Dhp 128` or `AN8.119` never match exactly. Scan the
    book's rows and test numeric containment on sc_code and dpd_code.
    """
    m = _SINGLE_CODE_RE.match(cand)
    if not m:
        return []
    prefix, chapter, num = m.group(1), m.group(2), int(m.group(3))
    book_code = _BOOK_CODE_FOR_PREFIX.get(prefix)
    if book_code is None:
        return []
    sql = f"SELECT {_SUTTA_INFO_COLS} FROM sutta_info WHERE book_code = ?"
    matches = []
    for row in conn.execute(sql, (book_code,)):
        for code in (row[0], row[2]):
            rm = _RANGE_CODE_RE.match(code or "")
            if not rm:
                continue
            r_chapter, r_start = rm.group(2), int(rm.group(3))
            r_end = _range_end(r_start, int(rm.group(4)), rm.group(4))
            if (chapter or None) != (r_chapter or None):
                continue
            if r_start <= num <= r_end:
                matches.append(_row_to_match(row))
                break
    return matches


def _resolve_candidate(conn, cand: str) -> list[dict]:
    """Exact lookup across all five coding systems, then range containment.

    Coding systems: sc_code (SuttaCentral), cst_code (CST Pāḷi), dpd_code
    (DPD — sometimes book-range like DN1-13), dpr_code (Digital Pali
    Reader), bjt_sutta_code (Buddha Jayanthi). A ref may resolve under any.
    """
    matches = _exact_matches(conn, cand)
    if matches:
        return matches
    return _containment_matches(conn, cand)


def _split_range_candidate(cand: str) -> tuple[str, str] | None:
    """`SN48.9-10` → (`SN48.9`, `SN48.10`); `DHP256-272` → (`DHP256`, `DHP272`)."""
    m = _RANGE_CODE_RE.match(cand)
    if not m:
        return None
    prefix, chapter, start, end = m.groups()
    head = f"{prefix}{chapter}." if chapter else prefix
    return (f"{head}{start}", f"{head}{end}")


def verify_citation(ref: str, dpd_db: Path | None = None) -> dict:
    """Confirm that `ref` (a human sutta reference) exists in dpd.db sutta_info.

    Returns {ref, normalised, verdict, exists, matches: [...]}. Verdict is one of:
      - "verified"          — found (exactly, by range containment for
                              range-stored books like Dhp/AN ones-twos, or by
                              resolving both endpoints of a hyphenated range)
      - "unverifiable-form" — a global verse number (Snp/Thag/Thig) that has
                              no per-verse row in sutta_info; cannot be
                              checked, NOT evidence of fabrication
      - "rejected"          — not found under any coding system
    `exists` stays True only for "verified" (backward compatible). Multiple
    matches when the ref is ambiguous (e.g. "Sn 4.8" → both SN and SNP).
    Existence-only — does NOT claim the content matches the reviewer's gloss.
    """
    db_path = dpd_db or DEFAULT_DPD_DB
    if db_path is None or not db_path.exists():
        return {"ref": ref, "normalised": [], "verdict": "rejected",
                "exists": False, "matches": [], "error": "dpd.db not available"}
    candidates = _normalise_citation(ref)
    matches: list[dict] = []
    seen: set[tuple] = set()
    unverifiable_note: str | None = None
    try:
        with sqlite3.connect(db_path) as conn:
            for cand in candidates:
                found = _resolve_candidate(conn, cand)
                if not found:
                    endpoints = _split_range_candidate(cand)
                    if endpoints:
                        lo = _resolve_candidate(conn, endpoints[0])
                        hi = _resolve_candidate(conn, endpoints[1])
                        if lo and hi:
                            found = lo + hi
                for row in found:
                    key = (row["sc_code"], row["cst_code"])
                    if key not in seen:
                        seen.add(key)
                        matches.append(row)
                if not found:
                    m = _SINGLE_CODE_RE.match(cand)
                    if m and m.group(1) in _VERSE_NUMBERED_BOOKS and not m.group(2):
                        unverifiable_note = (
                            f"{cand}: global verse number — sutta_info has no "
                            "per-verse rows for this book; cite by "
                            "chapter.sutta (e.g. Snp 4.14, Thag 16.1) to verify"
                        )
    except sqlite3.Error as e:
        return {"ref": ref, "normalised": candidates, "verdict": "rejected",
                "exists": False, "matches": [], "error": str(e)}
    if matches:
        verdict = "verified"
    elif unverifiable_note:
        verdict = "unverifiable-form"
    else:
        verdict = "rejected"
    result = {
        "ref": ref,
        "normalised": candidates,
        "verdict": verdict,
        "exists": bool(matches),
        "matches": matches,
    }
    if unverifiable_note and not matches:
        result["note"] = unverifiable_note
    return result


_VERDICT_LABELS = {
    "verified": "[VERIFIED]",
    "unverifiable-form": "[UNVERIFIABLE — global verse number, no per-verse "
                         "row in sutta_info; cite by chapter.sutta to verify]",
    "rejected": "[REJECTED — not in sutta_info]",
}


def annotate_citations(text: str, dpd_db: Path | None = None) -> str:
    """Stamp every Pāḷi sutta citation in `text` with its verification verdict.

    [VERIFIED] / [REJECTED — not in sutta_info] / [UNVERIFIABLE — …] for
    global verse numbers (Snp/Thag/Thig) that sutta_info cannot confirm or
    deny. The label is existence-only — `[VERIFIED]` means the citation
    exists in sutta_info, NOT that the reviewer's content claim about it is
    correct. Pāḷi-quote verification is separate (deferred Phase 2 work).
    """
    cache: dict[str, str] = {}

    def _stamp(m: _re.Match) -> str:
        raw = m.group(0)
        if raw not in cache:
            result = verify_citation(raw, dpd_db=dpd_db)
            cache[raw] = result.get("verdict", "rejected")
        return f"{raw} {_VERDICT_LABELS[cache[raw]]}"

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


# ---------- Scratch dossier (delegated to tools/scratch.py) ----------

from tools.scratch import (  # noqa: E402, F401
    _SCRATCH_DIR,
    _AUTO_SKIP_PHASES,
    _run_key,
    _state_file,
    _file_lock,
    _read_state,
    _write_state,
    _STATE_PHASE_UNSET,
    _SCRATCH_PHASES,
    _PHASE_INDEX,
    _next_worked_phase,
    _scratch_path,
    _run_class,
    scratch_init,
    _phase_section_header,
    _append_under_phase,
    scratch_log,
    _gate_marker,
    scratch_gate,
    scratch_verify,
    scratch_resume,
    _maybe_autolog,
)


# ---------- CLI ----------
#
# Thin argparse wrapper so agents can call helpers without `python -c` quoting hell.
# Every subcommand prints a JSON array (or object) to stdout. Errors -> stderr, exit 1.
#
# Examples:
#     uv run tools/research_sources.py search-canon "paṭiccasamuppāda" --books "s*_mul" --limit 10
#     uv run tools/research_sources.py resolve-citation s0201m_mul 23
#     uv run tools/research_sources.py search-vault "paṭiccasamuppāda" --limit 5
#     uv run tools/research_sources.py search-library-folders "dependent origination" --limit 5
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


def _load_library_folders_module():
    import importlib.util
    import sys

    module_path = Path(__file__).with_name("library_folders.py")
    spec = importlib.util.spec_from_file_location("vicaya_library_folders", module_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"could not load library folders module from {module_path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _cli() -> int:
    import argparse
    import sys

    p = argparse.ArgumentParser(prog="research_sources")
    sub = p.add_subparsers(dest="cmd", required=True)

    def _done(
        autolog_argv: list[str] | None = None,
        result_for_autolog: object = None,
        *,
        exit_code: int = 0,
        autolog: bool = True,
    ) -> tuple[int, list[str], object, bool]:
        return exit_code, autolog_argv or [], result_for_autolog, autolog

    def _handle_search_vault(args):
        result = search_vault(args.query, folder=args.folder, limit=args.limit)
        argv = (
            [args.query]
            + (["--folder", args.folder] if args.folder else [])
            + ["--limit", str(args.limit)]
        )
        _dump(result)
        return _done(argv, result)

    def _handle_search_canon(args):
        result = search_canon(
            args.query,
            books=args.books,
            lang=args.lang,
            limit=args.limit,
        )
        argv = (
            [args.query]
            + (["--books"] + list(args.books) if args.books else [])
            + ["--lang", args.lang, "--limit", str(args.limit)]
        )
        _dump(result)
        return _done(argv, result)

    def _handle_resolve_citation(args):
        result = resolve_citation(args.book_code, args.paranum)
        _dump(result)
        return _done([args.book_code, str(args.paranum)], result)

    def _handle_search_youtube(args):
        channels = {} if args.no_filter else None
        result = search_youtube(args.query, channels=channels, limit=args.limit)
        _dump(result)
        return _done([args.query, "--limit", str(args.limit)], result)

    def _handle_fetch_transcript(args):
        tr = fetch_youtube_transcript(args.video_id, languages=tuple(args.lang))
        if tr is None:
            print("error: no transcript available", file=sys.stderr)
            return _done(exit_code=1, autolog=False)
        _dump(tr)
        return _done([args.video_id, "--lang"] + list(args.lang), tr)

    def _handle_lookup_book(args):
        _dump(lookup_book(args.value))
        return _done()

    def _handle_gemini_cross_check(args):
        prompt = sys.stdin.read()
        if not prompt.strip():
            print("error: empty prompt on stdin", file=sys.stderr)
            return _done(exit_code=1, autolog=False)
        text = gemini_cross_check(prompt, timeout=args.timeout)
        sys.stdout.write(text + "\n")
        return _done(["<stdin>"], {"output": text})

    def _handle_cross_check(args):
        prompt = sys.stdin.read()
        if not prompt.strip():
            print("error: empty prompt on stdin", file=sys.stderr)
            return _done(exit_code=1, autolog=False)
        text = cross_check(prompt, timeout=args.timeout)
        sys.stdout.write(text + "\n")
        return _done(["<stdin>"], {"output": text})

    def _handle_get_ebc_overview(args):
        result = get_ebc_overview(args.code)
        if result is None:
            print(f"error: no EBC overview for {args.code!r}", file=sys.stderr)
            return _done(exit_code=1, autolog=False)
        _dump(result)
        return _done([args.code], result)

    def _handle_get_agama(args):
        result = get_agama_texts(args.code, max_parallels=args.max_parallels)
        _dump(result)
        return _done([args.code, "--max", str(args.max_parallels)], result)

    def _handle_search_ebc(args):
        result = search_ebc(args.query, folder=args.folder, limit=args.limit)
        argv = (
            [args.query]
            + (["--folder", args.folder] if args.folder else [])
            + ["--limit", str(args.limit)]
        )
        _dump(result)
        return _done(argv, result)

    def _handle_search_sanskrit(args):
        result = search_sanskrit(args.query, folder=args.folder, limit=args.limit)
        argv = (
            [args.query]
            + (["--folder", args.folder] if args.folder else [])
            + ["--limit", str(args.limit)]
        )
        _dump(result)
        return _done(argv, result)

    def _handle_library_folders_check(_args):
        library_folders = _load_library_folders_module()
        result = library_folders.check()
        _dump(result)
        return _done([], result)

    def _handle_library_folders_refresh(args):
        library_folders = _load_library_folders_module()
        result = library_folders.refresh(
            limit=args.limit,
            retry_failed=args.retry_failed,
        )
        argv = ["--limit", str(args.limit)] if args.limit is not None else []
        if args.retry_failed:
            argv.append("--retry-failed")
        _dump(result)
        return _done(argv, result)

    def _handle_search_library_folders(args):
        library_folders = _load_library_folders_module()
        result = library_folders.search(
            args.query,
            limit=args.limit,
            include_duplicates=args.include_duplicates,
        )
        argv = [args.query, "--limit", str(args.limit)]
        if args.include_duplicates:
            argv.append("--include-duplicates")
        _dump(result)
        return _done(argv, result)

    def _handle_library_folders_duplicates(args):
        library_folders = _load_library_folders_module()
        result = library_folders.duplicates(samples=args.samples)
        _dump(result)
        return _done(["--samples", str(args.samples)], result)

    def _handle_sc_parallels(args):
        result = sc_parallels(args.citation, include_text=not args.no_text)
        argv = [args.citation] + (["--no-text"] if args.no_text else [])
        _dump(result)
        return _done(argv, result)

    def _handle_sc_search(args):
        result = sc_search(args.query, lang=args.lang, limit=args.limit)
        _dump(result)
        return _done([args.query, "--lang", args.lang, "--limit", str(args.limit)], result)

    def _handle_scratch_init(args):
        path = scratch_init(
            args.slug,
            run_class=args.run_class,
            question_original=args.question_original,
            question_polished=args.question_polished,
            scope_assumptions=args.scope_assumptions,
            ambiguity=args.ambiguity,
        )
        gate0_written = "### PHASE 0 EXIT GATE" in path.read_text(encoding="utf-8")
        _dump({
            "ok": True, "path": str(path), "slug": args.slug, "class": args.run_class,
            "phase0_gate": (
                "written — proceed to Phase 1" if gate0_written
                else "NOT written — pass --question-polished, --scope-assumptions "
                     "and --ambiguity, or run scratch-gate 0 after recording them"
            ),
            "isolation": (
                "auto-logging is isolated to this run (keyed to the agent "
                "process); parallel runs never collide — nothing to pin or export"
            ),
        })
        return _done()

    def _handle_scratch_log(args):
        path = scratch_log(
            args.phase,
            args.tool,
            args=args.rest or None,
            summary=args.summary,
            results_file=args.results,
            hits=args.hits,
        )
        _dump({"ok": True, "path": str(path), "phase": args.phase, "tool": args.tool})
        return _done()

    def _handle_scratch_gate(args):
        result = scratch_gate(args.phase)
        _dump(result)
        return _done(exit_code=0 if result.get("ok") else 1, autolog=False)

    def _handle_scratch_verify(args):
        result = scratch_verify(through=args.through)
        _dump(result)
        return _done(exit_code=0 if result.get("ok") else 1, autolog=False)

    def _handle_scratch_resume(args):
        result = scratch_resume(slug=args.slug)
        _dump(result)
        return _done(exit_code=0 if result.get("ok") else 1, autolog=False)

    def _handle_scratch_which(_args):
        try:
            print(_scratch_path())
            return _done(autolog=False)
        except ValueError as e:
            print(e, file=sys.stderr)
            return _done(exit_code=1, autolog=False)

    def _handle_verify_citation(args):
        result = verify_citation(args.ref)
        _dump(result)
        # 0 verified · 2 unverifiable-form (verse number, not fabrication) · 1 rejected
        if result.get("exists"):
            code = 0
        elif result.get("verdict") == "unverifiable-form":
            code = 2
        else:
            code = 1
        return _done(exit_code=code, autolog=False)

    pv = sub.add_parser("search-vault")
    pv.add_argument("query")
    pv.add_argument("--folder", default=None)
    pv.add_argument("--limit", type=int, default=20)
    pv.set_defaults(func=_handle_search_vault)

    pc = sub.add_parser("search-canon")
    pc.add_argument("query")
    pc.add_argument("--books", nargs="*", default=None,
                    help="Book specifiers, e.g. 's*_mul' '*_att'. Default: sutta mūla.")
    pc.add_argument("--lang", choices=["pali", "english", "any"], default="pali")
    pc.add_argument("--limit", type=int, default=20)
    pc.set_defaults(func=_handle_search_canon)

    pr = sub.add_parser("resolve-citation")
    pr.add_argument("book_code")
    pr.add_argument("paranum")
    pr.set_defaults(func=_handle_resolve_citation)

    pg = sub.add_parser("gemini-cross-check",
                        help="Reads prompt from stdin to avoid shell quoting issues.")
    pg.add_argument("--timeout", type=int, default=120)
    pg.set_defaults(func=_handle_gemini_cross_check)

    pcc = sub.add_parser("cross-check",
                         help="OpenRouter cross-check; falls back to a "
                              "# SELF_REVIEW: sentinel if unreachable. "
                              "Reads prompt from stdin.")
    pcc.add_argument("--timeout", type=int, default=180)
    pcc.set_defaults(func=_handle_cross_check)

    py = sub.add_parser("search-youtube")
    py.add_argument("query")
    py.add_argument("--limit", type=int, default=20)
    py.add_argument("--no-filter", action="store_true",
                    help="Disable channel allowlist filtering (mostly for debug).")
    py.set_defaults(func=_handle_search_youtube)

    pt = sub.add_parser("fetch-transcript")
    pt.add_argument("video_id")
    pt.add_argument("--lang", nargs="*", default=["en"])
    pt.set_defaults(func=_handle_fetch_transcript)

    pb = sub.add_parser("lookup-book",
                        help="Translate any CST book identifier into the others.")
    pb.add_argument("value",
                    help="cst_filename (s0101m.mul), table name (s0101m_mul), "
                         "Pāḷi title, gui code (dn1), or DPD code (DN/DNa).")
    pb.set_defaults(func=_handle_lookup_book)

    peo = sub.add_parser("get-ebc-overview",
                         help="Parse the EBC per-sutta overview card for SUTTA_CODE.")
    peo.add_argument("code", help="Sutta code, e.g. MN10, mn-10, mn 10, DN22, MA98.")
    peo.set_defaults(func=_handle_get_ebc_overview)

    pga = sub.add_parser("get-agama",
                         help="Fetch Āgama parallel translations for a sutta. "
                              "Reads get-ebc-overview parallels_agama, resolves each "
                              "to its Patton or BDK file, and returns the full text. "
                              "Missing codes are listed in parallels_missing.")
    pga.add_argument("code", help="Sutta code, e.g. MN10, DN22.")
    pga.add_argument("--max", dest="max_parallels", type=int, default=5,
                     help="Maximum parallels to fetch (default: 5).")
    pga.set_defaults(func=_handle_get_agama)

    pes = sub.add_parser("search-ebc",
                         help="Fixed-string grep across the Early Buddhist Connections vault.")
    pes.add_argument("query")
    pes.add_argument("--folder", default=None,
                     help="Restrict to a subfolder of the EBC vault.")
    pes.add_argument("--limit", type=int, default=20)
    pes.set_defaults(func=_handle_search_ebc)

    pss = sub.add_parser("search-sanskrit",
                         help="Fixed-string grep across the local GRETIL Sanskrit corpus (.txt files).")
    pss.add_argument("query")
    pss.add_argument("--folder", default=None,
                     help="Restrict to a subfolder of the GRETIL corpus (e.g. '1_veda').")
    pss.add_argument("--limit", type=int, default=20)
    pss.set_defaults(func=_handle_search_sanskrit)

    plfc = sub.add_parser("library-folders-check",
                          help="Probe configured library folders paths and index health.")
    plfc.set_defaults(func=_handle_library_folders_check)

    pfr = sub.add_parser("library-folders-refresh",
                         help="Refresh the configured library folders index.")
    pfr.add_argument("--limit", type=int, default=None)
    pfr.add_argument("--retry-failed", action="store_true",
                     help="Re-extract unchanged files whose previous extraction "
                          "did not succeed (e.g. after adding extractor support).")
    pfr.set_defaults(func=_handle_library_folders_refresh)

    psfc = sub.add_parser("search-library-folders",
                          help="Search the configured library folders index.")
    psfc.add_argument("query")
    psfc.add_argument("--limit", type=int, default=20)
    psfc.add_argument("--include-duplicates", action="store_true")
    psfc.set_defaults(func=_handle_search_library_folders)

    pfd = sub.add_parser("library-folders-duplicates",
                         help="Summarize duplicate clusters in the library folders index.")
    pfd.add_argument("--samples", type=int, default=5)
    pfd.set_defaults(func=_handle_library_folders_duplicates)

    psp = sub.add_parser("sc-parallels",
                         help="SuttaCentral offline archive: list parallels for a citation "
                              "(e.g. 'mn18') and return text + en translation where present.")
    psp.add_argument("citation")
    psp.add_argument("--no-text", action="store_true",
                     help="Skip text retrieval; report parallel refs only.")
    psp.set_defaults(func=_handle_sc_parallels)

    pscs = sub.add_parser("sc-search",
                          help="Fixed-string grep across SuttaCentral offline root texts.")
    pscs.add_argument("query")
    pscs.add_argument("--lang", default="pli",
                      help="Root-text language: pli, lzh (Chinese Āgamas), san, pra, en, misc.")
    pscs.add_argument("--limit", type=int, default=20)
    pscs.set_defaults(func=_handle_sc_search)

    psi = sub.add_parser("scratch-init",
                         help="Create the scratch dossier file for a run.")
    psi.add_argument("slug")
    psi.add_argument("--class", dest="run_class", default="sutta-anchored",
                     choices=["sutta-anchored", "thematic"],
                     help="thematic = non-sutta-anchored; auto-skips Phase 2.5/3b gates.")
    psi.add_argument("--question-original", default=None,
                     help="The user's exact request wording.")
    psi.add_argument("--question-polished", default=None,
                     help="The polished research question (Phase 0 evidence).")
    psi.add_argument("--scope-assumptions", default=None,
                     help="Inferred textual/interpretive scope, depth, seeds (Phase 0 evidence).")
    psi.add_argument("--ambiguity", default=None,
                     choices=["clear", "minor_uncertainty", "unclear"],
                     help="Ambiguity status (Phase 0 evidence). Providing this plus "
                          "--question-polished and --scope-assumptions writes the "
                          "Phase 0 gate automatically.")
    psi.set_defaults(func=_handle_scratch_init)

    psl = sub.add_parser("scratch-log",
                         help="Append a manual entry to the scratch dossier under a phase.")
    psl.add_argument("phase", help="Phase id: 0, 1, 2, 2.5, 3, 3b, 4, 4b, 4c, 5, 6, 7")
    psl.add_argument("tool", help="Tool/source name (free text).")
    psl.add_argument("rest", nargs="*", help="Free-form args / query string (logged verbatim).")
    psl.add_argument("--summary", default=None)
    psl.add_argument("--results", default=None, type=Path,
                     help="Path to a JSON file whose contents will be embedded verbatim.")
    psl.add_argument("--hits", default=None, type=int)
    psl.set_defaults(func=_handle_scratch_log)

    psg = sub.add_parser("scratch-gate",
                         help="Append the canonical exit-gate checklist for a phase.")
    psg.add_argument("phase")
    psg.set_defaults(func=_handle_scratch_gate)

    psv = sub.add_parser("scratch-verify",
                         help="Verify every prior phase has its exit gate. Exits 1 on failure.")
    psv.add_argument("--through", default=None,
                     help="Check gates through this phase id; default = highest gate written.")
    psv.set_defaults(func=_handle_scratch_verify)

    psr = sub.add_parser("scratch-resume",
                         help="Print the last gate written and the suggested next phase.")
    psr.add_argument("slug", nargs="?", default=None,
                     help="Slug for the scratch file; omit if VICAYA_SCRATCH is set.")
    psr.set_defaults(func=_handle_scratch_resume)

    psw = sub.add_parser("scratch-which",
                         help="Print this run's active scratch path (resolved from run state).")
    psw.set_defaults(func=_handle_scratch_which)

    pvc = sub.add_parser("verify-citation",
                         help="Confirm a human sutta reference exists in dpd.db sutta_info.")
    pvc.add_argument("ref", help='Reference, e.g. "SN 46.42", "MN60", "Sn 4.8".')
    pvc.set_defaults(func=_handle_verify_citation)

    args = p.parse_args()

    exit_code, autolog_argv, result_for_autolog, autolog = args.func(args)
    if autolog:
        _maybe_autolog(args.cmd, autolog_argv, result_for_autolog)
    return exit_code


if __name__ == "__main__":
    raise SystemExit(_cli())
