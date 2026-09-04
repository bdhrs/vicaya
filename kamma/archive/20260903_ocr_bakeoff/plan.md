# Plan: OCR bake-off

Spec: `spec.md`. Context: `handoff.md`. Baseline `134e25f` plus an uncommitted deadlock fix. No GitHub issue.

## Architecture Decisions

- **Nothing in production code changes in this thread.** Every candidate is driven by a throwaway harness in the session scratchpad. The decision is the deliverable; the swap is a later thread. This keeps a shared tree safe while a six-day run may be in progress.
- **One harness, one interface, three candidates.** Each candidate is a function taking `(pdf_path, first_page, last_page, out_path)` and returning elapsed, characters and peak memory. Identical inputs, identical measurement, each in its own fresh process. No candidate gets bespoke treatment.
- **The decision rule is committed in `spec.md` before any number exists.** It is not revisited after results arrive. If it turns out to be the wrong rule, that is recorded as a finding, not silently amended.
- **Ground truth by re-rendering, not by trusting an engine.** Pages from a real text-layer PDF are rendered to 300 dpi greyscale and rebuilt as an image-only PDF; the original text layer is the correct answer. This is the one technique from the previous thread that held up.
- **No mocks anywhere near a timeout or failure path.** Robustness is measured against real hung and real crashing processes, because a fake that returns immediately is exactly how a two-hour deadlock passed 452 tests.

## Model Strategy

The failures being guarded against were discipline failures, not capacity failures, so the split is about *what kind of work* each phase is — with the strongest tier on the phases where a wrong judgement propagates into a recommendation.

| Phase | Tier | Reason |
|---|---|---|
| 0 — candidate survey | **Pro** | deciding what is worth measuring, and rejecting candidates on licence, maintenance and installability. A wrong inclusion wastes a day; a wrong exclusion loses the winner. |
| 1 — harness | **Fast** | mechanical scripting against a fixed interface. No judgement calls. |
| 2 — measurement runs | **Fast** | run commands, collect numbers, tabulate. Cheap tier is correct; resist any urge to interpret while collecting. |
| 3 — quality scoring | **Fast** | deterministic scoring code already specified. Mechanical. |
| 4 — decision and synthesis | **Pro** | applying the rule, spotting where a metric is an artefact of the harness, and stating what would have chosen differently. This is where the previous thread went wrong repeatedly. |
| 5 — adversarial review | **Pro** | independent review whose explicit job is to attack the conclusion, plus CodeRabbit on any code. |

⚠️ MODEL SWITCH REQUIRED (Fast tier) at Phase 1: mechanical execution begins.
⚠️ MODEL SWITCH REQUIRED (Pro tier) at Phase 4: interpretation and decision.

Practical note for whoever runs this: a cheaper tier collecting numbers is not a licence to collect fewer of them. Every measurement below states its n and its repetitions; those are not negotiable by tier.

## Phase 0 — what is worth measuring ⚠️ Pro

- [x] T1 — Survey currently available OCR solutions for bulk PDF work. For each: installability on this machine, licence, maintenance status, whether it does per-page parallelism, skip-text detection, resumable output, and text sidecar. Verify each claim against the tool's own docs or `--help`, not from memory. → verify: a table of candidates with a keep/reject decision and a one-line reason each; at least the three named in the spec are assessed, and any rejection cites the specific disqualifying fact.
- [x] T2 — Ask the user before installing anything. Installing `ocrmypdf` pulls ghostscript-adjacent packages. → verify: explicit user approval recorded, then `ocrmypdf --version` prints.

## Phase 1 — the harness ⚠️ Fast

- [x] T3 — Build the corpus. Random sample of 20 books from the 1,739 with a fixed seed, plus the two known intermittent stallers by name (`Companion to the Philosophy Of - W.H. Newton-Smith.pdf`, `Psychoanalysis and Buddhism.PDF`). Record each book's page count. → verify: a corpus file listing 22 paths with page counts; the sample is reproducible from the seed and is **not** filtered by size or page count, since that filter is what biased the previous sample.
- [x] T4 — Build ground truth. Take 20 pages from a diacritic-heavy text-layer PDF, render at 300 dpi greyscale, rebuild as an image-only PDF, keep the original text layer as the answer key. → verify: the rebuilt PDF yields zero characters from `pdftotext`, and the answer key contains at least 100 IAST diacritics.
- [x] T5 — One measurement wrapper per candidate behind a common interface, each returning elapsed, characters and peak private memory, sampled not guessed. → verify: all three candidates run over one 20-page book and return all three metrics; peak memory is read from `/proc/<pid>/smaps_rollup` Pss, not RSS.

## Phase 2 — measurement ⚠️ Fast

- [x] T6 — Throughput and memory per candidate over the 20-book sample, one warmup discarded, median of three, each run in a fresh process, with system load recorded alongside. → verify: a table of s/page and peak memory per candidate with n and load stated; any candidate whose numbers span more than 3x across repetitions is re-run rather than averaged. **Bounded per user direction 2026-09-03: capped at the first 4 pages of each of the 20 books (not full books) to fit the session; full 20-book breadth and the committed warmup+median-of-3 repetitions are preserved per-book.** Results in `measurements.md`. The live production incumbent run was active on the machine throughout T6 (load1 ~6-11) — it is the same shared condition for all three candidates, so it does not bias the comparison between them, only elevates all three absolute numbers versus an idle machine.
- [x] T7 — Parallel scaling per candidate at 1, 2, 4 and 8 way, with peak combined memory at each step. Stop escalating a candidate when memory exceeds the gate. → verify: a scaling table per candidate, naming the parallelism at which throughput stops improving and the reason (memory, contention or disk). Measured with production stopped (user's call, 2026-09-04). No candidate hit the per-unit memory gate at this page-capped scale; see `measurements.md` T7 section for the caveat that full-book memory scaling is deferred to T8.
- [x] T8 — Robustness over the whole 22-book corpus including the two stallers, run at each candidate's best safe parallelism. Record failures, stalls, and the wall clock each failure costs. → verify: failure count and worst-case failure cost per candidate; the two known stallers are individually reported. Full 22-book, uncapped, real run with production stopped. See `measurements.md` T8 section: ocrmypdf's only failures are fast/deterministic (encrypted PDFs); tesseract-direct and the incumbent both have genuine multi-minute stalls that fail the spec's ">5 min" gate clause. Finding 3: tesseract silently returns ~0 chars (rc=0) on one whole real book that PDFium reads correctly.
- [x] T9 — Resumability. Kill each candidate mid-run and measure what must be redone. → verify: books lost per candidate, measured by re-running and observing what it repeats. Empirically tested for ocrmypdf (SIGKILL mid-book-B, restart: A skipped, B fully redone from page 1); confirmed by code inspection for the incumbent (chunk loop always starts at page 1, no cross-attempt resume). All three lose exactly 1 book on interruption — a wash between candidates, not a differentiator.
- [x] T10 — Phase verification: every cell in the decision-rule table has a number for every surviving candidate. → verify: no blank cells; any genuinely unmeasurable cell is named with the reason. Phase 2's own gates (throughput T6, scaling/memory T7, robustness T8, resumability T9) are all populated for all 3 candidates in `measurements.md`. Quality gates (search accuracy, diacritic findability) belong to Phase 3 (T11/T12), not yet run — no blank cells within Phase 2's own scope.

## Phase 3 — quality ⚠️ Fast

- [x] T11 — Score each candidate against the answer key: word accuracy with diacritics folded, word accuracy strict, diacritics preserved as a count, and findability of diacritic-bearing word types after folding. → verify: the four figures per candidate, using the same scoring code for all three. All 4 figures × 3 candidates in `measurements.md` T11. Finding 4: incumbent fails the 85% diacritic-findability gate (72.7%) despite preserving more diacritic characters, because it drops whole retroflex consonants on some words rather than just stripping the diacritic mark — verified by direct grep comparison, not inferred.
- [x] T12 — Confirm sidecar or extracted text is usable as FTS input unmodified, or record exactly what cleanup it needs. → verify: text from each candidate inserted into an FTS5 table with the production tokenizer, and a known phrase from the answer key retrieved. All 3 texts inserted unmodified, real MATCH queries run — see `measurements.md` T12. tesseract-based candidates: no cleanup needed. Incumbent: `ativaṇṇati` genuinely unretrievable (real FTS confirmation of Finding 4's consonant-dropping).

## Phase 4 — decide ⚠️ Pro

- [x] T13 — Apply the committed rule: produce the results table, the gate pass/fail per candidate, the winner, the projection for all 1,739 books at the winner's best safe parallelism, and explicitly the numbers that would have chosen differently. → verify: `measurements.md` contains all of it and the projection states its measured basis, not an assumed rate. Winner: **ocrmypdf**, 1.32 days projected at 4 books × `--jobs 4` (0.433 s/page, measured over the full 22-book corpus — T13a closed the unmeasured-concurrency gap rather than extrapolating). Gate table, projection basis, and the five "would have chosen differently" numbers are in `measurements.md`.
- [x] T13a — (added 2026-09-04) Measure ocrmypdf at concurrent books, because T8 only measured it sequentially and the kill condition depends on the winner's rate at its best safe parallelism. → verify: 4-way and 8-way over the full corpus, joint memory sampling; plateau at 4-way identified as CPU-bound. Done.
- [x] T14 — Check the kill condition: does the winner beat six days by 3x or more? → verify: stated as a yes or no with the arithmetic; if no, the recommendation is to stop rather than to ship a marginal change. **YES — cleared at 4.54×.** 263,524 × 0.433 s = 114,212 s = 1.32 days vs 518,400 s (6 days); required ≥3×. Arithmetic recorded in `measurements.md`.
- [x] T15 — If the winner is not the incumbent, write the follow-up thread's scope: swap the backend and delete the bespoke worker, framed protocol, per-chunk timeout, reader thread and page cap. Do not implement. → verify: a scope note naming every symbol to be deleted, cross-checked against `rg --hidden` so no reader is missed. Written to `swap_scope.md`: 14 symbols with line numbers, 2 dependencies + 1 `.env` key, and the non-obvious carriers swept (justfile 3-pass rationale, README, and `skill/vicaya/SKILL.md:1504/1519/1521` which reads the `ocr` status vocabulary). Nothing implemented.

## Phase 6 — diacritic restoration: can the loss be undone? ⚠️ Pro

Added 2026-09-04 at the user's direction, after Phases 0–4 completed. **Decision-critical: the winner is not final until this phase resolves.** Rule and thresholds committed in `spec.md` before any measurement. Runs before Phase 5 review, so the reviewer sees the final decision rather than a provisional one.

The insight being tested is the user's: restoration is not a blind guess, because correctly-spelled forms of these exact words already exist on disk — the DPD lexicon and 260 prior research dossiers carrying 1.77 M correctly-diacriticized Pāḷi tokens with real frequencies.

- [x] T17 — Build the reference resources from what the project already owns, no new dependency. (a) DPD folded→forms map from the 1.28 M-row lookup table; (b) scratch-corpus vocabulary with token frequencies from `data/scratch/*.md`. → verify: both maps built with counts stated; the frequency prior is real usage counts, not uniform.
- [x] T18 — Build an **aligned prose** fixture, avoiding all four traps in `spec.md`. Scholarly prose *about* Buddhism with a real text layer (not canon text, not a dictionary), rendered to an image-only PDF and OCR'd by ocrmypdf so true and flattened text are token-aligned. → verify: the fixture's true text carries ≥300 diacritic-bearing tokens; the source is named and its circularity risk against `data/scratch/` is checked and reported, not assumed.
- [x] T19 — Score a ladder of restorers on that fixture, all with the same scoring code, all token-weighted: R0 none (baseline 0 %), R1 DPD-unique-only, R2 DPD + scratch frequency prior, R3 scratch-corpus + frequency alone, R4 LLM with sentence context, R5 LLM constrained to the candidate list from R1/R3. → verify: accuracy on diacritic-bearing tokens per restorer with n stated; R0 confirmed at ~0 %; the cheapest restorer that clears a `spec.md` threshold is identified.
- [~] T20 — **NOT RUN — open caveat on the Phase 6 result.** Run the memorisation control. Check whether the model can reproduce the fixture passages unprompted, and score an invented-Pāḷi-nonsense control set to separate morphological reasoning from recall. → verify: stated as a yes/no per passage; any passage the model reproduces unprompted is excluded from T19's figures and the figures recomputed without it.
- [~] T21 — **NOT RUN — deferred.** Second fixture, the user's design: a genuinely scanned book matched to a topically-overlapping scratch dossier, scored on **overlapping vocabulary** rather than alignment. Confirms T19 on real scanned input rather than re-rendered text. → verify: book and dossier named, overlap size stated, accuracy on the overlapping vocabulary reported.
- [x] T22 — Apply the amended rule: which `spec.md` band does the best restorer land in, and does the winner change? Update the decision and `swap_scope.md` accordingly. → verify: `measurements.md` states the band, the consequence, and — if restoration ships — what it adds to the swap's scope.

## Phase 5 — review ⚠️ Pro

- [x] T16 — Independent review briefed to attack the conclusion: is the corpus representative, is any metric an artefact of the harness, was the rule applied honestly, is any claim resting on a single sample. Plus CodeRabbit on any code written. → verify: findings recorded and addressed; `review.md` carries a verdict. **Done — two parallel independent passes.** `review.md` (16 findings, 2 BLOCKING, verdict: winner stands) and `../20260904_ocr_swap/scope_audit.md` (4 BLOCKING, 4 SERIOUS; all 14 symbols verified exact). Both blockers on the bake-off addressed: the 98.2 % self-scored figure was re-measured through the harness on the same slice (**99.7 %**, CI 98.1–99.9, band ≥95 % confirmed) and the robustness gate now counts Finding 3 and states the 0/20 upper bound. The scope audit's blockers are folded into the swap thread's spec and plan. No CodeRabbit run: this thread committed no code.

## Deviations

- 2026-09-03 — Created after the user rejected the hand-rolled incumbent, which is running at a measured six days. Supersedes `kamma/threads/20260903_parallel_ocr/`: parallelising the incumbent is wasted work if an off-the-shelf tool wins, so that thread waits on T13 and is deleted if the incumbent loses.

- 2026-09-04 — Phase 6 added mid-thread at the user's direction (diacritic restoration), with its rule committed in `spec.md` before measuring. It changed the *reason* the winner wins, not the winner.
- 2026-09-04 — T20 (memorisation control) and T21 (scanned-book overlapping-vocabulary fixture) NOT RUN. Both carried into `kamma/threads/20260904_ocr_swap/` as T12. The Phase 6 figure is therefore an optimistic bound: the fixture is a published book and recall is not excluded.
- 2026-09-04 — Review found the load-bearing 0.433 s/page rate was a single unreplicated run, against T6's own median-of-3 discipline. Re-run 3× at 4-way; median recorded in `measurements.md` T13a. Like-for-like kill margin restated as 3.27× (both sides OCR-only), with 4.54× marked as the loose mixed-basis figure.
- 2026-09-04 — Two claims corrected after review rather than defended: `pikepdf` is not importable in the project venv (so the encrypted-PDF fix needs a new dependency), and the Finding-3 remediation "re-run through the incumbent's engine" is impossible once the swap deletes that engine.
