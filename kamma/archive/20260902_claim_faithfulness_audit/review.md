# Review — quote-supports-claim check + falsifier line

## What was built

Two prompt edits to `skill/vicaya/SKILL.md`, exactly as specced. No code, no tests, no gates, no new subcommands.

1. A sixth review point in the Phase 6 source-armed reviewer's brief — quote-to-claim fit, naming the three failure shapes (over-reading, misreading, conflation) and requiring the resolved text as evidence. A short paragraph below the block says why this reviewer and not the others.
2. A falsifier line appended to the Phase 0 scope assumptions, in both the field description and the user-facing confirmation template, with a worked example distinguishing a concrete falsifier from a hedge.

## Coverage of the checks

- **Full suite:** 420 passed, 0 failed. Nothing in `tools/` was touched, so this is a smoke check rather than evidence about the change itself — the change lives in a prompt and cannot be unit-tested.
- **Scope confirmed before editing:** `scope_assumptions` is stored in the dossier header and only tested for truthiness when deciding whether to auto-write the Phase 0 gate. It is never parsed, so the trailing line is safe.
- **Blast radius confirmed:** the five-point checklist appears three times. Only the source-armed reviewer got point 6. The external cross-check chain and the self-review fallback were deliberately left at five — neither can resolve a passage, so asking either to judge quote-to-claim fit would produce guesses dressed as findings.
- **Not verified, and cannot be here:** whether the sixth point actually catches a misread in a live run. That needs a real `/vicaya` run with a known bad quote. Until then the mechanism is reasoned, not measured.

## Judgement

The first draft of this spec proposed a per-footnote claim audit with its own subcommand, marker, three refusal paths and a note-checker refactor. It was discarded before implementation: the verdict would have been written by the same agent that made the misread, so it would only ever have caught errors the agent already doubted — roughly thirty recorded entries per run guarding nothing.
The shipped version puts the same question to a reviewer that has database access, fresh eyes, and standing instructions to check rather than reason. Same intent, one paragraph, no new surface for a weaker agent to trip over.

Vicaya already carries a lot of end-of-run ceremony. The right lesson from the comparison was to ask an existing instrument a better question, not to add another gate.

## Follow-ups (not this thread)

- Secondary-source quality screening inside T3 — library folders are arbitrary ebook trees, so a self-published paperback currently carries the same weight as a critical edition. Considered, deferred by the user.
- Mandatory contradiction disclosure when sources genuinely conflict. Considered, deferred.
- Watch the next few runs for whether point 6 produces substantive findings or noise; the retrospective loop is the natural place for that.

## Review findings (self-audit + CodeRabbit)

**CodeRabbit** — 0 findings on the changed file. Scoped to the skill directory so the parallel OCR thread's dirty files stayed out of the diff.

**Self-audit — two findings, both fixed:**

1. *Stale count in the reviewer brief.* The line introducing the checklist still read "Report against these five" after a sixth point was added. A weaker agent reading the instruction before the list would have stopped at five and skipped the new check entirely — the exact failure the edit exists to prevent. Fixed to "these six". CodeRabbit did not catch this.
2. *Hard-wrapped prose.* The falsifier text was wrapped to match the surrounding bullet, against the project-wide one-line-per-paragraph rule. Unwrapped; the pre-existing wrapped lines above it were left alone rather than reflowed, to keep the diff to what this thread changed.

**Deliberately unchanged:** two other references to a "five"-point checklist remain in the file. Both belong to the external cross-check chain and its self-review fallback, which still have five points by design. Verified by reading each.

**Re-run after fixes:** 420 passed, 0 failed.

## Project docs

`tech.md` was not updated: this thread adds no tool, dependency, constraint or working assumption — it is prompt text inside an existing phase. The file is also currently modified by a parallel thread, so touching it would tangle two threads' changes.
