"""Tests for the prior-note audit run at the start of an enrichment (#127).

Footnote and Critical Gaps lines are copied from real vault notes
(2026-05-24 hindu-sects-early-buddhism-comparison, 2026-10-16 saddha-faith).
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

from tools.note_audit import audit_note
from tools.research_sources import DEFAULT_CANON_DB, DEFAULT_DPD_DB

ROOT = Path(__file__).resolve().parents[1]

needs_dbs = pytest.mark.skipif(
    not (
        DEFAULT_CANON_DB
        and DEFAULT_CANON_DB.exists()
        and DEFAULT_DPD_DB
        and DEFAULT_DPD_DB.exists()
    ),
    reason="canon and DPD databases not available",
)

# Real: the Tathāgata-arises passage is DN2 §190, but the note labelled it DN1.
WRONG_LABEL = (
    "[^s0101m-190]: DN1 Brahmajālasuttaṃ para 190 — db: s0101m_mul, para 190\n"
)
RIGHT_LABEL = (
    "[^s0101m-190]: DN2 Sāmaññaphalasuttaṃ para 190 — db: s0101m_mul, para 190\n"
)


def _audit(text: str) -> dict:
    return audit_note(text, DEFAULT_CANON_DB, DEFAULT_DPD_DB)


@needs_dbs
def test_footnote_label_that_names_the_wrong_sutta_is_a_finding():
    result = _audit(WRONG_LABEL)
    (finding,) = result["findings"]
    assert finding["verdict"] == "label-mismatch"
    assert finding["footnote_says"] == "DN1"
    assert finding["db_says"].startswith("DN2 Sāmaññaphalasuttaṃ")
    assert result["ok"] is False


@needs_dbs
def test_correct_footnote_label_passes():
    result = _audit(RIGHT_LABEL)
    assert result["findings"] == []
    assert result["checked"]["footnote_labels"] == 1


@needs_dbs
def test_footnote_citing_a_paragraph_the_book_lacks_is_a_finding():
    text = "[^x]: DN2 Sāmaññaphalasuttaṃ para 99999 — db: s0101m_mul, para 99999\n"
    (finding,) = _audit(text)["findings"]
    assert finding["verdict"] == "no-such-paragraph"


@needs_dbs
def test_critical_gaps_are_listed_for_a_fresh_search():
    text = (
        "## Critical Gaps\n\n"
        "- **Minor** — the Tibetan *dad pa* scholastic classification is not "
        "represented by a primary text in the vault.\n"
        "- **Minor** — transcript timestamps above are approximate.\n\n"
        "## Bibliography\n- unrelated\n"
    )
    gaps = _audit(text)["gaps_to_retest"]
    assert len(gaps) == 2
    assert "dad pa" in gaps[0]
    assert all("Bibliography" not in g and "unrelated" not in g for g in gaps)


@needs_dbs
def test_cli_exits_1_on_a_finding_and_0_on_a_clean_note(tmp_path):
    def run(text: str) -> subprocess.CompletedProcess[str]:
        note = tmp_path / "n.md"
        note.write_text(text, encoding="utf-8")
        return subprocess.run(
            [sys.executable, "tools/research_sources.py", "audit-note", str(note)],
            capture_output=True,
            text=True,
            cwd=ROOT,
            env={**__import__("os").environ, "VICAYA_SCRATCH": "/dev/null/none"},
            stdin=subprocess.DEVNULL,
        )

    bad = run(WRONG_LABEL)
    assert bad.returncode == 1
    assert json.loads(bad.stdout)["findings"][0]["verdict"] == "label-mismatch"
    assert run(RIGHT_LABEL).returncode == 0


# --- check-bibliography (#97) ------------------------------------------------
# Entries copied from the real notes 2026-10-16 saddha-faith and
# 2026-09-12 bhavanga-development-and-comparative-gap.

from tools.note_audit import check_bibliography  # noqa: E402

BIBLIOGRAPHY = """\
## Bibliography

### Primary Sources (Canonical)

*Majjhima Nikāya* 47 (*Vīmaṃsakasuttaṃ*). Chaṭṭha Saṅgāyana Tipiṭaka.

### Secondary Sources

Nyanaponika Thera. *Devotion in Buddhism*. Kandy: Buddhist Publication Society, 1965.

Lusthaus, Dan. *Pudgalavāda Doctrines of the Person*. (Calibre #9995)

Karunadasa, Y. *Theravāda Abhidhamma: Its Inquiry into the Nature of Conditioned Reality*. (Calibre #7335)

### Online Sources

Ṭhānissaro Bhikkhu. "Faith in Awakening." *dhammatalks.org*. Accessed 2026-10-16. https://www.dhammatalks.org/books/PurityOfHeart/Section0005.html
"""

DOSSIER = (
    '"title": "Devotion in Buddhism - Nyanaponika Thera.pdf", "snippet": "Kandy"\n'
    "Calibre book 7335 Karunadasa Theravada Abhidhamma\n"
    "fetched https://www.dhammatalks.org/books/PurityOfHeart/Section0005.html\n"
)


def test_bibliography_entries_the_run_never_saw_are_flagged():
    result = check_bibliography(BIBLIOGRAPHY, DOSSIER)
    assert result["checked"] == 4
    (finding,) = result["findings"]
    assert finding["entry"].startswith("Lusthaus, Dan.")
    assert "author" in finding["reason"] or "neither" in finding["reason"]
    assert result["ok"] is False


def test_a_calibre_id_a_library_title_or_a_fetched_url_counts_as_evidence():
    # Karunadasa is traced by its Calibre number, Nyanaponika by the library
    # title in a logged hit, the dhammatalks page by the fetched URL.
    flagged = {
        f["entry"][:10] for f in check_bibliography(BIBLIOGRAPHY, DOSSIER)["findings"]
    }
    assert flagged == {"Lusthaus, "}


def test_primary_sources_are_not_checked():
    result = check_bibliography(BIBLIOGRAPHY, "")
    assert all("Majjhima" not in f["entry"] for f in result["findings"])


def test_a_note_without_a_bibliography_is_clean():
    assert check_bibliography("# Note\n\nText.\n", DOSSIER) == {
        "ok": True,
        "checked": 0,
        "findings": [],
    }


def test_diacritics_do_not_hide_a_match():
    dossier = "karunadasa theravada abhidhamma inquiry nature conditioned reality"
    entry = (
        "## Bibliography\n\n### Secondary Sources\n\n"
        "Karunadasa, Y. *Theravāda Abhidhamma: Its Inquiry into the Nature of "
        "Conditioned Reality*. (Calibre #1)\n"
    )
    assert check_bibliography(entry, dossier)["ok"] is True
