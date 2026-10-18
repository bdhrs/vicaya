"""Tests for the all-or-nothing note editor (issue #130)."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from tools.note_edits import apply_edits

ROOT = Path(__file__).resolve().parents[1]


def _note(tmp_path: Path, text: str) -> Path:
    path = tmp_path / "draft.md"
    path.write_bytes(text.encode("utf-8"))
    return path


def test_applies_every_edit_in_order(tmp_path):
    path = _note(tmp_path, "alpha beta\ngamma\n")
    result = apply_edits(
        path, [{"old": "alpha", "new": "ALPHA"}, {"old": "ALPHA beta", "new": "x"}]
    )
    assert result["ok"] and result["written"]
    assert path.read_text(encoding="utf-8") == "x\ngamma\n"


def test_one_missing_target_writes_nothing(tmp_path):
    # The silent no-op: one character differs, the earlier edit must not land.
    text = "the samugghāta — MN 64\n"
    path = _note(tmp_path, text)
    result = apply_edits(
        path,
        [
            {"old": "MN 64", "new": "MN 63"},
            {"old": "the samugghāta - MN 64", "new": "gone"},
        ],
    )
    assert not result["ok"] and not result["written"]
    assert [e["status"] for e in result["edits"]] == ["applied", "not-found"]
    assert path.read_bytes() == text.encode("utf-8")


def test_ambiguous_target_is_refused_unless_all(tmp_path):
    path = _note(tmp_path, "cat cat\n")
    refused = apply_edits(path, [{"old": "cat", "new": "dog"}])
    assert refused["edits"][0]["status"] == "ambiguous"
    assert path.read_text(encoding="utf-8") == "cat cat\n"
    done = apply_edits(path, [{"old": "cat", "new": "dog", "all": True}])
    assert done["ok"] and path.read_text(encoding="utf-8") == "dog dog\n"


def test_reports_leftover_copies_of_the_old_text(tmp_path):
    path = _note(tmp_path, "ab ab\n")
    clean = apply_edits(path, [{"old": "ab", "new": "x", "all": True}])
    assert clean["edits"][0]["old_remaining"] == 0
    path = _note(tmp_path, "ab\n")
    grown = apply_edits(path, [{"old": "ab", "new": "abab"}])
    assert grown["edits"][0]["old_remaining"] == 2


def test_line_endings_and_apostrophes_are_preserved(tmp_path):
    path = _note(tmp_path, "it's one\r\nit's two\r\n")
    result = apply_edits(path, [{"old": "one", "new": "1"}])
    assert result["ok"]
    assert path.read_bytes() == "it's 1\r\nit's two\r\n".encode("utf-8")


def test_bad_input_is_an_error_not_a_crash(tmp_path):
    path = _note(tmp_path, "x\n")
    assert not apply_edits(path, [])["ok"]
    assert not apply_edits(path, [{"old": "", "new": "y"}])["ok"]
    assert not apply_edits(tmp_path / "missing.md", [{"old": "a", "new": "b"}])["ok"]


def test_cli_exits_nonzero_and_leaves_the_file(tmp_path):
    path = _note(tmp_path, "keep me\n")
    run = subprocess.run(
        [sys.executable, "tools/research_sources.py", "apply-edits", str(path)],
        input=json.dumps([{"old": "absent", "new": "x"}]),
        capture_output=True,
        text=True,
        cwd=ROOT,
        env={"VICAYA_SCRATCH": "/dev/null/none", "PATH": "/usr/bin:/bin"},
    )
    assert run.returncode == 1
    assert json.loads(run.stdout)["ok"] is False
    assert path.read_text(encoding="utf-8") == "keep me\n"
