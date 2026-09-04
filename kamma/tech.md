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
- **Library folders search:** one or more document trees (including Calibre libraries) indexed into a user-controlled local SQLite FTS5 database via `tools/library_folders.py`. When a folder contains `metadata.db` it is recognised as a Calibre library and author/tag metadata is prepended to each book's FTS text automatically. Refresh walks all configured roots and extracts stdlib-supported text (incl. `.mht`/`.mhtml` via the `email` module and `.pptx` via the zip reader) plus optional local tools (`pdftotext`, `textutil`, `antiword`, `catdoc`, and `ebook-convert` for the Kindle/Mobipocket family — `.mobi`/`.azw3`/`.azw`/`.prc`/`.lit`/`.pdb`/`.chm` — plus `.rtf`). PDFs are extracted with `pdftotext` in reading-order mode (no `-layout`, which interleaved two-column books line-by-line); when pdftotext yields no text (scans, broken text layers), a fallback shells out to the `ocrmypdf` binary over the whole book and reads its sidecar — see **PDF OCR fallback** below. `.zip`, `.bz2`, and `.7z` archives are indexed as one document each by routing every text-bearing member back through the same extractor dispatch and concatenating the result, bounded by per-archive caps of 5,000 members, 2 GB uncompressed, and 300 s wall-clock (noise/encrypted/nested-archive members are skipped). Normal search queries the local index only. Refresh skips files with unchanged size+mtime, so after adding extractor support the previously-failed rows must be retried with `library-folders-refresh --retry-failed` (re-extracts only docs whose status does not start with `ok`; steady-state refresh stays instant).
- **YouTube:** `yt-dlp` for search, `youtube-transcript-api` for transcript fetch
- **Note validation:** `scripts/validate_note.py` uses `tools/note_checks.py` for final-note mechanical checks
- **PDF generation:** `scripts/generate_note_pdf.py` renders optional final-note PDFs with `markdown` and `weasyprint`
- **Web:** `WebSearch` / `WebFetch` (Claude Code built-ins)
- **Cross-check:** `cross_check()` tries each `app:model` entry in `$VICAYA_CROSS_CHECK_CHAIN` (`.env`, pipe-separated) in order via subprocess — `opencode run -m <model> <prompt>`, `agy --print <prompt> --model <model>`, or `pi -p --model <provider/id>[:thinking] --no-tools --no-session --no-extensions --no-skills --offline --no-context-files <prompt>` (pi pins the no-agent flags so the entry is a pure model call; credentials come from pi's own key store, i.e. the original Z.ai/DeepSeek APIs, not OpenRouter; a `:thinking` suffix passes through to pi's `--model` — pin it, because an unpinned entry inherits the machine `defaultThinkingLevel=max` and a 30 KB review then takes 12–17 min instead of 1–2). First entry to exit 0 with non-empty stdout wins. On empty/unset chain or every entry failing, returns a `# SELF_REVIEW:` sentinel so the calling agent runs the Phase 6 checklist on its own synthesis. No HTTP/SDK dep; vicaya stores no provider API keys — the chain app must already be authenticated out-of-band.
- **Sanskrit search:** `grep -rn -F --include="*.htm"` across a local GRETIL corpus (shallow clone of `wujastyk/GRETIL-mirror`). Unicode IAST `.htm` files; no new dependencies.
- **Validation:** pytest, ruff, pyright, pyrefly

## PDF OCR fallback
Scanned or broken-layer PDFs (pdftotext returns no text) are OCR'd at refresh time by shelling out to the [`ocrmypdf`](https://ocrmypdf.readthedocs.io/) binary, which wraps tesseract. `tools/library_folders.py::_extract_pdf_ocr_fallback` runs it once per book with `--force-ocr --jobs 12 --optimize 0 --output-type pdf --sidecar <tmp>` and the output PDF sent to `/dev/null` — only the sidecar text is wanted, and writing a searchable copy of every scanned book would cost tens of gigabytes for nothing. Set `VICAYA_LIBRARY_FOLDERS_OCR=0` to skip the fallback for fast text-only refreshes.

`ocrmypdf` is an **apt package, not a uv dependency** — `uv sync` will not install it. An absent binary is therefore the normal state on a fresh machine, so `_extract_pdf_ocr_fallback` probes `shutil.which("ocrmypdf")` and returns `None` when it is missing, mirroring the `pdftotext` probe in the same file. Returning `None` is load-bearing: it makes the caller keep pdftotext's own status instead of writing an OCR error over every scanned PDF in the library. The kill switch above is a separate thing — an explicit user opt-out, not the availability probe.

### Why this engine
Chosen by measurement on 2026-09-03 against the previous pipeline ([pdf-inspector](https://github.com/firecrawl/pdf-inspector) + `onnxruntime` + PDFium behind a bespoke chunk-streaming subprocess worker) and against calling tesseract directly. Full numbers in `kamma/archive/20260903_ocr_bakeoff/measurements.md`.

| | projected for 263,524 pages | memory per unit | books stalled | word accuracy (folded) |
|---|---:|---:|---:|---:|
| **ocrmypdf** | **1.32 days** | 488 MB | 0 of 22 | 91.7 % |
| pdf-inspector (previous) | 4.31 days (user observed 6) | 5.0 GB | 4 of 22 | 96.1 % |
| tesseract direct | 10.8 days | ~900 MB | 1 of 22 | 92.0 % |

The 10× memory drop is what matters most in practice: the previous engine's 5.0 GB per book capped the refresh at 3-way parallelism, which is why it was slow. Treat **0.433 s/page as an unreplicated figure** — the one repeat run came in at 0.528 s/page, which would put the like-for-like margin at 2.68× rather than 3.27×. Measured again on 2026-09-04 through the shipped code path, with `--optimize 0` and the output PDF discarded: **0.627 s/page** on a 708-page book (1.6 M characters), 0.972 s/page on "Chanakya" (a known outlier for every candidate), 0.172 s/page on an 85-page book. Dropping `--optimize` and the output file roughly halved the rate on every one of the three — 2.371 → 0.972 on Chanakya — for identical extracted text (9,866 characters both ways). Neither had been measured in the bake-off.

The one real quality loss is **IAST diacritics**: tesseract preserves none of them, where the previous engine kept 74 %. This does not hurt search, because the FTS index uses `unicode61 remove_diacritics 2` and folds diacritics on both sides of a query — `Ākāśagarbha` and `Akasagarbha` are the same token either way. It does hurt anyone pasting a Pāḷi passage out of the index into a note. Restoring diacritics on the quote path (not in the index) was measured as recoverable at 99.7 % by a frontier model and is not yet implemented; see the `20260904_ocr_swap` thread.

### Parallelism — read this before changing `OCR_JOBS`
The refresh loop processes books **sequentially**. ocrmypdf parallelises per *page*, so `OCR_JOBS` is what uses the machine, and it is the whole parallelism story.

This matters because the bake-off's headline **0.433 s/page → 1.32 days** was measured at **4 books × `--jobs 4`** — a concurrency `refresh()` does not have. The sequential row of that same table is 0.904 s/page. Raising `--jobs` recovers most of the difference inside one invocation, which is far cheaper than making the loop concurrent: the clock-based commit and the progress bar both assume one book at a time, and there is no throughput left to win.

Measured live on a real refresh on a 22-core machine:

| `--jobs` | s/page | machine |
|---:|---:|---|
| 4 | 0.904 | ~4 cores |
| 8 | 0.537 | ~8 cores, 53 % idle |
| 12 | current setting | ~12 cores, 30 % idle, 7 % iowait |

Set for headroom, not for peak throughput — the machine is the user's workstation. Two traps when reading CPU during a run: ocrmypdf **nices** its workers, so the load appears in `top`'s `ni` column and a monitor showing user CPU only will read 2–3 % while eight cores are saturated; and killing the refresh **orphans** ocrmypdf (see below), so a stray run from a previous invocation can double the real worker count and make the current setting look far too high.

### Bounds and statuses
`OCR_SUBPROCESS_TIMEOUT` (1800 s) bounds the whole book. This bound is not optional: the machinery it replaced existed to contain an unkillable wait, and the zero-stall record above covers only 1.3 % of the library. The child is started in its own session and the timeout kills the whole **process group**, not just the parent — ocrmypdf drives a pool of tesseract workers, and orphaning that pool would leave it burning CPU for the rest of a multi-day refresh.

**The same isolation has a cost, and it is not fixed:** because the child has its own session, a Ctrl-C or `kill` on the refresh does not reach it. ocrmypdf survives and keeps 8–12 cores busy until it finishes the book. Observed twice on 2026-09-04, once alongside a restarted run on the same book, which saturated the machine at 20 workers on 22 cores. The fix is a SIGINT/SIGTERM handler in `refresh()` that kills the group. Until then: after stopping a refresh, check for stray `ocrmypdf` processes and kill them by PID — `pkill` fails silently in some sandboxes, so verify by re-listing.

ocrmypdf writes its sidecar **once, at the end**, so a killed or timed-out run leaves no text at all. That retires the previous `partial: …` vocabulary, which existed only because the old worker streamed text per 10-page chunk and a stall left real pages behind. The 25 rows in the live index that still carry a `partial:` status are re-extracted like any other non-`ok` row; nothing is stranded. The page cap (`OCR_PAGE_CAP`) is gone with it, along with `ok: ocr truncated at 1000 of 1678 pages` — measured against the live index before removal, **0 rows** carried that status, so there was no migration to do.

The statuses the OCR path can now emit:

| status | meaning | retried by `--retry-failed` |
|---|---|---|
| `ok` | sidecar text, plausible length for the page count | no |
| `empty: pdf ocr produced no text` | ran cleanly, produced no text | yes |
| `error: pdf ocr timed out after 1800s` | hit the whole-book bound | yes |
| `error: pdf ocr: <last stderr line>` | non-zero exit | yes |
| `error: pdf ocr subprocess: <exc>` | could not spawn the binary | yes |
| `error: pdf ocr output implausibly short (N chars from M pages)` | see below | yes |

Every status other than `ok` contains the substring `ocr` on purpose — `skill/vicaya/SKILL.md` branches on it, and a status without it sends the research agent down the pdftotext dead end those passages exist to prevent.

### Two measured safety behaviours
**Encrypted PDFs are pre-decrypted.** ocrmypdf refuses them outright (`EncryptedPdfError`, rc=8), and **43 of 1,735** scanned books carry owner-only encryption with an empty user password — a "no copy/print" restriction, not access control. `_decrypted_pdf` opens the file with `pikepdf` and re-saves it to a temp copy, which strips it. No credentials are involved. `pikepdf` is a main dependency for exactly this reason; the apt copy that ocrmypdf itself uses is invisible to the venv, which sets `include-system-site-packages = false`.

**Implausibly short output is flagged, not called success.** Both tesseract-based candidates returned **84 characters for an entire 85-page book** while reporting rc=0 — a book the previous engine read at 211,181 characters. A return code cannot catch that, so `_extract_pdf_ocr_fallback` compares the character count against `OCR_MIN_CHARS_PER_PAGE` (20, far below any real scan) times the page count from `pdfinfo`, and records `error: pdf ocr output implausibly short (…)` instead of `ok`. Two things to know about this: the population rate is **unknown** (n=1 in a 22-book sample), and after this swap there is **no second engine** to recover such a book — all 7 tesseract page-segmentation modes at both 150 and 300 dpi were tried on it and every one returned zero characters. A flagged book stays unindexed and stays visible in the count; it is not silently recorded as read.

### Rebuild
A full rebuild is three passes, in order: `just lf-refresh-text` (every file, OCR off, fast), then `just lf-refresh-retry` (only the rows pass 1 could not read, OCR on, hours). The third retry pass is kept deliberately: "zero stalls" is 0 out of 20 attempts, whose 95 % upper bound is 16 %, which is not a basis for removing a recovery pass. The order is stated in the justfile header and in both recipe doc-comments.

Because an OCR pass runs for hours, the index is opened in WAL mode and the refresh commits every `REFRESH_COMMIT_SECONDS` (30 s) instead of once at the end: an interrupted run keeps the files it finished, and a search can read the index while a refresh is writing it. There is no sub-book resume — an interrupted book is redone from page 1, which was true of the previous engine too.

**Install:**
1. `uv sync` — installs the Python side (`pikepdf`).
2. `sudo apt install ocrmypdf` — the OCR engine itself, **not** managed by uv. Verify with `ocrmypdf --version` (15.2.0 and tesseract 5.3.4 are the measured versions). Without it, scanned PDFs keep their pdftotext status and are never OCR'd.
3. Nothing else. There is no PDFium download, no `PDFIUM_LIB_PATH`, no `ORT_DYLIB_PATH` and no model download — all four were needs of the previous engine. If `PDFIUM_LIB_PATH` is still set in your `.env`, it is now unused and can be deleted.

**Verify it works:**
```bash
uv run python -c "
from pathlib import Path
from tools import library_folders as lf
r = lf._extract_pdf(Path('<a known scanned pdf>'))
print(r.status, len(r.text))  # expect: ok <nonzero>
"
```

**Update:** `sudo apt upgrade ocrmypdf` for the engine; `uv lock --upgrade-package pikepdf && uv sync` for the Python side.

**Gotcha (fixed 2026-09-02, watch for recurrence):** `.venv/bin/*` console scripts once had shebangs pointing at another project's venv (`research-hub`), so `uv run pytest` silently ran under a foreign interpreter — deps like weasyprint/pikepdf "missing" in tests only. If tests fail to import venv packages, check `head -1 .venv/bin/pytest` and reinstall the package that owns the script.

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
