# Spec — Citation gate, evaluated by backtest

## Overview

Add one deterministic check that vicaya does not currently have — **does every canon citation in a finished note actually resolve to the sutta it claims?** — and decide whether to keep it by running it retroactively over the 204 notes already in the vault.

This is the "easy" arm of the agentic-quality-loop assessment (2026-07-29). It ships no research runs and no new agent behaviour. The evaluation instrument is a backtest table the user reads, not a subjective comparison of notes.

## Scope correction from the original assessment

The initial assessment overstated the gap. `tools/note_checks.py` already covers most of what agentic-quality-loop would call the mechanical gate:

| Proposed check | Status |
|---|---|
| Required sections present | already in `note_checks.py` (`REQUIRED_SECTIONS`) |
| Frontmatter unquoted colon-space | already (`_has_unquoted_colon_space`) |
| Footnote↔blockquote ratio in T1/T2 | already (`_evidence_section_footnote_and_blockquote_counts`) |
| Series-format awareness | already (`_SERIES_HEADING_RE`) |
| `[REJECTED]` token in note | already a hard refusal in `scratch-gate 7` |
| **Canon citations resolve to the claimed sutta** | **missing — this thread** |

So the thread is one check, not a check suite. That is the whole point of speccing before building.

## Phase 1 measurement outcome — 2026-07-29 (read before the sections below)

Phase 1 ran and **invalidated two of this spec's three premises**. Full detail in `temp/citation-backtest/phase1-verdict.md`. Summary:

- **Extraction feasibility (assumption 2): holds.** 38 distinct citation forms over 904 citations; top-20 cover 96.6%; 1.0% singletons.
- **The `ADJACENT` class: dead.** Three probes over the full 260-note corpus found one plausible instance. The `-adjacent` hits are ordinary conceptual adjacency (`Stoic-adjacent`, `TMT-adjacent`); the hedge-token sweep caught content hedging, not citation hedging; out-of-bibliography CST codes are the documented correct provenance style. The two DN16 cases behind `SKILL.md:1789` are not in the current vault.
- **The existence check: raw precision ≈4%**, because 85% of its 584 rejections are vicaya's own `Vinaya 02 §679` convention, which `verify_citation` does not cover at all. Against the pre-registered `P ≥ 0.7` threshold, **the check as specced fails its own decision rule.**
- **New and better than what was specced:** notes citing both a human ref and a `table:paranum` (`**MN18 …§204** (s0201m_mul:204)`) supply their own ground truth, and the pair is checkable. Real, but present in only 11 / 260 notes (4.2%) — an opportunistic check, not a gate.

### Scope decision — 2026-07-29, user

**Narrowed to structural malformed-reference detection.** The user chose option 1. The verifier's Vinaya and full-collection-name gaps are noted and deliberately left alone (option "leave them alone") — not filed, not fixed.

The thread now builds exactly one check, and it uses **no database**:

> A canon reference is malformed if its numeric part carries more addressing segments than its collection has, or if its leading segment exceeds that collection's known size.

`MN118.150` is malformed because MN suttas are addressed by a single number (1–152) — that `.150` is a paragraph number glued onto the sutta number. Likewise `DN2.244`, `DN22.385`, `SN 5.46.20`, `Khp 5.10`.

**What this scope explicitly does not catch, stated up front:** four of the ~20 real defects are depth-valid but out of range in their second segment — `SN17.99` (SN17 has 43 suttas), `SN48.471–477`, `SN45.195-199`, `AN 3.375`. Detecting those needs per-section sutta counts, i.e. a database, which this scope excludes. `verify_citation` already flags all four correctly, so they remain reachable later without new work.

Expected catch: ~8 of the ~20 distinct defects. Precision should be near 1.0, which is the claim the backtest tests.

**Deviation during Phase 2 — the leading-segment maximum was dropped.** The scope above proposed two sub-checks: segment depth, and a leading-segment ceiling per collection (MN ≤ 152, DN ≤ 34, …). The ceiling is **unsound and was removed**. Ud, Iti, Snp, Thag and Thig are each cited both by chapter.sutta (`Ud 5.5`) and by global number (`Ud 73`, `Iti 75`), so no single ceiling holds for them. The first backtest run made this obvious: 519 `range` findings against 31 `depth`, essentially all of them SuttaCentral uids inside URLs (`UD73`, `SNP28`, `an107`) or CST filenames inside code spans (`dn.02.0`). Two fixes landed: URLs and code spans are now skipped as machine data, and the check is depth-only. Findings fell from 550 to 18.

The sections below are the *original* spec, left unedited as the record of what was predicted.

## The gap being closed

`SKILL.md` Hard Rule 9 says CST paragraph numbers are book-global and every distinct paranum must be confirmed with `resolve-citation` before citing. `SKILL.md:1789` records the failure this rule exists to prevent: two passages footnoted as "DN22-adjacent" and "DN14-adjacent" were both actually DN16, and the Phase 6 reviewer never flagged them because it has no database access.

Today that rule is enforced only by the agent's own diligence. Nothing checks the finished note. Existence-checking happens during Phase 6 (`[VERIFIED]` / `[REJECTED]` pre-annotation against `dpd.db sutta_info`), but that runs over the *reviewer's* output, not over the note's own citations, and it is existence-only — it cannot catch a real sutta cited for the wrong passage.

## What it should do

A new subcommand:

```bash
uv run tools/research_sources.py check-citations <note-path>
```

For the note at `<note-path>`:

1. Extract every canon reference — `canon_refs` frontmatter entries, and inline references in the body matching the standard forms (`MN 60`, `SN22.95`, `AN 4.55`, `DN16`, `Snp 4.14`, `Thag 16.1`, `SN48.9-10`, `MN 02 §23`).
2. For each, check existence against `dpd.db sutta_info`, reusing the existing verifier that Phase 6 citation pre-annotation already uses — do not write a second one.
3. Classify each as `RESOLVED`, `NOT_FOUND`, or `UNVERIFIABLE`, with the same semantics `SKILL.md:1791` already defines (global verse numbers in Snp/Thag/Thig have no per-verse rows and are `UNVERIFIABLE`, which is **not** evidence of fabrication).
4. Flag `ADJACENT` as its own class: any inline reference whose surrounding text contains a hedge token (`-adjacent`, `approximately`, `circa`, a bare CST table code like `s0102m_mul` used as a citation label). These are the DN16 failure mode — a citation the agent itself signalled it had not resolved.
5. Emit one line per finding and exit nonzero if any `NOT_FOUND` or `ADJACENT` exists. `UNVERIFIABLE` alone exits zero.

Output is a stable, greppable line format so the backtest can aggregate 204 notes.

## Explicitly out of scope

- **Verifying that a resolved citation supports the claim made about it.** That is judgment, not a fact a tool can produce. It belongs to the Phase 6 reviewer — thread B.
- Consolidating the existing four Phase 7 steps into one command. Deferred; it is cosmetic and would confound this thread's evaluation.
- Replacing `scratch-self-audit`. Its six questions target failure modes (easy-source bias, dropped user seeds, early stopping) that no deterministic check can reach. The original assessment was wrong to call it a self-graded exam that should be mechanised — only its citation-verification question overlaps with this check.
- Touching `SKILL.md` Phase 7 wiring. Nothing is added to the agent's workflow until the backtest says the check earns its place.

## Evaluation — the backtest

Run the check over all 204 notes in `$VICAYA_VAULT_PATH/Vicaya/` (including subfolders) and write a report to `temp/citation-backtest/report.md`:

- One row per note with a nonzero exit, listing each finding with its line number and surrounding sentence.
- Summary counts by class.
- A sampled worklist: 15 findings drawn at random across notes, each with enough context for the user to adjudicate.

The user reads the sampled worklist and marks each finding **real defect** / **false positive** / **unclear**.

## Pre-registered decision rule

Fixed before the report is read. Written here so it cannot be adjusted afterwards to justify the work.

Let `P` = precision on the 15 sampled findings (real defects ÷ (real defects + false positives), excluding "unclear").

- **`P ≥ 0.7` and ≥ 3 distinct notes carry a real defect** → the check earns its place. Wire it into Phase 7 as a hard gate in a follow-up thread.
- **`P ≥ 0.7` but fewer than 3 notes affected** → keep the subcommand as a manual tool, do not gate on it. Prose discipline is already working.
- **`P < 0.7`** → the check is noise. Delete it and close the thread as churn. Record the null result in `kamma/lessons.md`.

A null result is a successful outcome of this thread. The thread exists to find out, not to ship.

## Assumptions and uncertainties

1. **`dpd.db sutta_info` is the right authority for existence.** Assumed, because Phase 6 pre-annotation already relies on it. If its coverage turns out to be patchier than Phase 6's usage implies, `UNVERIFIABLE` counts will dominate and the backtest will be uninformative — that is itself a finding worth reporting.
2. **Inline citation forms are regular enough to extract.** Uncertain. 204 notes written over three months by several agents may vary more than the standard forms suggest. Task 1 measures this before any check is written; if extraction recall looks poor, the spec needs revising rather than the regex needing widening.
3. **The existing Phase 6 verifier is reusable as a library.** Needs confirming in `tools/research_sources.py` before task 3. If it is only reachable as a CLI path, the thread adds a thin extraction rather than duplicating logic.
4. Whether `ADJACENT` hedge-token detection generalises beyond the two DN16 cases, or is a two-instance pattern being over-fitted. The backtest answers this directly.

## Confidence

**8/10.** High, because the evaluation is deterministic, the corpus already exists, the decision rule is pre-registered, and a null result costs one afternoon and closes cleanly. The uncertainty is concentrated in assumption 2 — if inline citation forms are irregular across 204 notes, extraction recall becomes the real work and the scope grows.
