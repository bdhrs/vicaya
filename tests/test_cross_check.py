"""Unit tests for `cross_check`. Network calls are monkey-patched."""

from __future__ import annotations

import io
import json
import sys
import urllib.error
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tools import research_sources as rs  # noqa: E402


class _FakeResp:
    def __init__(self, body: bytes):
        self._body = body

    def read(self):
        return self._body

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


# ---------- _load_openrouter_key ----------


def test_key_prefers_env(monkeypatch, tmp_path):
    monkeypatch.setenv("OPENROUTER_API_KEY", "env-key")
    auth = tmp_path / "auth.json"
    auth.write_text(json.dumps({"openrouter": {"key": "file-key"}}))
    monkeypatch.setattr(rs, "_OPENCODE_AUTH_PATH", auth)
    assert rs._load_openrouter_key() == "env-key"


def test_key_falls_back_to_auth_json(monkeypatch, tmp_path):
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    auth = tmp_path / "auth.json"
    auth.write_text(json.dumps({"openrouter": {"key": "file-key"}}))
    monkeypatch.setattr(rs, "_OPENCODE_AUTH_PATH", auth)
    assert rs._load_openrouter_key() == "file-key"


def test_key_returns_none_when_unset(monkeypatch, tmp_path):
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    monkeypatch.setattr(rs, "_OPENCODE_AUTH_PATH", tmp_path / "missing.json")
    assert rs._load_openrouter_key() is None


# ---------- _load_openrouter_models ----------


def test_models_reads_json(monkeypatch, tmp_path):
    f = tmp_path / "or.json"
    f.write_text(json.dumps({"models": ["a/b:free", "c/d:free"]}))
    monkeypatch.setattr(rs, "_OPENROUTER_MODELS_PATH", f)
    assert rs._load_openrouter_models() == ["a/b:free", "c/d:free"]


def test_models_truncates_to_api_cap(monkeypatch, tmp_path):
    f = tmp_path / "or.json"
    overlong = [f"m{i}/x:free" for i in range(rs._OPENROUTER_MAX_MODELS + 2)]
    f.write_text(json.dumps({"models": overlong}))
    monkeypatch.setattr(rs, "_OPENROUTER_MODELS_PATH", f)
    out = rs._load_openrouter_models()
    assert len(out) == rs._OPENROUTER_MAX_MODELS
    assert out == overlong[:rs._OPENROUTER_MAX_MODELS]


def test_models_returns_empty_when_missing(monkeypatch, tmp_path):
    monkeypatch.setattr(rs, "_OPENROUTER_MODELS_PATH", tmp_path / "nope.json")
    assert rs._load_openrouter_models() == []


def test_models_returns_empty_on_bad_json(monkeypatch, tmp_path):
    f = tmp_path / "bad.json"
    f.write_text("{ not valid")
    monkeypatch.setattr(rs, "_OPENROUTER_MODELS_PATH", f)
    assert rs._load_openrouter_models() == []


def test_models_returns_empty_on_wrong_shape(monkeypatch, tmp_path):
    f = tmp_path / "shape.json"
    f.write_text(json.dumps({"models": [1, 2, 3]}))
    monkeypatch.setattr(rs, "_OPENROUTER_MODELS_PATH", f)
    assert rs._load_openrouter_models() == []


# ---------- cross_check ----------


def test_cross_check_returns_model_text(monkeypatch):
    monkeypatch.setattr(rs, "_load_openrouter_key", lambda: "k")
    monkeypatch.setattr(rs, "_load_openrouter_models", lambda: ["a/b:free"])
    payload = {"choices": [{"message": {"content": "critique"}}]}
    monkeypatch.setattr(
        "urllib.request.urlopen",
        lambda req, timeout: _FakeResp(json.dumps(payload).encode()),
    )
    assert rs.cross_check("hi") == "critique"


def test_cross_check_self_review_when_no_key(monkeypatch):
    monkeypatch.setattr(rs, "_load_openrouter_key", lambda: None)
    monkeypatch.setattr(rs, "_load_openrouter_models", lambda: ["a/b:free"])
    assert rs.cross_check("hi").startswith("# SELF_REVIEW:")


def test_cross_check_self_review_when_no_models(monkeypatch):
    monkeypatch.setattr(rs, "_load_openrouter_key", lambda: "k")
    monkeypatch.setattr(rs, "_load_openrouter_models", lambda: [])
    assert rs.cross_check("hi").startswith("# SELF_REVIEW:")


def test_cross_check_self_review_on_http_error(monkeypatch):
    monkeypatch.setattr(rs, "_load_openrouter_key", lambda: "k")
    monkeypatch.setattr(rs, "_load_openrouter_models", lambda: ["a/b:free"])

    def boom(req, timeout):
        raise urllib.error.HTTPError(
            "http://x", 429, "rate limit", {}, io.BytesIO(b"")
        )

    monkeypatch.setattr("urllib.request.urlopen", boom)
    assert rs.cross_check("hi").startswith("# SELF_REVIEW:")


def test_cross_check_self_review_on_empty_content(monkeypatch):
    monkeypatch.setattr(rs, "_load_openrouter_key", lambda: "k")
    monkeypatch.setattr(rs, "_load_openrouter_models", lambda: ["a/b:free"])
    payload = {"choices": [{"message": {"content": "   "}}]}
    monkeypatch.setattr(
        "urllib.request.urlopen",
        lambda req, timeout: _FakeResp(json.dumps(payload).encode()),
    )
    assert rs.cross_check("hi").startswith("# SELF_REVIEW:")


def test_self_review_lists_all_checklist_items(monkeypatch):
    monkeypatch.setattr(rs, "_load_openrouter_key", lambda: None)
    out = rs.cross_check("hi")
    for label in ("Perspective coverage", "Tier integrity",
                  "Citation quality", "Internal consistency", "Overreach"):
        assert label in out
