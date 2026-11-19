"""Measure the library title matcher on real notes and their run dossiers.

One-off for task 2.1. Read-only: it reads notes and dossiers and writes a
JSON dump to the path given as the first argument.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(REPO))

from tools.scratch import (  # noqa: E402
    _HitNames,
    _hits_cited,
    _IndexText,
    _logged_library_docs,
)

REF_RE = re.compile(r'^\s*-\s*"?(?:(\d+)\s*:\s*)?(.*?)"?\s*$')


def library_refs(note_text: str) -> list[tuple[int | None, str]]:
    refs: list[tuple[int | None, str]] = []
    in_refs = False
    for line in note_text.splitlines():
        if line.startswith("library_refs:"):
            in_refs = True
            continue
        if in_refs:
            if line.rstrip() == "---" or not line.startswith((" ", "-")):
                break
            m = REF_RE.match(line)
            if m and m.group(2):
                refs.append((int(m.group(1)) if m.group(1) else None, m.group(2)))
    return refs


def book_key(hit: dict) -> str:
    rel = hit.get("relative_path") or ""
    parts = rel.split("/")
    for i, part in enumerate(parts):
        if re.search(r"\(\d+\)$", part):
            return "/".join(parts[: i + 1])
    return rel


def main() -> None:
    out = Path(sys.argv[1])
    # `--with-text` also looks a missed title up in the indexed text (2.1b).
    index_text = _IndexText(None) if "--with-text" in sys.argv else None
    rows = []
    for dossier in sorted((REPO / "data" / "scratch").glob("*.md")):
        text = dossier.read_text(encoding="utf-8")
        m = re.search(r"^\*\*Vault note:\*\*\s*(.+)$", text, re.M)
        if not m:
            continue
        note = Path(m.group(1).strip())
        if not note.is_file():
            continue
        docs = _logged_library_docs(text)
        hits = list(docs.values())
        refs = library_refs(note.read_text(encoding="utf-8"))
        if not refs or not hits:
            continue
        names = {d: _HitNames(h) for d, h in docs.items()}
        for number, citation in refs:
            ids = _hits_cited(citation, names, docs, index_text)
            matched = [docs[d] for d in sorted(ids)]
            keys = sorted({book_key(h) for h in matched})
            rows.append(
                {
                    "dossier": dossier.name,
                    "note": note.name,
                    "folder": note.parent.name,
                    "number": number,
                    "citation": citation,
                    "matched_ids": sorted({h["document_id"] for h in matched}),
                    "book_keys": keys,
                    "number_in_dossier": number in {h["document_id"] for h in hits},
                    "number_matched": number in {h["document_id"] for h in matched},
                }
            )
    out.write_text(json.dumps(rows, ensure_ascii=False, indent=1), encoding="utf-8")
    total = len(rows)
    matched = sum(1 for r in rows if r["matched_ids"])
    multi = sum(1 for r in rows if len(r["book_keys"]) > 1)
    num_ok = [r for r in rows if r["number_in_dossier"]]
    print(
        json.dumps(
            {
                "notes": len({r["note"] for r in rows}),
                "entries": total,
                "matched": matched,
                "unmatched": total - matched,
                "matching_two_or_more_book_keys": multi,
                "entries_whose_number_is_a_logged_hit": len(num_ok),
                "of_those_matched_on_that_hit": sum(
                    1 for r in num_ok if r["number_matched"]
                ),
            },
            indent=1,
        )
    )


if __name__ == "__main__":
    main()
