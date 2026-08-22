"""Generate a PDF copy of a final Vicaya note."""

from __future__ import annotations

import argparse
import importlib.util
import os
import platform
import re
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
    "@page { margin: 20mm; "
    "@footnote { border-top: 0.6pt solid #999; padding-top: 3pt; margin-top: 8pt; } } "
    "body { font-family: Georgia, serif; font-size: 11pt; line-height: 1.6; } "
    # Images wider than the content area must scale down to the page width,
    # otherwise they run off the edge of the page in the generated PDF.
    "img { max-width: 100%; height: auto; } "
    ".pagefn { float: footnote; footnote-display: block; font-size: 0.72em; line-height: 1.3; } "
    ".pagefn.missing { color: #b00020; font-weight: bold; } "
    "::footnote-call { color: #7a2e2e; font-size: 0.72em; vertical-align: super; "
    # Without this, two adjacent footnote markers (e.g. [^a][^b]) render as
    # touching digits that read as one number.
    "padding-left: 1pt; }"
)

_FOOTNOTE_CALL_RE = re.compile(
    r'<sup id="fnref\d*:([^"]+)"><a class="footnote-ref"[^>]*>\d+</a></sup>'
)
_FOOTNOTE_DEF_RE = re.compile(r'<li id="fn:([^"]+)">(.*?)</li>', re.S)
_FOOTNOTE_BACKREF_RE = re.compile(r'(?:&#160;)?<a class="footnote-backref".*?</a>')
_SOLE_PARAGRAPH_RE = re.compile(r"^<p>(.*)</p>$", re.S)
_FOOTNOTE_BLOCK_RE = re.compile(r'<div class="footnote">.*?</div>\s*', re.S)


def _footnote_definition_html(content: str) -> str:
    """A footnote `<li>`'s inner HTML, backref arrow stripped. A single
    paragraph — the vault's own footnote convention, and the common case —
    unwraps its `<p>` tags; a multi-paragraph definition keeps them all, so
    later content is never silently dropped."""
    content = _FOOTNOTE_BACKREF_RE.sub("", content).strip()
    sole_paragraph = _SOLE_PARAGRAPH_RE.match(content)
    return sole_paragraph.group(1) if sole_paragraph else content


def _place_footnotes_at_page_foot(html_body: str) -> str:
    """Move each footnote's text to sit under the page that cites it.

    The markdown `footnotes` extension emits a calling marker plus a
    definitions list at the very end. WeasyPrint's `float: footnote` puts an
    element at the bottom of whatever page it lands on, so replacing each
    calling marker with its own definition text — wrapped for that float —
    turns the trailing list into true per-page notes with no manual page
    tracking required.
    """
    notes = {
        fid: _footnote_definition_html(content)
        for fid, content in _FOOTNOTE_DEF_RE.findall(html_body)
    }

    def _replace_call(match: re.Match[str]) -> str:
        fid = match.group(1)
        if fid not in notes:
            # A dangling [^id] with no matching definition: render an
            # obviously-wrong marker instead of a silently blank note, so a
            # typo'd id is visible in the PDF rather than hidden by it.
            return f'<span class="pagefn missing">[missing footnote: {fid}]</span>'
        return f'<span class="pagefn">{notes[fid]}</span>'

    html_body = _FOOTNOTE_CALL_RE.sub(_replace_call, html_body)
    return _FOOTNOTE_BLOCK_RE.sub("", html_body)


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
        vault_path = env.get("VICAYA_VAULT_PATH", "").strip()
        if not vault_path:
            raise ValueError("VICAYA_VAULT_PATH is required to place the PDF")
        notes_root = Path(vault_path).expanduser() / "Vicaya"
        output_path = note_checks.resolve_pdf_path(note_path, notes_root)
        output_path.parent.mkdir(parents=True, exist_ok=True)
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

    html_body = markdown.markdown(
        markdown_body, extensions=["tables", "fenced_code", "footnotes"]
    )
    html_body = _place_footnotes_at_page_foot(html_body)
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
