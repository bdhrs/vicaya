---
name: vicaya
description: Run a structured Pāḷi/Buddhist research session across the user's local sources (Obsidian vault, CST canon SQLite, library folders) plus web search, cross-checked with Gemini, and write a single linked note into the Obsidian vault. Invoke when the user types /vicaya <question> or asks for "research on X", "look into X across my sources", "find what the suttas say about X", or any multi-source research request that should land as a permanent vault note.
---

# Research skill

Run a multi-phase research session across the user's local + web sources and write a single structured note into their Obsidian vault.

This skill runs as a single orchestrating session. After Phase 1, each gather
phase (2, 2.5, 3, 3b, 4a, 4b, 4c) is delegated to its own single-phase
sub-agent that writes findings to the shared scratch file; the orchestrating
session handles Phase 0, Phase 1, Phase 5, Phase 6, and Phase 7 and spot-checks
each phase between agents. This file is the canonical one-goal `/vicaya`
workflow and the only behavioral source of truth.

## Critical execution rules

Four structural commands carry the run. Everything else is reference.

1. **Phase 0:** `scratch-init <slug> --question-original "…" --question-polished "…" --scope-assumptions "…" --ambiguity <clear|minor_uncertainty|unclear>` (add `--class thematic` for non-sutta-anchored questions). This records the active scratch for *this run*, fills the Phase 0 header fields, and — because all the Phase 0 evidence is then present — writes the Phase 0 exit gate automatically, so the run starts at Phase 1. Do not run the bare form unless the question is still unresolved; a bare init leaves gate 0 unwritten and every later gate will refuse until you run `scratch-gate 0`. Auto-logging is isolated automatically — the run's state is keyed to your agent process, so parallel runs never collide. There is nothing to pin or export **while you are the only agent working the run** (Phase 0/1, and Phases 5–7). The moment gather phases are delegated to sub-agents (below), that guarantee no longer holds — see the mandatory `VICAYA_PHASE` pin in **Sub-agent dispatch**.
2. **Each phase boundary:** end the prior phase with `scratch-gate <prev-phase>`. The gate auto-advances the active phase, so the next phase's helper calls log correctly without any manual step. It refuses if earlier gates are missing and prints the exact evidence still needed. Thematic runs auto-skip the Phase 2.5 (SC-parallels) and 3b (Sanskrit) gates.
3. **Start of Phase 5:** `scratch-verify`. Exit 0 = proceed to synthesis. Exit 1 = backfill the named phase first; do not draft.
4. **End of Phase 7:** `scratch-set-note <note-path> --pdf <pdf-path|skipped>` (records the saved paths in the scratch header — the [REJECTED] hard-gate target), then `scratch-self-audit` (answer the failure checklist — the gate refuses without it), then `scratch-gate 7`, then publish the saved note with `uv run scripts/sync_notes.py "Vicaya/${TODAY} - ${SLUG}.md"`; after writing the reflection, publish the run report with `uv run scripts/sync_run_report.py`. The run is not complete until the gate passes and both sync commands have been attempted.

If context compaction fires at any point, `scratch-resume <slug>` explicitly selects that run, reattaches the active scratch state, and prints the last gate and next phase — no findings are lost.

## Hard rules (read first — these are not preferences)

These rules apply to every run, by every agent. They are part of the skill, not stored in any agent's private memory.

1. **No AI / model attribution in the scholarship body.** Never write "Gemini noted", "Claude found", "the AI suggested", "added by cross-check", etc. inside the findings, evidence, or analysis. The body must read like scholarship — information and sources are what matter, not the process of producing them. If a second-pass review surfaces material, integrate it silently with proper citations to the underlying primary or secondary source. **The only places agent identity appears are the `agent` frontmatter field and the final footer line** (see Phase 7 — Agent self-identification). Those are metadata, not scholarship.
2. **No process or workflow logging inside the research note.** No "Improvements made" sections, no "the helper failed and I switched to X", no "this was missed in the first pass". Notes contain content; process belongs in the terminal report only (Phase 7's final summary), and improvement suggestions go into the run report under `## Improvement suggestions` for `/vicaya-improve` to process later — never into `SKILL.md` directly.
3. **Pāḷi spelling conventions differ per source:**
   - **Canon SQLite (`tipitaka-translation-data.db`) and the Obsidian vault** use exact Pāḷi diacritics (`paṭiccasamuppāda`, `dukkha`, `nibbāna`). Search verbatim. The `search-canon` helper normalizes niggahita (`ṁ`/`ŋ` → `ṃ`), case, and embedded markup automatically; direct SQL `LIKE` does not — there use `ṃ` exactly. If 0 hits, also try edition spelling variants (`pathavī`/`paṭhavī`, `kaṅkhā`/`kankhā`-type retroflex–dental swaps) before concluding absence.
   - **Library folders** index contains Calibre metadata labels with ASCII Pāḷi (`paticcasamuppada`). Diacritics in queries are handled automatically.
4. **Obsidian CLI requires the Obsidian desktop app to be running.** If a `search-vault` command exits with a traceback containing "app may not be running", launch the desktop app yourself in the background and wait ~5 seconds before retrying. Use the OS-appropriate command — **never bare `obsidian`** (that resolves to the CLI, not the app, on Linux):
   - **Linux:** `setsid xdg-open "obsidian://" >/dev/null 2>&1 &`
   - **macOS:** `open -a Obsidian`
   - **Windows:** `start "" "obsidian://"`
   The `obsidian://` URI is registered by every standard Obsidian install across all platforms regardless of install method (apt, AppImage, flatpak, dmg, installer). Don't ask the user to open it.
5. **Don't ask the user to run shell commands you can run yourself.** Read-only inspection, launching local applications, running helper scripts via `uv run` — all yours to do. Only ask when something genuinely requires the user: interactive logins, granting permissions, installing system packages, etc.
6. **Citations are non-negotiable.** Every claim has a reference. A claim without a citation is a hallucination waiting to happen.
7. **Auto-captions mishear Pāḷi.** YouTube's auto-generated captions mangle Pāḷi terms (e.g. "Suddhāso" → "saso", "Apaṇṇaka" → "apaka"). When a YouTube transcript's `is_auto` is true, **paraphrase and link to the timestamp** — never quote Pāḷi verbatim from auto-captions. Human-uploaded captions (`is_auto = false`) may be quoted with normal care.
8. **Query YouTube in English, anchor with Pāḷi sutta name + numeric reference.** Pāḷi-heavy queries return zero results; long English glosses return zero results. `apannaka sutta MN 60` works; `apannaka safe-bet wager rebirth` returns nothing.
9. **CST paragraph numbers are book-global, not sutta-local.** A `paranum` returned by `search-canon` is a continuous index across the entire book file — para 261 in `s0202m_mul` is MN78, not MN60. Always run `resolve-citation` to confirm which sutta a paragraph belongs to before citing it. Never assume the paragraph number matches a sutta number. Exception: a few books (Khp, Paṭisambhidāmagga, Netti, Milinda) restart paranums per section — `resolve-citation` then says "paranum repeats per section" and lists candidate sections; disambiguate from the hit's own text before citing.
10. **YAML frontmatter safety.** Always wrap YAML values in double quotes if they contain a colon followed by a space (e.g. `"Topic: Subtitle"`). Unquoted colons break Obsidian's property rendering.
11. **No global temporary directories.** Every stage must keep working files inside this repo. Use `data/scratch/` for anything needed after an interruption, restart, context refresh, or handoff. Use repo-local `temp/` only for disposable extraction files, and create it with `mkdir -p temp` before use.
12. **A 0-hit in a book you expected to contain the term is a book-code problem until proven otherwise.** Before concluding a term is absent from a given book or nipāta, confirm the code is right: run `lookup-book <your-code>` (or check the embedded book-code table) to verify you have the correct CST table for that text. The commonest mistake is AN nipāta off-by-one — `s0404m3_mul` is AN10 (Dasakanipāta), `s0404m4_mul` is AN11 (Ekādasakanipāta) — but the same pattern recurs across the Khuddaka collection. Only after confirming the code may you log 0-hits as evidence of absence.

## Inputs

- **Topic / question** (required): the user's original research request; Phase 0 preserves it and derives a polished research question.
- **Optional references** the user passed in: URLs, vault note names, book titles, sutta refs. Treat these as authoritative seeds.

### Question sanitization

Before using the topic as the note's `topic:` field value or the final note's
`## Question`, smooth it into a proper English sentence or question: complete
grammar, correct punctuation, question mark where the phrasing calls for one.
Remove any loaded or leading language — preconceived conclusions, partisan
framing, or strong opinions should not be baked into the question itself. Keep
the original scope and intent intact. The research body is where findings and
positions are reported; the question just names the topic neutrally. Preserve
the verbatim user input only in the scratchpad and run reflection as
`question_original:`.

## Setup — paths and tools

Hard-coded for this machine. If a path is missing or a tool isn't installed, stop and tell the user; don't guess.

All user-specific paths come from the project's `.env` file (see `.env.example` at the repo root). The helper module resolves them on import. Agents do not hard-code paths; use the helpers and CLI.

**Python env is a precondition, not a mid-run activity.** The project `.venv` must already be in sync with `uv.lock` (`uv sync`, run once per machine) before a research run starts. On a synced env `uv run` never needs uv's global cache — the lockfile has no git or local dependencies — which matters on macOS, where the sandbox denies `~/.cache/uv`. If a cache permission error appears mid-run, see **When something fails**.

**⚠️ `$VICAYA_*` variables are NOT set in your shell.** They are `.env` keys, loaded only by the Python helpers — every Bash call starts a fresh shell where `$VICAYA_DPD_DB` etc. expand to empty strings, and a `~` read out of `.env` by hand is never tilde-expanded. Before any **direct** shell command that uses them (`sqlite3`, `grep`, `ls`, `cp`, `rg` on those paths), put this prefix in the same Bash call:

```bash
eval "$(uv run tools/research_sources.py env)"
```

It prints all `VICAYA_*` values as shell-quoted `export` lines with `~` expanded, whatever style the `.env` uses. Helper CLI calls need no prefix — they load `.env` themselves.

- Vault Root: `$VICAYA_VAULT_PATH` (This is the absolute path to the root directory of the vault).
- Output folder in vault: `$VICAYA_VAULT_PATH/Vicaya/` (this folder is its own git repo — publish notes only through the pre-approved `scripts/sync_notes.py` path after Phase 7 validation/gating)
- Helper module: `<repo>/tools/research_sources.py`
- Canon db: read-only SQLite at `$VICAYA_CANON_DB`.
- DPD dictionary db: read-only SQLite at `$VICAYA_DPD_DB` — Pāḷi word meanings, grammar, roots, and inflected-form resolution. See the **DPD dictionary database** section below for the two lookup paths.
- Library folders: `$VICAYA_LIBRARY_FOLDERS` (pipe-separated paths) are indexed into `$VICAYA_LIBRARY_FOLDERS_INDEX`, a local SQLite FTS5 database. Calibre libraries are recognised automatically — author and tag metadata (`Calibre #id | Authors: … | Tags: …`) is prepended to each book's FTS text, making tag/author searches work through the unified index. Normal search reads the index only; source files are touched only during `library-folders-refresh` or manual inspection.
- Cross-check uses `VICAYA_CROSS_CHECK_CHAIN` (env), a pipe-separated `app:model` list tried in order (`opencode run -m <model>` or `agy --print ... --model <model>`). The first successful subprocess response wins; if the chain is empty or every entry fails, the helper returns a `# SELF_REVIEW:` sentinel and the agent runs the checklist on its own synthesis. vicaya does not store any provider API keys — `opencode`/`agy` must already be authenticated.
- **Book code → source XML map**: `/home/bodhirasa/MyFiles/3_Active/dpd-db/tools/pali_text_files.py` maps every canon book code (e.g. `s0201m_mul`) to its source XML file in the DPD database. Consult this when you need to know which raw XML file a given book code corresponds to, or when debugging why a search returns no results for a book you expect to exist.
- **EBC vault** (Early Buddhist Connections): `$VICAYA_EBC_VAULT_PATH` — a separate, read-only Obsidian vault of curated EBT material. Supplies per-sutta Āgama-parallel metadata, multiple parallel English translations of each sutta, Chinese-Āgama translations (Patton + BDK), and a Pātimokkha rule/commentary set. See the **EBC vault** section below.

## Calling the helpers

**Prefer the CLI over `python -c` heredocs.** Heredoc invocations have repeatedly caused quoting bugs (single-quotes-in-single-quotes SyntaxErrors) and field-name guesses (`.snippet` on a `CanonHit`, which has no such field). The CLI eliminates both.

**`jq` may be absent on this machine** (same caveat as `rg` — it's a Claude Code wrapper, not always a real binary). To slice helper JSON, pipe to `uv run python3 -c "import json,sys; …"`, not `jq`.

Run from the project root:

```bash
cd <repo-root>   # the vicaya repo
uv run tools/research_sources.py <subcommand> [args...]
```

**If you are a per-phase gather sub-agent** (see **Sub-agent dispatch**), prefix
every call below with `VICAYA_PHASE=<your-assigned-phase>` — this is mandatory,
not the bare form shown here. The bare form is only safe for the single
orchestrating session (Phase 0/1/5/6/7), which is never running concurrently
with anything else.

Subcommands (each prints JSON to stdout):

| Subcommand | Args | Notes |
|---|---|---|
| `env` | — | Prints `VICAYA_*` config as shell `export` lines (not JSON), `~` expanded, shell-quoted. Use as `eval "$(uv run tools/research_sources.py env)"` before direct shell commands that need `$VICAYA_*` paths (see Setup). |
| `search-vault QUERY` | `--folder PATH` `--limit N` | Obsidian vault full-text search |
| `search-canon QUERY` | `--books PAT...` `--lang pali\|english\|any` `--limit N` | Default books: sutta mūla (`s*_mul`) |
| `resolve-citation BOOK_CODE PARANUM` | — | Returns `Citation` JSON |
| `library-folders-check` | — | Probe configured library folders root/index. Does not walk the source tree. |
| `library-folders-refresh` | `--limit N` | Refresh the library folders SQLite index. This is the only command that walks the source tree. |
| `search-library-folders QUERY` | `--limit N` `--include-duplicates` `--timeout N` | Search the library folders index. Exact duplicates are collapsed by default. A stopword or one word of an unquoted multi-word phrase can force a full scan of a multi-gigabyte index; the query is aborted after `--timeout` seconds (default 20) with a clear `error: search timed out … too broad` on stderr instead of hanging. On timeout, retry with more specific or additional terms rather than raising the timeout. |
| `library-folders-duplicates` | `--samples N` | Read-only duplicate diagnostic from the local index. |
| `lookup-book VALUE` | — | Translate any CST book identifier into the others (filename, table, Pāḷi title, gui code, DPD code) |
| `cross-check` | `--timeout N`; **prompt on stdin** | App/model chain per `VICAYA_CROSS_CHECK_CHAIN` → `# SELF_REVIEW:` sentinel on failure. Output is post-processed: every sutta citation is stamped `[VERIFIED]`, `[REJECTED — not in sutta_info]`, or `[UNVERIFIABLE — …]` (global verse numbers). Use this in Phase 6. |
| `verify-citation REF` | — | Confirm a human sutta reference (`MN60`, `SN 46.42`, `Sn 4.8`, `Dhp 178`, `SN48.9-10`) exists in `dpd.db sutta_info`. Handles range-stored books by containment, hyphenated ranges by endpoints, Thag/Thig/Kp aliases. Exit 0 verified · 1 rejected · 2 unverifiable (global verse number — cite by chapter.sutta instead). Existence-only; says nothing about content claims. |
| `get-ebc-overview SUTTA_CODE` | — | Parsed EBC overview card: PTS ref, titles, themes, training, formula, **named Āgama parallels**, partial parallels. Accepts `MN10`, `mn 10`, `mn-10`, `DN22`, `MA98`, etc. Returns `EBCOverview` JSON or exits 1 if missing. |
| `get-agama SUTTA_CODE` | `--max N` | **Always call this immediately after `get-ebc-overview`.** Resolves every code in `parallels_agama`, reads the Patton (preferred) or BDK translation file, and returns the full text in `parallels_found`. Codes with no file on disk appear in `parallels_missing` — never silently dropped. Default max 5. |
| `search-ebc QUERY` | `--folder PATH` `--limit N` | Fixed-string grep across the EBC vault (markdown only). Returns `VaultHit`s. `--folder` accepts a subdir like `+Suttas/Overviews Suttas/MN` or `+Vinaya/Patimokkha/bmc1`. |
| `sc-parallels CITATION` | `--no-text` | Look up parallels for a citation (e.g. `mn18`, `sn35.28`) in the offline SuttaCentral archive. Returns `SCParallel` objects: `ref`, `resemblance` (bool, `~` prefix), `paragraph_range`, `text_pali`, `text_lzh`, `text_san`, `text_pra`, `translation_en`, `text_gaps` (list — explicit when text isn't in the partial archive). Parallel *identification* is comprehensive; text retrieval is best-effort. |
| `sc-search QUERY` | `--lang pli\|lzh\|san\|pra\|en` `--limit N` | Fixed-string grep across SuttaCentral offline root texts in one language. `lzh` = Literary Chinese Āgamas. Returns `VaultHit`s with the matched JSON segment. |

Parse the JSON with `jq` or read it as a file. Only fall back to `uv run python -c "..."` if you genuinely need to combine helpers in one step — and if so, write a short `.py` script under repo-local `temp/` and run that, rather than a heredoc.

## Helper return shapes (read before calling)

Every helper returns dataclasses serialised to JSON by the CLI. Field names are exact — guessing them has caused crashes in prior runs.

- **VaultHit**: `path` (str), `snippet` (str), `line` (int | null)
- **CanonHit**: `book_code` (str, e.g. `s0201m_mul`), `paranum` (str), `pali` (str), `english` (str). **No `snippet` field** — quote from `pali` / `english` directly. XML/TEI markup is stripped automatically; text is plain UTF-8. Hits on continuation rows (which carry no paranum of their own) come back with the nearest preceding paranum — the paragraph they belong to — so `paranum` pipes straight into `resolve-citation`.
- **Citation**: `machine` (e.g. `s0201m_mul:23`), `human` (e.g. `MN60 Apaṇṇakasuttaṃ para 97`), `pitaka`, `text_type`, `paranum`.
- **Library folders hit**: plain dict with `document_id`, `title`, `relative_path`, `source_path`, `extension`, `snippet`, `extraction_status`, `duplicate_count`, `duplicate_paths`, `possible_duplicate_of`, and `source_available`.
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

## DPD dictionary database (`dpd.db`)

The Digital Pāḷi Dictionary database — a separate SQLite file from the canon db.
Use it to look up the **meaning, grammar, and root** of any Pāḷi word, and to
resolve an **inflected or compound form** found in the canon back to its
dictionary entry. The skill already uses one of its tables (`sutta_info`) behind
`verify-citation`; this section covers the dictionary proper.

**Location.** Path is in `$VICAYA_DPD_DB` (e.g. `~/MyFiles/3_Active/dpd-db/dpd.db`).
Read-only, ~2 GB. If the variable is unset, tell the user to add
`VICAYA_DPD_DB=~/path/to/dpd-db/dpd.db` to `.env` (see `.env.example`) — don't
guess the path.

**Access.** Query it directly with `sqlite3`, exactly as the canon db is queried
above. `$VICAYA_DPD_DB` is empty in a fresh shell — every direct-SQL call starts
with the `eval "$(uv run tools/research_sources.py env)"` prefix (see Setup). The dpd-db repo ships a full SQLAlchemy model layer (`db/models.py`), but
that is for building/editing the dictionary and pins you to that repo's
environment; for read-only lookups raw SQL is simpler and the table/column schema
is stable. Resolve the JSON columns in Python (`json.loads`) when you need them.
If ordinary read-only access fails with `unable to open database file`, retry with
SQLite's immutable URI form: `sqlite3 "file:${VICAYA_DPD_DB}?mode=ro&immutable=1"
"SELECT ...;"`.

**Spelling.** Exact Pāḷi diacritics with the `ṃ` niggahita (never `ṁ`), same as
the canon db. Search verbatim.

### Way 1 — headword lookup (`dpd_headwords`)

You know a dictionary word and want its meaning, grammar, and derivation. Query
`lemma_1`, which is **sense-numbered** (`dukkha 1`, `dukkha 2`, …), so match with
`LIKE 'word%'` to get every sense:

```bash
eval "$(uv run tools/research_sources.py env)"
sqlite3 "$VICAYA_DPD_DB" \
  "SELECT lemma_1, pos, grammar, plus_case, meaning_1, meaning_lit, construction, root_key
   FROM dpd_headwords WHERE lemma_1 LIKE 'dukkha%' LIMIT 10;"
```

Useful columns: `lemma_1` (headword + sense number), `pos` (part of speech),
`grammar`, `plus_case` (case governed), `meaning_1` (primary gloss),
`meaning_lit` (literal), `meaning_2` (alternative gloss), `construction` (morph
breakdown, e.g. `√dukkh + a`), `root_key` (links to `dpd_roots`), `sanskrit`,
`example_1` + `sutta_1` (an attested canonical usage).

### Way 2 — inflected / compound form lookup (`lookup`)

You have an inflected or compound form from the canon and don't know its
dictionary form. Look the exact form up in `lookup`; it returns a JSON array of
`dpd_headwords.id` values plus a grammatical analysis:

```bash
eval "$(uv run tools/research_sources.py env)"
sqlite3 "$VICAYA_DPD_DB" \
  "SELECT headwords, grammar, deconstructor, roots FROM lookup WHERE lookup_key='dukkhassa';"
# headwords  -> [32875, 32876, 32877, 32878]   (ids into dpd_headwords)
# grammar    -> [["dukkha","adj","masc dat sg"], ...]   (each id's inflection reading)
# deconstructor -> compound splits, e.g. ["sabbaṃ + ca"] (empty for simple words)
# roots      -> candidate roots when relevant
```

Then resolve the ids against `dpd_headwords` to get the actual entries:

```bash
eval "$(uv run tools/research_sources.py env)"
sqlite3 "$VICAYA_DPD_DB" \
  "SELECT id, lemma_1, pos, meaning_1 FROM dpd_headwords WHERE id IN (32875,32876,32877,32878);"
```

`headwords`, `grammar`, `deconstructor`, and `roots` are JSON strings — parse with
`json.loads` to get the id list before the `IN (...)` query.

### Other tables

The two lookups above cover almost every need. The rest are there if a question
calls for them: `dpd_roots` and `family_root` for a term's verbal root and
word-family (etymology); `bold_definitions` to find where the aṭṭhakathā glosses
a term in bold; `sutta_info` for cross-coding a sutta across CST/SC/PTS/DPD (also
behind `verify-citation`); plus `family_word`/`family_compound`/`family_idiom`/
`family_set` and `inflection_templates` for finer morphological work.

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

1. **Any sutta-anchored question** → `get-ebc-overview <code>` then immediately
   `get-agama <code>`. The overview returns the parallel list and metadata; `get-agama`
   resolves each `parallels_agama` code to its Patton or BDK translation file and
   returns the full text. **Always call both — do not stop at the overview.**
   Codes with no file on disk appear in `parallels_missing`; note those as gaps.
2. **Cite the translation** → quote as *Madhyamāgama 98, trans. Charles Patton, §<n>*
   (Patton paragraphs are numbered). BDK translations cite as *Dīrghāgama 10,
   trans. BDK English Tripiṭaka*.
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
# Step 1: metadata + parallel list
uv run tools/research_sources.py get-ebc-overview MN10

# Step 2: fetch all Āgama translation texts (always do this immediately after)
uv run tools/research_sources.py get-agama MN10
# Returns parallels_found with full Patton/BDK text, parallels_missing for gaps.

# Free-text discovery scoped to one translator
uv run tools/research_sources.py search-ebc "ekayano ayaṁ maggo" \
  --folder "+Suttas/Sutta Texts/Sujato-pali" --limit 10

# Vinaya commentary search
uv run tools/research_sources.py search-ebc "pārājika" \
  --folder "+Vinaya/Patimokkha/bmc1" --limit 10
```

## Research scratchpad

**Model: scratch = comprehensive dossier. Vault = curated distillation.** The
scratch file is the only reliable defence against context compaction. If the
entire thread is lost mid-run, the scratch file must contain enough to rebuild
the dossier without re-running any expensive search.

**The helper owns the scratch format.** Never hand-craft scratch markdown.
Six subcommands cover every interaction:

```bash
# 1. At Phase 0 — create the file with the Phase 0 fields in one shot
#    (records this run's active scratch + phase AND writes the Phase 0 gate)
uv run tools/research_sources.py scratch-init <slug> \
  --question-original "<user's exact wording>" \
  --question-polished "<polished research question>" \
  --scope-assumptions "<textual/interpretive scope, depth, seeds>" \
  --ambiguity clear   # or minor_uncertainty | unclear
# add --class thematic for non-sutta-anchored questions (auto-skips 2.5 / 3b)
# Bare `scratch-init <slug>` still works but leaves gate 0 unwritten — you must
# then run `scratch-gate 0` yourself before any later gate will pass.

# 2. While searching — auto-log fires for every helper call, no exports needed
uv run tools/research_sources.py search-canon "anatta" --books "s*_mul"
# (full Pāḷi + English of every hit lands in scratch automatically)

# 3. For manual entries (web fetches, Read-tool excerpts you want to cite)
uv run tools/research_sources.py scratch-log 2 web "https://..." --summary "..."

# 4. At each phase end — appends the exit-gate checklist and advances the phase
uv run tools/research_sources.py scratch-gate 2
# Refuses if any earlier phase's gate is missing and prints the missing evidence list.

# 5. Before synthesis (Phase 5) — refuse to draft until all prior gates exist
uv run tools/research_sources.py scratch-verify    # exit 0 = proceed, 1 = backfill first

# 6. At Phase 7 — record the saved note + PDF paths in the scratch header
#    (sets the target of the [REJECTED] hard gate; never hand-edit the header)
uv run tools/research_sources.py scratch-set-note "Vicaya/${TODAY} - ${SLUG}.md" --pdf "<pdf-path|skipped>"
# Vault-relative paths resolve against VICAYA_VAULT_PATH; absolute paths work too.
# Refuses if the note file does not exist — pass the path exactly as saved.

# Resume after compaction or restart; explicit slug wins
uv run tools/research_sources.py scratch-resume <slug>

# Ad-hoc: print this run's active scratch path (for shell variables in code blocks)
uv run tools/research_sources.py scratch-which
```

**Auto-logging is on as soon as `scratch-init` has run.** The active scratch path
and phase are persisted to a per-run state file (`data/scratch/.active-<run>.json`)
keyed to your agent process. Every `search-*`, `sc-*`, `get-ebc-overview`,
`fetch-transcript`, and `cross-check` call appends a full
JSON-results block to the selected phase. Forgetting to log is structurally
impossible. Scratch target precedence is: explicit helper argument such as
`scratch-resume <slug>` or a direct `scratch=` path, then `VICAYA_SCRATCH` (manual
override), then the per-run state file. `VICAYA_PHASE` overrides only the phase for
helper auto-logs.

**Parallel runs are isolated automatically — nothing to pin.** The per-run state
file is keyed to the agent process that launched the helper calls, so two Vicaya
runs live at once (in any combination of agents — Claude, Gemini, opencode, …)
write to separate state files and cannot hijack each other's auto-log target.
There is no single shared `.active` pointer to clobber. You do **not** need to
`export VICAYA_SCRATCH`; it exists only as an explicit one-off override (e.g. to
force a specific scratch when resuming a run from a different process). `export`
does not survive between Bash calls in most agent harnesses anyway — rely on the
automatic per-run isolation instead.

**Within one run, the active-phase pointer is shared and racy — sub-agents must
pin `VICAYA_PHASE`, not rely on it.** Everything above isolates *runs* from each
other; it does nothing for *phases within the same run*. `scratch-gate` advances
the shared pointer the instant it writes a gate, and `export` doesn't survive
between Bash calls — so a sub-agent's own trailing helper call, or a sibling
sub-agent's call landing a moment late, can read a pointer that has already
moved on and file real evidence under the wrong phase's heading (issue #55: this
has silently scrambled headings and, once, tripped `scratch-gate`'s "no logged
evidence" refusal). An unpinned auto-log now appends a `phase-source: run-pointer`
line so this is visible on inspection instead of silent — but the fix is not
relying on the pointer at all inside a sub-agent: see the mandatory inline pin
in **Sub-agent dispatch** below.

**Within one run, helper writes are lock-serialized — hand-edits are not.**
Every scratch-mutating helper call (auto-logs, `scratch-log`, `scratch-gate`)
holds a blocking file lock for its whole read→splice→write, so helper calls in
the same parallel tool batch cannot clobber each other's appends. That lock
does **not** cover direct edits to the scratch file (Edit/Write tools, ad-hoc
scripts): never hand-edit the scratch in the same parallel batch as any
scratch-mutating helper call — a racing hand-edit silently drops the helper's
append (a real run lost a phase append this way). Run hand-edits alone, then
continue.

**Iron rule:** a phase cannot be left without calling `scratch-gate <phase>`.
`scratch-verify` is the enforcement mechanism at Phase 5 start — it exits 1 and
prints the missing gate plus its expected evidence list (or a `content_issue`
for a gate written over an empty/placeholder phase), so backfilling is
mechanical, not interpretive.

**Gate discipline** (each of these has caused a real run failure):

- **Gates are written only by the helper.** Never write a `### PHASE N EXIT
  GATE` header by hand — a bare header has no timestamp or checklist body and
  later gate/verify calls will not honour it, forcing a full backfill. This
  applies to every gate, not just the final one.
- **Backfill ascending.** If any gate call reports an earlier gate missing,
  backfill with `scratch-gate <missing>` in ascending order (0, 1, 2, …) in one
  uninterrupted pass, then continue. Do not interleave gating with re-running
  searches.
- **Backfill after gate is fine.** A gate is append-only history, not a lock.
  If work for an already-gated phase completes later (e.g. a source became
  reachable), log the new evidence under that phase with
  `scratch-log <phase> …` — do not rewrite or duplicate the gate.

Scratch files accumulate in `data/scratch/` (gitignored). Future runs on
related topics should grep them for already-harvested sources before starting
fresh queries.

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

Journal article (if available via library folders or web):
```
Anālayo, Bhikkhu. "The Luminous Mind in Theravāda and Dharmaguptaka Discourses."
  *Journal of the Oxford Centre for Buddhist Studies* 13 (2017): 10–51.
  (Calibre #8904)
```

When publisher / year / page range are not available from the library folders metadata, include
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

**Two evidence classes thematic searches miss** (from real runs): (1) For a question about the *meaning, scope, or authority* of a term, also search the **definitional loci** — the Vinaya *padabhājaniya* word-definitions (e.g. Pācittiya 4 defines *dhamma* as *buddha/sāvaka/isi/devatā-bhāsita*) and the Abhidhamma definitions — not only thematic stems. (2) For any *authenticity / canonicity / authority* question, treat each corpus's **origin-story (*nidāna*)** as its own evidence class: the legitimation narrative (the Atthasālinī's deva-realm Abhidhamma, the *Prajñāpāramitā* nāga legend, *terma*) is itself the data.

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
- **EBC vault** (`get-ebc-overview <code>` then `get-agama <code>`) — always call
  both. `get-agama` returns the full Patton or BDK translation text for each named
  Āgama parallel; `parallels_missing` lists codes with no file available.
- **Library folders — search "Analayo"** — Bhikkhu Anālayo's *Comparative Study of the
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
Abhidhamma reference. Library folders — tag `Abhidhamma`; authors Bhikkhu Bodhi
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
commentarial summa. Library folders — tag `Commentary`, tag `Atthakatha`.
*Satisfying hit:* a Buddhaghosa, Dhammapāla, or ṭīkā gloss cited with
paragraph reference; explicit note when the commentary diverges from a
plausible reading of the mūla.

### Other schools of Buddhism

**6. Mahāyāna / Vajrayāna / Yogācāra.**
*Applies to:* any question where a comparative-school reading enriches the
analysis (philosophy of mind, emptiness, bodhicitta, tantric practice,
buddha-nature, ālaya-vijñāna, two truths, etc.).
*Where to search:* library folders — search for tag `Mahayana`, `Mahayana Sutra`, `Madhyamaka`,
`Tibetan Buddhism`, `Zen Buddhism`, `Vajrayana` (verify against
`data/calibre_tags.csv`). Corporate author `84000` (the Tibetan translation
project, 36 books). Tag `Yogacara` may not exist verbatim — consult the csv,
fall back to free-text search. Web: 84000.co, Lotsawa House, Berzin Archives.
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
- **Library folders**: tag `Sanskrit Text`; verify against `data/calibre_tags.csv` whether
  `Hinduism`, `Jainism`, `Vedic`, `Upanishads`, `Indology`, `Indian Religion` exist
  as tags — use what is present, free-text otherwise. Authors: Patrick Olivelle,
  Johannes Bronkhorst, Richard Gombrich (esp. *How Buddhism Began*), Karel Werner.
- **Web**: GRETIL online (gretil.sub.uni-goettingen.de) when local corpus absent;
  *Encyclopædia of Indian Religions*.

*Satisfying hit:* a verbatim IAST passage from GRETIL with text name + line number,
**or** a Sanskrit / Vedic / Jain passage via library folders or scholar's analysis showing
the term, debate, or image at issue; explicit note when the Buddhist position responds
to or departs from the precedent. Note: searching by English translation theme is
often more productive than searching IAST terms directly.

**8. Other religions — Christianity, Islam, Daoism, Confucianism, etc.**
*Applies to:* questions where cross-religious comparison is genuinely
illuminating — contemplative practice, mystical phenomenology, ethics,
soteriology. Apply selectively; do not force.
*Where to search:* library folders — search for tag `Comparative Religion`, `Comparative Studies`,
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
*Where to search:* library folders — Thai Forest (`Ajahn Chah`, `Ajahn Brahmavamso`,
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
*Where to search:* library folders — consult `data/calibre_tags.csv` for `Sociology`,
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
*Where to search:* library folders — search for tag `Psychology` (668 books, well-populated), plus
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
*Where to search:* library folders — search for tag `Philosophy` (631 books). Authors: Mark Siderits,
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
*Where to search:* library folders — search for tag `Cognitive Science`, `Neuroscience`,
`Consciousness`. Authors: Francisco Varela, Evan Thompson (*Mind in Life*,
*Waking, Dreaming, Being*), Antoine Lutz, Richard Davidson, Wendy Hasenkamp,
Cliff Saron, Judson Brewer. Web: *Mind & Life Institute*, *Frontiers in Human
Neuroscience*.
*Satisfying hit:* a cognitive-science result or theoretical framework paired
with the Buddhist construct it engages, cited.

**14. Archaeology — material culture, sites, inscriptions, art history.**
*Applies to:* questions about early Buddhist history, Aśokan period, monastic
architecture, relics, the historical Buddha, regional spread, dating debates.
*Where to search:* library folders — consult `data/calibre_tags.csv` for `Archaeology`,
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
*Where to search:* library folders — search for tag `History` (808 books, well-populated). Authors:
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
- Library folders — search "Analayo", "Bingenheimer" (SA), "Choong" (EA), tags `Comparative Studies`, `Chinese Canon (Tripitaka)`.
**Hard rule — machine-translated Chinese is comprehension-only.** When no
published translation exists, machine translation may be used as a reading aid
to assess relevance. It must **never** be quoted in the vault note as a
translation. Only published translations (Patton, BDK, Anālayo, Bingenheimer,
Sujato where available) may be quoted. Absent a published translation, paraphrase
and mark as "(no published translation; summary from Chinese source)".
*Satisfying hit:* a named parallel recension with a published translation quote,
or an explicit statement of doctrinal divergence between Pāḷi and Āgama versions
with both sides cited.

### Phase 0 — Request understanding and scope check

Before research, convert the user's request into a clean research question.
Always record these working fields in the scratchpad — pass them to
`scratch-init` (see Critical execution rules), which fills the header and
writes the Phase 0 exit gate in one shot:

- `question_original` (`--question-original`): the user's exact wording.
- `question_polished` (`--question-polished`): a grammatical, neutral,
  complete research question.
- `scope_assumptions` (`--scope-assumptions`): inferred textual scope,
  interpretive scope, depth, practical angle, and seed sources.
- `ambiguity_status` (`--ambiguity`): `clear`, `minor_uncertainty`, or
  `unclear`.

If the question needs user confirmation first (ambiguity), resolve that
*before* `scratch-init`, then init with the confirmed fields.

The `question_polished` is the question used in the final vault note. The
original request is preserved only in scratch/reflection metadata, not as the
displayed `## Question`.

If the request is clear and specific enough that misunderstanding is unlikely,
do not ask for confirmation. Proceed directly to Phase 1 using `question_polished`.

If there is any realistic ambiguity, speech-to-text corruption, unclear scope,
unclear tradition, unclear source layer, unclear depth, or unclear seed
reference, stop and ask for confirmation before research. Rephrase the request
and list the assumptions:

```text
I understand the research question as:

<question_polished>

Assumptions:
- Textual scope: <mūla/commentary/both/other>
- Interpretive scope: <neutral map / named dispute / named teacher>
- Depth: <full note / focused answer>
- Practical angle: <included/excluded>
- Seeds: <texts/scholars/notes inferred>

Please confirm or correct this before I begin.
```

Ask the five detailed scope questions only when the uncertainty cannot be
resolved by a simple confirmation request. Present them together in a single
message — don't ask one at a time. Wait for the response, then carry the answers
into Phase 1.

1. **Textual scope** — Are you asking about the mūla (root canon), the commentarial tradition, or both? Any particular Nikāya or text?
2. **Interpretive dispute** — Is there a specific school, teacher, or scholarly debate you want foregrounded, or should the note map the main positions neutrally?
3. **Depth** — Full note (~3,500 words, all applicable angles) or a focused answer on one specific aspect?
4. **Practical angle** — Do you want the note to connect the topic to practice and modern teachers, or keep it primarily textual/scholarly?
5. **Seeds** — Any specific suttas, scholars, books, or vault notes you already know are relevant?

If the question already answers most of these (e.g. `/vicaya the cessationist
vs. realist readings of Nibbāna in the commentaries`) skip the questions and
proceed directly to Phase 1 — don't ask for confirmation the user doesn't need.

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

**Enrichment runs.** If the vault search surfaces an existing Vicaya note on
this same topic, this is an enrichment run, not a fresh compile. Read the
existing note in full — its `## Critical Gaps` table is the ready-made research
plan — and target the gaps. At Phase 7, update the existing note in place (keep
its filename and `date`; add the new entries, then update the frontmatter refs,
bibliography, and footer to match) rather than writing a near-duplicate sibling.
When adding entries to a numbered series note, check every cross-reference
between entries after renumbering — they do not update themselves.

**EBC seed lookup** — if the question is anchored on one or more specific suttas (named in the user's question, or surfaced by the vault search), call `get-ebc-overview <code>` once per sutta. The returned `parallels_agama` and `parallels_partial` lists feed directly into the perspective map and the Phase 3 parallel-evidence search; the `themes`, `formula`, and `training` fields can suggest related suttas you might otherwise miss. This costs nothing and replaces a SuttaCentral parallel-table lookup.

For thematic (non-sutta-anchored) questions, `eval "$(uv run tools/research_sources.py env)" && grep -F "<theme>" "$VICAYA_EBC_VAULT_PATH/Catalogue/Suttas-Catalogue.tsv"` is the cheapest way to surface a candidate sutta list before Phase 2 — the TSV has columns for theme, topic, training, formula, and parallels.

**Perspective map.** Before moving to Phase 2, explicitly name the 2–5 competing positions or schools of thought the question touches. Examples: "Theravāda commentarial vs. Ñāṇavīra structural", "cessationist vs. realist readings of Nibbāna", "three-lives vs. momentary paṭiccasamuppāda". If the question is purely factual with no interpretive dispute, skip this step. Otherwise, tag subsequent evidence — canon hits, library sources, web sources — as supporting a named position. This ensures the final note covers all significant views, not just the first position the search surfaces.

**Counter-perspective search.** For each position named in the perspective map, actively search for sources that support it — don't rely on the first position the keyword searches happen to surface. If a web or canon search returns only one school's voice, run a second search scoped to a known proponent of the opposing view (e.g. `authors:Analayo` for early-Buddhist readings, a specific scholar for the academic critique). Evidence gaps for any named position belong in Critical Gaps, not silent omission.

→ **Phase 1 exit:** `uv run tools/research_sources.py scratch-gate 1`. Auto-log has already captured the helper calls; the gate writes the canonical checklist (angle triage, vault hits, perspective map, counter-perspective targets) — tick the boxes once each is true.

### Sub-agent dispatch (after Phase 1 gate) — one sub-agent per phase

After the Phase 1 gate passes, run the gather phases as a **sequence of single-phase sub-agents** — one per applicable phase, in order (2, 2.5, 3, 3b, 4a, 4b, 4c), skipping any phase the angle triage marked non-applicable. Spawn the next agent only after the previous one returns and you have spot-checked it. This keeps the main context clear for synthesis while bounding each sub-agent to one phase.

**Thematic auto-skip applies to gates only, not to work.** On a thematic (non-sutta-anchored) run, `scratch-gate` auto-writes the 2.5 and 3b gates without requiring the usual evidence — but if angle 16 (Āgama comparison) or angle 7 (Sanskrit/comparative) was marked *applicable* in Phase 1, the work for that phase must still be done. Run the SC-parallels or Sanskrit searches; the gate just won't block on them. Skipping the gate is not permission to skip the research.

**Why per-phase, not one agent for all of 2–4c.** A sub-agent that runs every phase accumulates full SKILL sections + the growing scratch + verbose search dumps + full transcripts and crashes with "Prompt is too long" mid-run. There is **no warning before it dies** — an overflowing agent just returns the error — so you cannot react to it, only prevent it. One agent per phase bounds each agent's context to a single phase's work, so an overflow or crash costs at most one phase, and the orchestrator never holds the verbose tool output.

The only datum each prompt must carry is the **scratch slug** — `uv run tools/research_sources.py scratch-which` resolves the active scratch path. Everything else is already in the scratch file; do **not** re-transcribe the angle triage, perspective map, or seeds into the prompt.

**Spawn** each phase agent:

- **Claude Code:** Use the Agent tool with `model: "sonnet"` (only environment where a cheaper model can be selected). Every other environment inherits the parent model — context isolation is the benefit, not cost savings.
- **Any other environment:** Use that environment's sub-agent mechanism. If dispatching a gather phase via an external CLI subprocess (e.g. `opencode run -m <model>`), launch it with `run_in_background: true` from the *first* call, never foreground: the CLI's streaming latency alone can exceed the Bash tool's ~120s foreground cap and silently cut the process off mid-phase — search calls and auto-logging can complete while only the final `scratch-gate` call gets truncated, which is worse than an obvious failure because it looks like a clean phase from the scratch alone.

**Four rules keep each agent light and correctly filed — state all four in every dispatch prompt:**

1. **Pin `VICAYA_PHASE=<PHASE>` inline on EVERY helper call, no exceptions.** This is not advisory and it is not the same as exporting it once — `export` does not survive between Bash calls, and even if it did, the shared per-run active-phase pointer moves the instant any phase (yours or a sibling's) gates, so relying on it is a race (issue #55: it has scrambled which phase auto-logged content lands under, and once caused `scratch-gate` to refuse with "no logged evidence"). Prefix every single `search-*`/`sc-*`/`get-*`/`fetch-*` call: `VICAYA_PHASE=<PHASE> uv run tools/research_sources.py search-canon ... --quiet`. An unpinned call is visible after the fact as a `phase-source: run-pointer` line in the scratch — there should be none inside a phase sub-agent's own log entries.
2. **Read only the briefing, never the dossier.** Read the Phase 0/1 briefing block at the TOP of the scratch (question, angle triage, perspective map, seeds) — never the accumulating evidence blocks below it. Auto-log already persists every hit; re-reading them is what fills the context.
3. **Pass `--quiet` on every search helper call** (`search-canon`, `search-library-folders`, `search-ebc`, `search-sanskrit`, `sc-parallels`, `sc-search`, `get-agama`). The full result still goes to the scratch dossier; only the agent's stdout is compacted to a snippet — that compaction is what keeps the agent's context from filling. (The dossier and the synthesised note are unaffected: full text always lands in the scratch.)
4. **Read only the SKILL sections for its one phase** (table below), plus the shared preamble.

**Phase 4b transcript rule.** The YouTube agent collects video **details** (titles, channels, URLs, tiers) for the candidate set and pulls a transcript **only** for a video clearly relevant to the question — never bulk-fetch transcripts. A full transcript is ~4,000 lines and is the single largest context killer; one is plenty, zero is fine when the titles already settle relevance.

**Shared preamble** (every phase agent reads these): `## Critical execution rules`, `## Hard rules`, `## Setup — paths and tools`, `## Calling the helpers`, `## Helper return shapes`, `## Research scratchpad`, `## Evidence tiers`, `## When something fails`.

**Per-phase sections** (the agent reads only its own row in addition to the preamble):

| Phase | Also read |
|---|---|
| 2 | `### Phase 2 — Canon search` (incl. the EBC parallel-evidence pull subsection), `## Book-identifier lookups`, the book-code map |
| 2.5 | `### Phase 2.5 — SuttaCentral offline parallel search` |
| 3 | `### Phase 3 — Library search` |
| 3b | `### Phase 3b — Sanskrit source search` |
| 4a | `### Phase 4a — Web search`, `## EBC vault` |
| 4b | `### Phase 4b — YouTube search` |
| 4c | `### Phase 4c — WisdomLib` |

**Dispatch prompt** (one per phase — fill `<PHASE>` and `<PHASE-SECTIONS>`):

```text
You are a Vicaya gather sub-agent for ONE phase of an in-progress run.
Do NOT run any other phase. Do NOT run Phase 0, 1, 5, 6, or 7. Do NOT write to the vault.

Repo root: <repo-root>
Scratch slug: <slug>
Phase assigned: <PHASE>

MANDATORY: prefix EVERY helper call below with VICAYA_PHASE=<PHASE> inline,
e.g. `VICAYA_PHASE=<PHASE> uv run tools/research_sources.py search-canon ... --quiet`.
Do not rely on the run's shared active-phase pointer — a sibling sub-agent's
scratch-gate call (or your own) can advance it out from under you mid-phase and
misfile your evidence under the wrong heading. This applies to every step below
that calls a search/fetch helper, not just step 4.

Steps:
1. cd <repo-root> && uv run tools/research_sources.py scratch-resume <slug>
   (Attaches to the run; auto-logging then writes to this run's scratch. This
   call itself is exempt from the VICAYA_PHASE prefix — it isn't auto-logged.)
2. Read ONLY the Phase 0/1 briefing block at the TOP of the printed scratch path —
   the question, angle triage, perspective map, and seeds. Do NOT read the
   accumulating evidence blocks lower in the file (auto-log already has them).
3. Read from skill/vicaya/SKILL.md (the actual file — not training data): the
   shared preamble (Critical execution rules, Hard rules, Setup, Calling the
   helpers, Helper return shapes, Research scratchpad, Evidence tiers, When
   something fails) plus your phase's sections: <PHASE-SECTIONS>.
4. Execute Phase <PHASE> per those instructions. Prefix EVERY search helper call
   with VICAYA_PHASE=<PHASE> (see MANDATORY above) and pass --quiet (full results
   still go to the scratch; only your stdout shrinks).
   (Phase 4b only: collect video details; fetch a transcript ONLY if a video is
   clearly relevant — never bulk-fetch transcripts.)
5. Gate it: uv run tools/research_sources.py scratch-gate <PHASE>
6. Return a 2–3 line report: source counts, gate status, and anything you could
   NOT do (0-hit bodies you expected to find, missing files) so the orchestrator
   can backfill.
```

**After each agent returns — spot-check before spawning the next.** `scratch-verify` now also flags gated-but-empty and placeholder-only phases (`content_issues`), so it backstops a crashed/limited/stubbed agent structurally — but still spot-check immediately after each agent so a silent gap is caught before the next agent builds on it, not only at the Phase 5 verify.

- Confirm the phase's section has real logged hits, not just a header: `grep -n '^## Phase' <scratch>` for the section bounds, then check it is not empty. Scan 4a/4b/4c logs for "would search"/placeholder language. An empty-but-gated phase is a silent gap — re-run that phase before continuing.
- **Check for misfiled content:** `grep -n 'phase-source: run-pointer' <scratch>`. Any hit means that sub-agent did not pin `VICAYA_PHASE` on that call — go read the entry and confirm it landed under the correct heading (it may belong under a different phase's section entirely if the pointer had already moved on). Zero hits is the expected state for a correctly-run sub-agent.
- If a spawn fails (shared-account session limit, or the Agent tool blocked by a hook), run that one phase inline in the orchestrator yourself, then gate it.
- **Re-verify the top cited suttas before spawning the next agent.** A sub-agent's completion report names the suttas it found — run `verify-citation` on the 2–3 highest-priority ones before accepting them. A sub-agent can report evidence not actually in the scratch (context-exhausted hallucination), name suttas without having run `resolve-citation`, or get 0 hits from a wrong book code and silently log them as absent. The re-verify step catches all three before the next phase builds on the error. Log the result in the orchestrator's working notes ("verified: MN60 ✓, AN4.1 ✗ not found in sutta_info — re-run phase 2 for this book"); if a cited sutta fails, treat it as a content issue and backfill, same as an empty phase.

After the last phase, run `uv run tools/research_sources.py scratch-verify`:

- Exit 0 → proceed to Phase 5.
- Exit 1 → the output names either a **missing** gate (with its expected evidence) or a **content_issue** (`empty` / `placeholder` — the phase is gated but was never really worked). Either way, run that phase (inline or a fresh single-phase agent) so it has real logged hits, then re-verify. Never proceed to Phase 5 with a missing gate or an empty phase.

Note: with no `--through`, `scratch-verify` checks every pre-synthesis phase (0 through 4c) — the same set `scratch-gate 5` requires — so it no longer stops at the highest gate written and miss an ungated 4b/4c in the middle. Thematic runs skip the 2.5/3b gates.

### Phase 2 — Canon search

**Book code map** — all codes are embedded here. Never guess a code from memory.

Codes come directly from the CST XML file headers. The suffix `_mul` = mūla (root text);
`_att` = aṭṭhakathā (commentary); `_tik` = ṭīkā (sub-commentary). Pass codes verbatim
to `--books`.

**Each book code is also the exact SQLite table name in the canon database.** For example,
the Paṭisambhidāmagga mūla is stored in a table named `s0517m_mul`, with columns
`paranum`, `pali_text`, `english_translation` (full schema below). The `search-canon`
helper queries these tables directly using the codes you pass to `--books`. This means you
can also query the database directly via `sqlite3` if you need ordered paragraph access
(e.g. `SELECT paranum, pali_text, english_translation FROM s0517m_mul ORDER BY
CAST(paranum AS INTEGER) LIMIT 5`). Note the column names are `pali_text` /
`english_translation`, not the `pali` / `english` field names CanonHit uses.

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

When in doubt, drop one more character than you think you need — but expect false positives: substring match means a short stem also hits unrelated compounds and homographs (`mān` hits both `māna` conceit and `mānasa`). Skim each hit's context before counting it as evidence; the stem casts the net, it does not classify the catch.

To go the other way — turn an inflected form back into its dictionary stem, case, and number — look the exact form up in the DPD `lookup` table (see the **DPD dictionary database** section).

```bash
uv run tools/research_sources.py search-canon "<Pāḷi stem>" --books "s*_mul" --lang pali --limit 20
# Also try English if the user used English terms:
uv run tools/research_sources.py search-canon "<English term>" --books "s*_mul" --lang english --limit 20
```

**0-hit recheck protocol (Hard Rule 12).** If a search returns 0 hits in a specific book that the question or the perspective map predicts should contain the term, do not log "absent" yet. Confirm the book code first:

```bash
uv run tools/research_sources.py lookup-book "<your code or book name>"
```

If `lookup-book` returns a different `cst_table` than the one you searched, re-run with the correct table. Common mistake: AN nipāta codes are volume-numbered, not nipāta-numbered — `s0404m3_mul` = AN10 Dasakanipāta, `s0404m4_mul` = AN11 Ekādasakanipāta. Only after confirming the code matches the book may you log 0-hits as evidence of absence.

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
  "english": "In attentive hearing, wisdom is knowledge born of hearing."
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
eval "$(uv run tools/research_sources.py env)"
test -s "$VICAYA_CANON_DB" || { echo "VICAYA_CANON_DB missing or empty: $VICAYA_CANON_DB" >&2; exit 1; }
sqlite3 -readonly "$VICAYA_CANON_DB" \
  "SELECT id, paranum, pali_text, english_translation FROM <table> WHERE id BETWEEN <start_id> AND <end_id>;"
```

**When a direct-SQL hit has empty `paranum`** — this is normal for subhead, gatha, and continuation rows within a paragraph (only the first row of each paragraph carries `paranum`). `search-canon` hits already arrive with the owning paranum filled in; this recipe is only needed when you query the db directly. To find the owning sutta, query by `id`:

```bash
eval "$(uv run tools/research_sources.py env)"
test -s "$VICAYA_CANON_DB" || { echo "VICAYA_CANON_DB missing or empty: $VICAYA_CANON_DB" >&2; exit 1; }
# Find the nearest preceding paranum for a hit at row <id>:
sqlite3 -readonly "$VICAYA_CANON_DB" \
  "SELECT paranum FROM <table> WHERE id < <hit_id> AND paranum != '' ORDER BY id DESC LIMIT 1;"
# Then resolve it:
uv run tools/research_sources.py resolve-citation <table> <paranum>
```

**Shell-loop pitfall.** Always pass `book_code` and `paranum` as two separate literal arguments — never as a single space-joined variable. A loop variable like `ref="s0202m_mul 97"` passed as `resolve-citation $ref` sends one argument and the parser fails. Use `resolve-citation $book_code $paranum` with two distinct variables, or quote/split explicitly.

If the hit is a `subhead` rend (the row introduces the next sutta), prefer looking forward — the following non-empty `paranum` is the sutta it names. If it is a continuation `bodytext` or `gatha`, look backward — the preceding non-empty `paranum` owns it.

**Quote fully, not representatively.** Pull up to 20 of the most pertinent paragraphs and plan to use all of them in the Canon Evidence section — not just a curated sample. "Genuinely relevant" means relevant to at least one position in the perspective map; it does not mean "I'll pick the 2–3 best." If you retrieved 15 hits and your final note cites 3, you have discarded evidence without cause.

**⚠️ IRON RULE — Paragraph numbers are book-global.** The `paranum` in a `CanonHit` is a continuous index across the entire book file, not local to the sutta. Always run `resolve-citation` to confirm which sutta a paragraph belongs to before citing it (see Hard Rule 9).

**After individual hits cluster in the same book or nipāta, scan the wider structural unit.** Stem-search returns scattered paragraph hits but misses thematic chapter blocks (e.g. AN8.31–39 dāna chapter, SN35.* sense-contact group). When hits concentrate in one table, do a broader window query:

```bash
eval "$(uv run tools/research_sources.py env)"
test -s "$VICAYA_CANON_DB" || { echo "VICAYA_CANON_DB missing or empty: $VICAYA_CANON_DB" >&2; exit 1; }
sqlite3 -readonly "$VICAYA_CANON_DB" \
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
| `english_translation` | TEXT | English translation where available (generated draft — verify load-bearing wording against `pali_text`) |
| `*_mark`, `*_timestamp` | TEXT | translation bookkeeping (`chinese_translation_mark`, `english_translation_timestamp`, …) |

Table-name suffixes: `_mul` = mūla, `_att` = aṭṭhakathā, `_tik` = ṭīkā, `_nrf` = non-canonical reference.

**Diacritics in direct SQL.** The canon db stores NFC UTF-8 with native Pāḷi diacritics. Direct SQL `LIKE` must use the real characters (`ñ`, `ā`, `ṭ`, etc.) and the `ṃ` niggahita (never `ṁ`). Example: `WHERE pali_text LIKE '%papañca%'` → hits correctly. `WHERE pali_text LIKE '%papanca%'` → 0 hits. The ASCII-insensitivity rule applies to the library folders FTS index (and it handles diacritics automatically); never strip diacritics for canon SQL.

**⚠️ Multi-word phrases: use `search-canon`, not direct `LIKE`.** Rows embed TEI markup mid-phrase (`Evaṃ me su<pb ed="V" n="1.0001" />taṃ`), so a direct `LIKE '%evaṃ me sutaṃ%'` silently misses ~75% of occurrences (123 raw vs 460 normalized across `s*_mul`). The helper strips markup, folds `ṁ`→`ṃ`, and ignores case before matching; direct SQL does none of that. Reserve direct SQL for single-word stems and `id`-window pulls.

**Trust the Pāḷi, verify the English.** `english_translation` is a generated draft: coverage varies by book and the alignment is occasionally off (wrong-paragraph English has been observed). Quote it as a convenience gloss, but verify any doctrinally load-bearing wording against the `pali_text` (or a published translation from EBC) before it carries weight in the note.

→ **Phase 2 exit:** `scratch-gate 2`.

#### EBC parallel-evidence pull

For every sutta cited from the Pāḷi canon in Phase 2, pull the matching parallel evidence from EBC. This is what the Phase 1 `get-ebc-overview` call set up:

1. **Chinese Āgama parallels.** From the overview's `parallels_agama` list, pick the closest parallel(s) (full parallels first, then partial). `Read` the Patton translation at `+Suttas/Sutta Texts/Agamas Dhamma pearls/<nik>-patton/<code>-patton.md`, falling back to BDK at `Agamas BDK/<nik>-bdk/<code>-bdk.md` if no Patton file exists. Quote verbatim with paragraph numbers and attribute to the translator (e.g. *Madhyamāgama 98, trans. Charles Patton, §5*). This is T1 evidence for the parallel recension and is *not* substitutable by a SuttaCentral link.
2. **Alternative Pāḷi translations.** When a translator-specific reading is doctrinally load-bearing (e.g. a contested term like *vitakka* / *vicāra* or *upādāna*), pull a second translator from `Sutta Texts/Bodhi/`, `Sujato-pali/`, `dn_walshe/`, or `Thanissaro notes/` and quote side-by-side. T3.
3. **Vinaya rule + commentary.** For Vinaya questions, after the canon mūla quote, pull bmc1 (`+Vinaya/Patimokkha/bmc1/`) for Ṭhānissaro's analysis and/or Ñāṇatusita (`+Vinaya/Patimokkha/Ñañatusita/`). T2.

Pāḷi names in EBC use exact diacritics, same as the canon db. The overview-card paths are absolute — copy them directly into `Read`. If a named parallel has no file (rare), note it as a known gap rather than silently dropping the parallel.

→ **EBC pulls:** auto-log already captures the helper calls. For `Read`s of EBC translation files that you cite, run `scratch-log 2 read <path> --summary "<one line>"` so the dossier still has them.

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

→ **Phase 2.5 exit:** `scratch-gate 2.5`.

### Phase 3 — Library search

**Phase 3 preflight — check the library folders index is reachable before querying:**

```bash
uv run tools/research_sources.py library-folders-check
```

If this exits 1, the index path is missing or the database cannot be opened. The message tells you which. Proceed without the index and note the gap rather than retrying blindly.

The library folders index covers all configured library paths including Calibre books. The tag vocabulary is in `<repo>/data/calibre_tags.csv` (~2k tags).

**Tag vocabulary first.** Before guessing technical terms, list the real tag vocabulary:
```bash
# grep -i "<concept>" data/calibre_tags.csv
```
Pick the closest existing tag. When in doubt, use the csv.

```bash
uv run tools/research_sources.py search-library-folders "<term>" --limit 20
```

**Format-agnostic extraction.** Books are in any format — PDF, epub, MOBI, doc,
txt, AZW3, or others. Never assume epub. Per-format extraction:

```bash
SCRATCH="$(uv run tools/research_sources.py scratch-which)"
RUN_TEMP="temp/$(basename "${SCRATCH%.md}")"
mkdir -p temp
```

| Format | Command |
|---|---|
| PDF | `pdftotext /path/to/book.pdf -` |
| epub | `mkdir -p "$RUN_TEMP/epub_extract" && find "$RUN_TEMP/epub_extract" -mindepth 1 -depth -delete && unzip -q /path/to/book.epub -d "$RUN_TEMP/epub_extract" && rg "<term>" "$RUN_TEMP/epub_extract"/` |
| .doc | `mkdir -p "$RUN_TEMP" && libreoffice --headless --convert-to txt /path/to/book.doc --outdir "$RUN_TEMP" && rg "<term>" "$RUN_TEMP/"*.txt` |
| Any format | `mkdir -p "$RUN_TEMP" && ebook-convert /path/to/book.<ext> "$RUN_TEMP/book.txt" && rg "<term>" "$RUN_TEMP/book.txt"` |

`ebook-convert` (ships with Calibre) is the universal fallback for most formats, but fails silently on legacy `.doc` files — use `libreoffice` for those. The book's source
path is in the metadata returned by `search-library-folders` or from the library's folder.

**Zero-hit fallback.** If a known author returns 0, try searching by title keyword
or a distinctive term from the book, and inspect the `title`/`relative_path` fields
from the returned hits. E.g. `search-library-folders "Armstrong" --limit 5`.

Snippets come back with each hit when FTS text is indexed — quote them with book + author attribution. If `extraction_status` is not `"ok"`, extract manually with `pdftotext` or `ebook-convert`.

#### Library folders search guidelines

The library folders index is an FTS5 database. All Calibre books are included with their author and tag metadata prepended. Search the index using natural language or tag/author terms (e.g. `"Bhikkhu Bodhi"`, `"Buddhism"` — these appear as literal prefix text in the FTS rows). Zero results mean no match; try broader terms or check `library-folders-check`.

**Hard rule:** search results are evidence, not a complete survey. Always run `search-library-folders` before concluding a topic has no library coverage.

#### Query conventions — different from the canon DB

- **FTS is case- and diacritic-insensitive.** `nibbāna`, `nibbana`, and `Nibbana` return identical results. Use ASCII for consistency; do not waste a second round trying the diacritic form.
- **Do NOT apply Pāḷi stem truncation here.** The stem-truncation rule applies to the canon SQLite only. In the library folders FTS, truncated stems match compound tokens (`jhān'aṅga`), HTML entities (`nibban&agrave;na`), and abbreviations — not the full word. Use the complete ASCII Pāḷi term: `satipatthana` not `satipaṭṭhān`; `paticcasamuppada` not `paṭiccasamuppād`.
- **Multi-word English queries work as implicit AND.** `"four foundations of mindfulness"`, `meditation retreat laypeople`, `dependent origination` all return precise results. Combine Pāḷi and English when a concept has both: `nibbana liberation`.
- **Extraction is a build-time concern, not a query-time concern.** All formats (PDF, EPUB, MOBI, DOC, etc.) are extracted into the FTS index during `library-folders-refresh`. A hit with `extraction_status: "ok"` has its full text in the index — use the FTS snippet. If `extraction_status` is not `"ok"`, that is a refresh gap, not something to fix at query time; note it in Critical Gaps.

**Tag vocabulary clusters.** The vocab is fragmented — there is no single canonical form for many concepts. Always consider the cluster, not just the first name that comes to mind.

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

**Author naming conventions (strip the title).** The library mixes many
honorific patterns: "Bhikkhu X" (58 entries), "X Bhikkhu" (25), "Ajahn X"
(38), "X Sayadaw" (22), "Ven. X" (98), "Dr. X" (56). Top authors: Piya Tan
(1,293), Bhikkhu Anālayo (410), Vipassana Research Institute (249), Pali
Text Society (114), Anandajoti Bhikkhu (104), Bhikkhu Bodhi (79),
Thanissaro Bhikkhu (76), Ajahn Brahmavamso (58), Ajahn Chah (49), Mahasi
Sayadaw (45), Bhikkhu Sujato (31), Nyanaponika Thera (28).

Search the distinguishing element, not the title — e.g. search `"Analayo"`, not `"Bhikkhu Analayo"`. Case and diacritics are handled automatically.

**Search ladder — descend when hits are thin.** Don't give up after one
search returning zero:

1. **Tag/author phrase.** `search-library-folders "Bhikkhu Bodhi nibbana"` — FTS5 ranks author+tag prefix text highly.
2. **Free-text phrase.** `search-library-folders "jhana absorption"`.
3. **Widen via synonym tag cluster** from the table above. Try related tag terms as free-text.
4. **Known-author search.** `search-library-folders "Analayo"` or `search-library-folders "Bhikkhu Bodhi"`.

If all rungs return nothing, the topic is genuinely absent from the
index — note it as a gap in *Open Threads*, do not invent a citation.

**The library folders index must always be queried.** Never skip it because other sources returned results. What to do with the results is the agent's judgment; the search itself is mandatory.

```bash
uv run tools/research_sources.py search-library-folders "<term>" --limit 20
```

Exact byte duplicates and identical normalized extracted text are already
collapsed in default search results; use `--include-duplicates` only when you
need to inspect every copy. A hit's `possible_duplicate_of` entries are weak
filename-based same-book hints for judgment, not proof and not grounds to
double-count evidence. If `source_available` is false, treat the hit as an
access gap for quotation/verification, not as no evidence: the index matched,
but the original source tree is unavailable.

→ **Phase 3 exit:** `scratch-gate 3`.

### Phase 3b — Sanskrit source search

**Skip this phase** unless angle 7 was marked applicable in Phase 1, or unless `VICAYA_GRETIL_PATH` is configured (check with `grep '^VICAYA_GRETIL_PATH=' .env` — the variable is not set in your shell).

**On a thematic run, the gate auto-skips but the work does not.** `scratch-gate 3b` is written automatically for thematic runs — this only means the gate won't block Phase 4; it does not mean the Sanskrit search can be omitted. If angle 7 is applicable, run `search-sanskrit` and log the hits before moving on.

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

→ **Phase 3b exit:** `scratch-gate 3b`.

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

→ **Phase 4 exit:** `scratch-gate 4`. For each web fetch, run `scratch-log 4 web <url> --summary "<one line>"` since `WebFetch` isn't a helper subcommand and won't auto-log.

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

→ **Phase 4b exit:** `scratch-gate 4b`.

### Phase 4c — WisdomLib

**This phase is mandatory for Indological runs — skip it only when the question has no Sanskrit, Pāḷi, or Indian-tradition terms.** (Examples of legitimate skips: a question on Christian mysticism, grief psychology, or Western philosophy.) WisdomLib is a comprehensive encyclopaedia of Indian religion, philosophy, and culture, covering Buddhist (Theravāda, Mahāyāna, Tibetan), Hindu (Nyāya, Vaiśeṣika, Yoga, Vedānta, Ayurveda, and others), and Jain traditions. It is the most reliable single-site source for precise definitions of technical Sanskrit and Pāḷi terms.

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

→ **Phase 4c exit:** `scratch-gate 4c`. WisdomLib fetches go via `WebFetch`, so log each one with `scratch-log 4c wisdomlib <url> --summary "<term + tradition>"`.

### Phase 5 — Synthesis

**Phase 5 entry gate:** run `uv run tools/research_sources.py scratch-verify`. If it exits non-zero, the output names the missing phase gate and its expected evidence — or a `content_issue` for a phase that was gated but left empty or stubbed with placeholder text. Backfill that work first, then re-run verify. Do not draft until verify exits 0.

**Read the scratch file before drafting.** Run `cat "$SCRATCH"` to recover the full list of findings from all prior phases. This is the compaction rescue step — if your context was compressed, everything you found is still in that file.

Draft the answer in your working notes. Cite as you go — never make a claim without a reference.

**Before drafting, read the "Pāḷi/English presentation" rules in the Style notes section.** Those rules govern how every Pāḷi quote and every inline Pāḷi term is rendered in the final vault note. Apply them from the first draft so you don't have to retrofit on the final pass.

**Source completeness check before you write.** Review your perspective map from Phase 1. For every named position, ask: do I have the canon passages that establish it, a secondary source that analyses it, and a web or talk source where the user could learn more? If any position is thin on sources, loop back to Phases 2–4 before synthesising. More prose does not fix missing sources — only more searching does.

**Angle coverage check.** Review the angle triage from Phase 1. For every angle marked *applicable*, ask: have I cited at least one source from that angle? If an applicable angle has zero citations, either loop back and search it, or downgrade it to *not applicable* with an honest reason for the `## Angles Not Pursued` table. Silent omission of a triaged angle is not acceptable.

**⚠️ IRON RULE — Devil's Advocate pass before drafting.** After the source and angle checks, answer each question below in the scratchpad before writing a single sentence of the Findings section. Brief answers are fine; the point is to surface problems while there is still time to fix them, not to generate prose.

1. **Citation balance.** For each position in the perspective map — do I have sources that *support* it AND sources that *challenge or complicate* it? If one position is supported by 6 canon hits and another by 1, is that imbalance accurate scholarship or search bias?
2. **Suppressed evidence.** Are there canon hits or library sources in the scratchpad that I was not planning to cite? For each: why not? If the honest answer is "it complicates my framing," the source goes in, not out.
3. **Alternative readings.** For the most important sutta passage I plan to quote — what does the commentarial tradition say about it, and what does at least one modern scholar who disagrees with that reading say? Am I collapsing a live interpretive dispute into a single reading? Where the tradition relies on a legitimation narrative (a *nidāna* / origin-story), is it internally consistent, or are there competing versions whose seams are themselves evidence?
4. **Strongest opposing voice.** What would the most credible scholar who holds the *opposing* view say is wrong with my synthesis? If I cannot name that argument, I have not understood the debate well enough to write about it.
5. **Evidence tier of load-bearing claims.** Is the central claim of the Findings section supported by T1 (canon mūla) or T2 (commentary) evidence, or does it ultimately rest on a modern teacher's talk or a secondary source? If the latter, the Findings prose must reflect that epistemic status.

Append answers to the scratchpad under `## Devil's Advocate`. Then draft.

**Use all relevant evidence.** If you collected 15 canon hits and 6 library sources, all of them go in the note — not a representative sample. Drop a hit only if it is a verbatim duplicate of one already quoted. Paraphrase only when the full text is unavailable. Prefer blockquotes (Rule P1) over inline summaries everywhere. **Evidence Fidelity Rule:** Every footnoted source must also appear as a full blockquote in its Evidence section; a footnote without its accompanying blockquote is a defect.

**Track every rejection.** Each time you decide not to use a source — whether a canon paragraph, a library book, a web page, or a YouTube video — note it immediately with a one-line reason. These go into `## Sources Investigated, Not Used` in the final note. Common reasons: duplicate, metadata-only (no content to quote), URL blocked, auto-captions too degraded to paraphrase, out of scope, wrong sutta. Do not discard sources silently.

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

**Deferred-draft handoff (very large dossiers).** When the dossier is too large
to draft in the remaining context, do not gate Phase 5 on a rushed draft.
Instead: (1) record a compact synthesis plan via
`scratch-log 5 synthesis-plan … --summary "PHASE 5 SYNTHESIS PLAN: <outline,
section order, source allocation>"`; (2) write whatever draft payload exists to
`data/scratch/<slug>.phase5-draft.md` and log that path in the main scratch;
(3) stop and hand off — the next pass resumes from the plan and draft file,
completes the draft, and only then runs `scratch-gate 5`. Never leave a
handoff-critical draft only in model context or under `temp/`.

→ **Phase 5 exit:** `scratch-gate 5` once the draft is in scratch and the Devil's Advocate answers are recorded.

### Phase 6 — Second-pass review (cross-check)

Pipe your synthesis to a second model for an independent review:

Write the prompt to scratch-local files, then pipe it in (avoids all shell quoting hazards):

```bash
SCRATCH="$(uv run tools/research_sources.py scratch-which)"
CROSS_CHECK_PROMPT="${SCRATCH%.md}.cross-check-prompt.txt"
CROSS_CHECK_REVIEW="${SCRATCH%.md}.cross-check-review.txt"

cat > "$CROSS_CHECK_PROMPT" <<'EOF'
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

uv run tools/research_sources.py cross-check < "$CROSS_CHECK_PROMPT" > "$CROSS_CHECK_REVIEW"
uv run tools/research_sources.py scratch-log 6 cross-check-review "$CROSS_CHECK_REVIEW" \
  --summary "Raw Phase 6 cross-check output saved in the scratch-local review file and integrated before the Phase 6 gate."
```

**Run this in the background from the first attempt** (e.g. `run_in_background: true` on the Bash call), not only after a foreground timeout. The helper's own `--timeout` defaults to 180s, longer than the Bash tool's ~120s foreground cap — on a long synthesis, opencode/agy latency alone silently truncates the call before `$CROSS_CHECK_REVIEW` is written, even though the underlying model request would have succeeded.

The `cross-check` helper tries each `app:model` entry in `VICAYA_CROSS_CHECK_CHAIN` (env) in order via subprocess (`opencode run -m <model>` or `agy --print ... --model <model>`), returns the first one that succeeds, and falls back to the `# SELF_REVIEW:` sentinel if the chain is empty or every entry fails. **If the scratch-local review file begins with `# SELF_REVIEW:`**, no chain entry succeeded (or the chain was empty). In that case, run the embedded five-point checklist on your own synthesis: read each numbered item, audit your synthesis against it, and apply fixes the same way you would for an external review. Do not write anything in the note acknowledging the self-review fallback; it is still subject to the IRON RULE below. The terminal report in Phase 7 records `cross-check: self-review` instead of a model name.

**Citation pre-annotation.** Every sutta reference in the helper's output arrives already labelled `[VERIFIED]`, `[REJECTED — not in sutta_info]`, or `[UNVERIFIABLE — …]` (existence check against `dpd.db sutta_info`). The label is existence-only: `[VERIFIED]` means the citation is a real sutta, **not** that the reviewer's content claim about it is correct. Pāḷi-quote misreads (e.g. `asantasanto` confused with `asanta`) and conceptual conflations are *not* caught by this — those still need scholarly judgement during integration. **Drop every `[REJECTED]` claim entirely; do not paraphrase, do not retain.** A `[REJECTED]` tag anywhere in the final vault note will cause `scratch-gate 7` to refuse, so they must be excised cleanly.

The verifier understands range-stored books (Dhp verses, AN ones/twos, peyyāla blocks resolve by containment), hyphenated ranges (`SN48.9-10` verifies via its endpoints), and the Thag/Thig/Kp code aliases. Global verse numbers in Suttanipāta/Theragāthā/Therīgāthā (`Sn 925`, `Thag 591`) have no per-verse rows in `sutta_info` and are labelled `[UNVERIFIABLE — …]`: this is **not** evidence of fabrication. If you pulled the verse verbatim from the canon DB, keep it and cite by chapter.sutta (`Snp 4.14`, `Thag 16.1`) or CST table+para; if it came only from the reviewer, substantiate it against the canon DB before integrating.

**Silently integrate** anything substantive that is `[VERIFIED]` (or a content claim with no citation that you can substantiate elsewhere). If the review surfaces:
- A missed school / lineage / teacher → research the primary or secondary sources for it and incorporate with proper citations (canon, library, web). If you can't substantiate it, drop it.
- A factual correction → verify against a primary or secondary source you can cite, then incorporate.
- An alternative interpretation → add it as a position in the note, cited to whoever actually holds it.

**⚠️ IRON RULE — Never write that the review surfaced something.** No "Gemini noted", no attribution to any AI model, no meta-commentary about how the note was produced. If you incorporate a school the user might not have asked about, that's fine — it stands on its own academic merit, cited properly.

If the review surfaces nothing substantive, move on without any acknowledgement in the note.

→ **Phase 6 exit:** `scratch-gate 6` once the cross-check raw output and any integrations are recorded.

### Phase 7 — Write the note

**⚠️ MANDATORY RULE: EVERY footnote must have an accompanying blockquote.** Every footnoted source must also appear as a full blockquote in its Evidence section; a footnote without its accompanying blockquote is a defect.

**The vault only receives complete notes.** The scratch dossier in `data/scratch/`
holds the in-progress work. Phase 7 is the *finalization and transfer* step: take
the comprehensive dossier, curate the strongest evidence into the structured note
template below, and write the result to `$VICAYA_VAULT_PATH/Vicaya/` only when it
is complete. Never write a partial or draft note to the vault.

**Re-read the format requirements before drafting.** At Phase 7 start, re-read
this entire section — the note template, the frontmatter rules, and the
Pāḷi/English presentation rules in Style notes — *before* writing the first
line of the draft. Drafting from memory of the template has produced notes in
the wrong shape that needed a full rewrite before validation.

**Caller-supplied fixed formats (e.g. the "What the suttas say about X"
series).** When the user's command supplies a fixed note format, do not choose
between that format and the template below — use the established hybrid. This
paragraph is the spec; do not reverse-engineer the shape from sibling notes.

- Keep the standard frontmatter, `## Question`, and a short `## Findings`
  overview (a few orienting paragraphs). The validator hard-requires all
  three; every series run that omitted them failed validation and had to
  retrofit them.
- Place the caller's sections verbatim beneath the Findings overview (for the
  series: `## What the EBTs say about X` / `## What the EBTs don't say about
  X`, each claim backed by block-quoted Pāḷi + English).
- Omit `## Canon Evidence (T1)` when the quotes live inside the caller's
  sections — the validator recognizes series-body headings and does not warn.
- Keep the standard tail: `## Sources Investigated, Not Used`,
  `## Critical Gaps`, `## Bibliography`, and `## Angles Not Pursued` when
  applicable.

**Comparative-religion questions (non-Buddhist tradition as primary subject).** When the research question centres on a tradition with no canon-DB primary text (e.g. Christianity, Islam, Judaism, Stoicism), replace `## Canon Evidence (T1)` with a tradition-appropriate heading — `## Biblical Evidence (T1)`, `## Quranic Evidence (T1)`, `## Stoic Sources (T1)`, etc. The validator accepts any `## * Evidence (T1)` heading and does not warn. Use the same blockquote + citation discipline as the standard Canon Evidence section: verbatim primary-text quotes with source attribution, not paraphrase. The Buddhist canon evidence (if any parallel is relevant) goes in a separate `## Canon Evidence (T1)` section alongside.

**Before writing, run this source-coverage check:**
- Is every position from the perspective map represented by at least one block-quoted canon passage?
- Is every *applicable* angle from the Phase 1 triage represented by at least one citation, and is every *non-applicable* angle logged in `## Angles Not Pursued` with a one-line reason?
- Are all pertinent canon hits in the Canon Evidence (T1) section — not a curated sample?
- Have I searched the library folders for every plausible tag/author cluster, not just the first match?
- Have I handled `possible_duplicate_of` / `source_available` correctly in library folders results?
- Have I pulled transcripts for the most relevant Dhamma talks, not just noted the video titles?
- Have I fetched and read the most promising web sources, not just linked to search results?
- Is the draft approaching ~12 pages (~3,500 words)? If not, the answer is almost always: I have not surfaced enough sources.

Render the final markdown. Use this template as a structural guide — expand every section to the depth the evidence warrants:

```markdown
---
date: YYYY-MM-DD
topic: <question_polished or concise neutral topic derived from it>
tool: "https://github.com/bdhrs/vicaya"
agent: "<Model family + version> (<host app>)"  # replace with your runtime identity — see Rule F5
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
<question_polished>

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
*Researched by [Vicaya](https://github.com/bdhrs/vicaya) using <Model family + version> (<host app>) on YYYY-MM-DD HH:MM.*

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

The `book_id` must come from the `document_id` in a library folders hit — never invent an ID.

**Rule F5 — `agent` field and footer line: self-identify accurately.**

The note records which model produced it, in two places:

1. The `agent` frontmatter field — quoted string, format `"<Family Version> (<host app>)"`.
2. A single italic footer line at the very end of the note: `*Researched by [Vicaya](https://github.com/bdhrs/vicaya) using <Family Version> (<host app>) on YYYY-MM-DD HH:MM.*`

The parenthetical names the **host app/harness you are running inside** (e.g. Claude Code,
Antigravity, Codex CLI, agy) — never the raw model slug. A model slug like
`gemini-3.5-flash` is pure duplication when the family+version is already spelled out
("Gemini 3.5 Flash"); the host app is the information actually worth recording, since the
same model family can run under different orchestrating apps.

Read your own model identity and host app from your **system prompt** or **environment
context** — do **not** guess from training data, do **not** invent a version number or app
name, and **never copy the agent string from the template example above or from a prior
vault note**. Template examples are illustrations, not your identity. If you genuinely
cannot determine your identity, write `unknown agent` in both places rather than fabricating.

To find your identity: read your system prompt for statements like "You are powered by the model
named X" or "You are Claude, an AI assistant made by Anthropic." Use exactly what it reports.

Examples (do not copy — look up your own):

- Claude Code: `"Claude Opus 4.7 (Claude Code)"`, `"Claude Sonnet 4.6 (Claude Code)"`.
- Gemini running in Antigravity: `"Gemini 3.5 Flash (Antigravity)"` — not `(gemini-3.5-flash)`.
- agy: `"Gemini 2.5 Pro (agy)"` or whatever the CLI reports as its own host name.
- Codex / GPT-based: `"GPT-5.4 (Codex CLI)"` or equivalent.
- Other: `"<Model name as the runtime reports it> (<host app as the runtime reports it>)"`.

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
agent: "<Model family + version> (<host app>)"  # replace with your runtime identity — see Rule F5
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

**Multi-day runs keep the start date.** A run that crosses midnight or resumes
on a later day carries the date the run began (the dossier's Phase 0 date) in
the filename, the frontmatter `date`, and the footer — consistent with the
retrieval dates already cited in the note. Do not let a late completion shift
the date.

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

After writing the note — whether via the Obsidian CLI or the disk fallback — validate
the final note shape and generate a PDF copy.

```bash
uv run scripts/validate_note.py "Vicaya/${TODAY} - ${SLUG}.md"
```

**Read the validator's output, including warnings and errors.** An `error`-severity line
(e.g. `under-quoted-evidence` or `missing-canon-ref`) fails the command. A `warning` still
names a real defect in the note you just wrote. Before continuing: edit the note to fix
every issue the validator reports, then re-run `validate_note.py` to confirm the output is
clean. Only once it prints no warnings or errors, proceed:

```bash
uv run scripts/generate_note_pdf.py "Vicaya/${TODAY} - ${SLUG}.md"
```

`generate_note_pdf.py` reads `VICAYA_PDF_PATH` from `.env`. If unset or empty, it exits
successfully with a skip message. Include the PDF path in the Section 1 run summary if
generation succeeded.

Then record both paths in the scratch header — this sets the file the Phase 7
`[REJECTED]` hard gate scans. Never hand-edit the `**Vault note:**` header:

```bash
uv run tools/research_sources.py scratch-set-note "Vicaya/${TODAY} - ${SLUG}.md" \
  --pdf "<pdf-path, or 'skipped'>"
```

Vault-relative paths resolve against `VICAYA_VAULT_PATH`; absolute paths work
too. The command refuses if the note file does not exist, so a typo cannot
silently disarm the gate.

### Library coverage check (advisory)

After `scratch-set-note`, run:

```bash
uv run tools/research_sources.py scratch-check-coverage
```

This flags library-folder documents that were gathered in any phase but
appear nowhere in the note — not cited, and not logged in `## Sources
Investigated, Not Used` either. It is a narrow, targeted check (re-scoped
from a broader hypothesis in 2026-07-05 triage, see TODO #64): an audit of 6
recent notes found canon and web coverage already self-curated well through
the rejection table, but library documents can slip through both the
citations and the rejection table silently. It is advisory, not a hard
gate — a nonzero exit just means review the listed documents and either cite
them or add a one-line reason to the rejection table.

The check matches `calibre-<document_id>` / `Calibre #<document_id>` (the
two forms already used in notes) anywhere in the note text. **When logging a
library source in `## Sources Investigated, Not Used`, include its calibre
id** (e.g. `Author, Title (Calibre #2365)`) so the rejection is machine-
checkable, not just a title a future pass can't verify against.

### Self-audit (required before the gate)

After `scratch-set-note` and before `scratch-gate 7`, record the failure
checklist — the gate refuses until it is in the dossier:

```bash
uv run tools/research_sources.py scratch-self-audit   # prints the questions
uv run tools/research_sources.py scratch-self-audit \
  --answer "<a1>" --answer "<a2>" --answer "<a3>" \
  --answer "<a4>" --answer "<a5>" --answer "<a6>"
```

The six questions target the recurring end-of-run failure modes: easy-source
bias, dropped user seeds, early stopping, artifact-vs-completion confusion,
stale instructions followed mechanically, and cross-check corrections applied
without mūla verification. Answer honestly in one line each — naming a problem
here means fixing the note *before* gating, which is the entire point. "None"
is a valid answer only after actually checking.

### GitHub note sync (pre-approved)

After the note is written, validated, PDF generated, and `scratch-gate 7` passes, run:

```bash
uv run scripts/sync_notes.py "Vicaya/${TODAY} - ${SLUG}.md"
```

`scripts/sync_notes.py` is the pre-approved publishing script for the notes repo
only. It loads `.env`, targets `$VICAYA_VAULT_PATH/Vicaya/`, may pull, stage the
named note, commit it if needed, and push it to `bdhrs/vicaya-notes`.

Do not ask a yes/no approval question for this step. Do not run arbitrary
`git`, publishing, deployment, sync, delete, or overwrite commands outside this
approved script path.

A sync failure is never fatal — the note is already saved to the vault.

→ **Phase 7 exit:** after validation/PDF generation, run `scratch-set-note` (records the saved note + PDF paths), then `scratch-check-coverage` (advisory — review any flagged library documents), then `scratch-self-audit` with answers (the gate refuses without it), then `scratch-gate 7`, then `uv run scripts/sync_notes.py "Vicaya/${TODAY} - ${SLUG}.md"`; after writing the reflection, run `uv run scripts/sync_run_report.py`. The run is not complete until the gate passes and both sync commands have been attempted — the gate confirms the vault path and PDF path are recorded in the dossier, note sync publishes the saved note, and run-report sync publishes the latest `runs/*.md` report. `scripts/sync_run_report.py` is a pre-approved run-report publishing script and may pull, commit, and push Vicaya run reports in this project repo. New or materially modified scripts are not automatically pre-approved for git, publishing, deployment, sync, delete, or overwrite operations.

After both sync commands have been attempted, clean only this run's disposable repo-local temp directory; never remove `data/scratch/` or scratch-local draft/review files:

```bash
SCRATCH="$(uv run tools/research_sources.py scratch-which)"
RUN_TEMP="temp/$(basename "${SCRATCH%.md}")"
case "$RUN_TEMP" in
  temp/*)
    if [ -d "$RUN_TEMP" ]; then
      find "$RUN_TEMP" -type f -delete
      find "$RUN_TEMP" -depth -type d -empty -delete
    fi
    ;;
  *) echo "Refusing to remove unexpected temp path: $RUN_TEMP" ;;
esac
```

## Final report to the user

The terminal report has two distinct sections. Keep them separate — conflating them was a recurring bug in prior runs.

### Section 1 — Run summary

- Path of the saved note.
- Hit counts: canon refs, library books, web sources cited.
- One sentence: the headline finding.
- Optionally one line per *content* integration from the cross-check, framed as content not process. **Example (good):** `Added MN 101 Devadahasutta as a load-bearing reference — it refutes the strict-determinist reading.` **Example (bad — never write this):** `Gemini noted MN 101 was missing.`

### Section 2 — Improvement suggestions

Suggestions for future `/vicaya-improve` runs only — **never direct edits to `SKILL.md`, anything in `tools/`, or anything in `scripts/`**. One line each, prefixed with `Suggest:`. **If you have no suggestions, omit this section entirely** — don't pad it with content integrations (those go in Section 1).

### Section 3 — Distillation reminder (conditional)

Count the files in `runs/`. If there are 10 or more, print one line:

> **Skill distillation due** — `runs/` has <N> reflections. Run `/vicaya-improve` to batch-process them and promote recurring lessons into SKILL.md.

If fewer than 10, omit this section entirely.

## When something fails

- **Helper raises `FileNotFoundError`**: a path is wrong — tell the user, don't fudge.
- **`lookup-book` raises `RuntimeError: cst_book_translator not found`**: the dpd-db repo isn't at an expected path on this machine. Fall back to `resolve-citation` for passage and book names, plus direct sqlite against `$VICAYA_CANON_DB` for table↔book mapping.
- **`uv run` fails with a cache permission error (`~/.cache/uv` denied — macOS sandbox)**: the `.venv` is cold or stale. On a synced env `uv run` never touches the global cache (no git deps in `uv.lock`), so this error means the env needs building — ask the user to run `uv sync` once outside the sandbox, then continue (`uv run --no-sync` skips the sync check on a known-good env). Do **not** export `UV_CACHE_DIR` as a workaround: it re-downloads every package into the repo, and the changed invocation environment it rides along with alters the process key that per-run scratch state is bound to — two runs lost their active scratch this way. If you ever must change the invocation environment mid-run, pin `VICAYA_SCRATCH` explicitly first.
- **Canon search returns 0 hits**: try lang="any" and/or broader book scope before giving up.
- **Library folders returns 0 hits**: first distinguish empty from error — `library-folders-check` exits 1 when the index path is missing or unreadable. If the index is reachable and truly empty: try fewer/looser terms; check `data/calibre_tags.csv` for the right tag vocabulary; try an author's surname as the query. Extract content directly with `pdftotext` or `ebook-convert` on known book files when needed.
- **`search-library-folders` exits 1 with `error: search timed out … too broad`**: a stopword or one word of an unquoted multi-word phrase forced a full scan of the index. This is the query aborting cleanly (default 20s budget via `--timeout`), not a hang — narrow the query (drop the stopword, add a more specific term, quote an exact phrase) and retry; don't raise `--timeout` as the first move.
- **`WebSearch` returns 403 on every query**: the search backend is blocked or mis-credentialed on this machine (seen on macOS) — don't keep retrying. Fall back to `WebFetch` on directly constructed URLs (the mirror patterns in Phase 4a); for academic papers use the arXiv search endpoint (`http://export.arxiv.org/api/query?search_query=all:"<terms>"`) — arXiv IDs cannot be guessed.
- **`cross-check` returns `# SELF_REVIEW:`**: every configured chain entry failed (or `VICAYA_CROSS_CHECK_CHAIN` is unset/blank). Run the embedded checklist on your own synthesis as described in Phase 6; do not retry the helper. Common root causes: the chain var is empty, `opencode`/`agy` aren't on `$PATH`, or neither app has valid provider credentials configured.
- **A backgrounded sub-agent or external-CLI dispatch never delivers its completion notification** (seen after a session/process restart): do not keep waiting on the notification. Check the task's output file directly — the phase's work and auto-logging may already be complete even though the wait mechanism never fired. Confirm ground truth via `scratch-resume`/`scratch-which` and the actual gate state before deciding whether to re-run the phase.
- **`scratch-gate 7` shows passed but the vault note is missing**: a prior
  invocation gated before the vault write completed. Do not treat the run as
  done and do not try to re-gate — write the complete note to the vault now,
  log the write with `scratch-log 7 …`, and continue with validation, PDF, and
  sync. The gate's `[REJECTED]`-scan is the substantive constraint, not its
  timestamp.
- **Obsidian create fails**: print the rendered markdown to the terminal so the user can save it manually.
- **PDF URL — WebFetch returns garbled or empty content**: WebFetch cannot decode PDF binary. Instead, save the file under this run's repo-local temp directory and extract with `pdftotext`:
  ```bash
  SCRATCH="$(uv run tools/research_sources.py scratch-which)"
  RUN_TEMP="temp/$(basename "${SCRATCH%.md}")"
  mkdir -p "$RUN_TEMP" && curl -sL "<url>" -o "$RUN_TEMP/source.pdf" && pdftotext "$RUN_TEMP/source.pdf" -
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
- **Target depth: ~12 pages (~3,500 words), measured by source coverage.** This is the length at which the user has reported finding the notes most useful. Reach it by surfacing more sources, not by writing more prose per source. If a draft is short, the right fix is: did I search for all relevant canon passages? did I exhaust the library folders index? did I pull transcripts from the most relevant Dhamma talks? — not: did I write enough sentences about each position?
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
question_original: <verbatim user request, one line>
question_polished: <clean research question used in the final note>
note_path: <path of the saved research note>
duration_min: <approximate>
---

## Retrospective
- [POSITIVE] Evidence: <what worked well in this run, or "nothing">. Cause: <why it worked>. Fix: <what to preserve, or "none">. Scope: <local/global>.
- [WORKFLOW] Evidence: <friction, wasted effort, unclear sequencing, or "nothing">. Cause: <likely cause>. Fix: <proposed change, or "none">. Scope: <local/global>.
- [CONFUSION] Evidence: <misunderstanding, bad inference, or "nothing">. Cause: <likely cause>. Fix: <proposed change, or "none">. Scope: <local/global>.
- [BEHAVIOR] Evidence: <missed required step, risky action, rule violation, or "nothing">. Cause: <likely cause>. Fix: <proposed change, or "none">. Scope: <local/global>.
- [BUG] Evidence: <script/tool failure or unclear output, or "nothing">. Cause: <likely cause>. Fix: <proposed change, or "none">. Scope: <local/global>.
- [DOC] Evidence: <instruction that should be clarified, or "nothing">. Cause: <likely cause>. Fix: <proposed documentation change, or "none">. Scope: <local/global>.

## Improvement suggestions
- <one bullet per suggestion for `/vicaya-improve` to act on, prefixed with `Suggest:`, or "nothing" — never direct edits to SKILL.md, tools/, or scripts/>

## Channel tuning
- Promote to trusted: <Channel — one-line reason this run, or "none">
- Demote to excluded: <Channel — one-line reason this run, or "none">
- New probationary channels seen: <comma-separated list, or "none">
```

Be terse. Three bullets per retrospective tag max. If a tag has no item, write one
`[TAG] ... "nothing"` bullet — don't delete the tag. These files are the input to
periodic skill-tuning passes.

### Step 1b — Publish the run report

After writing the reflection, run:

```bash
uv run scripts/sync_run_report.py
```

This publishes the latest `runs/*.md` report. The run is not complete until this command has been run.

After writing the reflection, apply any concrete `Channel tuning` decisions directly to
`data/youtube_channels.md`. Promotions and demotions are how the channel allowlist gets
richer over time; without this step the file goes stale.

### Step 2 — Write improvement suggestions to the run report only

**Never edit `SKILL.md` or any file in `tools/` or `scripts/` during a vicaya run.** Skill and script edits are handled exclusively by `/vicaya-improve`, which batches run reflections and applies changes deliberately.

If reflection turned up a fix — one-line or larger — write it as a clearly marked suggestion in the run report under `## Improvement suggestions`. Use the format:

```
## Improvement suggestions
- Suggest: <concise description of what to change and why>
```

These suggestions will be picked up by `/vicaya-improve` in the next improvement cycle.

### Step 3 — Report skill suggestions in Section 2 of the final report

See "Final report to the user" above. **Content integrations** (e.g. "added MN 101")
belong in Section 1, not here. **Improvement suggestions** (e.g. "document `CanonHit` fields") go
in Section 2 as `Suggest:` lines — never `Improved:` lines, since no edits are made during a run.

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
