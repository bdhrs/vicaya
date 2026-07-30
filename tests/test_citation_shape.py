"""Structural malformed-reference detection (thread 20260729_citation-gate-backtest).

Every `depth` fixture below is a real reference found in the vault during the
thread's Phase 1 corpus scan, not an invented case.
"""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tools.research_sources import (  # noqa: E402
    check_citation_shape,
    check_citation_shape_file,
)


def verdicts(text: str) -> list[str]:
    return [f["verdict"] for f in check_citation_shape(text)]


@pytest.mark.parametrize(
    "ref",
    [
        "MN118.150",  # MN118 §150 — paranum glued to the sutta number
        "MN118.152",
        "DN22.385",
        "DN2.244",
        "DN 2.244",
        "Khp 5.10",
        "SN 5.46.20",  # three segments; SN addresses saṃyutta.sutta
        "SN 4.35.45",
        "SN 5.51.4",
    ],
)
def test_real_vault_defects_flagged_as_depth(ref):
    findings = check_citation_shape(f"See {ref} for the passage.")
    assert [f["verdict"] for f in findings] == ["depth"], ref
    assert findings[0]["ref"].startswith(ref.split()[0])


@pytest.mark.parametrize(
    "ref",
    [
        "MN 22",
        "MN22",
        "DN1",
        "DN 33",
        "SN 22.59",
        "SN22.59",
        "SN12",
        "AN3.137",
        "AN 3.137",
        "AN6",
        "Dhp 279",
        "Snp 1.2",
        "Ud 5.5",
        "Thag 16.1",
        "Khp 6",
    ],
)
def test_well_formed_references_not_flagged(ref):
    assert check_citation_shape(f"See {ref} for the passage.") == []


@pytest.mark.parametrize(
    "text",
    [
        "Vinaya 02 §679 — the anāpatti clause.",  # book + § suffix, not depth
        "Vin 02 §16 gives the ruling.",
        "AN1.41-50 §48 on lahuparivatta.",  # range plus § suffix
        "AN1.41-50 para 49 likewise.",
        "Dhp 277–279 as a triad.",
        "SN12.39–40 pair up.",
        "MN58 para 86 is the locus.",
        "AN 3 collects the Threes.",  # bare nipāta, prose
        "The Vinaya's rule code is later.",  # bare collection name
        "Visuddhimagga §176 on ekacittakkhaṇika.",
    ],
)
def test_shapes_that_must_not_flag(text):
    assert check_citation_shape(text) == [], text


@pytest.mark.parametrize(
    "text",
    [
        "See https://suttacentral.net/ud73/en/sujato for the verse.",
        "See https://suttacentral.net/an107/pli/ms text.",
        "The file `dn.02.0` holds it.",
        "Stored as `s0201m_mul:204` in the table.",
    ],
)
def test_urls_and_code_spans_are_skipped(text):
    """SuttaCentral uids and CST filenames are machine data, not citations."""
    assert check_citation_shape(text) == [], text


@pytest.mark.parametrize("ref", ["Ud 73", "Iti 75", "Snp 1068", "Thag 591"])
def test_global_verse_numbers_are_not_flagged(ref):
    """Ud/Iti/Snp/Thag are cited both by chapter.sutta and by global number."""
    assert check_citation_shape(f"See {ref} for the verse.") == []


def test_unhandled_collections_are_silent():
    assert check_citation_shape("Mil 4.2 and Nett 12.3 and Ps 1.2.3") == []


def test_finding_carries_line_and_context():
    text = "intro line\nsecond line cites MN118.150 mid-sentence\ntrailer"
    (finding,) = check_citation_shape(text)
    assert finding["line"] == 2
    assert finding["expected_segments"] == 1
    assert finding["found_segments"] == 2
    assert "mid-sentence" in finding["context"]


def test_multiple_findings_on_one_line_all_reported():
    assert verdicts("Both MN118.150 and DN2.244 are wrong.") == ["depth", "depth"]


def test_case_insensitive_collection_match():
    assert verdicts("see mn118.150 here") == ["depth"]


def test_file_helper_adds_path(tmp_path):
    note = tmp_path / "note.md"
    note.write_text("cites MN118.150 here\n", encoding="utf-8")
    (finding,) = check_citation_shape_file(note)
    assert finding["file"] == str(note)
    assert finding["verdict"] == "depth"


CORPUS_REGRESSION_NOTE = """\
**Arising (MN118.150):** body-contemplation passage.[^MN118.152]

**DN2.244 — the three knowledges (*tevijjā*):** listed here.

- **SN 5.46.20**
- **SN 4.35.45**

Maṅgalasutta (Khp 5.10) example, and DN22.385 for the template.

The word *khaṇa* appears at SN 1.4.6 in the non-technical sense.
"""


def test_every_real_corpus_defect_shape_still_caught(tmp_path):
    """All six malformed shapes found in the 2026-07-29 vault backtest.

    Each was graded a real defect and corrected. If this test stops failing on
    any of them, the check has regressed and the class can return unnoticed.
    """
    note = tmp_path / "regression.md"
    note.write_text(CORPUS_REGRESSION_NOTE, encoding="utf-8")
    flagged = {f["ref"] for f in check_citation_shape_file(note)}
    for ref in (
        "MN118.150",
        "MN118.152",
        "DN2.244",
        "SN 5.46.20",
        "SN 4.35.45",
        "Khp 5.10",
        "DN22.385",
        "SN 1.4.6",
    ):
        assert any(hit.startswith(ref) for hit in flagged), f"{ref} not flagged"


def test_corrected_forms_of_corpus_defects_are_clean(tmp_path):
    """The replacements actually written into the vault must not re-trip."""
    note = tmp_path / "corrected.md"
    note.write_text(
        "**Arising (MN118 §150):** and MN118 §152 and DN2 §244.\n"
        "- SN 46.20\n- SN 35.45\n- SN 51.4\n"
        "Maṅgalasutta (Khp 5, v. 10) and DN22 §385.\n"
        "SN 35.135 *Khaṇasuttaṃ* on the moment.\n"
        "Footnote anchors [^MN118-para150] and [^DN22-para385] too.\n",
        encoding="utf-8",
    )
    assert check_citation_shape_file(note) == []


def test_clean_file_yields_no_findings(tmp_path):
    note = tmp_path / "clean.md"
    note.write_text("cites MN 22 and SN 22.59 and Vinaya 02 §679\n", encoding="utf-8")
    assert check_citation_shape_file(note) == []
