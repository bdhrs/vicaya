# Plan — Translation Aligner

**GitHub issue:** #23

## Tasks

### Phase 1 — Deterministic tool
- [x] T1: `tools/align_translations.py` — parse args (`--phrase`, `--in`),
  reuse helpers from `research_sources`.
- [x] T2: Bilara phrase locator — grep root Pāḷi, parse `(uid, segment_key)`
  from each hit; group by uid.
- [x] T3: Disambiguation gate — `--in` filter; else >1 uid → `AMBIGUOUS` + stop.
- [x] T4: Bilara aligned-pull — for chosen uid + matched keys, read root Pāḷi and
  each English author JSON; build Pāḷi + translator rows.
- [x] T5: EBC file discovery — glob `+Suttas/Sutta Texts/**/<uid>-*.md` and
  `<uid>.md`; translator label = top folder.
- [x] T6: Render — print header line, Markdown table, EBC source list to stdout.

### Phase 2 — Tests
- [x] T7: `tests/test_align_translations.py` — fixtures for a tiny Bilara tree +
  EBC tree; cover key parsing, single-sutta table, ambiguous→stop, `--in` scope,
  EBC discovery, no-match.

### Phase 3 — Integration
- [x] T8: Minimal `skill/align/SKILL.md` — run tool, on `AMBIGUOUS` ask the user
  for context, read listed EBC files, extract each translator's rendering, emit
  the combined table. Symlink note for `~/.claude/skills/` left to user.
- [x] T9: Update `kamma/tech.md` (new tool + doc ownership) and `README` pointer.

### Phase 4 — Verify & finalize
- [x] T10: Scoped checks — `ruff`, `pyright`, `pyrefly`, pytest on new files.
- [~] T11: Review done (range-file bug found + fixed). Finalize + close issue #23 pending user go-ahead.
