"""Tests for whole-paragraph lookup and the quote-in-cited-paragraph check.

Rows are copied from the real CST canon db (s0202m_mul ids 155–161 and
1231–1232, s0501m_mul ids 14 and 30); long rows keep their real opening only.
"""

from __future__ import annotations

import sqlite3
import sys
from pathlib import Path

import pytest

from tools.canon_paragraphs import check_quotes, get_paragraph, paranum_numbers

_MN_ROWS = [
    (
        155,
        "bodytext",
        "60",
        '<p rend="bodytext" n="60"><hi rend="paranum">60</hi><hi rend="dot">.</hi> '
        "Evaṃ vutte, dīghatapassī nigaṇṭho nigaṇṭhaṃ nāṭaputtaṃ etadavoca – ‘‘na kho "
        "metaṃ, bhante, ruccati.</p>",
    ),
    (
        156,
        "bodytext",
        "",
        '<p rend="bodytext">‘‘Āgamā khvidha, gahapati, dīghatapassī nigaṇṭho’’ti.</p>',
    ),
    (
        157,
        "bodytext",
        "",
        '<p rend="bodytext">‘‘Ahu kho pana te, bhante, dīghatapassinā nigaṇṭhena '
        "saddhiṃ kocideva kathāsallāpo’’ti?</p>",
    ),
    (
        158,
        "bodytext",
        "",
        '<p rend="bodytext">‘‘Ahu kho me, gahapati, dīghatapassinā nigaṇṭhena saddhiṃ '
        "kocideva kathāsallāpo’’ti.</p>",
    ),
    (
        159,
        "bodytext",
        "",
        '<p rend="bodytext">‘‘Yathā kathaṃ pana te, bhante, ahu dīghatapassinā '
        "nigaṇṭhena saddhiṃ kocideva kathāsallāpo’’ti?</p>",
    ),
    (
        160,
        "bodytext",
        "",
        '<p rend="bodytext">Atha kho bhagavā yāvatako ahosi dīghatapassinā nigaṇṭhena '
        "saddhiṃ kathāsallāpo taṃ sabbaṃ upālissa gahapatissa ārocesi.</p>",
    ),
    (
        161,
        "bodytext",
        "61",
        '<p rend="bodytext" n="61"><hi rend="paranum">61</hi><hi rend="dot">.</hi> '
        "Evaṃ vutte, upāli gahapati bhagavantaṃ etadavoca – ‘‘sādhu sādhu, bhante "
        "tapassī!</p>",
    ),
    (
        1231,
        "bodytext",
        "429",
        '<p rend="bodytext" n="429"><hi rend="paranum">429</hi><hi rend="dot">.</hi> '
        "‘‘Saddhā cepi, bhāradvāja, purisassa hoti; ‘evaṃ me saddhā’ti – iti vadaṃ "
        "saccamanurakkhati <note>evameva sijjhatīti iti vā, taṃ saccamanurakkhati "
        '(ka.)</note>, natveva tāva ekaṃsena niṭṭhaṃ gacchati <pb ed="T" n="2.0602" /> '
        "– ‘idameva saccaṃ, moghamañña’nti.</p>",
    ),
    (
        1232,
        "bodytext",
        "430",
        '<p rend="bodytext" n="430"><hi rend="paranum">430</hi><hi rend="dot">.</hi> '
        "‘‘Ettāvatā, bho gotama, saccānurakkhaṇā hoti, ettāvatā saccamanurakkhati, "
        "ettāvatā ca mayaṃ saccānurakkhaṇaṃ pekkhāma.</p>",
    ),
]

# DN31: a verse row with no paranum of its own, ending in "-ī’’ti".
_DN_ROWS = [
    (
        692,
        "bodytext",
        "265",
        '<p rend="bodytext" n="265"><hi rend="paranum">265</hi><hi rend="dot">.</hi> '
        "Idamavoca bhagavā, idaṃ vatvāna sugato athāparaṃ etadavoca satthā –</p>",
    ),
    (
        697,
        "gatha",
        "",
        '<p rend="gatha1">‘‘Ekena bhoge bhuñjeyya, dvīhi kammaṃ payojaye;</p>'
        '<p rend="gathalast">Catutthañca nidhāpeyya, āpadāsu bhavissatī’’ti.</p>',
    ),
]

# Khuddakapāṭha restarts its paragraph numbers in each section.
_KHP_ROWS = [
    (
        14,
        "bodytext",
        "5",
        '<p rend="bodytext" n="5"><hi rend="paranum">5</hi><hi rend="dot">.</hi> '
        "Surāmerayamajjapamādaṭṭhānā veramaṇī-sikkhāpadaṃ</p>",
    ),
    (20, "subhead", "", '<p rend="subhead">4. Kumārapañhā</p>'),
    (
        30,
        "bodytext",
        "5",
        '<p rend="bodytext" n="5"><hi rend="paranum">5</hi><hi rend="dot">.</hi> '
        "‘‘Pañca nāma kiṃ’’? ‘‘Pañcupādānakkhandhā’’.</p>",
    ),
]


@pytest.fixture
def canon_db(tmp_path: Path) -> Path:
    path = tmp_path / "canon.db"
    with sqlite3.connect(path) as conn:
        for table, rows in (
            ("s0202m_mul", _MN_ROWS),
            ("s0103m_mul", _DN_ROWS),
            ("s0501m_mul", _KHP_ROWS),
        ):
            conn.execute(
                f"CREATE TABLE {table} (id INTEGER PRIMARY KEY, rend TEXT, "
                "paranum TEXT, pali_text TEXT, english_translation TEXT)"
            )
            conn.executemany(f"INSERT INTO {table} VALUES (?, ?, ?, ?, '')", rows)
    return path


@pytest.fixture
def dpd_db(tmp_path: Path) -> Path:
    """Only the slice of `sutta_info` the label resolver reads."""
    path = tmp_path / "dpd.db"
    with sqlite3.connect(path) as conn:
        conn.execute(
            "CREATE TABLE sutta_info (dpd_code TEXT, sc_code TEXT, "
            "cst_sutta TEXT, cst_file TEXT, cst_paranum INTEGER)"
        )
        conn.executemany(
            "INSERT INTO sutta_info VALUES (?, ?, ?, ?, ?)",
            [
                ("MN56", "MN56", "1. Upālisuttaṃ", "romn/s0202m.mul.xml", 60),
                ("MN95", "MN95", "2. Caṅkīsuttaṃ", "romn/s0202m.mul.xml", 429),
                ("DHP212-216", "Dhp212-216", "Piyavaggo", "romn/s0502m.mul.xml", 216),
            ],
        )
    return path


@pytest.mark.parametrize(
    ("cell", "numbers"),
    [
        ("97", {97}),
        ("583-4", {583, 584}),
        ("133-4", {133, 134}),
        ("575-576", {575, 576}),
        ("", set()),
    ],
)
def test_paranum_numbers(cell: str, numbers: set[int]) -> None:
    assert paranum_numbers(cell) == numbers


def test_paragraph_includes_its_continuation_rows(canon_db: Path) -> None:
    result = get_paragraph("s0202m_mul", 60, canon_db=canon_db)

    occurrence = result["occurrences"][0]
    assert (occurrence["first_row_id"], occurrence["last_row_id"]) == (155, 160)
    assert occurrence["pali"].endswith("upālissa gahapatissa ārocesi.")


def test_row_id_maps_to_the_paragraph_that_holds_it(canon_db: Path) -> None:
    # Issue #124: row 158 was cited as "para 158"; it is inside paragraph 60.
    result = get_paragraph("s0202m_mul", row_id=158, canon_db=canon_db)

    assert result["paranum"] == "60"
    assert "never the row id" in result["note"]


def test_variant_readings_and_markup_are_removed(canon_db: Path) -> None:
    pali = get_paragraph("s0202m_mul", 429, canon_db=canon_db)["occurrences"][0]["pali"]

    assert "(ka.)" not in pali and "<" not in pali
    assert "saccamanurakkhati , natveva tāva" in pali


def test_restarting_numbers_return_every_occurrence(canon_db: Path) -> None:
    result = get_paragraph("s0501m_mul", 5, canon_db=canon_db)

    assert len(result["occurrences"]) == 2
    assert "occurs 2 times" in result["warning"]


def test_missing_paragraph_is_refused(canon_db: Path) -> None:
    result = get_paragraph("s0202m_mul", 999, canon_db=canon_db)

    assert result["ok"] is False
    assert "do not cite" in result["error"]


def _note(quote: str, para: str = "60") -> str:
    return (
        "## Canon Evidence (T1)\n\n"
        f"**MN56 Upālisuttaṃ para {para}**\n\n"
        f"> {quote}[^s0202m-{para}]\n\n"
        "> Then the Buddha told Upāli the householder the whole conversation.\n\n"
        f"[^s0202m-{para}]: MN56 Upālisuttaṃ para {para} — db: s0202m_mul, para {para}\n"
    )


_CONTINUATION_QUOTE = (
    "Atha kho bhagavā yāvatako ahosi dīghatapassinā nigaṇṭhena saddhiṃ "
    "kathāsallāpo taṃ sabbaṃ upālissa gahapatissa ārocesi."
)


def test_quote_from_a_continuation_row_matches_its_paragraph(canon_db: Path) -> None:
    result = check_quotes(_note(_CONTINUATION_QUOTE), canon_db)

    assert result["checked"] == 1
    assert result["findings"] == []


def test_quote_cited_to_the_wrong_paragraph_names_the_right_one(
    canon_db: Path,
) -> None:
    result = check_quotes(_note(_CONTINUATION_QUOTE, para="61"), canon_db)

    assert [(f["verdict"], f["found_in"]) for f in result["findings"]] == [
        ("in-other-paragraph", ["60"])
    ]


def test_quote_matches_despite_spacing_variants_and_sandhi(canon_db: Path) -> None:
    # The note's own spelling (real, 2026-09-08 saccanurakkhana note): "na
    # tveva" where the canon has "natveva", plain quotes, and a variant
    # reading the canon carries inline.
    quote = (
        "Saddhā cepi, bhāradvāja, purisassa hoti; 'evaṃ me saddhā'ti — iti vadaṃ "
        "saccamanurakkhati, na tveva tāva ekaṃsena niṭṭhaṃ gacchati: 'idameva "
        "saccaṃ, moghamaññan'ti."
    )

    assert check_quotes(_note(quote, para="429"), canon_db)["findings"] == []


def test_quote_finished_from_memory_is_not_found(canon_db: Path) -> None:
    # Issue #96: the opening is right, the ending was supplied from memory.
    quote = (
        "Saddhā cepi, bhāradvāja, purisassa hoti; 'evaṃ me saddhā'ti — iti vadaṃ "
        "saccamanurakkhati, na tveva tāva ekaṃsena aññaṃ byākaroti."
    )

    findings = check_quotes(_note(quote, para="429"), canon_db)["findings"]

    assert [f["verdict"] for f in findings] == ["not-found"]
    matched, total = findings[0]["matched_words"].split("/")
    assert 0 < int(matched) < int(total)


def test_quote_ending_before_ti_drops_the_long_vowel(canon_db: Path) -> None:
    # Real note text (2026-08-22 sutta-financial-advice): the quote stops at
    # "bhavissati" where the canon reads "bhavissatī’’ti".
    note = (
        "> Ekena bhoge bhuñjeyya, dvīhi kammaṃ payojaye; Catutthañca nidhāpeyya, "
        "āpadāsu bhavissati.[^s0103m-265]\n\n"
        "[^s0103m-265]: DN31 Siṅgālasuttaṃ para 265 — db: s0103m_mul, para 265\n"
    )

    result = check_quotes(note, canon_db)

    assert result["checked"] == 1
    assert result["findings"] == []


def test_gap_marked_with_dots_splits_the_quote(canon_db: Path) -> None:
    quote = (
        "Saddhā cepi, bhāradvāja, purisassa hoti ... natveva tāva ekaṃsena "
        "niṭṭhaṃ gacchati"
    )

    assert check_quotes(_note(quote, para="429"), canon_db)["findings"] == []


def test_label_inside_the_quote_is_ignored(canon_db: Path) -> None:
    assert (
        check_quotes(_note("— Pāḷi: " + _CONTINUATION_QUOTE), canon_db)["findings"]
        == []
    )


def test_citation_of_a_missing_paragraph_is_reported(canon_db: Path) -> None:
    findings = check_quotes(_note(_CONTINUATION_QUOTE, para="999"), canon_db)[
        "findings"
    ]

    assert [f["verdict"] for f in findings] == ["no-such-paragraph"]


def test_check_quotes_cli_exits_1_on_findings(
    canon_db: Path, tmp_path: Path, monkeypatch, capsys
) -> None:
    import tools.research_sources as rs

    note = tmp_path / "note.md"
    note.write_text(_note(_CONTINUATION_QUOTE, para="61"), encoding="utf-8")
    monkeypatch.setattr(rs, "DEFAULT_CANON_DB", canon_db)
    monkeypatch.setattr(sys, "argv", ["research_sources.py", "check-quotes", str(note)])

    assert rs._cli() == 1
    assert "in-other-paragraph" in capsys.readouterr().out


def test_get_paragraph_cli_needs_exactly_one_locator(monkeypatch, capsys) -> None:
    import tools.research_sources as rs

    monkeypatch.setattr(
        sys, "argv", ["research_sources.py", "get-paragraph", "s0202m_mul"]
    )

    assert rs._cli() == 2
    assert "exactly one of" in capsys.readouterr().out


@pytest.mark.parametrize(
    ("cell", "numbers"),
    [("18-19-20", {18, 19, 20}), ("179-", {179}), ("1699-700", {1699, 1700})],
)
def test_odd_paranum_cells_from_the_real_db(cell: str, numbers: set[int]) -> None:
    assert paranum_numbers(cell) == numbers


def test_paragraph_stops_at_a_heading(canon_db: Path) -> None:
    first = get_paragraph("s0501m_mul", 5, canon_db=canon_db)["occurrences"][0]

    assert first["last_row_id"] == 14


_PARA_429_QUOTE = (
    "Saddhā cepi, bhāradvāja, purisassa hoti; 'evaṃ me saddhā'ti — iti vadaṃ "
    "saccamanurakkhati"
)
_DEFS = (
    "[^a]: MN56 Upālisuttaṃ para 60 — db: s0202m_mul, para 60\n"
    "[^b]: MN95 Caṅkīsuttaṃ para 429 — db: s0202m_mul, para 429\n"
)


def test_each_quote_in_a_run_uses_its_own_footnote(canon_db: Path) -> None:
    # Review finding: a run of quotes, each with its own footnote, was checked
    # against the run's last footnote (real case: 2026-10-16 saddha-faith).
    note = (
        "**Two passages**\n\n"
        f"> {_CONTINUATION_QUOTE}[^a]\n\n"
        f"> {_PARA_429_QUOTE}[^b]\n\n" + _DEFS
    )

    result = check_quotes(note, canon_db)

    assert result["checked"] == 2
    assert result["findings"] == []


def test_footnote_on_the_translation_pairs_the_pali_above_it(canon_db: Path) -> None:
    note = (
        f"> {_PARA_429_QUOTE}\n\n"
        "> If a person has faith, they preserve truth when they say so.[^b]\n\n" + _DEFS
    )

    assert check_quotes(note, canon_db)["checked"] == 1


def test_prose_footnote_above_a_quote_is_not_borrowed(canon_db: Path) -> None:
    # Review finding: a DN16 quote took the MN136 footnote of the paragraph
    # above it (real case: 2026-06-19 a-good-death-in-buddhism).
    note = f"The Buddha said as much elsewhere.[^a]\n\n> {_PARA_429_QUOTE}\n\n" + _DEFS

    result = check_quotes(note, canon_db)

    assert (result["checked"], result["unpaired"], result["findings"]) == (0, 1, [])


def test_commentary_label_does_not_pair_with_the_mula_number(canon_db: Path) -> None:
    # Review finding: "Khuddakapāṭha-aṭṭhakathā on para 15" paired commentary
    # text with mūla paragraph 15 (real case: 2026-06-14 note).
    note = f"**MN95-aṭṭhakathā on para 429**\n\n> {_CONTINUATION_QUOTE}\n\n" + _DEFS

    result = check_quotes(note, canon_db)

    assert (result["checked"], result["unpaired"]) == (0, 1)


def test_abbreviated_range_footnote_covers_both_paragraphs(canon_db: Path) -> None:
    note = (
        "> Evaṃ vutte, upāli gahapati bhagavantaṃ etadavoca[^r]\n\n"
        "[^r]: MN56 Upālisuttaṃ para 60-1 — db: s0202m_mul, para 60-1\n"
    )

    assert check_quotes(note, canon_db)["findings"] == []


def test_footnote_citing_a_row_id_is_a_finding(canon_db: Path) -> None:
    # Issue #124 written into the note itself (real form: "s0304m_mul id 1739").
    note = (
        f"> {_CONTINUATION_QUOTE}[^x]\n\n"
        "[^x]: MN56 Upālisuttaṃ — db: s0202m_mul, id 158\n"
    )

    findings = check_quotes(note, canon_db)["findings"]

    assert findings == [
        {
            "line": 3,
            "verdict": "row-id-citation",
            "cites": "s0202m_mul id 158",
            "cite_as": "db: s0202m_mul, para 60",
        }
    ]


def test_not_found_names_the_closest_paragraph(canon_db: Path) -> None:
    quote = _PARA_429_QUOTE + ", na tveva tāva ekaṃsena aññaṃ byākaroti."
    note = f"> {quote}[^a]\n\n" + _DEFS

    finding = check_quotes(note, canon_db)["findings"][0]

    assert finding["verdict"] == "not-found"
    assert finding["closest_paragraph"] == "429"


def test_get_paragraph_quiet_keeps_the_full_text(
    canon_db: Path, monkeypatch, capsys
) -> None:
    import json

    import tools.research_sources as rs

    monkeypatch.setenv("VICAYA_SCRATCH", "/dev/null/none")
    monkeypatch.setattr(rs, "DEFAULT_CANON_DB", canon_db)
    monkeypatch.setattr(
        sys,
        "argv",
        ["research_sources.py", "get-paragraph", "s0202m_mul", "60", "--quiet"],
    )

    assert rs._cli() == 0
    pali = json.loads(capsys.readouterr().out)["occurrences"][0]["pali"]
    assert pali.endswith("upālissa gahapatissa ārocesi.")


def test_speaker_labels_inside_a_quote_are_ignored(canon_db: Path) -> None:
    # Real label form (2026-06-13 mind-travel note: 'Ānanda: "Abhijānāti …"').
    # The note's own colon after "gacchati" in the 429 quote must survive.
    quote = (
        f'Bhagavā: "{_CONTINUATION_QUOTE}" … Upāli: "Evaṃ vutte, upāli gahapati '
        'bhagavantaṃ etadavoca"'
    )
    note = (
        f"> {quote}[^r]\n\n"
        "[^r]: MN56 Upālisuttaṃ para 60-1 — db: s0202m_mul, para 60-1\n"
    )

    assert check_quotes(note, canon_db)["findings"] == []


# --- issue #157: the note template's own `- Pāḷi:` bullet format ---------------
#
# The template writes evidence as a bold label bullet with a nested Pāḷi bullet:
#   - **MN56 Upālisuttaṃ para 60**
#     - Pāḷi: "…"
# `check-quotes` only read `>` blockquotes, so every such quote was never
# tested. Fixtures below use the real rows the module already carries.


def test_template_bullet_quote_is_checked(canon_db: Path, dpd_db: Path) -> None:
    note = (
        "- **MN56 Upālisuttaṃ para 60** (T1a)\n"
        f'  - Pāḷi: "{_CONTINUATION_QUOTE}"\n'
        '  - English: "Then the householder Upāli said to the Blessed One…"\n'
    )

    result = check_quotes(note, canon_db, dpd_db)

    assert result["findings"] == []
    assert (result["bullet_checked"], result["checked"]) == (1, 1)


def test_template_bullet_finished_from_memory_is_found(canon_db: Path) -> None:
    # The real failure mode: a quote that drifts after a correct opening.
    quote = _PARA_429_QUOTE + ", idaṃ na bhavati kvaci."
    note = f'- **MN95 Caṅkīsuttaṃ s0202m_mul para 429**\n  - Pāḷi: "{quote}"\n'

    finding = check_quotes(note, canon_db)["findings"][0]

    assert finding["verdict"] == "not-found"
    assert finding["format"] == "bullet"
    # The opening is right, so the cited paragraph is still the closest one.
    assert "closest_paragraph" not in finding
    assert finding["matched_words"] == "11/15"


def test_template_bullet_can_cite_a_table_code(canon_db: Path) -> None:
    note = (
        f'- **MN95 Caṅkīsuttaṃ s0202m_mul para 429**\n  - Pāḷi: "{_PARA_429_QUOTE}"\n'
    )

    result = check_quotes(note, canon_db)

    assert (result["bullet_checked"], result["findings"]) == (1, [])


def test_template_bullet_beside_a_blockquote_both_count(
    canon_db: Path, dpd_db: Path
) -> None:
    note = (
        f"> {_CONTINUATION_QUOTE}[^a]\n\n" + _DEFS + "\n"
        "- **MN95 Caṅkīsuttaṃ para 429**\n"
        f'  - Pāḷi: "{_PARA_429_QUOTE}"\n'
    )

    result = check_quotes(note, canon_db, dpd_db)

    # The footnote still pairs the blockquote; the bullet pairs by its label.
    assert (result["checked"], result["bullet_checked"]) == (2, 1)


def test_template_bullet_without_a_paragraph_is_reported_unpaired(
    canon_db: Path, dpd_db: Path
) -> None:
    # Real form (2026-10-28 udāna note): a label naming the source but no para.
    note = f'- **MN56 Upālisuttaṃ**\n  - Pāḷi: "{_CONTINUATION_QUOTE}"\n'

    result = check_quotes(note, canon_db, dpd_db)

    assert result["findings"] == []
    assert result["bullet_checked"] == 0
    assert result["bullet_unpaired"] == [
        {
            "line": 2,
            "label_line": 1,
            "reason": "label names s0202m_mul but no paragraph number",
        }
    ]


def test_template_bullet_label_outside_canon_is_skipped(canon_db: Path) -> None:
    # A commentary label names no table code, so it is not tested against the
    # mūla paragraph of the same number (the blockquote path's old trap).
    note = f'- **Papañcasūdanī on MN 10 §113**\n  - Pāḷi: "{_CONTINUATION_QUOTE}"\n'

    result = check_quotes(note, canon_db)

    assert result["checked"] == 0
    assert result["findings"] == []
    assert result["bullet_skipped"] == {"label names no canon table or sutta code": 1}


def test_template_bullet_english_text_is_not_a_quote(canon_db: Path) -> None:
    # Real form: a bullet holding a note-to-self instead of Pāḷi.
    note = (
        "- **MN119 Kāyagatāsatisuttaṃ para 154**\n"
        "  - Pāḷi: (mindfulness of the body, cited as the anchor — see para 154)\n"
    )

    result = check_quotes(note, canon_db)

    assert result["checked"] == 0
    assert result["findings"] == []
    assert result["bullet_skipped"] == {"no Pāḷi text in the bullet": 1}


def test_sutta_code_label_resolves_through_the_dpd_db(
    canon_db: Path, dpd_db: Path
) -> None:
    # The template's commonest label names a DPD code, not a CST table
    # ("MN56 … para 60"); sutta_info.cst_file carries the table.
    note = f'- **MN56 Upālisuttaṃ para 60**\n  - Pāḷi: "{_CONTINUATION_QUOTE}"\n'

    result = check_quotes(note, canon_db, dpd_db)

    assert (result["bullet_checked"], result["findings"]) == (1, [])


def test_dhp_range_code_resolves_to_its_book(dpd_db: Path) -> None:
    # Dhp labels come as verse ranges ("Dhp212-216"), which sutta_info holds as
    # one range row rather than one row per verse.
    from tools.canon_paragraphs import _dpd_code_table

    assert _dpd_code_table("Dhp212-216", dpd_db, {}) == "s0502m_mul"
    assert _dpd_code_table("MN56", dpd_db, {}) == "s0202m_mul"
    assert _dpd_code_table("ZZ99", dpd_db, {}) is None
