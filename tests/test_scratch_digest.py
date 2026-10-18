"""Tests for the dossier digest that replaces `cat`-ing a huge dossier (#109).

The entries are copied from the real dossier 2026-10-16-saddha-faith, with the
hit text shortened so the fixture stays small.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

from tools.scratch import scratch_digest

ROOT = Path(__file__).resolve().parents[1]

_HITS = [
    {
        "book_code": "s0101m_mul",
        "paranum": "1",
        "pali": "1. Evaṃ me sutaṃ – ekaṃ samayaṃ bhagavā antarā ca rājagahaṃ",
        "english": "1. Thus have I heard. At one time the Blessed One was traveling",
    },
    {
        "book_code": "s0101m_mul",
        "paranum": "2",
        "pali": "2. Atha kho bhagavā ambalaṭṭhikāyaṃ rājāgārake ekarattivāsaṃ",
        "english": "2. Then the Blessed One, together with the company of monks",
    },
    {
        "book_code": "s0101m_mul",
        "paranum": "11",
        "pali": "11. ‘‘‘Yathā vā paneke bhonto samaṇabrāhmaṇā saddhādeyyāni",
        "english": "11. Whereas some honorable ascetics and brahmins, having partaken",
    },
]
_SUMMARY = (
    "Vault search: no dedicated saddhā note exists; 12 related notes to "
    "cross-link and build on: (1) pancindriya-pancabala note"
)

DOSSIER = (
    "# Vicaya dossier — saddha-faith\n"
    "**Slug:** saddha-faith\n\n"
    "## Phase log\n\n"
    "## Phase 0 — Request understanding\n\n"
    "### PHASE 0 EXIT GATE\n"
    "- timestamp: 2026-10-16T14:21:38\n\n"
    "## Phase 1 — Vault / EBC\n\n"
    "### 2026-10-16T14:24:12 · note\n"
    "- args: `vault-hits`\n"
    f"- summary: {_SUMMARY}\n\n"
    "## Phase 2 — Canon\n\n"
    "### 2026-10-16T14:30:18 · search-canon\n"
    "- args: `saddh --books s*_mul vin*_mul --lang pali --limit 20`\n"
    "- hits: 20\n"
    "- results:\n"
    "```json\n" + json.dumps(_HITS, ensure_ascii=False, indent=2) + "\n```\n\n"
)


def _write(tmp_path: Path) -> Path:
    path = tmp_path / "2026-10-16-saddha-faith.md"
    path.write_text(DOSSIER, encoding="utf-8")
    return path


def test_digest_keeps_own_notes_and_shortens_hits(tmp_path):
    out = scratch_digest(scratch=_write(tmp_path), top=2)
    assert _SUMMARY in out
    assert "· s0101m_mul:1 — 1. Thus have I heard" in out
    assert "· s0101m_mul:2 — 2. Then the Blessed One" in out
    assert "s0101m_mul:11" not in out
    assert "… 1 more in the dossier entry" in out
    assert "gate: PHASE 0 EXIT GATE" in out


def test_digest_line_numbers_point_at_the_entry(tmp_path):
    path = _write(tmp_path)
    out = scratch_digest(scratch=path)
    line = int(
        next(
            row
            for row in out.splitlines()
            if "search-canon" in row and row.startswith("L")
        ).split()[0][1:]
    )
    assert (
        path.read_text(encoding="utf-8")
        .splitlines()[line - 1]
        .endswith("· search-canon")
    )


def test_digest_can_be_limited_to_one_phase(tmp_path):
    out = scratch_digest(scratch=_write(tmp_path), phase="2")
    assert "search-canon" in out
    assert _SUMMARY not in out


def test_digest_is_much_smaller_than_a_dossier_full_of_hits(tmp_path):
    path = tmp_path / "big.md"
    entry = (
        "### 2026-10-16T14:30:18 · search-canon\n- args: `x`\n- hits: 200\n"
        "- results:\n```json\n"
        + json.dumps(_HITS * 70, ensure_ascii=False, indent=2)
        + "\n```\n\n"
    )
    path.write_text(DOSSIER + entry * 40, encoding="utf-8")
    digest = scratch_digest(scratch=path)
    assert len(digest) * 20 < path.stat().st_size


def test_cli_reads_the_dossier_the_environment_names(tmp_path):
    path = _write(tmp_path)
    run = subprocess.run(
        [sys.executable, "tools/research_sources.py", "scratch-digest"],
        capture_output=True,
        text=True,
        cwd=ROOT,
        stdin=subprocess.DEVNULL,
        env={**os.environ, "VICAYA_SCRATCH": str(path)},
    )
    assert run.returncode == 0, run.stderr
    assert "s0101m_mul:1" in run.stdout
