# Rejected imports from alphaXiv/OpenResearch

Recorded so the same imports are not re-proposed. Per `kamma/lessons.md` 2026-09-02: the useful output of a compare-and-improve thread is mostly a rejection list with reasons.

Source: https://github.com/alphaXiv/OpenResearch (MIT, Rust CLI + agent skills, "turn your coding agents into research agents"). Examined 2026-09-20: `SKILL.md`, `SYSTEM_PROMPT.md`, and the `orx-lit-review`, `orx-evidence`, `orx-reports`, `orx-experiment-tree`, `orx-agent-delegation` skills.

## 1. Cross-corpus scholarly retrieval (alphaXiv / OpenAlex / bioRxiv)

Their strongest concrete tool: four discovery primitives plus a ranked main-agent retrieval loop, no auth required.

**Rejected on 2026-09-20, then OVERTURNED the same day by an empirical probe. Deferred to its own thread — do not re-reject it on the reasoning below.**

The original rejection read: no run in `runs/TODO.md` reports failing to *find* scholarship (the three academic/scholarly hits are all about *writing* attributions from memory, #96/#97), while two untriaged runs credit the local library index with finding exactly the right sources — Anālayo's DĀ 26 study and his brahmavihāra articles, Martini on the appamāṇas (`runs/20260920-023254.md`), and Drummond's chapter comparing Gendlin's Focusing with Goenka's vedanānupassanā (`runs/20260920-100058.md`).

**That reasoning was wrong, and wrong in a way this thread's own Hard Rule 13 names:** absence of a complaint is not evidence of coverage, and absence in the source you happened to open is not absence. Nobody reports a monograph they never knew existed.

Two probes were run against the live OpenAlex API (free, no auth, `api.openalex.org`) using the exact topics of those two runs as baselines. Both found real material the local library did not hold:

- **Canonical topic (brahmavihāras as a basis for insight).** Maithrimurthi, *Wohlwollen, Mitleid, Freude und Gleichmut* (Heidelberg 1999, digitised 2025, DOI `10.11588/fid4sarep.00004644`, open access) — the standard book-length history-of-ideas treatment of the pre-Buddhist-origins question, which is precisely half of what that run was asking. And Shulman, "An Ethical Samādhi: Brahma-vihāra Meditation and the Flexible Early Buddhist Path", *Mindfulness* 2025 (DOI `10.1007/s12671-025-02597-6`, CC-BY, PDF verified downloadable) — on the other half. Also Heim on Buddhaghosa's phenomenology of love and compassion, for the Visuddhimagga IX section (paywalled), and a 2023 Anālayo immeasurables article later than the two the baseline had.
- **Cross-tradition topic (Gendlin's Focusing vs vedanānupassanā).** Drummond 2007 in *Buddhist Studies Review* (DOI `10.1558/bsrv.v23i1.113`, open access) — the same author's peer-reviewed journal version of the baseline book chapter, separately citable with a substantial abstract; plus the 2018 *Contemporary Buddhism* vedanā special issue (reissued as DOI `10.4324/9780429345067`), six articles the run had none of.

**But the probes also establish hard constraints, and a naive integration would deliver mostly noise.** These are the requirements any future thread must build to:

1. **Diacritics do not fold, and the sets are disjoint in both directions.** `brahmavihara` returns 64 hits, `brahmavihāra` 32, `brahma-vihara` 37 — not nested. Anālayo's Tevijja article appears *only* under the diacritic form; Sharma and Shaw appear *only* under the plain form. Author names too: `Analayo` → 12 works, `Anālayo` → 307.
2. **The natural Pāḷi spelling is the weakest key.** `appamāṇa` returns **2** hits against the Sanskrit `apramāṇa`'s 8 (live counts re-checked 2026-09-20; the probe's original "zero" was wrong and was propagated into four places before an independent audit caught it). Martini's article is in the index under the mangled string "Appamāas" — the ṇ eaten on ingestion. The Sanskrit cognate `apramāṇa` works (8 hits, 6 on topic). The route to Pāḷi material is through Sanskrit, English glosses, or adjacent terms.
3. **Free-text `search=` is worthless; `title_and_abstract.search` is where every useful hit came from.** `search=brahmavihara+early+Buddhism` → 111 hits, 0–2 on topic, swamped by clinical mindfulness, business ethics and Myanmar politics. `search=Analayo+brahmavihara` → 14 hits, not one work by Anālayo. Narrow technical forms run 38–75% useful (`Tevijja` 5/13, `apramāṇa` 6/8); plain-English forms run 0–8% ("four immeasurables" → 105 hits, 1 relevant, ~20 psychometrics papers; "divine abodes" → 7 Hebrew Bible papers on God's dwelling-place).
4. **So the channel needs a term-expansion layer or it must not be built at all:** plain form, diacritic form, hyphenated form, Sanskrit cognate and English gloss, all fanned out, all against `title_and_abstract.search`.
5. **Full text is mostly unreachable by script.** Canonical probe: 11 of 21 relevant hits flagged open access, and two spot-checked PDFs fetched cleanly — but the Maithrimurthi monograph sits behind a proof-of-work anti-bot gate (a browser gets it, `curl` gets a challenge). Cross-tradition probe: of 11 relevant hits, 2 flagged open access and **both returned 403 to automated retrieval** — machine-readable full text 0 of 11. Treat this as an abstract-and-metadata channel that names sources for the user to fetch, not a text source.
6. **It supplements, it does not beat the library on its own ground.** The single most relevant canonical item OpenAlex returned (Anālayo on DĀ 26) was already in the local library. The gain is at the edges — foreign-language monographs, very recent journal articles, and the modern scholarly context around a term.

**Verdict: BUILT IN THIS THREAD**, to requirements 1–5, at the user's direction. `search-openalex` ships in `tools/research_sources.py` with 12 tests and a Phase 4a subsection. A live fanned-out call returns 81 unique works from four spellings of one term and reproduces both probe findings. arXiv and bioRxiv remain useless for this field and were not built; OpenAlex is the only relevant corpus of OpenResearch's three.

## 2. Modularizing the skill into lazily-loaded sections

OpenResearch keeps a deliberately short core skill carrying cardinal rules and a command index, with every procedure in a module loaded on demand (`orx skill <name>`). `skill/vicaya/SKILL.md` is ~2,770 lines loaded in full every run, so the saving looked large.

**Rejected on prior art — this was built and then deleted.** `kamma/archive/20260602_vicaya-staged-skills-section-router` built four staged router skills that extracted exact sections by heading text; its own spec records an *earlier* failed attempt using "concise reference files", which drifted into a paraphrased alternate workflow. `kamma/archive/20260618_remove_staged_routers` then deleted all four as redundant once the canonical skill moved to single-session sub-agent dispatch. Per-phase sub-agents already bound context per phase (`SKILL.md` "Sub-agent dispatch": each agent reads the shared preamble plus only its own phase's sections), which is the same saving without a second source of truth to keep in sync.

## 3. Main agent must not delegate the retrieval loop

OpenResearch: "You are the retrieval ranker. Call the primitives yourself… Never delegate this loop to a sub-agent." Their argument is that ranking needs the whole candidate set visible to the judging agent.

**Rejected — contradicts an architecture adopted for a verified reason.** `SKILL.md` records that a sub-agent running every phase "accumulates full SKILL sections + the growing scratch + verbose search dumps… and crashes with 'Prompt is too long' mid-run", with no warning before it dies. Delegation exists to prevent that, and vicaya already compensates for the fidelity loss the rule is aimed at: top-citation re-verification after each agent, `scratch-verify` content checks, and the rule that a completion-report claim with no matching logged tool call is treated as false until re-run. `kamma/archive/20260520_ars-borrow` separately rejected multi-agent restructuring on portability grounds.

## 4. Per-completion dispatch loop instead of a wait-for-all barrier

Their loop returns on the first completion, reconciles against full state, and refills the freed slot, rather than waiting for a whole batch.

**Rejected — unevidenced.** Vicaya batches spot-checks after a parallel wave and no run reports a problem with the barrier; the parallel-wave sanction (issue #102) records three real runs with zero misfiling. Their companion insight — that the wait signal is not the source of truth and full state must be re-read on every wake — is already vicaya's rule: never trust a completion notification's own phase ID or status claim; confirm from the scratch.

## 5. The experiment-tree model (frozen nodes, stacked bushes, repair cap)

A project as a tree of experiment nodes: a node freezes once a run answers it, children branch off winners, two non-answering runs on one node then ask the user.

**Rejected — no analogue.** A vicaya run produces one note, not a tree of measured variants. The one transferable fragment — never re-run a query that already failed — was taken, and lives in the Phase 0 `Target:` bullet as round discipline; `runs/20260902-133109.md` had independently rediscovered it ("several retries wasted" on the same failing FTS string).

## 6. A standalone "result caps" hard rule

OpenResearch's "truncated output is not evidence of absence" mapped onto a real local mechanism: `search_canon` and its siblings take `limit: int = 20` and hard-truncate (`tools/research_sources.py:151`, `219–221`), and every search recipe in the skill passes `--limit 20`, so a result holding exactly 20 hits is a capped set.

**Rejected as its own rule; kept as a clause.** The failure mode was found by reading the helper's source, not reported by any run — inventing a defect and then fixing it is its own risk. It earns a clause inside Hard Rule 13 only because #116's proposed fix says to "count" family members, and a count read off a capped set would be wrong.

## Note on backlog #116

This thread implements #116's proposed fix (generalize the concept-family absence sweep from the series format to Phase 2). `runs/TODO.md` was deliberately not edited — closing the item belongs to `/vicaya-improve`'s triage.
