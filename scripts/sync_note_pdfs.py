"""Keep the Vicaya PDF tree an exact mirror of the notes: one PDF per note, nothing else."""

from __future__ import annotations

import argparse
import os
import sys
from dataclasses import dataclass
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from scripts import generate_note_pdf  # noqa: E402
from tools import note_checks  # noqa: E402

PDF_DIR_NAME = "PDF"


@dataclass(frozen=True)
class Audit:
    missing: list[tuple[Path, Path]]
    orphans: list[Path]

    @property
    def clean(self) -> bool:
        return not self.missing and not self.orphans


def find_notes(notes_root: Path) -> list[Path]:
    """Every note in the tree, excluding the PDF tree and any dot-directory."""
    pdf_root = notes_root / PDF_DIR_NAME
    notes = []
    for path in notes_root.rglob("*.md"):
        relative = path.relative_to(notes_root)
        if any(part.startswith(".") for part in relative.parts):
            continue
        if path.is_relative_to(pdf_root):
            continue
        notes.append(path)
    return sorted(notes)


def audit(notes_root: Path) -> Audit:
    """Compare the notes against the PDF tree.

    A note with no PDF at its mirrored path is missing one. Anything else in
    the PDF tree — a PDF whose note is gone, or a file that is not a PDF at
    all — is an orphan, since the tree holds nothing but note twins.
    """
    notes_root = notes_root.resolve()
    expected = {
        note_checks.resolve_pdf_path(note, notes_root): note
        for note in find_notes(notes_root)
    }
    missing = sorted((note, pdf) for pdf, note in expected.items() if not pdf.exists())
    pdf_root = notes_root / PDF_DIR_NAME
    orphans = sorted(
        path for path in pdf_root.rglob("*") if path.is_file() and path not in expected
    )
    return Audit(missing=missing, orphans=orphans)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--fix",
        action="store_true",
        help="Generate the missing PDFs and delete the orphans (default: report only).",
    )
    parser.add_argument(
        "--rebuild",
        action="store_true",
        help="With --fix, also regenerate every existing PDF, not just the missing ones.",
    )
    args = parser.parse_args(argv)

    env = {**note_checks.load_dotenv(_REPO_ROOT / ".env"), **os.environ}
    vault_path = env.get("VICAYA_VAULT_PATH", "").strip()
    if not vault_path:
        print("error: VICAYA_VAULT_PATH is required")
        return 2
    notes_root = (Path(vault_path).expanduser() / "Vicaya").resolve()
    if not notes_root.is_dir():
        print(f"error: notes root not found: {notes_root}")
        return 2

    result = audit(notes_root)
    notes = find_notes(notes_root)
    print(f"notes root: {notes_root}")
    print(f"notes: {len(notes)}")

    rebuild = args.fix and args.rebuild
    if result.clean and not rebuild:
        print("every note has its PDF twin and the PDF tree holds nothing else")
        return 0

    for note, pdf in result.missing:
        print(f"missing PDF: {pdf.relative_to(notes_root)}")
    for path in result.orphans:
        print(f"orphan: {path.relative_to(notes_root)}")

    if not args.fix:
        print(
            f"\n{len(result.missing)} missing, {len(result.orphans)} orphaned "
            "— re-run with --fix to generate and delete"
        )
        return 1

    missing_pdfs = {pdf for _note, pdf in result.missing}
    targets = notes if rebuild else [note for note, _pdf in result.missing]
    regenerated = 0
    for note in targets:
        pdf = note_checks.resolve_pdf_path(note, notes_root)
        pdf.parent.mkdir(parents=True, exist_ok=True)
        body = note_checks.strip_frontmatter(note.read_text(encoding="utf-8"))
        generate_note_pdf.render_pdf(body, pdf)
        if pdf in missing_pdfs:
            print(f"generated: {pdf.relative_to(notes_root)}")
        else:
            print(f"regenerated: {pdf.relative_to(notes_root)}")
            regenerated += 1
    for path in result.orphans:
        path.unlink()
        print(f"deleted: {path.relative_to(notes_root)}")

    _prune_empty_dirs(notes_root / PDF_DIR_NAME)
    print(
        f"\nfixed: {len(result.missing)} generated, {regenerated} regenerated, "
        f"{len(result.orphans)} deleted"
    )
    return 0


def _prune_empty_dirs(root: Path) -> None:
    for path in sorted(root.rglob("*"), key=lambda p: len(p.parts), reverse=True):
        if path.is_dir() and not any(path.iterdir()):
            path.rmdir()


if __name__ == "__main__":
    raise SystemExit(main())
