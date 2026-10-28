"""Whole CST paragraphs, and a check that a note's Pāḷi quotes sit in them.

A CST paragraph spans several rows: only its first row carries `paranum`, the
rest have it blank. Agents pulling rows by `id` kept citing the row id as the
paragraph number, and `WHERE paranum = N` pulls dropped the continuation rows,
so quotes came out truncated or spliced across two paragraphs (issue #124).
`get_paragraph` returns every row of a paragraph under its real number;
`check_quotes` tests each Pāḷi quote in a note against the paragraph its
citation names, which also catches a quote finished from memory (issue #96).

Two note formats carry Pāḷi, and both are checked. The older one is a `>`
blockquote paired with a `db: <table>, para N` footnote. The note template's
own format is a `- Pāḷi: "…"` bullet under a bold label
(`- **MN60 Apaṇṇakasuttaṃ para 97**`), which the blockquote path never saw:
513 such quotes sat untested across 49 vault notes while `check-quotes`
reported `checked: 0` (issue #157).
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

# --- the note template's bullet format: `- **MN60 … para 97**` + `- Pāḷi: …`
# The Pāḷi bullet itself. Group 1 is the indent, group 2 the quoted text.
_BULLET_QUOTE_RE = re.compile(
    r"^([ \t]*)[-*+][ \t]+\**(?:Pāḷi|Pāli|Pali)\**[ \t]*:[ \t]*(.*)$", re.I
)
# A bold bullet is a label when it is the parent of the Pāḷi bullet above it.
_BULLET_LABEL_RE = re.compile(r"^([ \t]*)[-*+][ \t]+\*\*(.+?)\*\*")
_HEADING_LINE_RE = re.compile(r"^#{1,6}\s")
_ANY_BULLET_RE = re.compile(r"^[ \t]*[-*+][ \t]")
# A CST table code written into the label ("s0203m_mul").
_LABEL_TABLE_RE = re.compile(r"\b([a-z0-9]+_(?:mul|att|tik|nrf))\b")
# A DPD/CST sutta code: AN4.184, MN60, SN55.27, Dhp212-216, ITI30.
_LABEL_CODE_RE = re.compile(r"\b([A-Z][A-Za-z]{1,3}\d+(?:[.\-]\d+)*)\b")
# The paragraph the label names: "para 97", "paras 265–268", "§113".
_LABEL_PARA_IN_TEXT_RE = re.compile(r"(?:\bparas?\b|§)\s*(\d+(?:\s*[–-]\s*\d+)?)", re.I)
_CST_FILE_RE = re.compile(r"(?:.*/)?(.+)\.(mul|att|tik|nrf)\.xml$")
_DPD_RANGE_RE = re.compile(r"^([A-Z]+)(\d+)-(\d+)$")


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


def _dpd_code_table(code: str, dpd_db: Path | None, cache: dict) -> str | None:
    """The CST table a DPD sutta code names, via `sutta_info.cst_file`.

    `cst_file` is stored as `romn/s0402m3.mul.xml`; the canon tables drop the
    path and join type and stem with an underscore (`s0402m3_mul`). A Dhp-style
    range code (`DHP212-216`) matches the range row that covers its first
    number, so a verse number still lands in the right book.
    """
    if dpd_db is None or not dpd_db.exists():
        return None
    wanted = re.sub(r"\s+", "", code).upper()
    if wanted in cache:
        return cache[wanted]
    table = None
    try:
        with sqlite3.connect(f"file:{dpd_db}?mode=ro", uri=True) as conn:
            rows = conn.execute(
                "SELECT cst_file FROM sutta_info "
                "WHERE REPLACE(UPPER(dpd_code), ' ', '') = ? LIMIT 1",
                (wanted,),
            ).fetchone()
            if rows is None:
                span = _DPD_RANGE_RE.match(wanted)
                if span:
                    prefix, start = span.group(1), int(span.group(2))
                    for dpd_code, cst_file in conn.execute(
                        "SELECT dpd_code, cst_file FROM sutta_info "
                        "WHERE dpd_code LIKE ?",
                        (f"{prefix}%",),
                    ):
                        r = _DPD_RANGE_RE.match((dpd_code or "").upper())
                        if (
                            r
                            and r.group(1) == prefix
                            and int(r.group(2)) <= start <= int(r.group(3))
                        ):
                            rows = (cst_file,)
                            break
    except sqlite3.Error:
        rows = None
    if rows:
        match = _CST_FILE_RE.match(rows[0] or "")
        if match:
            table = f"{match.group(1)}_{match.group(2)}"
    cache[wanted] = table
    return table


def _label_locator(label: str, dpd_db: Path | None, cache: dict) -> dict:
    """The (table, paragraph numbers) a bold label names, or why it names none.

    An explicit table code wins over a sutta code, so a commentary label that
    says which aṭṭhakathā table it quotes from is checked against that table
    rather than skipped. A label that names only a paragraph number, or only a
    source, cannot be resolved and is reported as unpaired.
    """
    numbers_match = _LABEL_PARA_IN_TEXT_RE.search(label)
    numbers = paranum_numbers(numbers_match.group(1)) if numbers_match else set()
    table_match = _LABEL_TABLE_RE.search(label)
    table = table_match.group(1) if table_match else None
    if table is None and not _COMMENTARY_LABEL_RE.search(label):
        for code in _LABEL_CODE_RE.findall(label):
            table = _dpd_code_table(code, dpd_db, cache)
            if table:
                break
    if table is None:
        reason = (
            "commentary label names no table code"
            if _COMMENTARY_LABEL_RE.search(label)
            else "label names no canon table or sutta code"
        )
        return {"table": None, "numbers": numbers, "reason": reason}
    if not numbers:
        return {
            "table": table,
            "numbers": set(),
            "reason": f"label names {table} but no paragraph number",
        }
    return {"table": table, "numbers": numbers, "reason": None}


def _bullet_quotes(lines: list[str]) -> list[dict]:
    """Each `- Pāḷi:` bullet with the bold label bullet it belongs to.

    The label is the nearest bold bullet above it at the same or a smaller
    indent, which is how the note template nests them. Blank lines are allowed
    between the two; a heading, a sibling bullet or a prose line ends the
    search, so a quote is never paired with a label from another block.
    """
    pairs: list[dict] = []
    for index, line in enumerate(lines):
        match = _BULLET_QUOTE_RE.match(line)
        if not match:
            continue
        indent = len(match.group(1).expandtabs(4))
        label: str | None = None
        label_line: int | None = None
        for back in range(index - 1, -1, -1):
            above = lines[back]
            if not above.strip():
                continue
            if _HEADING_LINE_RE.match(above):
                break
            label_match = _BULLET_LABEL_RE.match(above)
            if label_match:
                if len(label_match.group(1).expandtabs(4)) <= indent:
                    label = label_match.group(2).strip()
                    label_line = back + 1
                break
            if _ANY_BULLET_RE.match(above):
                break
            break
        pairs.append(
            {
                "line": index + 1,
                "text": match.group(2).strip(),
                "label": label,
                "label_line": label_line,
            }
        )
    return pairs


def check_quotes(
    note_text: str, canon_db: Path | None, dpd_db: Path | None = None
) -> dict:
    """Test each cited Pāḷi quote against the paragraph it cites.

    A blockquote is paired with the `db: <table>, para N` footnote on it, on its
    translation (the next block), or on the bold label line above its run. A
    template bullet (`- Pāḷi:`) is paired with the bold label bullet above it,
    which names the table (or sutta code) and paragraph. A footnote that cites
    a row `id` instead of a paragraph is itself a finding. Findings are
    advisory — the check cannot tell a misquote from a legitimate variant
    reading — so each says where the text actually is and how much of it
    matched, for a person to judge.
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
    code_cache: dict = {}
    bullet_checked = 0
    bullet_unpaired: list[dict] = []
    bullet_skipped: dict[str, int] = {}
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

        def judge(fragments: list[str], table: str, numbers: set[int], base: dict):
            """Test one quote's fragments; append findings, report if it was tested."""
            paragraphs = paragraphs_of(table)
            if paragraphs is None:
                return False
            low, high = min(numbers), max(numbers)
            base = {
                **base,
                "cites": f"{table} para {low}" + (f"–{high}" if high > low else ""),
            }
            cited = [p for p in paragraphs if p["numbers"] & numbers]
            if not cited:
                findings.append({**base, "verdict": "no-such-paragraph"})
                return True
            cited_text = "".join(p["text"] for p in cited)
            missing = [f for f in fragments if not _found(f, cited_text)]
            if not missing:
                return True
            homes = [[p for p in paragraphs if _found(f, p["text"])] for f in missing]
            if all(homes):
                found_in = sorted({p["paranum"] for home in homes for p in home})
                findings.append(
                    {**base, "verdict": "in-other-paragraph", "found_in": found_in}
                )
                return True
            worst_first = min(
                missing,
                key=lambda f: _matched_prefix(f, cited_text) / len(f.split()),
            )
            # Only the last word differs: a variant ending or sandhi, not a
            # misquote, and flagging it buries the real findings.
            if _matched_prefix(worst_first, cited_text) >= len(worst_first.split()) - 1:
                return True
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
            closest = max(paragraphs, key=lambda p: _matched_prefix(worst, p["text"]))
            closest_words = _matched_prefix(worst, closest["text"])
            if closest_words > _matched_prefix(worst, cited_text):
                finding["closest_paragraph"] = closest["paranum"]
                finding["closest_matched_words"] = f"{closest_words}/{total}"
            findings.append(finding)
            return True

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
                if judge(
                    fragments,
                    table,
                    numbers,
                    {
                        "line": block["line"] + 1,
                        "quote": _QUOTE_LABEL_RE.sub("", text)[:80],
                    },
                ):
                    checked += 1

        # The note template's own format: `- **MN60 … para 97**` + `- Pāḷi: …`.
        # Issue #157: this path did not exist, so these quotes were never seen.
        for bullet in _bullet_quotes(lines):
            text = bullet["text"]

            def skip(reason: str) -> None:
                bullet_skipped[reason] = bullet_skipped.get(reason, 0) + 1

            if text.lstrip("*_ (").startswith("(") or not _is_pali(text):
                skip("no Pāḷi text in the bullet")
                continue
            fragments = _quote_fragments(text)
            if not fragments:
                skip("quote too short to place")
                continue
            if not bullet["label"]:
                skip("no bold label above the bullet")
                continue
            locator = _label_locator(bullet["label"], dpd_db, code_cache)
            if locator["table"] is None:
                skip(locator["reason"])
                continue
            if not locator["numbers"]:
                bullet_unpaired.append(
                    {
                        "line": bullet["line"],
                        "label_line": bullet["label_line"],
                        "reason": locator["reason"],
                    }
                )
                continue
            base = {
                "line": bullet["line"],
                "format": "bullet",
                "quote": _QUOTE_LABEL_RE.sub("", text)[:80],
            }
            if judge(fragments, locator["table"], locator["numbers"], base):
                bullet_checked += 1
            else:
                bullet_unpaired.append(
                    {
                        "line": bullet["line"],
                        "label_line": bullet["label_line"],
                        "reason": f"no canon table {locator['table']}",
                    }
                )
    return {
        "ok": not findings,
        "checked": checked + bullet_checked,
        "unpaired": unpaired,
        "findings": findings,
        "bullet_checked": bullet_checked,
        "bullet_unpaired": bullet_unpaired,
        "bullet_skipped": bullet_skipped,
    }
