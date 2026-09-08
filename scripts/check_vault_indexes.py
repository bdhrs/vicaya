"""Verify the Vicaya vault index notes against the notes actually on disk.

Read-only. Checks `Vicaya/catalog-by-topics.md` and `Vicaya/summary-vicaya.md` for:

  * notes on disk that no index lists (the note you just wrote, or an older gap)
  * index entries whose wikilink resolves to no file anywhere in the vault
  * the same note listed twice in one index
  * a stale "<N> research notes" count line in the catalog
  * stray horizontal rules in the catalog (the signature of a botched
    append-to-every-section edit, which once duplicated one bullet 33 times)

Obsidian resolves a bare `[[filename]]` by basename across the whole vault, so a
subfolder note linked without its folder prefix is CORRECT and is not reported.

Exit 0 clean, 1 findings, 2 error. `--note <path>` additionally asserts that one
specific note is present in both indexes, which is what Phase 7 needs.
"""

from __future__ import annotations

import argparse
import importlib.util
import os
import re
import sys
from pathlib import Path

try:
    from tools import note_checks
except ModuleNotFoundError:
    spec = importlib.util.spec_from_file_location(
        "note_checks",
        Path(__file__).resolve().parents[1] / "tools" / "note_checks.py",
    )
    if spec is None or spec.loader is None:
        raise
    note_checks = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = note_checks
    spec.loader.exec_module(note_checks)

CATALOG = "catalog-by-topics.md"
SUMMARY = "summary-vicaya.md"
# Index notes and the repo readme are apparatus, not research notes.
NOT_A_NOTE = {CATALOG, SUMMARY, "README.md"}
BULLET = re.compile(r"^\s*-\s*\[\[([^\]|]+)")
# summary-vicaya rows are table cells, so the link is anywhere in the line.
ANY_LINK = re.compile(r"\[\[([^\]|]+)")
COUNT_LINE = re.compile(r"(\d+) research notes from Vicaya/")


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _notes_on_disk(vicaya: Path) -> dict[str, Path]:
    """Research notes under Vicaya/, keyed by basename. PDF/ is not notes."""
    found: dict[str, Path] = {}
    for path in sorted(vicaya.rglob("*.md")):
        if "PDF" in path.relative_to(vicaya).parts:
            continue
        if path.name in NOT_A_NOTE:
            continue
        found[path.stem] = path
    return found


def _vault_basenames(vault: Path) -> set[str]:
    """Every markdown basename in the vault — how Obsidian resolves wikilinks."""
    return {p.stem for p in vault.rglob("*.md")}


def _links(text: str, pattern: re.Pattern[str]) -> list[str]:
    out = []
    for line in text.splitlines():
        match = pattern.match(line) if pattern is BULLET else pattern.search(line)
        if match:
            # Rows inside a markdown table escape the alias pipe as "\|", so the
            # captured target keeps a trailing backslash. Strip it.
            out.append(match.group(1).strip().rstrip("\\").strip())
    return out


def check(vault: Path, note: str | None) -> list[str]:
    vicaya = vault / "Vicaya"
    if not vicaya.is_dir():
        raise ValueError(f"no Vicaya/ folder under {vault}")

    findings: list[str] = []
    on_disk = _notes_on_disk(vicaya)
    resolvable = _vault_basenames(vault)

    catalog_text = _read(vicaya / CATALOG)
    summary_text = _read(vicaya / SUMMARY)
    catalog_links = _links(catalog_text, BULLET)
    summary_links = _links(summary_text, ANY_LINK)

    def basename(link: str) -> str:
        return link.split("/")[-1]

    catalog_names = {basename(x) for x in catalog_links}
    summary_names = {basename(x) for x in summary_links}

    for stem in sorted(on_disk):
        missing = [
            n
            for n, s in ((CATALOG, catalog_names), (SUMMARY, summary_names))
            if stem not in s
        ]
        if missing:
            findings.append(
                f"uncatalogued: {stem!r} is on disk but absent from {', '.join(missing)}"
            )

    for index_name, links in ((CATALOG, catalog_links), (SUMMARY, summary_links)):
        for link in links:
            if basename(link) not in resolvable:
                findings.append(
                    f"broken link: {index_name} -> [[{link}]] resolves to no file in the vault"
                )
        seen: dict[str, int] = {}
        for link in links:
            seen[basename(link)] = seen.get(basename(link), 0) + 1
        for name, count in sorted(seen.items()):
            if count > 1:
                findings.append(
                    f"duplicate entry: {index_name} lists {name!r} {count} times"
                )

    stated = COUNT_LINE.search(catalog_text)
    if stated and int(stated.group(1)) != len(catalog_links):
        findings.append(
            f"stale count: {CATALOG} says {stated.group(1)} research notes but lists {len(catalog_links)}"
        )

    rules = sum(1 for line in catalog_text.splitlines() if line.strip() == "---")
    if rules:
        findings.append(
            f"stray horizontal rules: {CATALOG} has {rules} bare '---' line(s); "
            "these mark a botched append-to-every-section edit"
        )

    if note:
        stem = Path(note).stem
        for index_name, names in ((CATALOG, catalog_names), (SUMMARY, summary_names)):
            if stem not in names:
                findings.append(
                    f"this run's note {stem!r} was not added to {index_name}"
                )

    return findings


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--note",
        help="Also assert this note (path or Vicaya-relative) appears in both indexes",
    )
    args = parser.parse_args(argv)

    env = {**note_checks.load_dotenv(Path(".env")), **os.environ}
    vault = env.get("VICAYA_VAULT_PATH", "").strip()
    if not vault:
        print("error: VICAYA_VAULT_PATH is not set (see .env.example)", file=sys.stderr)
        return 2

    try:
        findings = check(Path(vault).expanduser(), args.note)
    except (OSError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    if not findings:
        print("vault indexes: PASS")
        return 0
    for finding in findings:
        print(f"vault indexes: {finding}")
    print(f"vault indexes: {len(findings)} finding(s)")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
