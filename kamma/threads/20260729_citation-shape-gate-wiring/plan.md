# Plan — Wire the citation shape check into Phase 7, and fix the 18 known defects

## Architecture Decisions

- Defects are fixed **before** the gate is wired. Wiring first would leave six known-failing notes tripping a new hard gate on the next unrelated run.
- The MN/DN/Khp corrections take their target form from each note's own footnote text, not from a guess. The footnotes already state sutta and paragraph separately.
- The four three-part SN references are resolved against the canon DB individually. No pattern-based rewrite.
- The `SKILL.md` addition is a few lines in the Phase 7 exit sequence. Check semantics stay in the subcommand's help and docstring.
- Vault corrections publish through `scripts/sync_notes.py` only — the pre-approved path. No other git commands.

---

## Phase 1 — Fix the mechanical defects

- [x] `2026-05-27 - bojjhanga-definitions.md`: rewrite `MN118.150`, `MN118.152`, `DN22.385` to `MN118 §150`, `MN118 §152`, `DN22 §385`, including the footnote anchors, taking each target from the footnote's own text.
  → verify: `check-citation-shape` on the note exits 0; every footnote still resolves to a definition

- [x] `2026-06-20 - bojjhanga-complete-ebt-reference.md`: same for `MN118.150`.
  → verify: check exits 0

- [x] `2026-05-27 - pali-prosody-study-guide.md`: correct `Khp 5.10` to the real Maṅgalasutta reference.
  → verify: check exits 0; the corrected ref verifies via `verify_citation`

- [x] `2026-07-24 - gnostic-indian-parallels.md`: correct `DN 2.244` and `DN2.244` to `DN2 §244`.
  → verify: check exits 0

## Phase 2 — Resolve the four SN references

- [x] For each of `SN 5.46.20`, `SN 4.35.45`, `SN 5.51.4` (in `2026-06-06 - nibbidā-…`) and `SN 1.4.6` (in `2026-07-15 - what-the-suttas-say-about-the-differences-…`): identify the actual passage from the note's surrounding text, confirm with `resolve-citation`, and rewrite to the standard two-part form.
  → verify: each corrected ref passes `verify_citation`; each still matches the claim made about it in the note

- [x] Any reference that cannot be confidently resolved: leave as-is and record it in the thread's `review.md`. **Do not invent a correction.**
  → verify: unresolved refs listed explicitly, or an explicit statement that all four resolved

- [x] Re-run the backtest over the full corpus.
  → verify: `check-citation-shape` reports zero findings across all 260 notes, or only the explicitly-unresolved ones

## Phase 3 — Publish the corrections

- [ ] Sync each corrected note with `uv run scripts/sync_notes.py "<path>"`.
  → verify: each sync command reported success, or the failure is recorded

## Phase 4 — Wire the gate

- [x] Add `check-citation-shape` to the Phase 7 exit sequence in `skill/vicaya/SKILL.md`, between `scratch-set-note` and `scratch-self-audit`, as a hard failure. Keep it to a few lines.
  → verify: the Phase 7 exit paragraph names the command in order; no semantics duplicated from the docstring

- [x] Add a regression test using a fixture note built from all six real defect shapes.
  → verify: `uv run -m pytest tests/ -k citation` passes; removing the check makes it fail

- [x] Run the full suite. Fix every failure, including pre-existing ones, per `CLAUDE.md`.
  → verify: `uv run -m pytest tests/` green

## Phase 5 — Close out

- [ ] `/kamma:3-review`, then `/kamma:4-finalize`.
  → verify: `review.md` written; thread archived

---

## Outcomes recorded during implementation

### `SN 1.4.6` was not a formatting error — it was the wrong sutta

The plan assumed the three-part SN references were PTS `volume.saṃyutta.sutta` and could be corrected by dropping the volume. That held for three of them, but not this one. Searching the canon for the quoted phrase `khaṇo vo mā upaccagā` returned no hit under any reading of `SN 1.4.6`; the phrase is in **SN 35.135 Khaṇasuttaṃ** (`s0304m_mul:135`), a sutta literally named for the word being discussed. Corrected to `SN 35.135 *Khaṇasuttaṃ*`.

This is the thread's strongest result: a **structural** check with no database access surfaced a **substantive** citation error, because a malformed shape is a reliable marker of a reference nobody verified.

### The three nibbidā references were never content-verified — and still aren't

`SN 5.46.20` → `SN 46.20`, `SN 4.35.45` → `SN 35.45`, `SN 5.51.4` → `SN 51.4`. All three verify as real suttas via `verify_citation`, and the PTS volume mapping is consistent (vol IV = SN 35, vol V = SN 45–56).

But the note itself records `Pāḷi: [Not directly retrieved but referenced in sources]` against each. **This thread fixed their form, not their substance** — whether those three suttas actually support the nibbidā claims made about them was never checked by the original run and was not checked here. Pre-existing gap, deliberately left; noted so it is not mistaken for verified.

### Footnote anchors vs rendered prose

7 of the 18 findings were footnote anchors (`[^MN118.150]`) rather than rendered text. An anchor is an identifier and does not display, so the reader-facing defect there is nil — the fix is machine-readability and consistency. The remaining 11 were rendered prose and genuinely misleading. Anchors were renamed with their definitions together (`[^MN118-para150]`), matching the note's existing `[^SN46.chain]` convention.
