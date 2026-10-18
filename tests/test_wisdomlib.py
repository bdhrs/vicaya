"""Tests for the WisdomLib fetcher behind Phase 4c (#131).

The page excerpt is cut from the real https://www.wisdomlib.org/definition/nibbana
(2026-10-18); the fake openers stand in for the network.
"""

from __future__ import annotations

import gzip
import urllib.error
from email.message import Message
from collections.abc import Iterator
from pathlib import Path

from tools.wisdomlib import fetch_wisdomlib, parse_definitions, term_slug

PAGE = (Path(__file__).parent / "data" / "wisdomlib_nibbana_excerpt.html").read_bytes()


class _Response:
    def __init__(self, body: bytes, url: str, status: int = 200):
        self._body, self.url, self.status = body, url, status

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def read(self):
        return self._body


def _http_error(url: str, code: int) -> urllib.error.HTTPError:
    return urllib.error.HTTPError(url, code, "x", Message(), None)


class _Opener:
    """A fake `urlopen`. `routes` maps a URL prefix to bytes, an HTTP status, or
    an exception to raise; `calls` records every URL asked for."""

    def __init__(self, routes: dict[str, bytes | int | Exception]):
        self.routes = routes
        self.calls: list[str] = []

    def __call__(self, request, timeout=0):
        url = request.full_url
        self.calls.append(url)
        for prefix, answer in self.routes.items():
            if url.startswith(prefix):
                if isinstance(answer, int):
                    raise _http_error(url, answer)
                if isinstance(answer, Exception):
                    raise answer
                return _Response(answer, url)
        raise AssertionError(f"unexpected request {url}")


def _opener(routes: dict[str, bytes | int | Exception]) -> _Opener:
    return _Opener(routes)


def test_slug_drops_diacritics():
    assert term_slug("Saddhā") == "saddha"
    assert term_slug("Nibbāna sutta") == "nibbana-sutta"


def test_parses_definitions_with_section_and_source():
    page = parse_definitions(PAGE.decode("utf-8"))
    assert page["title"].startswith("Nibbana")
    first, second = page["definitions"]
    assert first["section"] == "In Buddhism > Theravada (major branch of Buddhism)"
    assert first["source"] == "Access to Insight: A Glossary of Pali and Buddhist Terms"
    assert first["text"].startswith("Liberation; literally")
    assert second["source"] == "Dhamma Dana: Pali English Glossary"
    # "Resources" and the text after "See also" carry no source line.
    assert len(page["definitions"]) == 2


def test_long_definitions_are_cut_and_say_so():
    page = parse_definitions(PAGE.decode("utf-8"), max_chars=100)
    assert page["definitions"][0]["truncated_from"] > 100
    assert page["definitions"][0]["text"].endswith(" …")
    assert (
        "truncated_from"
        not in parse_definitions(PAGE.decode("utf-8"))["definitions"][0]
    )


def test_live_page_is_used_when_it_answers():
    opener = _opener({"https://www.wisdomlib.org/definition/nibbana": PAGE})
    result = fetch_wisdomlib("Nibbāna", opener=opener)
    assert result["ok"] and result["via"] == "live"
    assert len(result["definitions"]) == 2
    assert len(opener.calls) == 1


def test_blocked_live_page_falls_back_to_the_archive():
    # The 403 the September runs saw, then a gzip-compressed snapshot.
    opener = _opener(
        {
            "https://www.wisdomlib.org/": 403,
            "https://web.archive.org/web/2id_/": gzip.compress(PAGE),
        }
    )
    result = fetch_wisdomlib("nibbana", opener=opener, retry_wait=0)
    assert result["ok"] and result["via"] == "archive"
    assert result["definitions"][0]["text"].startswith("Liberation")
    assert len(opener.calls) == 2


def test_challenge_page_counts_as_blocked():
    challenge = b"<html><title>Just a moment...</title></html>"
    opener = _opener(
        {"https://www.wisdomlib.org/": challenge, "https://web.archive.org/": 404}
    )
    result = fetch_wisdomlib("nibbana", opener=opener, retry_wait=0)
    assert result["ok"] is False and result["blocked"] is True
    assert "challenge page" in result["attempts"][0]


def test_everything_blocked_says_so_once_with_the_reasons():
    opener = _opener(
        {
            "https://www.wisdomlib.org/": 403,
            "https://web.archive.org/": urllib.error.URLError("timed out"),
        }
    )
    result = fetch_wisdomlib("nibbana", opener=opener, retry_wait=0)
    assert result["blocked"] is True
    assert result["attempts"][0] == "live: HTTP 403"
    assert result["attempts"][1].startswith("archive: URLError")
    assert "do not retry" in result["advice"]
    assert len(opener.calls) == 2


def test_unknown_term_is_not_a_block():
    opener = _opener({"https://www.wisdomlib.org/": 404})
    result = fetch_wisdomlib("zzzqqq", opener=opener)
    assert result == {
        "ok": True,
        "found": False,
        "term": "zzzqqq",
        "url": "https://www.wisdomlib.org/definition/zzzqqq",
    }
    assert len(opener.calls) == 1


def test_no_archive_flag_skips_the_fallback():
    opener = _opener({"https://www.wisdomlib.org/": 403})
    result = fetch_wisdomlib("nibbana", archive=False, opener=opener)
    assert result["blocked"] is True and len(opener.calls) == 1


def test_archive_rate_limit_is_retried_once():
    answers: Iterator[bytes | int] = iter([429, gzip.compress(PAGE)])
    calls: list[str] = []

    def opener(request, timeout=0):
        url = request.full_url
        calls.append(url)
        if url.startswith("https://www.wisdomlib.org/"):
            raise _http_error(url, 403)
        answer = next(answers)
        if isinstance(answer, int):
            raise _http_error(url, answer)
        return _Response(answer, url)

    result = fetch_wisdomlib("nibbana", opener=opener, retry_wait=0)
    assert result["ok"] and result["via"] == "archive"
    assert len(calls) == 3
