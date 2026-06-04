## Thread
- **ID:** 20260602_vicaya-staged-skills
- **Objective:** Split Vicaya into a permanent full-run skill plus model-aware staged skills.
- **Strict audit basis:** User clarified on 2026-06-02 that the staged skills must be an exact behavioral partition of the existing monolithic `skill/vicaya/SKILL.md`. Summaries, abbreviated references, weakened rules, new semantics, or omitted operational details are not acceptable.

## Files Changed
- `skill/vicaya/SKILL.md` - canonical full-run skill; used as the source of truth for this audit.
- `skill/vicaya/shared/core.md` - staged shared core rules.
- `skill/vicaya/shared/scope.md` - staged Phase 0 reference.
- `skill/vicaya/shared/sources.md` - staged Phase 1-4c reference.
- `skill/vicaya/shared/synthesis.md` - staged Phase 5-6 reference.
- `skill/vicaya/shared/completion.md` - staged Phase 7 reference.
- `skill/vicaya-0-scope/SKILL.md` - staged Phase 0 skill.
- `skill/vicaya-1-gather/SKILL.md` - staged Phase 1-4c skill.
- `skill/vicaya-2-synthesize-review/SKILL.md` - staged Phase 5-6 skill.
- `skill/vicaya-3-complete/SKILL.md` - staged Phase 7 skill.
- `kamma/threads/20260602_vicaya-staged-skills/review.md` - replaced the previous `PASSED` review with this stricter blocking audit.

## Findings
| # | Severity | Location | What | Why | Fix |
|---|----------|----------|------|-----|-----|
| 1 | blocking | `skill/vicaya/shared/sources.md:11` vs `skill/vicaya/SKILL.md:514` | The 16 investigation angles are compressed into a six-line topic list. The original contains detailed applicability rules, where-to-search rules, satisfying-hit criteria, and special warnings per angle. | Phase 1 triage cannot produce the same search scope. This directly explains missing evidence in staged runs. | Carry the original Investigation angles section into the staged source path without semantic compression, or split it verbatim into an angle reference loaded by `vicaya-1-gather`. |
| 2 | blocking | `skill/vicaya/shared/sources.md:48` vs `skill/vicaya/SKILL.md:859` | Phase 2 canon guidance is a summary. It omits exact book-code tables, CST table schema, direct-SQL access rules, empty-`paranum` recovery, whole-range pulls for parallel argument structures, wider structural-unit scans, and "quote fully, not representatively." | A gathering agent can cite incorrectly, miss clustered evidence, and cherry-pick canon hits while still appearing to follow the staged file. | Restore the full Phase 2 operational material into the staged source reference, including tables and rescue procedures. |
| 3 | blocking | `skill/vicaya/shared/sources.md:73` vs `skill/vicaya/SKILL.md:1102` | The EBC/parallel-evidence pull is reduced to generic commands. It drops Patton-first/BDK fallback, the T1/T3/T2 tier distinctions, alternative Pali-translation rule, Vinaya bmc1/Nanatusita rule, and manual `scratch-log 2 read` requirement for cited EBC reads. | Parallel evidence is not interchangeable with a generic SuttaCentral or EBC search. The staged result will not match the monolithic evidence standard. | Copy the original EBC parallel-evidence pull rules into the Phase 2 staged reference. |
| 4 | major | `skill/vicaya/shared/sources.md:98` vs `skill/vicaya/SKILL.md:1146` | Phase 3 Calibre guidance drops most of the original library-shape instructions: live library counts, Calibre search grammar, exact-vs-loose tag behavior, tag clusters, author naming conventions, series strategy, extraction fallback by format, and parallel-agent lock diagnosis. | Staged gathering becomes much less reliable against this specific Calibre library and will return different source sets. | Restore the full Calibre section or move it to a loaded Phase 3 reference. |
| 5 | blocking | `skill/vicaya/shared/synthesis.md:55` vs `skill/vicaya/SKILL.md:1427` | Phase 5 is weakened. It omits the instruction to read Pali/English presentation rules before drafting, the specific source-completeness loop-back to Phases 2-4, the "all relevant evidence goes in the note" rule, immediate rejection tracking, recursive citation loop-backs, and the full citation-form guidance. | The synthesis stage can produce a shorter, cleaner-looking answer that violates the monolithic workflow's evidence-first behavior. | Restore the full Phase 5 instructions in the staged synthesis path, or make the stage load the original Phase 5 and Style sections. |
| 6 | major | `skill/vicaya/shared/synthesis.md:93` vs `skill/vicaya/SKILL.md:1483` | Phase 6 is compressed and drops the exact cross-check prompt text, OpenRouter model-chain behavior notes, common fallback causes, terminal-report handling for self-review, and detailed integration rules for missed schools, factual corrections, and alternative interpretations. | Cross-check behavior can diverge even if the command runs. The prompt itself is part of the workflow and must not be paraphrased under the clarified requirement. | Carry the original Phase 6 prompt and integration rules exactly into the staged synthesis reference. |
| 7 | blocking | `skill/vicaya/shared/completion.md:19` vs `skill/vicaya/SKILL.md:1524` | Phase 7 source-coverage checks are incomplete. Missing checks include block-quoted canon coverage per position, Calibre tag-cluster exhaustion, Dhamma-talk transcript pulls, web source reading, and the 12-page/3500-word source-coverage target. | The final note can pass staged completion while materially failing the monolithic completion threshold. | Restore the full Phase 7 pre-write checklist. |
| 8 | blocking | `skill/vicaya/shared/completion.md:40` vs `skill/vicaya/SKILL.md:1541` | The final note template is simplified. It omits the evidence funnel, source type column, detailed Critical Gaps semantics, example bibliography entries, footnote examples, and several exact formatting conventions. | The staged note shape is not the same artifact as the monolithic `/vicaya` note. | Use the original Phase 7 template verbatim in the completion stage. |
| 9 | blocking | `skill/vicaya/shared/completion.md:137` vs `skill/vicaya/SKILL.md:1786` | The staged completion reference never gives the original Obsidian CLI note-creation command or the `open` requirement. It jumps from note template to validation/PDF. | A Phase 7 agent lacks the exact write path used by the canonical skill. This is operationally blocking. | Restore the Obsidian create command and disk-fallback instructions from the monolithic skill. |
| 10 | blocking | `skill/vicaya/shared/completion.md:225` vs `skill/vicaya/SKILL.md:1987` | The self-improvement loop is reduced to three bullets. It omits the exact reflection filename format, required reflection template, "nothing" bullets, run-report publishing step details, channel tuning edits, immediate small-fix rule, reflection triggers, and portability rule. | The staged mode cannot reproduce the end-of-run learning behavior of the original skill. | Copy the full Self-improvement loop into the staged completion reference. |
| 11 | major | `skill/vicaya/shared/scope.md:28` vs `skill/vicaya/SKILL.md:14` | Staged run-class semantics add a new rule: Pali terms or early Buddhist text layers make a run `sutta-anchored`. The original only says to add `--class thematic` for non-sutta-anchored questions. | This can wrongly prevent thematic auto-skips for broad Pali-term research questions. It is a semantic addition, not a split. | Define run class using the original criterion only, or document an exact monolithic-source rule before adding categories. |
| 12 | blocking | prior `review.md` test evidence | The previous review relied on `rg` keyword checks and line-presence checks. Those checks prove discoverability of words, not equivalence of workflow behavior. | A keyword hit can pass while the rule is shortened, weakened, or missing its operational conditions. That is exactly what happened here. | Replace verification with a section-by-section equivalence audit against `skill/vicaya/SKILL.md`; do not pass until every original instruction is assigned unchanged or justified as stage-local glue. |

## Fixes Applied
- Reclassified the thread review from `PASSED` to `BLOCKED`.
- No staged skill or shared reference fixes were made in this audit.

## Test Evidence
- Read `kamma/threads/20260602_vicaya-staged-skills/spec.md`, `plan.md`, and the prior `review.md`.
- Read `skill/vicaya/SKILL.md` and all staged `SKILL.md` / shared reference files.
- `wc -l skill/vicaya/SKILL.md skill/vicaya/shared/*.md skill/vicaya-*/SKILL.md` showed the monolithic skill is 2,080 lines while all staged references and stage files total about 1,161 lines. This is not proof alone, but it supports the finding that the staged path is a summary, not a partition.
- `rg -n "^## |^### |^#### |^# " skill/vicaya/SKILL.md` showed many original sections whose operational content is absent or compressed in the staged references.
- No Python code was changed; no pytest/ruff/pyright/pyrefly run was relevant for this documentation-only audit.

## Verdict
BLOCKED
- Review date: 2026-06-02
- Reviewer: Codex
- Required next step: rebuild the staged skills as a mechanical partition of `skill/vicaya/SKILL.md`, not as concise summaries. Do not finalize this thread until a section-by-section equivalence audit passes.
