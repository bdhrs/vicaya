# Vicaya

A research tool for Pāḷi and Buddhist topics.

You ask a question. The tool searches your Obsidian vault, the Pāḷi canon
(suttas, Vinaya, Abhidhamma, commentaries, sub-commentaries), your Calibre
library, unmanaged folder corpora, YouTube talks, and the open web. It drafts an answer with full
citations, has a second model review the draft, and saves a single Markdown
note into your vault under `Vicaya/`. Notes link back to existing notes
on related topics, so the vault accumulates as a connected body of work.

The main skill is invoked as `/vicaya <your question>` inside Claude Code (or
any agent that reads a Markdown skill file). For lower-context staged runs, use
the sibling skills `vicaya-0-scope`, `vicaya-1-gather`,
`vicaya-2-synthesize-review`, and `vicaya-3-complete`; they route to exact sections in `skill/vicaya/SKILL.md`, which remains the behavioral source of truth.

## Sources

Each source is optional — if the tool or path isn't configured it is silently skipped.

| Source | What it searches |
|---|---|
| **Obsidian vault** | Your existing research notes |
| **Pāḷi canon** | Local SQLite DB — CST text, translations, commentaries |
| **Calibre library** | Your book collection; metadata via read-only `metadata.db`, full-text via Calibre FTS when indexed |
| **Folder corpus** | Unmanaged document tree indexed into a local SQLite FTS database; separate from Calibre |
| **Sanskrit (GRETIL)** | Local clone of the GRETIL corpus — Vedic, Epic, Upaniṣadic, and philosophical Sanskrit texts in IAST plain text |
| **YouTube** | Dhamma talks and sutta studies via a curated channel allowlist |
| **Web** | General search and page fetch |
| **Gemini cross-check** | Second model reviews the draft before the note is written |

## Setup

1. `cp .env.example .env` and edit the paths to match your vault, library,
   and canon database.
2. Install whichever of these you want to use: `obsidian` CLI, `calibredb`
   (Calibre 9+, for full-text snippets), `yt-dlp`, `sqlite3`, `gemini` CLI.
3. `uv sync` to install Python dependencies.
4. Symlink the main skill folder into your agents' skills directories. Using
   symlinks ensures that changes made in this repository are immediately
   reflected in all agents. If you use staged runs, symlink the staged sibling
   folders too: `vicaya-0-scope`, `vicaya-1-gather`,
   `vicaya-2-synthesize-review`, and `vicaya-3-complete`.

   **Gemini CLI / OpenCode:**
   ```bash
   ln -sf "$(pwd)/skill/vicaya" ~/.agents/skills/vicaya
   ```

   **Claude Code:**
   ```bash
   ln -sf "$(pwd)/skill/vicaya" ~/.claude/skills/vicaya
   ```

5. (Optional) Clone the GRETIL Sanskrit corpus for pre-Buddhist source search:
   ```bash
   git clone https://github.com/wujastyk/GRETIL-mirror.git ~/MyFiles/2_Resources/gretil
   ```
   Set `VICAYA_GRETIL_PATH` in `.env` to match. If skipped, Sanskrit source search is silently disabled.

6. Run `/vicaya <a question>` in Claude Code.

Full setup notes are in [`skill/vicaya/SKILL.md`](skill/vicaya/SKILL.md).

### Calibre full-text search (optional but recommended)

The skill always searches Calibre book metadata by reading the library's
`metadata.db` directly in read-only mode. To also search inside book content
(EPUB/PDF), enable FTS indexing once:

1. Open Calibre with your library.
2. Click the **FT** button at the left edge of the search bar.
3. Select **Enable indexing for this library**.
4. Leave Calibre open while indexing runs — large libraries take several days.
   Indexing pauses on quit and resumes next time you open Calibre.

Calibre does not need to be open for the skill to *search* once the index is
built. It only needs to be open while the initial indexing is in progress.

| Scenario | Calibre GUI needed? |
|---|---|
| FTS indexing is running | **Yes** — indexing only runs while the GUI is open |
| Searching full text after index is built | No — `calibredb fts_search` queries the stored index directly |
| Metadata search (no FTS) | No — Vicaya reads `<library>/metadata.db` read-only |

> Note: The old path `Preferences → Searching → Full text search` was removed
> in Calibre 9. Use the **FT** button in the search bar instead.

| Platform | `calibredb` path after Calibre install |
|---|---|
| macOS | Added to PATH automatically by the Calibre installer |
| Linux (AppImage) | `~/.local/bin/calibredb` or wherever you extracted the AppImage |
| Linux (apt/rpm) | `/usr/bin/calibredb` |
| Windows | Added to PATH by the installer; may need a new terminal after install |

### Folder corpus search (optional)

The folder corpus source indexes an unmanaged document tree without reading
Calibre metadata or calling `calibredb`. Configure:

- `VICAYA_FOLDER_CORPUS_ROOT`: the source tree, which may be local, external, or server-mounted.
- `VICAYA_FOLDER_CORPUS_INDEX`: a local SQLite index path outside this repository.

Normal research search uses only the SQLite index. Source files are touched
during `folder-corpus-refresh` or later manual inspection, not during
`search-folder-corpus`.

Build and verify the index after setting `.env`:

```bash
uv run tools/research_sources.py folder-corpus-check
uv run tools/research_sources.py folder-corpus-refresh
uv run tools/research_sources.py search-folder-corpus "dhamma" --limit 5
uv run tools/research_sources.py folder-corpus-duplicates --samples 10
```

The first unbounded refresh may take a long time on a large or mounted tree
because it must walk and hash every accepted file. Search covers files where
text extraction succeeds; metadata-only files are still tracked for path,
hash, and duplicate diagnostics but are not searchable by body text. Optional
local tools such as `pdftotext`, `textutil`, `antiword`, and `catdoc` improve
extraction coverage when installed.

Duplicate handling is conservative. Exact byte duplicates and identical
normalized extracted text are collapsed by default; `--include-duplicates`
returns every member. Filename-only matches are surfaced as
`possible_duplicate_of` hints for the researcher to judge, not auto-hidden.
Junk names such as `metadata.opf` and `Picasa.ini` are filtered from those
hints.

### Obsidian CLI

The `obsidian` command is part of the Obsidian desktop app — install Obsidian
from https://obsidian.md and the CLI comes with it.

**The desktop app must be running** when the skill executes. If it is not open,
vault search and note creation are disabled (the skill falls back to writing
the note directly to the vault folder, which Obsidian indexes on next launch).

To start Obsidian silently in the background before running the skill:

| Platform | Command |
|---|---|
| macOS | `open -a Obsidian` |
| Linux | `setsid obsidian </dev/null >/dev/null 2>&1 &` |
| Windows | `Start-Process obsidian` |

Verify the CLI is reachable: `obsidian version`

---

## Autonomous agent setup

> These instructions are written for AI agents (Claude Code, GitHub Copilot,
> etc.) that need to set up this project without human intervention. Read this
> section in full before running any commands. Every step includes a
> verification check — do not proceed past a failed check without telling the
> user.

### 0 — Prerequisites check

Run the following and note what is missing:

```bash
which uv          # Python package manager — required
which obsidian    # Obsidian CLI — optional (vault search)
which calibredb   # Calibre — optional (full-text library snippets)
which yt-dlp      # yt-dlp — optional (YouTube search)
which gemini      # Gemini CLI — optional (cross-check model)
python3 --version # system Python — only needed if uv is absent
```

`uv` is the only hard requirement. Install it if missing:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Install optional CLI tools only if the user wants those sources. Skip any
tool the user does not need — the skill degrades gracefully.

```bash
# yt-dlp (YouTube search + transcript)
pip install -U yt-dlp          # or: uv tool install yt-dlp

# Calibre CLI — install Calibre from https://calibre-ebook.com/download
# needed for full-text snippets; metadata search reads metadata.db directly
# then calibredb is available in PATH automatically.

# Gemini CLI — requires Google AI Studio API key
npm install -g @google/gemini-cli   # or follow https://github.com/google-gemini/gemini-cli
```

The `obsidian` CLI is bundled with the Obsidian desktop app on some platforms.
Check `which obsidian`; if missing, the vault search source is disabled.

### Runtime requirements

Some sources require a desktop application to be open:

| Source | Requirement | Impact if not running |
|---|---|---|
| **Obsidian vault** | Obsidian desktop app must be running | Vault search and note-write are disabled; note is written directly to disk instead |
| **Calibre FTS** | Calibre must be open *during initial indexing only* | Indexing pauses; once index is built, Calibre does not need to be open for searches |

Tell the user about these requirements after setup is complete. Specifically:
- If `VICAYA_VAULT_PATH` is configured: remind them to keep Obsidian open when
  running `/vicaya`.
- If `VICAYA_CALIBRE_LIBRARY` is configured: walk them through the FT button
  steps above and tell them to leave Calibre open until indexing finishes.

### 1 — Python environment

```bash
uv sync
```

Verify:

```bash
uv run python -c "import youtube_transcript_api; print('ok')"
```

### 2 — Discover local paths

The `.env` file maps local paths to the user's local data. Discover them
automatically before writing:

```bash
# Obsidian vault — find the vault directory (contains .obsidian/)
find ~ -maxdepth 4 -name ".obsidian" -type d 2>/dev/null | head -5

# Calibre library — contains metadata.db
find ~ -maxdepth 5 -name "metadata.db" 2>/dev/null | grep -i calibre | head -5

# Optional unmanaged folder corpus — ask before choosing a large source tree.
# The index path should be local and outside this repository.

# Canon DB — tipitaka-translation-data.db (from dpd-db project)
find ~ -maxdepth 8 -name "tipitaka-translation-data.db" 2>/dev/null | head -3

# DPD DB — dpd.db (from dpd-db project)
find ~ -maxdepth 8 -name "dpd.db" 2>/dev/null | head -3

# GRETIL corpus — check if already cloned
find ~ -maxdepth 6 -name "gretil.html" 2>/dev/null | head -3
```

If any path is not found, leave that variable blank in `.env` — the
corresponding source will be silently skipped.

### 3 — Write .env

Copy the template and fill in the discovered paths:

```bash
cp .env.example .env
```

Edit `.env` with the values found in step 2. Use `~` for the home directory.
Example layout (adjust to actual paths):

```
VICAYA_VAULT_NAME=Obsidian
VICAYA_VAULT_PATH=~/Obsidian
VICAYA_CALIBRE_LIBRARY=~/Calibre Library
VICAYA_FOLDER_CORPUS_ROOT=
VICAYA_FOLDER_CORPUS_INDEX=
VICAYA_CANON_DB=~/path/to/dpd-db/resources/tipitaka_translation_db/tipitaka-translation-data.db
VICAYA_DPD_DB=~/path/to/dpd-db/dpd.db
VICAYA_GRETIL_PATH=~/MyFiles/2_Resources/gretil
```

Verify the file was written and does not contain placeholder text:

```bash
cat .env
```

`.env` is gitignored and will never be committed.

### 4 — Run the test suite

```bash
uv run pytest tests/ -q
```

Expected: all tests pass or are skipped (skipped = optional tool not
installed, which is fine). Zero failures.

If DPD-backed citation tests are skipped because `VICAYA_DPD_DB` is blank
but you did find a `dpd.db` in step 2, go back and fill in that path.

### 5 — Symlink the skill

To make the main skill available across all your agents while keeping it in
sync with this repository, create symlinks in the following locations. If you
use staged runs, create matching symlinks for `skill/vicaya-0-scope`,
`skill/vicaya-1-gather`, `skill/vicaya-2-synthesize-review`, and
`skill/vicaya-3-complete`.

**For Gemini CLI and OpenCode (shared central directory):**

```bash
mkdir -p ~/.agents/skills
ln -sf "$(pwd)/skill/vicaya" ~/.agents/skills/vicaya
```

**For Claude Code:**

```bash
mkdir -p ~/.claude/skills
ln -sf "$(pwd)/skill/vicaya" ~/.claude/skills/vicaya
```

**Verification:**

```bash
# Check Gemini/OpenCode
ls ~/.agents/skills/vicaya/SKILL.md

# Check Claude
ls ~/.claude/skills/vicaya/SKILL.md
```

If you ever move or rename this repository, you will need to re-run these
commands to update the symlinks.

### 6 — Final verification

```bash
# Resolve a known citation (requires VICAYA_DPD_DB to be set)
uv run tools/research_sources.py resolve-citation s0202m_mul 97
# Expected: { "human": "MN60 Apaṇṇakasuttaṃ para 97", ... }

# Search canon (requires VICAYA_CANON_DB to be set)
uv run tools/research_sources.py search-canon "dukkha" --limit 3
# Expected: list of CanonHit objects

# Check optional folder corpus configuration
uv run tools/research_sources.py folder-corpus-check
# Expected: JSON status; unavailable is fine when the source is not configured
```

Setup is complete when both return results without errors. The skill is
ready to use: `/vicaya <your question>` in Claude Code.

## Layout

```
vicaya/
├── tools/research_sources.py   # source helpers + CLI subcommands
├── tools/folder_corpus.py       # unmanaged folder-corpus SQLite index/search
├── tests/                       # pytest suite
├── data/
│   ├── calibre_tags.csv         # tag vocabulary
│   ├── youtube_channels.md      # YouTube channel allowlist
│   └── youtube_cache/           # cached transcripts (gitignored)
├── skill/vicaya/                # the main skill prompt
├── skill/vicaya-*/              # staged skill routers
└── kamma/                       # design history
```
