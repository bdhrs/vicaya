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
    monkeypatch.setattr(rs, "_run_opencode", lambda p, m, t: ("hello", ""))
    assert rs.cross_check("hi") == "hello"


def test_cross_check_agy_success(monkeypatch):
    monkeypatch.setenv("VICAYA_CROSS_CHECK_CHAIN", "agy:Gemini 3.5 Flash (High)")
    monkeypatch.setattr(rs, "_run_agy", lambda p, m, t: ("hello", ""))
    assert rs.cross_check("hi") == "hello"


def test_cross_check_pi_success(monkeypatch):
    monkeypatch.setenv("VICAYA_CROSS_CHECK_CHAIN", "pi:zai/glm-5.3")
    monkeypatch.setattr(rs, "_run_pi", lambda p, m, t: ("hello", ""))
    assert rs.cross_check("hi") == "hello"


def test_cross_check_pi_model_keeps_slash_after_colon_split(monkeypatch):
    """`pi:zai/glm-5.3` must split on the FIRST colon only — the model keeps
    its provider/id slash (that's the whole point of the pi entry form)."""
    seen = {}

    def fake_pi(prompt, model, timeout):
        seen["model"] = model
        return ("ok", "")

    monkeypatch.setenv("VICAYA_CROSS_CHECK_CHAIN", "pi:zai/glm-5.3")
    monkeypatch.setattr(rs, "_run_pi", fake_pi)
    assert rs.cross_check("hi") == "ok"
    assert seen["model"] == "zai/glm-5.3"


def test_cross_check_pi_thinking_suffix_passes_through(monkeypatch):
    """`pi:zai/glm-5.3:off` — pi's own `--model` syntax carries an optional
    `:thinking` level. The chain parser must not eat it: without a pinned
    level the entry inherits the machine's defaultThinkingLevel (max on
    this machine = 12–17 min per review), so entries pin one explicitly."""
    seen = {}

    def fake_pi(prompt, model, timeout):
        seen["model"] = model
        return ("ok", "")

    monkeypatch.setenv("VICAYA_CROSS_CHECK_CHAIN", "pi:zai/glm-5.3:off")
    monkeypatch.setattr(rs, "_run_pi", fake_pi)
    assert rs.cross_check("hi") == "ok"
    assert seen["model"] == "zai/glm-5.3:off"


def test_run_pi_command_shape(monkeypatch):
    """The pi builder must pin --no-tools/--no-session (a pure model call,
    no agent machinery) and pass the prompt as the trailing argv element."""
    seen = {}

    def fake_status(cmd, timeout):
        seen["cmd"] = cmd
        return ("ok", "")

    monkeypatch.setattr(rs, "_run_chain_subprocess_status", fake_status)
    text, reason = rs._run_pi("prompt text", "zai/glm-5.3", 10)
    assert (text, reason) == ("ok", "")
    cmd = seen["cmd"]
    assert cmd[0] == "pi"
    assert "-p" in cmd
    assert cmd[cmd.index("--model") + 1] == "zai/glm-5.3"
    for flag in (
        "--no-tools",
        "--no-session",
        "--no-extensions",
        "--no-skills",
        "--offline",
        "--no-context-files",
    ):
        assert flag in cmd
    assert cmd[-1] == "prompt text"


# ---------- cross_check: fallthrough ----------


def test_cross_check_first_fails_second_succeeds(monkeypatch):
    monkeypatch.setenv(
        "VICAYA_CROSS_CHECK_CHAIN",
        "opencode:bad|agy:good",
    )
    monkeypatch.setattr(
        rs, "_run_opencode", lambda p, m, t: (None, "timed out after 180s")
    )
    monkeypatch.setattr(rs, "_run_agy", lambda p, m, t: ("second wins", ""))
    assert rs.cross_check("hi") == "second wins"


def test_cross_check_pi_falls_through_to_next_entry(monkeypatch):
    """Empty output with exit 0 is a real pi failure mode (observed in a
    live probe) — it must fall through, not return the empty string."""
    monkeypatch.setenv("VICAYA_CROSS_CHECK_CHAIN", "pi:zai/glm-5.3|opencode:good")
    monkeypatch.setattr(rs, "_run_pi", lambda p, m, t: (None, "no output"))
    monkeypatch.setattr(rs, "_run_opencode", lambda p, m, t: ("fallback", ""))
    assert rs.cross_check("hi") == "fallback"


# ---------- cross_check: all fail ----------


def test_cross_check_all_fail_returns_self_review(monkeypatch):
    monkeypatch.setenv(
        "VICAYA_CROSS_CHECK_CHAIN",
        "opencode:bad|agy:also-bad",
    )
    monkeypatch.setattr(
        rs, "_run_opencode", lambda p, m, t: (None, "timed out after 180s")
    )
    monkeypatch.setattr(rs, "_run_agy", lambda p, m, t: (None, "timed out after 180s"))
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
    monkeypatch.setattr(rs, "_run_opencode", lambda p, m, t: ("opencode text", ""))
    assert rs.cross_check("hi") == "opencode text"


# ---------- _run_chain_subprocess: hard wall-clock ceiling ----------


def test_chain_subprocess_returns_stdout():
    assert rs._run_chain_subprocess(["bash", "-c", "echo hello"], timeout=10) == "hello"


def test_chain_subprocess_none_on_nonzero_exit():
    assert rs._run_chain_subprocess(["bash", "-c", "exit 3"], timeout=10) is None


def test_chain_subprocess_none_on_missing_binary():
    assert rs._run_chain_subprocess(["definitely-not-a-binary-xyz"], timeout=10) is None


def test_chain_subprocess_kills_process_group_on_timeout():
    # Regression for issue #71: a grandchild inheriting the stdout pipe kept
    # the post-kill drain blocked long past the declared timeout (observed
    # live: 5m+ past --timeout 260). The backgrounded sleep here plays the
    # grandchild; the group kill must take it down within the timeout plus a
    # small grace, not wait out its 30s.
    import time

    start = time.monotonic()
    result = rs._run_chain_subprocess(["bash", "-c", "sleep 30 & sleep 30"], timeout=1)
    elapsed = time.monotonic() - start
    assert result is None
    assert elapsed < 10


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


# ---------- issue #103: the sentinel names the failure ----------


def test_sentinel_names_each_failed_entry_and_reason(monkeypatch):
    """Issue #103: a silent sentinel cannot be acted on — it must say who
    failed and why (timeout vs exit vs missing binary)."""
    monkeypatch.setenv("VICAYA_CROSS_CHECK_CHAIN", "opencode:m1|agy:m2")
    monkeypatch.setattr(
        rs, "_run_opencode", lambda p, m, t: (None, "timed out after 180s")
    )
    monkeypatch.setattr(
        rs, "_run_agy", lambda p, m, t: (None, "exited 1: auth token expired")
    )
    out = rs.cross_check("hi")
    assert out.startswith("# SELF_REVIEW:")
    assert "opencode:m1 — timed out after 180s" in out
    assert "agy:m2 — exited 1: auth token expired" in out
    assert "retry once" in out


def test_sentinel_distinguishes_unconfigured_chain(monkeypatch):
    """Issue #103: 'chain not set' and 'chain configured but failing' are
    different diagnoses — the sentinel header must separate them."""
    monkeypatch.delenv("VICAYA_CROSS_CHECK_CHAIN", raising=False)
    out = rs.cross_check("hi")
    assert "VICAYA_CROSS_CHECK_CHAIN is not set" in out
    assert "failed" not in out.split("Run the Phase 6 checklist")[0]


def test_sentinel_names_unknown_app_entries(monkeypatch):
    monkeypatch.setenv("VICAYA_CROSS_CHECK_CHAIN", "mystery:m|agy:ok")
    monkeypatch.setattr(rs, "_run_agy", lambda p, m, t: (None, "no output"))
    out = rs.cross_check("hi")
    assert "mystery:m — unknown app (supported: opencode, agy, pi)" in out
    assert "agy:ok — no output" in out


def test_chain_subprocess_status_reasons_cover_failure_modes():
    """Direct engine probes: each failure mode yields a distinct reason."""
    ok, reason = rs._run_chain_subprocess_status(["bash", "-c", "echo hi"], timeout=10)
    assert (ok, reason) == ("hi", "")
    _, reason = rs._run_chain_subprocess_status(["bash", "-c", "exit 3"], timeout=10)
    assert reason.startswith("exited 3")
    _, reason = rs._run_chain_subprocess_status(
        ["definitely-not-a-binary-xyz"], timeout=10
    )
    assert reason.startswith("could not start")
    _, reason = rs._run_chain_subprocess_status(["bash", "-c", "sleep 5"], timeout=1)
    assert reason == "timed out after 1s"
    _, reason = rs._run_chain_subprocess_status(["bash", "-c", "true"], timeout=10)
    assert reason == "no output"


# ---------- issue #103: preflight ----------


def test_preflight_reports_ok_entry(monkeypatch):
    monkeypatch.setenv("VICAYA_CROSS_CHECK_CHAIN", "opencode:m1")
    monkeypatch.setattr(rs, "_run_opencode", lambda p, m, t: ("OK", ""))
    result = rs.cross_check_preflight(timeout=5)
    assert result["ok"] is True
    assert result["chain_configured"] is True
    assert result["entries"][0]["app"] == "opencode"
    assert result["entries"][0]["ok"] is True


def test_preflight_reports_pi_entry(monkeypatch):
    monkeypatch.setenv("VICAYA_CROSS_CHECK_CHAIN", "pi:zai/glm-5.3")
    monkeypatch.setattr(rs, "_run_pi", lambda p, m, t: ("OK", ""))
    result = rs.cross_check_preflight(timeout=5)
    assert result["ok"] is True
    assert result["entries"][0]["app"] == "pi"
    assert result["entries"][0]["model"] == "zai/glm-5.3"
    assert result["entries"][0]["ok"] is True
    assert result["entries"][0]["reason"] == ""


def test_preflight_reports_failure_reason_and_prompt_is_tiny(monkeypatch):
    monkeypatch.setenv("VICAYA_CROSS_CHECK_CHAIN", "opencode:m1|agy:m2")
    seen_prompts = []

    def fake_opencode(prompt, model, timeout):
        seen_prompts.append((prompt, timeout))
        return (None, "timed out after 60s")

    monkeypatch.setattr(rs, "_run_opencode", fake_opencode)
    monkeypatch.setattr(rs, "_run_agy", lambda p, m, t: ("OK", ""))
    result = rs.cross_check_preflight(timeout=60)
    assert result["ok"] is True  # second entry answered
    assert result["entries"][0]["reason"] == "timed out after 60s"
    assert result["entries"][0]["ok"] is False
    # the probe prompt is tiny, not the draft — cheap and fast
    assert seen_prompts[0][0] == "Reply with exactly: OK"
    assert seen_prompts[0][1] == 60


def test_preflight_on_unconfigured_chain(monkeypatch):
    monkeypatch.delenv("VICAYA_CROSS_CHECK_CHAIN", raising=False)
    result = rs.cross_check_preflight(timeout=5)
    assert result["ok"] is False
    assert result["chain_configured"] is False
    assert result["entries"] == []
