# Spec: evidence budget and the absence/inference rule

**Goal:** two prose controls added to `skill/vicaya/SKILL.md`, plus one new search helper — all adapted from `alphaXiv/OpenResearch` (MIT). No GitHub issue.

**Scope was widened mid-thread, 2026-09-20.** The thread began documentation-only, having rejected OpenResearch's scholarly-retrieval channel as unevidenced. Two live API probes overturned that rejection the same day, and the user directed that the channel be built here rather than deferred. Sections 3 and 4 below are that addition.

## Why

**1. Evidence budget — the big win.** OpenResearch's retrieval loop rates a question's difficulty, which buys a fixed number of follow-up search rounds — "a hard cap, not a target" — and stops as soon as coverage is sufficient, preferring fewer strong sources over padding. Vicaya has no breadth ceiling anywhere. 66 run reports carry `duration_min`: median **105 min**, mean 128, max 480; 44 of 66 over 90 min, 24 over 120 — against `kamma/project.md`'s stated "under 30 minutes". `runs/20260912-160000.md` is a dedicated retrospective on a 160-minute run that blames "running all 7 gather phases at maximum breadth for a question that needed ~10 suttas + Visuddhimagga IX + a few modern sources", plus a Phase 2 agent told to pull the whole argument range for **21 loci with no size ceiling** — a 10,321-line phase, a 5.5 MB / ~1.3M-token dossier "larger than any context window", and five bespoke scripts written to reduce it. That run asks by name for a "target evidence set" treated as a stop condition and a size ceiling on sub-agent pulls.

**2. One rule for absence and unread inference.** Both are the same error — asserting what you have not checked — so they are one rule, not two. Absence: backlog **#116** (`runs/TODO.md:379`, Medium, 2 runs) — two sibling runs asserted "the word never occurs in the suttas" without sweeping the concept family; the `antarā-` idiom (antarāparinibbāyī, sambhavesin, opapātika, AN 9.12) is frequent though the compound noun is absent, and foregrounding it re-spined the note. #100 (`runs/TODO.md:448`) is the one-source variant: SA 470 logged as an unreachable gap after checking only the SuttaCentral archive while the Patton translation sat in the EBC vault. Unread inference: #96/#97/#111 (`runs/TODO.md:414, 435, 497`) — fabricated Pāḷi blockquotes, a scholarly attribution written from memory and substantively backwards, an AN6.9/6.10 off-by-one reaching the draft — all three **parked** under the single-sighting rule, so none is scheduled; plus `runs/20260912-160000.md`'s false alarm about 8 "misfiled" scratch entries, all correctly filed, reported from a `grep -c` without reading them.

## Current behavior — read from the source, not assumed

- **Phase 0 scope field.** `scratch-init --scope-assumptions` takes one free-text string; `SKILL.md:900` tells the agent to end it with a `Falsifier: <…>` line. Nothing in `tools/` or `tests/` parses, validates or mentions "falsifier" — a pure prose convention inside an existing field. The budget line copies that pattern, so it costs no code.
- **No breadth ceiling.** `SKILL.md:1342` ("Parallel argument structures — pull the whole range") gives an `id BETWEEN` SQL recipe with no limit on how many loci get one. `SKILL.md:1367` caps a *single* pull at ~20 paragraphs; nothing caps the number of pulls or the run's total target.
- **Search helpers cap at 20 and truncate.** `search_canon` and siblings take `limit: int = 20` with `hits[:limit]` (`tools/research_sources.py:151`, `219–221`). Every search recipe in the skill passes `--limit 20`. #116's own proposed fix says to "count" family members — a count read off a capped set is unreliable, so the rule must say so. (This is a clause, not its own rule: no run has yet made that mistake.)
- **Absence rules today** cover book codes (Hard Rule 12, `SKILL.md:49`; Phase 2 0-hit protocol, `SKILL.md:1303`) and spelling variants (Hard Rule 3, `SKILL.md:35`). The **concept-family** sweep exists only in the series-format section (`SKILL.md:1942`) and `skill/vicaya-what-the-suttas-say/SKILL.md:40`, so it never fires on an ordinary run — exactly what #116 reports.
- **Hard rules are 1–12** (`SKILL.md:28–49`). No prose states a count, so appending #13 renumbers nothing and truncates no instruction. The by-number references to rules 11 and 12 (`SKILL.md:1086`, `1303`, `1943`) stay valid.
- **The dispatch section says "Six rules … state all six"** (`SKILL.md:1010`). Any edit there must not leave that count stale — the failure mode recorded in `kamma/lessons.md` 2026-09-02, where "these five" silently truncated a six-item instruction.
- **The run report template** (`SKILL.md:2682–2689`) has `duration_min` in frontmatter and no record of intended scope.
- **No test asserts `SKILL.md` content** — the two matches under `tests/` are comments. Verification here is structural, not pytest.

## What it should do

### 1. Evidence budget

- **Phase 0 (`SKILL.md:~900`), in the `scope_assumptions` bullet:** add a `Target:` line beside `Falsifier:` — one sentence **naming** the evidence that would answer the question (e.g. "the ~10 suttas where the term is doctrinally load-bearing, Visuddhimagga IX, and two or three modern treatments"), not a count. A named set is checkable against the perspective map; three invented integers are not. State that it is a stop condition, not a quota: stop when the question is answered even if the target is unspent, and exceeding it is a decision to record in the run report, not a default.
- **Phase 0 confirmation template (`SKILL.md:~930`):** add the matching `- Target: …` line.
- **Phase 2 whole-range recipe (`SKILL.md:~1342`):** add a ceiling — whole-range pulls are for the loci that carry the argument, not every hit; name how many up front from the Phase 0 target; prefer a bounded `id` window. Cross-reference the ~20-paragraph cap at `SKILL.md:1367` so the two read as one rule.
- **Sub-agent dispatch (`SKILL.md:~1010–1080`):** fold the ceiling into the existing context-light rules rather than adding a seventh numbered rule, so the "Six rules … state all six" wording stays true. Carry one line into the dispatch prompt template naming the phase's share of the target.
- **Round discipline**, once, in the budget bullet: a search that returned nothing or errored is never re-run verbatim — change the term, stem, book or source, or log the gap and move on. (`runs/20260902-133109.md` wasted several retries on the same failing query.)
- **Run report template (`SKILL.md:~2687`):** add one frontmatter line beside `duration_min` recording the stated target and what was actually gathered. This is the only thing that makes the whole change falsifiable later.

### 2. New Hard Rule 13 — verify before asserting

One rule covering both halves:

- **Absence is a claim that needs its own search.** Before writing that a term, idea or passage is absent: sweep the **concept family** (near-synonyms, grammatical variants, the idiom it belongs to), not just the citation-form compound; check more than one source where one exists (canon DB, EBC vault, SuttaCentral archive); confirm the book code per Hard Rule 12. A doctrinal term can be absent while its concept is frequent. When the *user* says a concept is "frequently mentioned", read that as a claim about the family, not the compound. Counting: helpers cap at `--limit 20`, so a result at exactly the limit is a capped set — say "at least N", or run a counting query, never a frequency claim off a capped result.
- **A lead is not a finding.** A count, a status, a filename, a title, or a clipped `--quiet` snippet is a lead. Read the matched text before reporting it as fact — to the user, in a completion report, or in the note. State an inference as an inference, never as an observation.
- **Phase 2 0-hit protocol (`SKILL.md:~1303`):** add the concept-family sweep as a numbered step after the book-code check, so it fires on ordinary runs.
- **Dedupe:** `SKILL.md:1942` and `skill/vicaya-what-the-suttas-say/SKILL.md:40` point at Hard Rule 13 instead of restating it.

### 3. OpenAlex scholarly channel (added mid-thread)

A new `search-openalex` helper in `tools/research_sources.py`, wired into Phase 4a, following the established sibling pattern of `search-canon` / `search-sanskrit` / `sc-search` (same `_handle_*` shape, same `--quiet`, same `_done` autolog contract).

The probes established five requirements. A build that ignores any of them returns mostly loving-kindness psychometrics, so they are the specification, not advice:

1. **Query `title_and_abstract.search`, never free-text `search=`.** Free text is bag-of-words and degrades to whichever term is commonest: `search=brahmavihara+early+Buddhism` gave 111 hits with 0–2 on topic; `search=Analayo+brahmavihara` gave 14 hits containing not one work by Anālayo. Narrow technical forms against `title_and_abstract.search` ran 38–75% useful.
2. **Fan out over spelling variants and merge.** Diacritic and plain forms return *disjoint* sets in both directions — `brahmavihara` 64 hits, `brahmavihāra` 32, `brahma-vihara` 37, not nested; Anālayo's Tevijja article appears only under the diacritic form, Sharma and Shaw only under the plain one. The helper derives the ASCII fold automatically (it can strip diacritics; it cannot invent them), and takes any further variants from the caller.
3. **The caller must be able to add terms the helper cannot derive.** `appamāṇa` returns just **2** results — Martini's own article sits in the index under the mangled string "Appamāas" — while the Sanskrit cognate `apramāṇa` returns 8 hits, 6 on topic. No transformation derives `apramāṇa` from `appamāṇa`, nor an English gloss from a Pāḷi term. So an `--also` option carries the Sanskrit cognate, the hyphenated form and the gloss, and the skill text tells the agent to supply them.
4. **Abstracts, not full text.** OpenAlex stores abstracts as an inverted index, which the helper reconstructs into plain text. Full text is largely unreachable by script: on one probe 11 of 21 relevant hits were flagged open access but the key monograph sits behind a proof-of-work anti-bot gate; on the other, both flagged-open items returned 403 to automated retrieval — machine-readable full text 0 of 11. The channel therefore names sources with enough abstract to judge them; fetching is the user's, in a browser.
5. **Polite pool.** Send `mailto` on every request, as OpenAlex asks.

Returned per hit: title, year, authors, venue, DOI, landing URL, open-access flag and OA URL when present, citation count, and reconstructed abstract. Results are deduplicated by OpenAlex work id across the fanned-out queries.

**Phase 4a wiring.** One subsection telling the agent when to reach for it (a modern scholarly angle, a foreign-language monograph, the current literature around a term — not a canonical question, where it is near-useless), how to query it (technical transliterated terms, plus the Sanskrit cognate and English gloss via `--also`), and that its output is a source *to fetch*, never a source to cite from the abstract alone — Hard Rule 13's "a lead is not a finding" applies directly.

### 4. Network-call discipline

This is the repo's first helper that calls an external service. Per `~/.claude/CLAUDE.md`: a function touching the network ships with a test using a faked response. Failures must be legible — a timeout, a non-200, or unparseable JSON returns a named error, never an empty list that reads like "no scholarship found". The HTTP opener is injectable so tests never touch the network.

## Assumptions & uncertainties

- **The 105-minute median is not purely search time.** `duration_min` is whole-run wall clock, including user interruptions, cross-check waits and note rewrites. It proves runs are long; the 160-minute retrospective proves breadth is *a* cause; neither proves over-gathering is the dominant one.
- **Guidance cannot be enforced, by choice.** Per `kamma/lessons.md` 2026-09-02 — "if the checker and the checked are the same agent, the gate guards nothing"; "a prompt line beats a subcommand, a marker and a gate".
- **Structural checks prove plumbing, not behaviour.** Greps confirm the text landed; they would stay green if the rule changed nothing. Behaviour is unproven until several real runs carry the new report line — which is why that line is in scope. The in-thread falsification is a dry re-run of the 160-minute run's question against the new Phase 0 text (below), not a claim that runs got shorter.
- **Scanned, not read in full:** the 70 untriaged run reports since the 2026-08-14 triage were searched by keyword.

## Constraints

- **Code is limited to the new helper and its tests.** `tools/research_sources.py` gains `search_openalex` plus its CLI wiring; `tests/` gains coverage for it. Nothing else under `tools/`, `scripts/` or `config/` changes, and no existing helper is modified.
- **`skill/vicaya/SKILL.md` stays one file.** Do not re-modularize: the staged section-router was built (`kamma/archive/20260602_vicaya-staged-skills-section-router`) and deleted as redundant (`kamma/archive/20260618_remove_staged_routers`).
- **One anchored insertion per edit, structure checked after.** `kamma/lessons.md` 2026-05-12: sloppy inline `SKILL.md` edits once displaced two hard rules into Phase 4b and orphaned a code block.
- **No hard-wrapped prose** in any markdown this thread writes — one line per paragraph.
- **Portable** across Claude Code, Codex, pi and opencode.
- **Do not touch** `runs/TODO.md` item text or anything under `kamma/archive/**`.

## How we'll know it's done

- Hard Rule 13 exists; rules 1–12 are byte-identical (`git diff` shows no change inside them); the by-number references at `SKILL.md:1086`, `1303`, `1943` still name the right rules.
- `SKILL.md:1010`'s "Six rules … state all six" is still accurate after the dispatch edit.
- Phase 0's scope bullet and confirmation template both carry a `Target:` line; the Phase 2 recipe carries a loci ceiling; the 0-hit protocol carries the concept-family step; the report template carries the target/actual line.
- Both prior copies of the concept-family rule point at Hard Rule 13 rather than restating it.
- **Falsification:** re-read `runs/20260912-160000.md`'s question against the new Phase 0 text and write down the target set it produces. If that target does not visibly exclude the 21-loci whole-range pull, the wording is too weak and gets rewritten before the thread closes.
- Structure intact: the heading list is unchanged and the code-fence count stays even.
- `search-openalex` returns real hits against the live API for a probe term, and its tests pass against faked responses without touching the network.
- A failed request (timeout, non-200, bad JSON) produces a named error, not an empty result set.
- `uv run pytest tests/ -q` passes and `uv run ruff check .` is clean.
- `rejected.md` exists in this thread directory recording what was dropped and why.

## What's not included

- **No code**: no budget flag, no scratch field, no overrun warning. Guidance only, by decision.
- **No result-cap hard rule of its own** — folded into Hard Rule 13 as a counting clause. The failure mode was found by reading the helper's source, not reported by any run; inventing a defect and then fixing it is its own risk.
- **No alphaXiv or bioRxiv integration.** Neither indexes this field. OpenAlex is the only relevant corpus of OpenResearch's three.
- **No skill modularization** — built and removed already.
- **No change to the sub-agent architecture.** OpenResearch forbids delegating the retrieval loop; vicaya delegates per phase for a verified reason (an all-phase agent overflows and dies without warning, `SKILL.md:1000`), and `kamma/archive/20260520_ars-borrow` already rejected multi-agent restructuring on portability grounds.
- **No per-completion dispatch loop, no experiment-tree model** — unevidenced, and no analogue in a run that produces one note.
- **No revival of parked #96, #97, #100, #111** as separate work — Hard Rule 13 covers the family.
