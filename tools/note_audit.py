"""Audit an existing vault note before an enrichment run builds on it (#127).

A run that extends an old note tends to trust it: its citations, the label on
each footnote, its quotes and its Critical Gaps. The reference-exists check
passes a wrong claim, because the reference is real. This audit tests the
claims a note makes about its references against the databases.
"""

from __future__ import annotations

import re
import unicodedata
from pathlib import Path
from typing import Any

from tools.canon_paragraphs import check_quotes
from tools.note_checks import extract_frontmatter

# "[^id]: SN48.8 Daṭṭhabbasuttaṃ para 478 — db: s0305m_mul, para 478"
_FOOTNOTE_RE = re.compile(
    r"^\[\^([^\]]+)\]:\s*(?P<label>\S+)[^\n]*?\bdb:\s*(?P<table>[a-z0-9]+_(?:mul|att|tik|nrf)),"
    r"\s*(?P<kind>para\.?|§)\s*(?P<para>\d+(?:\s*[-–]\s*\d+)?)",
    re.M,
)
_GAPS_HEADING_RE = re.compile(r"^##\s+Critical Gaps\s*$", re.M)


def _norm(code: str) -> str:
    return re.sub(r"\s+", "", code).upper()


def _same_sutta(a: str, b: str) -> bool:
    """Equal codes, or one is the coarser form of the other (SN25 / SN25.1)."""
    a, b = _norm(a), _norm(b)
    return a == b or a.startswith(b + ".") or b.startswith(a + ".")


def _critical_gaps(body: str) -> list[str]:
    match = _GAPS_HEADING_RE.search(body)
    if not match:
        return []
    section = re.split(r"^##\s", body[match.end() :], maxsplit=1, flags=re.M)[0]
    return [
        line.strip()
        for line in section.splitlines()
        if line.strip() and not line.strip().startswith(("|---", "| ---", "|:--"))
    ]


def audit_note(
    note_text: str, canon_db: Path | None, dpd_db: Path | None = None
) -> dict[str, Any]:
    """Test the claims an old note makes about its references.

    Findings: `quote-elsewhere` / `quote-not-found` / `row-id-citation` from the
    quote check; `label-mismatch` where a footnote's sutta code is not the
    sutta its own `db:` paragraph falls in; `no-such-paragraph` where the
    footnote cites a paragraph the book does not have. `gaps_to_retest` lists the
    note's Critical Gaps rows, which a new run must search again, not trust.
    """
    from tools.research_sources import resolve_citation

    findings: list[dict[str, Any]] = []
    quotes = check_quotes(note_text, canon_db, dpd_db)
    if not quotes.get("ok", True) and "error" in quotes:
        return {"ok": False, "error": quotes["error"]}
    findings.extend(quotes.get("findings", []))

    labels_checked = 0
    for m in _FOOTNOTE_RE.finditer(note_text):
        first = int(re.findall(r"\d+", m.group("para"))[0])
        resolved = resolve_citation(
            m.group("table"), str(first), dpd_db=dpd_db, canon_db=canon_db
        )
        if resolved.paranum_exists is None or not re.match(
            r"[A-Za-z]+\d", m.group("label")
        ):
            continue
        labels_checked += 1
        line = note_text.count("\n", 0, m.start()) + 1
        if resolved.paranum_exists is False:
            findings.append(
                {
                    "line": line,
                    "verdict": "no-such-paragraph",
                    "cites": f"{m.group('table')} para {first}",
                }
            )
            continue
        resolved_code = resolved.human.split(" ", 1)[0]
        if re.match(r"[A-Za-z]+\d", resolved_code) and not _same_sutta(
            m.group("label"), resolved_code
        ):
            findings.append(
                {
                    "line": line,
                    "verdict": "label-mismatch",
                    "footnote_says": m.group("label"),
                    "db_says": resolved.human,
                    "cites": f"{m.group('table')} para {first}",
                }
            )

    _, body = extract_frontmatter(note_text)

    return {
        "ok": not findings,
        "findings": findings,
        "checked": {
            "quotes": quotes.get("checked", 0),
            "footnote_labels": labels_checked,
        },
        "gaps_to_retest": _critical_gaps(body),
    }


_BIB_SECTIONS = ("Secondary Sources", "Online Sources", "Media Sources")
_TITLE_STOP = frozenset(
    "about their these those which where there under between through"
    " volume edition press university journal".split()
)


def _plain(text: str) -> str:
    folded = unicodedata.normalize("NFKD", text)
    folded = "".join(c for c in folded if not unicodedata.combining(c))
    return re.sub(r"\s+", " ", folded.lower())


def _bibliography_entries(note_text: str) -> list[tuple[str, str]]:
    """(subsection, entry) for each source entry of the note's bibliography."""
    match = re.search(r"^## Bibliography\s*\n(.*?)(?=^## |\Z)", note_text, re.M | re.S)
    if not match:
        return []
    entries = []
    for block in re.split(r"^### ", match.group(1), flags=re.M)[1:]:
        heading, _, body = block.partition("\n")
        heading = heading.strip()
        if not heading.startswith(_BIB_SECTIONS):
            continue
        for para in re.split(r"\n\s*\n", body):
            entry = " ".join(para.split())
            if len(entry) >= 25:
                entries.append((heading, entry))
    return entries


def _untraced_reason(entry: str, dossier: str) -> str | None:
    """Why `entry` cannot have come from this run's evidence, or None if it can."""
    calibre = re.search(r"Calibre #(\d+)", entry)
    if calibre and calibre.group(1) in dossier:
        return None
    url = re.search(r"https?://([^/\s)]+)", entry)
    if url and url.group(1).removeprefix("www.") in dossier:
        return None
    head = re.split(r"[,.]", entry, maxsplit=1)[0]
    surname_words = [w for w in re.findall(r"[a-z]{4,}", _plain(head))]
    author_seen = (not surname_words) or any(w in dossier for w in surname_words)
    title = re.search(r"[*\"“]([^*\"”]{8,}?)[*\"”]", entry)
    words = (
        [
            w
            for w in re.findall(r"[a-z]{5,}", _plain(title.group(1)))
            if w not in _TITLE_STOP
        ][:4]
        if title
        else []
    )
    title_seen = (not words) or sum(w in dossier for w in words) >= max(
        1, len(words) // 2
    )
    if author_seen and title_seen:
        return None
    if not author_seen and not title_seen:
        return "neither the author nor the title appears anywhere in the run's evidence"
    if not author_seen:
        return "the author's name appears nowhere in the run's evidence"
    return "the title's words appear nowhere in the run's evidence"


def check_bibliography(note_text: str, dossier_text: str) -> dict[str, Any]:
    """Flag bibliography entries that nothing in the run's dossier supports.

    A real source reaches the note through a logged search: a library hit, an
    OpenAlex record, a fetched page. An entry whose author or title appears
    nowhere in the dossier was written from memory, which is how a guessed
    publisher, a book that does not exist, and a wrongly dated edition got
    into published notes (issue #97). Advisory: a source read outside the
    helpers is legitimate, but then it must be logged (`scratch-log`).
    """
    dossier = _plain(dossier_text)
    findings = []
    entries = _bibliography_entries(note_text)
    for heading, entry in entries:
        reason = _untraced_reason(entry, dossier)
        if reason:
            findings.append(
                {
                    "section": heading,
                    "entry": entry[:160],
                    "verdict": "not-in-evidence",
                    "reason": reason,
                }
            )
    return {"ok": not findings, "checked": len(entries), "findings": findings}
