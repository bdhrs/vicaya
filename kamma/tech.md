# Tech — Vicaya

## Tools & Platforms
- **Runtime:** Python 3.13+, managed with `uv`
- **Agent integration:** Claude Code skill (Markdown skill file at `skill/vicaya/SKILL.md`),
  symlinked to `~/.claude/skills/vicaya/`
- **Canon search:** SQLite (`tipitaka-translation-data.db`) via stdlib `sqlite3`
- **Vault I/O:** Obsidian CLI v1.12.7+ (subcommand-style; requires desktop app running)
- **Library folders search:** one or more document trees (including Calibre libraries) indexed into a user-controlled local SQLite FTS5 database via `tools/library_folders.py`. When a folder contains `metadata.db` it is recognised as a Calibre library and author/tag metadata is prepended to each book's FTS text automatically. Refresh walks all configured roots and extracts stdlib-supported text (incl. `.mht`/`.mhtml` via the `email` module and `.pptx` via the zip reader) plus optional local tools (`pdftotext`, `textutil`, `antiword`, `catdoc`, and `ebook-convert` for the Kindle/Mobipocket family — `.mobi`/`.azw3`/`.azw`/`.prc`/`.lit`/`.pdb`/`.chm` — plus `.rtf`). `.zip`, `.bz2`, and `.7z` archives are indexed as one document each by routing every text-bearing member back through the same extractor dispatch and concatenating the result, bounded by per-archive caps of 5,000 members, 2 GB uncompressed, and 300 s wall-clock (noise/encrypted/nested-archive members are skipped). Normal search queries the local index only. Refresh skips files with unchanged size+mtime, so after adding extractor support the previously-failed rows must be retried with `library-folders-refresh --retry-failed` (re-extracts only docs whose status is not `ok`; steady-state refresh stays instant).
- **YouTube:** `yt-dlp` for search, `youtube-transcript-api` for transcript fetch
- **Note validation:** `scripts/validate_note.py` uses `tools/note_checks.py` for final-note mechanical checks
- **PDF generation:** `scripts/generate_note_pdf.py` renders optional final-note PDFs with `markdown` and `weasyprint`
- **Web:** `WebSearch` / `WebFetch` (Claude Code built-ins)
- **Cross-check:** `cross_check()` POSTs to OpenRouter (model list in `data/openrouter_models.json` — server-side fallback via the `models: [...]` field, cap 3). Current lead: `deepseek/deepseek-v4-flash` (paid, ~22s, ~$0.0001/call); free `gpt-oss-120b:free` as outage backup. On any failure returns a `# SELF_REVIEW:` sentinel so the calling agent runs the Phase 6 checklist on its own synthesis. Stdlib `urllib`; no SDK dep. Key from `OPENROUTER_API_KEY` env / `.env`, or `~/.local/share/opencode/auth.json` → `.openrouter.key`.
- **Sanskrit search:** `grep -rn -F --include="*.htm"` across a local GRETIL corpus (shallow clone of `wujastyk/GRETIL-mirror`). Unicode IAST `.htm` files; no new dependencies.
- **Validation:** pytest, ruff, pyright, pyrefly

## Validation Scope
- For routine code or documentation changes, run only checks scoped to the
  touched files.
- Do not run project-wide validation unless the user asks or an approved plan
  requires it.
- Prohibited by default: `uv run pytest`, `uv run pytest -q`,
  `uv run ruff check .`, bare `uv run pyright`, bare
  `uv run pyrefly check`.
- Preferred checks: `uv run pytest tests/<specific_test_file>.py -q`,
  `uv run ruff check <changed files>`,
  `uv run pyright <changed files>`,
  `uv run pyrefly check --search-path . <changed files>`.
- After touching any `.py` file, run the concrete scoped bundle before
  finalizing:
  - `uv run ruff check <changed .py files>`
  - `uv run pyright <changed .py files>`
  - `uv run pyrefly check --search-path . <changed .py files>`
  - `uv run pytest <relevant test file> -q`

## Constraints
- All paths are per-machine; configured via `.env` (not committed). See `.env.example`.
- Obsidian CLI requires the desktop app to be open; skill launches it automatically.
- Library folders indexes must live outside the repo. Searches must not walk or read the source tree; only refresh and manual inspection touch source files.
- Exact byte/text duplicates are collapsed by default in library-folders search, while filename-only matches remain `possible_duplicate_of` hints.
- `yt-dlp` 2024.04.09 cannot fetch captions; `youtube-transcript-api` is used instead.
- No vector RAG. Local corpora are structured enough that SQL + tag search + vault search
  is more precise than embeddings.
- `skill/vicaya/SKILL.md` is the canonical full-run skill.

## Resources
- Canon DB: `<dpd-db>/resources/tipitaka_translation_db/tipitaka-translation-data.db`
- DPD DB: `<dpd-db>/dpd.db` — used by `resolve_citation` to map CST codes → human refs via `sutta_info` table
- CST book translator: `<dpd-db>/tools/cst_book_translator.py` + `.tsv` — used by `lookup_book` to translate between cst_filename / SQLite table name / Pāḷi title / gui code / DPD code. Live-imported via file path.
- Vault: path in `$VICAYA_VAULT_PATH`, vault name `$VICAYA_VAULT_NAME`
- Optional PDF output: path in `$VICAYA_PDF_PATH`
- Library folders: one or more source paths (pipe-separated) in `$VICAYA_LIBRARY_FOLDERS`; index: local SQLite path in `$VICAYA_LIBRARY_FOLDERS_INDEX`; optional comma-separated skip list in `$VICAYA_LIBRARY_FOLDERS_EXCLUDE`
- YouTube cache: `data/youtube_cache/` (gitignored, grows over time)
- Channel allowlist: `data/youtube_channels.md`

## Documentation Ownership
- `tools/research_sources.py`: actual helper behavior and CLI implementation (library-folders commands delegate to `tools/library_folders.py`).
- `tools/align_translations.py`: standalone Pāḷi word/phrase translator-comparison tool (issue #23). Deterministic Bilara segment alignment (root Pāḷi + English authors share one segment key); locates the sutta and lists EBC translator files for the agent to read. On a phrase spanning >1 sutta with no `--in`, prints `AMBIGUOUS` and stops — never guesses. Prints a Markdown table to stdout; reuses `research_sources` helpers; no new deps. Agent procedure lives in `skill/align/SKILL.md`.
- `skill/align/SKILL.md`: agent procedure for the translation aligner — run the tool, ask the user on `AMBIGUOUS`, read EBC files to fill those rows.
- `skill/vicaya/SKILL.md`: canonical agent workflow and source-use procedure.
- `README.md`: user-facing setup and project overview.
- `kamma/tech.md`: architecture summary, constraints, and resource map.
- `skill/vicaya/README.md`: short skill-package overview; link to `SKILL.md`
  for detailed behavior instead of duplicating it.

## Output shape
A single `.md` file per research session written into `<vault>/Vicaya/`.
Source helpers return plain Python lists-of-dicts; no external I/O inside helpers.
