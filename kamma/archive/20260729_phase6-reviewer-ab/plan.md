# Plan — Phase 6 reviewer: A/B test with a noise floor

## Architecture Decisions

- The treatment lives in a `git worktree`, never a branch checked out in the main tree and never a stash. Parallel agent sessions and the user's own uncommitted work must be unaffected.
- The treatment diff is confined to the Phase 6 section of `skill/vicaya/SKILL.md` plus, if needed, one new reviewer prompt file. Any temptation to "fix while we're here" in Phases 0–5 or 7 invalidates the experiment.
- The tool-armed reviewer is a sub-agent, dispatched by the same mechanism Phases 2–4c already use (`SKILL.md:989`), with an explicitly narrowed tool set. Read-only is enforced by the tool set, not by asking the sub-agent nicely.
- The verification pass reuses the same sub-agent context via a follow-up message rather than spawning a fresh one — a fresh reviewer cannot confirm findings it never made.
- Blinding artifacts live in repo-local `temp/ab/` per Hard Rule 11. The mapping file is written but not read by the agent during scoring.
- **Each arm's note is quarantined out of the vault before the next arm runs.** Phase 1 searches the vault, so a note left in place would be found and built on by every later arm — contamination that grows with run order and would hand the last-run arm an unearned advantage. Caught by the user during Phase 1 setup, before any run started. `/vicaya` was checked and does not touch `summary-vicaya.md` or `catalog-by-topics.md`, so the note and its PDF are the only vectors.
- Baselines are run **before** the treatment is written, so that no knowledge of the treatment's shape can leak into how the baselines are supervised.
- **Every arm runs in its own fresh session** (user, 2026-07-30), including the first. This preserves agent blindness — no executing session knows an experiment exists — and equalises context budget across arms, removing a confound that would otherwise track arm order exactly.

---

## Phase 1 — Set up the experiment

- [x] Agree the question with the user against the spec's selection criteria. Run `/vicaya-pre` on it to confirm no existing vault note covers it; pick another if it does.
  → verify: question recorded verbatim in this plan under this task, with the `/vicaya-pre` verdict

- [x] Record the pre-registered decision rule and the scorecard into `temp/ab/protocol.md`, copied verbatim from `spec.md`, before any run starts.
  → verify: `protocol.md` exists and matches the spec's decision rule word for word

- [x] Write `temp/ab/blind.py`: copy the three notes, strip the `agent:` frontmatter field and the footer identification line, shuffle, write `note-X/Y/Z.md`, write the mapping to `temp/ab/.mapping`, and print word counts per blinded label.
  → verify: run against three arbitrary existing vault notes; identity stripped, mapping written, word counts printed

## Phase 2 — Run the baselines

- [x] Run `baseline-1` **in a fresh session** from `main` (commit `0ec40c1`), slug `arahant-domanassa-a`, using the launch prompt in `temp/ab/RUNBOOK.md` verbatim and nothing else. **Skip `sync_notes.py` and `sync_run_report.py`.** Record wall clock and whether compaction fired.
  → verify: note exists in the vault; no sync ran; timing recorded in `temp/ab/costs.md`

- [x] **Quarantine baseline-1's note out of the vault before any further arm runs:** `uv run temp/ab/quarantine.py arahant-domanassa-a`.
  → verify: script reports the vault clean of the slug; note and PDF now under `temp/ab/runs/`

- [x] Run `baseline-2` **in its own fresh session** from `main`, slug `arahant-domanassa-b`, same conditions. This arm is the noise floor — not a spare, and not skippable.
  → verify: as above; note is distinct from `baseline-1`

- [x] Quarantine baseline-2's note: `uv run temp/ab/quarantine.py arahant-domanassa-b`.
  → verify: vault clean of the slug

- [x] Eyeball the two baselines for *gross* divergence only — did one run fail a phase, hit a tool outage, or die to compaction? If either is structurally broken rather than merely different, discard and re-run that arm once. Do not discard a baseline for being *worse*; that is the variance being measured.
  → verify: an explicit note in `costs.md` that both baselines completed all phases, or which was re-run and why

## Phase 3 — Build the treatment

- [x] `git worktree add` a treatment worktree. Confirm the main tree is untouched.
  → verify: `git status` in the main tree is unchanged from thread start

- [x] Confirm spec assumption 2 in the worktree: can a sub-agent be given canon helpers with no write path to the dossier? Check the dispatch mechanism at `SKILL.md:989` and the `scratch-log` auto-logging behaviour. **If read-only cannot be enforced by tool set, stop and report to the user** — a reviewer that can edit the dossier is a different experiment.
  → verify: verdict recorded here with the mechanism named

- [x] In the worktree, rewrite Phase 6 to add the tool-armed read-only reviewer sub-agent alongside the existing external chain. Reviewer brief: the same five-point checklist, plus an explicit instruction to resolve every doubted citation with `resolve-citation` before reporting it, and to report only what it checked.
  → verify: diff touches only the Phase 6 section (plus at most one new prompt file); `git diff --stat` confirms

- [x] Add the verification pass: after integration, the same sub-agent re-reads the revised draft and confirms each accepted finding landed. One loop-back on unaddressed blockers, then record and proceed.
  → verify: Phase 6 exit criteria in the worktree require the verification result to be logged before `scratch-gate 6`

- [x] Record the treatment's `SKILL.md` line delta in `costs.md`.
  → verify: line count added/removed recorded

## Phase 4 — Run the treatment

- [x] Run `treatment` **in its own fresh session** from the worktree, slug `arahant-domanassa-c`, launch prompt identical to the baselines except the slug, sync skipped. Record wall clock, compaction, and whether the verification pass found unaddressed findings.
  → verify: note exists; timing and verification outcome in `costs.md`

- [x] Quarantine the treatment's note: `uv run temp/ab/quarantine.py arahant-domanassa-c`.
  → verify: vault clean of the slug; all three notes now under `temp/ab/runs/`

## Phase 5 — Blind evaluation

- [x] Run `blind.py` over the three notes. Confirm no agent identity survives in `temp/ab/`.
  → verify: `rg -i 'gemini|claude|opus|sonnet|agent:' temp/ab/note-*.md` returns nothing

- [x] **HARD STOP — hand `note-X/Y/Z.md`, the scorecard, and the word counts to the user.** Do not open `.mapping`. Do not offer an opinion on which note is which or which is better. Do not compute anything.
  → verify: user has returned a filled scorecard for all three notes

## Phase 6 — Apply the pre-registered decision rule

- [x] Reveal `.mapping`, map scores to arms, and apply the decision rule verbatim: kill condition first, then Ship / Inconclusive / Do not ship. Show the arithmetic.
  → verify: branch stated with `T`, `B₁`, `B₂`, and both inequalities evaluated

- [x] Report the verdict together with the cost accounting from `costs.md`, and state plainly that three runs on one question do not generalise.
  → verify: verdict and costs presented in one place

- [x] Execute the branch:
  - **Ship** → merge the worktree diff into `main` in a follow-up thread; open that thread also for isolating tool-access from the verification pass.
  - **Inconclusive** → ask the user: second question (three more runs) or close as churn. Do not default to shipping.
  - **Do not ship** → discard the worktree diff, record the null result in `kamma/lessons.md`.
  → verify: the chosen branch's artifacts exist; `main`'s `SKILL.md` unmodified under Inconclusive and Do-not-ship

- [x] Decide the fate of the vault notes: keep at most one, delete the others **before** any future `sync_notes.py` run, so near-duplicates never reach the public notes repo. Confirm the deletion target with the user first.
  → verify: vault contains at most one note from this experiment; user confirmed which

## Phase 7 — Close out

- [x] Remove the worktree. Clean `temp/ab/` except `protocol.md`, the scorecard, and `costs.md`.
  → verify: `git worktree list` shows only the main tree

- [x] Cross-check against `20260729_citation-gate-backtest` (spec assumption 5): if both landed, note whether the treatment's citation-resolution work makes either redundant.
  → verify: a one-paragraph verdict in `review.md`

- [x] Run the full suite. Fix every failure, including pre-existing ones, per `CLAUDE.md`.
  → verify: `uv run -m pytest tests/` green

- [ ] `/kamma:3-review`, then `/kamma:4-finalize`.
  → verify: `review.md` written; thread archived

---

## Phase 1 outcomes — 2026-07-30

**Question fixed:** *Does an arahant still experience mental pain (domanassa), or only bodily pain (kāyika dukkha)?* `/vicaya-pre` verdict: *Review first, then `/vicaya`* — three notes give partial coverage of the two-dart simile, but all stop at the *instructed noble disciple*, a category spanning stream-enterer to arahant. The tension between that and the Abhidhamma position that domanassa is abandoned only at anāgāmi is unexamined in the vault.

**Base commit `0ec40c1`.** The citation-shape work was committed before any arm runs, so all three arms share an identical starting tree. Running baselines from an uncommitted `main` while the treatment ran from a clean worktree would have introduced a second difference between arms and invalidated the comparison. Caught before any run started, not after.

**Spec assumption 2 resolved — read-only enforcement is possible, with a caveat.** A reviewer sub-agent can be denied `Edit`/`Write`/`NotebookEdit` by tool set, which prevents it editing the draft or dossier directly. But helper calls auto-log to the scratch, so its own lookups *will* be recorded under Phase 6 via Bash regardless. That is acceptable — arguably correct, since Phase 6 evidence belongs in the scratch and the gate already requires a Phase 6 entry — but it means "read-only" here means "cannot edit the draft", not "leaves no trace". Not a stopper.

**Execution model changed: one fresh session per arm** (user, 2026-07-30). The original plan had this session executing the arms, which would have broken agent blindness — the operator would know which arm was which while running it. Running each arm in a clean session restores blindness *and* equalises context budget across arms, removing a confound that would have tracked arm order exactly. Launch prompts are fixed in `temp/ab/RUNBOOK.md` and are the complete input for each arm.

**Sub-agent dispatch authorised** (user, 2026-07-30) — the skill's normal per-phase mode, used identically by all three arms.

**Blinding verified before it mattered.** `blind.py` was dry-run against three existing vault notes. It caught a third identity form not in the spec — `*Researched by [Vicaya](…) using <model> on <date>*`, distinct from the `*Agent:` footer — and a version-number leak where "Claude Opus 4.8" reduced to `[redacted] 4.8`, still identifying the arm. Both fixed and re-verified.

---

## Thread outcome

See `review.md`. Pre-registered rule returned **do not ship** (`T`=18 ≤ `Bmax`=19; user could not distinguish the arms). **User overrode and merged**, cost measured light. Two bugs fixed before merge: the reviewer's lost return path, and partial-landing checks in the verification brief.

Deviation from the plan's Ship/Inconclusive/Do-not-ship branches: none of the three fired as written. The rule said do-not-ship; the user shipped anyway with the failure in view. Recorded as an override rather than dressed up as a rule outcome.

The three arm notes were superseded by a single merged note compiled from all three, published to the vault at `Vicaya/2026-07-30 - arahant-domanassa-mental-pain.md` (16,904 words, validator PASS, citation-shape clean). The arm notes and `temp/ab/` scaffolding were then deleted.
