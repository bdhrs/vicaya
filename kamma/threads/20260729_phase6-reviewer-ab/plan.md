# Plan — Phase 6 reviewer: A/B test with a noise floor

## Architecture Decisions

- The treatment lives in a `git worktree`, never a branch checked out in the main tree and never a stash. Parallel agent sessions and the user's own uncommitted work must be unaffected.
- The treatment diff is confined to the Phase 6 section of `skill/vicaya/SKILL.md` plus, if needed, one new reviewer prompt file. Any temptation to "fix while we're here" in Phases 0–5 or 7 invalidates the experiment.
- The tool-armed reviewer is a sub-agent, dispatched by the same mechanism Phases 2–4c already use (`SKILL.md:989`), with an explicitly narrowed tool set. Read-only is enforced by the tool set, not by asking the sub-agent nicely.
- The verification pass reuses the same sub-agent context via a follow-up message rather than spawning a fresh one — a fresh reviewer cannot confirm findings it never made.
- Blinding artifacts live in repo-local `temp/ab/` per Hard Rule 11. The mapping file is written but not read by the agent during scoring.
- Baselines are run **before** the treatment is written, so that no knowledge of the treatment's shape can leak into how the baselines are supervised.

---

## Phase 1 — Set up the experiment

- [ ] Agree the question with the user against the spec's selection criteria. Run `/vicaya-pre` on it to confirm no existing vault note covers it; pick another if it does.
  → verify: question recorded verbatim in this plan under this task, with the `/vicaya-pre` verdict

- [ ] Record the pre-registered decision rule and the scorecard into `temp/ab/protocol.md`, copied verbatim from `spec.md`, before any run starts.
  → verify: `protocol.md` exists and matches the spec's decision rule word for word

- [ ] Write `temp/ab/blind.py`: copy the three notes, strip the `agent:` frontmatter field and the footer identification line, shuffle, write `note-X/Y/Z.md`, write the mapping to `temp/ab/.mapping`, and print word counts per blinded label.
  → verify: run against three arbitrary existing vault notes; identity stripped, mapping written, word counts printed

## Phase 2 — Run the baselines

- [ ] Run `baseline-1` from `main`: `/vicaya <question>` with slug `<slug>-r1`. Do not tell the agent it is in an experiment. **Skip `sync_notes.py` and `sync_run_report.py`.** Record wall clock and whether compaction fired.
  → verify: note exists in the vault; no sync ran; timing recorded in `temp/ab/costs.md`

- [ ] Run `baseline-2` from `main`, slug `<slug>-r2`, same conditions.
  → verify: as above; note is distinct from `baseline-1`

- [ ] Eyeball the two baselines for *gross* divergence only — did one run fail a phase, hit a tool outage, or die to compaction? If either is structurally broken rather than merely different, discard and re-run that arm once. Do not discard a baseline for being *worse*; that is the variance being measured.
  → verify: an explicit note in `costs.md` that both baselines completed all phases, or which was re-run and why

## Phase 3 — Build the treatment

- [ ] `git worktree add` a treatment worktree. Confirm the main tree is untouched.
  → verify: `git status` in the main tree is unchanged from thread start

- [ ] Confirm spec assumption 2 in the worktree: can a sub-agent be given canon helpers with no write path to the dossier? Check the dispatch mechanism at `SKILL.md:989` and the `scratch-log` auto-logging behaviour. **If read-only cannot be enforced by tool set, stop and report to the user** — a reviewer that can edit the dossier is a different experiment.
  → verify: verdict recorded here with the mechanism named

- [ ] In the worktree, rewrite Phase 6 to add the tool-armed read-only reviewer sub-agent alongside the existing external chain. Reviewer brief: the same five-point checklist, plus an explicit instruction to resolve every doubted citation with `resolve-citation` before reporting it, and to report only what it checked.
  → verify: diff touches only the Phase 6 section (plus at most one new prompt file); `git diff --stat` confirms

- [ ] Add the verification pass: after integration, the same sub-agent re-reads the revised draft and confirms each accepted finding landed. One loop-back on unaddressed blockers, then record and proceed.
  → verify: Phase 6 exit criteria in the worktree require the verification result to be logged before `scratch-gate 6`

- [ ] Record the treatment's `SKILL.md` line delta in `costs.md`.
  → verify: line count added/removed recorded

## Phase 4 — Run the treatment

- [ ] Run `treatment` from the worktree, slug `<slug>-r3`, same question, sync skipped, agent not told it is in an experiment. Record wall clock, compaction, and whether the verification pass found unaddressed findings.
  → verify: note exists; timing and verification outcome in `costs.md`

## Phase 5 — Blind evaluation

- [ ] Run `blind.py` over the three notes. Confirm no agent identity survives in `temp/ab/`.
  → verify: `rg -i 'gemini|claude|opus|sonnet|agent:' temp/ab/note-*.md` returns nothing

- [ ] **HARD STOP — hand `note-X/Y/Z.md`, the scorecard, and the word counts to the user.** Do not open `.mapping`. Do not offer an opinion on which note is which or which is better. Do not compute anything.
  → verify: user has returned a filled scorecard for all three notes

## Phase 6 — Apply the pre-registered decision rule

- [ ] Reveal `.mapping`, map scores to arms, and apply the decision rule verbatim: kill condition first, then Ship / Inconclusive / Do not ship. Show the arithmetic.
  → verify: branch stated with `T`, `B₁`, `B₂`, and both inequalities evaluated

- [ ] Report the verdict together with the cost accounting from `costs.md`, and state plainly that three runs on one question do not generalise.
  → verify: verdict and costs presented in one place

- [ ] Execute the branch:
  - **Ship** → merge the worktree diff into `main` in a follow-up thread; open that thread also for isolating tool-access from the verification pass.
  - **Inconclusive** → ask the user: second question (three more runs) or close as churn. Do not default to shipping.
  - **Do not ship** → discard the worktree diff, record the null result in `kamma/lessons.md`.
  → verify: the chosen branch's artifacts exist; `main`'s `SKILL.md` unmodified under Inconclusive and Do-not-ship

- [ ] Decide the fate of the vault notes: keep at most one, delete the others **before** any future `sync_notes.py` run, so near-duplicates never reach the public notes repo. Confirm the deletion target with the user first.
  → verify: vault contains at most one note from this experiment; user confirmed which

## Phase 7 — Close out

- [ ] Remove the worktree. Clean `temp/ab/` except `protocol.md`, the scorecard, and `costs.md`.
  → verify: `git worktree list` shows only the main tree

- [ ] Cross-check against `20260729_citation-gate-backtest` (spec assumption 5): if both landed, note whether the treatment's citation-resolution work makes either redundant.
  → verify: a one-paragraph verdict in `review.md`

- [ ] Run the full suite. Fix every failure, including pre-existing ones, per `CLAUDE.md`.
  → verify: `uv run -m pytest tests/` green

- [ ] `/kamma:3-review`, then `/kamma:4-finalize`.
  → verify: `review.md` written; thread archived
