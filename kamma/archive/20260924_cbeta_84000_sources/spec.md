# Spec — CBETA and 84000 as vicaya sources

## Overview

Add two canonical sources to vicaya so a research run can find **what other Buddhist schools say about a topic**: the Chinese canon (CBETA) and the Tibetan canon in English translation (84000). Topic search across traditions is the main use. Parallels are secondary. One small parallels fix is included because it is cheap and fixes wrong output today.

This thread came out of a review of CanonRAG (canonrag.dharmaaccess.org), which searches SuttaCentral, CBETA, GRETIL and 84000. We decided **not** to call CanonRAG. All of the following was checked on 2026-09-24:

- Its public API does not work. `api.canonrag.com` (the host in the user's request example) has no DNS record. `api.canonrag.dharmaaccess.org` (the host in its docs) returns Railway `{"message":"Application not found"}` (404) behind a `*.up.railway.app` certificate. Only the website's own `/api/query` proxy answers.
- Four test searches through that proxy gave poor results. "two arrows feeling" did not find SN 36.6. A Chinese-filtered query returned 0 hits. A Sanskrit query returned one text that did not match. Every hit scored the same (0.016), and each query took 5–25 s.
- The free key (in dpd-db `config.ini`, key `canonrag`) allows 100 requests a day.
- vicaya already holds SuttaCentral and GRETIL locally. CBETA and 84000 are now cloned locally too (below).

## Current behaviour (verified 2026-09-24)

- vicaya has no Chinese-canon or Tibetan-canon search. The only cross-tradition primary-text channel is GRETIL: `search_sanskrit()` in `tools/research_sources.py`, used by `skill/vicaya/SKILL.md` "### Phase 3b — Sanskrit source search" (line 1597), gated on angle 7.
- Angle 16 ("Cross-school / Āgama comparison", `skill/vicaya/SKILL.md` ~line 873) lists only SuttaCentral and EBC tools.
- `sc_search(lang="lzh")` greps `$VICAYA_SC_DATA_PATH/sc_bilara_data/root/lzh/`, which holds 66 files. The skill (Phase 2.5, helper table line 143, angle 16 line 879) calls this a grep of "the offline Chinese Āgama root texts". That is false for almost all of them.
- `sc_parallels()` reads Chinese root text only from that same bilara folder. Measured: of the 1,911 Āgama uids (`sa|ma|ea|da…`) named in `parallels.json`, **55** have a bilara file. The rest come back with `text_gaps: ["no root text in offline archive"]`.
- The same archive holds `html_text/lzh/` with 4,620 Chinese HTML files keyed by SuttaCentral uid, e.g. `html_text/lzh/sutta/sa/sa401-500/sa470.html`, `html_text/lzh/sutta/ma/ma107.html`, `html_text/lzh/sutta/ea/ea11/ea11.7.html`. vicaya never reads it. Measured: **1,841 of 1,911** Āgama uids have an HTML file. The other 70 are range uids (e.g. `ma107-108`, `ea11.7-8`, `sa1060-1061`) whose member files do exist (`ma107.html`, `ea11.7.html`, `sa1060.html`). The existing `_sc_expand_range_uid()` produces those members.
- For example, `parallels.json` holds the group `['sn36.6', 'sa470']`. `sa470.html` is on disk, but `sc-parallels sn36.6` returns no Chinese text today.
- HTML layout: the text follows `</header>`, one `<p>` per paragraph. A Taishō line anchor `<a class='ref t' id='t0120a01' href='#t0120a01'>T 0120a01</a>` marks the **start** of that Taishō line, inline in the text.
- The comment block above `SCParallel` says "MA holds ~15 suttas, EA almost nothing". That is true only of the bilara folder.
- `tools/scratch.py::_maybe_autolog` logs every CLI subcommand except the `scratch-*` set and `lookup-book`, so new subcommands are logged with no extra work.
- The Phase 3b label lives in exactly three places (swept with `rg --hidden`): `tools/scratch.py:164` (`"Phase 3b — Sanskrit"`), `skill/vicaya/SKILL.md:1037` (gate table), `skill/vicaya/SKILL.md:1597` (heading). No test references it.
- The DPD database has **no** Chinese: 0 headwords with CJK in `meaning_1` or `notes`, and there is no Chinese column. Chinese search terms must come from elsewhere (see What it should do, item 5).
- The sibling pattern for an optional local corpus is GRETIL: env var `VICAYA_GRETIL_PATH`, `search_sanskrit()` returns `[]` when the path is unset, handler `_handle_search_sanskrit` (~line 2800), parser `pss` (~line 3230), `.env.example` lines 51–55, README Sources-table row (line 24), README "Getting the GRETIL corpus", "2 — Discover local paths" and "3 — Write .env".

## The two sources (cloned and measured 2026-09-24)

Test scripts for every figure below are kept in `artifacts/` next to this spec (`cbeta_probe.py`, `cbeta_par.py`, `e84000_probe.py`, `sc_probe.py`).

### CBETA

- Cloned: `git clone --depth 1 https://github.com/cbeta-org/xml-p5.git ~/MyFiles/2_Resources/cbeta`. Commit `dbdea41 CBETA 2026.R2`. The download took 16 min and uses 2.6 GB on disk. Licence CC BY-NC.
- Collections are top-level folders: `A B C CC D F G GA GB I J K L LC M N P S T TX U X Y YP ZS ZW` (plus `schema`).
- The Taishō (`T/`) has 2,459 XML files (859 MB) for 2,457 text ids. Filenames: `T/T02/T02n0099.xml`. Some ids carry suffix letters (`T0128a`, `T0128b`, `T0132a` …). One id spans several files: `T0220` is in `T05n0220`, `T06n0220` and `T07n0220`.
- Title: `<title level="m" xml:lang="zh-Hant">雜阿含經</title>` in the header.
- Taishō lines: `<lb n="0120a06" ed="T"/>` marks the start of line `0120a06`. The text between two `<lb>` tags belongs to the first one.
- Rare characters: `<g ref="#CB00145"/>`, declared per file in `<charDecl>` as `<char xml:id="CB…">…</char>`. **All 111,343** `<g>` references in the Taishō resolve when each `<char>` block is parsed on its own, preferring `<mapping type="unicode">U+XXXX</mapping>`, then "normalized form", then "composition". (A first test that used one regex across blocks wrongly showed 10 of 61 unresolved in T 99.)
- Line-crossing search works: in T 99, `凡夫身觸生諸受` crosses `<lb n="0120a06"/>` in the raw XML. After dropping tags and joining lines it matches, and it maps to line `0120a05`, where it starts.
- Speed, query `涅槃`, median of 3 after a warm-up run, load average under 1.2 on a 22-core machine:

  | scope | workers | median | hits | texts |
  |---|---:|---:|---:|---:|
  | Taishō | 1 | 13.9 s | 56,626 | 1,236 |
  | Taishō | 8 | 3.1 s | 56,626 | — |
  | Taishō | 12 | 2.7 s | 56,626 | — |
  | all collections (5,017 files) | 12 | 9.6 s | 142,481 | — |

  A process pool gives identical hit counts and makes a text cache unnecessary.

### 84000

- Cloned: `git clone --depth 1 https://github.com/84000/data-tei.git ~/MyFiles/2_Resources/84000`. It uses 250 MB on disk. Licence CC BY-NC-ND 3.0.
- Translations: `translations/kangyur/translations/*.xml` (396 files) plus `translations/tengyur/publications/*.xml` (3 files). The folders `translations/*/placeholders/` (560 + 3,366 files) are stubs and are out of scope.
- **Every one of the 399 filenames carries its Toh number(s)**, e.g. `071-011_toh297-multitude_of_constituents.xml`, `088-035_toh540,1078-the_dharani_surupa.xml`. 94 files carry more than one. The in-file `<bibl key="toh…">` is missing in 3 files (e.g. `043-009_toh72-…`), so the filename is the source for Toh numbers.
- Title: `<title type="mainTitle" xml:lang="en">Multitude of Constituents</title>`.
- Translator: `<author role="translatorEng">` (a person) and/or `<author role="translatorMain">` (a group). All 399 files have at least one.
- Body: `<p>` paragraphs with inline `<note>` elements (toh297: 94 `<p>`, 49 `<note>`). Notes are dropped before search.
- Web link: `https://84000.co/translation/toh297` returns 200 with title "Multitude of Constituents". The old `read.84000.co/translation/toh297.html` form returns 301 to it.
- Speed: a case-insensitive paragraph search for `four immeasurables` over the 396 Kangyur files takes 2.9 s (median of 3, after a warm-up run) and finds 84 paragraphs. The shipped search over all 399 files finds 88 (4 more in Tengyur Toh 3808) in 3.0 s. No pool is needed.

## What it should do

1. **`search-chinese QUERY`** searches CBETA under `$VICAYA_CBETA_PATH` with a fixed string, using a process pool (12 workers).
   - Scope: Taishō (`T/`) by default. `--collection X` picks another top-level collection. `--collection all` searches every collection. `--text T0099` limits the search to the file(s) of one text id.
   - Tags are dropped (`<note>`, `<rdg>`, the header and `<back>` removed, rare characters resolved) and Taishō lines are joined, so a phrase that crosses a line still matches.
   - The output is JSON with `by_text` (the 50 texts with most matches: `id`, `title`, `count`, most first; `total_texts` counts all of them — capped after a live run showed one search printing 116 KB into the dossier) and `hits` (up to `--limit`, default 20: `id`, `title`, `vol` such as `T02`, `line` such as `0120a05`, `snippet` of about 60 characters each side). It also gives `total_hits`.
   - An unset or missing path returns an empty result with no error, like GRETIL.
2. **`search-84000 QUERY`** searches the 399 translation files under `$VICAYA_84000_PATH`, case-insensitive, per `<p>`, with `<note>` removed. `--toh N` limits the search to files whose filename carries toh N. The output has `by_text` (`toh`, `title`, `count`, grouped by Toh, at most 50) and `total_texts` and `hits` (`toh`, `title`, `translator`, `snippet`, `url` = `https://84000.co/translation/toh<N>`). An unset path returns an empty result.
3. **The Āgama parallel fix.** When `sc_parallels` finds no bilara Chinese file for a uid, it reads `html_text/lzh/**/<uid>.html`. A range uid is read by joining its member files. Each Taishō anchor becomes an inline `[0120a01]` marker, one paragraph per line, in `text_lzh`. Its "no root text" gap then goes away. The agent can cite any quote to its Taishō line.
4. **Setup and config.** Add `VICAYA_CBETA_PATH` and `VICAYA_84000_PATH` to `.env.example`, next to the GRETIL block and in its style. Add README "Getting the CBETA canon" and "Getting the 84000 translations" sections (clone command, size, time, licence), Sources-table rows, and entries in "2 — Discover local paths" and "3 — Write .env". Update `kamma/tech.md` and `kamma/project.md`.
5. **Skill wiring.**
   - `skill/vicaya/SKILL.md`: rename Phase 3b to "Phase 3b — Other canons (Sanskrit, Chinese, Tibetan)" at both carriers. It runs when angle 7 or angle 16 applies, or when the question asks what other schools say. The search order is: English themes in 84000, then Chinese terms in CBETA, then GRETIL. The agent reads `by_text` first, then follows up with `--text`/`--toh` on the texts that matter. Chinese terms come from the Āgama parallel text (`sc-parallels` now returns it), WisdomLib/web, or the agent's own knowledge, and the agent states which source it used. DPD has no Chinese. Add helper-table rows, return shapes and `--quiet` list entries. Angles 2 and 16 name the new searches. The false `sc-search --lang lzh` description is fixed to point to `search-chinese`.
   - Citation formats: `T 99 (雜阿含經), T02 p. 0120a05, CBETA` and `Toh 297, *Multitude of Constituents*, trans. <translator>, 84000`. The existing published-translation rule stays: Chinese root text is quoted with a published translation, or paraphrased and labelled. 84000 is itself a published translation.
   - `tools/scratch.py:164`: rename the label to match, and change the checklist item to "Other canons (GRETIL / CBETA / 84000) searched where applicable (or 'not applicable')".
   - `skill/vicaya-quick/SKILL.md`: the triage names the two new searches for "what do other schools say" questions.
   - `skill/vicaya-what-the-suttas-say/SKILL.md` inherits from `skill/vicaya/SKILL.md` and needs no edit.
6. **Fix the false comment** above `SCParallel`.

## Assumptions & uncertainties

Everything in "Current behaviour" and "The two sources" was measured. What remains open:

- **Snippet quality in CBETA files other than T 99** has not been checked by eye. The drop list (`note`, `rdg`, `teiHeader`, `back`, `mulu`, `docNumber`, `figure`, `charDecl`) was tested only on T 99. The plan includes a spot check of three other texts.
- **The first-found `>` in the flat text** came from splitting on `<text` instead of `<body`. The real code splits on `<body`. This is known, not yet coded.
- **12 workers** is the measured sweet spot on this 22-core machine. The worker count follows `min(12, os.cpu_count())` and is not tuned for other machines.
- **Licences** (CBETA CC BY-NC, 84000 CC BY-NC-ND) allow private research and quotation with attribution. Vault notes sync to a public GitHub repo, so every quote carries its attribution.

## Constraints

- No network calls from the new helpers. Local files only.
- Never modify `.env`. Only `.env.example` changes; the user sets `.env`.
- Follow the GRETIL sibling pattern. New code goes in `tools/research_sources.py`.
- No new Python dependencies (stdlib `re`, `html`, `concurrent.futures`).
- Scoped validation only, per `kamma/tech.md` "Validation Scope".
- One line per paragraph in every markdown file.

## How we'll know it's done

- `search-chinese "涅槃"` returns `total_hits` 56,626 and `by_text` of 1,234 texts (T0220's three files merge into one entry), led by `T0220`, `T1851`, `T1736`, `T0374`. It runs in under 5 s.
- `search-chinese "凡夫身觸生諸受" --text T0099` returns a hit at line `0120a05`. A fixture test proves the line-joining and fails when the joining is reverted.
- `search-84000 "four immeasurables"` returns 88 paragraph hits (84 Kangyur + 4 in Tengyur Toh 3808), each with toh, title, translator and a `https://84000.co/translation/toh…` URL.
- `sc-parallels sn36.6` returns `sa470` with `text_lzh` containing `[0119c29]` and no "no root text" gap. A range uid (e.g. from `ma107-108`) returns joined text.
- With either env var unset, both new searches return empty results and do not crash.
- New tests use small fixture files (not the real corpora) and pass. Ruff, pyright and pyrefly are clean on touched files.
- A live `/vicaya-quick` on a "what do other schools say about X" question calls both new searches and cites them in the formats above.

## What's not included

- CanonRAG API integration (reasons in Overview).
- Pointers or text for non-Āgama Taishō (`t<N>`) and Derge (`d<N>`) parallels in `sc-parallels`. The agent can use `search-chinese --text` and `search-84000 --toh` instead.
- A change to `sc-search --lang lzh` to cover `html_text`. `search-chinese` covers the Āgamas (T 1, T 2 and others).
- 84000 placeholder files, and Tibetan-script originals (data-tei holds English only).
- Meaning-based (embedding) search, a cross-language term table, and machine translation of Chinese for quotation.

## Changes after review (2026-09-24)

The review found real-data bugs; see `plan.md` "Review fixes" (R1–R12) for evidence. Behaviour now differs from the sections above in these ways: `search_chinese` raises `ValueError` (CLI exit 1) for an unknown collection, a text id matching no file, or an empty query, and accepts loose ids (`T99`). Whitespace in a Chinese query is ignored. X-collection lines use only the file's own edition. Siddham/Rañjanā glyphs and XML comments are not searched. Both searches return `total_texts`. 84000 hits carry `section` (`front`/`body`/`back`) and a snippet around the match, and `--toh` accepts `Toh 297`. The `sc-parallels` html fallback applies to Āgama uids only. The Taishō search now takes about 3.0 s.

