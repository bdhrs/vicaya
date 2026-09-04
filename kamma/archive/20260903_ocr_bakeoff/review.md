# Phase 5 — adversarial review (T16)

Written 2026-09-04 by an independent reviewer briefed to attack the conclusion. Every number below was recomputed from the thread's own files, not taken from its summaries.

## VERDICT

**The winner stands — ocrmypdf is the right choice — but three of the thread's four headline numbers are overstated: the Phase 6 "98.2 %" must be withdrawn, the robustness gate hides a known total failure, and the kill condition's like-for-like margin is 8 %, not 51 %, on a single unreplicated run.**

---

## 1. BLOCKING — the 98.2 % restoration headline is not comparable to anything else in its own table, and it decides a committed band

`measurements.md:242` puts "Opus 5, context only, no lexicon — **98.2 %**, n=57" as the top row of the restorer ladder, and `:258` uses it to land the result in the spec's **≥ 95 %** band, whose committed consequence (`spec.md:43`) is that "quote fidelity ceases to be a cost". `handoff.md:14` promotes it to "the answer".

That row is not the same measurement as the four above it:

- **Different fixture slice.** `measurements.md:224` — the four scored models ran on the "Scored slice: 100 sentences, 303 diacritic-bearing tokens"; Opus ran on the "Self-test slice: 20 sentences, 57 tokens, drawn from a different part of the book". The slices are demonstrably different in composition: `:252` records that 5 of the 303 truth tokens (`VismṬ`, `CompṬ`, `VinṬ`) are PDF abbreviation artefacts "which no restorer can produce" — a hard 98.35 % ceiling on the scored slice. The 57-token slice evidently contains none. So the two numbers are not on the same scale by construction.
- **Different administration.** The four models went through a scripted harness with unaligned-token accounting. Opus scored itself, on a key it says was "withheld until after answering" — self-attested, unauditable, and its `unaligned = 0` (`:244`, against Haiku 33 / Sonnet 8 / DeepSeek 19) is exactly what you get when the candidate is also the aligner.
- **n=57.** One error. The thread's own Wilson CI (90.6–99.7, which I reproduce as 90.7–99.7) already crosses the 95 % band boundary, so even taken at face value the figure does not establish the band it is used to select.

**The best figure that actually went through the harness is 85.6 %** (DeepSeek, `:241`), Wilson 95 % CI **81.1–89.0 %**. Sonnet's 84.7 % gives 80.3–88.4 %. Both straddle the 85 % boundary. So the harnessed evidence places restoration in either the **85–95 %** band ("the swap must ship restoration, and quotes carry a stated residual error rate") or the **< 85 %** band ("restoration is not a fix… a real, permanent cost the user accepts explicitly"). It does not reach ≥ 95 % on any evidence that survived the harness.

Compounding it: **T20, the memorisation control, was never run** (`plan.md:71`) and the fixture is a published book (`measurements.md:267`). The one cell the entire band assignment rests on is the one cell with no control, no harness, and no replication.

**What would need to change.** Run Opus on the same 303-token slice through the same harness — this is the cheapest missing measurement in the whole thread (one batched call over 100 sentences) and it was skipped while a marked-NOT-RUN control was also skipped. Until then: demote 98.2 % to a footnoted feasibility signal, headline 85.6 % (CI 81–89), and state the band as **undetermined between "< 85 %" and "85–95 %"**. Both live options require the swap to ship restoration with a stated residual error rate — which `swap_scope.md` does not currently contain (see finding 9).

## 2. BLOCKING — the robustness gate omits Finding 3, and the swap deletes the only engine that could remediate it

Gate table `measurements.md:183` records ocrmypdf as "**2.5 % PASS** (43/1739 encrypted; 0 % with the verified fix)". Finding 3 (`:89–95`) is a *verified, reproduced, whole-book total failure*: "Survey of Vinaya Literature. Vol. I" (85 pages) returned **rc=0, 84 characters** for both tesseract wrappers, confirmed across 8 sampled pages and all 7 page-segmentation modes, on a book the incumbent read at 211,181 characters. That is a book "unrecoverably failed" in the plain sense of the gate's own words — and it is not counted in the gate cell. It was moved out of the gate and into "the numbers that would have chosen differently" (`:210`).

Counted, ocrmypdf's observed failure rate on this corpus is **3/22 = 13.6 %**, not 2/22, and the population rate of the Finding 3 mode is unknown. The gate cell should read "≥ 2.5 %, true rate unknown", not "2.5 % PASS… 0 % with the fix".

Worse, the stated mitigation is now impossible. `measurements.md:210` says to "re-run those through the incumbent's engine or inspect them" — but `swap_scope.md:32–34` deletes `pdf-inspector`, `onnxruntime` and `PDFIUM_LIB_PATH`. After the swap there is no second engine. `swap_scope.md:44` only requires *flagging* the book and recording "a distinguishable status"; there is no remediation path at all, so every Finding-3 book becomes a permanently unindexed hole.

**What would need to change.** Either (a) retain a minimal second-engine path for flagged books, or (b) state explicitly that Finding-3 books are permanently unindexed and bound the rate by measurement. The bound is affordable: at 0.433 s/page, a 100-book sample costs ~1.8 h of machine time against a 1.32-day full run. That single measurement would close both this and finding 4, and it was never attempted.

## 3. SERIOUS — the projection's entire basis (0.433 s/page) is a single unreplicated run, and the like-for-like kill-condition margin is 8 %

T6 committed to "1 warmup run discarded, then 3 kept runs" with a 3× re-run rule (`measurements.md:11`). **T13a, which produced the load-bearing number, states no repetitions at all** (`:147–159`) — one run per config. `handoff.md:9` describes it as "0.433 s/page measured over 2,868 real pages", which conflates page count with replication: 2,868 pages is one sample, not 2,868 of anything.

The kill condition is then evaluated on two different bases without noticing:

- `measurements.md:202` clears it at **4.54×** (6 observed days ÷ 1.32) — but the 6 days is a full production pass including DB writes and text extraction, while 1.32 days is explicitly OCR-only (`:167`). Mixed basis.
- The like-for-like ratio, both sides OCR-only, is **4.31 / 1.32 = 3.27×** against a required ≥ 3×. The thread states this at `:196` without noting the margin is **8 %**.

An 8 % margin on an unreplicated measurement is not a cleared gate. And a correction already visible in the thread's own data eats most of it: 85 of the 2,868 pages in the rate's denominator are the Finding-3 book, which produced 84 characters — i.e. ~3 % of the "pages OK" did no real OCR work while counting as throughput. Excluding them gives **0.447 s/page → 1.36 days → 3.17×**, a 5.6 % margin.

**What would need to change.** Re-run the 4-way config at least 3× and report the median with a spread, per the discipline T6 committed to. If the median lands above ~0.47 s/page the spec's own kill condition says stop. Also report the kill condition on the like-for-like basis as the primary figure, with the 4.54× as the loose one.

## 4. SERIOUS — B3 is unrefuted at low power, not established, and swap_scope already spends the finding

`handoff.md:11` and `swap_scope.md:58` state "zero stalls across 22 real books". That is **0/20 non-encrypted books, one attempt each** (T8, `:71–79`). Rule-of-three / Wilson upper bound on a 0/20 observation is **16.1 %** — against a 5 % gate. So spec assumption B3 (`spec.md:83`, "that ocrmypdf does not inherit the same intermittent stalls, since the failure may live in PDFium or the page images rather than the engine") is **not verified**; it is unfalsified at very low power.

The thread's own data proves one attempt cannot settle this: `measurements.md:85` records that the two named stallers *swapped* which one failed between candidates and passes, and `spec.md:75` establishes stalls as intermittent. Every robustness rate in the gate table — ocrmypdf 0 %, tesseract-direct 4.5 %, incumbent 18.2 % — is a single draw from an intermittent process, and none is presented with that caveat.

This matters most because `swap_scope.md:58` already spends the result: the justfile's third retry pass "loses its rationale" because ocrmypdf "showed **zero** stalls". Deleting a recovery mechanism on 0/20 single-attempt observations with a 16 % upper bound is the most consequential over-read in the thread.

**What would need to change.** Keep the third retry pass until a full production run demonstrates zero stalls. Restate the robustness cells as "0/20 observed, 95 % upper bound 16 %" rather than "0 %".

## 5. SERIOUS — the gate that nearly disqualified the winner is type-weighted, on a dictionary, in direct violation of two traps the spec itself names

`measurements.md:111` states the findability metric is "diacritic-bearing **word-type** findability after folding", and `:115–117` reports it as counts of 697 word *types*. The spec's own trap list says (`spec.md:53`): "**Type-level statistics.** A dictionary-only pass looked like 92.1 % accurate per word type and measured **15.1 %** token-weighted… **Every figure must be token-weighted**, with the type-level number reported separately if at all." And `spec.md:54`: "**Fixture bias.** The first ceiling measurement used pages of a Pāḷi *dictionary* — isolated headwords with no disambiguating context, the worst possible case."

The findability gate — the single cell that came within **3 word types out of 697** of eliminating the winner (`:192`; 85 % of 697 = 592.45, so 593 needed against 590 held) — is measured **over types**, on **20 pages of a Pāḷi-English dictionary** (`ground_truth.md:7`). Both defects the thread caught in Phase 6 are present, unremarked, in the Phase 3 gate that drove Phase 4.

The direction of the error is unknown but not negligible: type-weighting over-represents exactly the long rare compounds the thread showed behave differently from frequent short words, and a dictionary is all headwords. This cuts both ways — it also undermines the incumbent's decisive 72.7 % **FAIL** (`:182`), whose mechanism (Finding 4's dropped retroflex consonants) was observed only on dictionary headwords and may not generalise to running prose.

**What would need to change.** Re-score findability token-weighted, and on prose rather than a dictionary — the Phase 6 Buddhadhamma fixture already exists and is prose. Until then, mark the findability row as method-limited for all three candidates, not just as "indistinguishable from gate" for ocrmypdf.

## 6. SERIOUS — the "same engine, therefore noise" rescue is stated too strongly, and the thread's own robustness data contradicts it

`measurements.md:198` calls this "the load-bearing judgement of the decision": ocrmypdf and tesseract-direct "are the same OCR engine… their findability difference is 1.0 percentage point, z = 0.53 — statistically indistinguishable, exactly as two runs of one engine should be."

Two problems.

**(a) It is not two runs of one engine — only the recogniser is shared.** ocrmypdf rasterises via ghostscript at its own computed DPI; tesseract-direct rasterises via `pdftoppm -r 300` (`ground_truth.md:12`, `survey.md:10`). Different rasteriser, different DPI policy, therefore different input images and genuinely different achievable accuracy. The thread's own robustness pass proves the wrappers diverge materially on real input: on "Companion to the Philosophy Of", tesseract-direct stalled the full 1800 s recovering zero text while ocrmypdf completed it in 438.2 s (`:84`). You cannot claim the wrappers are interchangeable for quality and sharply different for robustness from the same evidence.

**(b) The z-test is the wrong test, and irrelevant either way.** Both candidates were scored on the *same* 697 word types, so the data are paired; a two-proportion z-test on paired data is invalid (McNemar on discordant pairs is the correct test). More importantly, the gate is **absolute** (≥ 85 %), not comparative — how ocrmypdf compares to tesseract-direct has no bearing on whether ocrmypdf clears 85 %.

**Was the rule bent?** Partly, but the escape is legitimate and the thread found the right door without naming it. `spec.md:19` does say "a candidate failing any gate is out regardless of speed" — and on point estimates ocrmypdf is out. But `spec.md:58` anticipates exactly this: "If no candidate clears the gates, the recommendation is the fastest gate-passing candidate at reduced quality, stated as such." All three candidates fail at least one gate, so that clause governs and ocrmypdf is the fastest of them. The thread reached the right answer via the wrong argument.

There is also a point in the thread's favour it never made, and should: the 85 % threshold itself was calibrated in `spec.md:24` against "measured incumbent 81.8 %, tesseract 87.9 %" — numbers Finding 4 (`:131`) subsequently **overturned** (72.7 % and 85.7 %). A threshold set to sit between two figures now known to be wrong has no authority to decide a 0.35 pp question in either direction. That is the honest defence.

**What would need to change.** Replace the "same engine" argument with the `spec.md:58` clause plus the threshold-provenance point, and drop the z-test.

## 7. SERIOUS — the incumbent's 4.31-day projection is a coincidence used as corroboration, and its derivation appears nowhere

`measurements.md:175` calls the incumbent projection reproducing the user's six days "**the main evidence the harness and projection method are sound**". It is not evidence of that at all, for two reasons.

**The harness did not produce it.** The cell reads "3.53 days/pass × 1.22 passes" (`:172`). That expression is derived nowhere in the thread. Reverse-engineered, 3.53 days over 263,524 pages is **1.157 s/page** — i.e. the inherited "1.18 s/page warm and unloaded" figure from `spec.md:75`, and 1.22 ≈ 1/(1 − 0.182), the retry multiplier from T8's stall rate. So the number is an inherited rate times a fudge factor, not a measurement from this thread's harness. Agreement between it and the user's observation says nothing about whether the harness or the ocrmypdf projection is sound.

**The choice of inherited rate manufactures the agreement.** `spec.md:75` establishes *two* incumbent rates: 1.18 s/page warm, and **2.9 s/page in production**. The production figure is the one comparable to a production six-day observation. Using it: 263,524 × 2.9 × 1.22 = **10.8 days**, nearly twice the observed six. Using the warm figure: 4.31 days, 72 % of observed. Whether the projection "independently corroborates" the user depends entirely on which of two established rates you pick, and the thread picked the one that lands nearer six without saying it had a choice.

**The data to do this properly was collected and not reported.** T8 ran the incumbent over all 22 books, uncapped, at its real 3-way production concurrency, on an idle machine (`:73`). That run's wall clock — the incumbent's measured s/page from this thread's own harness, directly comparable to T13a's 0.433 — is not in `measurements.md`. Its absence is conspicuous, since it is the one number that would make the head-to-head apples-to-apples.

**What would need to change.** Report the incumbent's measured s/page from T8, use it for the projection, and drop the corroboration claim or restate it as "consistent with the observation under one of two established rates". The winner does not change — the incumbent loses on four gates independently of its speed — but the method's claimed validation does not exist.

## 8. SERIOUS — B5 was never verified: every quality number comes from re-rendered clean digital text, not from a scan

`spec.md:85` lists as assumed-and-not-verified: "**B5** that no candidate's quality falls below the gates on this corpus specifically — Pāḷi diacritics, 19th-century scans, two-column journals."

All quality figures in the gate table (`:181–182`) come from a single fixture: 20 pages of one modern dictionary with a live text layer, rendered at 300 dpi greyscale and reassembled as an image-only PDF (`ground_truth.md:7–13`). That is the *easiest* possible OCR input — clean digital glyphs, uniform rendering, no scanner noise, no skew, no bleed-through, no 19th-century typography. **Zero quality measurement in this thread was performed on a genuine scan**, which is what all 1,739 target books are. The corpus contains two-column journals and old scans (`corpus.md:21,23,26`) but no ground truth was built for any of them.

B5 remains unverified, yet the gate table presents PASS/FAIL as established fact and `plan.md:48` (T10) claims "no blank cells". A gate whose input distribution differs this sharply from production is a gate cell with a footnote, not a number.

**What would need to change.** State plainly in the decision that all quality gates were measured on re-rendered digital text and that B5 is unverified. A cheap partial check: hand-verify one page of a genuine two-column scan against each candidate's output.

## 9. SERIOUS — T22 is marked done but did not update swap_scope.md, which still contradicts the Phase 6 conclusion

`plan.md:73` (T22) verify clause: "Update the decision and `swap_scope.md` accordingly… if restoration ships — what it adds to the swap's scope." It is marked `[x]`.

`swap_scope.md` was last written 14:16; `measurements.md`'s Phase 6 section 15:09. It was not updated. It still asserts, at `swap_scope.md:70`: "**Quote fidelity regresses and there is no fix in this scope.** ocrmypdf preserves 0 % of IAST diacritics… the user should know this is the price." That is the exact claim Phase 6 was run to overturn. §3's "two mandatory behaviours" contains no restoration item.

Under the corrected band (finding 1), `spec.md:44` requires that "the swap **must ship restoration**, and quotes carry a stated residual error rate" — a third mandatory behaviour that is absent from the swap's scope entirely.

**What would need to change.** Either finish T22 or unmark it. `swap_scope.md:70` must be rewritten and §3 must gain a restoration item with the residual error rate stated.

## 10. SERIOUS — T19 is marked done with one specified restorer missing, and it is the one the verify clause asked for

`plan.md:70` (T19) specifies six restorers: "R0 none… R1 DPD-unique-only, R2 DPD + scratch frequency prior, R3 scratch-corpus + frequency alone, R4 LLM with sentence context, **R5 LLM constrained to the candidate list from R1/R3**", and requires that "the cheapest restorer that clears a `spec.md` threshold is identified".

The results table (`measurements.md:233–242`) contains R0–R3 and four bare LLMs (R4). **R5 is absent.** T19 is marked `[x]`. No cheapest threshold-clearing restorer is identified anywhere.

R5 is not an incidental row: it is the hybrid that would supply the model with the frequency prior's candidate list, and `:250` identifies the prior's residual errors as "almost pure grammar… final vowel length… that a context-free prior structurally cannot make **and a model reading the sentence can**". R5 is precisely the combination the thread's own error analysis points at, and it is the plausible path to a genuine ≥ 95 % that does not depend on the withdrawn n=57 figure.

**What would need to change.** Run R5 on the 303-token slice, or unmark T19 and record R5 as not run.

## 11. SERIOUS — the restorer ladder compares rows scored on different token populations

`measurements.md:233–242`: R0–R3 report **n = 1,551**; the four LLM rows report **n = 303**. The fixture section (`:224`) defines only one "Scored slice: 100 sentences, 303 diacritic-bearing tokens". Where the 1,551 tokens come from, and whether the 303 are a subset of them, is never stated.

So the headline claim of Phase 6 — that a model (85.6 %) beats the best lexical restorer (72.2 %) by 13 points — compares two figures measured on **different token sets of different sizes**, with no evidence the 303-token slice is representative of the 1,551. The n values are disclosed per row, but the non-comparability is not.

**What would need to change.** Re-score R0–R3 on the same 303-token slice, or state which set is a subset of which and re-report the ladder on one common denominator.

## 12. MINOR — the "43 encrypted books, 0 % with the fix" claim over-reads what was measured

`measurements.md:38` scans the population with `pikepdf`'s `pdf.is_encrypted` and reports "**43 of 1,735 (2.5 %)** are encrypted **this way**" — "this way" meaning empty-user-password, owner-permissions-only. But `is_encrypted` is True for *any* encryption, including a real user password; it does not distinguish the two. If any of the 43 carry a genuine password, `pikepdf.open()` raises and the mitigation fails for those books.

The mitigation itself is verified on **n=1** (`:40`, Chanakya). The second encrypted book in the sample, Winternitz, was never decrypt-tested despite being on disk and identified. Yet `:183` claims "**0 %** with the verified fix" for all 43.

**What would need to change.** Attempt `pikepdf.open()` on all 43 (seconds of work) and report how many actually open with an empty password. Test the fix on Winternitz too.

## 13. MINOR — "CPU-bound at 4-way" is asserted, not demonstrated, and the swap is told to use that number

`measurements.md:157`: "Throughput plateaus at 4-way, and the reason is CPU contention, not memory or disk: 4 books × `--jobs 4` is 16 concurrent tesseract workers on 22 cores". No CPU utilisation was measured. Two other explanations fit the same data equally well:

- **Ragged tail.** With 20 books and a right-skewed size distribution (two books ≥ 456 pages carry 36 % of the sample's pages), the 4-way run's finish is underutilised, while the 8-way run is a single wave whose wall clock is just the longest book under 32-way oversubscription. The two configs are structurally different schedules, so "0.433 → 0.438, a 1 % difference well inside noise" is comparing shapes, not rates — and with n=1 each, "noise" is unquantified.
- **A serial per-book stage.** Going from 4 workers (sequential, `--jobs 4`) to 16 gave only **2.09×** (2593 s → 1243 s) on 22 free cores. Perfect scaling would be 648 s. That shortfall smells of a serial stage — ghostscript rasterisation, and the PDF assembly and image-optimisation stages that `swap_scope.md:50` itself notes are visible on every book — not of core exhaustion.

This matters because `swap_scope.md:48` instructs the follow-up thread to use exactly 4 × `--jobs 4`. If the limit is a serial per-book stage, then *more books × fewer jobs each* (8 × `--jobs 2`, same 16 workers) would be faster, and that configuration was never measured. In steady state over 1,739 books the tail vanishes, so the real production rate is probably **better** than 0.433 — the projection is conservative in direction, but the recommended parallelism may be wrong.

**What would need to change.** Sample CPU utilisation during one 4-way run, and measure 8 × `--jobs 2` before fixing the production configuration.

## 14. MINOR — assorted measurement artefacts and inconsistencies still uncaught

- **"Affects all three candidates identically" is refuted by the thread's own data.** `measurements.md:7` and `plan.md:44` claim T6's shared production load "affects all three candidates identically". The load1 medians in the same table (`:15–17`) are 7.00 / 6.27 / **9.44** — the incumbent was measured under 50 % higher load than tesseract-direct. Harmless (T6 is non-load-bearing, and the bias runs against the incumbent, which still came out fastest there) but the sentence is false as written.
- **T6's throughput table is misleading and its ordering is inverted relative to the decision.** At the 4-page cap, T6 (`:15–17`) makes the incumbent look **2× faster** than ocrmypdf (1.68 vs 3.42 s/page); T13a measures ocrmypdf at 0.433. The cap is disclosed (`:23`) but the table is still headed "throughput" and a reader could quote it.
- **"Worst single-failure cost" is censored at the backstop.** The 1800.1 s and 1519.6 s figures (`:78–79`) are properties of the chosen 1800 s timeout, not measured natural durations. Both fail the > 5 min clause regardless, so no impact — but they are ceilings, not measurements.
- **tesseract-direct's memory gate cell is unsourced.** `:185` gives "~900 MB PASS". No T6/T7 figure supports it: T7 shows 97–108 MB/unit and T6 a 140 MB max peak. The only ~900 MB number in the thread is the 899 MB Chanakya outlier from a 4-page-capped run (`:19`). Passes either way, but the cell's provenance is wrong.
- **Asymmetric bases in the memory gate.** ocrmypdf's PASS (488 MB) is a fresh uncapped full-book measurement; the incumbent's FAIL (5.0 GB) is an inherited production figure the spec forbade re-measuring (`:63`, `spec.md:107`). One of the incumbent's four gate failures therefore rests on evidence generated outside this thread. Plausible and probably correct, but it is not like-for-like.
- **Population figure drifts between 1,735 and 1,739.** `corpus.md:8` sampled from 1,735; `measurements.md:38` scans 1,735 and reports 43/1,735; `:183` writes the same 43 as "43/1739". Trivial.
- **T10's "no blank cells" is false for the final decision table.** `plan.md:48` narrows T10 to "Phase 2's own scope", which is defensible for T10 — but the decision table then ships with tesseract-direct's rate cell reading "sequential × 4 workers (**concurrent not measured**)" (`:173`), which is exactly the cell the decision rule requires ("projected wall clock… at its **best safe parallelism**", `spec.md:19`).

## 15. On the asymmetry that tesseract-direct was never measured at concurrent books — it does not change the ranking

Question asked, answered plainly: **no, it does not matter to the winner.** ocrmypdf got a dedicated concurrency pass (T13a) while tesseract-direct's projection uses an unscaled sequential rate (`:173`), which is a genuine methodological asymmetry — and it does inflate the "1.8× *slower* than the incumbent" claim. If tesseract-direct scaled like ocrmypdf did (2.09×), its rate would be ~1.69 s/page → 5.2 days, and the prior thread's own measured 1.41 s/page at 10-way (`spec.md:65`) implies ~4.3 days, i.e. roughly tied with the incumbent rather than 2.5× worse. Second and third place are therefore not established.

But tesseract-direct is eliminated by the robustness gate's > 5 min clause on a real 30-minute zero-recovery stall (`:84`, `:184`), which no amount of concurrency fixes, and it is 3.9–8× slower than ocrmypdf for identical recognition work on every basis measured. The ranking of first place is unaffected.

## 16. Attacks that failed — these parts of the projection hold up

Stated so the verdict is calibrated, because I went looking for these and did not find them.

- **The sample's size distribution is a good match, and the residual bias is conservative.** Population median 94, mean 153 (`spec.md:74`); the 20 measured books have median **93.5** and mean **143.4** (recomputed from `corpus.md`). Per-page rate in this sample *improves* with book size — the 587-page book ran at 0.746 s/page against the sequential 0.904 average, because fixed startup dominates the small books — so a sample mean slightly *below* the population's makes the projection conservative, not optimistic. The real gap is coverage of the upper tail: the sample's max is 587 against a population max of 1,678, so no book above 587 pages was ever measured, and ocrmypdf's memory and time at 1,000 pages with `--output-type pdf` are extrapolations. With an 8.4× memory margin that is a low risk, but it is unstated.
- **Excluding DB writes does not flatter ocrmypdf.** The exclusion is symmetric in text volume, and it actually runs *against* ocrmypdf: the 0.433 s/page includes writing a full output PDF per book plus image optimisation (`swap_scope.md:50`), work the incumbent never does and the production path can drop. The exclusion is a genuine like-for-like basis. The mixed-basis problem is in the *kill condition*, not the projection (finding 3).
- **`--force-ocr` was used** (`swap_scope.md:50`), which closes the obvious artefact — ocrmypdf silently skipping pages with a text layer and counting them as fast pages.
- **T7's combined-memory sum is disclosed as a conservative overestimate** (`:44`), and T13a replaced it with genuine joint sampling (`:149`). Correctly handled.
- **Finding 1 is the best-evidenced claim in the thread**: the 10 % sample rate was explicitly refused in favour of a full-population scan of 1,735 files, with the small-sample-luck reasoning spelled out (`:38`).
- **Finding 4 is properly earned.** It overturns the thread's own inherited assumption, states why (`:131`), and is confirmed by real FTS `MATCH` queries rather than by scoring code alone (`:140–145`). Overturning your own prior in the direction that complicates your preferred answer is the hardest thing on this list to do.
- **Every confidence interval I recomputed is correct**: 590/697 → 81.8–87.1; 597/697 → 82.9–88.1; 507/697 → 69.3–75.9; 56/57 → 90.7–99.7. The arithmetic of the projection is also right (263,524 × 0.433 = 114,106 s = 31.7 h = 1.32 d).
- **The type-vs-token trap was caught in flight and the 92.1 % figure discarded** (`:248`), and the `max_tokens`/reasoning-token defect was diagnosed rather than published as a model failure (`:254`). Both are exactly the discipline the spec was written to enforce.
- **Nothing in production changed**, the harness stayed in the scratchpad, and the suite is at baseline (`handoff.md:39`). The spec's process constraints were honoured.

## Summary of required changes

1. Withdraw 98.2 %; headline 85.6 % (CI 81–89); state the band as undetermined between "< 85 %" and "85–95 %"; run Opus at n=303 through the harness.
2. Count Finding 3 in the robustness gate cell; give flagged books a remediation path or state they are permanently unindexed.
3. Replicate T13a 3× and report the kill condition on the like-for-like 3.27× basis.
4. Restate every robustness rate as a single draw with its interval; keep the justfile's third retry pass.
5. Re-score findability token-weighted on prose; mark the current row method-limited for all three candidates.
6. Replace the "same engine" rescue with the `spec.md:58` clause and the threshold-provenance argument; drop the z-test.
7. Report the incumbent's measured s/page from T8; drop the corroboration claim.
8. State that B5 is unverified and all quality gates ran on re-rendered digital text.
9. Finish T22 (rewrite `swap_scope.md:70`, add restoration to §3) or unmark it. Same for T19/R5.
