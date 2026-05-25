---
name: vicaya
description: Run a structured Pāḷi/Buddhist research session across the user's local sources (Obsidian vault, CST canon SQLite, Calibre library) plus web search, cross-checked with Gemini, and write a single linked note into the Obsidian vault. Invoke when the user types /vicaya <question> or asks for "research on X", "look into X across my sources", "find what the suttas say about X", or any multi-source research request that should land as a permanent vault note.
---

# Research skill

Run a multi-phase research session across the user's local + web sources and write a single structured note into their Obsidian vault.

## Hard rules (read first — these are not preferences)

These rules apply to every run, by every agent. They are part of the skill, not stored in any agent's private memory.

1. **No AI / model attribution in the scholarship body.** Never write "Gemini noted", "Claude found", "the AI suggested", "added by cross-check", etc. inside the findings, evidence, or analysis. The body must read like scholarship — information and sources are what matter, not the process of producing them. If a second-pass review surfaces material, integrate it silently with proper citations to the underlying primary or secondary source. **The only places agent identity appears are the `agent` frontmatter field and the final footer line** (see Phase 7 — Agent self-identification). Those are metadata, not scholarship.
2. **No process or workflow logging inside the research note.** No "Improvements made" sections, no "the helper failed and I switched to X", no "this was missed in the first pass". Notes contain content; process belongs in the terminal report only (Phase 7's final summary), and self-improvement edits go into this `SKILL.md` file.
3. **Pāḷi spelling conventions differ per source:**
   - **Canon SQLite (`tipitaka-translation-data.db`) and the Obsidian vault** use exact Pāḷi diacritics (`paṭiccasamuppāda`, `dukkha`, `nibbāna`). Search verbatim. If 0 hits, suspect a bug or the alternate niggahita (`ṃ` vs `ṁ`), not loose spelling.
   - **Calibre library** uses ASCII Pāḷi (`paticcasamuppada`). The `search_calibre` helper strips diacritics from queries automatically.
4. **Obsidian CLI requires the Obsidian desktop app to be running.** If a CLI command fails with "unable to find Obsidian", launch the desktop app yourself in the background and wait ~5 seconds before retrying. On Linux that's typically `setsid obsidian </dev/null >/dev/null 2>&1 &` (or the absolute path to the binary on your system); on macOS, `open -a Obsidian`. Don't ask the user to open it.
5. **Don't ask the user to run shell commands you can run yourself.** Read-only inspection, launching local applications, running helper scripts via `uv run` — all yours to do. Only ask when something genuinely requires the user: interactive logins, granting permissions, installing system packages, etc.
6. **Citations are non-negotiable.** Every claim has a reference. A claim without a citation is a hallucination waiting to happen.
7. **Auto-captions mishear Pāḷi.** YouTube's auto-generated captions mangle Pāḷi terms (e.g. "Suddhāso" → "saso", "Apaṇṇaka" → "apaka"). When a YouTube transcript's `is_auto` is true, **paraphrase and link to the timestamp** — never quote Pāḷi verbatim from auto-captions. Human-uploaded captions (`is_auto = false`) may be quoted with normal care.
8. **Query YouTube in English, anchor with Pāḷi sutta name + numeric reference.** Pāḷi-heavy queries return zero results; long English glosses return zero results. `apannaka sutta MN 60` works; `apannaka safe-bet wager rebirth` returns nothing.
9. **CST paragraph numbers are book-global, not sutta-local.** A `paranum` returned by `search-canon` is a continuous index across the entire book file — para 261 in `s0202m_mul` is MN78, not MN60. Always run `resolve-citation` to confirm which sutta a paragraph belongs to before citing it. Never assume the paragraph number matches a sutta number.
10. **YAML frontmatter safety.** Always wrap YAML values in double quotes if they contain a colon followed by a space (e.g. `"Topic: Subtitle"`). Unquoted colons break Obsidian's property rendering.

## Inputs

- **Topic / question** (required): the research question, in the user's words.
- **Optional references** the user passed in: URLs, vault note names, book titles, sutta refs. Treat these as authoritative seeds.

### Question sanitization

Before using the topic as the note's `topic:` field value, smooth it into a proper English sentence or question: complete grammar, correct punctuation, question mark where the phrasing calls for one. Remove any loaded or leading language — preconceived conclusions, partisan framing, or strong opinions should not be baked into the question itself. Keep the original scope and intent intact. The research body is where findings and positions are reported; the question just names the topic neutrally. Record the verbatim user input only in the run reflection's `question:` field.

## Setup — paths and tools

Hard-coded for this machine. If a path is missing or a tool isn't installed, stop and tell the user; don't guess.

All user-specific paths come from the project's `.env` file (see `.env.example` at the repo root). The helper module resolves them on import. Agents do not hard-code paths; use the helpers and CLI.

- Vault Root: `$VICAYA_VAULT_PATH` (This is the absolute path to the root directory of the vault).
- Output folder in vault: `$VICAYA_VAULT_PATH/Vicaya/`
- Helper module: `<repo>/tools/research_sources.py`
- Canon db: read-only SQLite at the path baked into the helper module.
- Calibre library: path baked into the helper module. FTS indexing may or may not be complete depending on when the library was last indexed (14k books takes days to index from scratch). The helper checks FTS status automatically and falls back to metadata search if indexing is incomplete — don't try to force FTS. When FTS is active, snippets are returned with hits; when metadata-only, you get titles/authors/comments. Both are useful; note which mode is active in the scratch.
- Cross-check uses an OpenRouter model chain (see Phase 6; current lead `deepseek/deepseek-v4-flash` — paid but ~$0.0001/call). Requires `OPENROUTER_API_KEY` in env / `.env`, or an OpenRouter key in `~/.local/share/opencode/auth.json`. When unavailable the helper returns a `# SELF_REVIEW:` sentinel and the agent runs the checklist on its own synthesis.
- **Book code → source XML map**: `/home/bodhirasa/MyFiles/3_Active/dpd-db/tools/pali_text_files.py` maps every canon book code (e.g. `s0201m_mul`) to its source XML file in the DPD database. Consult this when you need to know which raw XML file a given book code corresponds to, or when debugging why a search returns no results for a book you expect to exist.
- **EBC vault** (Early Buddhist Connections): `$VICAYA_EBC_VAULT_PATH` — a separate, read-only Obsidian vault of curated EBT material. Supplies per-sutta Āgama-parallel metadata, multiple parallel English translations of each sutta, Chinese-Āgama translations (Patton + BDK), and a Pātimokkha rule/commentary set. See the **EBC vault** section below.

## Calling the helpers

**Prefer the CLI over `python -c` heredocs.** Heredoc invocations have repeatedly caused quoting bugs (single-quotes-in-single-quotes SyntaxErrors) and field-name guesses (`.snippet` on a `CanonHit`, which has no such field). The CLI eliminates both.

Run from the project root:

```bash
cd <repo-root>   # the vicaya repo
uv run tools/research_sources.py <subcommand> [args...]
```

Subcommands (each prints JSON to stdout):

| Subcommand | Args | Notes |
|---|---|---|
| `search-vault QUERY` | `--folder PATH` `--limit N` | Obsidian vault full-text search |
| `search-canon QUERY` | `--books PAT...` `--lang pali\|english\|chinese\|any` `--limit N` | Default books: sutta mūla (`s*_mul`) |
| `resolve-citation BOOK_CODE PARANUM` | — | Returns `Citation` JSON |
| `search-calibre QUERY` | `--tags T...` `--limit N` | Diacritics stripped automatically |
| `lookup-book VALUE` | — | Translate any CST book identifier into the others (filename, table, Pāḷi title, gui code, DPD code) |
| `cross-check` | `--timeout N`; **prompt on stdin** | OpenRouter model chain (see `data/openrouter_models.json`) → `# SELF_REVIEW:` sentinel on failure. Use this in Phase 6. |
| `gemini-cross-check` | `--timeout N`; **prompt on stdin** | Legacy direct gemini call. Not used in Phase 6; kept for ad-hoc use if you want a second opinion from a different provider. |
| `get-ebc-overview SUTTA_CODE` | — | Parsed EBC overview card: PTS ref, titles, themes, training, formula, **named Āgama parallels**, partial parallels. Accepts `MN10`, `mn 10`, `mn-10`, `DN22`, `MA98`, etc. Returns `EBCOverview` JSON or exits 1 if missing. |
| `search-ebc QUERY` | `--folder PATH` `--limit N` | Fixed-string grep across the EBC vault (markdown only). Returns `VaultHit`s. `--folder` accepts a subdir like `+Suttas/Overviews Suttas/MN` or `+Vinaya/Patimokkha/bmc1`. |
| `calibre-check` | — | Probe whether the Calibre library is reachable right now. Exits 0 if ok, 1 if locked or unavailable, with a specific message. Use at Phase 3 start. |
| `sc-parallels CITATION` | `--no-text` | Look up parallels for a citation (e.g. `mn18`, `sn35.28`) in the offline SuttaCentral archive. Returns `SCParallel` objects: `ref`, `resemblance` (bool, `~` prefix), `paragraph_range`, `text_pali`, `text_lzh`, `text_san`, `text_pra`, `translation_en`, `text_gaps` (list — explicit when text isn't in the partial archive). Parallel *identification* is comprehensive; text retrieval is best-effort. |
| `sc-search QUERY` | `--lang pli\|lzh\|san\|pra\|en` `--limit N` | Fixed-string grep across SuttaCentral offline root texts in one language. `lzh` = Literary Chinese Āgamas. Returns `VaultHit`s with the matched JSON segment. |

Parse the JSON with `jq` or read it as a file. Only fall back to `uv run python -c "..."` if you genuinely need to combine helpers in one step — and if so, write a short `.py` script to a temp path and run that, rather than a heredoc.

## Helper return shapes (read before calling)

Every helper returns dataclasses serialised to JSON by the CLI. Field names are exact — guessing them has caused crashes in prior runs.

- **VaultHit**: `path` (str), `snippet` (str), `line` (int | null)
- **CanonHit**: `book_code` (str, e.g. `s0201m_mul`), `paranum` (str), `pali` (str), `english` (str), `chinese` (str). **No `snippet` field** — quote from `pali` / `english` directly. XML/TEI markup is stripped automatically; text is plain UTF-8.
- **Citation**: `machine` (e.g. `s0201m_mul:23`), `human` (e.g. `MN60 Apaṇṇakasuttaṃ para 97`), `pitaka`, `text_type`, `paranum`.
- **CalibreHit**: `book_id` (int), `title` (str), `authors` (str), `tags` (list[str]), `location` (str), `snippet` (str — populated only when FTS is ready).
- **YouTubeHit**: `video_id` (str), `title` (str), `channel` (str), `channel_id` (str), `duration` (float | null, seconds), `url` (str), `tier` (str — `trusted` | `probationary`; `excluded` never appears here, those are filtered out).
- **YouTubeTranscript**: `video_id` (str), `lang` (str, e.g. `"en"`), `is_auto` (bool — **true means Pāḷi terms are unreliable; paraphrase, don't quote**), `segments` (list of `{start, duration, text}`), `fetched` (ISO date).
- **EBCOverview**: `code` (str), `path` (str — absolute path to the overview file), `pts` (str, e.g. `"M i 55"`), `titles` (list — Pāḷi + English), `nikaya` (list), `chapter` (list), `themes` (list), `topics` (list), `training` (list), `formula` (list), `audience` (list), `teacher` (list), `parallels_agama` (list of bare codes, e.g. `["MA98", "EA12.1"]`), `parallels_partial` (list).

## Book-identifier lookups (`lookup-book`)

Use when you've got one form of a CST book identifier and need another — e.g.
an unfamiliar code lands in your search results, the user mentions a book by
its Pāḷi name, or you have a `dpd_book_code` like `DN` / `DNa` and need the
SQLite-table form. Loads dpd-db's `cst_book_translator` live from the sibling
repo.

Accepts any of: `cst_filename` (`s0101m.mul`), vicaya's SQLite table form
(`s0101m_mul`), `cst_book_name` (`Dīghanikāya, Sīlakkhandhavaggapāḷi`),
`gui_book_code` (`dn1`), or `dpd_book_code` (`DN`, `DNa`). Auto-detects. A
single DPD code like `DN` expands to all matching books (e.g. 3 DN mūla volumes).

```bash
uv run tools/research_sources.py lookup-book s0101m_mul
uv run tools/research_sources.py lookup-book DN
uv run tools/research_sources.py lookup-book "Majjhimanikāya, Mūlapaṇṇāsapāḷi"
```

Returns a JSON list of `{cst_filename, cst_table, cst_book_name, gui_book_code,
dpd_book_code}`. Empty list on no match. The embedded book-code map below is
still the primary reference for picking `--books` patterns; `lookup-book` is
for one-off translations during a run.

## EBC vault (Early Buddhist Connections)

A second, read-only Obsidian vault sitting alongside the main vault at
`$VICAYA_EBC_VAULT_PATH` (default `~/MyFiles/2_Resources/Early Buddhist Connections`).
Source: https://github.com/dhamma-vinaya-connections/early-buddhist-connections.
Treat it as reference material — never write to it. Output notes always land in
`$VICAYA_VAULT_PATH/Vicaya/`.

**Two helpers** (`get-ebc-overview`, `search-ebc`) cover the structured-metadata
case. Everything else is plain files on disk — open them with `Read` once you
know the path. The folder map below tells you where each kind of file lives.

### Folder map

```
+Suttas/
  Overviews Suttas/<NIK>/<RANGE?>/<CODE>.md     # per-sutta YAML card
  Sutta Texts/
    Bodhi/<nik>-bodhi/<code>-bodhi.md           # Ven. Bodhi (MN, SN, AN)
    Sujato-pali/<nik>-sujato-pali/<code>-sujato-pali.md  # bilingual Sujato
    dn_walshe/<code>-walshe.md                  # DN only (Maurice Walshe)
    Thanissaro notes/...                        # Ajahn Ṭhānissaro notes
    Anīgha/...
    Pali Only/pali-sc/...                       # raw Pāḷi (SuttaCentral)
    Deep Seek-Pali/<nik>_deepseek_pali/...      # machine-aligned Pāḷi
    Agamas Dhamma pearls/<nik>-patton/<code>-patton.md  # Chinese Āgama (Patton)
    Agamas BDK/<nik>-bdk/<code>-bdk.md          # Chinese Āgama (BDK)
  Indexes Suttas/<NIK>/                         # Nikāya indexes
  Indexes Suttas/Thematic indexes/              # ATI, Suttafriends, etc.
+Vinaya/
  Patimokkha/
    bmc1/                                       # Buddhist Monastic Code I (Ven. Ṭhānissaro)
    Ñañatusita/                                 # Ñāṇatusita analysis + translation
    Vibhanga/{Monks,Nuns}/                      # Canonical Vibhanga
    Rule Overviews/{BU,BNI}/                    # Rule-by-rule overview cards
  Khandhakas/
    Brahmali/{mv,cv}-brahmali-pali/             # Ajahn Brahmali bilingual
    Deepseek/{mv,cv}-deepseek-pali/             # Machine-aligned Pāḷi
Catalogue/
  Suttas-Catalogue.tsv                          # 14k rows of structured metadata
  Patimokkha-Catalogue.tsv
```

Nikāya prefixes used in `<NIK>` and `<code>`: `MN`, `DN`, `SN`, `AN`, `DHP`,
`UD`, `ITI`, `SNP`, `THAG`, `THIG`, `MA`, `DA`, `EA`, `SA`, `T`, `PDHP`.

### When to reach for EBC

1. **Any sutta-anchored question** → `get-ebc-overview <code>` first. One call
   gives you PTS ref, themes, training, formula, and the full list of named
   Chinese-Āgama parallels + partial parallels. This is the single highest-leverage
   capability and replaces a SuttaCentral parallel-table lookup.
2. **Want a verbatim Chinese-Āgama parallel quote** → from the overview's
   `parallels_agama`, pick a code (e.g. `MA98`), then `Read` the Patton or BDK
   translation at the path shown in the folder map. Patton paragraphs are
   numbered; quote with `Madhyamāgama 98, trans. Charles Patton, §<n>`.
3. **Compare English translators on the same sutta** → `Read` two files from
   `Sutta Texts/Bodhi/`, `Sujato-pali/`, `dn_walshe/`, `Thanissaro notes/`, etc.
4. **Thematic catalogue lookup** → `grep -F "4 satipaṭṭhānā" Catalogue/Suttas-Catalogue.tsv`
   (the file is one TSV; no helper needed). Columns include `sutta_theme`,
   `sutta_topic`, `sutta_training`, `sutta_formula`, `āgamas_parallels`,
   `sanskrit_parallels`, `taisho_parallels`.
5. **Pātimokkha rule + commentary** → `search-ebc <rule> --folder "+Vinaya/Patimokkha"`,
   or `Read` directly under `bmc1/` (Ṭhānissaro) or `Ñañatusita/`.
6. **Free-text discovery across everything** → `search-ebc <query>` (fixed-string
   grep, markdown only, ~40ms on the full 22k-file vault). Pāḷi terms are sparse
   enough that hits are precise.

### Citation rules

- **Always cite the underlying translator or text, never "EBC".** EBC is the
  delivery mechanism; the scholarship is from Bodhi / Sujato / Ṭhānissaro /
  Patton / Brahmali / etc. Quote as e.g. *MN 10, trans. Bhikkhu Sujato §17* or
  *MA 98, trans. Charles Patton §5*.
- **Evidence tiers** (see the global tier table elsewhere in this doc):
  - Mūla Pāḷi files and Chinese-Āgama translations (Patton, BDK) → **T1** for the
    canonical text they carry.
  - Modern English translations (Bodhi, Sujato, Walshe, Ṭhānissaro) → **T3**
    when cited as translator's reading.
  - bmc1, Ñāṇatusita analysis, overview-card editorial summary/key-excerpts/similes
    → **T2** (commentarial / tradition-aligned editorial).
  - The overview-card YAML fields (`parallels_agama`, `themes`, etc.) are
    bibliographic metadata — use freely to *find* texts; don't cite them as a
    doctrinal source.

### Examples

```bash
# Step 1: get parallels for MN 10
uv run tools/research_sources.py get-ebc-overview MN10

# Step 2: read the Madhyamāgama parallel
# (path from the folder map; the overview confirms MA98 is one of the parallels)
# Use the Read tool on:
#   $VICAYA_EBC_VAULT_PATH/+Suttas/Sutta Texts/Agamas Dhamma pearls/ma-patton/ma98-patton.md

# Free-text discovery scoped to one translator
uv run tools/research_sources.py search-ebc "ekayano ayaṁ maggo" \
  --folder "+Suttas/Sutta Texts/Sujato-pali" --limit 10

# Vinaya commentary search
uv run tools/research_sources.py search-ebc "pārājika" \
  --folder "+Vinaya/Patimokkha/bmc1" --limit 10
```

## Research scratchpad

Context compaction can erase findings mid-run — including between Phase 7 write,
PDF generation, and reflection. The scratch file is the only reliable defence.

**Model: scratch = comprehensive dossier. Vault = curated distillation.**
The scratch file holds *everything found* — full Pāḷi + English quotes, complete
library excerpts, full web summaries, transcript segments with timestamps, every
query tried (including 0-hit ones), cross-check raw output, phase completion log.
The vault note is a curated subset: what earns its place, cited and attributed.
This separation means: (a) recovery after compaction is "read the scratch and
continue"; (b) future related runs can grep scratch files for already-harvested
sources; (c) the vault stays clean — only *complete* notes are ever written there.

**At the start of every run**, create the scratch file inside the repo's
`data/scratch/` folder (gitignored, so it persists across reboots and is
never committed):

```bash
SCRATCH="<repo-root>/data/scratch/$(date +%Y%m%d)_<slug>.md"
```

Use the same slug you'll use for the vault note. Initialise with this structure:

```markdown
# Vicaya dossier — YYYY-MM-DD
**Question:** <question>
**Slug:** <slug>
**Vault note:** (path set at Phase 7 start)

## Phase log
- Phase 0 start: <ts>

## Angle triage
<filled in Phase 1>

## Perspective map
<filled in Phase 1>

## Phase 1 — Vault / EBC
<append all hits>

## Phase 2 — Canon
<append every hit: full pali + english, paranum, resolve-citation output>

## Phase 2.5 — SC Parallels
<append sc-parallels output per sutta; text_gaps logged explicitly>

## Phase 3 — Library
<append every hit: book_id, title, authors, full snippet or extracted excerpt>

## Phase 3b — Sanskrit
<append GRETIL hits if applicable>

## Phase 4 — Web
<append every source: full summary, URL, date>

## Phase 4b — YouTube
<append: video_id, title, channel, tier, relevant transcript segments with timestamps>

## Phase 4c — WisdomLib
<append: terms looked up, URLs fetched, key definitions with tradition + source labels>

## Phase 5 — Synthesis draft
<full draft before any cross-check editing>

## Bibliography (accumulating)
### Primary Sources
<add entries as sources are finalized>
### Secondary Sources
<sorted by author surname; add entries as sources are finalized>
### Online Sources
<add entries as sources are finalized>
### Media Sources
<add entries as sources are finalized>
### Vault Sources Referenced
<add entries as sources are finalized>

## Phase 6 — Cross-check raw output
<paste raw cross-check output verbatim>

## Phase 6 — Integrations
<what was integrated from cross-check, with source>

## Considered but excluded
<sources looked at and dropped: reason (redundant / lower tier / off-topic / unreliable)>

## Phase 7 — Note written
- Path: <vault path>
- PDF: <pdf path or "skipped">

## Reflection written
- Path: <runs/ path or "skipped">
```

Keep `$SCRATCH` in your working context so subsequent phases can append to it.

**⚠️ IRON RULE — a phase is not complete until its scratchpad block is written.** Do not move to the next phase until the append is done. This rule covers every phase including Phase 7 (note write), PDF generation, and reflection — the full sequence is one compaction-safe unit. If context compaction can hit between any two of these steps, each step must record its completion in the Phase log before the next step begins.

**At the start of Phase 5**, read the full scratch file before drafting:

```bash
cat "$SCRATCH"
```

This is the compaction rescue step — even if your context was compressed,
the full dossier is in that file. Missing file: proceed from context, do not abort.

**After Phase 7** (vault note written, PDF attempted, reflection started), leave the
scratch file in place. It accumulates in `data/scratch/` as a permanent research
dossier — gitignored, never committed. Future runs on related topics should grep
`data/scratch/` for already-harvested sources before starting fresh queries.

## Evidence tiers

Every source used in the note belongs to one of four tiers. The tier determines its epistemic weight and which section heading it appears under.

| Tier | Sources | Weight |
|------|---------|--------|
| **T1 — Root canon** | Mūla texts: suttas (`s*_mul`), Vinaya (`vin*_mul`), Abhidhamma (`abh*_mul`) | Highest. Verbatim blockquote mandatory (Rule P1). |
| **T2 — Canonical exegesis** | Aṭṭhakathā (`*_att`), ṭīkā (`*_tik`), Visuddhimagga, late Khuddaka (Niddesa, Paṭisambhidāmagga, Nettippakaraṇa) | Authoritative within the tradition. Attribute to Buddhaghosa / Dhammapāla / the commentarial tradition — never to the Buddha. |
| **T3 — Academic scholarship** | Peer-reviewed books, critical editions, journal articles, scholarly translations (Bhikkhu Bodhi, Bhikkhu Anālayo, Pali Text Society, etc.) | Analytical. Cite author + work. Can support doctrinal claims when T1/T2 is absent or ambiguous. |
| **T4 — Modern teaching and popular sources** | Dhamma talks, recorded teachings, accessible books, YouTube transcripts | Supporting only. Cannot be load-bearing for doctrinal claims. Cite teacher + talk/book. |

The note template uses these tiers as section headings (see Phase 7). The Devil's Advocate checklist question 5 checks that load-bearing claims rest on T1 or T2, not T4.

## Bibliography

Every Vicaya note ends with a `## Bibliography` section. This is the publication-ready
reference list — distinct from footnotes (which are short inline locators) and from the
YAML frontmatter (which is machine-readable metadata). The bibliography is human-readable
and formatted for academic use.

**System adopted: Chicago Notes-Bibliography (N-B).** This is the dominant style in
academic Theravāda / Pāḷi Studies — used by JIABS, PTS publications, Oxford Journal of
Buddhist Studies, and Wisdom / University of Hawaii Press Buddhist Studies monographs.
Footnotes remain as short locators (unchanged); the bibliography provides the full,
sorted, properly-formatted citation for every source cited.

**Five subsections.** Emit a subsection only if it has at least one entry; omit empty
subsections entirely.

1. **Primary Sources** — Pāḷi canon and parallel Āgama texts
2. **Secondary Sources** — library books and journal articles (sorted by author surname)
3. **Online Sources** — web pages, SuttaCentral links
4. **Media Sources** — YouTube talks and Dhamma recordings
5. **Vault Sources Referenced** — internal Obsidian notes cited via wiki-link

**AI research sessions are excluded.** The agent footer already records model identity
and date; that is sufficient disclosure.

### Format rules

#### Primary sources (Pāḷi canon)

No specific translator (CST direct access):
```
*Majjhima Nikāya* 60 (*Apaṇṇakasuttaṃ*). Chaṭṭha Saṅgāyana Tipiṭaka.
  Accessed via tipitaka-translation-data.db (`s0201m_mul`).
```

With translator (EBC translation file):
```
*Majjhima Nikāya* 10 (*Satipaṭṭhānasuttaṃ*). Translated by Bhikkhu Sujato.
  SuttaCentral, 2018. Accessed via EBC vault.
```

Chinese Āgama parallel:
```
*Madhyamāgama* 98 (*Zhongahanijing* T 26). Translated by Charles Patton.
  Accessed via EBC vault, `ma-patton/ma98-patton.md`.
```

Commentary / sub-commentary:
```
Buddhaghosa. *Visuddhimagga* (Path of Purification). Chaṭṭha Saṅgāyana Tipiṭaka.
  Accessed via tipitaka-translation-data.db (`e0101n_mul`, `e0102n_mul`).
```

#### Secondary sources (library books)

Monograph:
```
Harvey, Peter. *The Selfless Mind: Personality, Consciousness and Nirvāṇa in Early
  Buddhism*. Richmond: Curzon Press, 1995. (Calibre #6294)
```

Edited volume:
```
Williams, Paul, ed. *Buddhism: Volume IV — Abhidharma and Madhyamaka*. London:
  Routledge, 2005. (Calibre #4937)
```

Chapter in edited volume:
```
Gethin, Rupert. "Bhavaṅga and Rebirth According to the Abhidhamma." In *The Buddhist
  Forum, vol. III*, edited by T. Skorupski and U. Pagel, 11–35. London: SOAS, 1994.
  (Calibre #10228)
```

Journal article (if available via Calibre or web):
```
Anālayo, Bhikkhu. "The Luminous Mind in Theravāda and Dharmaguptaka Discourses."
  *Journal of the Oxford Centre for Buddhist Studies* 13 (2017): 10–51.
  (Calibre #8904)
```

When publisher / year / page range are not available from the Calibre metadata, include
what is available and omit the rest — do not guess or invent publication details.

#### Online sources

```
Last, First (or Organisation). "Page Title." *Site Name*. Month Day, Year. URL.
```

Example:
```
Sujato, Bhikkhu. "The Nature of Nibbāna." *SuttaCentral*. Accessed May 25, 2026.
  https://suttacentral.net/...
```

#### Media sources (YouTube / Dhamma talks)

```
Teacher/Channel. "Talk Title." *YouTube*. Month Day, Year. URL.
  [Human captions | auto-captions — paraphrase only]
```

#### Vault sources referenced

```
[[Note Title]] — Vicaya research note, YYYY-MM-DD.
```

### Placement in the note

The `## Bibliography` section goes after `## Critical Gaps` and before the `---` footer
line. Footnote definitions (`[^id]: ...`) follow the footer, as now.

## Research phases (Phase 0 through 7)

Run these in order. Print a one-line status update before each phase so the user can follow along in their terminal.

**Skipping a phase:** Any phase that has no meaningful bearing on the question may be skipped (e.g. Phase 2 canon search for a secular topic, Phase 4b YouTube for a narrow Abhidhamma classification question). When you skip a phase: (1) print a one-line terminal note stating which phase and why, and (2) add a row to the `## Angles Not Pursued` table in the vault note with the phase name and reason.

## Investigation angles

A standing checklist of evidentiary lenses. For every research question, walk this
list once at the start of Phase 1 and decide per-angle whether it applies. **Applicable
angles must be searched** in Phases 2–4; **non-applicable angles are logged with a
one-line reason** in the scratchpad and, later, in the vault note's `## Angles Not
Pursued` table.

This is distinct from the *perspective map*. The perspective map names competing
**positions within a topic** (e.g. cessationist vs. realist Nibbāna). The angle list
names **evidentiary lenses across sources** (e.g. "what does the Abhidhamma say",
"what does cognitive science say"). The two complement each other: a position from
the perspective map may be supported or critiqued from several angles.

**Triage rule.** Apply liberally. If an angle could plausibly contribute *any*
evidence — corroborating, contradicting, or contextualising — mark it applicable.
Default to "applicable" when uncertain; the cost of one extra search is small,
the cost of a silent blind spot is large. Only mark "not applicable" when there
is a clear reason (e.g. archaeology has nothing to say about an Abhidhamma
classification question; cognitive science has little purchase on a Vinaya
procedure question).

Record the triage in the scratchpad before moving to Phase 2:

```markdown
## Angle triage
- Early Pāḷi (dhamma + vinaya): applicable — primary canon search
- EBT āgama parallels: applicable — SuttaCentral parallels + Anālayo
- Abhidhamma: not applicable — question is narratival, not analytical
- ...
```

### Textual layers

**1. Early Pāḷi — dhamma and vinaya.**
*Applies to:* almost every question on Buddhist doctrine, practice, or monastic life.
*Where to search:* canon DB sutta mūla (`s*_mul`) and Vinaya mūla (`vin*_mul`).
For Vinaya-relevant questions explicitly include `vin*_mul`. Use the Pāḷi-stem
truncation rule when searching Pāḷi.
*Satisfying hit:* a verbatim Pāḷi + English block-quote with a `resolve-citation`
human reference (e.g. *MN60 Apaṇṇakasuttaṃ para 97*).

**2. EBT āgama parallels — Chinese Āgamas, Sanskrit fragments, Tibetan parallels.**
*Applies to:* any sutta-level question where parallel recensions exist (most
Nikāya material has at least partial parallels).
*Where to search:*
- **`sc-parallels <uid>`** (offline SuttaCentral archive) — first call for any
  Pāḷi sutta. Returns the full parallel list from `parallels.json` (comprehensive)
  plus text and English translation where the partial archive has them. `text_gaps`
  explicitly flags missing texts rather than silently returning empty — log these
  as known gaps in Critical Gaps. The partial archive covers SA well, MA partially
  (~15 suttas), EA minimally — `text_gaps` will tell you.
- **EBC vault** (`get-ebc-overview <code>`) — provides named Āgama parallels with
  files readable via `Read`. Patton (MA) and BDK translations at
  `+Suttas/Sutta Texts/Agamas Dhamma pearls/` and `Agamas BDK/`.
- **Calibre `authors:Analayo`** — Bhikkhu Anālayo's *Comparative Study of the
  Majjhima-Nikāya* and related work is the standard T3 reference. Tags
  `Chinese Canon (Tripitaka)`, `Sanskrit Canon`, `Tibetan Canon`, `Comparative
  Studies`. Corporate author `84000` for Tibetan canon.
*Satisfying hit:* a named parallel (e.g. MĀ 16 for MN 60) with a citation to
Anālayo's comparative analysis or to a sectarian recension; an explicit note
when *no* parallel exists.

**3. Abhidhamma.**
*Applies to:* analytical questions — questions about mental factors, paths,
moments of consciousness, classifications of phenomena, the structure of
liberation, kamma mechanics.
*Where to search:* canon DB `abh*_mul` (mūla) and `abh*_att` (commentary).
Visuddhimagga (`e0101n_mul`, `e0102n_mul`) often functions as the practical
Abhidhamma reference. Calibre tag `Abhidhamma`; authors Bhikkhu Bodhi
(*Comprehensive Manual of Abhidhamma*), Nyanaponika Thera, Y. Karunadasa.
*Satisfying hit:* a canonical Abhidhamma classification or Visuddhimagga
treatment, cited with a paragraph or page reference.

**4. Late Khuddaka Nikāya — exegetical / proto-commentarial layer.**
*Applies to:* questions where the early layer is terse and the late-canonical
exegesis fills it out — meditation taxonomy, definitions of technical terms,
hermeneutical methods.
*Where to search:* canon DB `s05*_mul`, especially Niddesa (`s0515m_mul`,
`s0516m_mul`), Paṭisambhidāmagga (`s0517m_mul`), Nettippakaraṇa
(`s0519m_mul`), Peṭakopadesa (`s0520m_nrf`), Milindapañha (`s0518m_nrf`).
*Satisfying hit:* a definition, taxonomy, or hermeneutical principle from one
of these texts with a `resolve-citation` reference.

**5. Commentaries and ṭīkā — Theravāda exegetical tradition.**
*Applies to:* nearly every doctrinal question — the commentarial reading is one
of the major positions on almost any topic, and ṭīkā often refine or contest
it.
*Where to search:* canon DB `*_att` (aṭṭhakathā) and `*_tik` (ṭīkā). Mūla +
commentary together: `--books "s02*_mul" "s02*_att"`. Sub-commentaries:
`--books "*_tik"`. Visuddhimagga (`e0101n_mul`, `e0102n_mul`) is the great
commentarial summa. Calibre tags `Commentary`, `Atthakatha`.
*Satisfying hit:* a Buddhaghosa, Dhammapāla, or ṭīkā gloss cited with
paragraph reference; explicit note when the commentary diverges from a
plausible reading of the mūla.

### Other schools of Buddhism

**6. Mahāyāna / Vajrayāna / Yogācāra.**
*Applies to:* any question where a comparative-school reading enriches the
analysis (philosophy of mind, emptiness, bodhicitta, tantric practice,
buddha-nature, ālaya-vijñāna, two truths, etc.).
*Where to search:* Calibre tags `Mahayana`, `Mahayana Sutra`, `Madhyamaka`,
`Tibetan Buddhism`, `Zen Buddhism`, `Vajrayana` (verify against
`data/calibre_tags.csv`). Corporate author `84000` (the Tibetan translation
project, 36 books). Tag `Yogacara` may not exist verbatim — consult the csv,
fall back to free-text search `comments:yogacara` or
`comments:"consciousness-only"`. Web: 84000.co, Lotsawa House, Berzin Archives.
*Satisfying hit:* a school-specific position cited to a primary text or a
recognised secondary source; explicit comparison to the Theravāda reading
where the question warrants it.

### Comparative religion

**7. Sanskrit texts, Hindu and other Indian religions.**
*Applies to:* questions where Brahmanical, Jain, or Ājīvika context illuminates
the Buddhist position — meditation terminology with Upaniṣadic precedent,
debates the suttas engage (e.g. ātman, fire-imagery, varṇa), shared lexicon
(*dhamma*, *karma*, *yoga*, *samādhi*), comparative cosmology.
*Where to search:*
- **Local GRETIL corpus** (Phase 3b): `search-sanskrit` — Vedic, Epic, Upaniṣadic,
  and philosophical Sanskrit texts in IAST (`.htm` files; text is clean IAST with
  light HTML markup). Use `Path(hit.path).stem` to derive the text name (e.g.
  `avs___u` from `avs___u.htm`). Scope to a subfamily with `--folder` (e.g.
  `--folder 1_veda`). Only available when `VICAYA_GRETIL_PATH` is configured.
- **Calibre**: tag `Sanskrit Text`; verify against `data/calibre_tags.csv` whether
  `Hinduism`, `Jainism`, `Vedic`, `Upanishads`, `Indology`, `Indian Religion` exist
  as tags — use what is present, free-text otherwise. Authors: Patrick Olivelle,
  Johannes Bronkhorst, Richard Gombrich (esp. *How Buddhism Began*), Karel Werner.
- **Web**: GRETIL online (gretil.sub.uni-goettingen.de) when local corpus absent;
  *Encyclopædia of Indian Religions*.

*Satisfying hit:* a verbatim IAST passage from GRETIL with text name + line number,
**or** a Sanskrit / Vedic / Jain passage via Calibre or scholar's analysis showing
the term, debate, or image at issue; explicit note when the Buddhist position responds
to or departs from the precedent. Note: searching by English translation theme is
often more productive than searching IAST terms directly.

**8. Other religions — Christianity, Islam, Daoism, Confucianism, etc.**
*Applies to:* questions where cross-religious comparison is genuinely
illuminating — contemplative practice, mystical phenomenology, ethics,
soteriology. Apply selectively; do not force.
*Where to search:* Calibre tags `Comparative Religion`, `Comparative Studies`,
`Christianity`, `Mysticism`, `Daoism`, `Sufism` (verify against the csv).
Authors: Thomas Merton, Aldous Huxley, Bernadette Roberts, Daniel Ingram
(cross-traditional contemplative writing). Web: standard comparative religion
journals.
*Satisfying hit:* a structurally analogous claim from another tradition with
proper attribution; explicit note on where the analogy breaks down.

### Modern voices

**9. Modern teachers — living and recent (20th–21st c.) lineage holders and lay teachers.**
*Applies to:* every practical or applied question; most doctrinal questions
benefit from modern framing.
*Where to search:* Calibre — Thai Forest (`Ajahn Chah`, `Ajahn Brahmavamso`,
`Thanissaro Bhikkhu`, `Ajahn Sumedho`, `Ajahn Amaro`), Burmese (`Mahasi
Sayadaw`, `Pa-Auk Sayadaw`, `Sayadaw U Tejaniya`), Sri Lankan (`Nyanaponika
Thera`, `Bhikkhu Bodhi`, `Bhikkhu Anālayo`), Goenka tradition (`Vipassana
Research Institute`, 249 books). Tags `dhamma talk` (434 books), `Thai Forest
Tradition`, `Sri Lankan Tradition`, `Myanmar Tradition`. YouTube via
`search-youtube` — the channel allowlist already prioritises trusted modern
teachers.
*Satisfying hit:* a teaching from a recognised modern teacher cited with book
+ page or YouTube video + timestamp; ideally cite teachers from at least two
distinct lineages so the modern voice is not monochromatic.

### Academic disciplines

**10. Sociology — Buddhism as social formation, monasticism, lay-monastic relations, sect dynamics.**
*Applies to:* questions about institutional structure, monastic economics,
gender, ethnic Buddhism, modern Buddhism in society, conversion, reform
movements.
*Where to search:* Calibre — consult `data/calibre_tags.csv` for `Sociology`,
`Anthropology`, `Religious Studies`, `Buddhist Studies` clusters. Authors:
Melford Spiro, Stanley Tambiah, Donald Lopez, David McMahan (*The Making of
Buddhist Modernism*), Heinz Bechert. Web: *Journal of Buddhist Ethics*,
*Contemporary Buddhism*.
*Satisfying hit:* an empirical or theoretical sociological claim cited to a
named scholar.

**11. Psychology — clinical, depth, contemplative.**
*Applies to:* questions about mind, defilements, meditation effects,
suffering, healing, identity, the relation between *citta* / *mano* /
*viññāṇa* and modern constructs.
*Where to search:* Calibre tag `Psychology` (668 books, well-populated), plus
`Buddhist Psychology` (verify in csv), `Phenomenology`. Authors: Jack Engler,
John Welwood, Mark Epstein, Daniel Goleman, Rick Hanson, Tara Brach, Bhikkhu
Anālayo (*Satipaṭṭhāna* + meditation studies), Y. Karunadasa.
*Satisfying hit:* a psychological framing or finding paired with the Buddhist
term it engages, cited to a book or paper.

**12. Philosophy — analytic, phenomenological, comparative, history of philosophy.**
*Applies to:* questions about ontology, epistemology, philosophy of mind,
ethics, time, causation, personal identity, free will, language; also
**constructed selfhood, phenomenal experience, and anattā** (phenomenology is
directly relevant to Buddhist self-theory and mind-construction topics).
*Where to search:* Calibre tag `Philosophy` (631 books). Authors: Mark Siderits,
Jay Garfield, Evan Thompson, Jonardon Ganeri, Steven Collins (*Selfless
Persons*, *Nirvana and Other Buddhist Felicities*), Charles Goodman, Owen
Flanagan. **Phenomenology specifically:** Thomas Metzinger (*Being No One*,
*The Ego Tunnel* — phenomenal self model, PSM; central to anattā / constructed
selfhood), Dan Zahavi (*Subjectivity and Selfhood*, *Phenomenology and the
Self*; leading Buddhism–phenomenology bridge scholar), Maurice Merleau-Ponty
(embodied perception — relevant to vedanā and sense-contact topics). Series:
Routledge philosophy of religion, OUP. Web: *Stanford Encyclopedia of
Philosophy* entries on Buddhism, *Philosophy East and West*.
*Satisfying hit:* a philosophical analysis or argument cited to a named
philosopher.

**13. Cognitive science — neuroscience, contemplative science, embodied/enactive cognition.**
*Applies to:* meditation, attention, awareness, perception, default-mode
network, embodied self, predictive processing, contemplative training studies.
*Where to search:* Calibre tags `Cognitive Science`, `Neuroscience`,
`Consciousness`. Authors: Francisco Varela, Evan Thompson (*Mind in Life*,
*Waking, Dreaming, Being*), Antoine Lutz, Richard Davidson, Wendy Hasenkamp,
Cliff Saron, Judson Brewer. Web: *Mind & Life Institute*, *Frontiers in Human
Neuroscience*.
*Satisfying hit:* a cognitive-science result or theoretical framework paired
with the Buddhist construct it engages, cited.

**14. Archaeology — material culture, sites, inscriptions, art history.**
*Applies to:* questions about early Buddhist history, Aśokan period, monastic
architecture, relics, the historical Buddha, regional spread, dating debates.
*Where to search:* Calibre — consult `data/calibre_tags.csv` for `Archaeology`,
`Art History`, `Inscriptions`, `Material Culture`. Authors: Gregory Schopen
(esp. *Bones, Stones, and Buddhist Monks*), Lars Fogelin, Robert DeCaroli, Akira
Hirakawa (early Mahāyāna archaeology). Web: ASI publications, *South Asian
Studies*.
*Satisfying hit:* an inscription, site report, or material-culture finding
cited to a named scholar or archaeological report.

**15. History — origins, transmission, sectarian development, regional histories, modern history.**
*Applies to:* questions about sectarian splits, councils, transmission to Sri
Lanka / China / Tibet / SE Asia, modern reform movements, the historical
Buddha, dating of texts.
*Where to search:* Calibre tag `History` (808 books, well-populated). Authors:
Étienne Lamotte (*History of Indian Buddhism*), Erich Frauwallner, Hirakawa
Akira, Andrew Skilton (*A Concise History of Buddhism*), Richard Gombrich,
Heinz Bechert, Donald Lopez. Web: *Journal of the International Association of
Buddhist Studies*.
*Satisfying hit:* a historical claim with a date, place, and scholarly source.

**16. Cross-school / Āgama comparison — Chinese, Sanskrit, Tibetan recensions.**
*Applies to:* questions explicitly about school divergence, EBT critical history,
doctrinal development, or transmission — cases where the Pāḷi alone gives a
one-school picture and parallel recensions materially change the analysis.
*Where to search:*
- `sc-parallels <uid>` for any anchoring Pāḷi sutta — see angle 2 for detail.
- `sc-search <term> --lang lzh` to grep the offline Chinese Āgama root texts directly.
- `sc-search <term> --lang san` / `--lang pra` for Sanskrit/Prakrit fragments.
- EBC vault `Agamas Dhamma pearls/` (Patton translations) and `Agamas BDK/` (BDK translations).
- Calibre `authors:Analayo`, `authors:Bingenheimer` (SA), `authors:Choong` (EA), tags `Comparative Studies`, `Chinese Canon (Tripitaka)`.
**Hard rule — machine-translated Chinese is comprehension-only.** When no
published translation exists, machine translation may be used as a reading aid
to assess relevance. It must **never** be quoted in the vault note as a
translation. Only published translations (Patton, BDK, Anālayo, Bingenheimer,
Sujato where available) may be quoted. Absent a published translation, paraphrase
and mark as "(no published translation; summary from Chinese source)".
*Satisfying hit:* a named parallel recension with a published translation quote,
or an explicit statement of doctrinal divergence between Pāḷi and Āgama versions
with both sides cited.

### Phase 0 — Scope check

Ask the user these five questions before doing anything else. Present them together in a single message — don't ask one at a time. Wait for the response, then carry the answers into Phase 1.

1. **Textual scope** — Are you asking about the mūla (root canon), the commentarial tradition, or both? Any particular Nikāya or text?
2. **Interpretive dispute** — Is there a specific school, teacher, or scholarly debate you want foregrounded, or should the note map the main positions neutrally?
3. **Depth** — Full note (~3,500 words, all applicable angles) or a focused answer on one specific aspect?
4. **Practical angle** — Do you want the note to connect the topic to practice and modern teachers, or keep it primarily textual/scholarly?
5. **Seeds** — Any specific suttas, scholars, books, or vault notes you already know are relevant?

If the question already answers most of these (e.g. `/vicaya the cessationist vs. realist readings of Nibbāna in the commentaries`) skip the questions and proceed directly to Phase 1 — don't ask for confirmation the user doesn't need.

### Phase 1 — Vault context

**Angle triage first.** Before anything else in this phase, walk the standing
checklist in **Investigation angles** above and decide per-angle whether it
applies to this question. Record the triage in the scratchpad. Applicable
angles dictate the search scope of Phases 2–4; non-applicable angles will be
logged in the vault note's `## Angles Not Pursued` table with a one-line
reason.

Then search the existing vault for prior notes related to the topic. The user has been writing in this vault for years; new research must build on, not duplicate, what's there.

```bash
uv run tools/research_sources.py search-vault "<key terms>" --limit 20
```

Pull up to 4 search variations (Pāḷi term, English gloss, related concept). Summarise the top hits in your own working notes — you'll cite the most relevant ones in the final note via `[[wiki-links]]`.

**If `search-vault` returns 0 on terms you'd expect to find**, fall back to `rg "<term>" <vault-path>` — the helper has a known diacritic/index bug that can silently miss files `rg` finds.

**EBC seed lookup** — if the question is anchored on one or more specific suttas (named in the user's question, or surfaced by the vault search), call `get-ebc-overview <code>` once per sutta. The returned `parallels_agama` and `parallels_partial` lists feed directly into the perspective map and the Phase 3 parallel-evidence search; the `themes`, `formula`, and `training` fields can suggest related suttas you might otherwise miss. This costs nothing and replaces a SuttaCentral parallel-table lookup.

For thematic (non-sutta-anchored) questions, `grep -F "<theme>" "$VICAYA_EBC_VAULT_PATH/Catalogue/Suttas-Catalogue.tsv"` is the cheapest way to surface a candidate sutta list before Phase 2 — the TSV has columns for theme, topic, training, formula, and parallels.

**Perspective map.** Before moving to Phase 2, explicitly name the 2–5 competing positions or schools of thought the question touches. Examples: "Theravāda commentarial vs. Ñāṇavīra structural", "cessationist vs. realist readings of Nibbāna", "three-lives vs. momentary paṭiccasamuppāda". If the question is purely factual with no interpretive dispute, skip this step. Otherwise, tag subsequent evidence — canon hits, library sources, web sources — as supporting a named position. This ensures the final note covers all significant views, not just the first position the search surfaces.

**Counter-perspective search.** For each position named in the perspective map, actively search for sources that support it — don't rely on the first position the keyword searches happen to surface. If a web or canon search returns only one school's voice, run a second search scoped to a known proponent of the opposing view (e.g. `authors:Analayo` for early-Buddhist readings, a specific scholar for the academic critique). Evidence gaps for any named position belong in Critical Gaps, not silent omission.

→ **Scratch** — append Phase 1 results: angle triage (applicable + not-applicable with reasons), vault hit list, perspective map positions, counter-perspective targets.

### Phase 2 — Canon search

**Book code map** — all codes are embedded here. Never guess a code from memory.

Codes come directly from the CST XML file headers. The suffix `_mul` = mūla (root text);
`_att` = aṭṭhakathā (commentary); `_tik` = ṭīkā (sub-commentary). Pass codes verbatim
to `--books`.

**Each book code is also the exact SQLite table name in the canon database.** For example,
the Paṭisambhidāmagga mūla is stored in a table named `s0517m_mul`, with columns
`paranum`, `pali`, `english`, `chinese`. The `search-canon` helper queries these tables
directly using the codes you pass to `--books`. This means you can also query the database
directly via `sqlite3` if you need ordered paragraph access (e.g. `SELECT paranum, pali,
english, chinese FROM s0517m_mul ORDER BY CAST(paranum AS INTEGER) LIMIT 5`).

#### Aggregate patterns

| Scope | Mūla | Commentary |
|---|---|---|
| All suttas | `s*_mul` | `s*_att` |
| Dīgha Nikāya | `s01*_mul` | `s01*_att` |
| Majjhima Nikāya | `s02*_mul` | `s02*_att` |
| Saṃyutta Nikāya | `s03*_mul` | `s03*_att` |
| Aṅguttara Nikāya | `s04*_mul` | `s04*_att` |
| Khuddaka Nikāya | `s05*_mul` | `s05*_att` |
| Vinaya | `vin*_mul` | `vin*_att` |
| Abhidhamma | `abh*_mul` | `abh*_att` |
| Sub-commentaries (all) | — | `*_tik` |

Mūla + commentary together: `--books "s02*_mul" "s02*_att"`

#### Dīgha Nikāya (Sumaṅgalavilāsinī)

| Mūla | Aṭṭhakathā | Pāḷi title | Suttas |
|---|---|---|---|
| `s0101m_mul` | `s0101a_att` | Sīlakkhandhavaggapāḷi | DN 1–13 |
| `s0102m_mul` | `s0102a_att` | Mahāvaggapāḷi | DN 14–23 |
| `s0103m_mul` | `s0103a_att` | Pāthikavaggapāḷi | DN 24–34 |

#### Majjhima Nikāya (Papañcasūdanī)

| Mūla | Aṭṭhakathā | Pāḷi title | Suttas |
|---|---|---|---|
| `s0201m_mul` | `s0201a_att` | Mūlapaṇṇāsapāḷi | MN 1–50 |
| `s0202m_mul` | `s0202a_att` | Majjhimapaṇṇāsapāḷi | MN 51–100 |
| `s0203m_mul` | `s0203a_att` | Uparipaṇṇāsapāḷi | MN 101–152 |

#### Saṃyutta Nikāya (Sāratthappakāsinī)

| Mūla | Aṭṭhakathā | Pāḷi title | Saṃyuttas |
|---|---|---|---|
| `s0301m_mul` | `s0301a_att` | Sagāthāvaggo | SN 1–11 |
| `s0302m_mul` | `s0302a_att` | Nidānavaggo | SN 12–21 |
| `s0303m_mul` | `s0303a_att` | Khandhavaggo | SN 22–34 |
| `s0304m_mul` | `s0304a_att` | Saḷāyatanavaggo | SN 35–44 |
| `s0305m_mul` | `s0305a_att` | Mahāvaggo | SN 45–56 |

#### Aṅguttara Nikāya (Manorathapūraṇī)

Note: 11 mūla files consolidate into 4 commentary files.

| Mūla | Aṭṭhakathā | Pāḷi title | Nipātas |
|---|---|---|---|
| `s0401m_mul` | `s0401a_att` | Ekakanipātapāḷi | AN 1 |
| `s0402m1_mul` | `s0402a_att` | Dukanipātapāḷi | AN 2 |
| `s0402m2_mul` | *(in s0402a_att)* | Tikanipātapāḷi | AN 3 |
| `s0402m3_mul` | *(in s0402a_att)* | Catukkanipātapāḷi | AN 4 |
| `s0403m1_mul` | `s0403a_att` | Pañcakanipātapāḷi | AN 5 |
| `s0403m2_mul` | *(in s0403a_att)* | Chakkanipātapāḷi | AN 6 |
| `s0403m3_mul` | *(in s0403a_att)* | Sattakanipātapāḷi | AN 7 |
| `s0404m1_mul` | `s0404a_att` | Aṭṭhakanipātapāḷi | AN 8 |
| `s0404m2_mul` | *(in s0404a_att)* | Navakanipātapāḷi | AN 9 |
| `s0404m3_mul` | *(in s0404a_att)* | Dasakanipātapāḷi | AN 10 |
| `s0404m4_mul` | *(in s0404a_att)* | Ekādasakanipātapāḷi | AN 11 |

#### Khuddaka Nikāya

| KN # | Mūla | Aṭṭhakathā | English name |
|---|---|---|---|
| 1 | `s0501m_mul` | `s0501a_att` | Khuddakapāṭha |
| 2 | `s0502m_mul` | `s0502a_att` | Dhammapada |
| 3 | `s0503m_mul` | `s0503a_att` | Udāna |
| 4 | `s0504m_mul` | `s0504a_att` | Itivuttaka |
| 5 | `s0505m_mul` | `s0505a_att` | Suttanipāta |
| 6 | `s0506m_mul` | `s0506a_att` | Vimānavatthu |
| 7 | `s0507m_mul` | `s0507a_att` | Petavatthu |
| 8 | `s0508m_mul` | `s0508a1_att` `s0508a2_att` | Theragāthā |
| 9 | `s0509m_mul` | `s0509a_att` | Therīgāthā |
| 10 | `s0510m1_mul` `s0510m2_mul` | `s0510a_att` | Apadāna |
| 11 | `s0511m_mul` | `s0511a_att` | Buddhavaṃsa |
| 12 | `s0512m_mul` | `s0512a_att` | Cariyāpiṭaka |
| 13–14 | `s0513m_mul` `s0514m_mul` | `s0513a1_att` `s0513a2_att` `s0513a3_att` `s0513a4_att` `s0514a1_att` `s0514a2_att` `s0514a3_att` | Jātaka |
| 15 | `s0515m_mul` | `s0515a_att` | Mahāniddesa |
| 16 | `s0516m_mul` | `s0516a_att` | Cūḷaniddesa |
| 17 | `s0517m_mul` | `s0517a_att` | Paṭisambhidāmagga |
| 18 | `s0518m_nrf` | — | Milindapañha |
| 19 | `s0519m_mul` | `s0519a_att` | Nettippakaraṇa |
| 20 | `s0520m_nrf` | — | Peṭakopadesa |

To search mūla + commentary together for one KN book:
`--books s0502m_mul s0502a_att` (Dhammapada + Dhammapada-aṭṭhakathā)

#### Vinaya (Samantapāsādikā)

| Mūla | Aṭṭhakathā | Pāḷi title |
|---|---|---|
| `vin01m_mul` | `vin01a_att` | Pārājikapāḷi |
| `vin02m1_mul` | `vin02a1_att` | Pācittiyapāḷi |
| `vin02m2_mul` | `vin02a2_att` | Mahāvaggapāḷi |
| `vin02m3_mul` | `vin02a3_att` | Cūḷavaggapāḷi |
| `vin02m4_mul` | `vin02a4_att` | Parivārapāḷi |

#### Abhidhamma

| Mūla | Aṭṭhakathā | Pāḷi title | Book |
|---|---|---|---|
| `abh01m_mul` | `abh01a_att` | Dhammasaṅgaṇīpāḷi | Abh 1 |
| `abh02m_mul` | `abh02a_att` | Vibhaṅgapāḷi | Abh 2 |
| `abh03m1_mul` | `abh03a_att` | Dhātukathāpāḷi | Abh 3 |
| `abh03m2_mul` | *(in abh03a_att)* | Puggalapaññattipāḷi | Abh 4 |
| `abh03m3_mul` | *(in abh03a_att)* | Kathāvatthupāḷi | Abh 5 |
| `abh03m4_mul` `abh03m5_mul` `abh03m6_mul` | *(in abh03a_att)* | Yamakapāḷi | Abh 6 |
| `abh03m7_mul` … `abh03m11_mul` | *(in abh03a_att)* | Paṭṭhānapāḷi | Abh 7 |

#### Post-canonical

| Code | Pāḷi title | Notes |
|---|---|---|
| `e0101n_mul` `e0102n_mul` | Visuddhimaggo | Buddhaghosa's path manual (2 vols) |

Infer the canon scope from the question. Examples:
- "in the suttas" → `--books s*_mul`
- "in the suttas and commentaries" → `--books "s*_mul" "*_att"`
- "in the Vinaya" → `--books vin*_mul`
- "in the Abhidhamma" → `--books abh*_mul`
- "in the Khuddaka" → `--books s05*_mul`
- Unspecified → default to suttas mūla (helper default, `books=None`)

**Pāḷi inflection rule — always truncate to the stem.** The canon text contains inflected forms (`dhammo`, `dhamme`, `dhammena`, `dhammānaṃ`, `nibbānaṃ`, `nibbānassa`, etc.), not the nominative citation form. A search for `dhamma` matches only 317 rows in MN vol1; `dhamm` (stem) matches 594. Always drop the final vowel or case ending down to the invariant stem before searching:

| Citation form | Search stem |
|---|---|
| dhamma | `dhamm` |
| nibbāna | `nibbān` |
| saṃsāra | `saṃsār` |
| vipassanā | `vipassan` |
| paṭiccasamuppāda | `paṭiccasamuppād` |
| khandha | `khandh` |

When in doubt, drop one more character than you think you need — substring match means no false positives from truncating too far, only more hits.

```bash
uv run tools/research_sources.py search-canon "<Pāḷi stem>" --books "s*_mul" --lang pali --limit 20
# Also try English if the user used English terms:
uv run tools/research_sources.py search-canon "<English term>" --books "s*_mul" --lang english --limit 20
```

**Example — search for "ñāṇa" in the Paṭisambhidāmagga only, get Pāḷi + English:**

```bash
uv run tools/research_sources.py search-canon "ñāṇa" --books s0517m_mul --lang pali --limit 20
```

Returns `CanonHit` objects. Read `pali` and `english` fields directly — there is no `snippet` field:

```json
{
  "book_code": "s0517m_mul",
  "paranum": "1",
  "pali": "Sotāvadhāne paññā sutamaye ñāṇaṃ.",
  "english": "In attentive hearing, wisdom is knowledge born of hearing.",
  "chinese": "于专注听闻的智慧，是闻所成智。"
}
```

Then confirm which sutta the paragraph belongs to:

```bash
uv run tools/research_sources.py resolve-citation s0517m_mul 1
```

For each hit you'll cite, run `resolve-citation` with that hit's `book_code` and `paranum` to get the human-readable reference (e.g. `MN60 Apaṇṇakasuttaṃ para 97`):

```bash
uv run tools/research_sources.py resolve-citation s0201m_mul 23
```

**Parallel argument structures — pull the whole range.** Many suttas run the same argument across multiple parallel blocks (e.g. MN60's five rebirth-wager positions, AN 4.170's four paths, the five-aggregate formulae). Keyword search returns only the blocks containing your keyword — typically 1–2 of 5–10. When hits show a repeating formula (`''Tatra, gahapatayo…`, `''Kathañca…`, `''Idha bhikkhave…`), the other blocks carry the same structure with different terms and will be missed. Fix: find the `id` of the first hit and the `id` of the next sutta subhead, then pull everything in between:

```bash
CANON_DB=$(eval echo $(grep VICAYA_CANON_DB /home/bodhirasa/MyFiles/3_Active/vicaya/.env | cut -d= -f2-))
sqlite3 "$CANON_DB" \
  "SELECT id, paranum, pali_text, english_translation FROM <table> WHERE id BETWEEN <start_id> AND <end_id>;"
```

**When a search hit has empty `paranum`** — this is normal for subhead, gatha, and continuation rows within a paragraph (only the first row of each paragraph carries `paranum`). To find the owning sutta, query by `id`:

```bash
CANON_DB=$(eval echo $(grep VICAYA_CANON_DB /home/bodhirasa/MyFiles/3_Active/vicaya/.env | cut -d= -f2-))
# Find the nearest preceding paranum for a hit at row <id>:
sqlite3 "$CANON_DB" \
  "SELECT paranum FROM <table> WHERE id < <hit_id> AND paranum != '' ORDER BY id DESC LIMIT 1;"
# Then resolve it:
uv run tools/research_sources.py resolve-citation <table> <paranum>
```

If the hit is a `subhead` rend (the row introduces the next sutta), prefer looking forward — the following non-empty `paranum` is the sutta it names. If it is a continuation `bodytext` or `gatha`, look backward — the preceding non-empty `paranum` owns it.

**Quote fully, not representatively.** Pull up to 20 of the most pertinent paragraphs and plan to use all of them in the Canon Evidence section — not just a curated sample. "Genuinely relevant" means relevant to at least one position in the perspective map; it does not mean "I'll pick the 2–3 best." If you retrieved 15 hits and your final note cites 3, you have discarded evidence without cause.

**⚠️ IRON RULE — Paragraph numbers are book-global.** The `paranum` in a `CanonHit` is a continuous index across the entire book file, not local to the sutta. Always run `resolve-citation` to confirm which sutta a paragraph belongs to before citing it (see Hard Rule 9).

**After individual hits cluster in the same book or nipāta, scan the wider structural unit.** Stem-search returns scattered paragraph hits but misses thematic chapter blocks (e.g. AN8.31–39 dāna chapter, SN35.* sense-contact group). When hits concentrate in one table, do a broader window query:

```bash
sqlite3 "$CANON_DB" \
  "SELECT id, paranum, pali_text, english_translation FROM <table> \
   WHERE id BETWEEN <first_cluster_id - 50> AND <last_cluster_id + 200> \
   AND pali_text != '' ORDER BY id;"
```

This surfaces chapter-level collections the keyword search misses.

**CST schema reference.** All CST tables share this column set (verify once with `PRAGMA table_info(<table>)` if unsure):

| Column | Type | Notes |
|---|---|---|
| `id` | INTEGER PK | monotonically increasing, book-global |
| `rend` | TEXT | TEI element class (`bodytext`, `gatha`, `subhead`, `pb`, …) — stripped from `pali` / `english` before return |
| `paranum` | TEXT | book-global paragraph number; empty on continuation rows |
| `pali_text` | TEXT | Pāḷi source (NFC UTF-8 diacritics) |
| `myanmar_pali_text` | TEXT | Myanmar script Pāḷi |
| `chinese_translation` | TEXT | Chinese translation where available |
| `english_translation` | TEXT | English translation where available |
| `english_translation_mark` | TEXT | translator initials / mark |

Table-name suffixes: `_mul` = mūla, `_att` = aṭṭhakathā, `_tik` = ṭīkā, `_nrf` = non-canonical reference.

**Diacritics in direct SQL.** The canon db stores NFC UTF-8 with native Pāḷi diacritics. Direct SQL `LIKE` must use the real characters (`ñ`, `ā`, `ṭ`, etc.). Example: `WHERE pali_text LIKE '%papañca%'` → hits correctly. `WHERE pali_text LIKE '%papanca%'` → 0 hits. The ASCII-stripping rule applies *only* to Calibre; never strip diacritics for canon SQL.

→ **Scratch** — append Phase 2 results: queries run, all human refs resolved, any empty-result gaps.

#### EBC parallel-evidence pull

For every sutta cited from the Pāḷi canon in Phase 2, pull the matching parallel evidence from EBC. This is what the Phase 1 `get-ebc-overview` call set up:

1. **Chinese Āgama parallels.** From the overview's `parallels_agama` list, pick the closest parallel(s) (full parallels first, then partial). `Read` the Patton translation at `+Suttas/Sutta Texts/Agamas Dhamma pearls/<nik>-patton/<code>-patton.md`, falling back to BDK at `Agamas BDK/<nik>-bdk/<code>-bdk.md` if no Patton file exists. Quote verbatim with paragraph numbers and attribute to the translator (e.g. *Madhyamāgama 98, trans. Charles Patton, §5*). This is T1 evidence for the parallel recension and is *not* substitutable by a SuttaCentral link.
2. **Alternative Pāḷi translations.** When a translator-specific reading is doctrinally load-bearing (e.g. a contested term like *vitakka* / *vicāra* or *upādāna*), pull a second translator from `Sutta Texts/Bodhi/`, `Sujato-pali/`, `dn_walshe/`, or `Thanissaro notes/` and quote side-by-side. T3.
3. **Vinaya rule + commentary.** For Vinaya questions, after the canon mūla quote, pull bmc1 (`+Vinaya/Patimokkha/bmc1/`) for Ṭhānissaro's analysis and/or Ñāṇatusita (`+Vinaya/Patimokkha/Ñañatusita/`). T2.

Pāḷi names in EBC use exact diacritics, same as the canon db. The overview-card paths are absolute — copy them directly into `Read`. If a named parallel has no file (rare), note it as a known gap rather than silently dropping the parallel.

→ **Scratch** — append the EBC pulls: parallel codes consulted, files read, any missing parallels logged as gaps.

### Phase 2.5 — SuttaCentral offline parallel search

**Run this phase when angle 16 (Cross-school / Āgama comparison) is applicable,**
or whenever any Phase 2 Pāḷi canon hit warrants a quick parallel enrichment.

For any sutta cited in Phase 2, run:

```bash
uv run tools/research_sources.py sc-parallels <uid>
# e.g. sc-parallels mn18  or  sc-parallels sn35.28
```

This returns every known parallel from `parallels.json` (comprehensive coverage)
plus text + translation where the offline archive holds them. Check `text_gaps` —
if it is non-empty, the parallel exists but its text is not in the archive; log it
as a known gap in Critical Gaps rather than silently omitting.

For comparative/Āgama-focused questions, search the Chinese Āgama root texts directly:

```bash
uv run tools/research_sources.py sc-search "<term>" --lang lzh --limit 20
uv run tools/research_sources.py sc-search "<term>" --lang san --limit 20
```

**Published-translation requirement.** Root text (`text_lzh`, `text_san`) is the
primary source; a published English translation must accompany any quotation
(Patton for MA, Bingenheimer for SA, BDK). If no published translation exists for
a passage, paraphrase and label "(no published translation available)". Machine-translated
Chinese is a reading aid for the agent only — never quote it as a translation.

→ **Scratch** — append Phase 2.5 results: sc-parallels output per sutta, any text gaps logged.

### Phase 3 — Library search

**Phase 3 preflight — check the library is reachable before querying:**

```bash
uv run tools/research_sources.py calibre-check
```

If this exits 1, the library is locked — typically by the Calibre desktop GUI or
a parallel Vicaya agent. The message tells you which. Options: close the GUI,
wait for the other agent to finish, or proceed without Calibre and note the gap.
Do not silently return 0-hit results when the cause is a lock.

The user's Calibre library is whole-library non-fiction (Buddhism, religion, psychology). The tag vocabulary is in `<repo>/data/calibre_tags.csv` (~2k tags).

**Tag vocabulary first.** Before guessing technical terms, list the real tag vocabulary:
```bash
uv run tools/research_sources.py search-calibre "" --tags <candidate> --limit 1
# Or: grep -i "<concept>" data/calibre_tags.csv
```
Pick the closest existing tag — don't invent terms like `Yogacara` if the library
uses `Yogācāra` or `Consciousness-Only` instead. When in doubt, use the csv.

Pick up to 3 tags relevant to the question (e.g. `Abhidhamma`, `Buddhism`, `Vipassana`, `Meditation`). Tag names are exact strings; matching is case- and diacritic-insensitive.

```bash
uv run tools/research_sources.py search-calibre "<term>" --tags Buddhism --limit 20
```

**Parallel-agent note.** Calibre is single-process; concurrent Vicaya agents will
hit lock contention mid-session (not just at the start). The helper automatically
retries on lock errors with backoff, but persistent contention degrades to 0 results
that look like "nothing found". If early queries succeed and later ones return 0 on
terms that should match, the cause is likely lock contention, not vocabulary.
Fallback: use book IDs from earlier hits to extract content directly with the
format-appropriate tool (see below).

**Format-agnostic extraction.** Books are in any format — PDF, epub, MOBI, doc,
txt, AZW3, or others. Never assume epub. Per-format extraction:

| Format | Command |
|---|---|
| PDF | `pdftotext /path/to/book.pdf -` |
| epub | `unzip -o /path/to/book.epub -d /tmp/epub_extract && rg "<term>" /tmp/epub_extract/` |
| Any format | `ebook-convert /path/to/book.<ext> /tmp/book.txt && rg "<term>" /tmp/book.txt` |

`ebook-convert` (ships with Calibre) is the universal fallback. The book's Calibre
path is in the metadata returned by `search-calibre` or from the library's folder.

**`authors:` zero-hit fallback.** If a known author returns 0 via `authors:`, the
query may have gone down a different path than title/FTS. Fall back: search by title
keyword or a distinctive term from the book, and read the `authors` field from the
returned hits. E.g. `search-calibre "Armstrong" --limit 5` then inspect `authors`.

If FTS isn't ready (the helper handles this silently), you'll get metadata hits — book titles whose name/author/comments match. Still useful; note them as "potentially relevant reading" rather than quoting.

If FTS *is* ready, snippets come back with each hit — quote them with book + author attribution.

#### Calibre search guidelines (library shape, read before searching)

The library currently holds **12,501 books**, **2,140 tags**, **6,042 author
entries**, **607 series**, and **21 languages**. Searches frequently miss
because the agent guesses the wrong tag, the wrong author form, or scopes too
narrowly. The next several subsections fix this.

**1. `calibredb --search` syntax cheat sheet.** The helper passes its
expression straight to Calibre. The grammar is:

| Form | Meaning |
|---|---|
| `nibbana` | free-text match across all fields |
| `title:nibbana` | scope to title |
| `authors:Analayo` | scope to authors |
| `tags:Nibbana` | tag contains "Nibbana" (loose) — also catches `Parinibbana` |
| `tags:"=Nibbana"` | tag equals "Nibbana" exactly (what the helper uses) |
| `series:"Wheel Publication"` | scope to series |
| `publisher:"Pali Text Society"` | scope to publisher |
| `comments:jhana` | scope to the comments / description field |
| `languages:eng` | scope to language code |
| `A and B` / `A or B` / `not A` | boolean joins |
| `"two words"` | quoted phrase |

**2. Diacritics and case do not matter.** Calibre's metadata search is
already case- and diacritic-insensitive. Verified live:
`title:paticcasamuppada`, `title:Paticcasamuppada`, and
`title:paṭiccasamuppāda` all return the same 13 hits. The helper still
strips diacritics for safety, but **do not waste a second round trying the
other form** — if `paticcasamuppada` returned 0, `paṭiccasamuppāda` will
also return 0. (This refines Hard Rule 3 for Calibre specifically; the canon
SQLite and the vault still demand exact diacritics.)

**3. Tag matching: exact vs. loose.** The helper uses **exact match**
(`tags:"=Nibbana"`) which returns 52 books. Loose match (`tags:Nibbana`)
returns 60 — the extra 8 come from `Parinibbana` and the stray
diacritic-form `Nibbāna`. Exact is the default because it's more precise.
**To widen when results are thin:** pass multiple related tags to the helper
(`--tags Nibbana Parinibbana Nibbida`), or drop tags entirely and rely on
free-text + post-filter on the returned `tags` field.

**4. Tag vocabulary clusters (the realistic shape).** The vocab is
fragmented — there is no single canonical form for many concepts. Always
consider the cluster, not just the first name that comes to mind.

| Cluster | Tags to consider together |
|---|---|
| Pāḷi Canon meta | `Pali Canon`, `Pāli Canon`, `Pali Canon (Tipitaka)`, `Pali Canon (About)`, `Tipitaka`, `Canon` |
| Nikāyas | `Digha Nikaya`, `Majjhima Nikaya`, `Samyutta Nikaya`, `Anguttara Nikaya`, `Khuddaka Nikaya`, `Nikayas` |
| Other canons | `Chinese Canon (Tripitaka)`, `Tibetan Canon`, `Sanskrit Canon`, `Zen Canon`, `Extra-Canonical` |
| Doctrinal core | `Anatta`, `Anapanasati`, `Satipatthana`, `Jhana`, `Vipassana`, `Mindfulness`, `Meditation`, `Rebirth`, `Death & Dying`, `Nibbana`, `Parinibbana`, `Doctrine` |
| Theravāda traditions | `Theravada`, `Thai Forest Tradition`, `Sri Lankan Tradition`, `Myanmar Tradition`, `Early Buddhism` |
| Non-Theravāda schools | `Tibetan Buddhism`, `Zen Buddhism`, `Mahayana`, `Madhyamaka`, `Mahayana Sutra` |
| Language / philology | `Pali Text`, `Pali Grammar`, `Pali Literature`, `Sanskrit Text`, `English Translation`, `Commentary`, `Atthakatha`, `Sutta Studies` |
| Adjacent fields | `Psychology`, `Philosophy`, `Phenomenology`, `Neuroscience`, `Cognitive Science`, `Consciousness`, `Comparative Studies`, `Comparative Religion` |
| Noise — ignore | `!tagme` (621 books), `!name me` (230), `Readme!` (93), `Unknown` (in authors, 346) |

Top tags by count (sanity check for "is this a real tag"): Academic 2085,
Buddhism 957, English Translation 893, History 808, Psychology 668,
Philosophy 631, Meditation 574, Pali Canon (Tipitaka) 552, Tibetan Buddhism
538, Pali Text 514, dhamma talk 434, Doctrine 415, Mindfulness 390. The full
list is in `data/calibre_tags.csv`.

**5. Author naming conventions (strip the title).** The library mixes many
honorific patterns: "Bhikkhu X" (58 entries), "X Bhikkhu" (25), "Ajahn X"
(38), "X Sayadaw" (22), "Ven. X" (98), "Dr. X" (56). Top authors: Piya Tan
(1,293), Bhikkhu Anālayo (410), Vipassana Research Institute (249), Pali
Text Society (114), Anandajoti Bhikkhu (104), Bhikkhu Bodhi (79),
Thanissaro Bhikkhu (76), Ajahn Brahmavamso (58), Ajahn Chah (49), Mahasi
Sayadaw (45), Bhikkhu Sujato (31), Nyanaponika Thera (28).

Rule: **search the distinguishing element, not the title.** Use
`authors:Analayo`, not `authors:"Bhikkhu Analayo"`. Use `authors:Bodhi`, not
`authors:"Bhikkhu Bodhi"`. (Case and diacritics still don't matter.)

Corporate / canonical "authors" exist and are useful seed entries when the
human author is unknown: `Samyutta Nikaya` (55 books listed under this
"author"), `Pali Text Society` (114), `Vipassana Research Institute` (249),
`84000` (36 — the Tibetan translation project), `Wikipedia` (69).

**6. The `series:` field is unused but valuable.** 607 distinct series.
When a topic implies a known imprint, scope with it. Useful series:

- `A Very Short Introduction` (339) — Oxford pocket intros
- `Vipassana Research Institute` (224)
- `Wheel Publication` (134) — BPS short pamphlets
- `Pali Text Society Editions` (110)
- `Buddhist Studies Review` (68)
- `BDK English Tripiṭaka Series` (60)
- `Journal of the Pali Text Society` (49)
- `Bodhi Leaves` (48)
- `Kangyur` (36)
- `Insight Journal` (34)

The current helper does not expose `--series` as a flag, but the free-text
helper invocation can include a series clause via `comments:` or by passing
the series name as the query and post-filtering.

**7. Search ladder — descend when hits are thin.** Don't give up after one
search returning zero. Walk down these rungs in order:

1. **Tag-scoped phrase.** `search-calibre "jhana" --tags Meditation` — narrow and high-precision.
2. **Free-text phrase, no tags.** `search-calibre "jhana absorption"` — Calibre searches title/author/comments simultaneously.
3. **Drop the tag restriction** if step 1 returned 0. The book may be tagged with a sibling concept (e.g. `Mindfulness` instead of `Meditation`).
4. **Widen via synonym tag cluster** from the table above. Pass several related tags. E.g. for *Nibbāna* topics, pass `--tags Nibbana Parinibbana` together.
5. **Known-author search.** If you know an authority on the topic (e.g. Bhikkhu Anālayo on early Buddhism, Bhikkhu Bodhi on the Nikāyas, Piya Tan on sutta translations), do an `authors:` scoped search.

If all five rungs return nothing, the topic is genuinely absent from the
library — note it as a gap in *Open Threads*, do not invent a citation.

→ **Scratch** — append Phase 3 results: Calibre hits (book_id, title, author), any FTS snippets, gaps noted.

### Phase 3b — Sanskrit source search

**Skip this phase** unless angle 7 was marked applicable in Phase 1, or unless `VICAYA_GRETIL_PATH` is configured (check with `echo $VICAYA_GRETIL_PATH`).

Search the local GRETIL corpus for IAST terms or transliterated Sanskrit relevant to the question:

```bash
uv run tools/research_sources.py search-sanskrit "<iast-term>" --limit 20
uv run tools/research_sources.py search-sanskrit "<iast-term>" \
  --folder "gretil.sub.uni-goettingen.de/gretil/1_sanskr/1_veda" --limit 20
```

**Note:** Searching English translation themes (e.g. "non-self", "breathe") is often more productive than searching IAST terms directly (e.g. `anātman`), because there is no equivalent to SuttaCentral for Sanskrit — transliterations are not standardised across files.

**Deriving the text name:** use `Path(hit["path"]).stem` — e.g. `rigveda_shas_u.txt` → `rigveda_shas_u`.

**Citation format:** `<TextName> [GRETIL], line <N>` — e.g. *rigveda_shas_u [GRETIL], line 1423*.
Include the verbatim IAST snippet as a blockquote. Evidence tier: **T3** (critical edition / primary text via GRETIL, treated as scholarly resource).

**Sanskrit subfolder map** (relative to `VICAYA_GRETIL_PATH`):
```
gretil.sub.uni-goettingen.de/gretil/
  1_sanskr/
    1_veda/   — Vedic Saṃhitās, Brāhmaṇas, Āraṇyakas, Upaniṣads, Vedāṅgas
    2_epic/   — Mahābhārata, Rāmāyaṇa
    3_purana/ — Purāṇas
    4_rellit/ — Religious literature (Dharmaśāstra, Āgamas, etc.)
    5_poetry/ — Classical poetry (Kālidāsa, etc.)
    6_sastra/ — Śāstra literature (grammar, philosophy, science)
  2_pali/     — Pāli texts (if you want to cross-check against canon DB)
  corpustei/  — TEI/XML versions of all texts (avoid for grep — use htm)
```

Returns `[]` silently if the corpus is not installed — skip without error.

→ **Scratch** — append Phase 3b results: queries tried, hit count, text names found, any IAST passages worth quoting.

### Phase 4a — Web search

Use `WebSearch` (and `WebFetch` to read the most promising results). Use as many relevant sources as you can find, up to 20. Prefer:
- SuttaCentral (suttacentral.net) — primary translations + parallels
- Access to Insight (accesstoinsight.org) — older but solid
- Academic journals and respected scholars
- Avoid: blog spam, AI-generated content farms, low-quality summaries

**SuttaCentral blocks WebFetch.** The site requires JavaScript rendering — `WebFetch` returns only an empty JS shell, never sutta content. Use these alternatives instead:
- Thanissaro translations: `dhammatalks.org/suttas/` (e.g. `dhammatalks.org/suttas/mn/mn60.html`)
- Older Thanissaro + other translators: `accesstoinsight.org/tipitaka/`
- When no web mirror is available, quote directly from the canon DB using `search-canon` + `resolve-citation`.

→ **Scratch** — append Phase 4a results: URLs fetched, key quotes retrieved, any blocked/failed fetches.

### Phase 4b — YouTube search

YouTube hosts an enormous corpus of recorded Dhamma talks, sutta studies, and academic lectures. Mine it.

```bash
uv run tools/research_sources.py search-youtube "apannaka sutta MN 60" --limit 20
```

Each hit comes back with `tier ∈ {trusted, probationary}` (excluded channels are dropped server-side). Prefer trusted hits; treat probationary hits with appropriate skepticism. The allowlist lives at `data/youtube_channels.md` — promote/demote at the end of the run via the reflection template.

For the most promising videos (up to 20), pull the transcript (skip if video titles are sufficient to confirm content is tangential or low-value for the question):

```bash
uv run tools/research_sources.py fetch-transcript R0vhivplJuM
```

Transcripts are cached under `data/youtube_cache/<video_id>.json` — subsequent calls are instant. Each transcript records `is_auto` (true = YouTube's auto-generated captions; false = human-uploaded). **Auto-captions mishear Pāḷi** ("Suddhāso" → "saso", "Apaṇṇaka" → "apaka"). When `is_auto` is true, paraphrase and link to the timestamp — do not quote Pāḷi verbatim.

To locate the relevant moment in a long talk, scan `segments` for keywords (English glosses or the auto-caption form of the Pāḷi term) and cite the `start` timestamp.

→ **Scratch** — append Phase 4b results: video IDs fetched, transcript summaries (is_auto flag, key timestamps), any tier-rejected channels.

### Phase 4c — WisdomLib

**This phase is mandatory on every run — it cannot be skipped.** WisdomLib is a comprehensive encyclopaedia of Indian religion, philosophy, and culture, covering Buddhist (Theravāda, Mahāyāna, Tibetan), Hindu (Nyāya, Vaiśeṣika, Yoga, Vedānta, Ayurveda, and others), and Jain traditions. It is the most reliable single-site source for precise definitions of technical Sanskrit and Pāḷi terms.

**For every principal technical term in the research question** — up to ~8 terms per run — fetch:

```
https://www.wisdomlib.org/definition/<term-ascii>
```

**Term formation rule — ASCII only in the URL path.** Strip all diacritics before constructing the URL. Examples:

| Term as written | URL path segment |
|---|---|
| dukkha / duḥkha | `dukkha` / `duhkha` |
| paṭiccasamuppāda | `paticcasamuppada` |
| nibbāna / nirvāṇa | `nibbana` / `nirvana` |
| saṃsāra / saṃskāra | `samsara` / `samskara` |
| anicca / anityatā | `anicca` / `anityata` |

When a term has both a Pāḷi form and a Sanskrit IAST form, fetch **both** — the two pages cover different tradition clusters (Pāḷi page emphasises Theravāda; Sanskrit page covers Hindu schools and Mahāyāna).

**Filtering results by tradition.** The page lists definitions from many traditions. Focus on entries relevant to the question's tradition: for Pāḷi/Theravāda questions, prioritise Theravāda, Pāḷi dictionary, and Abhidhamma entries. For pan-Indian or comparative questions, read entries from multiple traditions and note where they converge or diverge.

**Evidence tier.**
- Default: **T2** (encyclopaedic secondary — treats the site as a scholarly reference work).
- Upgrade to **T1** only when the WisdomLib entry quotes a primary canon text verbatim and identifies it by name; in that case also cite the primary text directly.

**Citation form:**
```
[wisdomlib.org — <Term>](https://www.wisdomlib.org/definition/<term-ascii>) — retrieved YYYY-MM-DD
```

→ **Scratch** — append Phase 4c results: terms fetched, URLs, key definitions with tradition + source labels, any 404s or empty pages.

### Phase 5 — Synthesis

**Read the scratch file before drafting.** Run `cat "$SCRATCH"` to recover the full list of findings from all prior phases. This is the compaction rescue step — if your context was compressed, everything you found is still in that file.

Draft the answer in your working notes. Cite as you go — never make a claim without a reference.

**Before drafting, read the "Pāḷi/English presentation" rules in the Style notes section.** Those rules govern how every Pāḷi quote and every inline Pāḷi term is rendered in the final vault note. Apply them from the first draft so you don't have to retrofit on the final pass.

**Source completeness check before you write.** Review your perspective map from Phase 1. For every named position, ask: do I have the canon passages that establish it, a secondary source that analyses it, and a web or talk source where the user could learn more? If any position is thin on sources, loop back to Phases 2–4 before synthesising. More prose does not fix missing sources — only more searching does.

**Angle coverage check.** Review the angle triage from Phase 1. For every angle marked *applicable*, ask: have I cited at least one source from that angle? If an applicable angle has zero citations, either loop back and search it, or downgrade it to *not applicable* with an honest reason for the `## Angles Not Pursued` table. Silent omission of a triaged angle is not acceptable.

**⚠️ IRON RULE — Devil's Advocate pass before drafting.** After the source and angle checks, answer each question below in the scratchpad before writing a single sentence of the Findings section. Brief answers are fine; the point is to surface problems while there is still time to fix them, not to generate prose.

1. **Citation balance.** For each position in the perspective map — do I have sources that *support* it AND sources that *challenge or complicate* it? If one position is supported by 6 canon hits and another by 1, is that imbalance accurate scholarship or search bias?
2. **Suppressed evidence.** Are there canon hits or library sources in the scratchpad that I was not planning to cite? For each: why not? If the honest answer is "it complicates my framing," the source goes in, not out.
3. **Alternative readings.** For the most important sutta passage I plan to quote — what does the commentarial tradition say about it, and what does at least one modern scholar who disagrees with that reading say? Am I collapsing a live interpretive dispute into a single reading?
4. **Strongest opposing voice.** What would the most credible scholar who holds the *opposing* view say is wrong with my synthesis? If I cannot name that argument, I have not understood the debate well enough to write about it.
5. **Evidence tier of load-bearing claims.** Is the central claim of the Findings section supported by T1 (canon mūla) or T2 (commentary) evidence, or does it ultimately rest on a modern teacher's talk or a secondary source? If the latter, the Findings prose must reflect that epistemic status.

Append answers to the scratchpad under `## Devil's Advocate`. Then draft.

**Use all relevant evidence.** If you collected 15 canon hits and 6 library sources, all of them go in the note — not a representative sample. Drop a hit only if it is a verbatim duplicate of one already quoted. Paraphrase only when the full text is unavailable. Prefer blockquotes (Rule P1) over inline summaries everywhere.

**Track every rejection.** Each time you decide not to use a source — whether a canon paragraph, a Calibre book, a web page, or a YouTube video — note it immediately with a one-line reason. These go into `## Sources Investigated, Not Used` in the final note. Common reasons: duplicate, metadata-only (no content to quote), URL blocked, auto-captions too degraded to paraphrase, out of scope, wrong sutta. Do not discard sources silently.

**Recursive citation check.** As you draft, watch for sources that are load-bearing — a teacher, text, or sutta that the argument depends on but that hasn't been searched yet. If you find one, pause and loop back to Phase 2 or 3 for that specific entity before continuing. Up to two loop-backs per run; don't spiral beyond that. If after the loop-back the source still can't be found, note the gap honestly in Open Threads.

Citation forms:

- Canon: `**MN60 Apaṇṇakasuttaṃ para 97** — "<pali quote>" / "<english>"`
- Library: `[[<Book Title>]] — <Author>: "<snippet>"` (omit snippet if metadata-only)
- Web: `[<page title>](<url>) — retrieved YYYY-MM-DD`
- Vault: `[[<Existing Note Title>]]`

**Inline footnote markers.** As you write the Findings prose, place a named footnote superscript immediately after any claim that rests on a specific source. Use these ID conventions:

| Source type | ID form | Example |
|---|---|---|
| Canon | `[^<booktable>-<para>]` | `[^s0201m-70]` |
| Library | `[^calibre-<book_id>]` | `[^calibre-223]` |
| Web / YouTube | `[^web-<n>]` | `[^web-1]`, `[^web-2]` |

The footnote definitions go at the bottom of the note (see Phase 7 template). Keep definitions short — they are locators, not evidence repeats. The full Pāḷi/English blockquotes belong in the Evidence sections.

**Bibliography accumulation.** As you finalize each source for inclusion, append its
full Chicago N-B entry to the scratchpad under `## Bibliography (accumulating)`. Do this
*as you go*, not in one pass at Phase 7 — by the time you reach Phase 7 the bibliography
should be complete. Organize entries into the five subsections as you write them; sort
Secondary Sources alphabetically by author surname. See the `## Bibliography` section
above for format rules.

### Phase 6 — Second-pass review (cross-check)

Pipe your synthesis to a second model for an independent review:

Write the prompt to a temp file, then pipe it in (avoids all shell quoting hazards):

```bash
cat > /tmp/cross_check_prompt.txt <<'EOF'
You are reviewing a research synthesis on a Pāḷi/Buddhist question.
For each of the five areas below, respond specifically or say "no issue":

1. **Perspective coverage** — Are there named positions in the synthesis that are underrepresented or mischaracterised? Are there significant schools, teachers, or scholarly voices missing from this topic entirely?
2. **Tier integrity** — Is any claim attributed to the root canon (mūla) that actually originates in the commentarial tradition (aṭṭhakathā / ṭīkā)? Is any teacher's interpretation presented as if it were canonical?
3. **Disputed consensus** — Is any live interpretive dispute presented as settled? Are there scholars or lineages who hold a substantially different position that the synthesis does not mention?
4. **Factual accuracy** — Are there errors in Pāḷi terminology, sutta references, historical claims, or scholarly attributions?
5. **General** — Any other factual errors, oversights, or alternative interpretations not captured above.

Question: <the question>

Synthesis:
<the synthesis>
EOF

uv run tools/research_sources.py cross-check < /tmp/cross_check_prompt.txt > /tmp/cross_check_review.txt
```

The `cross-check` helper POSTs to OpenRouter (model list in `data/openrouter_models.json` — edit freely, read at runtime). OpenRouter routes server-side via `models: [...]`: the first reachable model wins, subsequent entries cover outages / rate-limits. On any failure (no key, all models down, network error) the helper returns the `# SELF_REVIEW:` sentinel. **If `/tmp/cross_check_review.txt` begins with `# SELF_REVIEW:`**, no external provider was reachable. In that case, run the embedded five-point checklist on your own synthesis: read each numbered item, audit your synthesis against it, and apply fixes the same way you would for an external review. Do not write anything in the note acknowledging the self-review fallback; it is still subject to the IRON RULE below. The terminal report in Phase 7 records `cross-check: self-review` instead of a model name.

**Silently integrate** anything substantive. If the review surfaces:
- A missed school / lineage / teacher → research the primary or secondary sources for it and incorporate with proper citations (canon, library, web). If you can't substantiate it, drop it.
- A factual correction → verify against a primary or secondary source you can cite, then incorporate.
- An alternative interpretation → add it as a position in the note, cited to whoever actually holds it.

**⚠️ IRON RULE — Never write that the review surfaced something.** No "Gemini noted", no attribution to any AI model, no meta-commentary about how the note was produced. If you incorporate a school the user might not have asked about, that's fine — it stands on its own academic merit, cited properly.

If the review surfaces nothing substantive, move on without any acknowledgement in the note.

### Phase 7 — Write the note

**The vault only receives complete notes.** The scratch dossier in `data/scratch/`
holds the in-progress work. Phase 7 is the *finalization and transfer* step: take
the comprehensive dossier, curate the strongest evidence into the structured note
template below, and write the result to `$VICAYA_VAULT_PATH/Vicaya/` only when it
is complete. Never write a partial or draft note to the vault.

**Before writing, run this source-coverage check:**
- Is every position from the perspective map represented by at least one block-quoted canon passage?
- Is every *applicable* angle from the Phase 1 triage represented by at least one citation, and is every *non-applicable* angle logged in `## Angles Not Pursued` with a one-line reason?
- Are all pertinent canon hits in the Canon Evidence (T1) section — not a curated sample?
- Have I searched Calibre for every plausible tag cluster, not just the first match?
- Have I pulled transcripts for the most relevant Dhamma talks, not just noted the video titles?
- Have I fetched and read the most promising web sources, not just linked to search results?
- Is the draft approaching ~12 pages (~3,500 words)? If not, the answer is almost always: I have not surfaced enough sources.

Render the final markdown. Use this template as a structural guide — expand every section to the depth the evidence warrants:

```markdown
---
date: YYYY-MM-DD
topic: <one-line topic>
tool: "https://github.com/bdhrs/vicaya"
agent: "<Model family + version, e.g. Claude Opus 4.7 (claude-opus-4-7)>"
tags:
  - research
  - pali
canon_refs:
  - <human_ref>
  - ...
library_refs:
  - "<book_id>: <title> — <author>"
web_refs:
  - <url>
---

# <Topic title>

## Question
<the user's question, verbatim>

## Findings
<the synthesised answer, with inline citations>

## Canon Evidence (T1)
- **MN60 Apaṇṇakasuttaṃ para 97**
  - Pāḷi: "..."
  - English: "..."
- ...

## Commentary Evidence (T2)
- **<aṭṭhakathā or ṭīkā ref>** — Buddhaghosa / Dhammapāla
  - Pāḷi: "..."
  - English: "..."
- ...

## Scholarly Sources (T3)
- [[Book Title]] — Author Name
  - "snippet" (if FTS was on)

## Web Evidence (T3)
- [Source title](url) — retrieved YYYY-MM-DD
  - <brief gloss of what this source contributes>

## Teacher Talks and Accessible Sources (T4)
- [Channel — Talk Title](https://youtu.be/<video_id>?t=<seconds>) — fetched YYYY-MM-DD (human captions | auto-captions; paraphrase)
  - <paraphrase or — only if `is_auto = false` — direct quote>

## Related Notes
- [[Existing vault note 1]]
- [[Existing vault note 2]]

## Sources Investigated, Not Used

Evidence funnel: <N> T1 canon hits → <N> T2 commentary hits → <N> T3 library/web → <N> T4 talks | Cited: <N> T1, <N> T2, <N> T3, <N> T4

| Source | Type | Reason not used |
|--------|------|-----------------|
| MN60 para 12 | T1 Canon | Duplicate of para 97 — same argument, verbatim repetition |
| Papañcasūdanī para 45 | T2 Commentary | Redundant — same gloss covered by para 44 already cited |
| [[Some Book Title]] — Author | T3 Scholarly | Metadata hit only; no FTS snippet; title too generic to cite without content |
| https://example.com/article | T3 Web | Blocked / JS-only; content not retrievable |
| Channel — Talk Title (video_id) | T4 Talks | Auto-captions only; Pāḷi terms mangled beyond reliable paraphrase |

## Angles Not Pursued
| Angle | Reason not pursued |
|-------|--------------------|
| Archaeology | Question is purely doctrinal; no material-culture bearing |
| Other religions | No structural analogue worth comparing on this question |
| EBT āgama parallels | Sutta is uniquely Pāḷi; no Chinese / Sanskrit / Tibetan parallel attested |

## Critical Gaps

Severity legend: `blocker` = central claim is unreliable without this; `gap` = applicable angle with no sources; `nit` = would strengthen but doesn't undermine the argument.

| Severity | Claim or perspective | What would close it |
|----------|----------------------|---------------------|
| `blocker` | <claim that rests on thin or secondary evidence only> | <specific search or source> |
| `gap` | <named perspective from the perspective map with insufficient sources> | <where to look> |
| `nit` | <minor omission or follow-up worth noting> | <suggested search> |

## Bibliography

Copy the accumulated bibliography from the scratchpad's `## Bibliography (accumulating)`
block. Omit any subsection that has no entries. Sort Secondary Sources by author surname.

### Primary Sources

*Majjhima Nikāya* 60 (*Apaṇṇakasuttaṃ*). Chaṭṭha Saṅgāyana Tipiṭaka.
  Accessed via tipitaka-translation-data.db (`s0201m_mul`).

*Madhyamāgama* 98 (*Zhongahanijing* T 26). Translated by Charles Patton.
  Accessed via EBC vault, `ma-patton/ma98-patton.md`.

### Secondary Sources

Harvey, Peter. *The Selfless Mind: Personality, Consciousness and Nirvāṇa in Early
  Buddhism*. Richmond: Curzon Press, 1995. (Calibre #6294)

Karunadasa, Y. *Theravāda Abhidhamma: Its Inquiry into the Nature of Conditioned
  Reality*. Hong Kong: University of Hong Kong, 2010. (Calibre #7335)

### Online Sources

Sujato, Bhikkhu. "On the Nature of Nibbāna." *SuttaCentral*. Accessed YYYY-MM-DD.
  https://suttacentral.net/...

### Media Sources

Ajahn Brahm. "Understanding Nibbāna." *Buddhist Society of Western Australia* (YouTube).
  January 1, 2020. https://youtu.be/...
  [Human captions]

### Vault Sources Referenced

[[Related Note Title]] — Vicaya research note, YYYY-MM-DD.

---
*Researched by [Vicaya](https://github.com/bdhrs/vicaya) using <Model family + version> on YYYY-MM-DD HH:MM.*

[^s0201m-70]: MN9 Sammādiṭṭhisuttaṃ para 70 — db: s0201m_mul, para 70
[^calibre-223]: [[On Meditation]] — Ajahn Chah (Calibre #223)
[^web-1]: [Ānāpānasati Sutta](https://www.dhammatalks.org/suttas/mn/mn118.html) — retrieved YYYY-MM-DD
```

### Frontmatter rules (agents get these wrong — read carefully)

**Rule F1 — Quote any value that contains `: ` (colon-space).**

The `topic` field almost always contains a colon. If it is not quoted, Obsidian's YAML
parser will silently corrupt it. Wrap the whole value in double quotes:

```yaml
# WRONG — YAML parser breaks on the second colon
topic: Meditation Subjects in Early Buddhist Texts: Frequency and Description

# CORRECT
topic: "Meditation Subjects in Early Buddhist Texts: Frequency and Description"
```

**⚠️ IRON RULE — Rule F2 — `canon_refs` entries must come verbatim from `resolve-citation` output. Never guess or infer a sutta number from a sutta name, or a name from a number.**

The `human` field returned by `resolve-citation` is the *only* authoritative string.
Copy it exactly. Common hallucination patterns to avoid:

```yaml
# WRONG — agent guessed that MN22 = Mahāsatipaṭṭhāna (it is not; DN22 is)
- MN22 Mahāsatipaṭṭhānasuttaṃ para 10

# WRONG — agent confabulated a range "AN9.93-432" which is not a real reference
- AN9.93-432 para 977 (Ānāpānasati Sutta)

# WRONG — parenthetical gloss is fabricated and wrong (DN11 is Kevaddhā, not Six Recollections)
- DN11 Kevattasuttaṃ (Six Recollections)

# CORRECT — taken verbatim from resolve-citation output
- MN118 Ānāpānasatisuttaṃ para 977
- DN22 Mahāsatipaṭṭhānasuttaṃ para 374
```

**Rule F3 — `web_refs` entries must be bare URLs only — no annotations.**

Obsidian's property renderer parses these as URLs. Any trailing text (` — retrieved …`,
sutta names, descriptions) breaks the URL type and shows the property as red/broken.
Put retrieval dates and annotations in the Web Evidence section body, not here.

```yaml
# WRONG — trailing annotation breaks Obsidian's URL property type
- https://accesstoinsight.org/tipitaka/dn/dn.22.0.than.html — retrieved 2026-05-12

# CORRECT — bare URL only
- https://accesstoinsight.org/tipitaka/dn/dn.22.0.than.html
```

**Rule F4 — `library_refs` entries must be quoted strings, not bare mappings.**

Obsidian's property renderer cannot display nested YAML objects. A bare `- 223: Title`
is a YAML mapping (key `223`, value `Title`) — Obsidian shows it as a red broken
property. Wrap the whole entry in double quotes so it is a plain string:

```yaml
# WRONG — YAML mapping, renders red/broken in Obsidian
library_refs:
  - 223: On Meditation — Ajahn Chah

# CORRECT — quoted string, renders cleanly
library_refs:
  - "223: On Meditation — Ajahn Chah"
```

The `book_id` must come from `CalibreHit.book_id` — never invent an ID.

**Rule F5 — `agent` field and footer line: self-identify accurately.**

The note records which model produced it, in two places:

1. The `agent` frontmatter field — quoted string, format `"<Family Version> (<exact model id>)"`.
2. A single italic footer line at the very end of the note: `*Researched by [Vicaya](https://github.com/bdhrs/vicaya) using <Family Version> on YYYY-MM-DD HH:MM.*`

Read your own model identity from your runtime context — do **not** guess from training
data, and do **not** invent a version number. If you genuinely cannot determine your
identity, write `unknown agent` in both places rather than fabricating.

Examples by agent:

- Claude Code: `"Claude Opus 4.7 (claude-opus-4-7)"`, `"Claude Sonnet 4.6 (claude-sonnet-4-6)"` — the exact ID is exposed in your environment context.
- Gemini CLI: `"Gemini 2.5 Pro"` or whatever the CLI reports.
- Codex / GPT-based: `"GPT-5.4 (codex)"` or equivalent.
- Other: `"<Model name as the runtime reports it>"`.

This is metadata, not attribution-in-scholarship — Hard Rule 1 still forbids weaving
model identity into the findings, evidence, or analysis.

**Rule F6 — `tool` field: always set to the Vicaya repo URL.**

Every note must include `tool: "https://github.com/bdhrs/vicaya"` in the frontmatter.
This field is fixed — never vary the URL, never omit it.

### Correct frontmatter example (reference this when writing)

```yaml
---
date: 2026-05-12
topic: "Ānāpānasati: Breath Meditation in the Nikāyas"
tool: "https://github.com/bdhrs/vicaya"
agent: "Claude Opus 4.7 (claude-opus-4-7)"
tags:
  - research
  - pali
  - meditation
canon_refs:
  - MN118 Ānāpānasatisuttaṃ para 977
  - SN54.1 Ekadhammosuttaṃ para 1
library_refs:
  - "223: On Meditation - Instructions from Talks by Ajaan Chah — Ajahn Chah"
  - "1683: Buddhist Meditation and Depth Psychology — Douglas M. Burns"
web_refs:
  - https://accesstoinsight.org/tipitaka/mn/mn.118.than.html
---
```

Write the note via the Obsidian CLI. Slugify the topic for the filename:

```bash
TODAY=$(date +%Y-%m-%d)
SLUG="<lowercase-hyphenated-slug>"
obsidian vault=Obsidian create \
  path="Vicaya/${TODAY} - ${SLUG}.md" \
  content="<full rendered markdown>" \
  open
```

(Use `open` so it opens in Obsidian for the user when they come back.)

### PDF generation (run after every successful vault write)

After writing the note — whether via the Obsidian CLI or the disk fallback — generate
a PDF copy. Read `VICAYA_PDF_PATH` from `.env`. If unset or empty, skip silently.

Write the following to `temp/gen_pdf_run.py`, then execute it with `uv run temp/gen_pdf_run.py`:

```python
# Generate PDF for the current vicaya note
import re, os, sys, platform, subprocess
from pathlib import Path

# macOS: weasyprint needs Homebrew GLib/Pango; re-exec with library path set
if platform.system() == "Darwin" and "/opt/homebrew/lib" not in os.environ.get("DYLD_LIBRARY_PATH", ""):
    env = dict(os.environ)
    env["DYLD_LIBRARY_PATH"] = "/opt/homebrew/lib:" + env.get("DYLD_LIBRARY_PATH", "")
    sys.exit(subprocess.run([sys.executable] + sys.argv, env=env).returncode)

env = {}
if Path(".env").exists():
    for line in Path(".env").read_text().splitlines():
        if "=" in line and not line.startswith("#"):
            k, _, v = line.partition("=")
            env[k.strip()] = v.strip()

pdf_dir = os.environ.get("VICAYA_PDF_PATH") or env.get("VICAYA_PDF_PATH", "")
vault_path = os.environ.get("VICAYA_VAULT_PATH") or env.get("VICAYA_VAULT_PATH", "")
if not pdf_dir or not vault_path:
    sys.exit(0)

import markdown
from weasyprint import HTML, CSS
from weasyprint.text.fonts import FontConfiguration

today = "<TODAY>"
slug = "<SLUG>"
note_file = Path(vault_path).expanduser() / "Vicaya" / f"{today} - {slug}.md"
pdf_out = Path(pdf_dir).expanduser() / f"{today} - {slug}.pdf"
pdf_out.parent.mkdir(parents=True, exist_ok=True)

text = note_file.read_text()
body = re.sub(r'^---\n.*?\n---\n', '', text, count=1, flags=re.DOTALL)
html = markdown.markdown(body, extensions=['tables', 'fenced_code'])
full_html = f"<html><body>{html}</body></html>"

font_config = FontConfiguration()
css = CSS(string="@page { margin: 20mm; } body { font-family: Georgia, serif; font-size: 11pt; line-height: 1.6; }", font_config=font_config)
HTML(string=full_html).write_pdf(str(pdf_out), stylesheets=[css], font_config=font_config)
print(f"PDF → {pdf_out}")
```

Replace `<TODAY>` and `<SLUG>` with the actual values used when writing the note.
Include the PDF path in the Section 1 run summary if generation succeeded.

### GitHub push (run after successful PDF generation)

After PDF generation, push the new note to `bdhrs/vicaya-notes` so collaborators
receive it automatically. Derive the repo path from the already-loaded `vault_path`:

```python
import subprocess
notes_repo = str(Path(vault_path).expanduser() / "Vicaya")
note_filename = f"{today} - {slug}.md"
try:
    subprocess.run(["git", "-C", notes_repo, "add", note_filename], check=True, capture_output=True)
    subprocess.run(["git", "-C", notes_repo, "commit", "-m", f"note: {today} - {slug}"], check=True, capture_output=True)
    subprocess.run(["git", "-C", notes_repo, "push", "origin", "HEAD"], check=True, capture_output=True)
    print(f"GitHub → pushed {note_filename}")
except Exception as e:
    print(f"GitHub push skipped: {e}")
```

Add the result (`GitHub → pushed …` or `GitHub push skipped: …`) to the Section 1
run summary. A push failure is never fatal — the note is already saved to the vault.

## Final report to the user

The terminal report has two distinct sections. Keep them separate — conflating them was a recurring bug in prior runs.

### Section 1 — Run summary

- Path of the saved note.
- Hit counts: canon refs, library books, web sources cited.
- One sentence: the headline finding.
- Optionally one line per *content* integration from the cross-check, framed as content not process. **Example (good):** `Added MN 101 Devadahasutta as a load-bearing reference — it refutes the strict-determinist reading.` **Example (bad — never write this):** `Gemini noted MN 101 was missing.`

### Section 2 — Skill improvements made

Only edits to `SKILL.md` or `tools/research_sources.py`. One line each, prefixed with `Improved:`. **If you made no skill edits, omit this section entirely** — don't pad it with content integrations (those go in Section 1).

### Section 3 — Distillation reminder (conditional)

Count the files in `runs/`. If there are 10 or more, print one line:

> **Skill distillation due** — `runs/` has <N> reflections. Read them back and promote any recurring lessons into SKILL.md Hard Rules or guidance sections.

If fewer than 10, omit this section entirely.

## When something fails

- **Helper raises `FileNotFoundError`**: a path is wrong — tell the user, don't fudge.
- **Canon search returns 0 hits**: try lang="any" and/or broader book scope before giving up.
- **Calibre returns 0 hits**: first distinguish empty from error — `calibre-check` exits 1 on a lock. If locked, note the gap and skip rather than retrying fruitlessly. If reachable and truly empty: try fewer/looser tags; check `data/calibre_tags.csv` for the right vocabulary; try `authors:` with a known authority. If early-session queries succeeded but mid-session queries return 0 with no lock, suspect parallel-agent contention — fall back to `pdftotext` or `ebook-convert` on already-known book IDs from earlier hits.
- **`cross-check` returns `# SELF_REVIEW:`**: OpenRouter is unreachable. Run the embedded checklist on your own synthesis as described in Phase 6; do not retry the helper. Common root causes: no `OPENROUTER_API_KEY` set (check `.env`), an empty / malformed `data/openrouter_models.json`, or every free model in the chain simultaneously rate-limited (rare). (Note: the legacy `gemini-cross-check` subcommand returns a `# ERROR:` line on failure instead — same response: skip the section and continue.)
- **Obsidian create fails**: print the rendered markdown to the terminal so the user can save it manually.
- **PDF URL — WebFetch returns garbled or empty content**: WebFetch cannot decode PDF binary. Instead, save the file to a temp path and extract with `pdftotext`:
  ```bash
  curl -sL "<url>" -o /tmp/source.pdf && pdftotext /tmp/source.pdf -
  ```
  `pdftotext` is at `/usr/bin/pdftotext` (Poppler 24.02) and handles Unicode including Pāḷi diacritics. If the PDF is password-protected or corrupt, `pdftotext` will exit non-zero — note the gap and move on. No other PDF extraction tool is reliably available on this system.

## When Obsidian isn't running

The Obsidian CLI requires the desktop app to be open. If `obsidian` commands fail with
"The CLI is unable to find Obsidian", fall back to writing the note directly to disk at
the vault path (`$VICAYA_VAULT_PATH/Vicaya/`). Obsidian will index it on
next launch. Tell the user in the final report that they need to open Obsidian to use
vault search next time.

## Style notes

- **The note's primary job is to surface sources.** The user wants a research map they can follow themselves — every relevant canon passage, every library book, every credible web source, every Dhamma talk. The Findings section orients them; the Evidence sections are the point. A note with thin evidence and expansive analysis has failed. A note with comprehensive evidence and concise analysis has succeeded.
- **"Don't pad" means:** don't add summary paragraphs the user can derive from reading the evidence themselves. It does **not** mean "keep it short." It means every line must earn its place — either as a direct quote, a citation, or a sentence that cannot be inferred from the sources alone.
- **Direct quotes over paraphrase.** When you have canon text, quote it in full with the blockquote format (Rule P1). Paraphrasing is a fallback for when you cannot retrieve the text — not the default. If you found 15 relevant canon hits, all 15 go in the Canon Evidence section.
- **Target depth: ~12 pages (~3,500 words), measured by source coverage.** This is the length at which the user has reported finding the notes most useful. Reach it by surfacing more sources, not by writing more prose per source. If a draft is short, the right fix is: did I search for all relevant canon passages? did I exhaust the Calibre library? did I pull transcripts from the most relevant Dhamma talks? — not: did I write enough sentences about each position?
- **Template is structure, not length.** The note template shows section headings and citation formats. It is not a short form to fill in one pass. The Evidence sections in particular should be as long as the sources warrant.
- Quote Pāḷi in IAST as it appears in the canon db (don't transliterate).
- Critical Gaps is for honest self-assessment, formatted as a severity table (`blocker` / `gap` / `nit`). Each row names one claim or missing perspective and the specific search that would close it. Not a catch-all for "more research could be done".
- The note is written for a reader — typically the user, weeks later — who wants information and sources. Not a workflow log.

### Pāḷi/English presentation (vault note only)

These rules apply to the final markdown note written into the vault. They
do **not** apply to the terminal report — terminal output stays plain.

**Rule P1 — Sentence/paragraph quotations: two blockquotes, one above the
other.** When you quote a Pāḷi sentence or paragraph and its English
translation, render each as its own markdown blockquote, separated by a
blank line. This makes the provenance unambiguous: the reader sees source
text first, then translation, both visually offset from the surrounding
prose.

```markdown
> Cattārome, bhikkhave, āhārā bhūtānaṃ vā sattānaṃ ṭhitiyā…

> Bhikkhus, there are these four foods for the sustenance of beings
> already born…
```

**Rule P2 — Inline Pāḷi inside English prose: italics + bracketed gloss on
first use.** Every Pāḷi word that appears in an English sentence is
italicised. On its **first appearance per section**, follow it with the
English gloss in round brackets; subsequent uses in the same section are
italics only.

```markdown
The four *āhāra* (nutriments) sustain beings already born and assist those
seeking rebirth. Three of the four *āhāra* are mental.
```

**Additional conventions:**

- **Sutta names in italic Pāḷi, citation tag in roman.** Write
  `*Apaṇṇakasutta*` for the title; write `MN60` for the reference tag. So
  a full inline citation is: *Apaṇṇakasutta* (MN60).
- **IAST fidelity.** Keep diacritics exactly as the canon SQLite returns
  them. Do not normalise `ṃ` to `ṁ` or vice versa; do not strip macrons.
- **Stem form vs. inflected form.** In prose, use the stem
  (`dukkha`, `paṭiccasamuppāda`, `khandha`). Use inflected forms
  (`dukkhaṃ`, `khandhā`) only inside a verbatim quote where the case ending
  is what the canon says.
- **English-loaned terms stay roman after first introduction.** Words that
  have entered English Buddhist usage — Dhamma, Buddha, Nibbāna, sutta,
  Sangha, Bhikkhu, Vinaya, Tipitaka — appear in roman type and need no
  bracketed gloss. Diacritics are kept (so: Nibbāna, not Nibbana).
  Distinguish capitalised proper-noun uses (the Dhamma = the teaching)
  from common-noun *dhamma* (mental object, phenomenon), which stays
  italicised because it carries a technical sense.
- **Verse.** Preserve line breaks inside the blockquote — one Pāḷi pāda per
  line, blank line, then the English with the same line break structure.

**Worked example — single canon hit, rendered both ways:**

Inline form (used in flowing analysis):

```markdown
The Buddha frames the four *āhāra* (nutriments) — *kabaḷīkārāhāra*
(physical food), *phassāhāra* (contact), *manosañcetanāhāra* (mental
volition), and *viññāṇāhāra* (consciousness) — as conditions for the
continuity of beings.
```

Blockquote form (used when the canon text itself is the evidence):

```markdown
**MN9 Sammādiṭṭhisuttaṃ para 70:**

> Cattārome, āvuso, āhārā bhūtānaṃ vā sattānaṃ ṭhitiyā sambhavesīnaṃ vā
> anuggahāya. Katame cattāro? Kabaḷīkāro āhāro oḷāriko vā sukhumo vā,
> phasso dutiyo, manosañcetanā tatiyā, viññāṇaṃ catutthaṃ.

> Friend, there are these four foods for the sustenance of beings already
> born and for the support of those seeking rebirth. What four? Physical
> food, gross or subtle; second, contact; third, mental volition; fourth,
> consciousness.
```

### Footnote definitions (vault note only)

Footnote definitions appear at the very bottom of the note, after the final `---`
and the italic footer line. They are **locators** — short enough to let the reader
jump straight to the source. They are **not** evidence repeats; do not copy the
full Pāḷi/English blockquote from the Evidence section into the footnote.

Format rules:

- **Canon:** `[^<booktable>-<para>]: <human_ref> — db: <table>, para <paranum>`
  Example: `[^s0201m-70]: MN9 Sammādiṭṭhisuttaṃ para 70 — db: s0201m_mul, para 70`
- **Library:** `[^calibre-<id>]: [[<Title>]] — <Author> (Calibre #<id>)`
  Example: `[^calibre-223]: [[On Meditation]] — Ajahn Chah (Calibre #223)`
- **Web:** `[^web-<n>]: [<page title>](<url>) — retrieved YYYY-MM-DD`
  Example: `[^web-1]: [Ānāpānasati Sutta](https://www.dhammatalks.org/suttas/mn/mn118.html) — retrieved 2026-05-14`
- **YouTube:** `[^web-<n>]: [<Channel> — <Title>](https://youtu.be/<id>?t=<sec>) — retrieved YYYY-MM-DD`

Only define footnotes that were actually cited inline in the Findings prose. Do not
list every Evidence section entry as a footnote — only the claims in Findings prose
that carry a superscript marker.

## Self-improvement loop (mandatory)

This skill must improve over time based on what goes wrong during real runs. The loop has
a **forcing function**: writing a reflection file. The run isn't done until that file
exists. Empty reflections are allowed; missing ones are not.

### Step 1 — Write a run reflection (always)

Before printing the final report, write a reflection to:

```
<repo-root>/runs/<UTC-timestamp>.md
```

Use the filename format `YYYYMMDD-HHMMSS.md` (UTC). Template:

```markdown
---
date: <YYYY-MM-DD>
question: <verbatim user question, one line>
note_path: <path of the saved research note>
duration_min: <approximate>
---

## What surprised me
- <one bullet per surprise, or "nothing notable">

## What I'd change in the skill
- <one bullet per concrete SKILL.md or helper change worth making, or "nothing">

## What I changed this run
- <one bullet per edit actually made to SKILL.md / research_sources.py, or "nothing">

## Channel tuning
- Promote to trusted: <Channel — one-line reason this run, or "none">
- Demote to excluded: <Channel — one-line reason this run, or "none">
- New probationary channels seen: <comma-separated list, or "none">
```

Be terse. Three bullets per section max. If a section is empty, write "nothing" — don't
delete the heading. These files are the input to periodic skill-tuning passes.

After writing the reflection, apply any concrete `Channel tuning` decisions directly to
`data/youtube_channels.md`. Promotions and demotions are how the channel allowlist gets
richer over time; without this step the file goes stale.

### Step 2 — If a change is small and obvious, make it now

If reflection turned up a one-line fix (a wrong path, a missing field name, a confusing
phrase), edit `SKILL.md` or `research_sources.py` directly in this run. The file is
symlinked from `~/.claude/skills/vicaya/` to `<repo>/skill/vicaya/`, so edits
propagate instantly. Larger refactors should go in the reflection as a proposal and be
batched later — don't derail a research run with a refactor.

### Step 3 — Report skill edits in Section 2 of the final report

See "Final report to the user" above. **Content integrations** (e.g. "added MN 101")
belong in Section 1, not here. **Skill edits** (e.g. "documented `CanonHit` fields") go
in Section 2 as `Improved:` lines.

### Reflection triggers

These are the kinds of things worth noting in the reflection:

- A helper returned 0 hits when there should have been hits (query / tag tuning).
- A helper crashed because you guessed a field name — the dataclass docs at the top of
  this file should have prevented it; if they didn't, fix them.
- A `python -c` heredoc bit you. The CLI exists to prevent this; either use it, or note
  that a needed subcommand is missing.
- The note template missed something useful, or had unused sections.
- A citation format was unclear or hard to round-trip back to source.
- You got confused about scope inference, tag selection, or anything procedural.
- Something worked surprisingly well and should be promoted to default.

### Portability

Rules belong in this file, not in agent memory. This skill is meant to be runnable by
any agent (Claude, Codex, Gemini, …). Agent-specific memory systems are non-portable.
If you discover a rule worth keeping, write it into the Hard Rules section at the top of
this file or into the relevant phase.
