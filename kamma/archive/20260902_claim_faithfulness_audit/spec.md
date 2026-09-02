# Spec — quote-supports-claim check + falsifier line

## Origin

Comparison of vicaya against [academic-research-skills](https://github.com/Imbad0202/academic-research-skills) (ARS).
Vicaya already has, in sharper domain-native form, nearly every control ARS advertises: phase gates that refuse to advance, a pre-drafting Devil's Advocate pass, dual review with a verification loop-back, citation-existence annotation, a structural citation-shape check, a self-audit, and a retrospective improvement loop.
Everything else ARS ships (PRISMA, meta-analysis, risk-of-bias, thirteen agents, ten stages, numeric concession scoring, Socratic non-generation mode, governance docs) is domain-irrelevant or ceremony on machinery that already self-gates. Rejected.

Two real gaps remain. Both are fixed with prompt text. **No code, no new subcommands, no new gates.**

An earlier draft of this spec proposed a per-footnote claim audit with its own subcommand and hard gate. It was discarded: the verdict would be written by the same agent that made the misread, so it would catch only the errors the agent already doubted — thirty entries of ceremony per run guarding nothing. Recorded here so it is not re-proposed.

## Problem

**1. Nothing checks that a quoted passage supports the claim built on it.**
The chain verifies that a citation exists, that its shape is well-formed, and that a blockquote is present. None of them look at the relationship between the sentence and the quote.
`SKILL.md` says so outright — the shape check "says nothing about whether the cited passage supports the claim" — and the Phase 6 notes record real misreads (`asantasanto` read as `asanta`) and conceptual conflations passing every existing check.

The source-armed reviewer is already the right instrument: database access, read-only, fresh eyes, and told to check rather than reason. Its five points cover perspective, tier integrity, disputed consensus, factual accuracy and general — "factual accuracy" is about whether references are *correct*, not whether quotes carry the weight put on them. It simply is not asked.

**2. Nothing states what would falsify the expected answer.**
Phase 0 records textual scope, interpretive scope, depth, practical angle and seeds. None of those name the finding that would show the expected answer wrong, so a run can confirm its own framing without ever noticing.

## Requirements

### R1 — Sixth review point for the source-armed reviewer

Add one numbered point to the source-armed reviewer's brief in Phase 6:

> 6. **Quote-to-claim fit** — for each blockquote, resolve the passage and check whether it actually says what the sentence built on it claims. Report over-reading (the quote is weaker than the claim), misreading (the Pāḷi does not mean what the claim takes it to mean), and conflation (two distinct terms treated as one). Paste the resolved text that establishes each finding.

Its findings are integrated under the discipline already stated for that reviewer — verify before accepting, drop what cannot be substantiated, and the IRON RULE applies unchanged. The existing one-loop-back and log-don't-block rule covers it; no new gate.

### R2 — Falsifier line in the Phase 0 scope assumptions

`scope_assumptions` is already a free-text field written into the dossier header at init. Phase 0 instructs the agent to end it with one line:

> Falsifier: <the finding that would show the expected answer is wrong>

No new field, no CLI flag, no caller sweep.

## Non-goals

- No new subcommand, gate, marker, or refusal path.
- No changes to `tools/`, no new tests.
- No secondary-source quality screen and no mandatory contradiction section — considered, deferred.
- No automated judging of quote-to-claim fit. A reviewer with database access reports; the drafter verifies.

## Affected files

| File | Change |
|---|---|
| `skill/vicaya/SKILL.md` | one review point added to the Phase 6 source-armed reviewer brief; one falsifier instruction added to Phase 0 |

## Assumptions and uncertainties

- The Phase 6 reviewer brief is a literal prompt block in `SKILL.md`; adding a sixth point needs no matching change in `tools/`. **Confirmed by reading it.**
- `scope_assumptions` accepts arbitrary free text and is not parsed downstream. **To confirm before editing.**
- The Phase 6 review checklist appears in more than one place (external cross-check prompt, source-armed reviewer brief, self-review fallback). Only the source-armed reviewer gets point 6 — it is the only one that can resolve a passage. The external chain has no database and would guess.

## Size note

This is two prompt edits. It is thread-sized only because the evaluation behind it was worth recording; the change itself is `/kamma:quick` territory.

## Confidence

9/10.
