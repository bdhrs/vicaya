# /vicaya

Multi-source research skill for Pāḷi / Buddhist topics. Pulls from your local
Obsidian vault, the CST canon, your library folders, YouTube, and the open web;
cross-checks the synthesis with a second model; and writes one structured note
into your Obsidian vault.

## Usage

```
/vicaya <your question>
```

The skill orchestrates sub-agents internally: after Phase 1 a Sonnet gather
sub-agent handles all evidence collection (Phases 2–4c), keeping the main
session's context clear for synthesis (Phases 5–7). No manual stage switching
needed. `SKILL.md` remains the behavioral source of truth.

For maintenance, use `vicaya-improve` to process accumulated run retrospectives
into `runs/TODO.md` and choose the next improvement.

Examples:
```
/vicaya what does the Buddha mean by "the dart" in MN 105?
/vicaya is upādāna in the suttas always grasping or sometimes appropriation?
/vicaya compare the abhidhamma definition of cetanā with modern psychology
```

You can also pass seed references:

```
/vicaya how do the commentaries treat MN 1?
   See [[Mūlapariyāyasutta notes]] and SC's translation by Bodhi.
```

## Output

A single Markdown note in your Obsidian vault under `Vicaya/`:

```
Vicaya/YYYY-MM-DD - <slug>.md
```

Frontmatter is structured for Obsidian dataview queries. Citations are inline;
sources appear in dedicated sections (Canon / Library / Web / YouTube).

## How it works

Seven phases (see `SKILL.md`):

1. **Vault context** — `obsidian search:context` for related prior notes.
2. **Canon** — SQLite query over `tipitaka-translation-data.db` (CST + translations).
3. **Library** — full-text index search across library folders via `search-library-folders`.
4. **Web + YouTube** — `WebSearch` / `WebFetch`, plus YouTube search and
   transcript fetch over a curated channel allowlist.
5. **Synthesis** — Claude drafts findings with inline citations.
6. **Cross-check** — independent second-opinion pass.
7. **Write** — `obsidian create` saves the final note into `Vicaya/`.

## Dependencies

| Tool | Required | Status check |
|------|----------|--------------|
| `obsidian` CLI v1.12.4+ | yes | `obsidian version` |
| `sqlite3` | yes | `sqlite3 --version` |
| `yt-dlp` | yes (YouTube search) | `yt-dlp --version` |
| `gemini` CLI | optional (cross-check) | `gemini --version` |
| `uv` | yes (to run helpers) | `uv --version` |

## Configuration

All user-specific paths live in `.env` at the repo root. Copy `.env.example` to
`.env` and edit. See `SKILL.md` for the full schema.

## Phase 7 utilities

```bash
uv run scripts/validate_note.py "Vicaya/YYYY-MM-DD - <slug>.md"
uv run scripts/generate_note_pdf.py "Vicaya/YYYY-MM-DD - <slug>.md"
```

## Known limitations

- **Citation human-refs** for canon are currently piṭaka/nikāya/paranum level
  (e.g. `MN 02 §23`). Full sutta-name resolution is a follow-up.
- **YouTube auto-captions** mishear Pāḷi terms. The skill paraphrases auto-
  caption material and links to the timestamp rather than quoting verbatim.

## Source layout

```
vicaya/
├── scripts/                     # standalone Phase 7 workflows
├── tools/research_sources.py    # source helpers (importable + CLI)
├── tools/note_checks.py         # final-note validation helpers
├── tests/                       # pytest suite
├── data/
│   ├── calibre_tags.csv         # tag vocabulary
│   ├── youtube_channels.md      # channel allowlist (trusted / probationary / excluded)
│   └── youtube_cache/           # cached transcripts (gitignored)
├── skill/vicaya/                # this main skill
├── skill/vicaya-improve/        # retrospective triage skill
├── skill/vicaya-*/              # staged skill routers
└── kamma/                       # design history
```
