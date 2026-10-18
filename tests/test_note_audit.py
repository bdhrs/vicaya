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
