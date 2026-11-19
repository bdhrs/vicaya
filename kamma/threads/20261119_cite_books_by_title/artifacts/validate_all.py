"""Validator findings for every migrated-candidate note, as JSON (tasks 4.2, 4.3).

Read-only. `uv run kamma/threads/20261119_cite_books_by_title/artifacts/validate_all.py OUT.json`
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from migrate_library_citations import _notes, _vault  # noqa: E402

from tools import note_checks  # noqa: E402

vault = _vault()
out = {
    str(path.relative_to(vault)): sorted(
        [i.code, i.severity, i.message]
        for i in note_checks.validate_note_text(path.read_text(encoding="utf-8"))
    )
    for path in _notes(vault)
}
Path(sys.argv[1]).write_text(
    json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8"
)
print(len(out), "notes")
