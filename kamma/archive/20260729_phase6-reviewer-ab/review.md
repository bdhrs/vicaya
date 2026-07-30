# Review — Phase 6 reviewer A/B

## Outcome: the pre-registered rule returned DO NOT SHIP. The user overrode it and the change was merged.

Both facts belong in the record. The measurement failed; the decision to ship it anyway was made with the failure in view.

## The measurement

Three arms, one question (*does an arahant still experience mental pain?*), blind-graded.

| | X = baseline A | Y = baseline B | Z = **treatment** |
|---|---|---|---|
| Citation accuracy | 5 | 5 | 5 |
| Tier integrity | 5 | 5 | 5 |
| Position coverage | 5 | 4 | **3** |
| Honest gaps | 4 | 5 | 5 |
| **Total** | **19** | **19** | **18** |

`T` = 18, `Bmax` = 19. `T ≤ Bmax` → **do not ship.**

The user's own verdict reached the same place faster and matters more than the scores: *"I honestly cannot tell them apart substantively."* If the domain expert cannot distinguish the treatment from two baselines, the treatment is not producing a better note. That is the whole measurement, and it came out negative.

**Grading caveat:** the scores above are not a blind grade. The coordinator had seen all three run reports and correctly de-anonymised X/Y/Z by content-matching before opening the mapping. Only the user's "cannot tell them apart" is genuinely blind, and it points the same way.

## What the treatment was actually better and worse at

**Better:** Z contains the sharpest single piece of scholarship in any of the three — Buddhaghosa glossing *ariyasāvaka* as *sotāpanna* on SN36.4 but as *khīṇāsavo ettha dhuraṃ, anāgāmīpi vaṭṭati* on SN36.6. It also had the disciplined stated-negative result (zero occurrences of *bhagavā anattamano* across the four Nikāyas, with both caveats) and MN140's *visaṃyutto naṃ vedeti*, the positive teaching the baselines underused.

**Worse:** Z never mentions Channa, Vakkali or Godhika. Three monks take the knife under severe illness and the texts call them arahants — the strongest canonical counter-evidence to the clean answer. Baseline A engages all three with Keown, Wynne and Horner. That absence is a missing objection, not a nuance. Z also had the thinnest library base (9 Calibre citations against A's 27).

## The signal the output could not show

The treatment's reviewer caught a real fabrication: the run had asserted that a commentary "does not gloss the term at all", built three paragraphs and an invented interpretive tension on it, and was wrong — it had read the paragraph through a 900-character truncation and asserted absence from a window that could not have shown it. The reviewer had database access, caught it, the run re-verified independently and rewrote.

That error never reached the note. So the mechanism worked and note quality cannot see it — a genuine limitation of measuring by output.

**This was explicitly not allowed to rescue the result.** Rescuing a failed pre-registered test with "but the process was better" is what pre-registration exists to prevent, and the evidence for it is an agent's self-report about its own run. Baseline A also caught a fabrication of its own (a wrong Nattier attribution) with no source-armed reviewer at all.

## Ship decision (user, 2026-07-30)

Merged on the user's instruction, conditional on cost being light. Cost measured: one isolated sub-agent, ~133k sub-agent tokens, ~3 minutes, against a 60–90 minute run, with **no orchestrator context consumed** — the reviewer's context is its own. That is light.

Two bugs the experiment exposed were fixed before merging:

1. **Return path.** The reviewer tried to `SendMessage` its verification to the orchestrator and it was lost — the dispatching session is not addressable from a sub-agent. The brief now says to return the report as the final message and explicitly not to use SendMessage. **Without this fix the verification half of the mechanism never closed.**
2. **Partial-landing checks.** The reviewer's most useful finding was that a caveat had been added to `## Critical Gaps` but not to the `## Findings` prose asserting the same claim, so a Findings-only reader would take the drafting agent's inference for something the tradition states. The verification brief now names this failure mode.

## Method problems found, and who found them

Recorded because the process errors were more instructive than the result:

- **Vault contamination between arms — found by the user.** Phase 1 searches the vault, so each arm would have found and built on its predecessors' notes. Contamination grows with run order, which in the planned sequence favours the treatment. Would have produced a fake positive. Fixed with a quarantine step between arms.
- **Uncommitted `main`.** Baselines ran from a dirty tree while the treatment worktree would have branched from a clean commit — a second, unrecorded difference between arms. Caught before any run.
- **Worktree config starvation.** `git worktree add` does not copy gitignored files, so the treatment worktree had no `.env`, no `CLAUDE.md`, no `.claude/`. The first treatment attempt died at Phase 1. Had it limped to completion instead, the treatment would have run under materially different config and the comparison would have been junk without showing it.
- **Cross-check flake, 34%.** 14 of 41 historical runs fell back to the `# SELF_REVIEW:` sentinel. Since the treatment's in-harness reviewer cannot flake the same way, a baseline drawing the fallback would have handed the treatment a win on plumbing rather than design. A validity condition was added; all three arms got real external reviews.
- **Operator interference — coordinator error.** Two `"Continue."` messages were sent into Arm B's live tool calls in the belief it had stalled. It had not; long tool calls produce no stream output. Arm B is contaminated by the coordinator, not the harness. Interruption counts: A 1, B 2, C 3 plus two session limits. No arm received content beyond the word "Continue."

## Cross-check against the citation-shape thread

Spec assumption 5 asked whether the two threads made each other redundant. They do not, and they failed in opposite directions. The citation-shape check is structural, needs no database, has precision 1.00, and found a substantive error (a passage cited as `SN 1.4.6` is SN 35.135 *Khaṇasuttaṃ*) — it shipped on measurement. The source-armed reviewer is semantic, needs the database, and failed its blind comparison — it shipped on judgement. Both catch citation defects; neither catches the other's class.

## Follow-up worth doing

Measure the reviewer on **caught errors per run**, not note quality. The one plausible benefit is upstream of the artifact, so the artifact is the wrong instrument. That experiment would need the return path fixed (done) and a way to count fabrications caught, which this design had no way to observe.
