"""Whole CST paragraphs, and a check that a note's Pāḷi quotes sit in them.

A CST paragraph spans several rows: only its first row carries `paranum`, the
rest have it blank. Agents pulling rows by `id` kept citing the row id as the
paragraph number, and `WHERE paranum = N` pulls dropped the continuation rows,
so quotes came out truncated or spliced across two paragraphs (issue #124).
`get_paragraph` returns every row of a paragraph under its real number;
`check_quotes` tests each Pāḷi blockquote in a note against the paragraph its
citation names, which also catches a quote finished from memory (issue #96).
"""

from __future__ import annotations

import re
import sqlite3
import unicodedata
from contextlib import closing
from pathlib import Path

# Rows that open a new book, chapter or sutta. A paragraph never runs past one,
# even when the next sutta's first numbered row comes later.
_HEADING_RENDS = frozenset(
    {"book", "chapter", "nikaya", "title", "subhead", "subsubhead"}
)
# CST embeds variant readings inline as <note>…</note>; they are not the text.
_NOTE_RE = re.compile(r"<note>.*?</note>", re.S)
_TAG_RE = re.compile(r"<[^>]+>")
_WS_RE = re.compile(r"\s+")
_TABLE_RE = re.compile(r"^[a-z0-9]+_(?:mul|att|tik|nrf)$")
_PALI_LETTERS = frozenset("ṃāīūṭḍṇñḷṅ")
_ENGLISH_WORD_RE = re.compile(
    r"\b(the|and|of|is|that|this|he|they|which|with|monks|bhikkhus)\b", re.I
)
_FOOTNOTE_DEF_RE = re.compile(
    r"^\[\^([^\]]+)\]:.*?\bdb:\s*([a-z0-9]+_(?:mul|att|tik|nrf)),\s*"
    r"(para\.?|§|id)\s*(\d+(?:\s*[-–]\s*\d+)?)",
    re.M,
)
_FOOTNOTE_REF_RE = re.compile(r"\[\^([^\]]+)\]")
_QUOTE_LABEL_RE = re.compile(
    r"^\s*[—–-]?\s*\**(Pāḷi|Pāli|Pali|English|Translation)\**\s*:\s*", re.I
)
_LABEL_PARA_RE = re.compile(r"^\*\*.*?\bpara\.?\s*(\d+)\b.*\*\*")
# A quote shorter than this is too generic to place (a stock phrase recurs).
_MIN_FRAGMENT_WORDS = 4


def clean_text(raw: str | None) -> str:
    """CST row text without markup or variant readings, NFC, ṃ niggahita."""
    text = _NOTE_RE.sub(" ", raw or "")
    text = unicodedata.normalize("NFC", _TAG_RE.sub("", text))
    text = text.replace("ṁ", "ṃ").replace("ŋ", "ṃ")
    return _WS_RE.sub(" ", text).strip()


def _comparable(text: str) -> str:
    """Fold what quoting legitimately changes: case, quote marks, punctuation."""
    # Mark gaps as "…" before punctuation goes, or "..." would vanish and a
    # quote with a gap would be compared as one unbroken run.
    text = re.sub(r"\.{3,}", "…", clean_text(text)).casefold()
    text = _FOOTNOTE_REF_RE.sub(" ", text)
    text = re.sub(r"[‘’'\"“”]", "", text)
    # "-aṃ + iti" is written "-anti" in the canon; notes often keep the ṃ.
    text = re.sub(r"ṃ(nti)\b", r"\1", text)
    text = re.sub(r"[^\w\s…]", " ", text)
    text = re.sub(r"^\s*\d+\s", " ", text)
    return _WS_RE.sub(" ", text).strip()


def paranum_numbers(paranum: str | None) -> set[int]:
    """Numbers a paranum cell covers: "97" → {97}; "583-4" → {583, 584}.

    Odd cells occur too ("18-19-20", "179-", "1699-700"); each later part may
    abbreviate the first, so missing leading digits come from the first part.
    """
    text = paranum or ""
    if not re.match(r"^\s*\d+(?:\s*[-–]\s*\d*)*\s*$", text):
        return set()
    parts = re.findall(r"\d+", text)
    head = parts[0]
    numbers = {int(head)}
    last = int(head)
    for tail in parts[1:]:
        value = (
            int(head[: len(head) - len(tail)] + tail)
            if len(tail) < len(head)
            else int(tail)
        )
        if value > last:
            numbers |= set(range(last, value + 1))
            last = value
    return numbers


def _table_rows(conn: sqlite3.Connection, table: str) -> list[tuple]:
    return conn.execute(
        f"SELECT id, rend, paranum, pali_text, english_translation FROM {table} "
        "ORDER BY id"
    ).fetchall()


def _paragraphs(rows: list[tuple]) -> list[dict]:
    """Split a table's rows into paragraphs: a numbered row and its continuations.

    Rows between a heading and the next numbered row (summary verses, "…pe…"
    stubs, some Jātaka prose) belong to no numbered paragraph. They form an
    unnumbered block, so a quote from one is still found, but no paranum ever
    names it.
    """
    paragraphs: list[dict] = []
    current: dict | None = None
    for row_id, rend, paranum, pali, english in rows:
        if rend in _HEADING_RENDS:
            current = None
            continue
        if (paranum or "").strip() or current is None:
            numbered = bool((paranum or "").strip())
            current = {
                "paranum": paranum.strip() if numbered else f"unnumbered, row {row_id}",
                "numbers": paranum_numbers(paranum) if numbered else set(),
                "row_ids": [],
                "pali": [],
                "english": [],
            }
            paragraphs.append(current)
        current["row_ids"].append(row_id)
        if pali:
            current["pali"].append(clean_text(pali))
        if english:
            current["english"].append(clean_text(english))
    return paragraphs


def _connect(canon_db: Path) -> closing[sqlite3.Connection]:
    return closing(sqlite3.connect(f"file:{canon_db}?mode=ro", uri=True))


def _table_exists(conn: sqlite3.Connection, table: str) -> bool:
    return bool(
        _TABLE_RE.match(table)
        and conn.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (table,)
        ).fetchone()
    )


def get_paragraph(
    book_code: str,
    paranum: int | None = None,
    *,
    row_id: int | None = None,
    canon_db: Path | None,
) -> dict:
    """Every row of one paragraph, by its paranum or by any row id inside it.

    A paranum that restarts per section (Khp, Paṭisambhidāmagga, Jātaka) has
    several occurrences; all are returned and the caller must pick by context.
    """
    if canon_db is None or not canon_db.exists():
        return {"ok": False, "error": "VICAYA_CANON_DB is not set or missing"}
    with _connect(canon_db) as conn:
        if not _table_exists(conn, book_code):
            return {
                "ok": False,
                "error": f"no canon table {book_code!r} — check it with lookup-book",
            }
        paragraphs = _paragraphs(_table_rows(conn, book_code))
    if row_id is not None:
        matches = [p for p in paragraphs if row_id in p["row_ids"]]
        if not matches:
            return {
                "ok": False,
                "error": f"row id {row_id} in {book_code} belongs to no paragraph "
                "(it is a heading, or the table has no such row)",
            }
    else:
        matches = [p for p in paragraphs if paranum in p["numbers"]]
        if not matches:
            return {
                "ok": False,
                "error": f"{book_code} has no paragraph {paranum} — do not cite it",
            }
    occurrences = [
        {
            "paranum": p["paranum"],
            "first_row_id": p["row_ids"][0],
            "last_row_id": p["row_ids"][-1],
            "pali": " ".join(p["pali"]),
            "english": " ".join(p["english"]),
        }
        for p in matches
    ]
    result: dict = {
        "ok": True,
        "book_code": book_code,
        "paranum": matches[0]["paranum"],
        "occurrences": occurrences,
    }
    if row_id is not None:
        result["note"] = (
            f"row id {row_id} is inside paragraph {matches[0]['paranum']}: "
            "cite the paragraph number, never the row id"
            if matches[0]["numbers"]
            else f"row id {row_id} follows a heading and has no paragraph "
            "number: cite it by its section heading, never the row id"
        )
    if len(matches) > 1:
        result["warning"] = (
            f"paragraph {paranum} occurs {len(matches)} times in {book_code} "
            "(numbering restarts per section): pick the occurrence by its text"
        )
    return result


def _is_pali(text: str) -> bool:
    return (
        sum(ch in _PALI_LETTERS for ch in text) >= 3
        and len(_ENGLISH_WORD_RE.findall(text)) < 2
    )


def _quote_runs(lines: list[str]) -> list[list[dict]]:
    """Runs of blockquotes between prose lines; each block is one quote.

    A block is a set of consecutive `>` lines. Blank lines separate blocks
    but keep the run going, since a Pāḷi quote and its translation are two
    blocks under one label.
    """
    runs: list[list[dict]] = []
    run: list[dict] = []
    block: dict | None = None
    for index, line in enumerate(lines):
        if line.startswith(">"):
            text = line[1:].strip()
            if block is None:
                block = {"line": index, "text": text}
                run.append(block)
            else:
                block["text"] += " " + text
        elif not line.strip():
            block = None
        else:
            block = None
            if run:
                runs.append(run)
                run = []
    if run:
        runs.append(run)
    return runs


# A label naming a commentary over a mūla paragraph ("Khuddakapāṭha-aṭṭhakathā
# on para 15") gives the mūla number, not the commentary's.
_COMMENTARY_LABEL_RE = re.compile(
    r"aṭṭhakathā|ṭīkā|atthakatha|tika\b|commentary|_att|_tik", re.I
)


def _run_label_marker(
    lines: list[str],
    run: list[dict],
    para_defs: dict[str, tuple[str, set[int]]],
    known: set[str],
) -> str | None:
    """The citation of the bold label line directly above a run, if any."""
    index = run[0]["line"] - 1
    while index >= 0 and not lines[index].strip():
        index -= 1
    above = lines[index] if index >= 0 else ""
    if not above.startswith("**") or _COMMENTARY_LABEL_RE.search(above):
        return None
    for marker in reversed(_FOOTNOTE_REF_RE.findall(above)):
        if marker in known:
            return marker
    label = _LABEL_PARA_RE.match(above)
    if label:
        number = int(label.group(1))
        markers = [m for m, (_, nums) in para_defs.items() if number in nums]
        if len({(para_defs[m][0], frozenset(para_defs[m][1])) for m in markers}) == 1:
            return markers[0]
    return None


def _block_marker(run: list[dict], k: int, known: set[str]) -> str | None:
    """A quote's own footnote, else its translation twin's (the next block)."""
    candidates = [run[k]]
    if k + 1 < len(run) and not _is_pali(run[k + 1]["text"]):
        candidates.append(run[k + 1])
    for block in candidates:
        for marker in reversed(_FOOTNOTE_REF_RE.findall(block["text"])):
            if marker in known:
                return marker
    return None


def _squash(text: str) -> str:
    # Editions space Pāḷi words differently ("na tveva" / "natveva"), so the
    # comparison ignores spaces altogether.
    return text.replace(" ", "")


def _found(fragment: str, haystack: str) -> bool:
    """Is the fragment in the text, allowing for sandhi at its last word?

    A quote that stops before "ti" drops the lengthened vowel the canon keeps
    ("bhavissati" for "bhavissatī’ti"), so the last character may differ.
    """
    squashed = _squash(fragment)
    return squashed in haystack or squashed[:-1] in haystack


def _matched_prefix(fragment: str, haystack: str) -> int:
    """How many leading words of `fragment` occur together in `haystack`."""
    words = fragment.split()
    low, high = 0, len(words)
    while low < high:
        mid = (low + high + 1) // 2
        if "".join(words[:mid]) in haystack:
            low = mid
        else:
            high = mid - 1
    return low


# A speaker label the note writes into a quote ("Ānanda: …", "… Bhagavā: …").
# The CST mūla text never contains a colon (0 rows), so a one- or two-word
# label at the start, or after a closing quote mark or gap, is the note's own.
_SPEAKER_LABEL_RE = re.compile(r"(^|[…\"”’']\s*)[^\W\d_]+(?:\s[^\W\d_]+)?:\s")


def _quote_fragments(text: str) -> list[str]:
    # A label ("— Pāḷi:") is the note's own words, not part of the quote.
    quote = _SPEAKER_LABEL_RE.sub(r"\1 … ", _QUOTE_LABEL_RE.sub("", text))
    return [
        f.strip()
        for f in re.split(r"…|\bpe\b", _comparable(quote))
        if len(f.split()) >= _MIN_FRAGMENT_WORDS
    ]


def check_quotes(note_text: str, canon_db: Path | None) -> dict:
    """Test each cited Pāḷi blockquote against the paragraph it cites.

    Each quote is paired with the `db: <table>, para N` footnote on it, on its
    translation (the next block), or on the bold label line above its run.
    A footnote that cites a row `id` instead of a paragraph is itself a
    finding. Findings are advisory — the check cannot tell a misquote from a
    legitimate variant reading — so each says where the text actually is and
    how much of it matched, for a person to judge.
    """
    if canon_db is None or not canon_db.exists():
        return {"ok": False, "error": "VICAYA_CANON_DB is not set or missing"}
    lines = note_text.splitlines()
    para_defs: dict[str, tuple[str, set[int]]] = {}
    id_defs: dict[str, tuple[str, int, int]] = {}
    for m in _FOOTNOTE_DEF_RE.finditer(note_text):
        if m.group(3) == "id":
            line = note_text.count("\n", 0, m.start()) + 1
            id_defs[m.group(1)] = (
                m.group(2),
                int(re.findall(r"\d+", m.group(4))[0]),
                line,
            )
        else:
            para_defs[m.group(1)] = (m.group(2), paranum_numbers(m.group(4)))
    known = set(para_defs) | set(id_defs)
    findings: list[dict] = []
    checked = 0
    unpaired = 0
    cache: dict[str, list[dict]] = {}
    with _connect(canon_db) as conn:

        def paragraphs_of(table: str) -> list[dict] | None:
            if table not in cache:
                if not _table_exists(conn, table):
                    return None
                cache[table] = [
                    {**p, "text": _squash(_comparable(" ".join(p["pali"])))}
                    for p in _paragraphs(_table_rows(conn, table))
                ]
            return cache[table]

        for table, row_id, line in id_defs.values():
            owner = next(
                (
                    p["paranum"]
                    for p in paragraphs_of(table) or []
                    if row_id in p["row_ids"]
                ),
                None,
            )
            finding = {
                "line": line,
                "verdict": "row-id-citation",
                "cites": f"{table} id {row_id}",
            }
            if owner:
                finding["cite_as"] = f"db: {table}, para {owner}"
            findings.append(finding)

        for run in _quote_runs(lines):
            label_marker = _run_label_marker(lines, run, para_defs, known)
            for k, block in enumerate(run):
                text = block["text"]
                if text.lstrip("*_ ").startswith("(") or not _is_pali(text):
                    continue
                fragments = _quote_fragments(text)
                if not fragments:
                    continue
                marker = _block_marker(run, k, known) or label_marker
                if marker is None:
                    unpaired += 1
                    continue
                if marker in id_defs:
                    continue
                table, numbers = para_defs[marker]
                paragraphs = paragraphs_of(table)
                if paragraphs is None:
                    unpaired += 1
                    continue
                checked += 1
                low, high = min(numbers), max(numbers)
                base = {
                    "line": block["line"] + 1,
                    "cites": f"{table} para {low}" + (f"–{high}" if high > low else ""),
                    "quote": _QUOTE_LABEL_RE.sub("", text)[:80],
                }
                cited = [p for p in paragraphs if p["numbers"] & numbers]
                if not cited:
                    findings.append({**base, "verdict": "no-such-paragraph"})
                    continue
                cited_text = "".join(p["text"] for p in cited)
                missing = [f for f in fragments if not _found(f, cited_text)]
                if not missing:
                    continue
                homes = [
                    [p for p in paragraphs if _found(f, p["text"])] for f in missing
                ]
                if all(homes):
                    found_in = sorted({p["paranum"] for home in homes for p in home})
                    findings.append(
                        {**base, "verdict": "in-other-paragraph", "found_in": found_in}
                    )
                    continue
                worst_first = min(
                    missing,
                    key=lambda f: _matched_prefix(f, cited_text) / len(f.split()),
                )
                # Only the last word differs: a variant ending or sandhi, not a
                # misquote, and flagging it buries the real findings.
                if (
                    _matched_prefix(worst_first, cited_text)
                    >= len(worst_first.split()) - 1
                ):
                    continue
                worst = min(
                    missing,
                    key=lambda f: _matched_prefix(f, cited_text) / len(f.split()),
                )
                total = len(worst.split())
                finding = {
                    **base,
                    "verdict": "not-found",
                    "matched_words": f"{_matched_prefix(worst, cited_text)}/{total}",
                }
                # Where the quote most likely comes from, so the fix is a lookup
                # rather than a search: the paragraph matching most of its opening.
                closest = max(
                    paragraphs, key=lambda p: _matched_prefix(worst, p["text"])
                )
                closest_words = _matched_prefix(worst, closest["text"])
                if closest_words > _matched_prefix(worst, cited_text):
                    finding["closest_paragraph"] = closest["paranum"]
                    finding["closest_matched_words"] = f"{closest_words}/{total}"
                findings.append(finding)
    return {
        "ok": not findings,
        "checked": checked,
        "unpaired": unpaired,
        "findings": findings,
    }
