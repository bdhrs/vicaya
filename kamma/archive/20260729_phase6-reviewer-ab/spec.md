# Spec — Phase 6 reviewer: A/B test with a noise floor

## Overview

Test whether arming the Phase 6 cross-check reviewer with source access, plus adding a verification pass after integration, produces a measurably better vault note — or just churn.

This is the "difficult" arm of the agentic-quality-loop assessment (2026-07-29). Unlike the citation-gate thread, the change here plausibly alters what the note *says*, so the evaluation instrument is the user's blind judgment of finished notes. The thread's job is to make that judgment trustworthy, which means controlling for run-to-run variance.

Depends on nothing. Can run before, after, or alongside `20260729_citation-gate-backtest`.

## The gap being closed

`SKILL.md:1789` documents the failure mode in the skill's own words: the Phase 6 reviewer "has no database access, so it reasons about citations probabilistically and errs both ways." Real runs saw it doubt correct citations (MN12, MN9, SN35.154, AN3.62, MN38, DN15 — all verified fine against the mūla) *and* miss real errors it never flagged (two passages footnoted "DN22-adjacent" / "DN14-adjacent", both actually DN16).

The skill's current mitigation is to distrust the reviewer in both directions and re-verify everything by hand. That works but pushes the whole burden back onto the agent that wrote the draft — the one least likely to catch its own errors.

Separately, agentic-quality-loop's step 5 has no vicaya equivalent: after the agent integrates review findings, nobody confirms the fixes actually landed. Phase 6 integrates and goes straight to Phase 7.

## The treatment

Phase 6 becomes:

1. **Unchanged** — the existing external cross-check via `VICAYA_CROSS_CHECK_CHAIN` (`opencode` / `agy`). Its value is model independence: a different model catches a different set of things. Nothing about this thread removes that.
2. **New** — a second reviewer running as a read-only sub-agent in-harness, with access to the canon DB helpers (`search-canon`, `resolve-citation`, `lookup-book`, `dpd.db`) and the scratch dossier, given the polished question and the Phase 5 draft. It may report findings; it may not edit the draft or the dossier. Its brief is the same five-point checklist, but it is instructed to **check rather than reason** — resolve every citation it doubts before reporting it.
3. **New** — a verification pass. After the orchestrator integrates findings, the same sub-agent re-reads the revised draft and confirms each accepted finding was addressed. Unaddressed blockers loop back once, then are recorded and the run proceeds.

The IRON RULE (`SKILL.md:1798`) applies unchanged — no reviewer, model, or process attribution anywhere in the note body.

### This is a bundle, and that is a deliberate compromise

Tool access and the verification pass are two changes tested together. If the treatment wins, a follow-up thread must isolate which half did the work. Testing them separately would need five research runs instead of three, and the marginal information does not justify the cost until we know the bundle does anything at all.

## Experiment design

### Arms — three runs, one question, same day

| arm | config | slug |
|---|---|---|
| `baseline-1` | current `SKILL.md`, from `main` | `<slug>-r1` |
| `baseline-2` | current `SKILL.md`, from `main` | `<slug>-r2` |
| `treatment` | modified Phase 6, from a worktree | `<slug>-r3` |

**`baseline-2` is the load-bearing arm.** It measures how far apart two notes land for no reason at all. Without it the comparison cannot distinguish signal from the variance that vicaya runs exhibit anyway — different search hits surface, different sources get pulled, different sections get expanded. A two-arm A/B here would produce a confident preference built mostly on noise, which is exactly how unnecessary churn gets shipped *because* it was tested.

### Question selection criteria

The user picks the question. It should:

- have a genuine canon base (not a purely thematic or comparative-religion question), so citation-checking has something to bite on;
- involve a live interpretive dispute, where a missed school or a mischaracterised position is possible;
- have **no existing vault note** — confirm with `/vicaya-pre` first, and pick another if it is already covered.

### Isolation

- Treatment runs from `git worktree add`, never a stash — parallel sessions and the user's own working tree must stay untouched.
- Three distinct slugs. Per `scratch-init` semantics, reusing a slug silently attaches new work to an existing dossier.
- **Sync is skipped for all three arms.** `sync_notes.py` and `sync_run_report.py` are not run. Three near-duplicate notes must not land in the public `bdhrs/vicaya-notes` repo. This is a deliberate, user-authorized deviation from the Phase 7 exit requirement, and it is recorded in each run's reflection.
- Neither baseline agent nor the treatment agent is told it is in an experiment. Each is given only `/vicaya <question>`.

### Blinding

A script copies the three notes to `temp/ab/`, then:

- strips the `agent:` frontmatter field and the footer self-identification line;
- shuffles the order and writes them as `note-X.md`, `note-Y.md`, `note-Z.md`;
- writes the mapping to `temp/ab/.mapping` — which the user does not open until scoring is complete.

**Blinding is imperfect and should be treated as such.** Word count, section shape, and citation density may differ enough between arms to be recognisable. Word counts are reported to the user anyway, since note length is a legitimate evaluation dimension, not just a tell.

### Scorecard

Per note, scored 1–5, on dimensions drawn from vicaya's own recurring failure modes:

1. **Citation accuracy** — spot-check five references against the canon
2. **Tier integrity** — is anything commentarial presented as mūla, or a teacher's reading as canonical
3. **Position coverage** — is a school, lineage, or reading you would expect missing
4. **Honest gaps** — does `## Critical Gaps` name real gaps, or is it filler

Plus, per note: **would I keep this note in the vault?** (yes/no), and a forced ranking 1st–3rd.

Total score per note is dimensions 1–4 summed: range 4–20.

## Pre-registered decision rule

Fixed before any run starts. Written here so it cannot be adjusted afterwards.

Let `T` = treatment total, `B₁` / `B₂` = baseline totals, `Bmax` = max(`B₁`, `B₂`).

- **Kill condition, checked first:** if treatment scores "no" on *would I keep this note* → **do not ship**, regardless of every other number.
- **Ship** if `T > Bmax` **and** `|B₁ − B₂| < (T − Bmax)`. The treatment must beat the better baseline by more than the two baselines differ from each other.
- **Inconclusive** if `T > Bmax` but `|B₁ − B₂| ≥ (T − Bmax)`. The treatment ranked first, but not by more than noise. The user then chooses: spend a second question (three more runs) or close as churn. **Defaulting to ship is not an option in this branch.**
- **Do not ship** if `T ≤ Bmax`. Delete the treatment, record the null result in `kamma/lessons.md`.

A null result is a successful outcome. The thread exists to find out.

## Cost accounting — reported alongside the verdict

Churn is not only about note quality. Recorded per arm:

- wall-clock duration;
- whether context compaction fired (a documented recurring failure — `runs/TODO.md` #78/#79 name sub-agent context exhaustion as a dominant signal);
- lines added to `SKILL.md` by the treatment.

A treatment that wins on quality while doubling run time or reliably triggering compaction is not obviously worth shipping. The user sees both numbers together.

## Explicitly out of scope

- Removing or replacing the external `opencode`/`agy` cross-check chain. Model independence is the property that makes cross-check valuable; the treatment adds to it.
- Isolating tool-access from the verification pass. Deferred to a follow-up, conditional on the bundle winning.
- Any change to Phases 0–5 or 7.
- Generalising the result. Three runs on one question cannot show the change helps in general, only that it helped here. The write-up must say so.

## Assumptions and uncertainties

1. **One question is enough to detect an effect worth shipping.** Genuinely uncertain. If the effect is real but small, three runs will land in the Inconclusive branch — which is the correct output, not a failure, but it means the thread may end without a decision.
2. **A read-only sub-agent can be given the helper tools without also being able to write the dossier.** Needs confirming against the sub-agent dispatch mechanism in `SKILL.md:989` before task 3. The `scratch-log` auto-logging behaviour may make read-only enforcement awkward.
3. **The treatment agent will not simply try harder because its instructions changed.** Unfalsifiable here. The diff is kept as narrow as possible to limit it.
4. **Both baselines are drawn from the same distribution.** They run the same code on the same question on the same day, but search results, web content, and model sampling all vary. If the baselines land absurdly far apart, that is itself the headline finding: vicaya's run-to-run variance swamps process improvements, and *no* Phase 6 change of this size is measurable.
5. Whether the treatment's own citation-resolution work overlaps enough with `20260729_citation-gate-backtest` to make one of the two redundant. Worth checking once both have results.

## Confidence

**6/10.** Lower than the citation-gate thread, and the reasons are structural rather than fixable. The diagnosis is solid — `SKILL.md:1789` documents the exact failure the treatment targets. But the measurement is expensive (three full research runs, likely 2–3 hours), a single question cannot generalise, and assumption 1 means the most probable single outcome is Inconclusive. The design's real merit is that it can return "this was churn" — and given how much of the original assessment turned out to duplicate work already in `note_checks.py`, that outcome deserves genuine probability.
