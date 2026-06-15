#!/usr/bin/env python3
"""Compare how translators render a Pāḷi word or phrase.

Given a Pāḷi term, this prints a Markdown table of translator renderings.

The SuttaCentral/Bilara part is deterministic: the root Pāḷi and every English
Bilara translator share the same segment key (e.g. ``mn1:52.1``), so the matched
Pāḷi segment and its translations line up exactly. EBC translators (Bodhi,
Thanissaro, Anīgha, …) are whole-sutta prose with no segment keys — the tool
locates the sutta and lists their files, leaving the reading-comprehension step
(extracting the rendering) to the calling agent.

Standalone:
    uv run tools/align_translations.py --phrase "sabbe dhammā anattā"
    uv run tools/align_translations.py --phrase "upādāna" --in MN1
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from tools.research_sources import (  # noqa: E402
    DEFAULT_EBC_VAULT_PATH,
    DEFAULT_SC_DATA_PATH,
    _normalise_sutta_code,
)

# CST/Velthuis writes niggahita dot-below (ṃ); SuttaCentral stores dot-above (ṁ).
# Normalise the query to SC's form so a phrase typed either way still matches.
_NIGGAHITA = str.maketrans({"ṃ": "ṁ", "Ṃ": "Ṁ"})

# Cap on grep hits scanned when locating a phrase. High enough to detect that a
# common word spans many suttas (→ ambiguous), low enough to stay fast.
_LOCATE_LIMIT = 500
# Cap on matched segments rendered per sutta, to keep table cells scannable.
_MAX_SEGMENTS = 20

_KEY_RE = re.compile(r'^"([^"]+)"\s*:')


@dataclass
class AlignResult:
    status: str  # "ok" | "ambiguous" | "not_found" | "not_in_scope"
    phrase: str
    uid: str = ""
    seg_keys: list[str] = field(default_factory=list)
    rows: list[tuple[str, str]] = field(default_factory=list)  # (label, text)
    ebc_files: list[tuple[str, Path]] = field(
        default_factory=list
    )  # (translator, path)
    candidate_uids: list[str] = field(default_factory=list)


@dataclass
class _Located:
    """A sutta whose root Pāḷi matched, with the actual file that holds it.

    `file_stem` is the filename stem before `_root` — equal to the uid for
    single-file suttas (`mn1`) but a range token for verse collections
    (`dhp279:1` lives in `dhp273-289_root-pli-ms.json`). Carrying the real path
    is what lets verse texts align instead of silently producing empty rows.
    """

    uid: str
    file_stem: str
    root_path: Path
    seg_keys: list[str] = field(default_factory=list)


def _uid_of(seg_key: str) -> str:
    """`mn1:52.1` → `mn1`; `kv22.8:4.2` → `kv22.8`."""
    return seg_key.rsplit(":", 1)[0]


def _normalise_pali(s: str) -> str:
    """Fold dot-below niggahita (ṃ) to SuttaCentral's dot-above (ṁ)."""
    return s.translate(_NIGGAHITA)


def locate_segments(
    phrase: str,
    sc_root: Path | None = None,
) -> dict[str, _Located]:
    """Grep Bilara root Pāḷi for `phrase`; return {uid: _Located}.

    Case-insensitive and niggahita-folded so a Pāḷi word typed in CST style or
    lowercase still matches SC's stored form. The matched file path is carried
    on each `_Located` so verse texts stored in range files align correctly.
    Order-preserving and de-duplicated per uid.
    """
    sc_root = sc_root or DEFAULT_SC_DATA_PATH
    if sc_root is None:
        return {}
    root = sc_root / "sc_bilara_data" / "root" / "pli"
    if not root.exists():
        return {}
    needle = _normalise_pali(phrase)
    cmd = ["grep", "-rn", "-F", "-a", "-i", "--include=*.json", "--", needle, str(root)]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
    except subprocess.TimeoutExpired:
        return {}
    if result.returncode > 1:
        return {}
    found: dict[str, _Located] = {}
    for line in result.stdout.splitlines()[:_LOCATE_LIMIT]:
        parts = line.split(":", 2)
        if len(parts) < 3:
            continue
        m = _KEY_RE.match(parts[2].strip())
        if not m:
            continue
        key = m.group(1)
        if ":" not in key:
            continue
        uid = _uid_of(key)
        loc = found.get(uid)
        if loc is None:
            path = Path(parts[0])
            loc = _Located(
                uid=uid, file_stem=path.name.split("_root", 1)[0], root_path=path
            )
            found[uid] = loc
        if key not in loc.seg_keys:
            loc.seg_keys.append(key)
    return found


def _bilara_en_author_files(file_stem: str, sc_root: Path) -> list[tuple[str, Path]]:
    """Return [(author, path), ...] for every English Bilara translation file.

    `file_stem` is the root file's stem (`mn1` or a range like `dhp273-289`) so
    the English files line up with the same segment keys as the Pāḷi.
    """
    base = sc_root / "sc_bilara_data" / "translation" / "en"
    if not base.exists():
        return []
    out: list[tuple[str, Path]] = []
    for path in sorted(base.rglob(f"{file_stem}_translation-en-*.json")):
        author = path.relative_to(base).parts[0]
        out.append((author, path))
    return out


def _read_segments(path: Path, keys: list[str]) -> str:
    """Join the values at `keys` from a Bilara JSON file, in key order."""
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return ""
    if not isinstance(data, dict):
        return ""
    parts = [str(data[k]).strip() for k in keys if str(data.get(k, "")).strip()]
    return " … ".join(parts)


def _ebc_translator_files(uid: str, vault: Path) -> list[tuple[str, Path]]:
    """Return [(translator, path), ...] for EBC sutta-text files of uid.

    Translator label is the top folder under `+Suttas/Sutta Texts/`.
    """
    base = vault / "+Suttas" / "Sutta Texts"
    if not base.exists():
        return []
    seen: set[Path] = set()
    out: list[tuple[str, Path]] = []
    patterns = (f"{uid}-*.md", f"{uid}.md")
    for pattern in patterns:
        for path in base.rglob(pattern):
            if path in seen:
                continue
            seen.add(path)
            rel = path.relative_to(base).parts
            translator = rel[0] if rel else path.stem
            out.append((translator.strip(), path))
    out.sort(key=lambda t: t[0].lower())
    return out


def align(
    phrase: str,
    scope: str | None = None,
    sc_root: Path | None = None,
    ebc_vault: Path | None = DEFAULT_EBC_VAULT_PATH,
) -> AlignResult:
    """Build the alignment result for a Pāḷi phrase.

    `scope` (e.g. "MN1") pins the comparison to one sutta. Without it, a phrase
    matching more than one sutta returns status "ambiguous" — never guessed.
    """
    sc_root = sc_root or DEFAULT_SC_DATA_PATH
    phrase = _normalise_pali(phrase.strip())
    found = locate_segments(phrase, sc_root=sc_root)

    if scope:
        target = _normalise_sutta_code(scope).lower()
        if target not in found:
            return AlignResult(
                status="not_in_scope",
                phrase=phrase,
                uid=target,
                candidate_uids=sorted(found),
            )
        found = {target: found[target]}
    elif len(found) > 1:
        return AlignResult(
            status="ambiguous",
            phrase=phrase,
            candidate_uids=sorted(found),
        )
    elif not found:
        return AlignResult(status="not_found", phrase=phrase)

    loc = next(iter(found.values()))
    seg_keys = loc.seg_keys[:_MAX_SEGMENTS]

    rows: list[tuple[str, str]] = []
    if sc_root is not None:
        rows.append(("**Pāḷi**", _read_segments(loc.root_path, seg_keys)))
        for author, path in _bilara_en_author_files(loc.file_stem, sc_root):
            rows.append((f"{author.title()} (Bilara)", _read_segments(path, seg_keys)))

    ebc_files = _ebc_translator_files(loc.uid, ebc_vault) if ebc_vault else []

    return AlignResult(
        status="ok",
        phrase=phrase,
        uid=loc.uid,
        seg_keys=seg_keys,
        rows=rows,
        ebc_files=ebc_files,
    )


def render(result: AlignResult) -> str:
    if result.status == "not_found":
        return (
            f"No Bilara root match for '{result.phrase}'. "
            "Matching ignores case and niggahita (ṃ/ṁ); check spelling, other "
            "diacritics, and that the phrase sits within one segment."
        )
    if result.status == "not_in_scope":
        seen = ", ".join(result.candidate_uids) or "no suttas"
        return f"'{result.phrase}' was not found in {result.uid}. It occurs in: {seen}."
    if result.status == "ambiguous":
        shown = result.candidate_uids[:15]
        more = len(result.candidate_uids) - len(shown)
        suffix = f", and {more} more" if more > 0 else ""
        return (
            f"AMBIGUOUS: '{result.phrase}' occurs in {len(result.candidate_uids)} "
            f"suttas: {', '.join(shown)}{suffix}.\n"
            "Re-run with --in <ref> to choose one (e.g. --in MN1)."
        )

    lines = [
        f"Phrase: {result.phrase}   Sutta: {result.uid}   "
        f"Segments: {', '.join(result.seg_keys)}",
        "",
        "| Translator | Rendering |",
        "| :-- | :-- |",
    ]
    for label, text in result.rows:
        lines.append(f"| {label} | {text or '—'} |")
    if result.ebc_files:
        lines.append("")
        lines.append(f"EBC sources to read for {result.uid}:")
        for translator, path in result.ebc_files:
            lines.append(f"- {translator}: {path}")
    return "\n".join(lines)


def _cli(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Compare translator renderings of a Pāḷi word or phrase.",
    )
    parser.add_argument(
        "--phrase", required=True, help="Pāḷi word or phrase (exact, with diacritics)"
    )
    parser.add_argument(
        "--in", dest="scope", default=None, help="Sutta to scope to, e.g. MN1"
    )
    args = parser.parse_args(argv)
    result = align(args.phrase, scope=args.scope)
    print(render(result))
    return 0 if result.status == "ok" else 1


if __name__ == "__main__":
    raise SystemExit(_cli())
