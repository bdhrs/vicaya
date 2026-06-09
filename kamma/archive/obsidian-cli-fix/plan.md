# Plan — obsidian-cli-fix

## Tasks

### Phase 1 — Code fix

- [x] 1.1 `research_sources.py`: in `search_vault`, raise `RuntimeError` on non-JSON CLI output instead of returning `[]`
- [x] 1.2 `skill/vicaya/SKILL.md`: replace Hard Rule 4 Linux launch line with `xdg-open "obsidian://"` and add Windows line

### Phase 2 — Tests

- [x] 2.1 Add/update test for `search_vault` non-JSON / error-stdout path in `tests/test_research_sources.py`

### Phase 3 — Validation

- [x] 3.1 Run: `uv run ruff check tools/research_sources.py`
- [x] 3.2 Run: `uv run pyright tools/research_sources.py`
- [x] 3.3 Run: `uv run pyrefly check --search-path . tools/research_sources.py`
- [x] 3.4 Run: `uv run pytest tests/test_research_sources.py -q` — 78 passed, 1 skipped
