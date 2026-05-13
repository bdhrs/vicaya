---
name: vicaya
description: Run a structured Pāḷi/Buddhist research session across the user's local sources (Obsidian vault, CST canon SQLite, Calibre library) plus web search, cross-checked with Gemini, and write a single linked note into the Obsidian vault. Invoke when the user types /vicaya <question> or asks for "research on X", "look into X across my sources", "find what the suttas say about X", or any multi-source research request that should land as a permanent vault note.
---

# Research skill

Run a multi-phase research session across the user's local + web sources and write a single structured note into their Obsidian vault.

## Hard rules (read first — these are not preferences)

These rules apply to every run, by every agent. They are part of the skill, not stored in any agent's private memory.

1. **No AI / model attribution in the research note.** Never write "Gemini noted", "Claude found", "the AI suggested", "added by cross-check", etc. The note must read like scholarship — information and sources are what matter, not the process of producing them. If a second-pass review surfaces material, integrate it silently with proper citations to the underlying primary or secondary source.
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

## Setup — paths and tools

Hard-coded for this machine. If a path is missing or a tool isn't installed, stop and tell the user; don't guess.

All user-specific paths come from the project's `.env` file (see `.env.example` at the repo root). The helper module resolves them on import. Agents do not hard-code paths; use the helpers and CLI.

- Vault: `$VICAYA_VAULT_PATH` (Obsidian CLI vault name: `$VICAYA_VAULT_NAME`)
- Output folder in vault: `Research/`
- Helper module: `<repo>/tools/research_sources.py`
- Canon db: read-only SQLite at the path baked into the helper module.
- Calibre library: path baked into the helper module. **Note: FTS indexing is in progress (14k books, takes days). Until then, Calibre search is metadata-only. The helper falls back automatically — don't try to force FTS.**
- `gemini` CLI on PATH for cross-check.
- **Book code → source XML map**: `/home/bodhirasa/MyFiles/3_Active/dpd-db/tools/pali_text_files.py` maps every canon book code (e.g. `s0201m_mul`) to its source XML file in the DPD database. Consult this when you need to know which raw XML file a given book code corresponds to, or when debugging why a search returns no results for a book you expect to exist.

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
| `gemini-cross-check` | `--timeout N`; **prompt on stdin** | Pipe the synthesis in; avoids quoting hell |

Parse the JSON with `jq` or read it as a file. Only fall back to `uv run python -c "..."` if you genuinely need to combine helpers in one step — and if so, write a short `.py` script to a temp path and run that, rather than a heredoc.

## Helper return shapes (read before calling)

Every helper returns dataclasses serialised to JSON by the CLI. Field names are exact — guessing them has caused crashes in prior runs.

- **VaultHit**: `path` (str), `snippet` (str), `line` (int | null)
- **CanonHit**: `book_code` (str, e.g. `s0201m_mul`), `paranum` (str), `pali` (str), `english` (str), `chinese` (str). **No `snippet` field** — quote from `pali` / `english` directly.
- **Citation**: `machine` (e.g. `s0201m_mul:23`), `human` (e.g. `MN60 Apaṇṇakasuttaṃ para 97`), `pitaka`, `text_type`, `paranum`.
- **CalibreHit**: `book_id` (int), `title` (str), `authors` (str), `tags` (list[str]), `location` (str), `snippet` (str — populated only when FTS is ready).
- **YouTubeHit**: `video_id` (str), `title` (str), `channel` (str), `channel_id` (str), `duration` (float | null, seconds), `url` (str), `tier` (str — `trusted` | `probationary`; `excluded` never appears here, those are filtered out).
- **YouTubeTranscript**: `video_id` (str), `lang` (str, e.g. `"en"`), `is_auto` (bool — **true means Pāḷi terms are unreliable; paraphrase, don't quote**), `segments` (list of `{start, duration, text}`), `fetched` (ISO date).

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

## The seven phases

Run these in order. Print a one-line status update before each phase so the user can follow along in their terminal.

### Phase 1 — Vault context

Search the existing vault for prior notes related to the topic. The user has been writing in this vault for years; new research must build on, not duplicate, what's there.

```bash
uv run tools/research_sources.py search-vault "<key terms>" --limit 20
```

Pull up to 4 search variations (Pāḷi term, English gloss, related concept). Summarise the top hits in your own working notes — you'll cite the most relevant ones in the final note via `[[wiki-links]]`.

**Perspective map.** Before moving to Phase 2, explicitly name the 2–5 competing positions or schools of thought the question touches. Examples: "Theravāda commentarial vs. Ñāṇavīra structural", "cessationist vs. realist readings of Nibbāna", "three-lives vs. momentary paṭiccasamuppāda". If the question is purely factual with no interpretive dispute, skip this step. Otherwise, tag subsequent evidence — canon hits, library sources, web sources — as supporting a named position. This ensures the final note covers all significant views, not just the first position the search surfaces.

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

```bash
uv run tools/research_sources.py search-canon "<Pāḷi term>" --books "s*_mul" --lang pali --limit 20
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

**Quote representatively.** Pull up to 20 of the most pertinent paragraphs — use as many as are genuinely relevant to give a full picture, not just the first few that match.

**Paragraph numbers are book-global.** The `paranum` in a `CanonHit` is a continuous index across the entire book file, not local to the sutta. Always run `resolve-citation` to confirm which sutta a paragraph belongs to before citing it (see Hard Rule 9).

### Phase 3 — Library search

The user's Calibre library is whole-library non-fiction (Buddhism, religion, psychology). The tag vocabulary is in `<repo>/data/calibre_tags.csv` (~2k tags).

Pick up to 3 tags relevant to the question (e.g. `Abhidhamma`, `Buddhism`, `Vipassana`, `Meditation`). Tag names are exact strings; matching is case- and diacritic-insensitive.

```bash
uv run tools/research_sources.py search-calibre "<term>" --tags Buddhism --limit 20
```

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

### Phase 4a — Web search

Use `WebSearch` (and `WebFetch` to read the most promising results). Use as many relevant sources as you can find, up to 20. Prefer:
- SuttaCentral (suttacentral.net) — primary translations + parallels
- Access to Insight (accesstoinsight.org) — older but solid
- Academic journals and respected scholars
- Avoid: blog spam, AI-generated content farms, low-quality summaries

### Phase 4b — YouTube search

YouTube hosts an enormous corpus of recorded Dhamma talks, sutta studies, and academic lectures. Mine it.

```bash
uv run tools/research_sources.py search-youtube "apannaka sutta MN 60" --limit 20
```

Each hit comes back with `tier ∈ {trusted, probationary}` (excluded channels are dropped server-side). Prefer trusted hits; treat probationary hits with appropriate skepticism. The allowlist lives at `data/youtube_channels.md` — promote/demote at the end of the run via the reflection template.

For the most promising videos (up to 20), pull the transcript:

```bash
uv run tools/research_sources.py fetch-transcript R0vhivplJuM
```

Transcripts are cached under `data/youtube_cache/<video_id>.json` — subsequent calls are instant. Each transcript records `is_auto` (true = YouTube's auto-generated captions; false = human-uploaded). **Auto-captions mishear Pāḷi** ("Suddhāso" → "saso", "Apaṇṇaka" → "apaka"). When `is_auto` is true, paraphrase and link to the timestamp — do not quote Pāḷi verbatim.

To locate the relevant moment in a long talk, scan `segments` for keywords (English glosses or the auto-caption form of the Pāḷi term) and cite the `start` timestamp.

### Phase 5 — Synthesis

Draft the answer in your working notes. Cite as you go — never make a claim without a reference.

**Before drafting, read the "Pāḷi/English presentation" rules in the Style notes section.** Those rules govern how every Pāḷi quote and every inline Pāḷi term is rendered in the final vault note. Apply them from the first draft so you don't have to retrofit on the final pass.

**Recursive citation check.** As you draft, watch for sources that are load-bearing — a teacher, text, or sutta that the argument depends on but that hasn't been searched yet. If you find one, pause and loop back to Phase 2 or 3 for that specific entity before continuing. Up to two loop-backs per run; don't spiral beyond that. If after the loop-back the source still can't be found, note the gap honestly in Open Threads.

Citation forms:

- Canon: `**MN60 Apaṇṇakasuttaṃ para 97** — "<pali quote>" / "<english>"`
- Library: `[[<Book Title>]] — <Author>: "<snippet>"` (omit snippet if metadata-only)
- Web: `[<page title>](<url>) — retrieved YYYY-MM-DD`
- Vault: `[[<Existing Note Title>]]`

### Phase 6 — Second-pass review (cross-check)

Pipe your synthesis to a second model for an independent review:

Write the prompt to a temp file, then pipe it in (avoids all shell quoting hazards):

```bash
cat > /tmp/cross_check_prompt.txt <<'EOF'
You are reviewing a research synthesis on a Pāḷi/Buddhist question.
Identify any factual errors, oversights, or alternative interpretations.
Be specific.

Question: <the question>

Synthesis:
<the synthesis>
EOF

uv run tools/research_sources.py gemini-cross-check < /tmp/cross_check_prompt.txt > /tmp/cross_check_review.txt
```

**Silently integrate** anything substantive. If the review surfaces:
- A missed school / lineage / teacher → research the primary or secondary sources for it and incorporate with proper citations (canon, library, web). If you can't substantiate it, drop it.
- A factual correction → verify against a primary or secondary source you can cite, then incorporate.
- An alternative interpretation → add it as a position in the note, cited to whoever actually holds it.

**Never write that the review surfaced something.** No "Gemini noted", no attribution to any AI model, no meta-commentary about how the note was produced. If you incorporate a school the user might not have asked about, that's fine — it stands on its own academic merit, cited properly.

If the review surfaces nothing substantive, move on without any acknowledgement in the note.

### Phase 7 — Write the note

Render the final markdown. Use this template:

```markdown
---
date: YYYY-MM-DD
topic: <one-line topic>
tags:
  - research
  - pali
canon_refs:
  - <human_ref>
  - ...
library_refs:
  - <book_id>: <title> — <author>
web_refs:
  - <url>
---

# <Topic title>

## Question
<the user's question, verbatim>

## Findings
<the synthesised answer, with inline citations>

## Canon Evidence
- **MN60 Apaṇṇakasuttaṃ para 97**
  - Pāḷi: "..."
  - English: "..."
- ...

## Library Evidence
- [[Book Title]] — Author Name
  - "snippet" (if FTS was on)

## Web Evidence
- [Source title](url) — retrieved YYYY-MM-DD
  - <brief gloss of what this source contributes>

## YouTube Evidence
- [Channel — Talk Title](https://youtu.be/<video_id>?t=<seconds>) — fetched YYYY-MM-DD (human captions | auto-captions; paraphrase)
  - <paraphrase or — only if `is_auto = false` — direct quote>

## Related Notes
- [[Existing vault note 1]]
- [[Existing vault note 2]]

## Open Threads
- <questions raised but not answered>
- <follow-up research worth doing>
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

**Rule F2 — `canon_refs` entries must come verbatim from `resolve-citation` output.
Never guess or infer a sutta number from a sutta name, or a name from a number.**

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

**Rule F3 — `web_refs` URL and annotation must refer to the same sutta/text.**

Write only the URL and the retrieval date. If you add an annotation, verify it matches
the URL. A URL pointing to `dn/dn.22.0.than.html` is DN22, *not* MN118:

```yaml
# WRONG — URL is DN22 but annotation says MN118
- https://accesstoinsight.org/tipitaka/dn/dn.22.0.than.html (MN118 ...) — retrieved 2026-05-12

# CORRECT
- https://accesstoinsight.org/tipitaka/dn/dn.22.0.than.html — retrieved 2026-05-12
```

**Rule F4 — `library_refs` use the integer `book_id` from Calibre, not a made-up number.**

Format: `<book_id>: <title> — <author>`. The `book_id` comes from the `CalibreHit.book_id`
field. Never invent an ID.

### Correct frontmatter example (reference this when writing)

```yaml
---
date: 2026-05-12
topic: "Ānāpānasati: Breath Meditation in the Nikāyas"
tags:
  - research
  - pali
  - meditation
canon_refs:
  - MN118 Ānāpānasatisuttaṃ para 977
  - SN54.1 Ekadhammosuttaṃ para 1
library_refs:
  - 223: On Meditation - Instructions from Talks by Ajaan Chah — Ajahn Chah
  - 1683: Buddhist Meditation and Depth Psychology — Douglas M. Burns
web_refs:
  - https://accesstoinsight.org/tipitaka/mn/mn.118.than.html — retrieved 2026-05-12
---
```

Write the note via the Obsidian CLI. Slugify the topic for the filename:

```bash
TODAY=$(date +%Y-%m-%d)
SLUG="<lowercase-hyphenated-slug>"
obsidian vault=Obsidian create \
  path="Research/${TODAY} - ${SLUG}.md" \
  content="<full rendered markdown>" \
  open
```

(Use `open` so it opens in Obsidian for the user when they come back.)

## Final report to the user

The terminal report has two distinct sections. Keep them separate — conflating them was a recurring bug in prior runs.

### Section 1 — Run summary

- Path of the saved note.
- Hit counts: canon refs, library books, web sources cited.
- One sentence: the headline finding.
- Optionally one line per *content* integration from the cross-check, framed as content not process. **Example (good):** `Added MN 101 Devadahasutta as a load-bearing reference — it refutes the strict-determinist reading.` **Example (bad — never write this):** `Gemini noted MN 101 was missing.`

### Section 2 — Skill improvements made

Only edits to `SKILL.md` or `tools/research_sources.py`. One line each, prefixed with `Improved:`. **If you made no skill edits, omit this section entirely** — don't pad it with content integrations (those go in Section 1).

## When something fails

- **Helper raises `FileNotFoundError`**: a path is wrong — tell the user, don't fudge.
- **Canon search returns 0 hits**: try lang="any" and/or broader book scope before giving up.
- **Calibre returns 0 hits**: try fewer/looser tags. The user can always specify a tag for next time.
- **Gemini returns empty string**: timeout or network — note in the Cross-Check section as "(Gemini unavailable)" and continue.
- **Obsidian create fails**: print the rendered markdown to the terminal so the user can save it manually.

## When Obsidian isn't running

The Obsidian CLI requires the desktop app to be open. If `obsidian` commands fail with
"The CLI is unable to find Obsidian", fall back to writing the note directly to disk at
the vault path (`$VICAYA_VAULT_PATH/Research/`). Obsidian will index it on
next launch. Tell the user in the final report that they need to open Obsidian to use
vault search next time.

## Style notes

- Quote Pāḷi in IAST as it appears in the canon db (don't transliterate).
- Don't pad with summaries the user can derive themselves. Findings should be specific, with quotes.
- Open Threads is for genuine open questions, not "more research could be done". Be honest.
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

## Self-improvement loop (mandatory)

This skill must improve over time based on what goes wrong during real runs. The loop has
a **forcing function**: writing a reflection file. The run isn't done until that file
exists. Empty reflections are allowed; missing ones are not.

### Step 1 — Write a run reflection (always)

Before printing the final report, write a reflection to:

```
<repo-root>/kamma/runs/<UTC-timestamp>.md
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
