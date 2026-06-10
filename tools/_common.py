"""Shared utilities for tools/: REPO_ROOT, dotenv loader, env_path, strip_xml."""

from __future__ import annotations

import os
import re as _re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

_XML_TAG_RE = _re.compile(r"<[^>]+>")
_XML_ENTITY_MAP = {"&amp;": "&", "&lt;": "<", "&gt;": ">", "&quot;": '"', "&apos;": "'"}


def strip_xml(s: str) -> str:
    if not s:
        return s
    out = _XML_TAG_RE.sub("", s)
    for k, v in _XML_ENTITY_MAP.items():
        out = out.replace(k, v)
    return _re.sub(r"\s+", " ", out).strip()


def _parse_dotenv(path: Path) -> dict[str, str]:
    result: dict[str, str] = {}
    if not path.exists():
        return result
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, val = line.partition("=")
        result[key.strip()] = val.strip().strip('"').strip("'")
    return result


def load_dotenv(path: Path = REPO_ROOT / ".env") -> None:
    for key, val in _parse_dotenv(path).items():
        os.environ.setdefault(key, val)


def env_path(key: str, default: str | None = None) -> Path | None:
    val = os.environ.get(key, default)
    return Path(os.path.expanduser(val)) if val else None
