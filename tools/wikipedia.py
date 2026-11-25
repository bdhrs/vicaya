"""Fetch the plain-text extract of one English Wikipedia article (Phase 4).

On some networks plain DNS (port 53) answers `0.0.0.0` / `::` for
`*.wikipedia.org` while HTTPS to the real address works (diagnosed 2026-11-25).
`WebFetch` and a plain `urllib` request both fail there, so this module tries
the system resolver first and, if the answer is a sinkhole or the connection
fails, asks DNS-over-HTTPS (Cloudflare, addressed by IP literal) for the real
address and connects to it with the correct SNI and Host header. If both
routes fail it says so once, with the reasons.
"""

from __future__ import annotations

import http.client
import json
import socket
import ssl
import urllib.error
import urllib.parse
import urllib.request
from typing import Any, Callable

_HOST = "en.wikipedia.org"
_API = f"https://{_HOST}/w/api.php"
_DOH = "https://1.1.1.1/dns-query"
_UA = "vicaya-research-helper/1.0 (Python urllib; plain-text extracts)"
_SINKHOLES = {"0.0.0.0", "::"}

Opener = Callable[..., Any]


def system_resolve(host: str) -> list[str]:
    """Addresses the system resolver gives for `host` (raises on failure)."""
    return sorted({str(info[4][0]) for info in socket.getaddrinfo(host, 443)})


def doh_resolve(host: str, timeout: int = 10) -> str | None:
    """First real IPv4 address for `host` from DNS-over-HTTPS, else None."""
    query = urllib.parse.urlencode({"name": host, "type": "A"})
    request = urllib.request.Request(
        f"{_DOH}?{query}", headers={"accept": "application/dns-json"}
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        answer = json.load(response).get("Answer") or []
    for record in answer:
        if record.get("type") == 1 and record.get("data") not in _SINKHOLES:
            return record["data"]
    return None


class _PinnedHTTPSConnection(http.client.HTTPSConnection):
    """HTTPS to a fixed IP while keeping the hostname for SNI and certificate checks."""

    def __init__(self, host: str, ip: str, **kwargs: Any) -> None:
        super().__init__(host, **kwargs)
        self._ip = ip

    def connect(self) -> None:
        sock = socket.create_connection((self._ip, self.port), self.timeout)
        self.sock = self._context.wrap_socket(sock, server_hostname=self.host)  # type: ignore[attr-defined]


class _PinnedHTTPSHandler(urllib.request.HTTPSHandler):
    def __init__(self, ip: str) -> None:
        super().__init__()
        self._ip = ip

    def https_open(self, req: urllib.request.Request) -> http.client.HTTPResponse:
        def connection(host: str, **kwargs: Any) -> _PinnedHTTPSConnection:
            return _PinnedHTTPSConnection(host, self._ip, **kwargs)

        return self.do_open(connection, req, context=ssl.create_default_context())


def pinned_opener(ip: str | None) -> Opener:
    """`urlopen` for the system route (`ip` None), else an opener pinned to `ip`."""
    if ip is None:
        return urllib.request.urlopen
    return urllib.request.build_opener(_PinnedHTTPSHandler(ip)).open


def _read(url: str, opener: Opener, timeout: int) -> tuple[int, dict[str, Any]]:
    """GET the API `url`; return (status, parsed JSON). HTTP errors return their status."""
    request = urllib.request.Request(url, headers={"User-Agent": _UA})
    try:
        with opener(request, timeout=timeout) as response:
            return getattr(response, "status", 200), json.load(response)
    except urllib.error.HTTPError as exc:
        return exc.code, {}


def fetch_wikipedia(
    title: str,
    *,
    resolver: Callable[[str], list[str]] = system_resolve,
    doh: Callable[[str], str | None] = doh_resolve,
    opener_for: Callable[[str | None], Opener] = pinned_opener,
    timeout: int = 30,
) -> dict[str, Any]:
    """Plain-text extract of one English Wikipedia article.

    Returns `{"ok": True, "found": True, "via": "dns" | "doh", "requested",
    "title", "url", "text"}`, where `title` is the redirect target; a stub or redirect page can return an empty `text`. A title with
    no article gives `{"ok": True, "found": False}`. When every route fails the
    result is `{"ok": False, "blocked": True, "attempts": [...]}`: record that
    once as a gap and do not retry. A blank title, a title holding `|` (the
    API reads it as several titles) or an API error gives `{"ok": False,
    "error"}` without `blocked`: fix the request rather than logging a gap.
    """
    if not title.strip() or "|" in title:
        return {"ok": False, "error": f"need exactly one title, got {title!r}"}
    params = {
        "action": "query",
        "prop": "extracts",
        "explaintext": "1",
        "redirects": "1",
        "format": "json",
        "formatversion": "2",
        "titles": title,
    }
    url = f"{_API}?{urllib.parse.urlencode(params)}"
    attempts: list[str] = []

    routes: list[str] = []
    try:
        addresses = resolver(_HOST)
        if addresses and not set(addresses) <= _SINKHOLES:
            routes.append("dns")
        else:
            attempts.append(
                f"dns: system resolver returned {', '.join(addresses) or 'nothing'} "
                "(sinkholed)"
            )
    except Exception as exc:
        attempts.append(f"dns: {type(exc).__name__}: {exc}")
    routes.append("doh")

    for via in routes:
        ip: str | None = None
        if via == "doh":
            try:
                ip = doh(_HOST)
            except Exception as exc:
                attempts.append(f"doh: lookup failed: {type(exc).__name__}: {exc}")
                break
            if not ip:
                attempts.append("doh: lookup returned no address")
                break
        try:
            status, data = _read(url, opener_for(ip), timeout)
        except Exception as exc:  # connection refused, timeout, TLS
            attempts.append(f"{via}: {type(exc).__name__}: {exc}")
            continue
        if status != 200:
            # The server answered, so name resolution was not the problem.
            attempts.append(f"{via}: HTTP {status}")
            break
        pages = (data.get("query") or {}).get("pages") or []
        if not pages:
            info = (data.get("error") or {}).get("info", "response had no pages")
            return {"ok": False, "title": title, "error": f"{via}: {info}"}
        page = pages[0]
        if page.get("missing") or page.get("invalid"):
            return {"ok": True, "found": False, "title": title}
        resolved = page.get("title", title)
        return {
            "ok": True,
            "found": True,
            "via": via,
            "requested": title,
            "title": resolved,
            "url": f"https://{_HOST}/wiki/"
            + urllib.parse.quote(resolved.replace(" ", "_")),
            "text": page.get("extract", ""),
        }
    return {
        "ok": False,
        "blocked": True,
        "title": title,
        "attempts": attempts,
        "advice": "Log this once as a gap and do not retry.",
    }
