"""Validate a final Vicaya note before publication."""

from __future__ import annotations

import argparse
import importlib.util
import os
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


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("note", help="Note path or Vicaya-relative note path")
    args = parser.parse_args(argv)

    env = {**note_checks.load_dotenv(Path(".env")), **os.environ}
    note_arg = str(args.note)
    try:
        note_path = note_checks.resolve_existing_note(note_arg, env)
        issues = note_checks.validate_note_file(note_path)
    except OSError as exc:
        print(f"{note_arg}: error: {exc}")
        return 2
    except ValueError as exc:
        print(f"{note_arg}: error: {exc}")
        return 2

    errors = [issue for issue in issues if issue.severity == "error"]
    for issue in issues:
        print(
            f"{note_path}:{issue.line}: {issue.severity}: {issue.code}: {issue.message}"
        )
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
