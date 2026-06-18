# Plan: Make Vicaya Notes Quote Their Evidence (fix Gemini under-quoting)

## Session continuity (read first)
This thread spans **multiple fresh sessions and model switches** (advanced model
for plan/implement/analysis; a separate Gemini window for the Phase 4 research
run). **Assume zero conversation memory carries across a switch.** The thread
files on disk are the only source of truth:
- `spec.md` — problem, diagnosis, baseline data table, acceptance criteria.
- `plan.md` — this file: decisions, phases, the decided threshold.
- `handoff.md` — **live state**: what is done, what is next, exact commands.

**Rule:** at every phase boundary and before any window/model switch, update
`handoff.md` (what changed, current state, next action, anything a cold reader
needs). Do not hold results — baseline numbers, the new note's measurements, the
chosen outcome — only in context. This mirrors the project's scratch-file
discipline: write at the end of EACH phase, not just at the end.

## Architecture Decisions
- **Lever = quotation fidelity, not length.** Vault evidence shows Gemini notes
  footnote sources without quoting them (e.g. `integrity` note: 9 footnotes, 0
  blockquotes). The fix enforces "every footnoted source also appears as a full
  blockquote," never a word/paragraph minimum.
- **Prompt + mechanical check, not prompt alone.** Gemini already ignores the
  existing prose rule "prefer blockquotes over inline summaries," so a stronger
  prose rule is necessary but not sufficient. We add a check in the Phase 7 note
  validator (`tools/note_checks.py`), which inspects the written `.md` file and
  is therefore model-agnostic — it holds even on the Gemini-CLI orchestrator
  path. This is a deliberate, justified expansion beyond the original
  "prompt-only" scope.
- **No sibling content-sync.** `vicaya-2-synthesize-review` and
  `vicaya-3-complete` are section routers (`kamma/project.md`), not copies. They
  read live sections by heading from `skill/vicaya/SKILL.md`. The only sibling
  obligation is to confirm the routed headings still exist after edits.
- **Hook point confirmed.** `tools/note_checks.py::_validate_body` (line 186)
  already emits `ValidationIssue`s with error/warning severity, checks
  `REQUIRED_SECTIONS`, counts `[REJECTED]` tags, and matches footnote-definition
  lines via `^\[\^[^\]]+\]:`. The new check slots in alongside these.
- **Severity + threshold: decided (best judgment, calibrate empirically).** Ship
  the check as a `warning` (like `SOFT_SECTIONS`) so it cannot block legitimate
  notes (e.g. metadata-only footnotes with nothing quotable). **Fire condition:**
  `footnote_defs >= 3` AND `blockquote_lines < footnote_defs`, where
  `blockquote_lines` counts `^>` lines and `footnote_defs` counts `^\[\^…\]:`
  lines. Rationale against the measured baseline: `integrity` (9 fn / 0 bq) →
  fires; `santana` (7 fn / 6 bq, a genuinely thin Gemini note) → fires;
  `papanca` (25 fn / 42 bq) → silent. The `>= 3` floor exempts short/structural
  notes. This default is intentionally committed now and **re-tuned in Phase 4**
  after one real Gemini run; promotion `warning → error` (hard gate) is held
  until the false-positive rate is observed on real notes.

## Phase 1: Prompt rule in the canonical skill

- [x] Add the hard quotation rule to `### Phase 5 — Synthesis` in
  `skill/vicaya/SKILL.md`, near the existing "Use all relevant evidence" /
  "Prefer blockquotes (Rule P1)" lines: *every footnoted source must also appear
  as a full blockquote in its Evidence section; a footnote without its blockquote
  is a defect.* Keep it evidence-fidelity framed; do not add any length target.
  → verify: read Phase 5 and confirm the rule is present and references the
  footnote→blockquote requirement explicitly.
- [x] Re-assert the same rule at the top of `### Phase 7 — Write the note` (Gemini
  de-weights mid-block instructions, so it must appear at section entry).
  → verify: read Phase 7 and confirm the rule is restated before the template.
- [x] Confirm no heading text changed: `### Phase 5 — Synthesis` and
  `### Phase 7 — Write the note` are byte-for-byte intact.
  → verify: `grep -n "^### Phase 5 — Synthesis\|^### Phase 7 — Write the note" skill/vicaya/SKILL.md`

## Phase 2: Mechanical under-quoting check in the note validator

- [x] In `tools/note_checks.py::_validate_body`, count footnote definitions
  (existing `^\[\^[^\]]+\]:` pattern) and blockquote lines (`^>`), and emit a
  `ValidationIssue("under-quoted-evidence", …, severity="warning")` when
  `footnote_defs >= 3` AND `blockquote_lines < footnote_defs` (the decided
  default threshold above).
  → verify: read the diff; confirm the new check reuses the existing footnote
  regex and adds a blockquote counter, and defaults to warning.
- [x] Add/extend a check in `tools/` tests or a smoke run: the detector fires on
  the `integrity`-style pattern (many footnotes, ~0 blockquotes) and stays
  silent on `papanca` (footnotes backed by blockquotes).
  → verify: run the project's note-check test path (e.g.
  `uv run pytest` for `note_checks`, or `uv run tools/research_sources.py`
  validate on the two sample notes) and confirm expected fire/silent behavior.
- [x] Confirm the check is reached by the Phase 7 gate path (`scratch-gate 7`
  → note validation) so it actually guards vault writes.
  → verify: trace `scratch-gate 7` / `scratch_set_note` → `validate_note_file`
  in `tools/research_sources.py` and confirm `_validate_body` runs.

## Phase 3: Sibling router heading-stability check (no content copy)

- [x] Confirm `vicaya-2-synthesize-review` and `vicaya-3-complete` route lists
  still resolve to the (unchanged) canonical headings; copy **nothing** into
  them.
  → verify: read both Route Lists and confirm `### Phase 5 — Synthesis` /
  `### Phase 7 — Write the note` appear and match the canonical headings exactly.

## Phase 4: Empirical verification loop (human-in-the-loop)

This phase is part of "done" — the change is not validated by the automated
tests alone, only by a real Gemini run. It spans two windows.

Baseline to beat (measured Gemini notes): ~1,100–1,800 words, blockquote lines
at or near zero, footnote defs 7–9.

- [ ] **(User, separate Gemini window)** After Phases 1–3 are merged, run one
  real `/vicaya` research task with a Gemini orchestrator on a topic comparable
  to the baseline notes. Let it write the note to the vault as normal.
  → verify: a new note exists in `vault/Vicaya/` with `agent:` recording a
  Gemini model.
- [ ] **(Advanced model, this window)** User returns; analyze the new note
  against the baseline. Measure: word count, `^>` blockquote lines, `^\[\^…\]:`
  footnote defs, and whether the under-quoted-evidence warning fired during its
  Phase 7 gate.
  → verify: produce a before/after comparison vs. the baseline table in spec.md.
- [ ] **Decide outcome:**
  - *Success* = blockquote lines now scale with footnotes (roughly `bq >= fn`)
    and word count rises toward the Claude range. → Consider promoting the check
    `warning → error` (hard gate); record the calibrated threshold.
  - *Partial* (more quotes but still thin, or threshold mis-fires) → re-tune the
    threshold / sharpen the Phase 5/7 wording; iterate.
  - *No change* (Gemini still under-quotes despite prompt + warning) → the prose
    lever is exhausted; escalate to either a hard error gate or the deferred
    gather-phase (Phases 2–4) investigation noted in spec.md.
  → verify: the chosen next step is recorded in the thread before closing.

## Validation summary
- Format/lint/type/test per project tooling on `tools/note_checks.py` changes
  (`uv run` the project-local format, lint, type, and test commands).
- Report tested vs not tested. The automated tests cover the detector logic
  only; the end-to-end "Gemini now quotes its evidence" outcome is validated by
  the Phase 4 human-in-the-loop run, not by CI.

## Rejected / superseded approach (logged per workflow rule)
- Original spec/plan proposed (a) minimum-paragraph-per-perspective length
  targets and (b) mirroring section content into the sibling skills. Both
  dropped: (a) targets the wrong lever — the defect is too much prose summary and
  too little quotation, so a length minimum amplifies the problem; (b)
  contradicts `kamma/project.md` (siblings are routers; do not copy behavioral
  rules into them).
