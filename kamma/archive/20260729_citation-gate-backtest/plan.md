# Plan — Citation gate, evaluated by backtest

## Architecture Decisions

- The check lives as a new subcommand in `tools/research_sources.py`, next to the other `scratch-*` / `check-*` verbs, not as a new script in `scripts/`. `scripts/` holds standalone Phase 7 workflows; this is a source helper.
- Existence verification **reuses** the verifier behind Phase 6 citation pre-annotation. If it is not currently importable, extract it into a function in place and call it from both — never a second implementation of the same lookup.
- The check is read-only and takes a note path. It does not touch the scratch dossier, so it is runnable over historical notes with no run state — which is what makes the backtest possible.
- Findings are printed as `<path>:<line>:<CLASS>:<ref>:<context>` — one line, stable order, greppable. The backtest aggregator parses this, so the format is the contract.
- `UNVERIFIABLE` never fails the exit code. `SKILL.md:1791` is explicit that Snp/Thag/Thig global verse numbers are legitimately unverifiable, and a check that fails on correct citations would be worse than no check.
- Nothing is wired into `SKILL.md` in this thread. The gate wiring is a separate follow-up, gated on the decision rule.

---

## Phase 1 — Measure before building

- [x] Sample 20 notes at random from `$VICAYA_VAULT_PATH/Vicaya/` and inventory every canon citation form that actually appears — frontmatter and inline. Write the inventory to `temp/citation-backtest/forms.md` with a count per form.
  → verify: `forms.md` lists each distinct form with an example and a count; total citations counted is stated
  **Done.** 904 citations, 38 distinct forms. A v1 measurement error (bare-abbreviation matching, `Thi`→"This" ×151, 392 phantom forms) was caught and fixed; recorded in `phase1-verdict.md` §1.

- [x] Assess extraction feasibility against that inventory. If the long tail of irregular forms exceeds ~20% of citations, **stop and report to the user** — the spec's assumption 2 has failed and the scope needs revising before any code is written.
  → verify: an explicit feasibility verdict recorded in `forms.md`, with the tail percentage
  **PASSES.** Top-20 forms cover 96.6%; singletons 1.0%. Assumption 2 holds.

- [x] Confirm the Phase 6 existence verifier is reusable. Locate it in `tools/research_sources.py`, record its function name and signature, and note whether it is importable as-is or needs extracting.
  → verify: function name + file:line recorded in `plan.md` under this task
  **Done.** `verify_citation(ref: str, dpd_db: Path | None = None) -> dict` at `tools/research_sources.py:1771`. Directly importable; no extraction needed. Returns verdict `verified` / `unverifiable-form` / `rejected`.

- [x] **Unplanned, added during Phase 1:** probe the actual yield of the specced checks before building them, so the thread cannot spend Phase 2 on a check the corpus does not support.
  → verify: `phase1-verdict.md` records per-class yield with a precision estimate
  **Done — and it invalidated two of three premises.** `ADJACENT` class dead (3 probes, 1 real signal in 260 notes). Human-ref↔CST-paranum cross-check real but only in 4.2% of notes. Existence check: 584 rejections across 76 notes, but 85% are the uncovered `Vinaya 02 §N` convention — raw precision ≈4%, against a pre-registered threshold of 0.7.

- [x] **HARD STOP — user decides scope.** Three options in `phase1-verdict.md` §Recommendation. Do not proceed to Phase 2 under the original spec; it would fail its own decision rule.
  → verify: user has chosen an option
  **Done.** Option 1 — narrow to structural malformed-reference detection, no database. Verifier gaps left alone, not filed. Recorded in `spec.md` §Scope decision.

## Phase 2 — Build the check (narrowed scope)

- [x] Add a citation **shape** table to `tools/research_sources.py`: per collection, the number of addressing segments and the leading-segment maximum (MN 1×152, DN 1×34, SN 2×56, AN 2×11, Dhp 1×423, Khp 1×9, Snp 2×5, Ud 2×8, Iti 2×4, Thag 2×21, Thig 2×16). Data only, no lookups.
  → verify: table present; every collection in the Phase 1 form inventory has an entry or is explicitly listed as unhandled

- [x] Add `check-citation-shape <note-path>`: extract citations using the Phase 1 forms, classify each as `OK` / `DEPTH` (too many segments) / `RANGE` (leading segment over maximum) / `UNHANDLED` (collection not in the table), print `<path>:<line>:<CLASS>:<ref>:<context>`, exit nonzero on any `DEPTH` or `RANGE`.
  → verify: exits 1 on a fixture containing `MN118.150`, naming the ref; exits 0 on a recent known-good note

- [x] Handle the shapes that must **not** flag: `Vinaya 02 §679` (book + § suffix, not a segment), `AN1.41-50 §48` (range plus suffix), `Dhp 277–279` (range), `SN 22.59` (space separator), bare nipātas (`AN 3`).
  → verify: a fixture containing all five is entirely `OK`

- [x] Add pytest coverage in `tests/`: one case per output class, plus a regression fixture per real defect found in Phase 1 (`MN118.150`, `DN2.244`, `DN22.385`, `SN 5.46.20`, `Khp 5.10`).
  → verify: `uv run -m pytest tests/ -k citation` passes; all five Phase 1 defects classify as `DEPTH`

## Phase 3 — Run the backtest

- [x] Write `temp/citation-backtest/run_backtest.py` (throwaway, repo-local per Hard Rule 11): walk all 260 notes, run the check, aggregate into `report.md` with per-note rows and summary counts by class.
  → verify: `report.md` covers every note found; note count matches the directory listing

- [x] Draw findings into a `## Worklist` section of `report.md`, each with the citation, the surrounding sentence, and a blank verdict field. The narrowed check is expected to yield ~8 distinct defects, so **grade every finding** rather than sampling 15; sample only if the count exceeds 15.
  → verify: every finding present (or 15 sampled if more), each with enough context to adjudicate without opening the note

- [x] **HARD STOP — hand the report to the user.** Do not compute precision, do not interpret the result, do not touch `SKILL.md`. The user marks each sampled finding real defect / false positive / unclear.
  → verify: user has returned verdicts
  **Done.** All 18 findings graded real defect; zero false positives. The three-part SN group was resolved by the user as a mistake, not a citation convention.

## Phase 4 — Apply the pre-registered decision rule

- [x] Compute `P` from the user's verdicts and apply the spec's decision rule verbatim. Report which branch fired and why, without arguing for the check.
  → verify: branch stated with the arithmetic shown
  **`P` = 18/(18+0) = 1.00; notes affected = 6.** `1.00 ≥ 0.7` and `6 ≥ 3` → **ship branch**. Arithmetic in `temp/citation-backtest/verdicts.md`.

- [x] Execute the branch:
  - `P ≥ 0.7`, ≥3 notes affected → open a follow-up thread for Phase 7 gate wiring; leave `SKILL.md` untouched in this thread.
  - `P ≥ 0.7`, <3 notes → keep the subcommand, document it in `skill/vicaya/README.md` as a manual tool only.
  - `P < 0.7` → delete the subcommand and its tests, record the null result in `kamma/lessons.md`.
  → verify: the chosen branch's artifacts exist; no `SKILL.md` gate wiring added under any branch
  **Done.** Follow-up thread `20260729_citation-shape-gate-wiring` created with spec + plan. `SKILL.md` untouched in this thread.

- [x] Run the full suite. Fix every failure, including pre-existing ones, per `CLAUDE.md`.
  → verify: `uv run -m pytest tests/` green
  **338 passed, 1 skipped.** Pre-existing Pyright diagnostics in `research_sources.py` (optional `youtube_transcript_api` import; intentional re-export shims already carrying `noqa`) were left alone deliberately — none are in code this thread wrote, and "fixing" the shims would break the scratch module contract.

## Phase 5 — Close out

- [x] Clean `temp/citation-backtest/` of disposable files, preserving `report.md` and the user's verdicts until finalize.
  → verify: only the report and verdicts remain

- [ ] `/kamma:3-review`, then `/kamma:4-finalize`.
  → verify: `review.md` written; thread archived
