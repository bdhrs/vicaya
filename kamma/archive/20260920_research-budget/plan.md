# Plan: evidence budget and the absence/inference rule

Spec: `spec.md` in this directory. No GitHub issue. Documentation-only thread — every edit lands in `skill/vicaya/SKILL.md` except one in `skill/vicaya-what-the-suttas-say/SKILL.md`.

## Architecture Decisions

- **The target set is prose inside an existing field, not a new flag.** `--scope-assumptions` already carries a free-text `Falsifier:` line that no code parses (verified: no match for "falsifier" anywhere in `tools/` or `tests/`). A `Target:` line is the same pattern, so the whole budget costs zero code and cannot break a helper call.
- **A named evidence set, not a count.** The retrospective that asked for this described its target as "~10 suttas + Visuddhimagga IX + a few modern sources" — a named set, checkable against the perspective map. Three invented integers would be precision the agent does not have at Phase 0.
- **One new hard rule, not three.** Rules 1–12 are mechanical traps (book codes, YAML colons, auto-captions). Absence and unread-inference are both "asserting what you did not check" and belong together; splitting them would dilute a section whose value is skimmability.
- **The counting clause lives inside Hard Rule 13, not on its own.** The `--limit 20` truncation was found by reading the helper's source; no run has yet made a frequency claim off a capped set. It earns a clause because #116's own fix says "count them", not a rule of its own.
- **Fold the dispatch ceiling into the existing rules.** `SKILL.md:1010` says "Six rules … state all six". Adding a seventh numbered rule there would leave a stale count — the exact defect in `kamma/lessons.md` 2026-09-02.
- **The report-template line is the measurement, not decoration.** Guidance cannot be enforced, so the only way a later triage can tell whether this worked is a per-run record of target vs actual beside `duration_min`.
- **Verification is structural plus one falsification.** Greps prove the text landed and would stay green if the rule did nothing; the dry re-run of the 160-minute run's question is what tests whether the wording bites.

## Phase 1 — Evidence budget

- [x] Record the pre-edit baseline for structure checks.
  → verify: `grep -c '^```' skill/vicaya/SKILL.md` and `grep -n '^#\{1,3\} ' skill/vicaya/SKILL.md > the session scratchpad (headings-before.txt)`; both saved in the task notes below for comparison at Phase 3.

- [x] Add the `Target:` line to the Phase 0 `scope_assumptions` bullet (`SKILL.md:~900`), beside the existing `Falsifier:` instruction: one sentence naming the evidence that would answer the question, explicitly a stop condition and not a quota, with overrun recorded in the run report rather than taken as default. Include the round-discipline sentence here — a search that returned nothing or errored is not re-run verbatim.
  → verify: `grep -n 'Target:' skill/vicaya/SKILL.md` shows the new line inside the `scope_assumptions` bullet and before the `ambiguity_status` bullet; the `Falsifier:` sentence is unchanged (`git diff` shows an addition only).

- [x] Add the matching `- Target: …` line to the Phase 0 confirmation template (`SKILL.md:~930`), between `Seeds:` and `Falsifier:`.
  → verify: `sed -n '/^Assumptions:/,/^```/p' skill/vicaya/SKILL.md` lists Textual scope, Interpretive scope, Depth, Practical angle, Seeds, Target, Falsifier — seven lines, in that order.

- [x] Add the loci ceiling to the Phase 2 whole-range recipe (`SKILL.md:~1342`): whole-range pulls are for the loci that carry the argument, not every hit; name the count up front from the Phase 0 target; prefer a bounded `id` window; cross-reference the ~20-paragraph cap at `SKILL.md:1367`.
  → verify: `sed -n '1342,1372p' skill/vicaya/SKILL.md` shows the ceiling sentence inside the "Parallel argument structures" paragraph and the code fence below it intact and unmoved.

- [x] Carry the phase's share of the target into the sub-agent dispatch prompt by folding it into the existing context-light rules (rule 2 or 3) and the prompt template's step 4 — do not add a seventh numbered rule.
  → verify: `sed -n '1010,1012p' skill/vicaya/SKILL.md` still reads "Six rules … state all six" and the numbered list below still ends at 6; `grep -n 'target' skill/vicaya/SKILL.md` shows the new text inside the dispatch prompt template.

- [x] Add the target/actual frontmatter line to the run report template (`SKILL.md:~2687`), directly beside `duration_min`.
  → verify: `sed -n '2682,2692p' skill/vicaya/SKILL.md` shows the new key inside the `---` frontmatter block, and the block still opens and closes with `---`.

- [x] Phase 1 verification.
  → verify: `uv run pytest tests/ -q` passes and `uv run ruff check .` is clean; `git diff --stat` lists `skill/vicaya/SKILL.md` and nothing else.

## Phase 2 — Hard Rule 13

- [x] Append Hard Rule 13 ("Verify before asserting") to the Hard rules section (`SKILL.md:~49`), covering both halves in one rule: the concept-family absence sweep with its multi-source and book-code clauses and the capped-result counting clause; and "a lead is not a finding" for counts, statuses, filenames, titles and clipped `--quiet` snippets, with inference stated as inference.
  → verify: `sed -n '28,52p' skill/vicaya/SKILL.md` shows rules 1–13 numbered consecutively; `git diff skill/vicaya/SKILL.md` shows no change inside rules 1–12.

- [x] Confirm the by-number cross-references still resolve.
  → verify: `grep -n 'Hard Rule 1[12]' skill/vicaya/SKILL.md` returns the three known sites (~1086 temp dirs → rule 11, ~1303 0-hit protocol → rule 12, ~1943 series absence → rule 12) and each still names the rule it means — confirm by reading each line, not by the count alone.

- [x] Add the concept-family sweep as a numbered step to the Phase 2 0-hit recheck protocol (`SKILL.md:~1303`), after the book-code check.
  → verify: `sed -n '1303,1316p' skill/vicaya/SKILL.md` shows the new step in sequence and the `lookup-book` code fence below it intact.

- [x] Point the two existing copies of the concept-family rule at Hard Rule 13 instead of restating it — `SKILL.md:~1942` and `skill/vicaya-what-the-suttas-say/SKILL.md:40`.
  → verify: `grep -n 'stem + synonym' skill/vicaya/SKILL.md skill/vicaya-what-the-suttas-say/SKILL.md` — each remaining hit references Hard Rule 13 rather than spelling the sweep out a second time.

- [x] Phase 2 verification.
  → verify: `uv run pytest tests/ -q` passes and `uv run ruff check .` is clean; `git diff --stat` lists only the two skill files.

## Phase 3 — Falsify, check structure, record rejections

- [x] **Falsification (this is the real test, not the greps).** Re-read the question in `runs/20260912-160000.md` and write the `Target:` line the new Phase 0 text would produce for it. Record it in this plan. If that target does not visibly exclude the 21-loci whole-range pull that run performed, the wording is too weak — rewrite the Phase 1 text and repeat.
  → verify: the written target set is in this file, and a one-line judgement states whether it excludes the 21-loci pull. A "yes" that does not name the excluding clause does not count.

- [x] Structure check against the Phase 1 baseline.
  → verify: `grep -n '^#\{1,3\} ' skill/vicaya/SKILL.md` matches `the session scratchpad (headings-before.txt)` exactly (`diff` returns nothing), and the code-fence count is unchanged and even.

- [x] Write `rejected.md` in this thread directory: OpenAlex/scholarly-database integration, skill modularization, the sub-agent architecture change, the per-completion dispatch loop, the experiment-tree model, and the standalone result-cap rule — each with the reason and the evidence checked, so the same imports are not re-proposed.
  → verify: `rejected.md` exists and names all six with a reason each.

- [x] Note in `rejected.md` that backlog #116's proposed fix is implemented by this thread, pending `/vicaya-improve` triage — do not edit `runs/TODO.md`.
  → verify: `git status --short runs/` is empty.

- [x] Phase 3 verification.
  → verify: `uv run pytest tests/ -q` passes, `uv run ruff check .` is clean, and `git status --short` lists only the two skill files and this thread's directory.

## Known limitation, recorded deliberately

Structural checks prove the text landed, not that runs get shorter or that absence claims get checked. Behaviour is unproven until several real runs carry the new target/actual report line, and that line exists so the next `/vicaya-improve` triage can answer it. If durations do not move, the honest response is to revisit the approach, not to tighten the wording.

## Phase 4 — OpenAlex scholarly channel (added mid-thread 2026-09-20)

Scope widened by the user after two live probes overturned the rejection of this channel. Requirements are in `spec.md` §3; they come from measured probe behaviour, not from the API docs, and a build that skips any of them returns noise.

- [x] Add a `ScholarHit` dataclass and `search_openalex()` to `tools/research_sources.py`, beside the other search functions. Query `title_and_abstract.search` only. Derive the ASCII-folded variant of the query automatically (strip combining marks via `unicodedata`); accept further variants from an `also` argument. Fan out one request per variant, dedupe by OpenAlex work id, reconstruct each abstract from `abstract_inverted_index`, send `mailto`. Take an injectable opener so tests never hit the network. On timeout, non-200 or unparseable JSON, raise/return a **named error** — never an empty list.
  → verify: `uv run python3 -c` calling `search_openalex` with a fake opener returning a canned two-work payload gives two hits with abstracts reconstructed in word order.

- [x] Wire the CLI subcommand `search-openalex` following the `search-sanskrit` pattern exactly: `_handle_search_openalex` with `_dump(..., quiet=...)` and `_done(argv, result)` so auto-logging files it like every other search helper. Options: `--also` (repeatable), `--limit`, `--quiet`.
  → verify: `uv run tools/research_sources.py search-openalex --help` lists `--also`, `--limit`, `--quiet`; and a live call for `Tevijja` returns real hits with DOIs.

- [x] Add tests in `tests/test_research_sources.py` with faked responses: abstract reconstruction from an inverted index; ASCII folding producing a second query for a diacritic term; dedupe when two variant queries return the same work id; and each failure path (timeout, non-200, bad JSON) producing a named error rather than an empty list.
  → verify: `uv run pytest tests/test_research_sources.py -q -k openalex` passes, and no test performs a real network call.

- [x] Wire it into Phase 4a of `skill/vicaya/SKILL.md`: when to reach for it and when not to (modern/cross-tradition and foreign-language monographs yes; a purely canonical question no), how to query it (technical transliterated terms; pass the Sanskrit cognate and English gloss via `--also`; note that the natural Pāḷi spelling of a term may return zero), and that a hit is a source to fetch, never a source to cite from its abstract — Hard Rule 13 applies.
  → verify: `grep -n 'search-openalex' skill/vicaya/SKILL.md` shows the subsection inside Phase 4a and before the Phase 4 exit-gate line; heading text and fence count still match the Phase 1 baseline.

- [x] Phase 4 verification.
  → verify: `uv run pytest tests/ -q` passes, `uv run ruff check .` clean, and live calls reproduce both probe results — Maithrimurthi's monograph (DOI `10.11588/fid4sarep.00004644`) from the fanned-out brahmavihāra query, and the Shulman 2025 article (DOI `10.1007/s12671-025-02597-6`) from a title-term query.

---

## Results

### Baseline (Phase 1, before any edit)

443 passed, 1 skipped; `ruff` clean. No pre-existing failures. `skill/vicaya/SKILL.md` 2,763 lines, 135 headings, 150 code fences. `data/youtube_channels.md` was already modified in the working tree at session start — **PRE-EXISTING — NOT CAUSED BY THIS THREAD**, not touched.

### Falsification — does the new wording actually exclude the 21-loci pull?

The question behind `runs/20260912-160000.md` was the brahmavihāra one (note: `Vicaya/2026-09-12 - brahmavihara-insight-basis.md`) — on what basis the brahmavihāras serve as a foundation for insight. The `Target:` line the new Phase 0 text produces for it:

> Target: the suttas where a brahmavihāra is explicitly yoked to insight or to a named liberation attainment (the mettā-cetovimutti passages and their AN/SN parallels), Visuddhimagga IX with the Vibhaṅga's treatment, and two or three modern analyses.

**Verdict: excluded, and the excluding clause is nameable.** It is not the `Target:` line by itself — a target naming "the suttas where X is yoked to insight" does not on its own forbid pulling 21 ranges. The clause that bites is the Phase 2 ceiling: *"Decide how many whole-range pulls this phase gets before you start, from the Phase 0 `Target:` line, and pull only those."* That converts a target naming roughly ten suttas into a budget of roughly ten whole-range pulls, and 21 visibly exceeds it. The byte size is then bounded by the pre-existing ~20-paragraph cap under "Quote fully, not representatively", which the new ceiling paragraph now cross-references explicitly so the two are read together: one bounds a single pull, the other bounds how many.

**Residual weakness, recorded rather than papered over.** The `Target:` line bounds the *count* of loci, not the *volume* of text. Ten whole-range pulls at the 20-paragraph cap is ~200 paragraphs — manageable, but only because that older cap exists. If the paragraph cap is ever relaxed, the ceiling alone will not prevent another oversized dossier. Nothing in this thread depends on that, but a later change to the quoting rule should not be made without re-reading the ceiling.

### Structure check (Phase 3)

135 headings, heading text byte-identical to the pre-edit baseline (line numbers shifted, as every insertion shifts them — the text comparison is the check). 150 code fences, unchanged and even. `git diff -U0` shows seven hunks, all pure insertions except one deliberately rewritten dispatch rule; nothing was deleted from Hard Rules 1–12.

### Cross-reference check (Phase 2)

Read, not counted: the three by-number references resolve correctly after the insertion — line ~1097 → Hard Rule 11 (temp directories), line ~1314 → Hard Rule 12 (book code), line ~1956 → Hard Rule 12 (book code). The dispatch section's "Six rules … state all six" is still accurate: the budget was folded into rule 2 rather than added as a seventh.

### Final checks

443 passed, 1 skipped; `ruff` clean. `git status --short` lists `skill/vicaya/SKILL.md`, `skill/vicaya-what-the-suttas-say/SKILL.md`, this thread directory, and the pre-existing `data/youtube_channels.md`.

### Still unproven, by design

Every check above proves the text landed and the file is structurally sound. None of it proves a run gets shorter or an absence claim gets checked — the greps would be just as green if the rules changed nothing. That question is answered by the `target_vs_actual` line now in the run report template, read across the next several runs at `/vicaya-improve` triage. If durations do not move, the honest response is to revisit the approach, not to tighten the wording.

### Phase 4 results (OpenAlex channel)

**A live call caught a real bug the unit tests did not.** The first implementation returned as soon as `limit` was reached, which stopped the fan-out before the later spellings were ever queried — so `--also` silently did nothing whenever the first spelling filled the quota. A fanned-out call with a limit of 40 queried only two of four spellings. Fixed by querying every variant and truncating at the end; the test that covered `limit` was rewritten to assert that both spellings are still requested, which is the behaviour that matters. This is the case for keeping a live call in the plan: the unit tests were green through the bug, because each one exercised a single variant.

**Fan-out confirmed against the live API.** `brahmavihāra` with `--also brahma-vihara --also apramāṇa` returns **81 unique works from four spellings** (25 / 24 / 25 / 7 unique contributions from a maximum of 100 raw results — only 19 duplicates). That independently reproduces the probe's central measurement: the spellings are near-disjoint, so the fan-out is the feature, not an optimisation.

**Both probe findings reproduced through the shipped helper**, with abstracts: Maithrimurthi, *Wohlwollen, Mitleid, Freude und Gleichmut* (2025 digitisation, open access, DOI `10.11588/fid4sarep.00004644`); and Shulman, "An Ethical Samādhi: Brahma-vihāra Meditation and the Flexible Early Buddhist Path" (2025, open access, DOI `10.1007/s12671-025-02597-6`).

**Tests proven to bite.** Reverting the two core behaviours — querying `title_and_abstract.search` instead of free text, and fanning out over variants — failed exactly 3 of the 12 OpenAlex tests; restored in the same command, all 12 pass. Twelve tests, no network access in any of them.

**Failure paths are named, not silent.** Non-200, HTTP error, timeout and unparseable JSON each raise `OpenAlexError` and the CLI exits 1 with an `error:` line; an empty list therefore always means zero hits for that spelling. This was the specific risk in adding the repo's first network helper.

**Diagnostics.** `pyright` reported 6 errors in the new test file (an attribute set on a function object); the fake opener was refactored to a callable class and `pyright` is clean on both changed Python files, as is `ruff`.

### Final state

455 passed, 1 skipped (up from the 443 baseline — 12 new). `ruff` clean, `pyright` clean on both touched Python files. Heading text and count unchanged from the Phase 1 baseline (135); code fences 152, up by exactly the one bash block added to Phase 4a, still even.

---

## Review round 1 — findings and fixes

Two reviews run in parallel: CodeRabbit (`--agent --uncommitted --include-untracked`, exit 0) and an independent from-scratch audit that read the spec cold. Every finding below was reproduced before being accepted.

**1. The fan-out starvation was never actually fixed (audit, CONFIRMED — the most serious finding).** The mid-implementation fix removed the early return so every spelling is *queried*, but the merge still concatenated variant-by-variant before truncating. With the CLI default limit of 25 and a page size of 25, the first spelling filled the quota and every later one was fetched and then discarded — `--also` was a no-op at the default. Reproduced live: `--also apramāṇa` at the default returned 25 hits, all from the first spelling. Worse, my own earlier live check *showed* this (25 + 15 from two of four spellings) and I read it as the fan-out working. Fixed by round-robin interleaving across variants before truncation; live at the default limit now returns 9 / 9 / 7 across three spellings.

**2. Hard 25-per-spelling cap with the capped-set signal discarded (audit, CONFIRMED).** `per_term` was hardcoded and unreachable from the CLI, so `--limit 100` still returned 25 of an available 64, and nothing told the caller the set was capped — the exact trap this thread's own Hard Rule 13 counting clause names, shipped in the same diff. Fixed: page size now follows `--limit` (clamped to the API maximum of 200), and every hit carries `term_total` from OpenAlex's `meta.count`. Live output now exposes totals of 8 / 32 / 64.

**3. One bad `--also` term aborted the whole fan-out (audit, CONFIRMED).** A comma or other filter-grammar character yields HTTP 400 and discarded every already-gathered result. Fixed two ways: reserved characters are stripped from terms before the query, and a per-variant failure is now collected rather than fatal — the working spellings' results survive, a warning names the failed ones, and only an all-variants failure raises.

**4. Valid JSON of the wrong shape (CodeRabbit, CONFIRMED).** The docstring promised a broken query could never be reported as "no results", but only transport and parse failures were guarded. Reproduced all four cases: a list payload and a malformed `results` value each raised a bare `AttributeError`; a response missing `results` returned **zero hits silently**. Fixed with an explicit shape check in `_openalex_fetch`; four parametrised tests cover it.

**5. The test named for finding 1 passed straight through it (audit, CONFIRMED).** It asserted only that both requests were *issued*, never that a later variant's work reached the caller — green while the behaviour it was named for was broken. This is the "guards the plumbing, not the behaviour" trap. Rewritten to assert a later spelling's work survives truncation, plus a second test asserting one hit from each of three spellings under a tight limit.

**6. "`appamāṇa` returns zero" was false (audit, CONFIRMED).** Live `meta.count` is **2**, not 0. I took the figure from a probe agent's report and propagated it into four user-facing places without checking — against the standing rule that every concrete count in user-facing output must be read from the source. Corrected everywhere to the real figures (2 against the Sanskrit cognate's 8); the argument for `--also` survives, the number did not.

**7. Hard Rule 13 claimed "the helpers cap at `--limit 20`" (audit, CONFIRMED).** Already wrong about the newest helper in the same diff, which defaults to 25. Reworded to state each helper's own default and to point at `term_total`.

**8. The mailto default was a hardcoded personal address (audit, CONFIRMED).** Every other installation would have sent it to OpenAlex on every request, and the error path echoed it into stdout. Now read from `VICAYA_OPENALEX_MAILTO` with no default — unset, the parameter is omitted and the API still answers. Documented in Phase 4a and covered by a test. `.env.example` was deliberately **not** edited (standing rule: never modify env files) — adding a line there is a one-line follow-up for the user.

**9. Hard-wrapped prose in two bullets this thread wrote (audit, CONFIRMED).** Against the project rule and the spec's own constraint. Unwrapped.

**CodeRabbit's finding on `per_term` vs `limit` was accepted in substance but not in form.** Its proposed fix — collapse the two parameters — would have deleted a deliberate knob; the real defect was that the CLI never passed the page size. Fixed at the call site, as finding 2 above.

### State after review round 1

469 passed, 1 skipped (up from 455 — 14 more tests). `ruff` and `pyright` clean on both changed Python files. Heading text and count unchanged from baseline (135); fences 152, even. A third independent review is expected and will be against pre-fix code, so its findings need mapping onto this list before being acted on.
