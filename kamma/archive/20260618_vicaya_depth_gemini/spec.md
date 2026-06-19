# Spec: Make Vicaya Notes Quote Their Evidence (fix Gemini under-quoting)

## Overview
Vicaya notes produced by Gemini orchestrators come out 3–5× shorter and
shallower than Claude-produced notes. Empirical check of the vault (notes record
their model in the `agent:` frontmatter field) confirmed this and, more
importantly, **diagnosed the actual failure mode**:

| Note | Model (`agent:`) | Words | Blockquote lines | Footnote defs |
|---|---|---|---|---|
| integrity-manipulative-tools-ebt | Gemini 3.5 Flash | 1,786 | **0** | 9 |
| santana-nibbana-abhidhamma | Gemini CLI | 1,205 | 6 | 7 |
| papanca-pali-canon | Claude Sonnet 4.6 | 9,623 | 42 | 25 |

The Gemini notes **cite** their sources (footnotes present) but do **not quote**
them — they collapse the full Pāḷi/English passages into inline prose summary.
The `integrity` note footnotes 9 sources and contains zero blockquotes. This
directly violates the existing Phase 5 rule "Prefer blockquotes (Rule P1) over
inline summaries everywhere," and it is the primary driver of the length/depth
gap. The mandatory meta-sections (`Sources Investigated, Not Used`, `Angles Not
Pursued`) are *present* in recent Gemini notes, so they are not the problem.

The failure mode is therefore **summarized-held-text / under-quoting**, not
"too few words." The corrective lever is the opposite of a word-count minimum:
**more verbatim quotation, less prose summary.**

## What it should do
1. **Prompt rule (canonical `skill/vicaya/SKILL.md`).** Add one hard,
   non-negotiable rule to Phase 5 and re-assert it in Phase 7: *every footnoted
   source must also appear as a full blockquote in its Evidence section; a
   footnote without its accompanying blockquote is a defect, not a style
   choice.* Frame it as evidence-fidelity, never as "write more" or "add
   paragraphs" (which would worsen the prose-summary problem).
2. **Mechanical check (`tools/note_checks.py`).** Extend `_validate_body` with a
   "cited-but-not-quoted" detector: when the count of footnote definitions
   substantially exceeds the count of blockquote lines, emit a `ValidationIssue`.
   Because the validator inspects the written `.md` file (it is reached by the
   Phase 7 `scratch-gate 7` path), it enforces the rule regardless of
   orchestrator — including the Gemini-CLI path that ignores prose instructions.
   This is the part Gemini "cannot summarize past."
3. **Sibling skills — heading-stability check only.** Do **not** copy any
   content into `vicaya-2-synthesize-review` or `vicaya-3-complete`. Per
   `kamma/project.md`, the siblings are section routers that read live sections
   from the canonical file by heading. The only obligation is to confirm the
   routed headings `### Phase 5 — Synthesis` and `### Phase 7 — Write the note`
   still exist unchanged after the edits.

## Diagnosis confidence
- 8/10 that under-quoting (footnotes without blockquotes) is the dominant Gemini
  failure mode — the `integrity` note (9 footnotes / 0 blockquotes) is
  unambiguous, and the pattern holds across the sampled Gemini notes.
- Open question (not blocking this fix): whether Gemini also *gathers* fewer
  sources in Phases 2–4, vs. only under-quoting what it gathered. Since the
  footnotes are present, under-quoting is happening regardless, so the fix is
  valid either way. Confirming the gather side would require diffing a Gemini
  run's `data/scratch/` dossier against its note; deferred.

## Assumptions & uncertainties
- The blockquote-vs-footnote ratio is a reliable proxy for under-quoting. Risk:
  some footnotes are legitimately metadata-only (URL blocked, no quotable text),
  so a strict 1:1 requirement would false-positive. Mitigation: use a tolerant
  threshold and default the issue to **warning** severity first, promoting to
  **error** only after calibration against existing good notes.
- The prompt rule alone is assumed insufficient for Gemini (it already ignores
  the existing "prefer blockquotes" prose), which is why the mechanical check is
  included rather than prose-only.

## Constraints
- **Maintenance rule** (`kamma/project.md`): `skill/vicaya/SKILL.md` is
  canonical; the staged siblings are routers, **not** alternate workflow
  documents — do not copy behavioral rules into them. Verify routed headings
  still resolve after edits.
- **Tone**: the prompt rule must stay strictly scholarly. It demands faithful
  quotation of gathered evidence, never filler or padding.
- **Reversibility**: the new validator check ships as a warning first so it
  cannot block legitimate notes until its threshold is tuned.

## How we'll know it's done
- `skill/vicaya/SKILL.md` Phase 5 and Phase 7 carry the explicit
  footnote-must-have-a-blockquote rule.
- `tools/note_checks.py` flags a note that footnotes sources without quoting
  them; a unit/smoke check demonstrates it fires on the `integrity` note pattern
  and stays silent on `papanca`.
- The routed headings in both sibling skills still resolve to the canonical file.
- **Acceptance is empirical, not just CI.** After merge, the user runs one real
  `/vicaya` task with a Gemini orchestrator (separate Gemini window), then
  returns to the advanced model to compare the new note against the measured
  baseline (~1,100–1,800 words, ~0 blockquote lines). Success = blockquote lines
  now scale with footnote count and word count rises toward the Claude range. If
  Gemini still under-quotes, the prose lever is exhausted and we escalate (hard
  error gate, or the deferred gather-phase investigation). See plan Phase 4.

## What's not included
- Changes to the gather phases (Phases 1–4) — deferred pending the gather-vs-quote
  diagnosis above.
- Any word-count or paragraph-count minimum (explicitly rejected: it targets the
  wrong lever and would amplify prose summary).
- Broader restructuring of the `uv run tools/...` pipeline beyond the single
  `_validate_body` check.
- Copying section content into the sibling router skills.
