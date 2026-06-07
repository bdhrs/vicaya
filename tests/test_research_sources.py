"""Integration tests for research_sources helpers.

Some tests hit real local systems (Obsidian CLI, SQLite canon db, Calibre FTS via
calibredb); Calibre metadata tests use a hermetic temp `metadata.db`. Tests that
need optional tools or data are skipped automatically when unavailable, so the
suite stays green on a machine that doesn't have everything wired up yet.
"""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tools.research_sources import (  # noqa: E402
    DEFAULT_CALIBRE_LIBRARY,
    DEFAULT_CANON_DB,
    DEFAULT_DPD_DB,
    DEFAULT_GRETIL_PATH,
    CalibreHit,
    CanonHit,
    VaultHit,
    gemini_cross_check,
    lookup_book,
    resolve_citation,
    search_calibre,
    search_canon,
    search_sanskrit,
    search_vault,
)

# ---------- skip markers ----------

obsidian_available = pytest.mark.skipif(
    shutil.which("obsidian") is None, reason="obsidian CLI not installed"
)
_calibre_library_present = (
    DEFAULT_CALIBRE_LIBRARY is not None and DEFAULT_CALIBRE_LIBRARY.exists()
)
calibre_available = pytest.mark.skipif(
    shutil.which("calibredb") is None or not _calibre_library_present,
    reason="calibredb or library not available",
)
_canon_db_present = DEFAULT_CANON_DB is not None and DEFAULT_CANON_DB.exists()
canon_available = pytest.mark.skipif(
    not _canon_db_present, reason="canon db not available"
)
gemini_available = pytest.mark.skipif(
    shutil.which("gemini") is None, reason="gemini CLI not installed"
)
dpd_available = pytest.mark.skipif(
    DEFAULT_DPD_DB is None or not DEFAULT_DPD_DB.exists(),
    reason="dpd.db not configured (VICAYA_DPD_DB)",
)


def _dpd_translator_present() -> bool:
    for candidate in (
        Path(__file__).resolve().parents[2] / "dpd-db" / "tools" / "cst_book_translator.py",
        Path.home() / "MyFiles" / "3_Active" / "dpd-db" / "tools" / "cst_book_translator.py",
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
        hits = search_canon(
            "suffering", books=["s0201m_mul"], lang="english", limit=3
        )
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


# ---------- search_vault ----------


@obsidian_available
class TestSearchVault:
    def test_search_returns_list(self):
        # We don't know what's in the vault; just verify the call shape works.
        hits = search_vault("the", limit=3)
        assert isinstance(hits, list)
        for h in hits:
            assert isinstance(h, VaultHit)


# ---------- search_calibre ----------


@calibre_available
class TestSearchCalibre:
    def test_metadata_search_by_tag(self):
        from tools.research_sources import CalibreUnavailable
        try:
            hits = search_calibre("", tags=["Buddhism"], limit=3)
        except CalibreUnavailable as e:
            pytest.skip(f"calibre library locked: {e}")
        assert isinstance(hits, list)
        for h in hits:
            assert isinstance(h, CalibreHit)
            assert h.book_id > 0
            assert h.title

    def test_search_returns_calibre_hits(self):
        from tools.research_sources import CalibreUnavailable
        try:
            hits = search_calibre("Buddha", limit=3)
        except CalibreUnavailable as e:
            pytest.skip(f"calibre library locked: {e}")
        assert isinstance(hits, list)


# ---------- gemini_cross_check ----------


@gemini_available
class TestGeminiCrossCheck:
    def test_trivial_prompt_returns_text(self):
        # Trivial call; just verify the subprocess works and we get a string.
        out = gemini_cross_check("Reply with the single word: pong")
        assert isinstance(out, str)
        # Don't assert content — model may be chatty. Empty string is also fine
        # (means timeout/error path was hit cleanly without crashing).


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
            lambda *a, **kw: Result(),
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

        def _boom(*a, **kw):
            raise AssertionError("network must not be called on cache hit")

        try:
            import youtube_transcript_api
            monkeypatch.setattr(
                youtube_transcript_api.YouTubeTranscriptApi, "__init__", _boom
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

    @sc_available
    def test_text_gaps_flagged_when_missing(self):
        from tools.research_sources import sc_parallels

        ps = sc_parallels("mn18", include_text=True)
        ma115 = next((p for p in ps if p.ref == "ma115"), None)
        # MA115 isn't in the partial offline archive — gap must be reported,
        # not silently rendered as empty text.
        if ma115 is not None:
            assert not any([ma115.text_pali, ma115.text_lzh,
                            ma115.text_san, ma115.text_pra])
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
        monkeypatch.setattr(
            "tools.research_sources._SCRATCH_DIR", tmp_path
        )
        path = scratch_init("test-slug")
        assert path.exists()
        text = path.read_text(encoding="utf-8")
        assert "Vicaya dossier — test-slug" in text
        for _, title, _ in _SCRATCH_PHASES:
            assert title in text

    def test_log_appends_entry_under_named_phase(self, tmp_path, monkeypatch):
        from tools.research_sources import scratch_init, scratch_log
        monkeypatch.setattr("tools.research_sources._SCRATCH_DIR", tmp_path)
        path = scratch_init("test-log")
        monkeypatch.setenv("VICAYA_SCRATCH", str(path))
        scratch_log("2", "search-canon", args=["pabhassara", "--limit", "1"],
                    summary="2 hits in AN", hits=2)
        text = path.read_text(encoding="utf-8")
        assert "search-canon" in text
        assert "pabhassara" in text
        # entry must be inside the phase 2 section, not at end of file
        canon_idx = text.index("## Phase 2 — Canon")
        next_section_idx = text.index("## Phase 2.5")
        assert canon_idx < text.index("search-canon") < next_section_idx

    def test_gate_refuses_when_prior_gate_missing(self, tmp_path, monkeypatch):
        from tools.research_sources import scratch_gate, scratch_init
        monkeypatch.setattr("tools.research_sources._SCRATCH_DIR", tmp_path)
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
        )
        monkeypatch.setattr("tools.research_sources._SCRATCH_DIR", tmp_path)
        path = scratch_init("test-gate-ok")
        monkeypatch.setenv("VICAYA_SCRATCH", str(path))
        for phase in ("0", "1", "2"):
            r = scratch_gate(phase)
            assert r["ok"], r
        text = path.read_text(encoding="utf-8")
        for phase in ("0", "1", "2"):
            assert f"PHASE {phase} EXIT GATE" in text
            for item in _PHASE_INDEX[phase][2]:
                assert item in text

    def test_verify_reports_missing_with_expected_evidence(self, tmp_path, monkeypatch):
        from tools.research_sources import scratch_gate, scratch_init, scratch_verify
        monkeypatch.setattr("tools.research_sources._SCRATCH_DIR", tmp_path)
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

    def test_resume_reports_last_gate_and_next_phase(self, tmp_path, monkeypatch):
        from tools.research_sources import scratch_gate, scratch_init, scratch_resume
        monkeypatch.setattr("tools.research_sources._SCRATCH_DIR", tmp_path)
        path = scratch_init("test-resume")
        monkeypatch.setenv("VICAYA_SCRATCH", str(path))
        for phase in ("0", "1", "2"):
            scratch_gate(phase)
        result = scratch_resume("test-resume")
        assert result["ok"]
        assert result["last_gate"]["phase"] == "2"
        assert result["next_phase"] == "2.5"

    def test_resume_slug_ignores_stale_active_state(self, tmp_path, monkeypatch):
        from tools.research_sources import _write_state, scratch_init, scratch_resume
        monkeypatch.setattr("tools.research_sources._SCRATCH_DIR", tmp_path)
        monkeypatch.delenv("VICAYA_SCRATCH", raising=False)
        stale_path = scratch_init("stale-run")
        selected_path = scratch_init("selected-run")
        _write_state(stale_path, "0")

        result = scratch_resume("selected-run")

        assert result["ok"]
        assert result["path"] == str(selected_path)

    def test_resume_updates_active_state_to_selected_scratch(self, tmp_path, monkeypatch):
        from tools.research_sources import (
            _read_state,
            _write_state,
            scratch_gate,
            scratch_init,
            scratch_resume,
        )
        monkeypatch.setattr("tools.research_sources._SCRATCH_DIR", tmp_path)
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

    def test_resume_thematic_run_reattaches_next_worked_phase(self, tmp_path, monkeypatch):
        from tools.research_sources import _read_state, scratch_gate, scratch_init, scratch_resume
        monkeypatch.setattr("tools.research_sources._SCRATCH_DIR", tmp_path)
        monkeypatch.delenv("VICAYA_SCRATCH", raising=False)
        path = scratch_init("thematic-resume", run_class="thematic")
        for phase in ("0", "1", "2"):
            assert scratch_gate(phase)["ok"]

        result = scratch_resume("thematic-resume")

        assert result["ok"]
        assert result["next_phase"] == "3"
        assert _read_state() == {"scratch": str(path), "phase": "3"}

    def test_phase_7_gate_refuses_when_vault_note_has_rejected(self, tmp_path, monkeypatch):
        from tools.research_sources import scratch_gate, scratch_init
        monkeypatch.setattr("tools.research_sources._SCRATCH_DIR", tmp_path)
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
        for phase in ("0", "1", "2", "2.5", "3", "3b", "4", "4b", "4c", "5", "6"):
            r = scratch_gate(phase)
            assert r["ok"], (phase, r)
        result = scratch_gate("7")
        assert result["ok"] is False
        assert "[REJECTED]" in result["reason"] or "REJECTED" in result["reason"]
        assert result["offending_lines"]

    def test_thematic_run_auto_skips_2_5_and_3b(self, tmp_path, monkeypatch):
        from tools.research_sources import _read_state, scratch_gate, scratch_init
        monkeypatch.setattr("tools.research_sources._SCRATCH_DIR", tmp_path)
        monkeypatch.delenv("VICAYA_SCRATCH", raising=False)
        path = scratch_init("test-thematic", run_class="thematic")
        for phase in ("0", "1", "2"):
            assert scratch_gate(phase)["ok"]
        # Gating phase 3 must succeed without the agent ever touching 2.5,
        # which would otherwise be a missing-prior-gate refusal.
        assert scratch_gate("3")["ok"]
        text = path.read_text(encoding="utf-8")
        assert "PHASE 2.5 EXIT GATE" in text
        assert "AUTO-SKIPPED (thematic run)" in text
        # Advance skips over the auto-skipped 3b → next worked phase is 4.
        assert _read_state()["phase"] == "4"
        # Gating 4 auto-skips 3b too.
        assert scratch_gate("4")["ok"]
        assert "PHASE 3b EXIT GATE" in path.read_text(encoding="utf-8")

    def test_sutta_anchored_run_still_requires_2_5(self, tmp_path, monkeypatch):
        from tools.research_sources import scratch_gate, scratch_init
        monkeypatch.setattr("tools.research_sources._SCRATCH_DIR", tmp_path)
        path = scratch_init("test-anchored")  # default class
        monkeypatch.setenv("VICAYA_SCRATCH", str(path))
        for phase in ("0", "1", "2"):
            scratch_gate(phase)
        # No auto-skip: gating 3 refuses because 2.5 is missing.
        assert scratch_gate("3")["ok"] is False

    def test_state_file_resolves_scratch_without_env(self, tmp_path, monkeypatch):
        from tools.research_sources import _scratch_path, scratch_init
        monkeypatch.setattr("tools.research_sources._SCRATCH_DIR", tmp_path)
        monkeypatch.delenv("VICAYA_SCRATCH", raising=False)
        path = scratch_init("test-state")
        # No env set — resolution falls through to the active-state file.
        assert _scratch_path() == path

    def test_gate_advances_active_phase_in_state(self, tmp_path, monkeypatch):
        from tools.research_sources import _read_state, scratch_gate, scratch_init
        monkeypatch.setattr("tools.research_sources._SCRATCH_DIR", tmp_path)
        monkeypatch.delenv("VICAYA_SCRATCH", raising=False)
        scratch_init("test-advance")
        assert _read_state()["phase"] == "0"
        scratch_gate("0")
        assert _read_state()["phase"] == "1"

    def test_autolog_uses_env_scratch_over_active_state(self, tmp_path, monkeypatch):
        from tools.research_sources import _maybe_autolog, _write_state, scratch_init
        monkeypatch.setattr("tools.research_sources._SCRATCH_DIR", tmp_path)
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
        monkeypatch.setattr("tools.research_sources._SCRATCH_DIR", tmp_path)
        monkeypatch.delenv("VICAYA_SCRATCH", raising=False)
        monkeypatch.delenv("VICAYA_PHASE", raising=False)
        path = scratch_init("autolog-active")

        _maybe_autolog("search-vault", ["dukkha"], [])

        assert "search-vault" in path.read_text(encoding="utf-8")


def _build_calibre_metadata_db(library: Path) -> Path:
    """Create a minimal Calibre-shaped metadata.db for hermetic tests."""
    import sqlite3
    db = library / "metadata.db"
    con = sqlite3.connect(db)
    con.executescript(
        """
        CREATE TABLE books (id INTEGER PRIMARY KEY, title TEXT);
        CREATE TABLE authors (id INTEGER PRIMARY KEY, name TEXT);
        CREATE TABLE books_authors_link (book INTEGER, author INTEGER);
        CREATE TABLE tags (id INTEGER PRIMARY KEY, name TEXT);
        CREATE TABLE books_tags_link (book INTEGER, tag INTEGER);
        CREATE TABLE comments (book INTEGER, text TEXT);
        """
    )
    con.executemany("INSERT INTO books (id, title) VALUES (?, ?)", [
        (1, "The Buddha's Teaching"),
        (2, "Sanskrit Grammar"),
    ])
    con.executemany("INSERT INTO authors (id, name) VALUES (?, ?)", [(1, "Bhikkhu Bodhi"), (2, "Whitney")])
    con.executemany("INSERT INTO books_authors_link (book, author) VALUES (?, ?)", [(1, 1), (2, 2)])
    con.executemany("INSERT INTO tags (id, name) VALUES (?, ?)", [(1, "Buddhism"), (2, "Sanskrit")])
    con.executemany("INSERT INTO books_tags_link (book, tag) VALUES (?, ?)", [(1, 1), (2, 2)])
    con.executemany("INSERT INTO comments (book, text) VALUES (?, ?)", [
        (1, "A study of dukkha and the path."),
        (2, "Classical Sanskrit reference."),
    ])
    con.commit()
    con.close()
    return db


class TestCalibreReadOnlySqlite:
    """Metadata search and the preflight read metadata.db directly, never locking."""

    def test_metadata_search_reads_sqlite_readonly(self, monkeypatch, tmp_path):
        import tools.research_sources as rs
        _build_calibre_metadata_db(tmp_path)
        monkeypatch.setattr(rs, "_run_calibre", lambda *a, **k: pytest.fail("used calibredb"))

        hits = rs._calibre_metadata_search("Buddha", None, tmp_path, limit=5)

        assert len(hits) == 1
        h = hits[0]
        assert isinstance(h, rs.CalibreHit)
        assert h.title == "The Buddha's Teaching"
        assert h.authors == "Bhikkhu Bodhi"
        assert h.tags == ["Buddhism"]
        assert "dukkha" in h.snippet

    def test_metadata_search_matches_author_and_comments(self, monkeypatch, tmp_path):
        import tools.research_sources as rs
        _build_calibre_metadata_db(tmp_path)
        monkeypatch.setattr(rs, "_run_calibre", lambda *a, **k: pytest.fail("used calibredb"))

        assert [h.book_id for h in rs._calibre_metadata_search("Whitney", None, tmp_path, 5)] == [2]
        assert [h.book_id for h in rs._calibre_metadata_search("path", None, tmp_path, 5)] == [1]

    def test_metadata_search_filters_by_tag(self, monkeypatch, tmp_path):
        import tools.research_sources as rs
        _build_calibre_metadata_db(tmp_path)
        monkeypatch.setattr(rs, "_run_calibre", lambda *a, **k: pytest.fail("used calibredb"))

        hits = rs._calibre_metadata_search("", ["Sanskrit"], tmp_path, limit=5)
        assert [h.book_id for h in hits] == [2]

    def test_metadata_search_falls_back_to_cli_on_schema_error(self, monkeypatch, tmp_path):
        import tools.research_sources as rs
        (tmp_path / "metadata.db").write_text("not a database", encoding="utf-8")
        called = {}

        def _cli(query, tags, library, limit, timeout=60):
            called["hit"] = True
            return [rs.CalibreHit(book_id=9, title="cli", authors="", tags=[])]

        monkeypatch.setattr(rs, "_calibre_metadata_search_cli", _cli)
        hits = rs._calibre_metadata_search("x", None, tmp_path, limit=5)
        assert called.get("hit") and hits[0].book_id == 9


class TestCalibreCheckHonesty:
    """calibre-check must use a fast, lock-free read-only SQLite probe."""

    def test_available_when_metadata_db_readable(self, monkeypatch, tmp_path):
        import tools.research_sources as rs
        _build_calibre_metadata_db(tmp_path)
        monkeypatch.setattr(rs, "DEFAULT_CALIBRE_LIBRARY", tmp_path)
        monkeypatch.setattr(rs, "_run_calibre", lambda *a, **k: pytest.fail("used calibredb lock"))
        monkeypatch.setattr(rs, "search_calibre", lambda *a, **k: pytest.fail("used FTS search"))
        ok, msg = rs.calibre_library_available()
        assert ok and msg == "ok"

    def test_unavailable_when_metadata_db_missing(self, monkeypatch, tmp_path):
        import tools.research_sources as rs
        monkeypatch.setattr(rs, "DEFAULT_CALIBRE_LIBRARY", tmp_path)
        monkeypatch.setattr(rs, "_run_calibre", lambda *a, **k: pytest.fail("used calibredb lock"))
        ok, msg = rs.calibre_library_available()
        assert ok is False
        assert "metadata.db not found" in msg

    def test_unavailable_when_metadata_db_corrupt(self, monkeypatch, tmp_path):
        import tools.research_sources as rs
        (tmp_path / "metadata.db").write_text("not a database", encoding="utf-8")
        monkeypatch.setattr(rs, "DEFAULT_CALIBRE_LIBRARY", tmp_path)
        monkeypatch.setattr(rs, "_run_calibre", lambda *a, **k: pytest.fail("used calibredb lock"))
        ok, msg = rs.calibre_library_available()
        assert ok is False


class TestCalibreFtsFallback:
    def test_search_falls_back_to_metadata_when_fts_times_out(self, monkeypatch, tmp_path, capsys):
        import tools.research_sources as rs

        metadata_hits = [
            rs.CalibreHit(
                book_id=42,
                title="Metadata result",
                authors="Author",
                tags=["Buddhism"],
                location="42",
                snippet="metadata comments are not FTS snippets",
            )
        ]
        seen = {}

        def _timeout(query, tags, library, limit, *, timeout):
            seen["fts"] = (query, tags, library, limit, timeout)
            raise subprocess.TimeoutExpired(["calibredb", "fts_search"], timeout)

        def _metadata(query, tags, library, limit, *, timeout):
            seen["metadata"] = (query, tags, library, limit, timeout)
            return metadata_hits

        monkeypatch.setattr(rs, "DEFAULT_CALIBRE_LIBRARY", tmp_path)
        monkeypatch.setattr(rs, "_calibre_fts_available", lambda library: True)
        monkeypatch.setattr(rs, "_calibre_fts_search", _timeout)
        monkeypatch.setattr(rs, "_calibre_metadata_search", _metadata)

        hits = rs.search_calibre("dhamma", tags=["Buddhism"], limit=5)

        assert hits == [
            rs.CalibreHit(
                book_id=42,
                title="Metadata result",
                authors="Author",
                tags=["Buddhism"],
                location="42",
                snippet="",
            )
        ]
        assert seen["fts"] == ("dhamma", ["Buddhism"], tmp_path, 5, 20)
        assert seen["metadata"] == ("dhamma", ["Buddhism"], tmp_path, 5, 60)
        assert "FTS timed out" in capsys.readouterr().err

    def test_search_keeps_calibre_unavailable_errors(self, monkeypatch, tmp_path):
        import tools.research_sources as rs

        def _locked(*a, **k):
            raise rs.CalibreUnavailable("database is locked")

        monkeypatch.setattr(rs, "DEFAULT_CALIBRE_LIBRARY", tmp_path)
        monkeypatch.setattr(rs, "_calibre_fts_available", lambda library: True)
        monkeypatch.setattr(rs, "_calibre_fts_search", _locked)
        monkeypatch.setattr(
            rs,
            "_calibre_metadata_search",
            lambda *a, **k: pytest.fail("fell back on a lock error"),
        )

        with pytest.raises(rs.CalibreUnavailable, match="locked"):
            rs.search_calibre("dhamma")


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
