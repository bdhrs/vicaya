"""Validate Vicaya final notes and resolve note paths for Phase 7 scripts.

Not a general YAML validator: the frontmatter checks are line-based and
conservative, catching only known note-shape hazards (unquoted colon-space
scalars, annotated URLs, YAML-mapping-style list items, missing fields).
"""

from __future__ import annotations

import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import TypedDict

_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from tools._common import _parse_dotenv  # noqa: E402


TOOL_URL = "https://github.com/bdhrs/vicaya"
REQUIRED_SECTIONS = (
    "## Question",
    "## Findings",
    "## Canon Evidence (T1)",
    "## Sources Investigated, Not Used",
    "## Critical Gaps",
    "## Bibliography",
)

# Absence of these is a warning, not an error: they are content-dependent,
# so a thematic/secular question or a custom note format may legitimately
# omit them. All other required sections remain hard errors.
SOFT_SECTIONS = frozenset({"## Canon Evidence (T1)"})

# Series-format bodies ("What the EBTs say / don't say about X") hold their
# block-quoted canon evidence inside those sections, so a separate Canon
# Evidence (T1) section is not expected and its soft warning is suppressed.
_SERIES_HEADING_RE = re.compile(
    r"^##\s+.*\bwhat the (ebts|suttas)\b.*\bsay\b", re.IGNORECASE
)

# Hints appended to missing-section errors that series runs hit repeatedly:
# the fixed series body replaces the evidence sections but never the
# scaffolding, and agents kept re-deriving that rule from sibling notes.
_SECTION_HINTS = {
    "## Question": (
        "fixed-format/series notes keep `## Question` above the custom body"
    ),
    "## Findings": (
        "fixed-format/series notes keep a short `## Findings` overview "
        "above the custom body"
    ),
}


@dataclass(frozen=True)
class ValidationIssue:
    code: str
    message: str
    line: int
    severity: str = "error"


class FrontmatterFields(TypedDict):
    scalars: dict[str, tuple[str, int]]
    lists: dict[str, list[tuple[str, int]]]


def load_dotenv(path: Path) -> dict[str, str]:
    return _parse_dotenv(path)


def resolve_note_path(note_arg: str, vault_path: Path) -> Path:
    note_path = Path(note_arg).expanduser()
    if note_path.is_absolute():
        return note_path
    if note_arg == "Vicaya" or note_arg.startswith("Vicaya/"):
        return vault_path.expanduser() / note_path
    return vault_path.expanduser() / "Vicaya" / note_path


def resolve_existing_note(note_arg: str, env: dict[str, str]) -> Path:
    raw_path = Path(note_arg).expanduser()
    if raw_path.is_absolute():
        note_path = raw_path
    else:
        vault_path = env.get("VICAYA_VAULT_PATH", "").strip()
        if not vault_path:
            raise ValueError("VICAYA_VAULT_PATH is required for relative note paths")
        note_path = resolve_note_path(note_arg, Path(vault_path))
    if not note_path.exists():
        raise OSError(f"note not found: {note_path}")
    return note_path


def extract_frontmatter(text: str) -> tuple[str, str]:
    if not text.startswith("---\n"):
        return "", text
    closing = text.find("\n---", 4)
    if closing == -1:
        return "", text
    after_closing = closing + len("\n---")
    if after_closing < len(text) and text[after_closing] == "\n":
        after_closing += 1
    return text[4:closing], text[after_closing:].lstrip("\n")


def strip_frontmatter(text: str) -> str:
    return extract_frontmatter(text)[1].lstrip("\n")


def validate_note_file(path: Path) -> list[ValidationIssue]:
    return validate_note_text(path.read_text(encoding="utf-8"))


def validate_note_text(text: str) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    frontmatter, body = extract_frontmatter(text)
    if not frontmatter:
        issues.append(
            ValidationIssue("missing-frontmatter", "YAML frontmatter is missing", 1)
        )
    else:
        _validate_frontmatter(frontmatter, issues)
    _validate_body(body, issues, frontmatter)
    return issues


def _validate_frontmatter(frontmatter: str, issues: list[ValidationIssue]) -> None:
    fields = _parse_frontmatter(frontmatter)
    tool = fields["scalars"].get("tool")
    if tool is None or _strip_quotes(tool[0]) != TOOL_URL:
        issues.append(
            ValidationIssue(
                "invalid-tool",
                f'tool must equal "{TOOL_URL}"',
                tool[1] if tool else 1,
            )
        )

    agent = fields["scalars"].get("agent")
    if not agent or not _is_scalar_string(agent[0]):
        issues.append(
            ValidationIssue("missing-agent", "agent must be a scalar string", 1)
        )

    topic = fields["scalars"].get("topic")
    if not topic:
        issues.append(
            ValidationIssue("missing-topic", "topic must be a scalar string", 1)
        )
    elif not _is_scalar_string(topic[0]) or _has_unquoted_colon_space(topic[0]):
        issues.append(
            ValidationIssue(
                "invalid-topic",
                "topic with colon-space must be quoted",
                topic[1],
            )
        )

    for value, line in fields["lists"].get("web_refs", []):
        ref = _strip_quotes(value)
        if not ref.startswith(("http://", "https://")) or re.search(r"\s", ref):
            issues.append(
                ValidationIssue(
                    "invalid-web-ref",
                    "web_refs entries must be bare URLs without annotations",
                    line,
                )
            )

    for value, line in fields["lists"].get("library_refs", []):
        if not _is_quoted(value) and re.match(r"^[^:]+:\s+", value):
            issues.append(
                ValidationIssue(
                    "invalid-library-ref",
                    "library_refs entries must be strings, not YAML mappings",
                    line,
                )
            )


def _validate_body(body: str, issues: list[ValidationIssue], frontmatter: str) -> None:
    lines = body.splitlines()
    line_offset = len(frontmatter.splitlines()) + 2 if frontmatter else 0

    for line_number, line in enumerate(lines, start=1 + line_offset):
        if "[REJECTED]" in line:
            issues.append(
                ValidationIssue(
                    "rejected-citation",
                    "body contains a [REJECTED] citation tag",
                    line_number,
                )
            )

    series_body = any(_SERIES_HEADING_RE.match(line.strip()) for line in lines)
    for heading in REQUIRED_SECTIONS:
        if any(line.strip() == heading for line in lines):
            continue
        if heading in SOFT_SECTIONS and series_body:
            continue
        hint = _SECTION_HINTS.get(heading)
        message = f"required section missing: {heading}"
        if hint:
            message = f"{message} ({hint})"
        issues.append(
            ValidationIssue(
                "missing-section",
                message,
                1 + line_offset,
                "warning" if heading in SOFT_SECTIONS else "error",
            )
        )

    if _section_has_content(lines, "## Canon Evidence (T1)") and not _list_items(
        frontmatter, "canon_refs"
    ):
        issues.append(
            ValidationIssue(
                "missing-canon-ref",
                "canon_refs must include an entry when canon evidence is cited",
                1,
            )
        )

    footer_index = _final_footer_index(lines)
    footnote_defs = 0
    blockquote_lines = 0
    for index, line in enumerate(lines):
        if re.match(r"^\[\^[^\]]+\]:", line):
            footnote_defs += 1
            if index < footer_index:
                issues.append(
                    ValidationIssue(
                        "invalid-footnote-placement",
                        "footnote definitions must appear after the final footer area",
                        index + 1 + line_offset,
                    )
                )
        elif line.lstrip().startswith(">"):
            blockquote_lines += 1

    if footnote_defs >= 3 and blockquote_lines < footnote_defs:
        issues.append(
            ValidationIssue(
                "under-quoted-evidence",
                f"note has {footnote_defs} footnote definitions but only {blockquote_lines} blockquote lines (under-quoted evidence)",
                1 + line_offset,
                "error",
            )
        )


def _parse_frontmatter(frontmatter: str) -> FrontmatterFields:
    scalars: dict[str, tuple[str, int]] = {}
    lists: dict[str, list[tuple[str, int]]] = {}
    current_list: str | None = None
    for line_number, raw_line in enumerate(frontmatter.splitlines(), start=2):
        stripped = raw_line.strip()
        if not stripped:
            continue
        if stripped.startswith("- ") and current_list:
            lists.setdefault(current_list, []).append(
                (stripped[2:].strip(), line_number)
            )
            continue
        current_list = None
        match = re.match(r"^([A-Za-z_][A-Za-z0-9_]*):(.*)$", raw_line)
        if not match:
            continue
        key = match.group(1)
        value = match.group(2).strip()
        if value:
            scalars[key] = (value, line_number)
        else:
            current_list = key
            lists.setdefault(key, [])
    return {"scalars": scalars, "lists": lists}


def _strip_quotes(value: str) -> str:
    value = value.strip()
    if _is_quoted(value):
        return value[1:-1]
    return value


def _is_quoted(value: str) -> bool:
    value = value.strip()
    return len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}


def _is_scalar_string(value: str) -> bool:
    stripped = value.strip()
    return bool(stripped) and not stripped.startswith(("{", "[", "- "))


def _has_unquoted_colon_space(value: str) -> bool:
    stripped = value.strip()
    if len(stripped) >= 2 and stripped[0] == stripped[-1] and stripped[0] in {"'", '"'}:
        return False
    return ": " in stripped


def _list_items(frontmatter: str, key: str) -> list[tuple[str, int]]:
    return _parse_frontmatter(frontmatter)["lists"].get(key, [])


def _section_has_content(lines: list[str], heading: str) -> bool:
    in_section = False
    for line in lines:
        if line.strip() == heading:
            in_section = True
            continue
        if in_section and line.startswith("## "):
            return False
        if in_section and line.strip() and not line.strip().startswith("- None"):
            return True
    return False


def _final_footer_index(lines: list[str]) -> int:
    for index in range(len(lines) - 1, -1, -1):
        if lines[index].strip() == "---":
            return index
    return len(lines)
