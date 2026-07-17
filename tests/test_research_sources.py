"""Integration tests for research_sources helpers.

Some tests hit real local systems (Obsidian CLI, SQLite canon db). Tests that
need optional tools or data are skipped automatically when unavailable, so the
suite stays green on a machine that doesn't have everything wired up yet.
"""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path
from unittest.mock import MagicMock

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tools.research_sources import (  # noqa: E402
    DEFAULT_CANON_DB,
    DEFAULT_DPD_DB,
    DEFAULT_GRETIL_PATH,
    CanonHit,
    VaultHit,
    lookup_book,
    resolve_citation,
    search_canon,
    search_sanskrit,
    search_vault,
)

# ---------- skip markers ----------

obsidian_available = pytest.mark.skipif(
    shutil.which("obsidian") is None, reason="obsidian CLI not installed"
)
_canon_db_present = DEFAULT_CANON_DB is not None and DEFAULT_CANON_DB.exists()
canon_available = pytest.mark.skipif(
    not _canon_db_present, reason="canon db not available"
)
dpd_available = pytest.mark.skipif(
    DEFAULT_DPD_DB is None or not DEFAULT_DPD_DB.exists(),
    reason="dpd.db not configured (VICAYA_DPD_DB)",
)


def _dpd_translator_present() -> bool:
    for candidate in (
        Path(__file__).resolve().parents[2]
        / "dpd-db"
        / "tools"
        / "cst_book_translator.py",
        Path.home()
        / "MyFiles"
        / "3_Active"
        / "dpd-db"
        / "tools"
        / "cst_book_translator.py",
    ):
        if candidate.exists():
            return True
    return False


cst_translator_available = pytest.mark.skipif(
    not _dpd_translator_present(),
    reason="dpd-db sibling repo with cst_book_translator.py not available",
)


# ---------- resolve_citation ----------


class TestResolveCitation:
    """Fallback behaviour — no dpd.db needed."""

    def test_machine_field(self):
        c = resolve_citation("s0201m_mul", "23")
        assert c.machine == "s0201m_mul:23"

    def test_mn_fallback_contains_nikaya_and_paranum(self):
        c = resolve_citation("s0201m_mul", "23")
        assert "MN" in c.human
        assert "23" in c.human
        assert c.pitaka == "Sutta"
        assert c.text_type == "mūla"

    def test_dn_fallback(self):
        c = resolve_citation("s0101m_mul", "1")
        assert "DN" in c.human
        assert c.pitaka == "Sutta"

    def test_vinaya_attakatha_fallback(self):
        c = resolve_citation("vin01a_att", "5")
        assert c.pitaka == "Vinaya"
        assert "aṭṭhakathā" in c.human
        assert "5" in c.human

    def test_abhidhamma_tika_fallback(self):
        c = resolve_citation("abh02t_tik", "7")
        assert c.pitaka == "Abhidhamma"
        assert "ṭīkā" in c.human

    def test_extra(self):
        c = resolve_citation("e0101n_mul", "1")
        assert c.pitaka == "Extra"

    def test_unknown_falls_back_gracefully(self):
        c = resolve_citation("xyz999_mul", "1")
        assert "1" in c.human

    def test_dpd_code_raises_with_lookup_book_hint(self):
        import pytest

        with pytest.raises(ValueError, match="lookup-book"):
            resolve_citation("VISM", "166")

    def test_gui_code_raises_with_lookup_book_hint(self):
        import pytest

        with pytest.raises(ValueError, match="lookup-book"):
            resolve_citation("DN", "1")


@dpd_available
class TestResolveCitationWithDPD:
    """DPD-backed lookup — skipped when VICAYA_DPD_DB is not set."""

    def test_mn60_para_97(self):
        c = resolve_citation("s0202m_mul", "97")
        assert c.human == "MN60 Apaṇṇakasuttaṃ para 97"
        assert c.machine == "s0202m_mul:97"
        assert c.pitaka == "Sutta"

    def test_an_kesamutti(self):
        c = resolve_citation("s0402m2_mul", "66")
        assert "Kesamutti" in c.human
        assert "para 66" in c.human

    def test_commentary_mn60(self):
        c = resolve_citation("s0202a_att", "92")
        assert c.human == "MNa60 para 92"
        assert c.pitaka == "Commentary"

    def test_range_paranum(self):
        c = resolve_citation("s0202m_mul", "97-99")
        assert "MN60" in c.human
        assert "para 97–99" in c.human

    def test_dn1(self):
        c = resolve_citation("s0101m_mul", "1")
        assert "DN1" in c.human
        assert "Brahmajāla" in c.human


@canon_available
class TestResolveCitationCanonHeadings:
    """Canon-DB heading naming for books sutta_info doesn't cover (#44)."""

    @dpd_available
    def test_snp_global_verse_resolves_to_correct_sutta(self):
        # Verse 452 is in Subhāsitasutta (SNP29); the old sutta_info
        # nearest-preceding lookup mislabelled it SNP28 (Padhānasutta).
        c = resolve_citation("s0505m_mul", "452")
        assert "SNP29" in c.human
        assert "Subhāsita" in c.human
        assert "SNP28" not in c.human

    def test_khp_repeating_paranum_flags_ambiguity(self):
        # Khp paranums restart per sutta: §10 occurs in several suttas, so
        # the resolver must not assert one sutta name (was: KHP9 Mettasuttaṃ).
        c = resolve_citation("s0501m_mul", "10")
        assert "Khuddakapāṭha" in c.human
        assert "Mettasutta" not in c.human or "repeats" in c.human
        assert "repeats" in c.human

    def test_vism_gets_book_and_chapter_name(self):
        c = resolve_citation("e0101n_mul", "176")
        assert "Visuddhimagg" in c.human
        assert "Anussatikammaṭṭhānaniddes" in c.human
        assert "176" in c.human

    def test_patisambhidamagga_named(self):
        c = resolve_citation("s0517m_mul", "5")
        assert "Paṭisambhidāmagga" in c.human

    def test_nettippakarana_named(self):
        c = resolve_citation("s0519m_mul", "1")
        assert "Nettippakaraṇ" in c.human

    def test_kathavatthu_named(self):
        c = resolve_citation("abh03m3_mul", "1")
        assert "Kathāvatthu" in c.human

    def test_milindapanha_named_from_chapter_row(self):
        # s0518m_nrf has no rend='book' row; the title lives in the first
        # chapter row.
        c = resolve_citation("s0518m_nrf", "1")
        assert "Milindapañha" in c.human


# ---------- search_canon ----------


@canon_available
class TestSearchCanon:
    def test_pali_search_in_mn(self):
        hits = search_canon("dukkha", books=["s0201m_mul"], lang="pali", limit=3)
        assert len(hits) > 0
        for h in hits:
            assert isinstance(h, CanonHit)
            assert h.book_code == "s0201m_mul"
            assert "dukkha" in h.pali.lower()

    def test_english_search(self):
        hits = search_canon("suffering", books=["s0201m_mul"], lang="english", limit=3)
        # English translations may be sparse; tolerate empty result but not crash.
        for h in hits:
            assert "suffering" in h.english.lower()

    def test_prefix_expansion(self):
        hits = search_canon("dukkha", books=["s02*"], lang="pali", limit=5)
        assert len(hits) > 0
        # All hits should come from s02* tables.
        for h in hits:
            assert h.book_code.startswith("s02")

    def test_default_scope_is_suttas(self):
        # No `books` arg -> defaults to s*_mul tables.
        hits = search_canon("buddho", limit=3)
        for h in hits:
            assert h.book_code.startswith("s")


class TestSearchCanonNormalisation:
    """Hermetic tests for the normalised matcher against a fixture db.

    Each test reproduces a failure mode raw LIKE had: TEI tags breaking
    phrases, ṁ-vs-ṃ niggahita, sentence-initial capitals, NFD queries, and
    empty paranum on continuation rows.
    """

    @pytest.fixture
    def canon_db(self, tmp_path):
        db = tmp_path / "canon.db"
        import sqlite3

        with sqlite3.connect(db) as conn:
            conn.execute(
                "CREATE TABLE s0201m_mul (id INTEGER PRIMARY KEY, rend TEXT, "
                "paranum TEXT, pali_text TEXT, english_translation TEXT)"
            )
            conn.executemany(
                "INSERT INTO s0201m_mul (id, rend, paranum, pali_text, "
                "english_translation) VALUES (?, ?, ?, ?, ?)",
                [
                    (
                        0,
                        "bodytext",
                        "1",
                        '<p rend="bodytext">Evaṃ me su<pb ed="V" n="1.0001" />taṃ – '
                        "ekaṃ samayaṃ bhagavā…</p>",
                        "Thus have I heard. On one   occasion the Blessed One…",
                    ),
                    (
                        1,
                        "gatha",
                        "",
                        '<p rend="gatha1">Karuṇāsītalahadayaṃ, paññāpajjota…</p>',
                        "",
                    ),
                    (
                        2,
                        "bodytext",
                        "5",
                        '<p rend="bodytext">Sabbe saṅkhārā aniccā.</p>',
                        "All conditioned things are impermanent.",
                    ),
                ],
            )
        return db

    def test_phrase_matches_across_embedded_tags(self, canon_db):
        hits = search_canon("evaṃ me sutaṃ", books=["s0201m_mul"], db_path=canon_db)
        assert len(hits) == 1
        assert hits[0].paranum == "1"

    def test_sutta_central_niggahita_matches_cst_storage(self, canon_db):
        hits = search_canon("evaṁ me sutaṁ", books=["s0201m_mul"], db_path=canon_db)
        assert len(hits) == 1

    def test_case_insensitive_pali(self, canon_db):
        # Stored text has sentence-initial "Evaṃ"; query is lowercase.
        hits = search_canon("evaṃ", books=["s0201m_mul"], db_path=canon_db)
        assert len(hits) >= 1

    def test_nfd_query_matches_nfc_storage(self, canon_db):
        import unicodedata

        nfd_query = unicodedata.normalize("NFD", "saṅkhārā aniccā")
        hits = search_canon(nfd_query, books=["s0201m_mul"], db_path=canon_db)
        assert len(hits) == 1
        assert hits[0].paranum == "5"

    def test_continuation_row_gets_preceding_paranum(self, canon_db):
        hits = search_canon(
            "karuṇāsītalahadayaṃ", books=["s0201m_mul"], db_path=canon_db
        )
        assert len(hits) == 1
        assert hits[0].paranum == "1"

    def test_english_multiword_whitespace_collapse(self, canon_db):
        # Stored English has irregular internal spacing.
        hits = search_canon(
            "on one occasion", books=["s0201m_mul"], lang="english", db_path=canon_db
        )
        assert len(hits) == 1

    def test_empty_query_returns_nothing(self, canon_db):
        assert search_canon("  ", books=["s0201m_mul"], db_path=canon_db) == []


# ---------- search_vault ----------


@obsidian_available
class TestSearchVault:
    def test_search_returns_list(self):
        # We don't know what's in the vault; just verify the call shape works.
        hits = search_vault("the", limit=3)
        assert isinstance(hits, list)
        for h in hits:
            assert isinstance(h, VaultHit)


class TestSearchLibraryFoldersTimeout:
    def test_cli_reports_clean_error_on_timeout(self, monkeypatch, capsys):
        import tools.research_sources as rs
        from tools.library_folders import LibraryFoldersSearchTimeout as _Timeout

        fake_library_folders = MagicMock()
        fake_library_folders.LibraryFoldersSearchTimeout = _Timeout
        fake_library_folders.search.side_effect = _Timeout(
            "search timed out after 20s — query 'of' is too broad"
        )

        monkeypatch.setattr(
            rs, "_load_library_folders_module", lambda: fake_library_folders
        )
        monkeypatch.setattr(
            sys, "argv", ["research_sources", "search-library-folders", "of"]
        )

        assert rs._cli() == 1
        assert "too broad" in capsys.readouterr().err


class TestChannelAllowlist:
    def test_channel_allowlist_parses(self, tmp_path):
        from tools.research_sources import load_channel_allowlist

        f = tmp_path / "channels.md"
        f.write_text(
            "# header\n\n"
            "## Format\n\n"
            "```\n## trusted\n- Example In Fence\n```\n\n"
            "## trusted\n- Trusted A | UC1111111111111111111111\n\n"
            "## probationary\n- Prob A\n- Prob B | UC2222222222222222222222\n\n"
            "## excluded\n- Bad Channel\n",
            encoding="utf-8",
        )
        a = load_channel_allowlist(f)
        assert sorted(a.keys()) == ["excluded", "probationary", "trusted"]
        assert [c["name"] for c in a["trusted"]] == ["Trusted A"]
        assert a["trusted"][0]["channel_id"] == "UC1111111111111111111111"
        assert [c["name"] for c in a["probationary"]] == ["Prob A", "Prob B"]
        assert [c["name"] for c in a["excluded"]] == ["Bad Channel"]
        assert not any(c["name"] == "Example In Fence" for c in a["trusted"])

    def test_seeded_allowlist_loads_with_probationary_entries(self):
        from tools.research_sources import load_channel_allowlist

        a = load_channel_allowlist()
        assert len(a["probationary"]) >= 9


class TestSearchYouTube:
    def test_search_youtube_parses_yt_dlp_stdout(self, monkeypatch):
        from tools.research_sources import YouTubeHit, search_youtube

        fake_stdout = (
            "vid1|||Talk One|||Buddhist Insights @ Empty Cloud|||UCabc|||1234.5\n"
            "vid2|||Talk Two|||Random Slop Channel|||UCdef|||NA\n"
            "vid3|||Talk Three|||Buddha Tube|||UCghi|||60.0\n"
        )

        class Result:
            returncode = 0
            stdout = fake_stdout

        monkeypatch.setattr(
            "tools.research_sources.subprocess.run",
            MagicMock(return_value=Result()),
        )
        allowlist = {
            "trusted": [{"name": "Buddhist Insights @ Empty Cloud", "channel_id": ""}],
            "probationary": [],
            "excluded": [{"name": "Buddha Tube", "channel_id": ""}],
        }
        hits = search_youtube("anything", channels=allowlist, limit=10)
        assert len(hits) == 2
        assert all(isinstance(h, YouTubeHit) for h in hits)
        first = hits[0]
        assert first.video_id == "vid1"
        assert first.title == "Talk One"
        assert first.tier == "trusted"
        assert first.duration == 1234.5
        assert first.url == "https://youtu.be/vid1"
        assert hits[1].duration is None
        assert hits[1].tier == "probationary"


class TestTranscriptCache:
    def test_transcript_cache_hit_skips_network(self, tmp_path, monkeypatch):
        import json
        from dataclasses import asdict

        from tools.research_sources import (
            YouTubeTranscript,
            fetch_youtube_transcript,
        )

        cached = YouTubeTranscript(
            video_id="cachedvid",
            lang="en",
            is_auto=False,
            segments=[{"start": 0.0, "duration": 1.0, "text": "hello"}],
            fetched="2026-05-12",
        )
        (tmp_path / "cachedvid.json").write_text(
            json.dumps(asdict(cached)), encoding="utf-8"
        )

        try:
            import youtube_transcript_api

            monkeypatch.setattr(
                youtube_transcript_api.YouTubeTranscriptApi,
                "__init__",
                MagicMock(
                    side_effect=AssertionError(
                        "network must not be called on cache hit"
                    )
                ),
            )
        except ImportError:
            pass

        result = fetch_youtube_transcript("cachedvid", cache_dir=tmp_path)
        assert result is not None
        assert result.video_id == "cachedvid"
        assert result.is_auto is False
        assert result.segments[0]["text"] == "hello"


# ---------- search_sanskrit ----------

gretil_available = pytest.mark.skipif(
    DEFAULT_GRETIL_PATH is None or not DEFAULT_GRETIL_PATH.exists(),
    reason="GRETIL corpus not available (VICAYA_GRETIL_PATH)",
)


class TestSearchSanskrit:
    def test_returns_empty_when_unconfigured(self, tmp_path):
        from tools.research_sources import search_sanskrit

        result = search_sanskrit("atman", path=tmp_path / "nonexistent")
        assert result == []

    @gretil_available
    def test_returns_vault_hits(self):
        hits = search_sanskrit("atman", limit=5)
        assert isinstance(hits, list)
        for h in hits:
            assert isinstance(h, VaultHit)
            assert h.path.endswith(".htm")
            assert h.snippet


@cst_translator_available
class TestLookupBook:
    EXPECTED_KEYS = {
        "cst_filename",
        "cst_table",
        "cst_book_name",
        "gui_book_code",
        "dpd_book_code",
    }

    def _dn1(self, hits):
        assert len(hits) == 1
        h = hits[0]
        assert set(h.keys()) == self.EXPECTED_KEYS
        assert h["cst_filename"] == "s0101m.mul"
        assert h["cst_table"] == "s0101m_mul"
        assert h["gui_book_code"] == "dn1"
        assert h["dpd_book_code"] == "DN"
        assert "Sīlakkhandha" in h["cst_book_name"]

    def test_cst_filename(self):
        self._dn1(lookup_book("s0101m.mul"))

    def test_table_underscore(self):
        self._dn1(lookup_book("s0101m_mul"))

    def test_book_name(self):
        self._dn1(lookup_book("Dīghanikāya, Sīlakkhandhavaggapāḷi"))

    def test_gui_code(self):
        self._dn1(lookup_book("dn1"))

    def test_dpd_code_returns_all_dn_mula(self):
        hits = lookup_book("DN")
        assert len(hits) == 3
        assert all(h["dpd_book_code"] == "DN" for h in hits)
        assert {h["cst_table"] for h in hits} == {
            "s0101m_mul",
            "s0102m_mul",
            "s0103m_mul",
        }

    def test_empty_on_no_match(self):
        assert lookup_book("bogus") == []

    def test_empty_input(self):
        assert lookup_book("") == []


# ---------- _strip_xml ----------


class TestStripXml:
    def test_strips_tei_markup(self):
        from tools.research_sources import _strip_xml

        sample = '<p rend="bodytext">Sā <pb ed="T" n="1.0131" /> papañcārāmassa</p>'
        assert _strip_xml(sample) == "Sā papañcārāmassa"

    def test_decodes_common_entities(self):
        from tools.research_sources import _strip_xml

        assert _strip_xml("a &amp; b &lt;c&gt;") == "a & b <c>"

    def test_collapses_whitespace_and_preserves_diacritics(self):
        from tools.research_sources import _strip_xml

        assert _strip_xml("\n  ñāṇa   ā\n") == "ñāṇa ā"

    def test_handles_empty_and_none_safe(self):
        from tools.research_sources import _strip_xml

        assert _strip_xml("") == ""


# ---------- get-agama ----------

from tools.research_sources import DEFAULT_EBC_VAULT_PATH  # noqa: E402

_ebc_vault_present = (
    DEFAULT_EBC_VAULT_PATH is not None and DEFAULT_EBC_VAULT_PATH.exists()
)
ebc_available = pytest.mark.skipif(
    not _ebc_vault_present, reason="EBC vault not available (VICAYA_EBC_VAULT_PATH)"
)


class TestGetAgama:
    def test_returns_error_when_vault_missing(self, tmp_path):
        from tools.research_sources import get_agama_texts

        result = get_agama_texts("MN10", vault=tmp_path / "nonexistent")
        assert "error" in result
        assert result["parallels_found"] == []
        assert result["parallels_missing"] == []

    def test_returns_error_on_unknown_sutta(self):
        from tools.research_sources import get_agama_texts

        result = get_agama_texts("XX999")
        assert "error" in result

    @ebc_available
    def test_mn10_returns_agama_texts(self):
        from tools.research_sources import get_agama_texts

        result = get_agama_texts("MN10")
        assert result["sutta_code"] == "MN10"
        assert len(result["parallels_found"]) >= 1
        first = result["parallels_found"][0]
        assert first["code"] in ("EA12.1", "MA31", "MA81", "MA98")
        assert first["translator"] in ("Patton", "BDK")
        assert len(first["text"]) > 100

    @ebc_available
    def test_missing_codes_reported_not_dropped(self):
        from tools.research_sources import get_agama_texts

        result = get_agama_texts("MN10")
        # EA27.1 exists in parallels_agama but has no file in the vault
        assert len(result["parallels_missing"]) >= 1

    @ebc_available
    def test_max_parallels_limits_results(self):
        from tools.research_sources import get_agama_texts

        result = get_agama_texts("MN10", max_parallels=2)
        assert len(result["parallels_found"]) + len(result["parallels_missing"]) <= 2

    @ebc_available
    def test_find_agama_path_sa_underscore(self):
        from tools.research_sources import _find_agama_path

        # SA1.167-style codes stored as sa1_167-unknown.md in sa-patton-1
        assert DEFAULT_EBC_VAULT_PATH is not None
        path, _ = _find_agama_path("SA1.167", DEFAULT_EBC_VAULT_PATH)
        if path is not None:
            assert path.exists()
            assert "sa-patton-1" in str(path)


# ---------- sc-parallels / sc-search ----------

from tools.research_sources import DEFAULT_SC_DATA_PATH  # noqa: E402

sc_available = pytest.mark.skipif(
    DEFAULT_SC_DATA_PATH is None or not DEFAULT_SC_DATA_PATH.exists(),
    reason="SuttaCentral offline archive not available (VICAYA_SC_DATA_PATH)",
)


class TestSCParallels:
    def test_returns_empty_when_unconfigured(self, tmp_path):
        from tools.research_sources import sc_parallels

        assert sc_parallels("mn18", sc_root=tmp_path / "nonexistent") == []

    def test_returns_empty_on_empty_citation(self):
        from tools.research_sources import sc_parallels

        assert sc_parallels("") == []

    @sc_available
    def test_mn18_has_expected_parallels(self):
        from tools.research_sources import sc_parallels

        ps = sc_parallels("mn18", include_text=False)
        refs = {p.ref for p in ps}
        # MN18 has known parallels in Chinese (MĀ 115) and the EĀ.
        assert "ma115" in refs
        assert "ea40.10" in refs
        # Query itself should not appear in its own parallels list.
        assert "mn18" not in refs

    def test_expand_range_uid(self):
        from tools.research_sources import _sc_expand_range_uid

        assert _sc_expand_range_uid("sn12.1-2") == ["sn12.1", "sn12.2"]
        assert _sc_expand_range_uid("an1.6-10") == [
            "an1.6",
            "an1.7",
            "an1.8",
            "an1.9",
            "an1.10",
        ]
        # Not ranges: bare uid, hyphenated collection name, inverted range.
        assert _sc_expand_range_uid("sa298") == []
        assert _sc_expand_range_uid("ea-2.1") == []
        assert _sc_expand_range_uid("sn12.5-3") == []

    def test_range_stored_uid_resolves_by_membership(self, tmp_path):
        # Regression for issue #69: parallels.json stores sn12.1-2 as one range
        # uid; a lookup for the member sn12.2 previously returned [].
        import json

        from tools.research_sources import sc_parallels

        rel = tmp_path / "relationship"
        rel.mkdir(parents=True)
        (rel / "parallels.json").write_text(
            json.dumps([{"parallels": ["sn12.1-2", "sa298", "~ea49.5"]}]),
            encoding="utf-8",
        )
        ps = sc_parallels("sn12.2", sc_root=tmp_path, include_text=False)
        refs = {p.ref for p in ps}
        assert refs == {"sa298", "ea49.5"}
        # The range uid carrying the query itself is not one of its parallels.
        assert "sn12.1-2" not in refs
        # A direct lookup of the range uid still works and skips itself.
        ps_range = sc_parallels("sn12.1-2", sc_root=tmp_path, include_text=False)
        assert {p.ref for p in ps_range} == {"sa298", "ea49.5"}

    @sc_available
    def test_sn12_2_returns_parallels_from_real_archive(self):
        from tools.research_sources import sc_parallels

        ps = sc_parallels("sn12.2", include_text=False)
        refs = {p.ref for p in ps}
        assert "sa298" in refs
        assert "sn12.2" not in refs
        assert "sn12.1-2" not in refs

    @sc_available
    def test_text_gaps_flagged_when_missing(self):
        from tools.research_sources import sc_parallels

        ps = sc_parallels("mn18", include_text=True)
        ma115 = next((p for p in ps if p.ref == "ma115"), None)
        # MA115 isn't in the partial offline archive — gap must be reported,
        # not silently rendered as empty text.
        if ma115 is not None:
            assert not any(
                [ma115.text_pali, ma115.text_lzh, ma115.text_san, ma115.text_pra]
            )
            assert ma115.text_gaps  # non-empty


class TestSCSearch:
    def test_returns_empty_when_unconfigured(self, tmp_path):
        from tools.research_sources import sc_search

        assert sc_search("anything", sc_root=tmp_path / "nonexistent") == []

    @sc_available
    def test_pli_search_returns_vault_hits(self):
        from tools.research_sources import sc_search

        hits = sc_search("papañca", lang="pli", limit=3)
        assert isinstance(hits, list)
        for h in hits:
            assert isinstance(h, VaultHit)
            assert h.path.endswith(".json")
            assert "papañca" in h.snippet


class TestScratchDossier:
    """End-to-end of the scratch CLI: init, log, gate refusal, verify, resume."""

    def test_init_creates_file_with_all_phase_sections(self, tmp_path, monkeypatch):
        from tools.research_sources import (
            _SCRATCH_PHASES,
            scratch_init,
        )

        monkeypatch.setattr("tools.scratch._SCRATCH_DIR", tmp_path)
        path = scratch_init("test-slug")
        assert path.exists()
        text = path.read_text(encoding="utf-8")
        assert "Vicaya dossier — test-slug" in text
        for _, title, _ in _SCRATCH_PHASES:
            assert title in text

    def test_init_with_fields_fills_header_and_writes_phase0_gate(
        self, tmp_path, monkeypatch
    ):
        # Regression for issue #31: agents ran scratch-init, recorded the
        # question fields, then forgot scratch-gate 0 — every later gate
        # refused until gate 0 was backfilled. One-shot init must end that.
        from tools.research_sources import _read_state, scratch_gate, scratch_init

        monkeypatch.setattr("tools.scratch._SCRATCH_DIR", tmp_path)
        monkeypatch.delenv("VICAYA_SCRATCH", raising=False)
        path = scratch_init(
            "test-oneshot",
            question_original="what about anatta?",
            question_polished="What do the suttas say about anattā?",
            scope_assumptions="mūla only; neutral map; full note",
            ambiguity="clear",
        )
        text = path.read_text(encoding="utf-8")
        assert "**Question original:** what about anatta?" in text
        assert "**Question polished:** What do the suttas say about anattā?" in text
        assert "**Scope assumptions:** mūla only; neutral map; full note" in text
        assert "**Ambiguity status:** clear" in text
        assert "<fill in>" not in text
        assert "### PHASE 0 EXIT GATE" in text
        assert _read_state()["phase"] == "1"
        # Phase 1 gate must now succeed without any backfilling.
        monkeypatch.setenv("VICAYA_SCRATCH", str(path))
        from tools.research_sources import scratch_log

        scratch_log("1", "search-vault", summary="test hit")
        assert scratch_gate("1")["ok"]

    def test_init_without_fields_keeps_placeholders_and_no_gate(
        self, tmp_path, monkeypatch
    ):
        from tools.research_sources import _read_state, scratch_init

        monkeypatch.setattr("tools.scratch._SCRATCH_DIR", tmp_path)
        monkeypatch.delenv("VICAYA_SCRATCH", raising=False)
        path = scratch_init("test-bare")
        text = path.read_text(encoding="utf-8")
        assert "**Question polished:** <fill in>" in text
        assert "### PHASE 0 EXIT GATE" not in text
        assert _read_state()["phase"] == "0"

    def test_init_with_partial_fields_fills_header_but_does_not_gate(
        self, tmp_path, monkeypatch
    ):
        from tools.research_sources import _read_state, scratch_init

        monkeypatch.setattr("tools.scratch._SCRATCH_DIR", tmp_path)
        monkeypatch.delenv("VICAYA_SCRATCH", raising=False)
        path = scratch_init(
            "test-partial",
            question_polished="What do the suttas say about anattā?",
        )
        text = path.read_text(encoding="utf-8")
        assert "**Question polished:** What do the suttas say about anattā?" in text
        assert "**Scope assumptions:** <fill in>" in text
        assert "### PHASE 0 EXIT GATE" not in text
        assert _read_state()["phase"] == "0"

    def test_init_rejects_invalid_ambiguity(self, tmp_path, monkeypatch):
        import pytest

        from tools.research_sources import scratch_init

        monkeypatch.setattr("tools.scratch._SCRATCH_DIR", tmp_path)
        with pytest.raises(ValueError, match="ambiguity"):
            scratch_init("test-bad-ambiguity", ambiguity="maybe")

    def test_init_with_fields_on_thematic_run_gates_phase0(self, tmp_path, monkeypatch):
        from tools.research_sources import _read_state, scratch_gate, scratch_init

        monkeypatch.setattr("tools.scratch._SCRATCH_DIR", tmp_path)
        monkeypatch.delenv("VICAYA_SCRATCH", raising=False)
        path = scratch_init(
            "test-oneshot-thematic",
            run_class="thematic",
            question_polished="How did lay devotion develop historically?",
            scope_assumptions="thematic; secondary literature emphasis",
            ambiguity="minor_uncertainty",
        )
        text = path.read_text(encoding="utf-8")
        assert "**Run class:** thematic" in text
        assert "### PHASE 0 EXIT GATE" in text
        assert _read_state()["phase"] == "1"
        monkeypatch.setenv("VICAYA_SCRATCH", str(path))
        from tools.research_sources import scratch_log

        scratch_log("1", "search-vault", summary="test hit")
        assert scratch_gate("1")["ok"]

    def test_init_on_existing_file_ignores_fields(self, tmp_path, monkeypatch):
        from tools.research_sources import scratch_init

        monkeypatch.setattr("tools.scratch._SCRATCH_DIR", tmp_path)
        monkeypatch.delenv("VICAYA_SCRATCH", raising=False)
        path = scratch_init("test-existing")
        again = scratch_init(
            "test-existing",
            question_polished="Should be ignored",
            scope_assumptions="ignored",
            ambiguity="clear",
        )
        assert again == path
        text = path.read_text(encoding="utf-8")
        assert "Should be ignored" not in text
        assert "### PHASE 0 EXIT GATE" not in text

    def test_cli_init_on_slug_with_progress_warns(self, tmp_path, monkeypatch, capsys):
        # Issue #60: re-running scratch-init on a slug that already has gates
        # and a note set must not silently reattach without a warning.
        import json

        import tools.research_sources as rs
        from tools.research_sources import (
            scratch_gate,
            scratch_init,
            scratch_log,
            scratch_set_note,
        )

        monkeypatch.setattr("tools.scratch._SCRATCH_DIR", tmp_path)
        monkeypatch.delenv("VICAYA_SCRATCH", raising=False)
        path = scratch_init(
            "reused-slug",
            question_polished="q",
            scope_assumptions="s",
            ambiguity="clear",
        )
        scratch_log("1", "search-vault", summary="hit", scratch=path)
        scratch_gate("1", scratch=path)
        note_path = path.parent / "note.md"
        note_path.write_text("# note", encoding="utf-8")
        result = scratch_set_note(str(note_path), scratch=path)
        assert result["ok"] is True

        monkeypatch.setattr(
            sys,
            "argv",
            ["research_sources", "scratch-init", "reused-slug"],
        )
        assert rs._cli() == 0
        out = json.loads(capsys.readouterr().out)
        assert out["ok"] is True
        assert "warning" in out
        assert "reused-slug" in out["warning"]
        assert "last gate: 1" in out["warning"]
        assert "note set" in out["warning"]

    def test_cli_init_fresh_slug_has_no_warning(self, tmp_path, monkeypatch, capsys):
        import json

        import tools.research_sources as rs

        monkeypatch.setattr("tools.scratch._SCRATCH_DIR", tmp_path)
        monkeypatch.delenv("VICAYA_SCRATCH", raising=False)
        monkeypatch.setattr(
            sys,
            "argv",
            ["research_sources", "scratch-init", "brand-new-slug"],
        )
        assert rs._cli() == 0
        out = json.loads(capsys.readouterr().out)
        assert out["ok"] is True
        assert "warning" not in out

    def test_init_creates_date_prefixed_filename(self, tmp_path, monkeypatch):
        import re as _re

        from tools.research_sources import scratch_init

        monkeypatch.setattr("tools.scratch._SCRATCH_DIR", tmp_path)
        monkeypatch.delenv("VICAYA_SCRATCH", raising=False)
        path = scratch_init("date-prefix-slug")
        assert _re.match(r"\d{4}-\d{2}-\d{2}-date-prefix-slug\.md$", path.name)
        # The filename gets the date; the header keeps the bare slug.
        assert "Vicaya dossier — date-prefix-slug" in path.read_text(encoding="utf-8")

    def test_init_is_idempotent_across_dated_filename(self, tmp_path, monkeypatch):
        from tools.research_sources import scratch_init

        monkeypatch.setattr("tools.scratch._SCRATCH_DIR", tmp_path)
        monkeypatch.delenv("VICAYA_SCRATCH", raising=False)
        first = scratch_init("resume-me")
        again = scratch_init("resume-me")
        assert again == first

    def test_resume_finds_date_prefixed_file_by_bare_slug(self, tmp_path, monkeypatch):
        from tools.research_sources import scratch_init, scratch_resume

        monkeypatch.setattr("tools.scratch._SCRATCH_DIR", tmp_path)
        monkeypatch.delenv("VICAYA_SCRATCH", raising=False)
        path = scratch_init("resumable")
        result = scratch_resume(slug="resumable")
        assert result["ok"]
        assert result["path"] == str(path)

    def test_gate_refusal_message_says_what_to_run(self, tmp_path, monkeypatch):
        # Issue #31, second half: the refusal must name the exact command,
        # not just describe the missing gate.
        from tools.research_sources import scratch_gate, scratch_init

        monkeypatch.setattr("tools.scratch._SCRATCH_DIR", tmp_path)
        path = scratch_init("test-refusal-message")
        monkeypatch.setenv("VICAYA_SCRATCH", str(path))
        result = scratch_gate("2")
        assert result["ok"] is False
        assert "run scratch-gate 0 first" in result["message"]

    def test_log_appends_entry_under_named_phase(self, tmp_path, monkeypatch):
        from tools.research_sources import scratch_init, scratch_log

        monkeypatch.setattr("tools.scratch._SCRATCH_DIR", tmp_path)
        path = scratch_init("test-log")
        monkeypatch.setenv("VICAYA_SCRATCH", str(path))
        scratch_log(
            "2",
            "search-canon",
            args=["pabhassara", "--limit", "1"],
            summary="2 hits in AN",
            hits=2,
        )
        text = path.read_text(encoding="utf-8")
        assert "search-canon" in text
        assert "pabhassara" in text
        # entry must be inside the phase 2 section, not at end of file
        canon_idx = text.index("## Phase 2 — Canon")
        next_section_idx = text.index("## Phase 2.5")
        assert canon_idx < text.index("search-canon") < next_section_idx

    def test_gate_refuses_when_prior_gate_missing(self, tmp_path, monkeypatch):
        from tools.research_sources import scratch_gate, scratch_init

        monkeypatch.setattr("tools.scratch._SCRATCH_DIR", tmp_path)
        path = scratch_init("test-gate-refuse")
        monkeypatch.setenv("VICAYA_SCRATCH", str(path))
        # Try to gate phase 2 without first gating phase 0 or 1.
        result = scratch_gate("2")
        assert result["ok"] is False
        assert result["missing_phase"] == "0"
        assert "expected_evidence" in result
        assert isinstance(result["expected_evidence"], list)
        assert result["expected_evidence"]
        # And it didn't write the phase 2 gate
        assert "PHASE 2 EXIT GATE" not in path.read_text(encoding="utf-8")

    def test_gate_appends_canonical_checklist_in_order(self, tmp_path, monkeypatch):
        from tools.research_sources import (
            _PHASE_INDEX,
            scratch_gate,
            scratch_init,
            scratch_log,
        )

        monkeypatch.setattr("tools.scratch._SCRATCH_DIR", tmp_path)
        path = scratch_init("test-gate-ok")
        monkeypatch.setenv("VICAYA_SCRATCH", str(path))
        for phase in ("0", "1", "2"):
            if phase in ("1", "2"):
                scratch_log(phase, "search-canon", summary=f"hit in {phase}")
            r = scratch_gate(phase)
            assert r["ok"], r
        text = path.read_text(encoding="utf-8")
        for phase in ("0", "1", "2"):
            assert f"PHASE {phase} EXIT GATE" in text
            for item in _PHASE_INDEX[phase][2]:
                assert item in text

    def test_verify_reports_missing_with_expected_evidence(self, tmp_path, monkeypatch):
        from tools.research_sources import scratch_gate, scratch_init, scratch_verify

        monkeypatch.setattr("tools.scratch._SCRATCH_DIR", tmp_path)
        path = scratch_init("test-verify")
        monkeypatch.setenv("VICAYA_SCRATCH", str(path))
        scratch_gate("0")
        # Skip 1; gate 2 should now refuse. Force-write phase 2 gate is blocked,
        # so verify against an explicit through-phase to surface the gap.
        result = scratch_verify(through="2")
        assert result["ok"] is False
        missing_phases = [m["phase"] for m in result["missing"]]
        assert "1" in missing_phases
        assert "2" in missing_phases
        # Every missing entry must carry the canonical evidence list.
        for m in result["missing"]:
            assert m["expected_evidence"]

    def test_verify_flags_gated_but_empty_phase(self, tmp_path, monkeypatch):
        import datetime

        from tools.research_sources import scratch_gate, scratch_init, scratch_verify
        from tools.scratch import _PHASE_INDEX, _append_under_phase, _gate_marker

        monkeypatch.setattr("tools.scratch._SCRATCH_DIR", tmp_path)
        path = scratch_init("test-empty")
        monkeypatch.setenv("VICAYA_SCRATCH", str(path))
        scratch_gate("0")
        # Simulate a gate written directly (bypassing scratch_gate's content check)
        # — the scenario a crashed sub-agent could produce via direct file access.
        ts = datetime.datetime.now().isoformat(timespec="seconds")
        _, title, evidence = _PHASE_INDEX["1"]
        block = "\n".join(
            [_gate_marker("1"), f"- timestamp: {ts}", f"- title: {title}"]
            + [f"- [ ] {item}" for item in evidence]
        )
        _append_under_phase(path, "1", block)
        result = scratch_verify(through="1")
        assert result["ok"] is False
        assert result["missing"] == []
        issues = {c["phase"]: c["issue"] for c in result["content_issues"]}
        assert issues.get("1") == "empty"

    def test_gate_refuses_when_no_content_logged(self, tmp_path, monkeypatch):
        from tools.research_sources import scratch_gate, scratch_init

        monkeypatch.setattr("tools.scratch._SCRATCH_DIR", tmp_path)
        path = scratch_init("test-gate-refuses")
        monkeypatch.setenv("VICAYA_SCRATCH", str(path))
        scratch_gate("0")
        result = scratch_gate("1")
        assert result["ok"] is False
        assert result["reason"] == "no logged evidence"
        assert "run the searches first" in result["message"]
        assert "### PHASE 1 EXIT GATE" not in path.read_text(encoding="utf-8")

    def test_verify_passes_when_phase_has_logged_content(self, tmp_path, monkeypatch):
        from tools.research_sources import (
            scratch_gate,
            scratch_init,
            scratch_log,
            scratch_verify,
        )

        monkeypatch.setattr("tools.scratch._SCRATCH_DIR", tmp_path)
        path = scratch_init("test-content")
        monkeypatch.setenv("VICAYA_SCRATCH", str(path))
        scratch_gate("0")
        scratch_log("1", "search-vault", summary="3 vault hits on the term")
        scratch_gate("1")
        result = scratch_verify(through="1")
        assert result["ok"] is True
        assert result["content_issues"] == []

    def test_verify_flags_placeholder_text(self, tmp_path, monkeypatch):
        from tools.research_sources import (
            scratch_gate,
            scratch_init,
            scratch_log,
            scratch_verify,
        )

        monkeypatch.setattr("tools.scratch._SCRATCH_DIR", tmp_path)
        path = scratch_init("test-placeholder")
        monkeypatch.setenv("VICAYA_SCRATCH", str(path))
        scratch_gate("0")
        scratch_log("1", "note", summary="would search for the term here")
        scratch_gate("1")
        result = scratch_verify(through="1")
        assert result["ok"] is False
        issues = {c["phase"]: c["issue"] for c in result["content_issues"]}
        assert issues.get("1") == "placeholder"

    def test_verify_ignores_placeholder_word_inside_inflected_text(
        self, tmp_path, monkeypatch
    ):
        from tools.research_sources import (
            scratch_gate,
            scratch_init,
            scratch_log,
            scratch_verify,
        )

        monkeypatch.setattr("tools.scratch._SCRATCH_DIR", tmp_path)
        path = scratch_init("test-not-placeholder")
        monkeypatch.setenv("VICAYA_SCRATCH", str(path))
        scratch_gate("0")
        scratch_log(
            "1",
            "search-canon",
            summary='DN15: "would searching still be found" — dependent origination',
        )
        scratch_gate("1")
        result = scratch_verify(through="1")
        assert result["ok"] is True
        assert result["content_issues"] == []

    def test_verify_default_checks_through_4c_not_high_water_mark(
        self, tmp_path, monkeypatch
    ):
        from tools.research_sources import (
            scratch_gate,
            scratch_init,
            scratch_log,
            scratch_verify,
        )

        monkeypatch.setattr("tools.scratch._SCRATCH_DIR", tmp_path)
        path = scratch_init("test-4b-gap")
        monkeypatch.setenv("VICAYA_SCRATCH", str(path))
        scratch_gate("0")
        for phase in ("1", "2", "2.5", "3", "3b", "4"):
            scratch_log(phase, "search", summary=f"real hit in {phase}")
            scratch_gate(phase)
        # Gates exist through phase 4; 4b/4c were never gated. The old verify
        # stopped at the high-water mark and passed — it must now flag the gap,
        # agreeing with scratch-gate 5 which requires 4b/4c.
        result = scratch_verify()
        assert result["ok"] is False
        missing_phases = {m["phase"] for m in result["missing"]}
        assert "4b" in missing_phases
        assert "4c" in missing_phases

    def test_verify_thematic_does_not_flag_autoskip_phases_missing(
        self, tmp_path, monkeypatch
    ):
        from tools.research_sources import (
            scratch_gate,
            scratch_init,
            scratch_log,
            scratch_verify,
        )

        monkeypatch.setattr("tools.scratch._SCRATCH_DIR", tmp_path)
        path = scratch_init("test-thematic-skip", run_class="thematic")
        monkeypatch.setenv("VICAYA_SCRATCH", str(path))
        scratch_gate("0")
        for phase in ("1", "2"):
            scratch_log(phase, "search", summary=f"real hit in {phase}")
            scratch_gate(phase)
        # 2.5/3b are not gated yet, but a thematic run auto-skips them — verify
        # must not report them missing, only the genuinely-skipped phase 3.
        result = scratch_verify(through="3b")
        missing_phases = {m["phase"] for m in result["missing"]}
        assert "2.5" not in missing_phases
        assert "3b" not in missing_phases
        assert "3" in missing_phases

    def test_resume_reports_last_gate_and_next_phase(self, tmp_path, monkeypatch):
        from tools.research_sources import (
            scratch_gate,
            scratch_init,
            scratch_log,
            scratch_resume,
        )

        monkeypatch.setattr("tools.scratch._SCRATCH_DIR", tmp_path)
        path = scratch_init("test-resume")
        monkeypatch.setenv("VICAYA_SCRATCH", str(path))
        for phase in ("0", "1", "2"):
            if phase in ("1", "2"):
                scratch_log(phase, "search-canon", summary=f"hit in {phase}")
            scratch_gate(phase)
        result = scratch_resume("test-resume")
        assert result["ok"]
        assert result["last_gate"]["phase"] == "2"
        assert result["next_phase"] == "2.5"

    def test_resume_slug_ignores_stale_active_state(self, tmp_path, monkeypatch):
        from tools.research_sources import _write_state, scratch_init, scratch_resume

        monkeypatch.setattr("tools.scratch._SCRATCH_DIR", tmp_path)
        monkeypatch.delenv("VICAYA_SCRATCH", raising=False)
        stale_path = scratch_init("stale-run")
        selected_path = scratch_init("selected-run")
        _write_state(stale_path, "0")

        result = scratch_resume("selected-run")

        assert result["ok"]
        assert result["path"] == str(selected_path)

    def test_resume_updates_active_state_to_selected_scratch(
        self, tmp_path, monkeypatch
    ):
        from tools.research_sources import (
            _read_state,
            _write_state,
            scratch_gate,
            scratch_init,
            scratch_resume,
        )

        monkeypatch.setattr("tools.scratch._SCRATCH_DIR", tmp_path)
        monkeypatch.delenv("VICAYA_SCRATCH", raising=False)
        stale_path = scratch_init("stale-active")
        selected_path = scratch_init("selected-active")
        monkeypatch.setenv("VICAYA_SCRATCH", str(selected_path))
        scratch_gate("0")
        monkeypatch.delenv("VICAYA_SCRATCH", raising=False)
        _write_state(stale_path, "0")

        result = scratch_resume("selected-active")

        assert result["ok"]
        assert result["next_phase"] == "1"
        assert _read_state() == {"scratch": str(selected_path), "phase": "1"}

    def test_resume_thematic_run_reattaches_next_worked_phase(
        self, tmp_path, monkeypatch
    ):
        from tools.research_sources import (
            _read_state,
            scratch_gate,
            scratch_init,
            scratch_resume,
        )

        monkeypatch.setattr("tools.scratch._SCRATCH_DIR", tmp_path)
        monkeypatch.delenv("VICAYA_SCRATCH", raising=False)
        path = scratch_init("thematic-resume", run_class="thematic")
        monkeypatch.setenv("VICAYA_SCRATCH", str(path))
        from tools.research_sources import scratch_log

        for phase in ("0", "1", "2"):
            if phase in ("1", "2"):
                scratch_log(phase, "search-canon", summary=f"hit in {phase}")
            assert scratch_gate(phase)["ok"]

        result = scratch_resume("thematic-resume")

        assert result["ok"]
        assert result["next_phase"] == "3"
        assert _read_state() == {"scratch": str(path), "phase": "3"}

    def test_phase_7_gate_refuses_when_vault_note_has_rejected(
        self, tmp_path, monkeypatch
    ):
        from tools.research_sources import (
            scratch_gate,
            scratch_init,
            scratch_self_audit,
        )

        monkeypatch.setattr("tools.scratch._SCRATCH_DIR", tmp_path)
        path = scratch_init("test-rejected-gate")
        # Point the scratch file at a vault note containing a [REJECTED] tag.
        vault = tmp_path / "fake_note.md"
        vault.write_text(
            "# Note\n\nThe reviewer cited MN999 [REJECTED — not in sutta_info].\n",
            encoding="utf-8",
        )
        text = path.read_text(encoding="utf-8").replace(
            "**Vault note:** <set at Phase 7>",
            f"**Vault note:** {vault}",
        )
        path.write_text(text, encoding="utf-8")
        monkeypatch.setenv("VICAYA_SCRATCH", str(path))
        from tools.research_sources import scratch_log

        _cp = ("1", "2", "2.5", "3", "3b", "4", "4b", "4c")
        for phase in ("0", "1", "2", "2.5", "3", "3b", "4", "4b", "4c", "5", "6"):
            if phase in _cp:
                scratch_log(phase, "search-canon", summary=f"hit in {phase}")
            r = scratch_gate(phase)
            assert r["ok"], (phase, r)
        assert scratch_self_audit(answers=["none"] * 6)["ok"]
        result = scratch_gate("7")
        assert result["ok"] is False
        assert "[REJECTED]" in result["reason"] or "REJECTED" in result["reason"]
        assert result["offending_lines"]

    def test_thematic_run_auto_skips_2_5_and_3b(self, tmp_path, monkeypatch):
        from tools.research_sources import (
            _read_state,
            scratch_gate,
            scratch_init,
            scratch_log,
        )

        monkeypatch.setattr("tools.scratch._SCRATCH_DIR", tmp_path)
        monkeypatch.delenv("VICAYA_SCRATCH", raising=False)
        path = scratch_init("test-thematic", run_class="thematic")
        monkeypatch.setenv("VICAYA_SCRATCH", str(path))
        for phase in ("0", "1", "2"):
            if phase in ("1", "2"):
                scratch_log(phase, "search-canon", summary=f"hit in {phase}")
            assert scratch_gate(phase)["ok"]
        # Gating phase 3 must succeed without the agent ever touching 2.5,
        # which would otherwise be a missing-prior-gate refusal.
        scratch_log("3", "search-library-folders", summary="library hit")
        assert scratch_gate("3")["ok"]
        text = path.read_text(encoding="utf-8")
        assert "PHASE 2.5 EXIT GATE" in text
        assert "AUTO-SKIPPED (thematic run)" in text
        # Advance skips over the auto-skipped 3b → next worked phase is 4.
        assert _read_state()["phase"] == "4"
        # Gating 4 auto-skips 3b too.
        scratch_log("4", "search-web", summary="web hit")
        assert scratch_gate("4")["ok"]
        assert "PHASE 3b EXIT GATE" in path.read_text(encoding="utf-8")

    def test_sutta_anchored_run_still_requires_2_5(self, tmp_path, monkeypatch):
        from tools.research_sources import scratch_gate, scratch_init

        monkeypatch.setattr("tools.scratch._SCRATCH_DIR", tmp_path)
        path = scratch_init("test-anchored")  # default class
        monkeypatch.setenv("VICAYA_SCRATCH", str(path))
        for phase in ("0", "1", "2"):
            scratch_gate(phase)
        # No auto-skip: gating 3 refuses because 2.5 is missing.
        assert scratch_gate("3")["ok"] is False

    def test_state_file_resolves_scratch_without_env(self, tmp_path, monkeypatch):
        from tools.research_sources import _scratch_path, scratch_init

        monkeypatch.setattr("tools.scratch._SCRATCH_DIR", tmp_path)
        monkeypatch.delenv("VICAYA_SCRATCH", raising=False)
        path = scratch_init("test-state")
        # No env set — resolution falls through to the active-state file.
        assert _scratch_path() == path

    def test_state_file_is_keyed_to_run(self, tmp_path, monkeypatch):
        from tools.research_sources import _state_file

        monkeypatch.setattr("tools.scratch._SCRATCH_DIR", tmp_path)
        # The state-pointer filename carries the run key, so it is per-run,
        # not a single global ".active".
        monkeypatch.setattr("tools.scratch._run_key", lambda: "run-A")
        assert _state_file() == tmp_path / ".active-run-A.json"
        monkeypatch.setattr("tools.scratch._run_key", lambda: "run-B")
        assert _state_file() == tmp_path / ".active-run-B.json"

    def test_parallel_runs_do_not_hijack_each_others_pointer(
        self, tmp_path, monkeypatch
    ):
        # Regression for the ".active scratch pointer hijack": a second run's
        # scratch-init must not redirect the first run's auto-log target.
        from tools.research_sources import _scratch_path, scratch_init

        monkeypatch.setattr("tools.scratch._SCRATCH_DIR", tmp_path)
        monkeypatch.delenv("VICAYA_SCRATCH", raising=False)

        # Run A initialises, then run B (different agent process) initialises.
        monkeypatch.setattr("tools.scratch._run_key", lambda: "agent-A")
        path_a = scratch_init("question-a")
        monkeypatch.setattr("tools.scratch._run_key", lambda: "agent-B")
        path_b = scratch_init("question-b")

        # Each run still resolves to its OWN scratch — B did not clobber A.
        monkeypatch.setattr("tools.scratch._run_key", lambda: "agent-A")
        assert _scratch_path() == path_a
        monkeypatch.setattr("tools.scratch._run_key", lambda: "agent-B")
        assert _scratch_path() == path_b

    def test_concurrent_appends_do_not_lose_entries(self, tmp_path, monkeypatch):
        # Regression for the "lost append": a run's subagents auto-log to the
        # same scratch concurrently; every entry must survive the read→write race.
        import threading

        from tools.research_sources import _append_under_phase, scratch_init

        monkeypatch.setattr("tools.scratch._SCRATCH_DIR", tmp_path)
        monkeypatch.delenv("VICAYA_SCRATCH", raising=False)
        path = scratch_init("concurrent-append")

        n = 40
        barrier = threading.Barrier(n)

        def worker(i: int) -> None:
            barrier.wait()  # release all writers at once to maximise contention
            _append_under_phase(path, "2", f"### entry-{i:03d}")

        threads = [threading.Thread(target=worker, args=(i,)) for i in range(n)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        text = path.read_text(encoding="utf-8")
        for i in range(n):
            assert f"entry-{i:03d}" in text, f"lost append: entry-{i:03d}"

    def test_gate_advances_active_phase_in_state(self, tmp_path, monkeypatch):
        from tools.research_sources import _read_state, scratch_gate, scratch_init

        monkeypatch.setattr("tools.scratch._SCRATCH_DIR", tmp_path)
        monkeypatch.delenv("VICAYA_SCRATCH", raising=False)
        scratch_init("test-advance")
        assert _read_state()["phase"] == "0"
        scratch_gate("0")
        assert _read_state()["phase"] == "1"

    def test_autolog_uses_env_scratch_over_active_state(self, tmp_path, monkeypatch):
        from tools.research_sources import _maybe_autolog, _write_state, scratch_init

        monkeypatch.setattr("tools.scratch._SCRATCH_DIR", tmp_path)
        stale_path = scratch_init("autolog-stale")
        selected_path = scratch_init("autolog-selected")
        _write_state(stale_path, "0")
        monkeypatch.setenv("VICAYA_SCRATCH", str(selected_path))
        monkeypatch.setenv("VICAYA_PHASE", "1")

        _maybe_autolog("search-vault", ["dukkha"], [])

        assert "search-vault" in selected_path.read_text(encoding="utf-8")
        assert "search-vault" not in stale_path.read_text(encoding="utf-8")

    def test_autolog_uses_active_state_without_env(self, tmp_path, monkeypatch):
        from tools.research_sources import _maybe_autolog, scratch_init

        monkeypatch.setattr("tools.scratch._SCRATCH_DIR", tmp_path)
        monkeypatch.delenv("VICAYA_SCRATCH", raising=False)
        monkeypatch.delenv("VICAYA_PHASE", raising=False)
        path = scratch_init("autolog-active")

        _maybe_autolog("search-vault", ["dukkha"], [])

        assert "search-vault" in path.read_text(encoding="utf-8")

    def test_autolog_flags_unpinned_phase_from_shared_pointer(
        self, tmp_path, monkeypatch
    ):
        """Issue #55: a phase inferred from the shared run pointer (no explicit
        VICAYA_PHASE) can be stale by the time a sibling sub-agent's call lands —
        so unpinned auto-logs must carry a visible marker a spot-check can catch."""
        from tools.research_sources import _maybe_autolog, scratch_init

        monkeypatch.setattr("tools.scratch._SCRATCH_DIR", tmp_path)
        monkeypatch.delenv("VICAYA_SCRATCH", raising=False)
        monkeypatch.delenv("VICAYA_PHASE", raising=False)
        path = scratch_init("autolog-unpinned")

        _maybe_autolog("search-vault", ["dukkha"], [])

        assert "phase-source: run-pointer" in path.read_text(encoding="utf-8")

    def test_autolog_pinned_phase_has_no_unpinned_marker(self, tmp_path, monkeypatch):
        from tools.research_sources import _maybe_autolog, scratch_init

        monkeypatch.setattr("tools.scratch._SCRATCH_DIR", tmp_path)
        path = scratch_init("autolog-pinned")
        monkeypatch.setenv("VICAYA_SCRATCH", str(path))
        monkeypatch.setenv("VICAYA_PHASE", "1")

        _maybe_autolog("search-vault", ["dukkha"], [])

        assert "phase-source" not in path.read_text(encoding="utf-8")


class TestPhaseAlias:
    """Issue #32: SKILL.md says "Phase 4a" but the phase table stores "4" —
    `scratch-log 4a` died with a raw ValueError traceback."""

    def test_scratch_log_4a_lands_under_phase_4(self, tmp_path, monkeypatch):
        from tools.research_sources import scratch_init, scratch_log

        monkeypatch.setattr("tools.scratch._SCRATCH_DIR", tmp_path)
        path = scratch_init("test-alias-log")
        monkeypatch.setenv("VICAYA_SCRATCH", str(path))
        scratch_log("4a", "web", args=["https://example.org"], summary="fetched")
        text = path.read_text(encoding="utf-8")
        web_idx = text.index("## Phase 4 — Web")
        next_idx = text.index("## Phase 4b")
        assert web_idx < text.index("https://example.org") < next_idx

    def test_scratch_gate_4a_writes_phase_4_gate(self, tmp_path, monkeypatch):
        from tools.research_sources import scratch_gate, scratch_init, scratch_log

        monkeypatch.setattr("tools.scratch._SCRATCH_DIR", tmp_path)
        path = scratch_init("test-alias-gate")
        monkeypatch.setenv("VICAYA_SCRATCH", str(path))
        _cp = ("1", "2", "2.5", "3", "3b")
        for phase in ("0", "1", "2", "2.5", "3", "3b"):
            if phase in _cp:
                scratch_log(phase, "search-canon", summary=f"hit in {phase}")
            assert scratch_gate(phase)["ok"]
        scratch_log("4", "search-web", summary="web hit")
        result = scratch_gate("4a")
        assert result["ok"]
        assert result["phase"] == "4"
        assert "### PHASE 4 EXIT GATE" in path.read_text(encoding="utf-8")

    def test_scratch_verify_accepts_4a(self, tmp_path, monkeypatch):
        from tools.research_sources import scratch_init, scratch_verify

        monkeypatch.setattr("tools.scratch._SCRATCH_DIR", tmp_path)
        path = scratch_init("test-alias-verify")
        monkeypatch.setenv("VICAYA_SCRATCH", str(path))
        result = scratch_verify(through="4a")
        assert "error" not in result
        assert result["checked_through"] == 7  # phases 0..4 inclusive

    def test_autolog_env_phase_4a_lands_under_phase_4(self, tmp_path, monkeypatch):
        from tools.research_sources import _maybe_autolog, scratch_init

        monkeypatch.setattr("tools.scratch._SCRATCH_DIR", tmp_path)
        path = scratch_init("test-alias-autolog")
        monkeypatch.setenv("VICAYA_SCRATCH", str(path))
        monkeypatch.setenv("VICAYA_PHASE", "4a")
        _maybe_autolog("search-web", ["query"], [])
        text = path.read_text(encoding="utf-8")
        web_idx = text.index("## Phase 4 — Web")
        next_idx = text.index("## Phase 4b")
        assert web_idx < text.index("search-web") < next_idx

    def test_unknown_phase_raises_with_valid_list(self, tmp_path, monkeypatch):
        import pytest

        from tools.research_sources import scratch_init, scratch_log

        monkeypatch.setattr("tools.scratch._SCRATCH_DIR", tmp_path)
        path = scratch_init("test-alias-unknown")
        monkeypatch.setenv("VICAYA_SCRATCH", str(path))
        with pytest.raises(ValueError, match=r"unknown phase '8'.*4a"):
            scratch_log("8", "web")

    def test_cli_scratch_log_unknown_phase_clean_error(
        self, tmp_path, monkeypatch, capsys
    ):
        import json

        import tools.research_sources as rs

        monkeypatch.setattr("tools.scratch._SCRATCH_DIR", tmp_path)
        path = rs.scratch_init("test-alias-cli")
        monkeypatch.setenv("VICAYA_SCRATCH", str(path))
        monkeypatch.setattr(
            sys, "argv", ["research_sources", "scratch-log", "9", "web", "query"]
        )
        assert rs._cli() == 1
        out = json.loads(capsys.readouterr().out)
        assert out["ok"] is False
        assert "unknown phase" in out["error"]

    def test_cli_scratch_log_4a_succeeds(self, tmp_path, monkeypatch, capsys):
        import json

        import tools.research_sources as rs

        monkeypatch.setattr("tools.scratch._SCRATCH_DIR", tmp_path)
        path = rs.scratch_init("test-alias-cli-ok")
        monkeypatch.setenv("VICAYA_SCRATCH", str(path))
        monkeypatch.setattr(
            sys,
            "argv",
            ["research_sources", "scratch-log", "4a", "web", "https://example.org"],
        )
        assert rs._cli() == 0
        out = json.loads(capsys.readouterr().out)
        assert out["ok"] is True
        assert "## Phase 4 — Web" in path.read_text(encoding="utf-8")


class TestScratchWhich:
    """scratch-which prints JSON by default like every other subcommand; --raw opts into a bare path string for shell variable assignment."""

    def test_default_prints_json(self, tmp_path, monkeypatch, capsys):
        import json

        import tools.research_sources as rs

        monkeypatch.setattr("tools.scratch._SCRATCH_DIR", tmp_path)
        path = rs.scratch_init("test-which-json")
        monkeypatch.setenv("VICAYA_SCRATCH", str(path))
        monkeypatch.setattr(sys, "argv", ["research_sources", "scratch-which"])
        assert rs._cli() == 0
        out = json.loads(capsys.readouterr().out)
        assert out["path"] == str(path)

    def test_raw_prints_bare_path(self, tmp_path, monkeypatch, capsys):
        import tools.research_sources as rs

        monkeypatch.setattr("tools.scratch._SCRATCH_DIR", tmp_path)
        path = rs.scratch_init("test-which-raw")
        monkeypatch.setenv("VICAYA_SCRATCH", str(path))
        monkeypatch.setattr(sys, "argv", ["research_sources", "scratch-which", "--raw"])
        assert rs._cli() == 0
        assert capsys.readouterr().out.strip() == str(path)


class TestScratchSetNote:
    """scratch-set-note records the vault note path the Phase 7 gate scans."""

    def test_sets_vault_note_header(self, tmp_path, monkeypatch):
        from tools.research_sources import scratch_init, scratch_set_note

        monkeypatch.setattr("tools.scratch._SCRATCH_DIR", tmp_path)
        path = scratch_init("set-note")
        monkeypatch.setenv("VICAYA_SCRATCH", str(path))
        note = tmp_path / "note.md"
        note.write_text("# Note\n", encoding="utf-8")

        result = scratch_set_note(str(note))

        assert result["ok"]
        text = path.read_text(encoding="utf-8")
        assert f"**Vault note:** {result['vault_note']}" in text
        assert "<set at Phase 7>" not in text

    def test_gate_7_scans_note_set_via_helper(self, tmp_path, monkeypatch):
        from tools.research_sources import (
            scratch_gate,
            scratch_init,
            scratch_self_audit,
            scratch_set_note,
        )

        monkeypatch.setattr("tools.scratch._SCRATCH_DIR", tmp_path)
        path = scratch_init("set-note-gate")
        monkeypatch.setenv("VICAYA_SCRATCH", str(path))
        note = tmp_path / "fake_note.md"
        note.write_text(
            "# Note\n\nThe reviewer cited MN999 [REJECTED — not in sutta_info].\n",
            encoding="utf-8",
        )
        assert scratch_set_note(str(note))["ok"]
        from tools.research_sources import scratch_log

        _cp = ("1", "2", "2.5", "3", "3b", "4", "4b", "4c")
        for phase in ("0", "1", "2", "2.5", "3", "3b", "4", "4b", "4c", "5", "6"):
            if phase in _cp:
                scratch_log(phase, "search-canon", summary=f"hit in {phase}")
            assert scratch_gate(phase)["ok"]
        assert scratch_self_audit(answers=["none"] * 6)["ok"]

        result = scratch_gate("7")

        assert result["ok"] is False
        assert result["offending_lines"]

    def test_relative_path_resolves_against_vault(self, tmp_path, monkeypatch):
        from tools.research_sources import scratch_init, scratch_set_note

        monkeypatch.setattr("tools.scratch._SCRATCH_DIR", tmp_path)
        path = scratch_init("set-note-vault")
        monkeypatch.setenv("VICAYA_SCRATCH", str(path))
        vault = tmp_path / "vault"
        (vault / "Vicaya").mkdir(parents=True)
        note = vault / "Vicaya" / "2026-06-11 - topic.md"
        note.write_text("# Note\n", encoding="utf-8")
        monkeypatch.setenv("VICAYA_VAULT_PATH", str(vault))

        result = scratch_set_note("Vicaya/2026-06-11 - topic.md")

        assert result["ok"]
        assert result["vault_note"] == str(note.resolve())

    def test_missing_note_refuses_without_writing(self, tmp_path, monkeypatch):
        from tools.research_sources import scratch_init, scratch_set_note

        monkeypatch.setattr("tools.scratch._SCRATCH_DIR", tmp_path)
        path = scratch_init("set-note-missing")
        monkeypatch.setenv("VICAYA_SCRATCH", str(path))
        monkeypatch.delenv("VICAYA_VAULT_PATH", raising=False)

        result = scratch_set_note(str(tmp_path / "no-such-note.md"))

        assert result["ok"] is False
        assert "not found" in result["message"]
        assert "<set at Phase 7>" in path.read_text(encoding="utf-8")

    def test_pdf_line_inserted_then_replaced(self, tmp_path, monkeypatch):
        from tools.research_sources import scratch_init, scratch_set_note

        monkeypatch.setattr("tools.scratch._SCRATCH_DIR", tmp_path)
        path = scratch_init("set-note-pdf")
        monkeypatch.setenv("VICAYA_SCRATCH", str(path))
        note = tmp_path / "note.md"
        note.write_text("# Note\n", encoding="utf-8")

        assert scratch_set_note(str(note), pdf="/tmp/out.pdf")["ok"]
        assert scratch_set_note(str(note), pdf="skipped")["ok"]

        text = path.read_text(encoding="utf-8")
        assert text.count("**PDF:**") == 1
        assert "**PDF:** skipped" in text

    def test_inserts_header_when_absent(self, tmp_path, monkeypatch):
        from tools.research_sources import scratch_init, scratch_set_note

        monkeypatch.setattr("tools.scratch._SCRATCH_DIR", tmp_path)
        path = scratch_init("set-note-legacy")
        monkeypatch.setenv("VICAYA_SCRATCH", str(path))
        text = path.read_text(encoding="utf-8")
        text = text.replace("**Vault note:** <set at Phase 7>\n", "")
        path.write_text(text, encoding="utf-8")
        note = tmp_path / "note.md"
        note.write_text("# Note\n", encoding="utf-8")

        result = scratch_set_note(str(note))

        assert result["ok"]
        new_text = path.read_text(encoding="utf-8")
        assert f"**Vault note:** {result['vault_note']}" in new_text
        assert new_text.index("**Run class:**") < new_text.index("**Vault note:**")


class TestScratchCheckCoverage:
    """scratch-check-coverage flags library hits absent from the final note.

    Regression for issue #64 (re-scoped 2026-07-05): a note comparing 6
    real scratch/note pairs found canon/web coverage is already
    self-curated well via the rejection table, but one library document
    with an on-topic snippet slipped through uncited and unlisted.
    """

    def _log_library_hit(self, tmp_path, document_id, title="A Relevant Book.pdf"):
        import json as _json

        from tools.research_sources import scratch_log

        results_file = tmp_path / f"lib-{document_id}.json"
        results_file.write_text(
            _json.dumps(
                [
                    {
                        "document_id": document_id,
                        "title": title,
                        "relative_path": f"Library/{title}",
                        "snippet": "... clearly on-topic passage ...",
                    }
                ]
            ),
            encoding="utf-8",
        )
        scratch_log(
            "3",
            "search-library-folders",
            summary="library hit",
            results_file=results_file,
            hits=1,
        )

    def test_flags_uncited_unlisted_library_hit(self, tmp_path, monkeypatch):
        from tools.research_sources import (
            scratch_check_coverage,
            scratch_init,
            scratch_set_note,
        )

        monkeypatch.setattr("tools.scratch._SCRATCH_DIR", tmp_path)
        path = scratch_init("coverage-gap")
        monkeypatch.setenv("VICAYA_SCRATCH", str(path))
        self._log_library_hit(tmp_path, 2366, "Meditation Centers Directory.pdf")
        note = tmp_path / "note.md"
        note.write_text(
            "# Note\n\nNo mention of that document at all.\n", encoding="utf-8"
        )
        assert scratch_set_note(str(note))["ok"]

        result = scratch_check_coverage()

        assert result["ok"] is False
        assert result["library_hits_gathered"] == 1
        assert result["unaccounted"] == [
            {
                "document_id": 2366,
                "title": "Meditation Centers Directory.pdf",
                "relative_path": "Library/Meditation Centers Directory.pdf",
                "snippet": "... clearly on-topic passage ...",
            }
        ]

    def test_passes_when_cited_as_footnote(self, tmp_path, monkeypatch):
        from tools.research_sources import (
            scratch_check_coverage,
            scratch_init,
            scratch_set_note,
        )

        monkeypatch.setattr("tools.scratch._SCRATCH_DIR", tmp_path)
        path = scratch_init("coverage-cited")
        monkeypatch.setenv("VICAYA_SCRATCH", str(path))
        self._log_library_hit(tmp_path, 2365)
        note = tmp_path / "note.md"
        note.write_text(
            "# Note\n\nSome claim.[^calibre-2365]\n\n[^calibre-2365]: A Relevant Book.\n",
            encoding="utf-8",
        )
        assert scratch_set_note(str(note))["ok"]

        result = scratch_check_coverage()

        assert result["ok"] is True
        assert result["unaccounted"] == []

    def test_passes_when_logged_in_rejection_table_by_id(self, tmp_path, monkeypatch):
        from tools.research_sources import (
            scratch_check_coverage,
            scratch_init,
            scratch_set_note,
        )

        monkeypatch.setattr("tools.scratch._SCRATCH_DIR", tmp_path)
        path = scratch_init("coverage-rejected")
        monkeypatch.setenv("VICAYA_SCRATCH", str(path))
        self._log_library_hit(tmp_path, 7439)
        note = tmp_path / "note.md"
        note.write_text(
            "# Note\n\n"
            "## Sources Investigated, Not Used\n"
            "| A Relevant Book (Calibre #7439) | T3 Library | Off-topic |\n",
            encoding="utf-8",
        )
        assert scratch_set_note(str(note))["ok"]

        result = scratch_check_coverage()

        assert result["ok"] is True
        assert result["unaccounted"] == []

    def test_refuses_without_vault_note(self, tmp_path, monkeypatch):
        from tools.research_sources import scratch_check_coverage, scratch_init

        monkeypatch.setattr("tools.scratch._SCRATCH_DIR", tmp_path)
        path = scratch_init("coverage-no-note")
        monkeypatch.setenv("VICAYA_SCRATCH", str(path))
        self._log_library_hit(tmp_path, 1)

        result = scratch_check_coverage()

        assert result["ok"] is False
        assert "scratch-set-note" in result["error"]


class TestScratchSelfAudit:
    """scratch-self-audit records the failure checklist the Phase 7 gate requires."""

    def test_no_answers_prints_questions_without_writing(self, tmp_path, monkeypatch):
        from tools.research_sources import scratch_init, scratch_self_audit
        from tools.scratch import _SELF_AUDIT_QUESTIONS

        monkeypatch.setattr("tools.scratch._SCRATCH_DIR", tmp_path)
        path = scratch_init("audit-questions")
        monkeypatch.setenv("VICAYA_SCRATCH", str(path))

        result = scratch_self_audit()

        assert result["ok"] is False
        assert result["questions"] == _SELF_AUDIT_QUESTIONS
        assert "### SELF-AUDIT" not in path.read_text(encoding="utf-8")

    def test_wrong_answer_count_refuses(self, tmp_path, monkeypatch):
        from tools.research_sources import scratch_init, scratch_self_audit

        monkeypatch.setattr("tools.scratch._SCRATCH_DIR", tmp_path)
        path = scratch_init("audit-count")
        monkeypatch.setenv("VICAYA_SCRATCH", str(path))

        result = scratch_self_audit(answers=["only one"])

        assert result["ok"] is False
        assert "expected" in result["error"]
        assert "### SELF-AUDIT" not in path.read_text(encoding="utf-8")

    def test_blank_answer_refuses(self, tmp_path, monkeypatch):
        from tools.research_sources import scratch_init, scratch_self_audit
        from tools.scratch import _SELF_AUDIT_QUESTIONS

        monkeypatch.setattr("tools.scratch._SCRATCH_DIR", tmp_path)
        path = scratch_init("audit-blank")
        monkeypatch.setenv("VICAYA_SCRATCH", str(path))
        answers = ["checked"] * (len(_SELF_AUDIT_QUESTIONS) - 1) + ["  "]

        result = scratch_self_audit(answers=answers)

        assert result["ok"] is False
        assert "### SELF-AUDIT" not in path.read_text(encoding="utf-8")

    def test_records_block_under_phase_7(self, tmp_path, monkeypatch):
        from tools.research_sources import scratch_init, scratch_self_audit
        from tools.scratch import _SELF_AUDIT_QUESTIONS

        monkeypatch.setattr("tools.scratch._SCRATCH_DIR", tmp_path)
        path = scratch_init("audit-record")
        monkeypatch.setenv("VICAYA_SCRATCH", str(path))
        answers = [f"answer {i}" for i in range(len(_SELF_AUDIT_QUESTIONS))]

        result = scratch_self_audit(answers=answers)

        assert result["ok"]
        text = path.read_text(encoding="utf-8")
        assert "### SELF-AUDIT" in text
        assert text.index("## Phase 7") < text.index("### SELF-AUDIT")
        for q, a in zip(_SELF_AUDIT_QUESTIONS, answers):
            assert f"- Q: {q}" in text
            assert f"  A: {a}" in text

    def test_second_call_does_not_duplicate(self, tmp_path, monkeypatch):
        from tools.research_sources import scratch_init, scratch_self_audit
        from tools.scratch import _SELF_AUDIT_QUESTIONS

        monkeypatch.setattr("tools.scratch._SCRATCH_DIR", tmp_path)
        path = scratch_init("audit-dup")
        monkeypatch.setenv("VICAYA_SCRATCH", str(path))
        n = len(_SELF_AUDIT_QUESTIONS)

        assert scratch_self_audit(answers=["none"] * n)["ok"]
        again = scratch_self_audit(answers=["none"] * n)

        assert again["ok"]
        assert "not duplicated" in again["note"]
        assert path.read_text(encoding="utf-8").count("### SELF-AUDIT") == 1

    def test_gate_7_refuses_without_audit(self, tmp_path, monkeypatch):
        from tools.research_sources import scratch_gate, scratch_init, scratch_set_note

        monkeypatch.setattr("tools.scratch._SCRATCH_DIR", tmp_path)
        path = scratch_init("audit-gate-refuse")
        monkeypatch.setenv("VICAYA_SCRATCH", str(path))
        note = tmp_path / "note.md"
        note.write_text("# Note\n\nClean.\n", encoding="utf-8")
        assert scratch_set_note(str(note))["ok"]
        from tools.research_sources import scratch_log

        _cp = ("1", "2", "2.5", "3", "3b", "4", "4b", "4c")
        for phase in ("0", "1", "2", "2.5", "3", "3b", "4", "4b", "4c", "5", "6"):
            if phase in _cp:
                scratch_log(phase, "search-canon", summary=f"hit in {phase}")
            assert scratch_gate(phase)["ok"]

        result = scratch_gate("7")

        assert result["ok"] is False
        assert "scratch-self-audit" in result["message"]
        assert "### PHASE 7 EXIT GATE" not in path.read_text(encoding="utf-8")

    def test_gate_7_passes_with_audit_and_clean_note(self, tmp_path, monkeypatch):
        from tools.research_sources import (
            scratch_gate,
            scratch_init,
            scratch_self_audit,
            scratch_set_note,
        )
        from tools.scratch import _SELF_AUDIT_QUESTIONS

        monkeypatch.setattr("tools.scratch._SCRATCH_DIR", tmp_path)
        path = scratch_init("audit-gate-pass")
        monkeypatch.setenv("VICAYA_SCRATCH", str(path))
        note = tmp_path / "note.md"
        note.write_text("# Note\n\nClean.\n", encoding="utf-8")
        assert scratch_set_note(str(note))["ok"]
        from tools.research_sources import scratch_log

        _cp = ("1", "2", "2.5", "3", "3b", "4", "4b", "4c")
        for phase in ("0", "1", "2", "2.5", "3", "3b", "4", "4b", "4c", "5", "6"):
            if phase in _cp:
                scratch_log(phase, "search-canon", summary=f"hit in {phase}")
            assert scratch_gate(phase)["ok"]
        assert scratch_self_audit(answers=["none"] * len(_SELF_AUDIT_QUESTIONS))["ok"]

        result = scratch_gate("7")

        assert result["ok"], result

    def test_uninitialised_scratch_raises(self, tmp_path, monkeypatch):
        from tools.research_sources import scratch_self_audit

        monkeypatch.setattr("tools.scratch._SCRATCH_DIR", tmp_path)
        monkeypatch.setenv("VICAYA_SCRATCH", str(tmp_path / "no-such.md"))

        with pytest.raises(FileNotFoundError):
            scratch_self_audit()


@canon_available
class TestVerifyCitation:
    """verify_citation queries dpd.db sutta_info (existence-only)."""

    def test_real_ref_is_verified(self):
        from tools.research_sources import verify_citation

        r = verify_citation("MN60")
        assert r["exists"]
        assert any(m["sc_code"] == "MN60" for m in r["matches"])

    def test_real_ref_with_space_normalises(self):
        from tools.research_sources import verify_citation

        r = verify_citation("SN 46.42")
        assert r["exists"]
        assert r["normalised"] == ["SN46.42"]

    def test_fabricated_ref_is_rejected(self):
        from tools.research_sources import verify_citation

        r = verify_citation("MN999")
        assert r["exists"] is False
        assert r["matches"] == []

    def test_sn_prefix_yields_two_candidates(self):
        from tools.research_sources import verify_citation

        r = verify_citation("Sn 4.8")
        # Both SN4.8 (Saṃyutta) and SNP4.8 (Suttanipāta) are real
        assert set(r["normalised"]) == {"SN4.8", "SNP4.8"}
        assert len(r["matches"]) >= 1

    def test_resolves_via_dpd_code_or_dpr_code(self):
        # dpd.db carries multiple coding systems. A book-range dpd_code like
        # DN1-13 should resolve. So should dpr_code (Digital Pali Reader),
        # which usually matches sc_code in format.
        from tools.research_sources import verify_citation

        r = verify_citation("DN1-13")
        assert r["exists"], r
        # And the row carries cross-system codes in the match.
        m = r["matches"][0]
        assert "dpd_code" in m
        assert "dpr_code" in m
        assert "bjt_sutta_code" in m

    def test_case_aware_sn_disambiguation(self):
        # Scholarly convention:
        #   `SN` (all caps)       → Saṃyutta only
        #   `Sn` / `sn` / `sN`    → ambiguous (Saṃyutta or Suttanipāta)
        #   `Snp` / `SNP` / `snp` → Suttanipāta only (the `p` disambiguates)
        # Reviewer caught: lowercase `sn 4.8` previously fell through to upper-only
        # via `s.upper()`, missing the ambiguity path. Mixed-case `Sn 4.8` did
        # trigger it. They should behave identically.
        from tools.research_sources import _normalise_citation

        assert _normalise_citation("SN 4.8") == ["SN4.8"]
        assert set(_normalise_citation("Sn 4.8")) == {"SN4.8", "SNP4.8"}
        assert set(_normalise_citation("sn 4.8")) == {"SN4.8", "SNP4.8"}
        assert _normalise_citation("snp 4.8") == ["SNP4.8"]
        assert _normalise_citation("Snp 4.8") == ["SNP4.8"]
        assert _normalise_citation("SNP 4.8") == ["SNP4.8"]

    def test_verse_ref_in_range_stored_book_verifies(self):
        # Dhp is stored as verse-range rows (DHP116-128 etc.), so single
        # verses must verify by numeric containment, not exact match.
        from tools.research_sources import verify_citation

        for ref in ("Dhp 178", "Dhp 128", "Dhp 95"):
            r = verify_citation(ref)
            assert r["verdict"] == "verified", (ref, r)

    def test_range_stored_an_suttas_verify_by_containment(self):
        # AN ones/twos and the AN8 peyyāla block are stored as ranges
        # (AN2.21-31, AN8.117-626): single suttas inside them must verify.
        from tools.research_sources import verify_citation

        for ref in ("AN2.31", "AN8.119", "AN1.600"):
            r = verify_citation(ref)
            assert r["verdict"] == "verified", (ref, r)

    def test_hyphenated_range_verifies_via_endpoints(self):
        # SN56.27 and SN56.28 both exist but "SN56.27-28" is not a key;
        # the range must verify by resolving both endpoints.
        from tools.research_sources import verify_citation

        for ref in ("SN56.27-28", "SN48.9-10", "SN46.14-16"):
            r = verify_citation(ref)
            assert r["verdict"] == "verified", (ref, r)

    def test_fabricated_range_still_rejected(self):
        from tools.research_sources import verify_citation

        r = verify_citation("SN99.1-2")
        assert r["verdict"] == "rejected"
        assert r["exists"] is False

    def test_thag_poem_resolves_via_th_alias(self):
        # dpd_code uses TH1…TH264, not THAG…; "Thag 5" must still verify.
        from tools.research_sources import verify_citation

        r = verify_citation("Thag 5")
        assert r["verdict"] == "verified", r

    def test_global_verse_number_is_unverifiable_not_rejected(self):
        # Snp/Thag global verse numbers have no per-verse row in sutta_info.
        # They must NOT be branded fabrications.
        from tools.research_sources import verify_citation

        for ref in ("Sn 925", "Snp 437", "Thag 591"):
            r = verify_citation(ref)
            assert r["verdict"] == "unverifiable-form", (ref, r)
            assert r["exists"] is False
            assert "verse number" in r["note"]


@canon_available
class TestAnnotateCitations:
    def test_stamps_each_citation_inline(self):
        from tools.research_sources import annotate_citations

        text = "Compare MN60 with SN46.42 and MN999."
        out = annotate_citations(text)
        assert "MN60 [VERIFIED]" in out
        assert "SN46.42 [VERIFIED]" in out
        assert "MN999 [REJECTED" in out

    def test_no_sutta_name_in_verified_label(self):
        # Per review feedback: existence-only label, no content-level implication.
        from tools.research_sources import annotate_citations

        out = annotate_citations("See MN60.")
        # The label must not embed the English sutta name "Unfailing"
        assert "Unfailing" not in out
        assert "MN60 [VERIFIED]" in out

    def test_verse_number_stamped_unverifiable(self):
        from tools.research_sources import annotate_citations

        out = annotate_citations("Quoting Sn 925 and Dhp 178 here.")
        assert "Sn 925 [UNVERIFIABLE" in out
        assert "Dhp 178 [VERIFIED]" in out


# ---------- search_vault error handling ----------


class TestSearchVaultErrorHandling:
    def _mock_run(self, stdout: str, returncode: int = 0) -> MagicMock:
        m = MagicMock()
        m.stdout = stdout
        m.stderr = ""
        m.returncode = returncode
        return m

    def test_non_json_stdout_raises(self, monkeypatch):
        """CLI exits 0 but prints plaintext → RuntimeError, not silent []."""
        monkeypatch.setattr(
            subprocess,
            "run",
            MagicMock(
                return_value=self._mock_run(
                    "The CLI is unable to find Obsidian. Please make sure Obsidian is running and try again."
                )
            ),
        )
        with pytest.raises(RuntimeError, match="non-JSON"):
            search_vault("dukkha")

    def test_non_zero_exit_raises(self, monkeypatch):
        """CLI exits non-zero → RuntimeError with the error message."""
        monkeypatch.setattr(
            subprocess,
            "run",
            MagicMock(return_value=self._mock_run("fatal error", returncode=1)),
        )
        with pytest.raises(RuntimeError, match="exited 1"):
            search_vault("dukkha")

    def test_empty_stdout_returns_empty_list(self, monkeypatch):
        """Empty stdout (vault unreachable, no output) → []."""
        monkeypatch.setattr(
            subprocess,
            "run",
            MagicMock(return_value=self._mock_run("")),
        )
        assert search_vault("dukkha") == []

    def test_no_matches_sentinel_returns_empty_list(self, monkeypatch):
        """CLI's literal zero-hit message → [], not a false 'app not running' error."""
        monkeypatch.setattr(
            subprocess,
            "run",
            MagicMock(return_value=self._mock_run("No matches found.")),
        )
        assert search_vault("dukkha") == []

    def test_valid_json_empty_returns_empty_list(self, monkeypatch):
        """Parsed empty JSON list → [] (genuine 0 hits)."""
        monkeypatch.setattr(
            subprocess,
            "run",
            MagicMock(return_value=self._mock_run("[]")),
        )
        assert search_vault("dukkha") == []

    def test_valid_json_hit_returns_vault_hits(self, monkeypatch):
        """Well-formed JSON → VaultHit list."""
        payload = '[{"file": "Vicaya/test.md", "matches": [{"text": "dukkha arises", "line": 3}]}]'
        monkeypatch.setattr(
            subprocess,
            "run",
            MagicMock(return_value=self._mock_run(payload)),
        )
        hits = search_vault("dukkha")
        assert len(hits) == 1
        assert hits[0].path == "Vicaya/test.md"
        assert hits[0].snippet == "dukkha arises"
        assert hits[0].line == 3


class TestEnvSubcommand:
    """`env` prints VICAYA_* config as eval-able shell export lines (#37)."""

    def _run_env(self, monkeypatch, capsys):
        import tools.research_sources as rs

        monkeypatch.setattr(sys, "argv", ["research_sources", "env"])
        assert rs._cli() == 0
        return capsys.readouterr().out.splitlines()

    def test_tilde_is_expanded(self, monkeypatch, capsys):
        monkeypatch.setenv("VICAYA_TEST_TILDE", "~/MyFiles/Obsidian")
        lines = self._run_env(monkeypatch, capsys)
        home = str(Path.home())
        assert f"export VICAYA_TEST_TILDE={home}/MyFiles/Obsidian" in lines

    def test_value_with_spaces_survives_shell_eval(self, monkeypatch, capsys):
        import shlex

        monkeypatch.setenv(
            "VICAYA_TEST_SPACES", "~/MyFiles/2_Resources/Early Buddhist Connections"
        )
        lines = self._run_env(monkeypatch, capsys)
        line = next(entry for entry in lines if "VICAYA_TEST_SPACES" in entry)
        words = shlex.split(line)
        assert words[0] == "export"
        assert words[1] == (
            f"VICAYA_TEST_SPACES={Path.home()}/MyFiles/2_Resources/"
            "Early Buddhist Connections"
        )

    def test_non_vicaya_keys_excluded(self, monkeypatch, capsys):
        monkeypatch.setenv("OPENROUTER_TEST_KEY", "secret")
        lines = self._run_env(monkeypatch, capsys)
        assert not any("OPENROUTER_TEST_KEY" in entry for entry in lines)

    def test_output_is_sorted_by_key(self, monkeypatch, capsys):
        lines = self._run_env(monkeypatch, capsys)
        keys = [entry.split("=", 1)[0].removeprefix("export ") for entry in lines]
        assert keys == sorted(keys)

    def test_eval_in_real_bash_sets_variable(self, monkeypatch, capsys):
        """End-to-end: bash eval of the output yields the expanded value."""
        monkeypatch.setenv("VICAYA_TEST_E2E", "~/some dir/with spaces")
        lines = self._run_env(monkeypatch, capsys)
        script = "\n".join(lines) + '\necho "$VICAYA_TEST_E2E"'
        result = subprocess.run(
            ["bash", "-c", script], capture_output=True, text=True, check=True
        )
        assert result.stdout.strip() == f"{Path.home()}/some dir/with spaces"


# ---------- --quiet compact stdout (full data still goes to scratch) ----------


class TestCompactQuietOutput:
    """`_compact` shapes the --quiet stdout view only; it must preserve every
    reference field and truncate only long text, so the scratch dossier (built
    from the untruncated result) is never degraded."""

    def test_short_strings_pass_through_unchanged(self):
        from tools.research_sources import _compact

        assert _compact("short pali line") == "short pali line"

    def test_long_strings_are_truncated_with_marker(self):
        from tools.research_sources import _QUIET_MAXLEN, _compact

        long = "x" * (_QUIET_MAXLEN + 50)
        out = _compact(long)
        assert out.startswith("x" * _QUIET_MAXLEN)
        assert "full text in scratch" in out
        assert len(out) < len(long) + 60

    def test_canon_hit_refs_preserved_text_truncated(self):
        from tools.research_sources import _QUIET_MAXLEN, CanonHit, _compact

        hit = CanonHit(
            book_code="s0505m_mul",
            paranum="261",
            pali="P" * (_QUIET_MAXLEN + 100),
            english="E" * (_QUIET_MAXLEN + 100),
        )
        out = _compact([hit])
        assert isinstance(out, list) and len(out) == 1
        item = out[0]
        # references survive intact for resolve-citation / id-range follow-ups
        assert item["book_code"] == "s0505m_mul"
        assert item["paranum"] == "261"
        # bulky text fields are clipped
        assert "full text in scratch" in item["pali"]
        assert "full text in scratch" in item["english"]

    def test_recurses_nested_dicts_and_lists(self):
        from tools.research_sources import _QUIET_MAXLEN, _compact

        payload = {
            "count": 2,
            "parallels_found": [{"ref": "MA98", "text": "T" * (_QUIET_MAXLEN + 10)}],
            "parallels_missing": ["EA12.1"],
        }
        out = _compact(payload)
        assert out["count"] == 2
        assert out["parallels_missing"] == ["EA12.1"]
        assert out["parallels_found"][0]["ref"] == "MA98"
        assert "full text in scratch" in out["parallels_found"][0]["text"]

    def test_non_string_scalars_unchanged(self):
        from tools.research_sources import _compact

        assert _compact({"line": 5, "resemblance": True, "n": None}) == {
            "line": 5,
            "resemblance": True,
            "n": None,
        }


class TestGetEbcOverview:
    """get_ebc_overview must handle the Sn/SNP ambiguity the same way
    _normalise_citation does: mixed-case "Sn" tries SNP first, all-caps "SN"
    is Saṃyutta only."""

    @pytest.fixture
    def ebc_vault(self, tmp_path):
        vault = tmp_path / "vault"
        snp_dir = vault / "+Suttas" / "Overviews Suttas" / "SNP"
        sn_dir = vault / "+Suttas" / "Overviews Suttas" / "SN"
        snp_dir.mkdir(parents=True)
        sn_dir.mkdir(parents=True)
        (snp_dir / "SNP2.2.md").write_text(
            '---\nsutta_code: "SNP2.2"\nsutta_title: "Ratanasuttaṃ"\n---\n',
            encoding="utf-8",
        )
        (sn_dir / "SN2.2.md").write_text(
            '---\nsutta_code: "SN2.2"\nsutta_title: "Dutiyakassapasuttaṃ"\n---\n',
            encoding="utf-8",
        )
        return vault

    def test_snp_code_returns_suttanipata(self, ebc_vault):
        from tools.research_sources import get_ebc_overview

        result = get_ebc_overview("SNP2.2", vault=ebc_vault)
        assert result is not None
        assert result.code == "SNP2.2"

    def test_sn_all_caps_returns_samyutta(self, ebc_vault):
        from tools.research_sources import get_ebc_overview

        result = get_ebc_overview("SN2.2", vault=ebc_vault)
        assert result is not None
        assert result.code == "SN2.2"

    def test_sn_mixed_case_prefers_suttanipata(self, ebc_vault):
        # Regression: "Sn 2.2" previously normalised to "SN2.2" and returned
        # the Saṃyutta sutta instead of the Suttanipāta one.
        from tools.research_sources import get_ebc_overview

        result = get_ebc_overview("Sn 2.2", vault=ebc_vault)
        assert result is not None
        assert result.code == "SNP2.2"

    def test_sn_mixed_case_falls_back_to_samyutta_when_no_snp(self, tmp_path):
        from tools.research_sources import get_ebc_overview

        vault = tmp_path / "vault"
        sn_dir = vault / "+Suttas" / "Overviews Suttas" / "SN"
        sn_dir.mkdir(parents=True)
        (sn_dir / "SN2.2.md").write_text(
            '---\nsutta_code: "SN2.2"\nsutta_title: "Dutiyakassapasuttaṃ"\n---\n',
            encoding="utf-8",
        )
        result = get_ebc_overview("Sn 2.2", vault=vault)
        assert result is not None
        assert result.code == "SN2.2"
