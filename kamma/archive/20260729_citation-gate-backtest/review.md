# Review — Citation gate, evaluated by backtest

## Outcome: shipped, on a measurement — but nothing the spec proposed survived.

The thread set out to build a citation-resolution gate. Phase 1 measured before building and killed two of three premises. What shipped was discovered by measurement, not designed.

| specced | outcome |
|---|---|
| Citation-resolution gate at Phase 7 | **Not built.** Raw precision ≈4% — 85% of its 584 "failures" were vicaya's own `Vinaya 02 §679` convention, which `verify_citation` does not cover. Would have failed its own pre-registered rule. |
| `ADJACENT` hedge-detection class | **Not built.** Three probes over 260 notes found one real signal. The `-adjacent` hits were ordinary English (`Stoic-adjacent`, `TMT-adjacent`); the hedge sweep caught scholarly hedging about content; the out-of-bibliography CST codes were the documented *correct* provenance style. |
| Human-ref ↔ CST-paranum cross-check | **Not built.** Real, but present in only 11 of 260 notes (4.2%). |
| — | **Built instead:** a structural depth check. `check-citation-shape`, no database, 50 tests. |

## The decision rule

`P` = 18 real defects / (18 + 0 false positives) = **1.00**; notes affected = **6**. Rule required `P ≥ 0.7` and ≥3 notes → **ship**. Gate wiring handed to `20260729_citation-shape-gate-wiring`.

## What the spec actually contributed

Not the design — the **pre-registered threshold**. Without it, the originally-specced check would have shipped on 584 findings across 76 notes, a number that looks impressive until you look at composition. The rule is what forced the composition check.

## Two measurement errors caught before they became findings

- **v1 inventory reported 392 citation forms** with `Thi` ×151 at the top — the regex matching the word *"This"*. A bare-abbreviation alternative plus an open-ended tail group produced phantom forms and an inflated count. Fixed: require a numeric reference, stop the signature at the reference. Real answer: **38 forms, top-20 covering 96.6%, 1.0% singletons.**
- **First backtest returned 550 findings**, 519 of them SuttaCentral uids inside URLs (`UD73`, `an107`) and CST filenames inside code spans (`dn.02.0`). Fixed by skipping URLs and code spans. Findings fell to 18.

Both were caught by looking at the data rather than the summary statistic.

## One unsound check removed

The spec proposed a leading-segment ceiling per collection (MN ≤ 152, DN ≤ 34). **Dropped as unsound** — Ud, Iti, Snp, Thag and Thig are each cited both by chapter.sutta (`Ud 5.5`) and by global number (`Ud 73`), so no single ceiling holds. The check is depth-only.

## Known limits of what shipped

- **Structural only.** It cannot tell whether a well-formed citation supports the claim made about it.
- **Second-segment range errors are out of reach** — `SN17.99`, `SN48.471–477`, `AN 3.375` are depth-valid but out of range. `verify_citation` already flags all four; this check does not.
- **`verify_citation` covers neither Vinaya nor spelled-out collection names** (`Dhammapada 279` fails while `Dhp 279` passes). Found here, deliberately left alone by user decision. It makes Phase 6's `[REJECTED]` pre-annotation noisier than necessary, which matters because SKILL.md tells agents to drop every `[REJECTED]` claim outright.

## Cross-check against the reviewer A/B thread

The two threads failed in opposite directions and neither makes the other redundant. This check is structural, needs no database, precision 1.00 — shipped on measurement. The source-armed reviewer is semantic, needs the database, and failed its blind comparison — shipped on user override. Both catch citation defects; neither catches the other's class.
