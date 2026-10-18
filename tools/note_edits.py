"""All-or-nothing text edits for a draft or vault note (issue #130).

Agents patch drafts with throwaway Python replace scripts. Those scripts
no-op when the target differs by one character, crash after printing
"patched", or die on an unescaped apostrophe, and the miss is found only
by a later grep. `apply_edits` refuses to write unless every target is
found, and reports what it did per edit.
"""

from __future__ import annotations

import io
import os
import tempfile
from pathlib import Path
from typing import Any


def _validate(edits: Any) -> str | None:
    if not isinstance(edits, list) or not edits:
        return "edits must be a non-empty JSON list of {old, new} objects"
    for i, edit in enumerate(edits, 1):
        if not isinstance(edit, dict):
            return f"edit {i} is not an object"
        if not isinstance(edit.get("old"), str) or not edit["old"]:
            return f"edit {i} needs a non-empty string 'old'"
        if not isinstance(edit.get("new"), str):
            return f"edit {i} needs a string 'new'"
    return None


def apply_edits(path: Path, edits: Any) -> dict[str, Any]:
    """Apply `edits` in order to the file at `path`, or change nothing.

    Each edit is `{"old": str, "new": str}`, plus `"all": true` to replace
    every occurrence. Without `all`, `old` must occur exactly once, so an
    ambiguous target is an error instead of a silent wrong match. Edits run
    in order on the running text, so a later edit sees an earlier one's
    result. Every failure is reported and no byte is written.
    """
    problem = _validate(edits)
    if problem:
        return {"ok": False, "error": problem}
    try:
        with io.open(path, encoding="utf-8", newline="") as fh:
            original = fh.read()
    except OSError as exc:
        return {"ok": False, "error": f"cannot read {path}: {exc}"}

    text = original
    report: list[dict[str, Any]] = []
    for i, edit in enumerate(edits, 1):
        old, new = edit["old"], edit["new"]
        count = text.count(old)
        replace_all = bool(edit.get("all"))
        if count == 0:
            status = "not-found"
        elif count > 1 and not replace_all:
            status = "ambiguous"
        else:
            status = "applied"
            text = text.replace(old, new)
        report.append(
            {
                "edit": i,
                "status": status,
                "occurrences": count,
                "old": old[:60],
                # A leftover copy of the old text means the claim is still
                # stated somewhere the edit did not reach.
                "old_remaining": text.count(old) if status == "applied" else None,
            }
        )
    failed = [r for r in report if r["status"] != "applied"]
    result: dict[str, Any] = {
        "ok": not failed,
        "path": str(path),
        "edits": report,
        "written": False,
    }
    if failed:
        result["error"] = (
            f"{len(failed)} of {len(report)} edits did not apply; "
            "the file was not changed"
        )
        return result
    if text != original:
        fd, tmp = tempfile.mkstemp(dir=path.parent, prefix=f".{path.name}.")
        try:
            with os.fdopen(fd, "w", encoding="utf-8", newline="") as fh:
                fh.write(text)
            os.chmod(tmp, path.stat().st_mode & 0o7777)
            os.replace(tmp, path)
        except BaseException:
            Path(tmp).unlink(missing_ok=True)
            raise
        result["written"] = True
    return result
