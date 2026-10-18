"""Gates and helper calls in a parallel gather wave (#133, #134, #135)."""

from __future__ import annotations

import pytest

from tools import scratch
from tools.research_sources import (
    scratch_gate,
    scratch_init,
    scratch_log,
    scratch_set_note,
)


@pytest.fixture
def run(tmp_path, monkeypatch):
    monkeypatch.setattr("tools.scratch._SCRATCH_DIR", tmp_path)
    path = scratch_init(
        "wave",
        question_polished="q",
        scope_assumptions="s",
        ambiguity="clear",
    )
    monkeypatch.setenv("VICAYA_SCRATCH", str(path))
    scratch_log("1", "note", summary="angle triage")
    assert scratch_gate("1")["ok"]
    return path


def test_a_later_gather_phase_can_gate_before_its_siblings(run):
    # #133: a 4c agent that finishes first used to be refused until Phase 4
    # was gated, and retried 14 times.
    scratch_log("4c", "wisdomlib", summary="saddha")
    assert scratch_gate("4c")["ok"]
    scratch_log("4b", "youtube", summary="talk")
    assert scratch_gate("4b")["ok"]


def test_synthesis_still_needs_every_gather_gate(run):
    scratch_log("4c", "wisdomlib", summary="saddha")
    scratch_gate("4c")
    refused = scratch_gate("5")
    assert refused["ok"] is False
    assert refused["missing_phase"] == "2"


def test_a_gather_phase_still_needs_the_briefing_gate(tmp_path, monkeypatch):
    monkeypatch.setattr("tools.scratch._SCRATCH_DIR", tmp_path)
    path = scratch_init(
        "early", question_polished="q", scope_assumptions="s", ambiguity="clear"
    )
    monkeypatch.setenv("VICAYA_SCRATCH", str(path))
    scratch_log("4c", "wisdomlib", summary="saddha")
    refused = scratch_gate("4c")
    assert refused["ok"] is False and refused["missing_phase"] == "1"


def test_a_gather_gate_still_needs_logged_evidence(run):
    refused = scratch_gate("4c")
    assert refused["ok"] is False and refused["reason"] == "no logged evidence"
    # #135: the refusal tells a batched caller to run the gate again alone.
    assert "run the gate again on its own" in refused["message"]


def test_phase_4a_is_named_as_phase_4_in_results(run):
    # #134
    scratch_log("4a", "web", summary="a page")
    result = scratch_gate("4a")
    assert result["ok"] and result["phase"] == "4"
    assert "stored as Phase 4" in result["alias"]


def test_a_pdf_that_does_not_exist_yet_is_refused(run, tmp_path):
    # #135: scratch-set-note ran before the PDF step had finished.
    note = tmp_path / "note.md"
    note.write_text("# n\n", encoding="utf-8")
    refused = scratch_set_note(str(note), pdf=str(tmp_path / "later.pdf"))
    assert refused["ok"] is False and "PDF not found" in refused["message"]
    assert scratch_set_note(str(note), pdf="skipped")["ok"]
    (tmp_path / "later.pdf").write_bytes(b"%PDF-1.4")
    assert scratch_set_note(str(note), pdf=str(tmp_path / "later.pdf"))["ok"]


def test_parallel_gather_set_matches_the_phase_table():
    assert scratch._PARALLEL_GATHER_PHASES <= set(scratch._PHASE_INDEX)


def test_resume_points_at_the_first_missing_gate_not_the_one_after_the_highest(run):
    scratch_log("4c", "wisdomlib", summary="saddha")
    scratch_gate("4c")
    assert scratch.scratch_resume(scratch=run)["next_phase"] == "2"
