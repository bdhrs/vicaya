"""Tests for the canon-wide term sweep behind absence and frequency claims.

Rows are copied whole from the real CST canon db: s0201m_mul ids 3, 295,
435–436 (MN 12), s0102m_mul id 656 (DN 17 §269), abh02t_tik id 293,
s0516m_mul id 750, s0305m_mul id 779, s0517m_mul id 654, s0505m_mul id 640.
"""

from __future__ import annotations

import json
import re
import sqlite3
import sys
from pathlib import Path

import pytest

from tools.canon_sweep import sweep_canon, stratum
from tools.research_sources import DEFAULT_CANON_DB

canon_available = pytest.mark.skipif(
    DEFAULT_CANON_DB is None or not DEFAULT_CANON_DB.exists(),
    reason="canon db not available",
)

_ROWS: dict[str, list[tuple[int, str, str, str]]] = {
    "s0201m_mul": [
        (3, "book", "", '<head rend="book">Mūlapaṇṇāsapāḷi</head>'),
        (
            295,
            "bodytext",
            "",
            '<p rend="bodytext">‘‘Seyyathāpi<pb ed="P" n="1.0058" />, bhikkhave, dakkho goghātako vā goghātakantevāsī vā gāviṃ vadhitvā catumahāpathe <note>cātummahāpathe (sī. syā. pī.)</note> bilaso vibhajitvā nisinno assa. Evameva kho, bhikkhave, bhikkhu imameva kāyaṃ yathāṭhitaṃ yathāpaṇihitaṃ dhātuso paccavekkhati – ‘atthi imasmiṃ kāye pathavīdhātu āpodhātu tejodhātu vāyodhātū’ti. Iti ajjhattaṃ vā kāye kāyānupassī viharati…pe… <pb ed="V" n="1.0075" /> evampi kho, bhikkhave<pb ed="T" n="1.0107" />, bhikkhu kāye kāyānupassī viharati.</p>',
        ),
        (
            435,
            "bodytext",
            "147",
            '<p rend="bodytext" n="147"><hi rend="paranum">147</hi><hi rend="dot">.</hi> ‘‘Kodhano heso, sāriputta, sunakkhatto moghapuriso. Kodhā ca panassa esā vācā bhāsitā. ‘Avaṇṇaṃ bhāsissāmī’ti kho, sāriputta, sunakkhatto moghapuriso vaṇṇaṃyeva tathāgatassa <pb ed="V" n="1.0100" /> bhāsati<pb ed="P" n="1.0069" />. Vaṇṇo heso, sāriputta, tathāgatassa yo evaṃ vadeyya – ‘yassa ca khvāssa atthāya dhammo desito so niyyāti takkarassa sammā dukkhakkhayāyā’ti.</p>',
        ),
        (
            436,
            "bodytext",
            "",
            '<p rend="bodytext">‘‘Ayampi hi nāma, sāriputta, sunakkhattassa moghapurisassa mayi dhammanvayo na bhavissati – ‘itipi so bhagavā arahaṃ sammāsambuddho vijjācaraṇasampanno sugato lokavidū anuttaro purisadammasārathi, satthā devamanussānaṃ, buddho bhagavā’ti.</p>',
        ),
    ],
    "s0102m_mul": [
        (
            656,
            "bodytext",
            "269",
            '<p rend="bodytext" n="269"><hi rend="paranum">269</hi><hi rend="dot">.</hi> ‘‘Atha <pb ed="V" n="2.0145" /> kho, ānanda, rājā mahāsudassano nacirasseva kālamakāsi. Seyyathāpi, ānanda, gahapatissa vā gahapatiputtassa vā manuññaṃ bhojanaṃ bhuttāvissa bhattasammado hoti, evameva kho, ānanda, rañño mahāsudassanassa <pb ed="P" n="2.0196" /> māraṇantikā vedanā ahosi. Kālaṅkato ca, ānanda, rājā mahāsudassano sugatiṃ brahmalokaṃ upapajji. Rājā, ānanda, mahāsudassano caturāsīti vassasahassāni kumārakīḷaṃ <note>kīḷitaṃ (ka.), kīḷikaṃ (sī. pī.)</note> kīḷi. Caturāsīti vassasahassāni oparajjaṃ kāresi. Caturāsīti vassasahassāni rajjaṃ kāresi. Caturāsīti vassasahassāni gihibhūto <note>gihībhūto (sī. pī.)</note> dhamme pāsāde brahmacariyaṃ cari <note>brahmacariyamacari (ka.)</note>. So cattāro brahmavihāre bhāvetvā kāyassa bhedā paraṃ maraṇā brahmalokūpago ahosi.</p>',
        ),
    ],
    "abh02t_tik": [
        (
            293,
            "bodytext",
            "",
            '<p rend="bodytext"><hi rend="bold">Pāḷiyaṃ vibhattesū</hi>ti katarapāḷiyaṃ? <hi rend="bold">Dhammasaṅgahe</hi> tāva aṭṭha kasiṇāni dasa asubhā cattāro brahmavihārā cattāri āruppāni vibhattāni, <hi rend="bold">āgamesu</hi> dasa anussatiyo āhāre paṭikūlasaññā <pb ed="V" n="0.0073" /> catudhātuvavatthānanti imāni cāti tattha tattha vibhattaṃ. <hi rend="bold">Imesu tīsū</hi>ti kāmādīsu tīsu ṭhānesu.</p>',
        ),
    ],
    "s0516m_mul": [
        (
            750,
            "bodytext",
            "",
            '<p rend="bodytext"><hi rend="bold">Evaṃ</hi> <pb ed="M" n="0.0096" /> <hi rend="bold">tuvaṃ oghamimaṃ taresī</hi>ti evaṃ kāmoghaṃ bhavoghaṃ diṭṭhoghaṃ avijjoghaṃ tareyyāsi uttareyyāsi patareyyāsi samatikkameyyāsi vītivatteyyāsīti – evaṃ tuvaṃ oghamimaṃ taresi. Tenāha bhagavā –</p>',
        ),
    ],
    "s0305m_mul": [
        (779, "subhead", "", '<p rend="subhead">1-8. Oghādisuttaṃ</p>'),
    ],
    "s0517m_mul": [
        (
            654,
            "gatha",
            "",
            '<p rend="gathalast">Sabbaṃ abhiññāsi yadatthi neyyaṃ, tathāgato tena samantacakkhūti <note>mahāni. 156; cūḷani. mogharājamāṇavapucchāniddesa 85</note>.</p>',
        ),
    ],
    "s0505m_mul": [
        (
            640,
            "gatha",
            "",
            '<p rend="gatha1"> Suddhā <pb ed="V" n="0.0127" /> suddhehi saṃvāsaṃ, kappayavho patissatā;</p><p rend="gathalast">Tato samaggā nipakā, dukkhassantaṃ karissathāti.</p>',
        ),
    ],
}


@pytest.fixture
def canon_db(tmp_path: Path) -> Path:
    path = tmp_path / "canon.db"
    with sqlite3.connect(path) as conn:
        for table, rows in _ROWS.items():
            conn.execute(
                f"CREATE TABLE {table} (id INTEGER PRIMARY KEY, rend TEXT, "
                "paranum TEXT, pali_text TEXT, english_translation TEXT)"
            )
            conn.executemany(f"INSERT INTO {table} VALUES (?, ?, ?, ?, '')", rows)
    return path


def _term(result: dict) -> dict:
    return result["terms"][0]


def _layer(entry: dict, name: str) -> dict:
    return next(s for s in entry["by_stratum"] if s["stratum"] == name)


@pytest.mark.parametrize(
    ("table", "layer"),
    [
        ("s0102m_mul", "mula-ebt"),
        ("vin02m1_mul", "mula-ebt"),
        ("s0509m_mul", "mula-ebt"),
        ("vin02m2_mul", "mula-later"),
        ("abh03m10_mul", "mula-later"),
        ("s0513m_mul", "mula-later"),
        ("s0518m_nrf", "mula-later"),
        ("s0517m_mul", "exegetical-mula"),
        ("e0101n_mul", "exegetical-mula"),
        ("s0201a_att", "atthakatha"),
        ("s0201t_tik", "tika"),
        ("e0103n_att", "tika"),
        ("vin05t_nrf", "tika"),
        ("e0801n_nrf", "post-canonical"),
    ],
)
def test_every_table_lands_in_its_tier(table: str, layer: str) -> None:
    assert stratum(table) == layer


def test_phrase_absent_from_the_suttas_is_flagged_when_its_words_are_there(
    canon_db: Path,
) -> None:
    # 20260920-023254 published "the four brahmavihāras is commentarial" from
    # a 0-hit on this exact phrase; DN 17 §269 reads "cattāro brahmavihāre".
    entry = _term(sweep_canon(["cattāro brahmavihārā"], canon_db=canon_db))

    assert _layer(entry, "mula-ebt")["rows"] == 0
    assert _layer(entry, "tika")["rows"] == 1
    together = entry["rows_with_every_word_stem"]["by_stratum"]["mula-ebt"]
    assert together == {"rows": 1, "examples": ["s0102m_mul 269"]}
    assert any("mula-ebt 1" in h for h in entry["hints"])


def test_exclude_drops_noise_by_prefix_and_keeps_compounds(canon_db: Path) -> None:
    # "mogha" (vain) is noise for ogha (flood); kāmoghaṃ is the flood of
    # sensuality and must stay, though it contains "mogha".
    entry = _term(sweep_canon(["ogha"], exclude=["mogha"], canon_db=canon_db))

    forms = {f["form"] for f in entry["forms"]}
    assert "kāmoghaṃ" in forms
    (group,) = entry["excluded"]
    assert (group["prefix"], group["occurrences"], group["distinct_forms"]) == (
        "mogha",
        3,
        2,
    )
    assert _layer(entry, "mula-ebt")["rows"] == 0


def test_a_term_only_in_a_variant_reading_is_counted_apart(canon_db: Path) -> None:
    entry = _term(sweep_canon(["mogharāja"], canon_db=canon_db))

    assert entry["rows"] == 0
    assert entry["variant_only_rows"] == 1


def test_vowel_length_variants_are_reported_in_their_real_spelling(
    canon_db: Path,
) -> None:
    # 20261010-171500 searched long "āvho" and nearly lost the short "avho" set.
    entry = _term(sweep_canon(["āvho"], canon_db=canon_db))
    assert entry["rows"] == 0
    assert entry["vowel_length_variants"]["forms"] == [
        {"form": "kappayavho", "count": 1}
    ]

    # Folding maps ā to a; the reported form must keep the text's own ā.
    ogha = _term(sweep_canon(["ogha"], canon_db=canon_db))
    loose = {f["form"] for f in ogha["vowel_length_variants"]["forms"]}
    assert "oghādisuttaṃ" in loose


def test_continuation_rows_report_their_paragraph_number(canon_db: Path) -> None:
    entry = _term(sweep_canon(["moghapurisassa"], canon_db=canon_db))

    (table,) = entry["tables"]
    assert table["table"] == "s0201m_mul"
    assert table["book"] == "Mūlapaṇṇāsapāḷi"
    assert table["paranums"] == ["147"]


def test_a_limited_sweep_says_it_is_not_canon_wide(canon_db: Path) -> None:
    result = sweep_canon(["ogha"], books=["s*_mul"], canon_db=canon_db)

    # The fixture holds no later-mūla or aṭṭhakathā table, and s*_mul skips
    # the ṭīkā table it does hold.
    assert result["not_searched"] == ["mula-later", "atthakatha", "tika"]
    assert "not canon-wide" in result["warning"]
    assert _layer(_term(result), "tika") == {
        "stratum": "tika",
        "tier": "T2",
        "searched": False,
    }


def test_counts_are_complete_rows_and_occurrences(canon_db: Path) -> None:
    entry = _term(sweep_canon(["moghapuris"], canon_db=canon_db))

    # Row 435 says "moghapuriso" twice; row 436 once.
    assert (entry["rows"], entry["occurrences"]) == (2, 3)


def test_cli_quiet_drops_the_table_list_only(
    canon_db: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture
) -> None:
    import tools.research_sources as rs

    monkeypatch.setenv("VICAYA_SCRATCH", "/dev/null/none")
    monkeypatch.setattr(rs, "DEFAULT_CANON_DB", canon_db)
    monkeypatch.setattr(
        sys,
        "argv",
        ["research_sources.py", "sweep-canon", "ogha", "--exclude", "mogha", "--quiet"],
    )

    assert rs._cli() == 0
    entry = json.loads(capsys.readouterr().out)["terms"][0]
    assert "tables" not in entry
    assert entry["tables_with_hits"] == 1
    assert entry["excluded"][0]["prefix"] == "mogha"


def test_cli_quiet_marks_clipped_forms(
    canon_db: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture
) -> None:
    import tools.research_sources as rs

    monkeypatch.setenv("VICAYA_SCRATCH", "/dev/null/none")
    monkeypatch.setattr(rs, "DEFAULT_CANON_DB", canon_db)

    def run(*extra: str) -> dict:
        monkeypatch.setattr(
            sys, "argv", ["research_sources.py", "sweep-canon", "a", *extra]
        )
        assert rs._cli() == 0
        return json.loads(capsys.readouterr().out)["terms"][0]

    full = run()
    # The fixture holds far more than 10 distinct word forms containing "a".
    assert len(full["forms"]) == 30
    quiet = run("--quiet")
    assert len(quiet["forms"]) == 10
    # Without the marker a 10-form list reads as complete.
    # The full result already counts forms beyond its own cap of 30; the quiet
    # view must add its clipping to that, not replace it.
    assert full["forms_not_shown"] > 0
    assert quiet["forms_not_shown"] == full["forms_not_shown"] + 30 - 10


canon_available = pytest.mark.skipif(
    DEFAULT_CANON_DB is None or not DEFAULT_CANON_DB.exists(),
    reason="canon db not available",
)


@canon_available
def test_the_live_db_holds_only_cst_text_tables() -> None:
    # _resolve_tables filters to the CST shape; this pins that the filter skips
    # nothing today, so tables_searched really is the whole db.
    conn = sqlite3.connect(f"file:{DEFAULT_CANON_DB}?immutable=1", uri=True)
    names = [
        r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
    ]
    assert names and all(re.fullmatch(r"[a-z0-9]+_(mul|att|tik|nrf)", n) for n in names)


@canon_available
def test_special_case_tables_hold_the_texts_their_stratum_claims() -> None:
    # The circular unit test pins the mapping to itself; this pins it to the
    # db. Without it the Visuddhimagga could drift out of e0103n_att silently.
    conn = sqlite3.connect(f"file:{DEFAULT_CANON_DB}?immutable=1", uri=True)
    heads = {}
    for table in (
        "e0101n_mul",
        "e0103n_att",
        "s0515m_mul",
        "s0518m_nrf",
        "s0520m_nrf",
        "vin04t_nrf",
    ):
        row = conn.execute(
            f"SELECT pali_text FROM {table} WHERE rend IN ('book', 'chapter') "
            "ORDER BY rend = 'book' DESC, id LIMIT 1"
        ).fetchone()
        heads[table] = re.sub(r"<[^>]+>", "", row[0] or "").strip() if row else ""

    assert heads["e0101n_mul"].startswith("Visuddhimaggo")
    assert stratum("e0101n_mul") == "exegetical-mula"
    assert heads["e0103n_att"].startswith("Visuddhimagga-mahāṭīkā")
    assert stratum("e0103n_att") == "tika"
    assert heads["s0515m_mul"].startswith("Mahāniddesa")
    assert stratum("s0515m_mul") == "exegetical-mula"
    assert heads["s0518m_nrf"].startswith("Milinda")
    assert stratum("s0518m_nrf") == "mula-later"
    assert heads["s0520m_nrf"].startswith("Peṭakopadesa")
    assert stratum("s0520m_nrf") == "mula-later"
    assert heads["vin04t_nrf"].startswith("Dvemātikā")
    assert stratum("vin04t_nrf") == "tika"


def test_t1a_is_dpd_dbs_ebt_set() -> None:
    # Copied from dpd-db tools/pali_text_files.py: ebts. Re-check against that
    # file when dpd-db changes its EBT definition; the sweep's T1a tier is
    # only as right as this copy.
    from tools.canon_sweep import _T1A

    assert len(_T1A) == 31
    assert "s0404m3_mul" in _T1A  # AN10, the classic off-by-one trap
    assert "s0404m4_mul" in _T1A  # AN11
    assert "s0506m_mul" not in _T1A  # Vimānavatthu is not EBT


def test_an_unreadable_table_is_not_counted_as_searched(tmp_path: Path) -> None:
    path = tmp_path / "canon.db"
    with sqlite3.connect(path) as conn:
        for table, rows in _ROWS.items():
            conn.execute(
                f"CREATE TABLE {table} (id INTEGER PRIMARY KEY, rend TEXT, "
                "paranum TEXT, pali_text TEXT, english_translation TEXT)"
            )
            conn.executemany(f"INSERT INTO {table} VALUES (?, ?, ?, ?, '')", rows)
        # Matches the CST name shape but holds none of the swept columns.
        conn.execute("CREATE TABLE zzz9t_nrf (id INTEGER PRIMARY KEY, junk TEXT)")
        # Readable but not a CST text table: must stay outside the sweep.
        conn.execute(
            "CREATE TABLE meta (id INTEGER PRIMARY KEY, rend TEXT, paranum TEXT, "
            "pali_text TEXT, english_translation TEXT)"
        )
        conn.execute("INSERT INTO meta VALUES (1, 'bodytext', '1', 'ogha ogha', '')")

    result = sweep_canon(["ogha"], canon_db=path)

    assert result["ok"]
    # 7 readable fixture tables, not 8 or 9: a failed SELECT is not a search,
    # and a table outside the CST shape is not swept at all.
    assert result["tables_searched"] == len(_ROWS)
    assert "tika" in result["strata_searched"]
    assert _term(result)["rows"] == 3  # fixture rows 295, 435, 750; not meta's


# abh06t_nrf id 5296, whole: four verse lines, each its own <p>.
_VERSE_ROW = (
    5296,
    "gatha",
    "",
    '<p rend="gatha1"> Hitesī sabbapāṇīnaṃ,</p><p rend="gatha2">Issāmaccheramuccito;</p><p rend="gatha3">Kodhopanāhabyāpāda</p><p rend="gathalast">Virodhopasame rato.</p>',
)


def test_verse_lines_do_not_fuse_across_paragraph_tags(tmp_path: Path) -> None:
    path = tmp_path / "canon.db"
    with sqlite3.connect(path) as conn:
        conn.execute(
            "CREATE TABLE abh06t_nrf (id INTEGER PRIMARY KEY, rend TEXT, "
            "paranum TEXT, pali_text TEXT, english_translation TEXT)"
        )
        conn.execute("INSERT INTO abh06t_nrf VALUES (?, ?, ?, ?, '')", _VERSE_ROW)

    # A phrase that runs from one verse line into the next.
    entry = _term(sweep_canon(["byāpāda virodhopasame"], canon_db=path))
    assert entry["rows"] == 1
    fused = sweep_canon(["byāpādavirodhopasame"], canon_db=path)
    assert _term(fused)["rows"] == 0


def test_exclude_also_applies_to_the_vowel_length_probe(canon_db: Path) -> None:
    plain = _term(sweep_canon(["ogha"], canon_db=canon_db))
    assert "oghādisuttaṃ" in {
        f["form"] for f in plain["vowel_length_variants"]["forms"]
    }

    excluded = _term(sweep_canon(["ogha"], exclude=["oghā"], canon_db=canon_db))
    left = {
        f["form"] for f in excluded.get("vowel_length_variants", {}).get("forms", [])
    }
    assert "oghādisuttaṃ" not in left
    assert not any(f.startswith("oghā") for f in left)


def test_books_matching_no_table_is_an_error(canon_db: Path) -> None:
    result = sweep_canon(["ogha"], books=["nonexist*"], canon_db=canon_db)

    assert result["ok"] is False
    assert "matched no canon table" in result["error"]


def test_complete_is_false_for_a_limited_sweep(canon_db: Path) -> None:
    assert sweep_canon(["ogha"], canon_db=canon_db)["complete"] is True
    limited = sweep_canon(["ogha"], books=["s*_mul"], canon_db=canon_db)
    assert limited["complete"] is False
