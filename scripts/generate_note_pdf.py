"""Generate a PDF copy of a final Vicaya note."""

from __future__ import annotations

import argparse
import importlib.util
import os
import platform
import subprocess
import sys
from pathlib import Path

import markdown

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


PDF_CSS = (
    "@page { margin: 20mm; } "
    "body { font-family: Georgia, serif; font-size: 11pt; line-height: 1.6; }"
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("note", help="Note path or Vicaya-relative note path")
    args = parser.parse_args(argv)

    env = {**note_checks.load_dotenv(Path(".env")), **os.environ}
    note_arg = str(args.note)
    pdf_enabled = env.get("VICAYA_PDF_PATH", "").strip()
    if not pdf_enabled:
        print("PDF generation skipped: VICAYA_PDF_PATH is unset")
        print(f"input: {note_arg}")
        return 0

    try:
        note_path = note_checks.resolve_existing_note(note_arg, env)
        pdf_dir = note_path.parent / "PDF"
        pdf_dir.mkdir(parents=True, exist_ok=True)
        output_path = pdf_dir / f"{note_path.stem}.pdf"
        body = note_checks.strip_frontmatter(note_path.read_text(encoding="utf-8"))
        render_pdf(body, output_path)
    except OSError as exc:
        print(f"{note_arg}: error: {exc}")
        return 2
    except ValueError as exc:
        print(f"{note_arg}: error: {exc}")
        return 2

    print("PDF generation completed")
    print(f"input: {note_path}")
    print(f"output: {output_path}")
    return 0


def render_pdf(markdown_body: str, output_path: Path) -> None:
    _ensure_homebrew_library_path()
    from weasyprint import CSS, HTML
    from weasyprint.text.fonts import FontConfiguration

    html_body = markdown.markdown(markdown_body, extensions=["tables", "fenced_code"])
    font_config = FontConfiguration()
    css = CSS(string=PDF_CSS, font_config=font_config)
    HTML(string=f"<html><body>{html_body}</body></html>").write_pdf(
        str(output_path), stylesheets=[css], font_config=font_config
    )


def _ensure_homebrew_library_path() -> None:
    dyld_path = os.environ.get("DYLD_LIBRARY_PATH", "")
    if platform.system() != "Darwin" or "/opt/homebrew/lib" in dyld_path:
        return
    env = dict(os.environ)
    env["DYLD_LIBRARY_PATH"] = f"/opt/homebrew/lib:{dyld_path}"
    raise SystemExit(subprocess.run([sys.executable, *sys.argv], env=env).returncode)


if __name__ == "__main__":
    raise SystemExit(main())
