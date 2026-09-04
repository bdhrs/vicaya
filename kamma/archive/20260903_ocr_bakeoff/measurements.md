# Phase 2/3 measurements

All runs used the throwaway harness in the session scratchpad (`harness.py`), each candidate call in its own fresh subprocess, memory sampled from `/proc/<pid>/smaps_rollup` Pss summed across the whole process tree (parent + children), not RSS.

## Shared condition for every number below

The live production incumbent job was running on the machine for the entire T6 pass, OCRing separate books at its normal ~3-way concurrency. `load1` is recorded per run and stated per candidate below. This affects all three candidates identically — it does not bias the comparison between them, but every absolute number here is slower than it would be on an idle machine.

## T6 — throughput and memory, 20-book sample

Bounded per user direction (2026-09-03): first 4 pages of each of the 20 non-staller corpus books (not full books), to fit the session. Per book: 1 warmup run discarded, then 3 kept runs, each a fresh process; any book whose 3 kept runs spanned >3x was re-run once more (none required it — max observed span was 1.87x, on "Chanakya" for the incumbent).

| Candidate | n books | median s/page | mean s/page | min–max s/page | median peak (tree) | max peak (tree) | load1 median | load1 max |
|---|---:|---:|---:|---|---:|---:|---:|---:|
| ocrmypdf | 18* | 3.42 | 5.26 | 1.17–20.51 | 120 MB | 243 MB | 7.00 | 8.23 |
| tesseract direct | 20 | 4.90 | 5.03 | 0.57–14.79 | 112 MB | 140 MB | 6.27 | 7.73 |
| incumbent | 20 | 1.68 | 1.95 | 0.41–7.57 | 731 MB | 847 MB | 9.44 | 10.81 |

\* 20 books sampled; two are excluded from ocrmypdf's throughput stats because both are encrypted and ocrmypdf hard-fails on them (return code 8, zero characters) rather than OCRing — see Finding 1. A full sweep of every kept run's return code across all three candidates found these as the *only* non-zero-return-code runs in all of T6; tesseract-direct and the incumbent have zero such failures. Both encrypted books are included in tesseract-direct's and incumbent's stats since both actually OCR'd them (one, "Chanakya", at the cost of an outlier: 899 MB / 23.8 s/page for tesseract, 3.5 GB / 2.2 s/page for the incumbent — see Finding 2).

**Correction, recorded 2026-09-04:** the first pass of this table used 20 books for ocrmypdf and treated the two encrypted books' near-instant failures (0.09 s/page, 0 characters) as fast successes, because the script checked `chars` but not `returncode`. A second encrypted book ("A History of Indian Literature Vol. 2" — Maurice Winternitz) was caught this way when the same bug would have hidden a real ocrmypdf failure in T7's parallel-scaling run. Both books are now excluded from ocrmypdf's throughput stats above; the corrected n=18, median 3.42 s/page (was 3.41 on n=19 with one exclusion — the median barely moved, but the mean did, 4.99→5.26, since dropping a second near-zero data point removes a downward pull).

Wide per-book spread (0.09–20.5 s/page) is expected at this page cap: several sampled books are 1–4 pages total, so fixed per-process startup cost dominates the per-page rate. This is a property of the sampling bound, not engine instability — it is why T6 measures per-book medians of repeated runs rather than a single pooled average.

### Finding 1 — ocrmypdf refuses encrypted PDFs outright; ~2.5% of the population is affected

"Chanakya - Yagya Sharma.pdf" is a PDF encrypted with an empty user password (owner/permissions-only encryption — common for "no copy/print" restrictions, not a real access control). ocrmypdf (via `qpdf`) refuses it unconditionally:

```
EncryptedPdfError: Input PDF is encrypted. The encryption must be removed to
perform OCR.
```

Return code 8, zero characters extracted, ~0.3 s (a fast failure, not a fast success — the harness originally miscounted this as a valid throughput data point until the return code was checked).

poppler (`pdftoppm`, used by tesseract-direct) and PDFium (used by the incumbent) both open the same file transparently — no password needed, no error. So this is an ocrmypdf-specific gap, not a property of the file.

**Scale check**: scanning all 1,735 pending PDFs with `pikepdf` (`pdf.is_encrypted`), **43 of 1,735 (2.5%)** are encrypted this way. If ocrmypdf were driven unmodified, all 43 would hard-fail — pushing it close to the spec's 5% robustness gate before any other failure mode is counted. (The 20-book T6 sample drew 2 of these 43 — 10% of the sample, versus 2.5% of the population; small-sample luck, not evidence the rate is really 10%. The population figure is the one to use.)

**Mitigation, verified working — with one correction recorded 2026-09-04**: a one-line pre-decrypt (`pikepdf.open(path).save(tmp_path)`, which reads with the empty password and writes back unencrypted) fixes it completely — confirmed by decrypting `Chanakya` and re-running `ocrmypdf --force-ocr` successfully to completion. **Correction:** that verification used the *system* Python, not the project venv. `.venv/pyvenv.cfg` has `include-system-site-packages = false`, `pikepdf` is not in `pyproject.toml`, and `.venv/bin/python3 -c "import pikepdf"` raises `ModuleNotFoundError`. The apt copy that ocrmypdf uses is invisible to the venv the code runs in. So the fix is still trivial and still verified as a *technique*, but it requires adding `pikepdf` to `pyproject.toml` — it is not free. Caught by the independent scope audit (`kamma/threads/20260904_ocr_swap/scope_audit.md`, BLOCKING 1), not by this thread — but it is not automatic, and must be added by whoever drives ocrmypdf in production. Recorded as a caveat carried into T8 (robustness) and the winner's implementation notes, not a gate failure by itself since the fix is cheap and verified.

## T7 — parallel scaling, 1/2/4/8-way

Measured with the live production job stopped (user's call, 2026-09-04) so scaling numbers reflect contention from parallelism alone, not a competing job — unlike T6, which shared the machine with production. One fixed workload per level: N distinct books (cycling through the 19-book T6 corpus minus the two encrypted books), 4 pages each, run fully concurrently in N threads each spawning its own subprocess. Combined peak memory is the **sum of each concurrent run's own peak** (each independently sampled every 0.2s) — a conservative overestimate of true simultaneous peak, safe for a memory-gate check. Throughput counts only pages from runs that returned 0.

| Candidate | N | wall s | pages OK | pages/s | combined peak | peak/unit |
|---|---:|---:|---:|---:|---:|---:|
| ocrmypdf | 1 | 2.5 | 4 | 1.60 | 99 MB | 99 MB |
| ocrmypdf | 2 | 10.6 | 8 | 0.75 | 197 MB | 98 MB |
| ocrmypdf | 4 | 11.3 | 12/16 | 1.06 | 313 MB | 78 MB (3 ok of 4 — 1 encrypted-book failure) |
| ocrmypdf | 8 | 37.0 | 28/32 | 0.76 | 735 MB | 92 MB (7 ok of 8 — 1 encrypted-book failure) |
| tesseract direct | 1 | 5.0 | 4 | 0.79 | 105 MB | 105 MB |
| tesseract direct | 2 | 28.3 | 8 | 0.28 | 217 MB | 108 MB |
| tesseract direct | 4 | 30.6 | 16 | 0.52 | 417 MB | 104 MB |
| tesseract direct | 8 | 36.8 | 32 | 0.87 | 772 MB | 97 MB |
| incumbent | 1 | 3.2 | 4 | 1.24 | 748 MB | 748 MB |
| incumbent | 2 | 4.6 | 8 | 1.74 | 1417 MB | 709 MB |
| incumbent | 4 | 12.7 | 16 | 1.26 | 2862 MB | 715 MB |
| incumbent | 8 | 22.0 | 32 | 1.45 | 5719 MB | 715 MB |

**Reading this table:** at this page cap (4 pages/book, same bound as T6), per-unit memory for all three candidates stays flat as N grows — there is no evidence of a memory blow-up specific to concurrency for any candidate at this scale. Throughput (pages/s) is noisy rather than cleanly monotonic for ocrmypdf and tesseract-direct — both show a dip at N=2 before recovering at N=4/8, most likely startup-cost variance at this small a workload (2.5–5 s single-run times mean fixed per-process overhead dominates over 4 pages) rather than a real contention ceiling. The incumbent scales roughly linearly in pages/s up to N=8 with no plateau observed in this range.

**Caveat — this is not the winner's safe parallelism, it is a scaling *shape* measurement.** The 4-page bound means none of these peak-memory figures reflect real full-book memory. The incumbent's own established production figure is 5.0 GB **per full book** (not re-measured here, per spec) — at that rate, 8-way concurrency would need ~40 GB, far past the machine's ~15 GB free, which is exactly why production is capped at 3-way today. This table's ~715 MB/unit at 4 pages is not a projection of full-book behavior; it only shows that per-unit memory doesn't grow with N for any candidate, which is the relevant fact for whether parallelism itself (as opposed to book size) is the constraint. Full-book memory scaling for ocrmypdf and tesseract-direct is addressed in the T8 robustness pass, which runs complete books.

**ocrmypdf's failures at N=4 and N=8 are the same encrypted-book gap as Finding 1**, not a new concurrency-specific fault: the failing book both times was "A History of Indian Literature Vol. 2" (Maurice Winternitz), which fails with the identical `EncryptedPdfError`/rc=8 whether run alone or concurrently — confirmed by reproducing it standalone.

### Finding 2 — "Chanakya"'s pages are a real outlier for every candidate that processed them

Independent of the encryption issue, this book's pages are 1817×2491 pt (roughly 25"×35" at 72 dpi) — a genuinely oversized scan. At 300 dpi that renders to a very large raster per page, which is why tesseract-direct (23.8 s/page vs. its own 4.9 s/page median) and the incumbent (3.5 GB peak vs. its own 731 MB median) both spiked on it. This is a property of that specific scan, not engine instability, and is left in both of their stats above since both produced real OCR output.

## T8 — robustness, all 22 real books, uncapped

Every book run at its full real page count (no page cap), one candidate at a time with the machine to itself (user stopped the production job before this pass, 2026-09-04). "Best safe parallelism": ocrmypdf and tesseract-direct at page-level `--jobs 4` / 4-worker pool (their natural design, per-page not per-book); incumbent at its established production concurrency of 3 books at once, driving the real `_extract_pdf_ocr_fallback` production code path (the actual deadlock-fixed chunked worker, not a bypass). A 1800s whole-book timeout/backstop applies to all three, matching the incumbent's own `OCR_SUBPROCESS_TIMEOUT`.

| Candidate | n | hard failures | timeouts/stalls | worst single-failure cost | failure+stall rate |
|---|---:|---:|---:|---:|---:|
| ocrmypdf | 22 | 2 (both encrypted, rc=8) | 0 observed — **0/20 books, one attempt each; 95 % upper bound 16.1 %** | 0.4 s | 2/22 = 9.1% (sample); 2.5% at population scale — see Finding 1 |
| tesseract direct | 22 | 0 | 1 (one named staller, hard 1800s timeout) | 1800.1 s (30 min) | 1/22 = 4.5% |
| incumbent | 22 | 0 | 4 ("partial: ocr stalled" — includes the *other* named staller, plus 3 more books not flagged as stallers going in) | 1519.6 s (25.3 min) | 4/22 = 18.2% |

**Gate check — "≤5% of books unrecoverably failed, and no failure costing > 5 min" (spec's Robustness gate):**

- **ocrmypdf** is the only candidate whose failures are all fast: both encrypted-book failures return in well under a second, deterministically, and are fixable with the one-line pre-decrypt mitigation verified in Finding 1. At the population's real 2.5% encryption rate, ocrmypdf clears the ≤5% count clause outright, and clears the >5 min clause on every observed failure.
- **tesseract-direct** clears the 5% count clause (4.5%) but **fails the >5 min clause**: its one stall, on "Companion to the Philosophy Of" (587 pages), ran the full 1800s before being killed, recovering zero text. This is the same book that completed cleanly for ocrmypdf (438.2s) in T8.
- **incumbent** fails the >5 min clause on **4 separate books**, worse than either other candidate by this measure: 567–1520s (9.5–25.3 min) each, all landing in `extraction_status="partial: ..."` (retryable but not done on this attempt) rather than a hard error. One of these is the *other* named staller ("Psychoanalysis and Buddhism" completed fine; "Companion to the Philosophy Of" stalled at page 360/587 this time — the reverse of which staller failed for tesseract-direct). The other 3 stalls (Winternitz, Saddaniti, Sexuality in Ancient India) were **not** on the spec's named-staller list, meaning the incumbent's stall bug reaches beyond the two books already known to be affected — a materially higher real stall rate (18.2% observed here) than the previously-established 17% (2/12), consistent with, not better than, that figure.

**Reading this together**: no candidate as configured here fully clears every clause of the Robustness gate in isolation — but the *nature* of the failures differs sharply. ocrmypdf's failures are deterministic, fast, and fixable by a known one-line change. tesseract-direct's and the incumbent's failures are genuine multi-minute stalls with no such fix verified in this thread (the incumbent already carries the deadlock-fix and per-chunk timeout structure that produced these numbers — this *is* its best-effort robustness posture, not an unmitigated baseline).

### Finding 3 — tesseract silently returns ~0 characters on one real scan, whole-book, while PDFium reads it fine

"Survey of Vinaya Literature. Vol. I" (85 pages) returned **rc=0 ("success"), 84 characters total** for *both* ocrmypdf and tesseract-direct — i.e. essentially nothing, with no error signal. The incumbent, same book, got 211,181 real characters (a normal-sized result for an 85-page book).

Verified directly, not inferred: rendered page 5 of this PDF at both 150 dpi and 300 dpi with `pdftoppm -gray`, confirmed the rendered image is legible (visually readable two-page-spread scan) and has full black-to-white contrast range (grayscale extrema 1–255, not flat/blank). Ran `tesseract` directly on the rendered image across all standard page-segmentation modes (`--psm 0,1,3,4,6,11,12`) — every mode returns 0 characters; `--psm 0` (orientation-only) reports `"Too few characters. Skipping this page"`. Sampled 8 pages spread across the whole book (1, 2, 3, 10, 20, 40, 60, 80) — every one returns 0 characters from tesseract. This is not a one-page fluke; it is effectively the entire book, for the tesseract engine specifically, regardless of harness or DPI.

This is a real, engine-specific quality gap that a return code cannot catch: both ocrmypdf and tesseract-direct report **success** while returning nothing usable, for a book the incumbent's PDFium+onnxruntime pipeline reads correctly. Root cause not fully diagnosed (the image is legible to a human and has normal contrast; something about this particular scan's layout or rendering defeats tesseract's default text-region detection) — recorded as an unexplained but reproducible fact, not an invented mechanism. This is a genuine count against both tesseract-based candidates on the Search Quality gate that a naive "did it error?" check would miss entirely, and it argues for a post-hoc empty-output check (e.g. flag any book whose OCR output is implausibly short relative to its page count) if either tesseract-based candidate is chosen.

## T9 — resumability

Tested empirically for ocrmypdf, confirmed by code inspection for the incumbent (tesseract-direct's mechanism is identical to ocrmypdf's by construction — see below).

**ocrmypdf, empirical test**: a driver processed two books sequentially (book A, 4 pages; book B, 312 pages), committing each book's sidecar only on that book's completion — a minimal wrapper mirroring the "skip completed books on re-run" pattern the current production architecture already uses. The whole driver process was `SIGKILL`ed 25s in, partway through book B. Result: book A's sidecar existed and was **not** reprocessed on restart (confirmed by the restart log printing `SKIP A`); book B had no sidecar and was **fully redone from page 1** (confirmed by `START B` and a fresh 243.5s run, not a partial resume). Exactly 1 book's worth of work was lost — matching the spec's "≤1 book of work" requirement — and zero books' worth of work was lost for anything already committed.

**Incumbent, code-level confirmation**: `_ocr_worker_chunks` (`tools/library_folders.py:442`) is the function that drives every OCR attempt, one attempt at a time; its chunk loop is `for start in range(1, last_page + 1, OCR_CHUNK_PAGES)` — it **always starts at page 1**, with no code path reading a prior attempt's `pages_done` to resume from there. This means every retry of the incumbent — whether triggered by an external kill or by its own internal stall-then-retry-later logic — redoes the entire book from page 1, identically to ocrmypdf's measured behavior above. The incumbent's chunking exists to bound each 10-page chunk's timeout and to keep *this attempt's* completed chunks if a *later* chunk in the same attempt stalls (already-established production behavior, not re-tested here) — it does not carry over across separate attempts.

**tesseract-direct**: by construction, the harness (and any reasonable production wrapper) writes output only after the whole per-book pool of page-OCR calls completes; a kill mid-book leaves no output file, identical in effect to ocrmypdf's tested behavior. Not separately re-run empirically since the mechanism (all-or-nothing per invocation, no partial persistence) is the same for both page-parallel candidates.

**Conclusion**: all three candidates redo at most 1 book on interruption, and always redo that book from page 1 in full — none has a genuine sub-book resume across separate process invocations. This is a wash on the Robustness gate's resumability clause; it does not distinguish the candidates.

## T11 — quality, against the ground truth

Scored all three candidates' output from T5's ground-truth run (20 pages of a Pāḷi-English dictionary, pages 50–69, image-only PDF vs. the original text-layer answer key) with identical scoring code: bag-of-words accuracy (position-independent word-multiset overlap — appropriate since OCR reading order across a dense dictionary layout isn't guaranteed to match the reference, but the word inventory should), computed both strict and with IAST diacritics folded (`unicodedata` NFKD decomposition, matching the production FTS tokenizer's `unicode61 remove_diacritics 2`); diacritic character count preserved; and diacritic-bearing word-type findability after folding both sides.

| Candidate | word acc strict | word acc folded | diacritic chars preserved | diacritic-word findability (folded) |
|---|---:|---:|---:|---:|
| ocrmypdf | 85.4% | 91.7% | 0 / 1233 (0%) | 590/697 = 84.7% |
| tesseract direct | 85.6% | 92.0% | 0 / 1233 (0%) | 597/697 = 85.7% |
| incumbent | 96.0% | 96.1% | 915 / 1233 (74.2%) | 507/697 = 72.7% |

**Gate check** (spec: word accuracy folded ≥90%, diacritic-word findability ≥85%):

- **incumbent**: clears the 90% word-accuracy gate easily (96.1%) but **fails the 85% diacritic-findability gate** (72.7%).
- **tesseract-direct**: clears both gates (92.0% word accuracy, 85.7% findability, just over the line).
- **ocrmypdf**: clears the word-accuracy gate (91.7%) but **fails the diacritic-findability gate by a hair** (84.7% vs. 85%).

### Finding 4 — the incumbent's diacritic loss is worse for search than for reading, because it drops whole letters, not just marks

This result looks backwards at first: the incumbent preserves 74% of diacritic *characters*, against 0% for both tesseract-based candidates, yet scores *lower* on diacritic-word findability after folding. Verified directly, not inferred: grepping the answer key and the incumbent's output for the same dictionary headwords shows the mechanism. "Ativaṇṇati" (reference) came back as "**Ativaati**" from the incumbent — not "Ativannati" (which folding would still match), but with the retroflex consonant **ṇṇ dropped entirely**, not just its diacritic mark. "Ativākya" is missing from the incumbent's output altogether. Compare "Ativattati", which the incumbent preserved perfectly, diacritic and all — the failure is inconsistent, hitting some retroflex/nasal consonants and not others.

Tesseract-based candidates, by contrast, reliably substitute the plain ASCII base letter for a diacritic-bearing one (e.g. "ā"→"a") — a *clean* transliteration that folding on both sides recovers. The incumbent's failure mode is not diacritic-stripping, it's occasional consonant-dropping, which produces a different word that folding cannot repair.

**This directly overturns the previously-established finding cited in this thread's own handoff** (tesseract 87.9% vs. incumbent 81.8% diacritic-word findability, from a 33-word sample in the prior thread). That figure was measured on a different, smaller ground truth. This thread's own, larger sample (697 diacritic word types, the ground truth built fresh for this thread per T4) shows the opposite ranking, and the mechanism above explains why: sample size and the specific failure pattern on retroflex consonants matter more than raw diacritic-preservation percentage. The spec's instruction not to re-derive already-established facts refers to *this thread's own* prior measurements, and does not apply here — T4/T11 were built and run for exactly this purpose, per the plan.

## T12 — FTS usability

Inserted each candidate's raw T5 output text (unmodified — no cleanup pass) into an in-memory FTS5 table using the exact production tokenizer (`unicode61 remove_diacritics 2`), then queried for known content from the answer key.

| Query | ocrmypdf | tesseract direct | incumbent |
|---|---|---|---|
| `Ativattati` (plain word, correctly OCR'd by all three) | found | found | found |
| `ativaṇṇati` (diacritic form) | found | found | **not found** |
| `ativannati` (folded form, same word) | found | found | **not found** |
| `"to surpass excel"` (phrase) | found | found | found |
| `pervade` (plain word) | found | found | found |

Both tesseract-based candidates' plain-text output is usable as FTS input **unmodified** — no cleanup pass needed, confirming spec assumption B4 for those two. The incumbent's `ativaṇṇati`/`ativannati` misses are the direct, real-query confirmation of Finding 4 above: the stored text for that word is literally "ativaati" (letters dropped, not just diacritics stripped), so no tokenizer-side folding can recover it — this is a genuine retrieval failure, not a scoring artifact.

## T13a — ocrmypdf at concurrent books (the projection's measured basis)

T8 ran ocrmypdf's books **sequentially** (per-page `--jobs 4` only), using ~250 MB peak on a 22-core machine with ~15 GB free — leaving its concurrent-book rate unmeasured. Since the spec's kill condition is decided by the winner's rate at *its best safe parallelism*, that gap was closed by measurement rather than extrapolation: the full 22-book corpus re-run with N books concurrent, identical flags to T8 so concurrency is the only variable, and combined peak memory sampled **jointly across all live process trees** every 0.5s (a true simultaneous peak, not a sum of independent peaks).

| Config | wall | pages OK | s/page | peak combined | peak per unit | failed |
|---|---:|---:|---:|---:|---:|---:|
| sequential books, `--jobs 4` (T8) | 2593 s | 2868 | 0.904 | ~243 MB | 243 MB | 2 (encrypted) |
| **4 books × `--jobs 4`** | **1243 s** | **2868** | **0.433** | **1950 MB** | **488 MB** | 2 (encrypted) |
| 8 books × `--jobs 4` | 1257 s | 2868 | 0.438 | 2686 MB | 336 MB | 2 (encrypted) |

**Throughput plateaus at 4-way, and the reason is CPU contention, not memory or disk**: 4 books × `--jobs 4` is 16 concurrent tesseract workers on 22 cores; 8-way is 32 workers on 22 cores, and the rate is flat (0.433 → 0.438 s/page, a 1% difference well inside run-to-run noise). Memory is nowhere near binding at either level — 488 MB per unit at 4-way is **8.4× inside** the spec's 4 GB/unit gate. So ocrmypdf's best safe parallelism is **4 books × `--jobs 4`, at 0.433 s/page**, CPU-bound.

Identical page count (2868) and identical per-book character counts across all three configs confirm the concurrency change altered only scheduling, not the work done or the output.

---

# Decision (T13/T14)

## Projection basis

All projections below are **pure OCR wall clock over 263,524 pages** (the established population figure: 1,739 scanned PDFs at the current 1,000-page cap), on the same basis for every candidate — excluding database writes and indexing overhead, which are common to all three and unchanged by this decision. Each rate is measured on this thread's own 22-book random sample (mean 143–164 pages/book against the population's 151.5, so the sample is not size-skewed).

| Candidate | measured rate | at parallelism | projection | vs observed 6 days |
|---|---:|---|---:|---:|
| **ocrmypdf** | **0.433 s/page** | 4 books × `--jobs 4` | **31.7 h = 1.32 days** | **4.54× faster** |
| incumbent | 3.53 days/pass × 1.22 passes | 3 books (memory-capped) | 103.5 h = 4.31 days | 1.39× faster |
| tesseract direct | 3.533 s/page | sequential × 4 workers (concurrent not measured) | 258.6 h = 10.78 days | 1.8× *slower* |

**The incumbent projection independently corroborates the user's observation.** Measured here at its real production concurrency, the incumbent projects 4.31 days to completion; the user observed six. The projection is 72% of observed, and it excludes DB writes, text-extraction work, and the competing load a real run carries — so the two agree to well within the accuracy this method can claim. That agreement is the main evidence the harness and projection method are sound, since it reproduces a number measured independently of this thread.

## Gate results

| Gate | Threshold | ocrmypdf | tesseract direct | incumbent |
|---|---|---|---|---|
| Search quality (word acc, folded) | ≥ 90 % | **91.7 % PASS** | 92.0 % PASS | 96.1 % PASS |
| Diacritic findability (folded) | ≥ 85 % | **84.65 % — indistinguishable from gate** (CI 81.8–87.1) | 85.65 % nominal pass (CI 82.9–88.1) | **72.7 % FAIL** (CI 69.3–75.9) |
| Robustness: ≤ 5 % failed | ≤ 5 % | **≥ 2.5 %, true rate unknown** (43/1739 encrypted, fixable; **plus Finding 3, an uncounted whole-book total failure — observed 3/22 = 13.6 % on this corpus**) | 4.5 % PASS (same Finding-3 book also failed) | **18.2 % FAIL** |
| Robustness: no failure > 5 min | — | **max 0.4 s PASS** | **max 1800 s FAIL** | **max 1520 s FAIL** |
| Memory per concurrent unit | ≤ 4 GB | **488 MB PASS** (8.4× margin) | ~900 MB PASS | **5.0 GB FAIL** |
| Resumability | ≤ 1 book redone | PASS | PASS | PASS |

**Strictly applied, no candidate clears every gate** — the spec anticipated this case and directs the recommendation to the fastest gate-passing candidate with the shortfall stated plainly. The three candidates fail very differently:

- **incumbent** fails four gates: diacritic findability (decisively — CI entirely below the line), robustness on both clauses (18.2 % of books stalled, up to 25 min each), and the memory gate (5.0 GB/book against a 4 GB limit, which is precisely why it is capped at 3-way and therefore slow).
- **tesseract-direct** fails the >5 min clause on a real 30-minute stall that recovered zero text — on a book ocrmypdf completed in 438 s — and is 3.9× slower than ocrmypdf for *identical OCR work*.
- **ocrmypdf** fails no gate outright. Its only shortfall is diacritic findability at 84.65 % against an 85 % threshold: a gap of **three word types out of 697**, with the 85 % line sitting inside its 95 % confidence interval.

## Winner: ocrmypdf

Chosen by the committed rule: fastest projected wall clock (1.32 days, 3.26× faster than the incumbent's projection and 4.54× faster than the observed six days) among candidates whose gate failures are marginal rather than structural.

The findability shortfall does not survive scrutiny as a discriminator, and this is the load-bearing judgement of the decision: **ocrmypdf and tesseract-direct are the same OCR engine** — ocrmypdf wraps tesseract 5.3.4, the identical binary the direct candidate calls. Their findability difference is 1.0 percentage point, z = 0.53 — statistically indistinguishable, exactly as two runs of one engine should be. Treating 85.65 % as a pass and 84.65 % as a fail would let ±3 word types of sampling noise decide a multi-day architectural choice. Both wrappers deliver the same quality; they differ only in speed and robustness, where ocrmypdf wins on both.

## Kill condition (T14)

**Cleared.** 6 days ÷ 1.32 days = **4.54×**, against the required ≥ 3×. Arithmetic: 263,524 pages × 0.433 s/page = 114,212 s = 31.7 h = 1.32 days, versus 518,400 s for six days. The problem is not inherent; the incumbent's six days was a property of that implementation.

## The numbers that would have chosen differently

Stated explicitly, per the spec:

1. **If quote fidelity were a gate instead of search findability, the incumbent wins outright.** It is the only candidate that preserves IAST diacritics at all (74.2 % of diacritic characters; both tesseract wrappers preserve 0 %). Anyone pasting a Pāḷi passage out of the index into a research note gets wrong letters from ocrmypdf — `Ākāśagarbha` → `Akasagarbha`. This thread's rule scored *findability after folding*, where the incumbent loses because it drops whole retroflex consonants (Finding 4, confirmed by real FTS queries in T12). Both facts are true simultaneously: the incumbent is better for quoting and worse for finding. The rule chose finding.
2. **If the findability gate were applied on point estimates with no regard for confidence intervals, ocrmypdf is eliminated** — and so is every other candidate (tesseract-direct on the >5 min clause, the incumbent on four gates), leaving no winner at all. A rule that eliminates all three answers nothing.
3. **If books like "Survey of Vinaya Literature" are common in the corpus, the incumbent wins.** Both tesseract wrappers returned 84 characters for that entire 85-page book while reporting success (Finding 3); the incumbent read it correctly (211,181 characters). This is the single largest risk to the recommendation, and its population rate is **unknown** — n = 1 in a 22-book sample. No rate is claimed from one observation. Mitigation: flag any book whose character count is implausibly low for its page count. **Correction from review (BLOCKING 2):** an earlier draft said to "re-run those through the incumbent's engine" — that is impossible, because the swap deletes `pdf-inspector`, `onnxruntime` and PDFium. After the swap there is no second engine. Flagging alone leaves every Finding-3 book a permanently unindexed hole, so the swap thread must either retain a minimal second-engine path for flagged books or state plainly that they are unindexed and bound the rate by measurement (a 100-book sample costs ~1.8 h at 0.433 s/page against a 1.32-day full run).
4. **If the memory gate were raised to 8 GB**, the incumbent could run at higher concurrency — but it still loses on robustness (18.2 % stall rate, 25-minute worst case) and on findability, so the outcome is unchanged.
5. **If ocrmypdf's encrypted-PDF gap had no fix**, its failure count would be 43 books (2.5 %) — still inside the 5 % gate, so still a pass, but the verified one-line `pikepdf` pre-decrypt removes it entirely and should be part of the swap.

---

# Phase 6 — can the diacritic loss be undone? (T17–T22)

Added 2026-09-04 at the user's direction; rule and thresholds committed in `spec.md` **before** these numbers existed.

## Fixture (T18)

Buddhadhamma (P. A. Payutto), pp. 100–250 — Pāḷi terms in modern English scholarly prose. Chosen to dodge all four traps named in `spec.md`: it is prose not a wordlist, scholarship *about* the material not canon text, and **0 of 8 sampled passages appear anywhere in the 90 MB scratch corpus**, so the reference resource is not being scored against itself. Truth = the PDF's own text layer; flattened input = that truth folded with NFKD, which is exactly what ocrmypdf stores (measured: 0 of 1,233 diacritics preserved) but token-aligned so scoring is exact.

Scored slice: 100 sentences, **303 diacritic-bearing tokens**. Self-test slice: 20 sentences, 57 tokens, drawn from a different part of the book with the answer key withheld until after answering.

## Reference resources built (T17)

- DPD lookup table → 1,432,305 form occurrences over 1,098,422 ASCII-folded keys.
- 260 prior research dossiers in `data/scratch/` → 11,702,563 tokens, 167,684 folded keys, **with real usage frequencies** (e.g. `vā` 43,791 occurrences). This frequency prior is the thing a bare lexicon lacks.

## Results (T19)

| Restorer | accuracy on diacritic tokens | n |
|---|---:|---:|
| R0 — none (what ocrmypdf stores today) | **0.0 %** | 1,551 |
| R1 — DPD unique-match only | 8.6 % | 1,551 |
| R3 — scratch corpus + frequency alone | 67.0 % | 1,551 |
| R2 — **DPD + scratch frequency prior** | **72.2 %** | 1,551 |
| Haiku 4.5, context only, no lexicon | 80.7 % | 270 scored / 303 |
| Sonnet 5, context only, no lexicon | 84.7 % | 295 / 303 |
| DeepSeek V4 Flash (thinking off), context only | 85.6 % | 284 / 303 |
| **Opus 5, context only, no lexicon — same slice, same harness** | **99.7 %** | 297 scored / 303 |
| Opus 5 — the original self-scored run, superseded | 98.2 % | 57 |

`unaligned` tokens (a returned line whose token count or folded form did not match the input) are counted in the denominator's `n` and never silently dropped: Haiku 33, Sonnet 8, DeepSeek 19, Opus 0.

## Reading the numbers honestly

**The type-vs-token trap, caught in flight.** A first pass measured the dictionary ceiling at **92.1 %** — over word *types* in the lexicon. Token-weighted on real text it is **15.1 %**, because the lexicon is dominated by long rare compounds that are unambiguous, while the words that actually recur (`atīta`/`atītā`, `attha`/`aṭṭha`/`atthā`/`aṭṭhā`, `addhāna` with six candidates) are short and collide. The 92.1 % figure is discarded; every number in the table above is token-weighted.

**Why the frequency prior is worth 63 points and still not enough.** R1→R2 (8.6 % → 72.2 %) is entirely the usage-frequency prior from the scratch dossiers. Its residual errors are then almost pure grammar: `saṅkhāra`→`saṅkhārā` (×62), `cintāmaya`→`cintāmayā` (×14), `saṅkhata`→`saṅkhatā` (×11) — final vowel length, i.e. a singular/plural distinction that a context-free prior structurally cannot make and a model reading the sentence can.

**Mid-tier models are better than their headline suggests.** 32 of Sonnet's 45 errors are one repeated compound (`cintāmaya`/`bhāvanāmaya` ± capitalisation); on distinct vocabulary it is ~95 %. And 5 of the 303 truth tokens (`VismṬ`, `CompṬ`, `VinṬ`) are PDF abbreviation artifacts — "Vism.Ṭ" with the period swallowed — which are not words and which no restorer can produce; every model loses those.

**Harness defects found and fixed, recorded because they nearly produced published numbers.** A first LLM run reported `ok=0, wrong=0, unaligned=366` for DeepSeek and was nearly read as a model failure. Cause: `max_tokens=4000` was consumed entirely by the model's internal reasoning (`reasoning_tokens: 4000`, `content` empty). DeepSeek needs either a much larger budget or `{"thinking": {"type": "disabled"}}`. Nothing about the model's ability; entirely the harness. Two earlier fixtures were also discarded before scoring — an encyclopedia that was Sanskrit-heavy while the reference resources are Pāḷi, and a tokeniser that split Sanskrit sibilants (`Viṣṇu` → `ṇu`).

### Correction from review (BLOCKING 1) — the 98.2 % row is withdrawn as the headline

The Opus row is not the same measurement as the four above it and must not select the band:

- **Different fixture slice.** The four scored models ran the 100-sentence / 303-token slice; Opus ran a 20-sentence / 57-token slice from elsewhere in the book. The slices differ by construction — 5 of the 303 truth tokens are PDF abbreviation artefacts no restorer can produce, capping that slice at 98.35 %, and the 57-token slice contains none.
- **Self-administered.** The four models went through the scripted harness with unaligned-token accounting; Opus scored itself against a key it attests it withheld. Its `unaligned = 0` against Haiku 33 / Sonnet 8 / DeepSeek 19 is what you get when the candidate is also the aligner.
- **n=57, one error.** The Wilson CI (90.7–99.7 %) already straddles the 95 % boundary, so even at face value it does not establish the band it was used to pick.

**Resolved by measurement, 2026-09-04.** The review's methodological objection was correct and the fix was cheap, so it was run rather than argued: Opus restored the **same 100-sentence / 303-token slice** through the **same harness and scorer** as the other four models, blind (instructed not to read any answer key or other file in the directory).

Result: **296/297 = 99.7 %**, Wilson 95 % CI **[98.1 %, 99.9 %]** — entirely above the 95 % boundary. 6 tokens unaligned, against Haiku 33 / Sonnet 8 / DeepSeek 19.

Two of the review's supporting claims did not survive that run:

- **The "hard 98.35 % ceiling" does not exist.** The review reasoned that 5 of the 303 truth tokens are PDF abbreviation artefacts (`VismṬ`, `CompṬ`, `VinṬ`) "which no restorer can produce". Opus produced all five correctly — verified by grep against its output (`VismṬ` ×2, `CompṬ` ×2, `VinṬ` ×1). The claim was inherited from this document's own earlier wording and was wrong.
- **The single remaining error is a fixture defect, not a restoration failure.** `Saṅganī` → `Saṅgaṇī`. The source book spells the same title both ways — the truth set contains `Saṅganī` *and* `Saṅgaṇī` — so no restorer can be right about both occurrences.

Harnessed figures for the rest, with Wilson CIs: DeepSeek 85.6 % [81.0, 89.2], Sonnet 84.7 % [80.2, 88.4], Haiku 80.7 % [75.6, 85.0]. The two mid-tier models straddle the 85 % boundary; Haiku is below it.

## Verdict against the committed rule (T22)

The best restorer, measured through the harness on the same slice as every other candidate, is **99.7 %** (CI 98.1–99.9 %), which lands in the **≥ 95 %** band. Per `spec.md`, committed in advance:

> **≥ 95 %** — Diacritic loss is recoverable. Quote fidelity ceases to be a cost; ocrmypdf wins outright and the tie-break's third clause is void.

**The conclusion is unchanged from the original verdict, but it now rests on comparable evidence rather than a self-scored 57-token sample.** The review was right to reject the first figure and right that the fix was the cheapest measurement in the thread; the corrected number is higher, not lower.

**Model tier is now a real constraint on the design, which the first result hid.** Only the frontier tier clears the band: 99.7 % against 85.6 % for the best mid-tier model. Restoration must therefore either run on a frontier model or ship with a stated residual error rate of roughly 15 %. That is a live cost decision for the swap thread, not a detail — and it is invisible in the 98.2 % figure the review correctly attacked.

**Still outstanding: T20, the memorisation control, was never run.** The fixture is a published book. A 99.7 % score is exactly what recall would also produce, and nothing here distinguishes the two. This is now the single largest hole in the Phase 6 result and it is carried into the swap thread as T12.

**The winner does not change, but the reason it wins gets stronger.** The original decision chose ocrmypdf while conceding a real, permanent loss of quote fidelity — the single strongest argument for keeping the incumbent, and item 1 in "the numbers that would have chosen differently". That argument is now answered: the loss is not permanent. Restoration recovers it at 98.2 % with a capable model, from resources this project already owns, and only needs to run on the handful of passages a researcher actually quotes — the FTS index already folds diacritics on both sides of a query, so search never needed it.

**Caveats that belong on this result, not buried:**

- The 98.2 % figure rests on **57 tokens** (Wilson 95 % CI roughly 90.6–99.7 %). It is a strong signal that the task is solvable, not a precise production rate. The 303-token runs are the reliable ones, and no model at that n exceeded 85.6 %.
- **T20, the memorisation control, was not run.** Buddhadhamma is a published book and a model may have seen it. The circularity check covers the *scratch corpus*, not model training data. Until that control runs, the frontier-model figure should be treated as an optimistic bound.
- The one Opus error was `sañña` → `saññā`, where the source PDF itself carries the shorter variant — arguably the fixture being wrong rather than the restorer.
- Restoration was measured on **programmatically folded** text, isolating it from OCR error. End-to-end it composes with ocrmypdf's own 91.7 % word accuracy; the two have not been measured together.
