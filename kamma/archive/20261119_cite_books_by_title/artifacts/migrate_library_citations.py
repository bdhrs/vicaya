"""One-off migration: cite library books by title and author, never by number.

Task 4 of the cite-books-by-title thread. Notes cite books by index row ids
(`library_refs` "223: Title", `[^calibre-223]`, `Calibre #223`, `doc 223`),
and those ids change on every rebuild. This rewrites the vault notes once:

- a `library_refs` entry loses its `<n>:` prefix and stays a quoted string;
- a `[^calibre-…]` footnote label becomes `[^lib-<k>]`, numbered by first use;
- a number beside a title the line already names is deleted;
- a number with no title beside it becomes the book's title, looked up first
  in the note's own `library_refs`, then in its run dossier(s); a number that
  resolves to neither is removed and reported;
- URLs and fenced code are never touched; line endings are kept.

Without `--apply` it only writes the dry-run report. Run from the repo root:
`uv run kamma/threads/20261119_cite_books_by_title/artifacts/migrate_library_citations.py [--apply]`
"""

from __future__ import annotations

import argparse
import difflib
import io
import json
import os
import random
import re
import sqlite3
import sys
from collections import Counter
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path

REPO = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(REPO))

from tools import note_checks  # noqa: E402
from tools.scratch import (  # noqa: E402
    _author_words,
    _book_label,
    _folded_words,
    _HitNames,
    _line_names_hit,
    _logged_library_docs,
    _title_sequence,
    _word_set,
)

ARTIFACTS = Path(__file__).resolve().parent
FOLDERS = ("", "Christianity Comparative", "What the Suttas Say About")

_SEP = r"\s*(?:,|/|&|\band\b|;\s*also)\s*"
_LEAD = (
    r"(?:calibre(?:\s+library)?|library(?:\s+(?:doc|index|id))?|index\s+doc"
    r"|doc(?:ument)?(?:\s+id)?)"
)
# A library number group: "Calibre #763, #434", "doc 5853", "Library doc #1744",
# "(Calibre #19588/19589)". A trailing number without "#" joins only if it
# resolves (a year after a comma must not).
GROUP_RE = re.compile(rf"\b{_LEAD}\s*#?\s*\d+(?:{_SEP}#?\s*\d+|\s+#\d+)*", re.I)
# A bare "#2917" of three or more digits; "(#1)" numbered lists stay.
# "ids #123 #456" lists numbers with spaces only; they form one group.
BARE_RE = re.compile(rf"(?<![\w&#/.\-]){'#'}\d{{3,}}(?:{_SEP}#?\d+|\s+#\d+)*")
LABEL_RE = re.compile(r"\[\^calibre-([^\]\s]+)\]")
LIB_LABEL_RE = re.compile(r"\[\^lib-(\d+)\]")
REF_RE = re.compile(r"""^(\s*-\s*)(["']?)(\d+)\s*:\s*(.*?)\2\s*$""")
URL_RE = re.compile(r"https?://\S+|<[^>\s]+>|\]\([^)]*\)")
NUM_RE = re.compile(r"(#)?\s*(\d+)")


@dataclass
class Report:
    actions: Counter = field(default_factory=Counter)
    unresolved: list[tuple[int, str, str]] = field(default_factory=list)
    bare_left: list[tuple[int, str]] = field(default_factory=list)


def _names(title: str) -> _HitNames:
    return _HitNames({"cite_as": title})


def _line_names(line: str, title: str) -> bool:
    """Does the line already name this book?

    Also when it holds the title's first three title words in order: a
    note's "[[The Mystery of the Breath Nimitta]]" names "The Mystery of the
    Breath Nimitta or The Case of the Missing Simile".
    """
    if _line_names_hit(_word_set(line), _names(title)):
        return True
    start = _title_sequence(title.rpartition(" — ")[0] or title)[:3]
    return len(start) == 3 and f" {' '.join(start)} " in (
        " " + " ".join(_title_sequence(line)) + " "
    )


def _cleanup(line: str) -> str:
    """Tidy what a deleted number leaves behind."""
    indent = line[: len(line) - len(line.lstrip())]
    body = line[len(indent) :]
    body = re.sub(r"\s*\(\s*(?:[,;/]\s*)*\)", "", body)
    body = re.sub(r"\(\s*(?:[,;/]\s*)+", "(", body)
    body = re.sub(r"\s*(?:[,;/]\s*)+\)", ")", body)
    body = re.sub(r"(?<=\S)[ \t]{2,}(?=\S)", " ", body)
    body = re.sub(r"\s+([.,;])(?=\s|$)", r"\1", body)
    body = re.sub(r"\|\s{2,}", "| ", body)
    body = re.sub(r",(?:\s*,)+", ",", body)
    body = re.sub(r"([:(])\s*,\s*", r"\1 ", body)
    body = re.sub(r"\s*,\s*(?=[.)]|$)", "", body)
    body = re.sub(r"\s*[,;]\s*(?=\|)", " ", body)
    # A list label whose numbers were all removed ("Document IDs:").
    body = re.sub(r"\s*\b(?:[A-Za-z]+ )?IDs?:\s*(?=[|.]|$)", "", body)
    body = re.sub(r"\s*\(\s*[.,;]?\s*\)", "", body)
    body = re.sub(r"(?<!\.)\.\s*\.(?!\.)", ".", body)
    return indent + body


def _mask(line: str) -> tuple[str, list[str]]:
    kept: list[str] = []

    def keep(m: re.Match[str]) -> str:
        kept.append(m.group(0))
        return f"\x00{len(kept) - 1}\x00"

    return URL_RE.sub(keep, line), kept


def _unmask(line: str, kept: list[str]) -> str:
    return re.sub(r"\x00(\d+)\x00", lambda m: kept[int(m.group(1))], line)


def migrate_text(
    text: str,
    resolve: Callable[[int], list[str]],
    report: Report | None = None,
) -> str:
    """The note text with every library number replaced by titles or removed.

    `resolve(n)` gives the candidate titles (`Title — Author`) for library
    number `n`: the note's own `library_refs` first, then its dossier hits.
    """
    report = report or Report()
    lines = text.splitlines(keepends=True)
    used = [int(n) for n in LIB_LABEL_RE.findall(text)]
    labels: dict[str, str] = {}
    for label in LABEL_RE.findall(text):
        if label not in labels:
            labels[label] = f"lib-{max(used, default=0) + len(labels) + 1}"

    in_front = text.startswith("---")
    in_refs = False
    in_fence = False
    out: list[str] = []
    for number, raw in enumerate(lines, start=1):
        line = raw.rstrip("\r\n")
        ending = raw[len(line) :]
        if in_front and number > 1 and line.rstrip() == "---":
            in_front = False
            in_refs = False
            out.append(raw)
            continue
        if in_front:
            if line.startswith("library_refs:"):
                in_refs = True
            elif in_refs and not line.startswith((" ", "-")):
                in_refs = False
            if in_refs and line.lstrip().startswith("-"):
                line = _migrate_ref(line, report, number)
            elif line.lstrip().startswith("-") and GROUP_RE.search(_mask(line)[0]):
                # A book listed under another key (one note lists books under
                # `canon_refs`): the entry itself names it.
                masked, kept = _mask(line)
                line = _unmask(_cleanup(GROUP_RE.sub("", masked)), kept)
                report.actions["number in another frontmatter list deleted"] += 1
            out.append(line + ending)
            continue
        if line.lstrip().startswith("```"):
            in_fence = not in_fence
        if in_fence or line.lstrip().startswith("```"):
            out.append(raw)
            continue

        masked, kept = _mask(line)
        new = LABEL_RE.sub(lambda m: f"[^{labels[m.group(1)]}]", masked)
        if new != masked:
            report.actions["footnote label renamed"] += len(LABEL_RE.findall(masked))
        changed = new != masked
        # Whether a title is "beside" a number is judged on the line as
        # written, not on titles this migration has just inserted into it.
        original = new
        for regex, bare in ((GROUP_RE, False), (BARE_RE, True)):
            pieces: list[str] = []
            last = 0
            for group in regex.finditer(new):
                before = new[: group.start()]
                aside = before.rstrip()[-1:] in ("", "(", ",", ";", "|")
                replacement = _replace_group(
                    group.group(0),
                    original,
                    bare,
                    resolve,
                    report,
                    number,
                    aside,
                    before,
                )
                if replacement is None:
                    continue
                pieces.append(new[last : group.start()])
                pieces.append(replacement)
                last = group.end()
                changed = True
            if pieces:
                new = "".join(pieces) + new[last:]
        if changed:
            new = _cleanup(new)
        out.append(_unmask(new, kept) + ending)
    return "".join(out)


REF_ITEM_RE = re.compile(r"""^(\s*-\s*)(["']?)(?:(\d+)\s*:\s*)?(.*?)\2\s*$""")


def _migrate_ref(line: str, report: Report, number: int) -> str:
    """A `library_refs` entry without its `<n>:` prefix or any number in it.

    The entry is the citation itself, so a number inside it ("Studies in
    Buddhist Philosophy (Calibre #10140)") always sits beside its title.
    """
    match = REF_ITEM_RE.match(line)
    if not match:
        return line
    lead, quote, prefix, title = match.groups()
    masked, kept = _mask(title)
    stripped = BARE_RE.sub("", GROUP_RE.sub("", masked))
    if stripped != masked:
        report.actions["number in a library_refs entry deleted"] += 1
        title = _unmask(_cleanup(stripped), kept)
    if prefix:
        report.actions["library_refs prefix dropped"] += 1
    if not prefix and stripped == masked:
        return line
    title = title.strip()
    if not title:
        report.unresolved.append(
            (number, line, "library_refs entry holds only a number")
        )
        return line
    if quote == "'" or ('"' in title and quote != '"'):
        return (
            f"{lead}'{title}'"
            if quote == "'"
            else f"{lead}'{title.replace(chr(39), chr(39) * 2)}'"
        )
    return f'{lead}"{title}"'


def _replace_group(
    group: str,
    line: str,
    bare: bool,
    resolve: Callable[[int], list[str]],
    report: Report,
    number: int,
    aside: bool = True,
    before: str = "",
) -> str | None:
    """What a number group becomes, or None to leave the text as it is.

    A number set aside from the sentence (in brackets, after a comma or a
    semicolon, at the start of a line or table cell) is deleted when the line
    already names its book. A number inside the sentence ("Duplicate file of
    Calibre #1275, already cited") is the sentence's noun: it becomes the
    title, or the sentence breaks.
    """
    lead = None if bare else re.match(rf"(?i){_LEAD}\s*", group)
    start = lead.end() if lead else 0
    rest = line.replace(group, " ")
    titles: list[str] = []
    consumed = len(group)
    for position, m in enumerate(NUM_RE.finditer(group, start)):
        hashed, value = m.group(1) == "#", int(m.group(2))
        candidates = list(dict.fromkeys(resolve(value)))
        if not candidates and position and not hashed:
            # "Calibre #6294, 1995": a trailing number without "#" that names
            # no book is not part of the group.
            consumed = len(group[: m.start()].rstrip(" ,/&;"))
            break
        if not candidates and bare:
            report.bare_left.append((number, line))
            return None
        if len(candidates) > 1:
            named = [c for c in candidates if _line_names(rest, c)]
            if len(named) != 1:
                report.unresolved.append((number, line, f"{value}: several books"))
                report.actions["number removed (ambiguous)"] += 1
                continue
            candidates = named
        if not candidates:
            report.unresolved.append(
                (number, line, f"{value}: no title in refs or dossier")
            )
            report.actions["number removed (unresolved)"] += 1
            continue
        titles.append(candidates[0])
    unnamed = [t for t in dict.fromkeys(titles) if not (aside and _line_names(rest, t))]
    report.actions["number deleted beside its title"] += len(titles) - len(unnamed)
    report.actions["number replaced by title"] += len(unnamed)
    # "Bomhard #964": the author is written just before, so only the title
    # goes in, not "Bomhard The Dhammapada — Allan R. Bomhard".
    near = set(_folded_words(before[-60:]))
    shown = []
    for title in unnamed:
        head, dash, author = title.rpartition(" — ")
        shown.append(head if dash and _author_words(author) & near else title)
    return "; ".join(shown) + group[consumed:]


# --- Data: notes, refs, dossiers, index -------------------------------------


def _vault() -> Path:
    env = {**note_checks.load_dotenv(REPO / ".env"), **os.environ}
    return Path(env["VICAYA_VAULT_PATH"]).expanduser() / "Vicaya"


def _index() -> Path | None:
    from tools.library_folders import default_config

    return default_config().index


def _head_text(vault: Path, path: Path) -> str:
    """The note as last committed in the vault repo (read-only `git show`)."""
    import subprocess

    rel = path.relative_to(vault).as_posix()
    shown = subprocess.run(
        ["git", "-C", str(vault), "show", f"HEAD:{rel}"],
        capture_output=True,
        text=True,
    )
    # A note git does not track (the feedback notes are ignored) was never
    # migrated, so the file on disk is its original.
    return shown.stdout if shown.returncode == 0 else path.read_text(encoding="utf-8")


def _notes(vault: Path, from_head: bool = False) -> list[Path]:
    notes = []
    for folder in FOLDERS:
        for path in sorted((vault / folder).glob("*.md")):
            text = (
                _head_text(vault, path)
                if from_head
                else path.read_text(encoding="utf-8")
            )
            if "library_refs:" in text or note_checks._library_number_issues(text):
                notes.append(path)
    return notes


def _dossiers_by_note() -> dict[str, list[Path]]:
    by_note: dict[str, list[Path]] = {}
    for dossier in sorted((REPO / "data" / "scratch").glob("*.md")):
        head = dossier.read_text(encoding="utf-8")[:4000]
        m = re.search(r"^\*\*Vault note:\*\*\s*(.+)$", head, re.M)
        if m:
            by_note.setdefault(m.group(1).strip(), []).append(dossier)
    return by_note


class _Titles:
    """Title of a logged hit: Calibre's stored title, else its file name."""

    def __init__(self, index: Path | None) -> None:
        self.conn = (
            sqlite3.connect(f"file:{index}?mode=ro", uri=True)
            if index and index.exists()
            else None
        )

    def of(self, hit: dict) -> str:
        path = hit.get("source_path")
        if self.conn is not None and isinstance(path, str):
            try:
                row = self.conn.execute(
                    "SELECT title, authors FROM calibre_books WHERE source_path = ?",
                    (path,),
                ).fetchone()
            except sqlite3.Error:
                row = None
            if row:
                return f"{row[0]} — {row[1]}" if row[1] else row[0]
        label = _book_label(hit)
        folder = (hit.get("relative_path") or "").rsplit("/", 2)
        if len(folder) == 3 and re.search(r"\(\d+\)$", folder[1]) and " - " in label:
            title, _, author = label.rpartition(" - ")
            return f"{title.replace('_ ', ': ')} — {author}"
        return label


def _resolver(text: str, dossiers: list[Path], titles: _Titles):
    refs: dict[int, str] = {}
    in_refs = False
    for line in text.splitlines():
        if line.startswith("library_refs:"):
            in_refs = True
            continue
        if in_refs:
            if line.rstrip() == "---" or not line.startswith((" ", "-")):
                break
            m = REF_RE.match(line)
            if m and m.group(4).strip():
                refs.setdefault(int(m.group(3)), m.group(4).strip())
    by_id: dict[int, str] = {}
    by_folder: dict[int, str] = {}
    for dossier in dossiers:
        for doc_id, hit in _logged_library_docs(
            dossier.read_text(encoding="utf-8")
        ).items():
            if not (hit.get("relative_path") or hit.get("title")):
                continue
            title = titles.of(hit)
            by_id.setdefault(doc_id, title)
            folder = re.findall(r"\((\d+)\)/", hit.get("relative_path") or "")
            if folder:
                by_folder.setdefault(int(folder[-1]), title)

    def resolve(n: int) -> list[str]:
        if n in refs:
            return [refs[n]]
        return [t for t in (by_id.get(n), by_folder.get(n)) if t]

    return resolve


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true")
    parser.add_argument(
        "--from-head",
        action="store_true",
        help="Read each note as last committed (to redo a migration already applied).",
    )
    args = parser.parse_args()
    vault = _vault()
    dossiers = _dossiers_by_note()
    titles = _Titles(_index())
    totals: Counter = Counter()
    per_note: list[tuple[str, Counter, int]] = []
    unresolved: list[str] = []
    bare_left: list[str] = []
    diffs: dict[str, str] = {}
    for path in _notes(vault, args.from_head):
        if args.from_head:
            text = _head_text(vault, path)
        else:
            with io.open(path, encoding="utf-8", newline="") as handle:
                text = handle.read()
        report = Report()
        new = migrate_text(
            text, _resolver(text, dossiers.get(str(path), []), titles), report
        )
        name = str(path.relative_to(vault))
        totals.update(report.actions)
        per_note.append((name, report.actions, len(dossiers.get(str(path), []))))
        unresolved += [
            f"- `{name}`:{n} — {why} — `{line.strip()[:220]}`"
            for n, line, why in report.unresolved
        ]
        bare_left += [
            f"- `{name}`:{n} — `{line.strip()[:220]}`" for n, line in report.bare_left
        ]
        if new != text:
            diffs[name] = "".join(
                difflib.unified_diff(
                    text.splitlines(keepends=True),
                    new.splitlines(keepends=True),
                    name,
                    name,
                    n=0,
                )
            )
            if args.apply:
                with io.open(path, "w", encoding="utf-8", newline="") as handle:
                    handle.write(new)
    random.seed(20261119)
    sample = random.sample(sorted(diffs), min(20, len(diffs)))
    lines = [
        "# Migration dry run" if not args.apply else "# Migration applied",
        "",
        f"Notes considered: {len(per_note)}. Notes changed: {len(diffs)}. Notes with a dossier: {sum(1 for _, _, d in per_note if d)}.",
        "",
        "## Counts per action",
        "",
        *[f"- {action}: {count}" for action, count in totals.most_common()],
        "",
        f"## Unresolved numbers ({len(unresolved)}): removed",
        "",
        *unresolved,
        "",
        f"## Bare `#N` left untouched ({len(bare_left)}): no title found, may not be a library number",
        "",
        *bare_left,
        "",
        "## Per note",
        "",
        *[
            f"- `{name}` (dossiers: {d}): "
            + ", ".join(f"{k} {v}" for k, v in sorted(c.items()))
            for name, c, d in per_note
        ],
    ]
    report_name = "migration-applied.md" if args.apply else "migration-dry-run.md"
    (ARTIFACTS / report_name).write_text("\n".join(lines) + "\n", encoding="utf-8")
    sample_path = Path(os.environ.get("MIGRATION_SAMPLE", "/dev/null"))
    if str(sample_path) != "/dev/null":
        sample_path.write_text("\n".join(diffs[n] for n in sample), encoding="utf-8")
    print(
        json.dumps(
            {"notes": len(per_note), "changed": len(diffs), **dict(totals)}, indent=1
        )
    )


if __name__ == "__main__":
    main()
