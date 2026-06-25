"""Unit tests for `cross_check`. Subprocess calls are monkey-patched."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tools import research_sources as rs  # noqa: E402


# ---------- _parse_cross_check_chain ----------


def test_parse_chain_parses_two_entries(monkeypatch):
    monkeypatch.setenv(
        "VICAYA_CROSS_CHECK_CHAIN",
        "opencode:openrouter/deepseek/v4 | agy:Gemini 3.5 Flash",
    )
    assert rs._parse_cross_check_chain() == [
        ("opencode", "openrouter/deepseek/v4"),
        ("agy", "Gemini 3.5 Flash"),
    ]


def test_parse_chain_returns_empty_for_unset_env(monkeypatch):
    monkeypatch.delenv("VICAYA_CROSS_CHECK_CHAIN", raising=False)
    assert rs._parse_cross_check_chain() == []


def test_parse_chain_returns_empty_for_blank_env(monkeypatch):
    monkeypatch.setenv("VICAYA_CROSS_CHECK_CHAIN", "")
    assert rs._parse_cross_check_chain() == []


def test_parse_chain_skips_malformed_no_colon(monkeypatch):
    monkeypatch.setenv("VICAYA_CROSS_CHECK_CHAIN", "opencode|agy:model")
    assert rs._parse_cross_check_chain() == [("agy", "model")]


def test_parse_chain_skips_malformed_empty_app(monkeypatch):
    monkeypatch.setenv("VICAYA_CROSS_CHECK_CHAIN", ":model|agy:model")
    assert rs._parse_cross_check_chain() == [("agy", "model")]


def test_parse_chain_skips_malformed_empty_model(monkeypatch):
    monkeypatch.setenv("VICAYA_CROSS_CHECK_CHAIN", "opencode:|agy:model")
    assert rs._parse_cross_check_chain() == [("agy", "model")]


def test_parse_chain_trims_whitespace(monkeypatch):
    monkeypatch.setenv(
        "VICAYA_CROSS_CHECK_CHAIN", " opencode : deepseek/v4 | agy : Gemini 3.5 "
    )
    assert rs._parse_cross_check_chain() == [
        ("opencode", "deepseek/v4"),
        ("agy", "Gemini 3.5"),
    ]


# ---------- cross_check: chain unset / empty ----------


def test_cross_check_self_review_when_chain_unset(monkeypatch):
    monkeypatch.delenv("VICAYA_CROSS_CHECK_CHAIN", raising=False)
    assert rs.cross_check("hi").startswith("# SELF_REVIEW:")


def test_cross_check_self_review_when_chain_blank(monkeypatch):
    monkeypatch.setenv("VICAYA_CROSS_CHECK_CHAIN", "")
    assert rs.cross_check("hi").startswith("# SELF_REVIEW:")


# ---------- cross_check: single working entry ----------


def test_cross_check_opencode_success(monkeypatch):
    monkeypatch.setenv(
        "VICAYA_CROSS_CHECK_CHAIN", "opencode:deepseek/deepseek-v4-flash"
    )
    monkeypatch.setattr(rs, "_run_opencode", lambda p, m, t: "hello")
    assert rs.cross_check("hi") == "hello"


def test_cross_check_agy_success(monkeypatch):
    monkeypatch.setenv("VICAYA_CROSS_CHECK_CHAIN", "agy:Gemini 3.5 Flash (High)")
    monkeypatch.setattr(rs, "_run_agy", lambda p, m, t: "hello")
    assert rs.cross_check("hi") == "hello"


# ---------- cross_check: fallthrough ----------


def test_cross_check_first_fails_second_succeeds(monkeypatch):
    monkeypatch.setenv(
        "VICAYA_CROSS_CHECK_CHAIN",
        "opencode:bad|agy:good",
    )
    monkeypatch.setattr(rs, "_run_opencode", lambda p, m, t: None)
    monkeypatch.setattr(rs, "_run_agy", lambda p, m, t: "second wins")
    assert rs.cross_check("hi") == "second wins"


# ---------- cross_check: all fail ----------


def test_cross_check_all_fail_returns_self_review(monkeypatch):
    monkeypatch.setenv(
        "VICAYA_CROSS_CHECK_CHAIN",
        "opencode:bad|agy:also-bad",
    )
    monkeypatch.setattr(rs, "_run_opencode", lambda p, m, t: None)
    monkeypatch.setattr(rs, "_run_agy", lambda p, m, t: None)
    assert rs.cross_check("hi").startswith("# SELF_REVIEW:")


# ---------- cross_check: unknown app ----------


def test_cross_check_unknown_app_treated_as_failure(monkeypatch):
    monkeypatch.setenv("VICAYA_CROSS_CHECK_CHAIN", "unknown:model")
    assert rs.cross_check("hi").startswith("# SELF_REVIEW:")


def test_cross_check_unknown_app_falls_through_to_valid(monkeypatch):
    monkeypatch.setenv(
        "VICAYA_CROSS_CHECK_CHAIN",
        "unknown:model|opencode:good",
    )
    monkeypatch.setattr(rs, "_run_opencode", lambda p, m, t: "opencode text")
    assert rs.cross_check("hi") == "opencode text"


# ---------- sentinel checklist matches the external-review rubric ----------


def test_self_review_lists_all_checklist_items(monkeypatch):
    monkeypatch.delenv("VICAYA_CROSS_CHECK_CHAIN", raising=False)
    out = rs.cross_check("hi")
    for label in (
        "Perspective coverage",
        "Tier integrity",
        "Disputed consensus",
        "Factual accuracy",
        "General",
    ):
        assert label in out
