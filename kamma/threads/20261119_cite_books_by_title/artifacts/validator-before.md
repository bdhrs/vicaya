# Validator before migration (task 3.1, 2026-11-19)

The new hard `library-number` check (`tools/note_checks.py`) run over every note in `<vault>/Vicaya` (top level), `Christianity Comparative/`, `What the Suttas Say About/` and `Digest/` that has `library_refs` or a finding. Read-only; scan script in the session scratchpad.

- Notes scanned: 360 (the spec's 360). Notes with findings: 335. Lines flagged: 9096.
- Notes with findings per folder: Vicaya (top level) 286; What the Suttas Say About 37; Christianity Comparative 12. `Digest/` has none.
- 25 notes have `library_refs` but no number anywhere.

## Twelve random findings, read

All twelve are library numbers: `(Calibre #19588)`, `(Calibre #10836)`, `(Calibre #3363)`, a `library_refs` entry `"905: A History of Mindfulness — Bhikkhu Sujato"`, four `[^calibre-…]` footnote definitions, `(Calibre #1336)`, `(Calibre #634)`, a `[^calibre-cittavithi]` marker (a calibre label without a number, still the old scheme), and `(library doc 1863)`.
