"""Tests for the Wikipedia extract fetcher and its DNS-over-HTTPS fallback.

Fake resolvers and openers stand in for the network; `opener_for` records which
address each request was pinned to (None = the system route).
"""

from __future__ import annotations

import json
import socket
import ssl
import urllib.error
from email.message import Message

import pytest

from tools import wikipedia
from tools.wikipedia import doh_resolve, fetch_wikipedia

PAGE = {
    "query": {
        "pages": [
            {"pageid": 1, "title": "Aṭṭhakavagga", "extract": "The Aṭṭhakavagga is…"}
        ]
    }
}
MISSING = {"query": {"pages": [{"title": "Zzqq", "missing": True}]}}


class _Response:
    def __init__(self, body: dict, status: int = 200):
        self._body, self.status = json.dumps(body).encode(), status

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def read(self, *args):
        return self._body


class _Network:
    """`opener_for` stand-in: `answers` maps a route (None or an IP) to a dict
    body, an HTTP status, or an exception to raise."""

    def __init__(self, answers: dict[str | None, dict | int | Exception]):
        self.answers = answers
        self.routes: list[str | None] = []

    def opener_for(self, ip: str | None):
        def opener(request, timeout=0):
            self.routes.append(ip)
            answer = self.answers[ip]
            if isinstance(answer, int):
                raise urllib.error.HTTPError(
                    request.full_url, answer, "x", Message(), None
                )
            if isinstance(answer, Exception):
                raise answer
            return _Response(answer)

        return opener


def _no_doh(host: str) -> str | None:
    raise AssertionError("DoH should not be asked")


def test_working_dns_uses_the_system_route():
    net = _Network({None: PAGE})
    result = fetch_wikipedia(
        "Atthakavagga",
        resolver=lambda h: ["103.102.166.224"],
        doh=_no_doh,
        opener_for=net.opener_for,
    )
    assert result["ok"] and result["found"] and result["via"] == "dns"
    assert result["requested"] == "Atthakavagga"
    assert result["title"] == "Aṭṭhakavagga"
    assert result["text"].startswith("The Aṭṭhakavagga")
    assert result["url"] == "https://en.wikipedia.org/wiki/A%E1%B9%AD%E1%B9%ADhakavagga"
    assert net.routes == [None]


def test_sinkholed_dns_goes_straight_to_doh():
    net = _Network({"103.102.166.224": PAGE})
    result = fetch_wikipedia(
        "Atthakavagga",
        resolver=lambda h: ["0.0.0.0", "::"],
        doh=lambda h: "103.102.166.224",
        opener_for=net.opener_for,
    )
    assert result["ok"] and result["via"] == "doh"
    assert net.routes == ["103.102.166.224"]  # the sinkhole address is never tried


def test_connection_failure_on_dns_route_falls_back_to_doh():
    net = _Network(
        {
            None: urllib.error.URLError(ConnectionRefusedError("refused")),
            "1.2.3.4": PAGE,
        }
    )
    result = fetch_wikipedia(
        "Atthakavagga",
        resolver=lambda h: ["1.2.3.4"],
        doh=lambda h: "1.2.3.4",
        opener_for=net.opener_for,
    )
    assert result["via"] == "doh"
    assert net.routes == [None, "1.2.3.4"]


def test_resolver_error_counts_as_a_failed_dns_route():
    def broken(host: str) -> list[str]:
        raise socket.gaierror(8, "nodename nor servname provided")

    net = _Network({"1.2.3.4": PAGE})
    result = fetch_wikipedia(
        "Atthakavagga",
        resolver=broken,
        doh=lambda h: "1.2.3.4",
        opener_for=net.opener_for,
    )
    assert result["via"] == "doh"


def test_doh_failure_after_sinkhole_reports_both_reasons():
    def down(host: str) -> str | None:
        raise urllib.error.URLError("timed out")

    net = _Network({})
    result = fetch_wikipedia(
        "Atthakavagga",
        resolver=lambda h: ["0.0.0.0"],
        doh=down,
        opener_for=net.opener_for,
    )
    assert result["ok"] is False and result["blocked"] is True
    assert result["attempts"][0] == "dns: system resolver returned 0.0.0.0 (sinkholed)"
    assert result["attempts"][1].startswith("doh: lookup failed: URLError")
    assert "do not retry" in result["advice"]
    assert net.routes == []


def test_http_error_does_not_trigger_doh():
    net = _Network({None: 429})
    result = fetch_wikipedia(
        "Atthakavagga",
        resolver=lambda h: ["103.102.166.224"],
        doh=_no_doh,
        opener_for=net.opener_for,
    )
    assert result["blocked"] is True
    assert result["attempts"] == ["dns: HTTP 429"]


def test_missing_article_is_not_a_block():
    net = _Network({None: MISSING})
    result = fetch_wikipedia(
        "Zzqq", resolver=lambda h: ["1.2.3.4"], doh=_no_doh, opener_for=net.opener_for
    )
    assert result == {"ok": True, "found": False, "title": "Zzqq"}


@pytest.mark.parametrize("title", ["", "  ", "Buddha|Dhamma"])
def test_not_exactly_one_title_is_an_error_not_a_block(title):
    result = fetch_wikipedia(title, resolver=_no_doh, doh=_no_doh)  # type: ignore[arg-type]
    assert result["ok"] is False and "blocked" not in result
    assert "exactly one title" in result["error"]


def test_api_error_body_is_an_error_not_a_block():
    net = _Network({None: {"error": {"code": "maxlag", "info": "Waiting for db"}}})
    result = fetch_wikipedia(
        "Atthakavagga",
        resolver=lambda h: ["1.2.3.4"],
        doh=_no_doh,
        opener_for=net.opener_for,
    )
    assert result["ok"] is False and "blocked" not in result
    assert result["error"] == "dns: Waiting for db"


def test_doh_resolve_skips_cnames_and_sinkholes(monkeypatch):
    body = {
        "Answer": [
            {"type": 5, "data": "dyna.wikimedia.org."},
            {"type": 1, "data": "0.0.0.0"},
            {"type": 1, "data": "103.102.166.224"},
        ]
    }
    asked: list[str] = []

    def fake_urlopen(request, timeout=0):
        asked.append(request.full_url)
        return _Response(body)

    monkeypatch.setattr(wikipedia.urllib.request, "urlopen", fake_urlopen)
    assert doh_resolve("en.wikipedia.org") == "103.102.166.224"
    assert asked[0].startswith("https://1.1.1.1/dns-query?name=en.wikipedia.org")


def test_doh_resolve_with_no_answer_returns_none(monkeypatch):
    monkeypatch.setattr(
        wikipedia.urllib.request, "urlopen", lambda request, timeout=0: _Response({})
    )
    assert doh_resolve("en.wikipedia.org") is None


def test_pinned_connection_dials_the_ip_but_verifies_the_hostname(monkeypatch):
    dialed: list[tuple] = []
    wrapped: dict = {}
    sock = object()

    def fake_create_connection(address, timeout=None):
        dialed.append(address)
        return sock

    class _Context:
        def wrap_socket(self, s, server_hostname=None):
            wrapped.update(sock=s, server_hostname=server_hostname)
            return s

    monkeypatch.setattr(wikipedia.socket, "create_connection", fake_create_connection)
    conn = wikipedia._PinnedHTTPSConnection(
        "en.wikipedia.org",
        "103.102.166.224",
        context=_Context(),  # type: ignore[arg-type]
    )
    conn.connect()
    assert dialed == [("103.102.166.224", 443)]
    assert wrapped == {"sock": sock, "server_hostname": "en.wikipedia.org"}


def test_pinned_handler_uses_a_verifying_tls_context(monkeypatch):
    seen: dict = {}

    def fake_do_open(self, http_class, req, **kwargs):
        seen["context"] = kwargs["context"]
        seen["conn"] = http_class("en.wikipedia.org", timeout=5)
        return "response"

    monkeypatch.setattr(wikipedia._PinnedHTTPSHandler, "do_open", fake_do_open)
    handler = wikipedia._PinnedHTTPSHandler("103.102.166.224")
    assert handler.https_open(object()) == "response"  # type: ignore[arg-type]
    assert seen["context"].verify_mode == ssl.CERT_REQUIRED
    assert seen["context"].check_hostname is True
    assert seen["conn"]._ip == "103.102.166.224"
