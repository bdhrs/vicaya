# Tech — Vicaya

## Tools & Platforms
- **Runtime:** Python 3.13+, managed with `uv`
- **Agent integration:** Claude Code skill (Markdown skill file at `skill/vicaya/SKILL.md`),
  symlinked to `~/.claude/skills/vicaya/`
- **Canon search:** SQLite (`tipitaka-translation-data.db`) via stdlib `sqlite3`
- **Vault I/O:** Obsidian CLI v1.12.7+ (subcommand-style; requires desktop app running)
- **Library search:** metadata search reads `metadata.db` directly via read-only `sqlite3` (lock-free, concurrent-safe; falls back to `calibredb list` on schema mismatch); FTS still uses `calibredb` (Calibre 9+) when indexed
- **YouTube:** `yt-dlp` for search, `youtube-transcript-api` for transcript fetch
- **Note validation:** `scripts/validate_note.py` uses `tools/note_checks.py` for final-note mechanical checks
- **PDF generation:** `scripts/generate_note_pdf.py` renders optional final-note PDFs with `markdown` and `weasyprint`
- **Web:** `WebSearch` / `WebFetch` (Claude Code built-ins)
- **Cross-check:** `cross_check()` POSTs to OpenRouter (model list in `data/openrouter_models.json` — server-side fallback via the `models: [...]` field, cap 3). Current lead: `deepseek/deepseek-v4-flash` (paid, ~22s, ~$0.0001/call); free `gpt-oss-120b:free` as outage backup. On any failure returns a `# SELF_REVIEW:` sentinel so the calling agent runs the Phase 6 checklist on its own synthesis. Stdlib `urllib`; no SDK dep. Key from `OPENROUTER_API_KEY` env / `.env`, or `~/.local/share/opencode/auth.json` → `.openrouter.key`.
- **Sanskrit search:** `grep -rn -F --include="*.htm"` across a local GRETIL corpus (shallow clone of `wujastyk/GRETIL-mirror`). Unicode IAST `.htm` files; no new dependencies.
- **Validation:** pytest, ruff, pyright, pyrefly

## Python File Validation
After touching any `.py` file, run the concrete scoped bundle before finalizing:
- `uv run ruff check <changed .py files>`
- `uv run pyright <changed .py files>`
- `uv run pyrefly check --search-path . <changed .py files>`
- `uv run pytest <relevant test file> -q`

## Constraints
- All paths are per-machine; configured via `.env` (not committed). See `.env.example`.
- Obsidian CLI requires the desktop app to be open; skill launches it automatically.
- Calibre FTS indexing is a background process that takes days on a large library.
- `yt-dlp` 2024.04.09 cannot fetch captions; `youtube-transcript-api` is used instead.
- No vector RAG. Local corpora are structured enough that SQL + tag search + vault search
  is more precise than embeddings.
- Maintenance coupling: `skill/vicaya/SKILL.md` is the canonical full-run
  skill. Edits to it must check the staged sibling skills
  (`skill/vicaya-0-scope`, `skill/vicaya-1-gather`,
  `skill/vicaya-2-synthesize-review`, `skill/vicaya-3-complete`) for affected
  route lists, stage boundaries, handoff labels, and bounded context-break
  guards. Edits to any staged sibling must verify exact routing back to
  `skill/vicaya/SKILL.md` and must not silently fork canonical workflow
  behavior.
- Staged sibling skills are router-only technical artifacts. They must not
  contain behavioral summaries or depend on `skill/vicaya/shared/`; after any
  canonical heading or staged route-list change, run a focused route-heading
  audit before review or finalize.

## Resources
- Canon DB: `<dpd-db>/resources/tipitaka_translation_db/tipitaka-translation-data.db`
- DPD DB: `<dpd-db>/dpd.db` — used by `resolve_citation` to map CST codes → human refs via `sutta_info` table
- CST book translator: `<dpd-db>/tools/cst_book_translator.py` + `.tsv` — used by `lookup_book` to translate between cst_filename / SQLite table name / Pāḷi title / gui code / DPD code. Live-imported via file path.
- Vault: path in `$VICAYA_VAULT_PATH`, vault name `$VICAYA_VAULT_NAME`
- Optional PDF output: path in `$VICAYA_PDF_PATH`
- Calibre library: path in `$VICAYA_CALIBRE_LIBRARY`
- YouTube cache: `data/youtube_cache/` (gitignored, grows over time)
- Channel allowlist: `data/youtube_channels.md`

## Documentation Ownership
- `tools/research_sources.py`: actual helper behavior and CLI implementation.
- `skill/vicaya/SKILL.md`: canonical agent workflow and source-use procedure.
- `README.md`: user-facing setup and project overview.
- `kamma/tech.md`: architecture summary, constraints, and resource map.
- `skill/vicaya/README.md`: short skill-package overview; link to `SKILL.md`
  for detailed behavior instead of duplicating it.

## Output shape
A single `.md` file per research session written into `<vault>/Vicaya/`.
Source helpers return plain Python lists-of-dicts; no external I/O inside helpers.
