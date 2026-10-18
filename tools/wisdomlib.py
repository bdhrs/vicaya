"""Fetch and read a WisdomLib definition page (Phase 4c).

Phase 4c used `WebFetch`, which returned 403 for every WisdomLib page in late
September 2026 (issue #131). A plain browser-style request still works from a
home connection, and the Wayback Machine keeps snapshots, so this module tries
the live page first and the newest snapshot second. If both fail it says so
once, with the reason, so the agent records one gap instead of retrying.
"""

from __future__ import annotations

import gzip
import re
import time
import unicodedata
import urllib.error
import urllib.request
from html.parser import HTMLParser
from typing import Any, Callable

_BASE = "https://www.wisdomlib.org/definition/"
_ARCHIVE = "https://web.archive.org/web/2id_/"
_UA = (
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/124.0 Safari/537.36"
)
_CHALLENGE = ("Just a moment...", "cf-chl-", "Attention Required! | Cloudflare")
_STOP_HEADINGS = ("See also", "Relevant text")


def term_slug(term: str) -> str:
    """`Saddhā` → `saddha`: the ASCII, hyphenated form WisdomLib uses in URLs."""
    plain = unicodedata.normalize("NFKD", term)
    plain = "".join(c for c in plain if not unicodedata.combining(c))
    return re.sub(r"[^a-z0-9]+", "-", plain.lower()).strip("-")


class _Page(HTMLParser):
    """Collects (section, text, source) definitions from a definition page."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.title = ""
        self.definitions: list[dict[str, Any]] = []
        self._headings: dict[int, str] = {}
        self._level: int | None = None
        self._buf: list[str] = []
        self._in_p = False
        self._in_source = False
        self._paras: list[str] = []
        self._stopped = False

    def _section(self) -> str:
        return " > ".join(self._headings[k] for k in sorted(self._headings) if k > 1)

    def _flush(self, source: str | None) -> None:
        if self._paras:
            self.definitions.append(
                {
                    "section": self._section(),
                    "text": "\n\n".join(self._paras),
                    "source": source,
                }
            )
        self._paras = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if re.fullmatch(r"h[1-4]", tag):
            self._level = int(tag[1])
            self._buf = []
        elif tag == "p" and not self._stopped:
            self._in_p = True
            self._buf = []
        elif tag == "section" and "source" in (dict(attrs).get("class") or ""):
            self._in_source = True
            self._buf = []

    def handle_data(self, data: str) -> None:
        if self._level is not None or self._in_p or self._in_source:
            self._buf.append(data)

    def handle_endtag(self, tag: str) -> None:
        text = re.sub(r"\s+", " ", "".join(self._buf)).strip()
        if self._level is not None and tag == f"h{self._level}":
            if self._level == 1:
                self.title = text
            else:
                self._flush(None)
                if self._level == 2 and text.startswith(_STOP_HEADINGS):
                    self._stopped = True
                self._headings[self._level] = text
                for deeper in [k for k in self._headings if k > self._level]:
                    del self._headings[deeper]
            self._level = None
        elif tag == "p" and self._in_p:
            self._in_p = False
            if text:
                self._paras.append(text)
        elif tag == "section" and self._in_source:
            self._in_source = False
            self._flush(re.sub(r"^Source:\s*", "", text) or None)

    def close(self) -> None:
        super().close()
        self._flush(None)


def parse_definitions(html: str, max_chars: int | None = 2500) -> dict[str, Any]:
    """The titled definitions on a page; blocks with no source line are site text.

    The page also holds navigation, an introduction and one-line blurbs about
    each tradition or language; none of them carries a `Source:` line, so none
    is a definition. A text over `max_chars` is cut and says so (the PTS
    dictionary entry for nibbāna alone is 22,000 characters).
    """
    page = _Page()
    page.feed(html)
    page.close()
    definitions = []
    for d in page.definitions:
        if not d["source"]:
            continue
        chars = len(d["text"])
        if max_chars is not None and chars > max_chars:
            d = {**d, "text": d["text"][:max_chars] + " …", "truncated_from": chars}
        definitions.append(d)
    return {"title": page.title, "definitions": definitions}


def _read(url: str, opener: Callable[..., Any], timeout: int) -> tuple[int, str, str]:
    """GET `url`; return (status, final_url, text). HTTP errors return their status."""
    request = urllib.request.Request(url, headers={"User-Agent": _UA})
    try:
        with opener(request, timeout=timeout) as response:
            status = getattr(response, "status", 200)
            final = getattr(response, "url", url)
            raw = response.read()
    except urllib.error.HTTPError as exc:
        return exc.code, url, ""
    if raw[:2] == b"\x1f\x8b":
        raw = gzip.decompress(raw)
    return status, final, raw.decode("utf-8", errors="replace")


def fetch_wisdomlib(
    term: str,
    *,
    archive: bool = True,
    max_chars: int | None = 2500,
    opener: Callable[..., Any] | None = None,
    timeout: int = 30,
    retry_wait: float = 3.0,
) -> dict[str, Any]:
    """Definitions of `term` from WisdomLib: the live page, else the newest snapshot.

    Returns `{"ok": True, "via": "live" | "archive", "url", "title",
    "definitions": [{section, text, source}]}`. A term WisdomLib has no page for
    gives `{"ok": True, "found": False}`. When every route fails the result is
    `{"ok": False, "blocked": True, "attempts": [...]}`: record that once as a
    gap and do not retry.
    """
    opener = opener or urllib.request.urlopen
    slug = term_slug(term)
    if not slug:
        return {"ok": False, "error": f"cannot build a WisdomLib URL from {term!r}"}
    url = _BASE + slug
    routes = [("live", url)] + ([("archive", _ARCHIVE + url)] if archive else [])
    attempts: list[str] = []
    for via, route in routes:
        try:
            status, final, html = _read(route, opener, timeout)
            if status == 429:  # the archive rate-limits bursts; one pause fixes it
                time.sleep(retry_wait)
                status, final, html = _read(route, opener, timeout)
        except Exception as exc:  # network down, DNS, timeout
            attempts.append(f"{via}: {type(exc).__name__}: {exc}")
            continue
        if status == 404:
            if via == "live":
                return {"ok": True, "found": False, "term": term, "url": url}
            attempts.append(f"{via}: no snapshot (HTTP 404)")
            continue
        if status != 200 or any(marker in html for marker in _CHALLENGE):
            attempts.append(
                f"{via}: HTTP {status}" + (" challenge page" if html else "")
            )
            continue
        parsed = parse_definitions(html, max_chars)
        if not parsed["definitions"]:
            attempts.append(f"{via}: page had no definitions")
            continue
        return {
            "ok": True,
            "found": True,
            "via": via,
            "term": term,
            "url": final if via == "archive" else url,
            **parsed,
        }
    return {
        "ok": False,
        "blocked": True,
        "term": term,
        "url": url,
        "attempts": attempts,
        "advice": "Log this once as a gap and do not retry. Use the library "
        "sources instead (see Phase 4c).",
    }
