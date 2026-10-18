"""Every helper subcommand accepts the flags the skill's call template adds (#132)."""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
ENV = {"VICAYA_SCRATCH": "/dev/null/none", "PATH": "/usr/bin:/bin"}


def _run(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "tools/research_sources.py", *args],
        capture_output=True,
        text=True,
        cwd=ROOT,
        env=ENV,
        stdin=subprocess.DEVNULL,
    )


def _subcommands() -> list[str]:
    out = _run("--help").stdout
    match = re.search(r"\{([a-z0-9,-]+)\}", out)
    assert match, out
    return match.group(1).split(",")


def test_subcommand_list_is_found():
    assert len(_subcommands()) > 30


@pytest.mark.parametrize("command", _subcommands())
def test_help_lists_quiet(command):
    help_text = _run(command, "--help").stdout
    assert "--quiet" in help_text, f"{command} does not accept --quiet"


@pytest.mark.parametrize(
    "command",
    ["scratch-which", "scratch-resume", "env"],
)
def test_quiet_is_not_an_argparse_error(command):
    # Parsing is what failed before: argparse exits 2 on an unknown flag.
    extra = ["x"] if command == "scratch-resume" else []
    result = _run(command, *extra, "--quiet")
    assert "unrecognized arguments" not in result.stderr


def test_check_citation_shape_accepts_slug(tmp_path):
    note = tmp_path / "n.md"
    note.write_text("nothing to flag\n", encoding="utf-8")
    result = _run("check-citation-shape", str(note), "--slug", "whatever", "--quiet")
    assert "unrecognized arguments" not in result.stderr
    assert result.returncode == 0
