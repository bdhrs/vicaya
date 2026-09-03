# Tech — Vicaya

## Tools & Platforms
- **Runtime:** Python 3.13+, managed with `uv`
- **Agent integration:** Markdown skill files under `skill/*/SKILL.md`, symlinked into each
  agent's skills directory (Claude Code, OpenCode, Antigravity, Pi coding agent — see README
  Setup). Pi additionally needs `~/.pi/agent/prompts/<name>.md` pointed at a small stub in
  `config/pi/prompts/<name>.md` (not directly at `SKILL.md`), so its bare `/name <args>` form
  forwards the typed argument via Pi's `$ARGUMENTS` placeholder. `just sync` keeps both symlink
  sets current and prefers a stub when one exists.
- **Canon search:** SQLite (`tipitaka-translation-data.db`) via stdlib `sqlite3`
- **Vault I/O:** Obsidian CLI v1.12.7+ (subcommand-style; requires desktop app running)
- **Library folders search:** one or more document trees (including Calibre libraries) indexed into a user-controlled local SQLite FTS5 database via `tools/library_folders.py`. When a folder contains `metadata.db` it is recognised as a Calibre library and author/tag metadata is prepended to each book's FTS text automatically. Refresh walks all configured roots and extracts stdlib-supported text (incl. `.mht`/`.mhtml` via the `email` module and `.pptx` via the zip reader) plus optional local tools (`pdftotext`, `textutil`, `antiword`, `catdoc`, and `ebook-convert` for the Kindle/Mobipocket family — `.mobi`/`.azw3`/`.azw`/`.prc`/`.lit`/`.pdb`/`.chm` — plus `.rtf`). PDFs are extracted with `pdftotext` in reading-order mode (no `-layout`, which interleaved two-column books line-by-line); when pdftotext yields no text (scans, broken text layers), a fallback runs [pdf-inspector](https://github.com/firecrawl/pdf-inspector) selective OCR in a timeout-bounded subprocess over the first 150 pages — see **PDF OCR fallback** below. `.zip`, `.bz2`, and `.7z` archives are indexed as one document each by routing every text-bearing member back through the same extractor dispatch and concatenating the result, bounded by per-archive caps of 5,000 members, 2 GB uncompressed, and 300 s wall-clock (noise/encrypted/nested-archive members are skipped). Normal search queries the local index only. Refresh skips files with unchanged size+mtime, so after adding extractor support the previously-failed rows must be retried with `library-folders-refresh --retry-failed` (re-extracts only docs whose status does not start with `ok`; steady-state refresh stays instant).
- **YouTube:** `yt-dlp` for search, `youtube-transcript-api` for transcript fetch
- **Note validation:** `scripts/validate_note.py` uses `tools/note_checks.py` for final-note mechanical checks
- **PDF generation:** `scripts/generate_note_pdf.py` renders optional final-note PDFs with `markdown` and `weasyprint`
- **Web:** `WebSearch` / `WebFetch` (Claude Code built-ins)
- **Cross-check:** `cross_check()` tries each `app:model` entry in `$VICAYA_CROSS_CHECK_CHAIN` (`.env`, pipe-separated) in order via subprocess — `opencode run -m <model> <prompt>`, `agy --print <prompt> --model <model>`, or `pi -p --model <provider/id>[:thinking] --no-tools --no-session --no-extensions --no-skills --offline --no-context-files <prompt>` (pi pins the no-agent flags so the entry is a pure model call; credentials come from pi's own key store, i.e. the original Z.ai/DeepSeek APIs, not OpenRouter; a `:thinking` suffix passes through to pi's `--model` — pin it, because an unpinned entry inherits the machine `defaultThinkingLevel=max` and a 30 KB review then takes 12–17 min instead of 1–2). First entry to exit 0 with non-empty stdout wins. On empty/unset chain or every entry failing, returns a `# SELF_REVIEW:` sentinel so the calling agent runs the Phase 6 checklist on its own synthesis. No HTTP/SDK dep; vicaya stores no provider API keys — the chain app must already be authenticated out-of-band.
- **Sanskrit search:** `grep -rn -F --include="*.htm"` across a local GRETIL corpus (shallow clone of `wujastyk/GRETIL-mirror`). Unicode IAST `.htm` files; no new dependencies.
- **Validation:** pytest, ruff, pyright, pyrefly

## PDF OCR fallback
Scanned or broken-layer PDFs (pdftotext returns no text) fall back to
[pdf-inspector](https://github.com/firecrawl/pdf-inspector) selective OCR at
refresh time. `pdf-inspector` + `onnxruntime` are main dependencies (an
optional extra was tried and removed: any bare `uv sync` silently strips
extras, silently losing OCR). The OCR runs in a dedicated subprocess per file
so an engine hang cannot stall a refresh. The subprocess entry point is
`_OCR_WORKER_SNIPPET`, which drives
`tools/library_folders.py::_ocr_worker_chunks`; the parent collects the replies
in `_collect_ocr_chunks`. Each chunk is bounded separately — see the per-chunk
timeout below, which is the live bound; `OCR_SUBPROCESS_TIMEOUT` (1800 s) is
only a whole-file backstop. Work per file is additionally capped at the first
`OCR_PAGE_CAP` pages (150, ~1 s/page measured); set
`VICAYA_LIBRARY_FOLDERS_OCR=0` to skip the fallback for fast text-only
refreshes.

When the page cap cuts a book short the row's status records it —
`ok: ocr truncated at 150 of 600 pages` — so partially-indexed books stay
queryable instead of being indistinguishable from fully-indexed ones. Such a
row counts as a success, not a failure: `--retry-failed` deliberately leaves it
alone (`_should_skip` treats any `ok…` status as done), because re-running would
redo the same capped pages. Finishing a capped book means a deliberate re-run at
a raised `OCR_PAGE_CAP`.

The worker streams one framed reply per 10-page chunk rather than one reply
per file. Each reply is framed with `_OCR_REPLY_MARKER` because pdf-inspector,
onnxruntime and PDFium all print to the child's stdout, and an unframed reply
would be corrupted by a single warning line.

Streaming per chunk is what allows a per-chunk deadline. `OCR_CHUNK_TIMEOUT`
(120 s, against a slowest measured chunk of 20 s) bounds each chunk instead of
bounding the whole file; `OCR_SUBPROCESS_TIMEOUT` remains a whole-file
backstop. When a chunk stalls, the pages already OCR'd are kept and the status
records `partial: ocr stalled at page N of M`. That status is deliberately
*not* an `ok…` one: stalls are intermittent — both books measured as stalling
on 2026-09-03 completed cleanly on the next attempt — so a stalled row keeps
its partial text but stays retryable, and `--retry-failed` will usually finish
it. A page-cap truncation is the opposite case: deterministic, so it stays
`ok…` and is skipped. This matters: measured on 2026-09-03, 2 of 12 random
scanned books stalled mid-book on that attempt, and the previous whole-file
timeout charged 1800 s and then discarded everything — one book lost 130 of 150
successfully OCR'd pages. Over the library's ~2,000 scanned books this is the
difference between roughly 240 h with 338 books unindexed and roughly 87 h with
none. Full numbers, including a tesseract comparison, are in the thread's
`measurements.md`.

The chunk reader is a thread feeding a queue, not a poll on the pipe: a wedged
worker leaves the read blocked indefinitely, so only a separate thread lets the
deadline fire.

Two things about OCR remain unverified against real data, both recorded here so
nobody assumes otherwise. The stall-recovery path has never fired against a
real wedged worker — both books measured as stalling completed when re-run, so
`partial: ocr stalled …` is covered by unit tests with a faked worker only, and
a full library rebuild is its first live exercise. And every timing measured
was warm-start, with the OCR models already cached; cold start, including the
one-time model download, is why the first chunk gets
`OCR_FIRST_CHUNK_TIMEOUT` rather than the ordinary bound.

A full rebuild is two passes, in order: `just lf-refresh-text` (every file, OCR
off, fast) then `just lf-refresh-retry` (only the rows pass 1 could not read,
OCR on, hours). The order is stated in the justfile header and in both recipe
doc-comments.

Because an OCR pass runs for hours, the index is opened in WAL mode and the
refresh commits every `REFRESH_COMMIT_SECONDS` (30 s) instead of once at the
end: an interrupted run keeps the files it finished, and a search can read the
index while a refresh is writing it.

**Install:**
1. `uv sync` — OCR deps are main dependencies; nothing extra needed.
2. PDFium shared library (not managed by uv): download the
   `pdfium-linux-x64.tgz` from [bblanchon/pdfium-binaries
   releases](https://github.com/bblanchon/pdfium-binaries/releases), extract
   `lib/libpdfium.so` to `~/.local/lib/pdfium/`, and set
   `PDFIUM_LIB_PATH="$HOME/.local/lib/pdfium/libpdfium.so"` in `.env`.
3. `ORT_DYLIB_PATH` is auto-located from the installed onnxruntime wheel; no
   setup needed.
4. The OCR model set is downloaded automatically on the first routed page
   (needs network once, then cached).

**Verify it works:**
```bash
set -a; . ./.env; set +a
uv run python -c "
from pathlib import Path
from tools import library_folders as lf
r = lf._extract_pdf(Path('<a known scanned pdf>'))
print(r.status, len(r.text))  # expect: ok <nonzero>
"
```

**Update:** `uv lock --upgrade-package pdf-inspector --upgrade-package
onnxruntime && uv sync` keeps the Python side current within the `<2` pin.
PDFium is not managed by uv — re-download the latest release tarball to the
same path occasionally. Bump the pin deliberately when a major version lands.

**Gotcha (fixed 2026-09-02, watch for recurrence):** `.venv/bin/*` console
scripts once had shebangs pointing at another project's venv
(`research-hub`), so `uv run pytest` silently ran under a foreign interpreter
— deps like weasyprint/pdf-inspector "missing" in tests only. If tests fail
to import venv packages, check `head -1 .venv/bin/pytest` and reinstall the
package that owns the script.

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
- Optional PDF output: `$VICAYA_PDF_PATH` is an on/off toggle (any non-empty value enables it); every PDF is written into the single `Vicaya/PDF/` tree, whose subfolders mirror the notes' own vault subfolders (`Vicaya/Digest/x.md` → `Vicaya/PDF/Digest/x.pdf`) — this var is not read as an output path. `tools/note_checks.resolve_pdf_path` owns the mapping
- Library folders: one or more source paths (pipe-separated) in `$VICAYA_LIBRARY_FOLDERS`; index: local SQLite path in `$VICAYA_LIBRARY_FOLDERS_INDEX`; optional comma-separated skip list in `$VICAYA_LIBRARY_FOLDERS_EXCLUDE`
- YouTube cache: `data/youtube_cache/` (gitignored, grows over time)
- Channel allowlist: `data/youtube_channels.md`

## Documentation Ownership
- `tools/research_sources.py`: actual helper behavior and CLI implementation (library-folders commands delegate to `tools/library_folders.py`).
- `tools/align_translations.py`: standalone Pāḷi word/phrase translator-comparison tool (issue #23). Deterministic Bilara segment alignment (root Pāḷi + English authors share one segment key); locates the sutta and lists EBC translator files for the agent to read. On a phrase spanning >1 sutta with no `--in`, prints `AMBIGUOUS` and stops — never guesses. Prints a Markdown table to stdout; reuses `research_sources` helpers; no new deps. Agent procedure lives in `skill/vicaya-align/SKILL.md`.
- `skill/vicaya-align/SKILL.md`: agent procedure for the translation aligner — run the tool, ask the user on `AMBIGUOUS`, read EBC files to fill those rows.
- `skill/vicaya/SKILL.md`: canonical agent workflow and source-use procedure.
- `skill/vicaya-pdf/SKILL.md`: the PDF folder standard plus the audit/repair procedure; wraps `scripts/sync_note_pdfs.py`.
- `scripts/sync_note_pdfs.py`: audits the notes against the `Vicaya/PDF/` tree and, with `--fix`, generates the missing twins and deletes the orphans (any file in the tree that is not a current note's PDF). Reuses `note_checks.resolve_pdf_path` for the mapping and `generate_note_pdf.render_pdf` for rendering.
- `skill/vicaya-digest/SKILL.md`: plain-English quick-study essay skill (`/vicaya-digest <topic>`) — Monarch Notes/CliffsNotes-style summary, no phase gates, no inline citations, writes into `<vault>/Vicaya Digest/`.
- `README.md`: user-facing setup and project overview.
- `kamma/tech.md`: architecture summary, constraints, and resource map.
- `skill/vicaya/README.md`: short skill-package overview; link to `SKILL.md`
  for detailed behavior instead of duplicating it.

## Output shape
A single `.md` file per research session written into `<vault>/Vicaya/`.
Source helpers return plain Python lists-of-dicts; no external I/O inside helpers.
`digest` writes into a separate `<vault>/Vicaya Digest/` folder — a different
output shape (short plain-English essay, no citation fields) from the
research notes above.
