# Vicaya skill improvements — work in progress

This file replaces the run-by-run reflection backlog. Processed reflections
live in `runs/processed/`.

Last triage: 2026-10-17 (second pass, 2 runs: 20261017-054516, 20261017-140000 — both committed before every fix of that day). Result: 1 REGRESSION (#155, fixed 2026-10-18: two runs on one `opencode serve` share one state file, so one run's helper calls land in the other's dossier — confirmed on disk), #129 bumped to 8 runs, 4 single sightings parked, 3 POSITIVEs merged into Working well, no channel tuning.

Prior triage: 2026-10-17, covering 98 runs from 2026-08-15 to 2026-10-16 (349 global findings, extracted by 7 parallel batch agents and clustered by hand by mechanism, not wording — the user asked for this explicitly, since separate agents describe one cause in different words). Result: 28 new issues (#124–#151), 2 REGRESSIONS (#54 placeholder detector, #90 sub-agent summary drift), 10 parked items revived on fresh evidence (#96, #97, #100, #109, #111, #112, #118, #121; #123 merged into #126), #89/#113/#116 moved up, ~60 single sightings parked as one-liners, 3 stale findings dropped (library index rebuild and pre-commit hook, both fixed 2026-09-03). The cycle is dominated by **wrong locators**: library books cited by an unstable or wrong id (#113, 24 runs), row ids cited as paragraph numbers (#124, 16), resolver mislabels in restarting books (#125, 9), CST-vs-SuttaCentral numbering (#112, 9). The second theme is **prose rules that did not hold**: the absence rule (#116, landed 09-20, six later failures), quotes from memory (#96, 11 runs), carried-over claims in enrichment runs (#127, 9). Every one of those has a structural fix proposed by the runs themselves — a helper or validator check rather than more prose. Channel tuning: five content-farm channels excluded (20261009-150500); every promotion the runs requested was already applied.

Prior triage: 2026-08-14, covering 9 runs from
2026-08-09 to 2026-08-14 — 13 new issues (#111–#123; 2 Medium, 11 Low), zero
regressions, zero drops. No run named a component the 2026-08-10 fixes
touched; the note-14 route-guard mystery resolved as a non-issue (staged
routers are gone entirely, so `tests/test_skill_routes.py` wasn't lost — its
subject was removed). This cycle's signals: citation *verification timing*
(#111: an AN6.9/6.10 off-by-one reached the Phase 5 draft because rules
verify only the top citations, not all of them), one tool defect in the
verse-book numbering layer (#112: resolve-citation answers "TH233" where
scholarship cites "Thag 10.1"), and the cross-check picture flipping on this
host (#103: the chain is now configured and works — one run got a real
5-issue review — while another got a silent sentinel after 180s; the skill's
"SELF_REVIEW is the expected outcome on pi" line is now stale and actively
suppresses cross-check use). #68 (Obsidian CLI banner) reached 4 runs and is
now fully captured. Most other new items are doc/discipline Lows (Wikipedia
extracts-API recipe, absence-claims synonym sweep, thematic T1 headings,
teacher-identity setup, id-token clarification, orchestrator pin, Phase 0
library preflight, commit-SHA recording, three small helper ideas).
Prior triage: 2026-08-09, covering 21 runs from
2026-07-20 to 2026-08-08 — 19 new issues (#92–#110; 3 High, 9 Medium, 7 Low),
zero regressions, one backlog item dropped (#86). Five tool-behavior claims
were verified against current code before merging, and one run's own diagnosis
was rejected: the `search-library-folders` hang is NOT a query bypassing #61's
FTS timeout guard (that guard is intact) but a per-hit `Path.exists()` stat in
the post-query loop blocking on an unreachable library volume (#92) — which
also explains this cycle's recurring offline-volume friction. Dominant signals:
prose/quotes drifting from the data underneath them again, now at the *quoted
text* layer rather than the locator layer (#96 fabricated and mis-assigned Pāḷi
blockquotes, #97 scholarly position attributions), tool paths that return a
confident answer instead of an error (#94 resolve-citation on a nonexistent
paranum — picked and closed 2026-08-10; plus #92, #87), and one severe
autonomy failure (#93: a gather fork ran the
whole pipeline, published, and deleted two siblings' unread work). Prior
triage: 2026-07-17 (second pass, 1 run:
20260717-140500 — two new issues #90/#91, one POSITIVE added to Working well;
the run postdates all of the same day's fixes, so nothing was stale and
nothing regressed; #90, #79's residue, and #91 were all picked and closed
the same session). Prior triage: 2026-07-17, covering 25 runs from
2026-07-10 to 2026-07-16 — 20 new issues (#69–#88; 2 High, 10 Medium, 8 Low),
zero regressions. Every tool-behavior claim was verified against the current
code before merging (per the hypothesis-testing rule): confirmed real — the
sc-parallels range-uid miss (#69, reproduced live), the get-ebc-overview
--quiet gap (#81), the phase-6 content-check exemption (#72), the coverage
matcher's per-id prefix requirement (#77); rejected — the "thematic auto-skip
did not work" claim from 20260715-060000 (auto-skip only fires when gating a
LATER phase; an explicit `scratch-gate 2.5` demanding evidence is by design),
and the PDF-subfolder complaint (already fixed by `90f7781` the same day).
Dominant signals: scratch-check-coverage noise on broad FTS sweeps (7+ runs,
#77), pi-harness adaptation friction (7+ runs, #78/#79), and sub-agent /
reviewer prose drifting from the raw data underneath it (#70/#74/#75).
Prior triage: 2026-07-06 (incremental, 1 run:
20260706-074500 — one new Low issue #67; one POSITIVE confirmation added to
Working well). Prior triage 2026-07-05, covering 21 runs from
2026-06-22 to 2026-07-05 — 13 new issues (#54-#66; 3 High, 6 Medium, 5 Low),
zero regressions. Dominant new signal: multi-agent-on-one-scratch phase
bookkeeping (#55) and a previously-claimed-fixed bug (#54) that was verified
against current code and found to never have actually landed — closed for
real same session. Context for this cycle: `64e074a` (2026-06-30) restricted
vicaya from self-editing SKILL.md/tools, so runs from 07-01 onward carry
"Improvement suggestions" instead of direct edits — none of this cycle's
findings were fixed in-run by the runs themselves; #54 was picked and fixed
as this triage's chosen issue, and #55 was picked as a follow-on and fixed
the same session. Prior triage
2026-06-22 (incremental, 1 run: 20260622-053000 — one new Low issue #53; one
POSITIVE added to Working well). Prior triage 2026-06-20 (incremental, 1 run:
20260620-133500 — no new global issues; one POSITIVE confirming #46). Prior
triage 2026-06-20, covering 26 runs from 2026-06-11 to 2026-06-19 (and
2026-06-10/11, 81 runs).

Triage 2026-06-20: the dominant new signal was **sub-agent context exhaustion**
— the single all-phases gather sub-agent overflowed ("Prompt is too long") and
its crashes left silent empty-but-gated phases that `scratch-verify` passed.
**Fixed this session:** #46 (per-phase gather sub-agents + `--quiet` helper
output, including the Option-3 quiet-helper), #47 doc half (orchestrator
spot-checks content), and #35 (lookup-book / cst_book_translator stub). Closed
2026-06-20 in follow-up sessions: #48 (`sync_notes.py` stranded-commit — rebase
onto remote before an explicitly-qualified push) and #47 residue (structural
verify-content — `scratch-verify` now flags empty/placeholder gather phases and
checks the full 0–4c set, reconciling the 4b disagreement with `scratch-gate 5`).
#49 (sub-agent claim verification) closed 2026-06-20: Hard Rule 12 (0-hit
book-code recheck before "absent") + orchestrator re-verify step for the top
cited suttas after each agent returns. All High/Medium issues from this triage
cycle now closed. Staged-router subskills were removed (`2304ecd`), retiring
the premise behind dropped #5.

## Done

| Issue | Status | Commit |
|---|---|---|
| #1 Scratch file not written before compaction | done | `feat: structural scratch-dossier system with per-phase gates + autolog` |
| #2 Calibre lock / multi-agent contention | done | `fix: serialize concurrent calibredb calls with cross-process flock` (then Calibre removed in `888be14`) |
| #4 Cross-check AI hallucinations | done | `feat: verify Pāḷi citations from cross-check output against dpd.db sutta_info` |
| Chinese column always emitted in canon hits (user request, mid-session) | done | Same commit as #1 |
| Thematic runs forced to hand-skip Phase 2.5 / 3b gates | done | `scratch-init --class thematic` auto-skips 2.5/3b in `scratch_gate` |
| `VICAYA_SCRATCH`/`VICAYA_PHASE` re-export tax every Bash call | done | per-run state keys in `fix: isolate scratch state per run to end .active pointer hijacking` |
| `calibre-check` "ok" while `search-calibre` dies on GUI lock | done | superseded — Calibre search removed in `888be14` |
| `.active` pointer hijacked by parallel runs (14 sightings, 06-01→06-07) | done | `fix: isolate scratch state per run to end .active pointer hijacking` (`ee5917a`); no shared pointer remains after `9a77539` |
| #13 Calibre query-syntax gotchas | dropped | stale — standalone Calibre search removed in `888be14` |
| #11 PDF generation failures / stale WeasyPrint | done | `feat(phase7): extract note validation and pdf generation` (`d279128`); used cleanly in all later runs |
| #21 sync_notes.py pull-rebase fails on dirty tree | done | `fix: commit Vicaya notes by pathspec without pulling first` (`ece9f98`); run-report sync hardened in `ac0dd25` |
| SKILL.md referenced removed `search-calibre`/`calibre-check` subcommands (20260609-112239) | done | fixed with `888be14` rename; verified no stale refs remain |
| search-vault traceback on "No matches found." + Obsidian launch command (20260610-071644) | done | `fix: search_vault raises on non-JSON CLI output; fix Obsidian app launch command` (`b1f71a7`) |
| DPD read-only access needs immutable URI fallback (20260606-112752) | done | documented in SKILL.md during that run |
| Canon Evidence section hard validation error for custom formats | done (residue closed with #30) | `fix: make Canon Evidence section a validation warning, not a hard error` (`4233e2b`) |
| scratch-mutating commands must run sequentially (lost append, 20260602-144756) | done | sequencing rule added to SKILL.md + vicaya-3-complete + shared/core.md during that run |
| #29 Citation verification false `[REJECTED]` cluster (12 runs) | done | `fix: verify citations by range containment and triage 81 run retrospectives into TODO.md` — range containment for range-stored books, endpoint resolution for hyphenated ranges, Thag/Thig/Kp aliases, new `unverifiable-form` verdict for global verse numbers; 7 regression tests |
| #31 scratch-init does not write the Phase 0 gate (7 runs) | done | `feat: one-shot scratch-init records Phase 0 fields and writes gate 0` — scratch-init gains `--question-original/--question-polished/--scope-assumptions/--ambiguity`; with the three evidence fields present it fills the header and writes the Phase 0 gate (run starts at Phase 1); gate refusals now say "run scratch-gate N first"; SKILL.md + vicaya-0-scope updated; 7 regression tests |
| #3 Canon / SQLite search failures (8 runs) | done | `fix: search canon on normalized text and auto-fill continuation-row paranums` — search-canon now matches on normalized text (TEI markup stripped, ṁ/ŋ→ṃ, NFC, whitespace collapsed, casefolded): "evaṃ me sutaṃ" 123→460 hits (MN book 1: 1→50), SuttaCentral-ṁ queries 0→460; empty paranum auto-filled from nearest preceding numbered row (pipes into resolve-citation); SKILL.md: fixed wrong `pali`/`english` column names in direct-SQL example, added multi-word-LIKE warning, english_translation trust caveat, pathavī/paṭhavī variant guidance, stem false-positive correction; 7 regression tests |
| #12 NFD/NFC Unicode normalization in search_canon | done | same commit as #3 — query and stored text are both NFC-normalized before matching |
| #5 Skill too long / restructure into kernel + reference | dropped (re-scoped) | The staged routers (`5b0cc50`) resolved the context problem in practice — zero context-exhaustion complaints in ~80 runs since the one failure (20260603-120425, which predates them). The kernel/reference restructure is not justified by current evidence; revisit only if context complaints recur. Residue shipped: route-list guard test (`tests/test_skill_routes.py`) so renaming a SKILL.md heading can no longer silently break a staged router — in `docs: close staged-run doc gaps and guard staged route lists` |
| #36 Phase 7 / staged-run doc-gap cluster (8 runs) | done | `docs: close staged-run doc gaps and guard staged route lists` — SKILL.md now documents: gate discipline (helper-only gates, ascending backfill, backfill-after-gate), enrichment-run mode for existing-topic notes, deferred-draft handoff for very large dossiers, Phase 7 format re-read before drafting, multi-day note-date rule, and gate-7-passed-but-note-missing recovery; plus a one-line helper-only-gates reminder in the Stage 2 router |
| #30 validate_note.py vs the "What the suttas say about X" series format (12+ runs) | done | `fix: validate series-format notes and document the hybrid in SKILL.md` — series-body H2s ("What the EBTs/suttas say") now satisfy the Canon Evidence (T1) soft section, so clean series notes validate with zero output; missing `## Findings`/`## Question` errors carry a hint stating the hybrid rule; the established hybrid (standard frontmatter + Question + Findings overview + caller's sections verbatim + standard tail) is documented in SKILL.md Phase 7 as the spec, ending per-run reverse-engineering from sibling notes; the `--series`/`note_format:` flag proposals were not adopted — the hybrid already passes the validator, so the gap was recognition + documentation, not a relaxation switch; 4 regression tests |
| #37 `.env` variables not exported into the agent shell (4 runs) | done | `fix: export VICAYA_* into the shell via env subcommand and doc prefix` — both halves confirmed live (empty vars + literal `~` from command substitution); new `env` subcommand prints `VICAYA_*` as shell-quoted export lines with `~` expanded, so `eval "$(uv run tools/research_sources.py env)"` works whatever style the user's `.env` uses; SKILL.md Setup gets a hard warning + the canonical prefix, all 8 direct-shell examples fixed (3 DPD sqlite blocks, 3 canon-db blocks lose the grep/sed dance, EBC TSV grep, GRETIL check); `.env.example` documents absolute+double-quoted values as the shell-sourceable convention; 5 regression tests incl. real-bash eval round-trip |
| #44 resolve-citation label gaps (residue of #29, 5 runs) | done | `fix: resolve citations for books outside sutta_info via canon headings` — book and section names now read from the canon table's own book/chapter/title/subhead rows (Vism → "Visuddhimaggo, 8. Anussatikammaṭṭhānaniddeso, Maraṇassatikathā"; Kathāvatthu, Paṭisambhidāmagga, Netti, Milinda all named); headings mapped back to DPD codes via sutta_info.cst_sutta (Snp 452 → SNP29 Subhāsitasuttaṃ, was SNP28); Khp/Snp dropped from paranum-based sutta_info lookup (Khp's cst_paranum is a sutta index, Snp's has gaps); books with per-section paranum restarts flagged "paranum repeats per section" with candidate sections instead of a confidently wrong name; SKILL.md Hard Rule 9 exception documented; 7 regression tests |
| #34 search-vault empty results (4 runs) | done | verified 2026-06-11: with Obsidian running every reported-failing query returns hits (parents 5+, samvega 17, urgency 20, abhibhāyatana 20, kasiṇa 20); with Obsidian closed the helper raises a clear RuntimeError, not silent `[]` — resolved by `b1f71a7` |
| #9 YouTube transcript fetch failures | closed | verified 2026-06-11: fetch-transcript returned full auto-captions for a live video; zero sightings in 81 runs |
| #23 Milinda paranum + #24 CST Extra books | done | resolved by `13580ea` (verified 2026-06-11: `s0518m_nrf:90` → "KN 18 §90 (non-canonical) — Milindapañhapāḷi"; `e0101n_mul:166` → "Visuddhimaggo, 7. Chaanussatiniddeso, Pakiṇṇakakathā"; `e0201n_nrf:12` → "Niruttidīpanīpāṭha, 1. Sandhikaṇḍa, Lahusaññārāsi") |
| #25 wisdomlib.org failures | closed | not reproducible 2026-06-11: real term → 200, bogus term → clean 404, no redirect-to-homepage |
| #16 tool-failure operational rules | done | already consolidated in SKILL.md "## When something fails" (line 1943, landed with the #36 doc commit); the two missing fallback lines (Google 403 → WebFetch, lookup-book → resolve-citation) folded into #14 |
| #39 search-canon JSON-parsing notes | done | jq-absent caveat documented at SKILL.md:93 (minor residue: SKILL.md:124 still says "Parse the JSON with `jq`" — one-line cleanup) |
| #7 Phase gate checklists don't verify evidence | done (2026-06-20) | `fix: scratch-gate refuses to write when no tool calls are logged for the phase` — before writing any gather-phase gate (phases in `_CONTENT_PHASES`: 1, 2, 2.5, 3, 3b, 4, 4b, 4c), `scratch_gate` now calls `_phase_content_issue(_phase_body(text, phase))`; if it returns `"empty"` (no `### <ts> · tool` log block found), the gate is refused with `ok: False, reason: "no logged evidence"` and the expected evidence list — exactly like `scratch_verify` catches the same gap post-hoc; Phase 0 (header-field evidence) and Phases 5–7 (draft/synthesis content) are exempt, as are AUTO-SKIPPED thematic phases; 12 existing tests updated to log before gating content phases; `test_gate_refuses_when_no_content_logged` added as regression test; `test_verify_flags_gated_but_empty_phase` updated to inject the gate directly (simulating a bypassed/crashed write) since that scenario now requires direct file manipulation. |
| resolve-citation in shell loops | done (2026-06-20) | `docs: warn against passing book_code and paranum as a single space-joined variable` — added a "Shell-loop pitfall" paragraph immediately after the `resolve-citation <table> <paranum>` example in Phase 2: always pass two separate literal args; a loop variable like `ref="s0202m_mul 97"` passed as `$ref` sends one arg and fails; use two distinct variables instead. (20260614-111501) |
| #52 comparative-religion scripture section undocumented | done (2026-06-20) | `docs: document comparative-religion T1 evidence section for non-Buddhist traditions` — added a paragraph in Phase 7 after the series-format block: for questions centred on a tradition with no canon-DB text, replace `## Canon Evidence (T1)` with a tradition-appropriate heading (`## Biblical Evidence (T1)`, `## Quranic Evidence (T1)`, etc.); validator already accepts any `## * Evidence (T1)` heading; same blockquote + citation discipline applies; Buddhist canon evidence (if relevant) goes in a separate section alongside. (20260619-155720) |
| #51 thematic auto-skip is about gates, not work | done (2026-06-20) | `docs: clarify thematic auto-skip applies to gates only, not to the research work` — two SKILL.md additions: (1) dispatch paragraph at line 953 now explicitly separates gate-skip from work-skip, names angles 16/7 as still requiring execution when applicable, and ends with "skipping the gate is not permission to skip the research"; (2) Phase 3b header gets a matching one-paragraph callout ("on a thematic run, the gate auto-skips but the work does not"). The dispatch prose previously said "skipping … the thematic auto-skips for 2.5/3b" with no caveat, which agents read as blanket permission to omit GRETIL searches. (seen in 2 runs: 20260619-021131, 20260615-134607) |
| #38 WisdomLib mandatory-on-every-run wrong for non-Indological topics | done (2026-06-20) | `docs: skip WisdomLib phase when no Sanskrit/Pāḷi terms in the question` — changed "mandatory on every run — it cannot be skipped" to "mandatory for Indological runs — skip only when the question has no Sanskrit, Pāḷi, or Indian-tradition terms"; added three concrete skip examples (Christian mysticism, grief psychology, Western philosophy). The arXiv sub-item (#38 residue: "IDs cannot be guessed — use the search endpoint") was already present at SKILL.md failure-fallback section. |
| #41 scratch-gate missing-gate visibility (half) | done | verified 2026-06-11: refusal JSON carries `missing_phase`, `missing_title`, expected evidence, and "run scratch-gate 1 first"; the validate_note silent-pass half stays open as #41 |
| #10 Obsidian CLI bypass (doc halves) | done | "When Obsidian isn't running" section documents the disk fallback and the final-report declaration; optional `vault-write` wrapper demoted to Low residue |
| #33 Helper to set the scratch `**Vault note:**`/PDF header (4 runs) | done | `feat: add scratch-set-note to record vault note and PDF paths` — new subcommand writes the `**Vault note:**` header (and a `**PDF:**` line) under the scratch file lock, so the Phase 7 `[REJECTED]` hard-gate target is set by the helper instead of hand-edits; vault-relative paths resolve against `VICAYA_VAULT_PATH`; refuses when the note file doesn't exist (a typo'd path previously disarmed the gate silently — gate 7 skips the scan for nonexistent paths); gate-7 checklist items now name the subcommand; SKILL.md updated (quick-start step 4, Research scratchpad block, Phase 7 section + exit line); 6 regression tests |
| #32 Phase-key naming mismatch — `scratch-log 4a` raw ValueError (2 runs: 20260528-143000, 20260609-230046) | done | `fix: accept phase 4a as alias for 4 with clean scratch CLI errors` — `4a` now normalizes to `4` everywhere a phase id enters (`scratch_log`, `scratch_gate`, `scratch_verify --through`, autolog via `VICAYA_PHASE`), so SKILL.md's "Phase 4a — Web search" wording and the helper agree; unknown phases get a clean ValueError listing valid ids + the alias, and the `scratch-log`/`scratch-gate` CLI handlers catch it (plus scratch-not-initialised) into `{ok: false, error}` JSON with exit 1 instead of a raw traceback; both argparse help strings document the alias; 7 regression tests |
| #14 Web search 403 / parameter failures (absorbs #16 residue) | done | `docs: add WebSearch-403 and lookup-book fallbacks to failure section` — two bullets in SKILL.md "## When something fails": WebSearch-403 → stop retrying, WebFetch direct URLs (Phase 4a mirrors) + arXiv search endpoint (IDs cannot be guessed); `lookup-book` RuntimeError (dpd-db repo not at expected path) → resolve-citation + direct sqlite on `$VICAYA_CANON_DB`; route guard tests pass (seen in 3 runs: 20260605-025640, 20260609-112239, 20260609-230046) |
| #6 Agent failure checklist before final response (3 supporting runs) | done | `feat: add scratch-self-audit failure checklist enforced by gate 7` — new subcommand holds the six fixed failure-mode questions (easy-source bias, dropped user seeds, early stopping, artifact-vs-completion, stale instructions, unverified cross-check corrections); no-args call prints the questions, `--answer`×6 appends the timestamped Q/A block under Phase 7; `scratch-gate 7` refuses until the block exists (same hard-gate pattern as the [REJECTED] scan), so the checklist is structural, not prose; SKILL.md updated (quick-start step 4, new Phase 7 "Self-audit" subsection, Phase 7 exit line); 8 regression tests + 2 existing gate-7 tests updated. Follow-up same day (`docs: route Self-audit section in stage 3 and add sync gate to vicaya-improve`): the new ### heading was unrouted — invisible to staged Stage-3 runs while gate 7 refused without it; added the Route List entry in vicaya-3-complete, a guard test pinning it, and a "Canonical-skill sync gate" section in vicaya-improve so SKILL.md edits always end with a route audit |
| #27 uv cache needs escalated access (macOS sandbox, 4 runs) | done (re-scoped 2026-06-11) | `docs: replace UV_CACHE_DIR workaround with uv sync precondition` — premise was wrong: `uv.lock` has no git/local deps, so a synced `.venv` never touches `~/.cache/uv`; a mid-run cache error means the env was cold/stale (a setup failure upstream), and the repo-local `UV_CACHE_DIR` convention the runs converged on re-downloads every package and twice coincided with active-scratch loss (20260609-221756, 20260610-044213 — the changed invocation environment alters the process key scratch state is bound to); SKILL.md Setup now states `uv sync` as a once-per-machine precondition, and "When something fails" routes cache errors to `uv sync` / `--no-sync` and explicitly bans the `UV_CACHE_DIR` export, with the `VICAYA_SCRATCH` pin for unavoidable env changes; route guard tests pass |
| #43 REGRESSION: sequential-scratch rule lost in doc restructure | done (re-scoped 2026-06-11) | `docs: re-add scratch sequencing rule scoped to hand-edits + guard test` — premise was partially stale: helper appends have been flock-serialized inside `_append_under_phase` since `ee5917a` (06-07), which postdates the last corruption sighting (20260606-110638) and survived `9a77539`, so parallel helper calls are structurally safe and the old blanket prose rule would be wrong; the only unprotected path is direct hand-edits to the scratch file (Edit/Write racing a helper append), so the restored rule targets exactly that, placed in `## Research scratchpad` (routed by all four staged routers); new guard test in `tests/test_skill_routes.py` fails if the rule ever leaves that section again |
| #46 Sub-agent context overflow (single all-phases gather agent) | done (2026-06-20) | `feat: per-phase gather sub-agents + --quiet helper output` — SKILL.md dispatch rewritten to spawn ONE single-phase sub-agent per phase (read only the Phase 0/1 briefing, not the growing dossier; read only that phase's SKILL sections; gate each phase; orchestrator spot-checks content between agents). Phase 4b now collects video details and pulls a transcript only if clearly relevant (no bulk fetch — transcripts were the biggest context killer). `--quiet` flag added to 8 search helpers (search-canon/vault/library-folders/ebc/sanskrit, sc-parallels, sc-search, get-agama): full results still written to the scratch dossier, only stdout compacted, so the dossier + note are byte-identical. 5 regression tests (`TestCompactQuietOutput`) confirm refs preserved, long text truncated, full text still in scratch. Implements the Option-3 quiet-helper too. (seen in 3 runs: 20260619-070000, 20260615-101237, 20260619-155720) |
| #47 (doc half) orchestrator spot-checks phase content after each agent | done (2026-06-20) | same commit — dispatch documents the post-agent content spot-check (`grep '^## Phase'`, scan 4a–4c for placeholder language) + inline-fallback on spawn failure. Structural verify-content half remains open as #47 residue (High). |
| #41 validate_note.py silent on success | done (2026-06-20) | `fix: print PASS on clean validate_note run` — a passing note now prints `<path>: PASS` (exit 0 + output, vs. exit 0 + silence); updated the existing silent-output test to assert PASS instead. |
| #45 resolve-citation silently mislabels DPD-code input | done (2026-06-20) | `fix: raise ValueError with lookup-book hint for non-table input to resolve-citation` — `resolve_citation` now raises `ValueError` immediately when `book_code` has no recognized `_<text_type>` suffix (e.g. `"VISM"`, `"DN"`), with a message naming the expected form and the exact `lookup-book` command to run; 2 regression tests (VISM and DN both raise with "lookup-book" in the message). |
| #49 sub-agent claims unverified before synthesis | done (2026-06-20) | `docs: add citation re-verify rule and 0-hit book-code recheck protocol` — two rules in SKILL.md. (1) Hard Rule 12: a 0-hit in a book the question predicts should contain the term must trigger `lookup-book` to confirm the code before logging absence; AN nipāta off-by-one (s0404m3 = AN10, s0404m4 = AN11) named as the canonical example. (2) Orchestrator spot-check block: re-verify the 2–3 highest-priority cited suttas from each sub-agent's report via `verify-citation` before spawning the next agent; covers the three real failure modes (hallucinated evidence, citation without resolve-citation, wrong-book 0-hit logged as absent); log the result in working notes. (seen in 5 runs: 20260613-231817, 20260614-123500, 20260614-143529, 20260614-230548, 20260615-215012) |
| #47 (residue) scratch-verify checks gate presence, not content | done (2026-06-20) | `feat: scratch-verify checks phase content and full gather set` — both halves closed. **Content half:** `scratch-verify` now classifies each gated gather phase's body (1, 2, 2.5, 3, 3b, 4, 4b, 4c) as `empty` (only the exit-gate block, no logged hits — a crashed/limited agent) or `placeholder` ("would search …", "<fill in>") and returns them under `content_issues`, making `ok` False so the orchestrator can't draft over a silent gap; auto-skipped (thematic 2.5/3b) and hand-explained N/A phases are exempt. **4b-disagreement half:** verify-without-`through` no longer stops at the highest gate written (which let an ungated 4b in the middle report `missing: []`) — it now checks every pre-synthesis phase (0 through 4c), the exact set `scratch-gate 5` requires, applying the thematic 2.5/3b auto-skip, so verify and gate 5 can never disagree. SKILL.md updated (dispatch spot-check note, Phase 5 entry-gate, Iron-rule). 5 regression tests. (seen in 4 runs: 20260615-134607, 20260614-230548, 20260619-070000, 20260619-155720) |
| #48 sync_notes.py strands commits — no pull before push | done (2026-06-20) | `fix: rebase notes onto remote before push so commits aren't stranded` — after committing the note by pathspec, `sync_notes.py` now runs `git pull --rebase --autostash origin <branch>` (branch detected via `rev-parse`, falls back to `main`) then pushes `HEAD:refs/heads/<branch>` explicitly, fixing both the non-fast-forward stranding (inverse of Done #21) and the "must fully qualify the ref (src HEAD)" error; `--autostash` keeps other in-flight vault edits from blocking the rebase; a rebase failure aborts cleanly (`git rebase --abort`) and falls back to commit-saved-locally, preserving the best-effort push contract; `main()` now takes `argv` for testability; 2 real-git regression tests (remote-advanced, dirty-tree) |
| #35 lookup-book broken — cst_book_translator import fails | done (2026-06-20) | `fix: stub ProjectPaths with TSV path for dpd-db cst_book_translator` — dpd-db's translator was changed (06-15) to read `ProjectPaths().cst_book_translator_tsv_path` at import time; the loader's `lambda: None` stub turned that into `None.attr` and broke every lookup-book call. Stub now returns a SimpleNamespace pointing at the TSV beside the module (+ `cst_xml_dir` placeholder). 6 `TestLookupBook` tests green again. The original "add a path candidate" proposal was a misdiagnosis — the path matched; the stub was the gap. |
| #50 `.doc` extraction fallback | done (2026-06-22) | `docs: add libreoffice .doc extraction row to Phase 3 table` — added a `.doc` row to the SKILL.md Phase 3 format/command table using `libreoffice --headless --convert-to txt`; added a note that `ebook-convert` fails silently on `.doc` files. (20260615-101237) |
| #42 (part) EBC `"Sn N.N"` returns wrong sutta | done (2026-06-22) | `fix: get-ebc-overview tries SNP before SN for mixed-case "Sn" input` — `get_ebc_overview` now extracts the raw prefix before uppercasing; if it's mixed-case `sn` without trailing `p`, tries `SNP{tail}` first then `SN{tail}`, mirroring `_normalise_citation`; 4 regression tests in `TestGetEbcOverview`. dhammatalks AN URL residue later dropped as a misdiagnosis, see Done. (20260604-034355) |
| #54 Placeholder-heuristic false positive — claimed fixed, never landed | done (2026-07-05) | `fix: word-boundary match placeholder patterns in scratch phase content check` — `_phase_content_issue` in `tools/scratch.py` now requires a trailing word boundary for word-final placeholder patterns (e.g. "would search" no longer false-matches "would searching" inside quoted canon translation text), via `re.search(re.escape(pat) + r"\b", low)`; patterns ending in punctuation (`<fill in>`) keep plain substring matching since they have no word-char tail to bound. New regression test `test_verify_ignores_placeholder_word_inside_inflected_text` reproduces the exact DN15 "would searching still be found" false positive from 20260630-040739/20260705-162000. The prior run's claim to have already made this fix was checked against `git log` and the live code during triage and found to be false — the fix had never actually landed; this closes that gap for real. All 260 tests pass. |
| #55 Phase-pointer drift scrambles auto-log headings across multi-agent runs | done (2026-07-05) | `docs: mandate inline VICAYA_PHASE pin for sub-agent dispatch to fix phase drift` — root cause: the per-run active-phase pointer is a single shared, mutable state file, and `scratch-gate` advances it the instant any phase (yours or a sibling's) gates; SKILL.md previously told agents "there is nothing to pin or export," actively discouraging the one thing that makes filing immune to the race. Fix is documentation-first (the `VICAYA_PHASE` env override already existed in `tools/scratch.py`, unused by the dispatch flow): the "Three rules" list in Sub-agent dispatch is now four, rule 1 mandates `VICAYA_PHASE=<PHASE>` inline on every single helper call (not `export`, which doesn't survive between Bash calls); the dispatch prompt template shows the literal prefixed invocation; the Phase 0 exec-rule and the Auto-logging section both now distinguish "nothing to pin" (true only for the single-orchestrator Phase 0/1/5/6/7 flow) from the multi-sub-agent gather phases, where it's false. Defense-in-depth in `tools/scratch.py`: `_maybe_autolog` now appends a `phase-source: run-pointer` line whenever a call was NOT explicitly pinned, so a pointer-inferred (and therefore possibly-stale) entry is visible on inspection instead of silent; the orchestrator's post-agent spot-check step now includes `grep 'phase-source: run-pointer' <scratch>` — any hit means that sub-agent skipped the mandatory pin. 3 new regression tests for the marker (pinned vs. unpinned auto-log). Also fixed while touching the test file (project static-analysis rule): unused-parameter lint noise in `tests/test_research_sources.py` — replaced 7 throwaway `lambda *a, **kw: …` mocks with `MagicMock(return_value=…)`/`MagicMock(side_effect=…)` (no named params to flag) and one unused tuple-unpack (`_translator` → `_`). All 262 tests pass. |
| #61 search-library-folders hangs indefinitely on stopword/long-phrase queries | done (2026-07-05) | `fix: abort FTS5 library-folders search on a wall-clock timeout` — root cause: `_search_rows` in `tools/library_folders.py` runs `ORDER BY bm25(document_fts) LIMIT ?` against a 12.8GB index; a stopword or one word of an unquoted multi-word phrase matches a huge fraction of the corpus, forcing SQLite to score and sort nearly the whole match set before LIMIT can trim it — minutes of CPU, not a query-syntax bug (the existing `_safe_fts_query` fallback only handles syntax errors, not this). Fix: `_search_rows` installs a `sqlite3.Connection.set_progress_handler` wall-clock deadline (default 20s, new `--timeout` flag on `search-library-folders`); on trip, the query is aborted and a new `LibraryFoldersSearchTimeout` is raised with a message naming the query and telling the caller to narrow it. The CLI handler (`_handle_search_library_folders`) catches it and prints a clean `error: … too broad` to stderr with exit 1 (no autolog), instead of the Bash tool call hanging past its own foreground timeout with zero diagnostic. SKILL.md documents the new flag and failure mode (helper table + "When something fails"). 3 regression tests: timeout raises with a tiny index + `_SEARCH_PROGRESS_STEPS` forced to 1 for determinism, a generous timeout still returns hits normally, and the CLI wiring prints the clean stderr message and exits 1. All 264 tests pass. |
| #64 Phase 5 drafts thin relative to dossier size | re-scoped, done (2026-07-05) | `feat: add scratch-check-coverage to catch dropped library sources` — before implementing the original hypothesis (a full gathered-vs-cited coverage-diff tool), ran an empirical audit: hand-checked sri-lanka-forest-monks-galduwa (dossier vs. note) and forked a 6-note survey across late-June/July runs. Verdict: the broad "agent ignores most of the dossier" claim doesn't hold — raw `hits: N` counts are dominated by stem-search noise and near-duplicate stock passages (e.g. the same "brothers went forth" narrative repeated 5x in one commentary); once deduped, T1 canon citation rates against each note's own self-reported evidence funnel ran 62-87%, with explicit reasons logged in `## Sources Investigated, Not Used` for the rest. The one confirmed gap, in both the hand-check and the fork's sample: a library document with an on-topic snippet that appeared in neither the note's citations nor its rejection table — a bookkeeping miss, not wholesale under-use. The original flagship case (karuna-vs-christian-compassion) traces to a weak sub-agent model (north-mini-code) that the same retrospective flagged as doing "searches and gating but no analytical work" — a model-capability issue, not a general Phase 5 defect. Shipped instead: `scratch_check_coverage()` in `tools/scratch.py` + `scratch-check-coverage` CLI subcommand — greps every `document_id`-bearing JSON block logged across all phases, and flags any whose id doesn't appear as `calibre-<id>` / `Calibre #<id>` anywhere in the vault note. Advisory only (not wired into `scratch_gate`/`scratch_verify`), run after `scratch-set-note` and before the self-audit. SKILL.md Phase 7 documents the new step and the id-tagging convention for `## Sources Investigated, Not Used` entries. 4 regression tests (`TestScratchCheckCoverage`). All 269 tests pass. |
| #57 External subprocess dispatches killed by Bash's ~120s foreground timeout | done (2026-07-05) | `docs: launch cross-check and external-CLI gather dispatch in the background from the first attempt` — the cross-check helper's own `--timeout` defaults to 180s, longer than the Bash tool's ~120s foreground cap, so a long synthesis silently truncated the call before the review file was written even though the model request would have succeeded; Phase 6 now says to launch it with `run_in_background: true` from the first attempt, not only after a foreground failure. Same fix documented in the sub-agent dispatch section's "Any other environment" line for external-CLI gather dispatch (e.g. `opencode run -m <model>`), where search calls and auto-logging could complete while only the final `scratch-gate` call got truncated. Added a related "When something fails" bullet: if a backgrounded sub-agent's completion notification never arrives (e.g. after a session restart), check the task's output file directly and confirm ground truth via `scratch-resume`/gate state rather than waiting indefinitely. Docs-only change; all 269 tests still pass. (seen in 4 runs: 20260626-054300, 20260630-040739, 20260705-074650, 20260705-162000) |
| #56 search-youtube has no --quiet flag | done (2026-07-06) | `fix: add --quiet flag to search-youtube for parity with other search helpers` — `search-youtube`'s argparser was missing `--quiet` even though the sub-agent dispatch prompt instructs agents to pass it on every search helper call; calling it raised `unrecognized arguments: --quiet` (confirmed live against real yt-dlp/YouTube before and after the fix). Added the same `--quiet` argument + `_dump(result, quiet=...)` wiring already used by `search-vault`/`search-canon`/etc.; the existing `_compact()` truncation logic is unchanged and already covered by `TestCompactQuietOutput`. All 160 tests in `tests/test_research_sources.py` still pass. |
| #59 validate_note.py's under-quoted-evidence heuristic conflated T1/T2 evidence footnotes with T3/T4 locator footnotes | done (2026-07-06) | `fix: scope under-quoted-evidence check to T1/T2 evidence-section footnotes` — the ratio check previously compared *every* footnote definition in the note (including T3/T4/Bibliography locators, which never carry a blockquote by design) against the total blockquote count, tripping false positives on citation-heavy but well-sourced notes. `tools/note_checks.py` now walks body sections, counting only footnote references (`[^id]`) that appear inline inside a heading matching `## * (T1)`/`## * (T2)` (e.g. `## Canon Evidence (T1)`, `## Commentary Evidence (T2)`, and tradition-specific variants like `## Biblical Evidence (T1)`), and only the blockquote lines inside those same sections; T3/T4/Bibliography footnotes no longer count toward the threshold. Existing tests rewritten to exercise scoped section content; new regression test `test_t3_t4_footnotes_do_not_trigger_under_quoted_evidence` reproduces the exact false-positive shape (fully-quoted T1 evidence + 3 unquoted T3 web footnotes) that previously tripped the check. All 270 tests pass; ruff and pyright clean on both touched files. |
| #60 scratch-init silently reuses an existing slug's scratch | done (2026-07-06) | `fix: warn when scratch-init reuses an existing slug's dossier` — `_handle_scratch_init` in `tools/research_sources.py` now reads the target scratch file before calling `scratch_init`; if it already exists, the CLI's JSON response gets a `warning` field naming the slug, the highest gate already written (or "none"), and whether the vault note is already set, so re-running a question under a slug another agent already progressed (or finished) is visible immediately instead of silently attaching new Phase 1/2 content to the old dossier. `scratch_init` itself is unchanged (still idempotent, still never overwrites) — the fix is purely in what the CLI surfaces. Documented in `skill/vicaya/SKILL.md` (Phase 0 execution rule) and `skill/vicaya-quick/SKILL.md`. 2 regression tests: a slug with a gate and a set note produces the warning text; a brand-new slug has no `warning` key. All 271 tests pass; ruff and pyright clean on both touched files. |
| #58 (part) search_vault raises on the literal "No matches found." sentinel | done (2026-07-06) | `fix: treat obsidian CLI's "No matches found." as zero hits, not an error` — `search_vault` in `tools/research_sources.py` special-cases the exact string `"No matches found."` (confirmed live against the real CLI: it prints this on stdout with exit 0 even when `format=json` is requested) to return `[]` before the JSON-parse/RuntimeError path, so a genuine zero-hit no longer reads as "Obsidian may not be running." New regression test `test_no_matches_sentinel_returns_empty_list`. All 272 tests pass. Residue (a distinct non-JSON installer-update banner, still correctly raises) tracked as new #68. |
| #62 Project CLAUDE.md model override easy to miss on the first dispatch | done (2026-07-06) | `docs: re-check project model override at first sub-agent dispatch` — `skill/vicaya/SKILL.md`'s Sub-agent dispatch section (the "Spawn each phase agent" Claude Code bullet, previously a bare `model: "sonnet"` default) now explicitly says a project `CLAUDE.md`/`AGENTS.md` or earlier session instruction naming a different sub-agent model wins over the skill default, and to re-check it at the *first* dispatch, not just once at session start. Docs-only change; `skill/vicaya-quick/SKILL.md` doesn't dispatch sub-agents so is unaffected. |
| #67 vicaya-quick doesn't document which phase auto-logs land under | done (2026-07-06) | `docs: state auto-log phase default in vicaya-quick SKILL.md` — the auto-logging paragraph in `skill/vicaya-quick/SKILL.md` now explicitly states entries file under whatever phase is currently active (Phase 1 by default, since `scratch-init` starts there and the workflow never gates or advances it), regardless of the evidence's actual content type, so a canon hit and a YouTube hit landing under the same "Phase 1" heading is expected, not a bug. Also rejoined that paragraph's pre-existing hard-wrapped lines into single unwrapped lines per the project's no-hard-wrap convention for prose (was already the file's dominant style elsewhere; this one paragraph was the outlier). Docs-only change. |
| #66 Cross-check prompt describes the synthesis instead of including its text | done (2026-07-06) | `docs: instruct cross-check prompt to paste literal synthesis text` — Phase 6's heredoc template in `skill/vicaya/SKILL.md` uses `<the question>`/`<the synthesis>` placeholders; a new bolded line right after the code block now states explicitly that these must be replaced with the literal polished question and the full current draft verbatim, not a paraphrase, since the cross-check model has no other access to the note and a description produces a non-substantive review. Docs-only change. |
| #65 Injected/garbled transcript replay | done (2026-07-06) | `docs: name injected-transcript replay as a known failure mode` — added a new bullet to `skill/vicaya/SKILL.md`'s "When something fails" section naming the corrupted "[Since your last turn…]" block pattern (describing phases that never ran, an apparent harness/session-replay artifact) and the recovery already used successfully: never trust it at face value, re-verify via `scratch-which`/`scratch-resume` and the real gate state, then tell the user plainly what's real vs. corrupted. Docs-only change. |
| #63 scratch-which returns a plain path string, not JSON, unlike every other subcommand | done (2026-07-06) | `fix: make scratch-which print JSON by default, add --raw for shell use` — `_handle_scratch_which` in `tools/research_sources.py` now prints `{"path": ...}` via the same `_dump()` path every other subcommand uses, matching the uniform-JSON assumption an orchestrator script can safely make; a new `--raw` flag opts into the old bare-path-string behavior for the 4 `SCRATCH="$(...)"` shell-embedding call sites in `skill/vicaya/SKILL.md`, all updated to pass it. Chose "make it JSON for consistency" over "document the exception" after review — consistency fixes the root cause instead of asking every future caller to remember a special case. 2 new regression tests (`TestScratchWhich`): default prints valid JSON with the right path, `--raw` prints the bare path. Verified live against the real CLI. All 274 tests pass. |
| #53 Sub-agent notification cross-labelling | done (2026-07-06) | `docs: warn against trusting sub-agent notification phase claims` — added a new bullet to the "spot-check before spawning the next" list in `skill/vicaya/SKILL.md`'s Sub-agent dispatch section: a completion notification's own phase ID or status can cross-label (e.g. a Phase 2 agent's notification reporting Phase 3 status) even when the actual work is filed correctly, so ground truth must come from `grep -n '^## Phase' <scratch>` or `scratch-resume`, never the notification text alone. Placed alongside the existing misfiled-content and re-verify-citations bullets since it's the same "don't trust the surface signal" pattern. Docs-only change. |
| #40 (part) nrf-table texts (Milindapañha) had no tier-classification guidance | done (2026-07-06) | `docs: split T1 into T1a (EBT) / T1b (later mula) evidence tiers` — verified the user's proposed mechanism against the sister dpd-db project's own EBT definition (`tools/pali_text_files.py: ebts` / `scripts/build/ebt_counter.py`) before writing anything, per the new vicaya-improve hypothesis-testing rule. `skill/vicaya/SKILL.md`'s Evidence tiers table now splits the old single T1 row into **T1a — EBT** (full DN/MN/SN/AN, Vinaya Suttavibhaṅga only, and the early Khuddaka texts through Theragāthā/Therīgāthā — the exact same file set dpd-db treats as EBT) and **T1b — later mūla, non-EBT** (Vinaya Khandhakas/Parivāra, later Khuddaka texts including Milindapañha, and the full Abhidhamma piṭaka). Milindapañha is now explicitly named as T1b, closing the classification gap. The note's `## Canon Evidence (T1)` heading stays singular (no validator/template/test changes needed — confirmed `_EVIDENCE_TIER_HEADING_RE` in `tools/note_checks.py` only matches headings ending exactly `(T1)`/`(T2)`, so an inline `(T1b)` tag on a citation doesn't collide); T1b citations get an inline `(T1b)` tag instead. Devil's Advocate question 5 extended: a claim about the *earliest* teaching needs T1a specifically, not just any T1. Docs-only. |
| #81–#85 + #88 Low-severity batch (6 issues) | done (2026-07-17) | `fix: add --quiet to get-ebc-overview and batch the Low-severity doc items` — **#81** (code): `get-ebc-overview` gains the same `--quiet`/`_dump(quiet=…)` wiring as every other search helper (verified live; parser-level regression test asserts the flag no longer exits 2). **#82**: aṭṭhakathā-name lookup table (15 rows, DN→Sumaṅgalavilāsinī through Abh 3–7→Pañcappakaraṇa-aṭṭhakathā) added to the book-code map with a "never infer by analogy" warning. **#83**: Phase 3b documents that thematic auto-skips are written by a *later* phase's gate (explicit `scratch-gate 3b` on a thematic run demands evidence by design) and gives the exact `scratch-log 3b note angle-7-not-applicable` recipe for sutta-anchored N/A runs (same for 2.5). **#84**: Rule F4 warns `document_id`s are not stable across `library-folders-refresh` (real drift: id 8757), re-resolve before reuse. **#85**: Phase 7 documents the `obsidian create` numbered-duplicate trap (pass `overwrite` on every create after the first) and the unrecognized-flag "Untitled 1.md" trap. **#88**: Phase 2 gains three stem-rule refinements (compound-first for verb roots like `bhav-`; substring≠stem-folding for inflected compounds; distinctive-compound retry for vocative-broken formulas), the `avijj`→`tiracchānavijjā` collision example, the SN saṃyutta→volume caveat, the duplicate-title (two Subhas) caution; Hard Rule 9 now covers direct-SQL pulls (title row carries the previous sutta's paranum) and per-paranum resolve-citation even mid-sutta. All 284 tests pass; ruff + pyright clean. |
| #73–#76 + #80 doc-cluster batch (5 issues, 11 runs) | done (2026-07-17) | `docs: batch the five prose-drift and citation-hygiene doc clusters` — one docs commit closing the remaining Medium doc items. **#73**: "Calling the helpers" now scopes the bare form precisely (safe only before any gather sub-agent is dispatched, and only for the phase the orchestrator currently owns) and mandates the orchestrator's own inline `VICAYA_PHASE` pin for any call belonging to a delegated phase. **#74**: new spot-check bullet — verify sub-agent summary sentences against the raw logged JSON (grep the scratch for the supporting tool call; a claim with no logged entry is false until re-run), with the four real drift instances named. **#75**: Phase 6 paragraph — reviewer factual-accuracy findings are necessary-not-sufficient (no DB access → false positives AND false negatives, real instances named); verify every reviewer content claim against the mūla; post-integration `resolve-citation` pass over every approximate/unresolved book-code citation regardless of flags. **#76**: Phase 5 "Draft durability" rule — full draft body to `data/scratch/<slug>.phase5-draft.md` before Phase 6, that file (never the dossier) feeds the cross-check, and it can be pre-validated via an ABSOLUTE path to validate_note.py. **#80**: never cite a verse/page ref from training memory (verify or soften to tradition-level attribution); series Section-2 negative claims verified against the canon DB before assertion (added to both the Phase 7 series spec and skill/what-the-suttas-say/SKILL.md); citations reused from prior vault notes re-verified via resolve-citation/verify-citation (enrichment paragraph). Docs-only; all 283 tests pass. |
| #71 cross-check subprocess hangs past its own --timeout (2 runs) | done (2026-07-17) | `fix: kill the whole process group when a cross-check chain entry times out` — root cause verified before coding: `subprocess.run(capture_output=True, timeout=…)` kills only the direct child, and opencode's node grandchildren keep the inherited stdout pipe open, blocking the post-kill drain indefinitely (a run observed 5m37s past `--timeout 260` with no output and no sentinel). New `_run_chain_subprocess` launches each chain entry with `start_new_session=True` and SIGKILLs the process group on TimeoutExpired, with a 5s bounded drain; `_run_opencode`/`_run_agy` delegate to it (existing name-level monkeypatch tests unaffected). Regression test spawns a real bash child with a backgrounded 30s grandchild holding stdout — returns None in ~1s instead of blocking. Phase 6 doc adds the two related gotchas: `--timeout` bounds each chain entry (N-entry chain → N× total), and a chained `>file >/dev/null 2>&1` redirect eats the review and masquerades as SELF_REVIEW. 4 new tests; all 283 pass; ruff + pyright clean. (seen in 2 runs: 20260711-211836, 20260715-162827) |
| #72 Phase 6 structurally skippable — gate 6 had no content requirement (2 runs) | done (2026-07-17) | `fix: require a logged Phase 6 entry before gate 6 is written` — "6" added to `_CONTENT_PHASES` in `tools/scratch.py`, so `scratch-gate 6` now refuses with "no logged evidence" until the phase holds a real logged block (the cross-check helper auto-logs; the self-review fallback records via `scratch-log 6 …`), closing the near-miss where a run went straight from synthesis to the vault write (caught only at self-audit Q6 in one run, self-caught post-set-note in another). The refusal message is phase-appropriate ("run the cross-check (or record the self-review) and log it"). Side effect: `scratch-verify --through 6/7` now content-checks Phase 6 too — consistent with the gate. Phases 0, 5, 7 stay exempt. SKILL.md Phase 6 exit line documents the refusal. 4 existing loop tests updated to log before gating 6; new regression test `test_gate_6_refuses_without_logged_cross_check`. All 279 tests pass; ruff + pyright clean. (seen in 2 runs: 20260715-054137, 20260711-113434) |
| #78 pi-harness fallbacks undocumented (+#79 doc half) (7+ runs) | done (2026-07-17) | `docs: add harness-fallbacks block for pi and other non-Claude-Code hosts` — new bolded block at the end of Sub-agent dispatch consolidating what every pi run had been re-deriving: inline gather as the pi default (generic planner/reviewer/scout/worker agents can't carry the dispatch prompt; subagent tool aborts/~120s cap) with the concrete inline recipe (inline VICAYA_PHASE pin, --quiet, id-window pulls, gate per phase, context-budget caveat); small enrichment runs (≤5 gaps) inline-by-choice anywhere; curl for server-rendered pages when the harness has no WebSearch/WebFetch (SuttaCentral stays unfetchable); SELF_REVIEW as the expected cross-check outcome on hosts without opencode/agy; and the #79 doc half — `VICAYA_SCRATCH=data/scratch/<slug>.md` inline pin (or same-invocation scratch-resume) when scratch-gate/scratch-which lose the state file across fresh shells (override precedence verified against `_scratch_path`: explicit slug > env > state file). Same three failure modes added as "When something fails" bullets. #79's CLI `--slug` nicety kept as residue. Docs-only; all 278 tests pass. (seen in 7+ runs: 20260715-054137, -054645, -061945, -064135, -071232, +5 more) |
| #77 (doc half) scratch-check-coverage ergonomics on broad FTS sweeps (8 runs) | done (2026-07-17) | `docs: sanction consolidated rejection rows for library FTS-noise tails` — the coverage-check section now states the per-id match rule explicitly (a grouped `Calibre #1944/#27645` row credits only the first id — one token per individually rejected doc) and adds a "Large FTS tails don't need per-row accounting" paragraph: name the load-bearing near-misses individually, account for the remainder with one consolidated row, and treat a reviewed nonzero residual as an acceptable advisory outcome, not a gate failure. The Phase 7 template's rejection-table example now shows both forms (a `Calibre #6294`-tagged T3 row and a consolidated "~180 further hits" row) so the format the checker needs is the one the template demonstrates — closing the exact template/checker mismatch the taṇhā run hit. Tool-side residue (investigated-vs-raw distinction) split off as #89. Docs-only; all 278 tests pass. (seen in 8 runs: 20260715-074500, -061945, -063715, -064135, -140000, -162827, sokaparideva, visuddhimagga, 20260716-224915) |
| #70 Āgama parallel codes cited from metadata without a content check | done (2026-07-17) | `docs: require content-check of every Āgama parallel before citing it` — new IRON RULE in Phase 2's EBC parallel-evidence pull: parallel codes are claims, not facts — read the retrieved translation text and confirm it matches the target sutta's actual content (protagonists, similes, argument — not broad theme) before citing; on mismatch, don't cite, log the discrepancy in scratch + `## Sources Investigated, Not Used`, and treat the sutta as having no confirmed parallel or substitute a verified one. Names the real failure instances (EA50.8/MA193/MA200 listed for MN21 but carrying MN22 material; MA152 listed for MN135 but matching MN99). Phase 2.5 gets a matching "content-check before citing" paragraph; the EBC vault "When to reach for EBC" item 1 gets a pointer line so the rule is seen at the first parallels touchpoint. Docs-only; all 278 tests pass. (seen in 1 run with 3 instances: 20260711-083537) |
| #69 sc-parallels returns [] for range-stored uids (2 runs) | done (2026-07-17) | `fix: resolve sc-parallels range-stored uids by member expansion` — `parallels.json` stores some suttas only under a range uid (`sn12.1-2`, `an3.183-352`, 692 range uids total, max width 169); `_sc_load_parallels_index` keyed by bare uid only, so `sc-parallels sn12.2` returned `[]` (reproduced live before the fix). New `_sc_expand_range_uid` expands numeric-tail range uids into member uids (guards: no digits-before-hyphen forms like the `ea-2.x` collection names, inverted ranges, widths > 400) and the index now registers each member; `sc_parallels` also skips the range uid that carries the query itself so `sn12.1-2` is not reported as its own parallel. Verified live after: `sn12.2` → 11 parallels incl. `sa298`/`ea49.5`, exactly the set the runs expected. SKILL.md Phase 2.5 documents the membership resolution + the `get-ebc-overview` fallback for a residual `[]`. 3 regression tests (expansion table, synthetic range-index round-trip, real-archive sn12.2). All 278 tests pass; ruff + pyright clean. |
| #79 (residue) expose a `--slug` arg on the scratch CLI | done (2026-07-17) | `feat: accept --slug on every scratch subcommand to bypass run state` — all seven state-dependent scratch subcommands (scratch-log, scratch-gate, scratch-set-note, scratch-self-audit, scratch-verify, scratch-check-coverage, scratch-which) gain `--slug <slug>`, resolved via the same `_scratch_path(slug)` lookup scratch-resume uses (bare or date-prefixed filename), bypassing `VICAYA_SCRATCH` and the per-process state file entirely — the Python functions already accepted a `scratch` path; the CLI just never passed one. Verified live (`scratch-which --slug beatitudes-buddhist-parallels` resolved the dated dossier with no state). SKILL.md updated in three places: the scratchpad quick-reference block, the precedence sentence, and both pi-fallback bullets now lead with `--slug` (the env pin and same-invocation scratch-resume stay documented as alternatives). 2 regression tests: fresh-shell simulation (no env, no state) where log/gate/which succeed by slug alone, and a companion proving the same condition without the flag still fails. All 286 tests pass; ruff + pyright clean. (seen in 2 runs: 20260715-060744, 20260715-064135) |
| #90 Sub-agents cite from memory of hit context, not from resolve output | done (2026-07-17) | `docs: mandate resolve-log-verbatim citations in gather dispatch` — a Phase 2 gather agent's consolidated mapping misattributed two citations (nivātavutti labelled DN33, actually DN31 Siṅgāla; asantuṭṭhitā labelled DN34, actually DN33) because it summarised from memory of which sutta a hit "was in"; the orchestrator-side spot-check (#74) caught both, but the errors shouldn't be produced at all. The Sub-agent dispatch "Four rules" list is now five: rule 5 requires every citation in the agent's final mapping/summary to copy the human ref verbatim from a resolve-citation call in its own log (never from memory; unresolved refs stay as raw book_code:paranum and are flagged). The dispatch prompt template gains a matching CITATIONS block in step 4 so every spawned agent sees the rule verbatim. Same commit: TestSearchVault's live-Obsidian test now skips cleanly when the app isn't running (pre-existing suite red herring), and the vicaya-improve SKILL.md Phase 6 questionnaire must be written in plain English per user request. All 284 tests pass (1 env skip); ruff + pyright clean. (seen in 1 run with 2 instances: 20260717-140500) |
| #91 resolve-citation rejects --quiet, unlike the search helpers | done (2026-07-17) | `fix: accept --quiet on the lookup helpers for call-template parity` — audited every subcommand for the gap (per the issue's own suggestion): the four gather-relevant lookup helpers lacked the flag — `resolve-citation` (the reported one), `lookup-book`, `verify-citation`, and `fetch-transcript`. Each now takes `--quiet` wired through the same `_dump(quiet=…)` compaction path as the search helpers (not a fake no-op — small outputs pass through unchanged, and fetch-transcript gains genuinely useful stdout compaction on ~4,000-line transcripts). Verified live: `resolve-citation s0103m_mul 242 --quiet` and `lookup-book dn1 --quiet` both return normal JSON instead of exit 2. SKILL.md dispatch rule 3 notes the lookup helpers accept the flag so a uniform prefixed template never errors. 4 regression tests (`TestLookupToolsQuietFlag`). All 290 tests pass; ruff + pyright clean. (seen in 1 run: 20260717-140500) |
| #40 (other part) general tier-relabelling allowance for non-doctrinal thematic runs | dropped (2026-07-06) | non-issue — verified against `tools/note_checks.py`: `## Canon Evidence (T1)` is already a soft/warning-only section when empty, and `## Commentary/Web/Talks Evidence (T2/T3/T4)` aren't in `REQUIRED_SECTIONS` at all, so a thematic run with no doctrinal canon already tolerates empty tier sections with zero validator friction — no relabelling mechanism needed. User confirmed: "keep things in these categories, just let them be empty ... its a non-issue." |
| #17 Transcript-mining helper | dropped (2026-07-06) | no demand across 81 runs of observation — never once requested; cut rather than kept as permanent dead weight |
| #18 Claim ledger output mode | dropped (2026-07-06) | traced to a single sighting (20260527-092930); never recurred across 40+ subsequent runs |
| #20 Inline Python blocked by CLAUDE.md hook | dropped (2026-07-06) | resolved by practice, not by a skill change — the temp/-script workflow became routine after the early cycles that first hit this, so the friction no longer occurs |
| #28 Movement-internal term mapping | dropped (2026-07-06) | traced to a single sighting (20260527-092930); never recurred across 40+ subsequent runs |
| #87 search-library-folders timeout diagnostic never reached the caller | done (2026-08-10) | `fix: emit the library-search timeout diagnostic on stdout as well` — not the unreproducible mystery the two runs suspected. `_handle_search_library_folders` caught `LibraryFoldersSearchTimeout`, printed to **stderr** and exited 1, leaving stdout empty while every other path emits JSON there — so a caller parsing stdout got a JSON decode error rather than the clear "too broad" message, which is exactly the confusion #61's clean-diagnostic fix existed to prevent. Both reported shapes fit: the long multi-word phrase (`Introduction to Pali Warder`) is the too-broad case outright, and the apostrophe query reaches the same timeout via the `_safe_fts_query` fallback re-running the search. The handler now also `_dump`s `{"ok": false, "error": …, "timed_out": true}`, keeping the stderr line and exit 1 for humans and shell chains. 1 regression test asserting the stdout payload parses. (seen in 2 runs: 20260716-224915, 20260801-155704) |
| #99 validator contradicted the documented evidence-heading rule | done (2026-08-10) | `fix: accept any (T1)-tagged evidence heading as the required section` — the skill says the validator "accepts any `## * Evidence (T1)` heading and does not warn", but `REQUIRED_SECTIONS` held the literal `## Canon Evidence (T1)` and the check was an exact string match, so `## Pāli Canon Evidence (T1)` warned on a correctly-formed note. Fixed the code rather than the docs, because the documented behaviour is the intended one: Done #52 tells comparative-religion runs to substitute the heading, so every such note was collecting a spurious warning. While writing it, the skill's own examples contradicted my first regex — `## Stoic Sources (T1)` carries no "Evidence" — so the marker is the `(T1)` tier tag, which is also exactly what `_EVIDENCE_TIER_HEADING_RE` already uses for the quote-ratio check; one notion of "T1 evidence section" in the file instead of two. The `canon_refs` requirement follows the heading the note actually uses, so the substitution can't be used to skip it. 5 regression tests (four documented variants incl. Stoic Sources; canon_refs still enforced; an untagged heading and a T2 heading both still missing). No doc change needed — the code now does what the docs always claimed. |
| #98 backticks in --summary/--answer silently delete logged text | done (2026-08-10) | `feat: accept logged prose from a file so the shell cannot eat it` — the corruption happens in the shell, before the process starts, so no amount of in-process validation can recover the lost word; the fix had to be a channel the shell cannot touch. `--summary-file` (scratch-log) and `--answer-file` (scratch-self-audit, repeatable, one file per answer) read the text verbatim, both accepting `-` for stdin. Detection is genuinely limited and the code says so: a *matched* backtick pair is substituted away without residue, so the only detectable signature is an **odd** backtick count — one span consumed while another survived — which now returns an advisory `warning` field rather than failing (a lone backtick can be legitimate prose). SKILL.md gets the rule in "Calling the helpers" (routed by every staged router, so gather sub-agents see it) plus a pointer at the self-audit block. 6 regression tests, two of which drive a real bash to pin the failure mode itself: `printf %s "a \`gap\` b"` → `a  b` (word gone) while the single-quoted and file forms round-trip intact. |
| #95 check-citation-shape rejects the vault-relative note path | done (2026-08-10) | `fix: resolve vault-relative note paths the same way in every command` — `_handle_check_citation_shape` did a bare `Path(args.note).expanduser()` while `scratch_set_note` retried a non-existent relative path against `VICAYA_VAULT_PATH`, so the documented `Vicaya/<file>.md` form failed in one command immediately after succeeding in the other. Rather than copy the retry a second time (which is how the two drifted apart), it is extracted into `resolve_vault_path()` in `tools/_common.py` and both call it — one definition, so a third caller can't reintroduce the split. The not-found error now also names both accepted path forms instead of just echoing the path. 5 regression tests (vault-relative resolves, absolute wins, missing path returns unchanged for the caller to report, plus both CLI paths end-to-end). |
| #104 library-folders-check rejects --quiet | done (2026-08-10) | `fix: resolve vault-relative note paths the same way in every command` — folded into the same commit: the parser took no arguments at all (the one subcommand #91's audit missed), so a uniform prefixed call template still hit an argparse error. Added the flag and wired `_dump(quiet=…)` like every sibling. 1 regression test. |
| #92 search-library-folders hangs on an unreachable library volume | done (2026-08-10) | `fix: probe each library source root once instead of statting every hit` — the run's own diagnosis (a common-word query bypassing #61's FTS guard) was checked and rejected: that guard is intact and covers the query. The real mechanism was `Path(row["source_path"]).exists()` running once per candidate row in the post-query result loop, outside any deadline — on an offline or hung mount each stat blocks for the mount's own timeout, and a broad sweep stats up to `limit * 10` rows, giving the reported 3+ minute hang with no diagnostic. New `_exists_probe()` bounds a stat with a daemon thread and a wall clock (no SQLite-level guard can bound a stat), and `_source_availability()` probes each *distinct source root* once per call rather than once per hit, so cost is O(roots) not O(hits). `source_available` becomes tri-state to match: `true` on disk, `false` genuinely missing, `null` volume unreachable — presence unknown, which is the honest answer and stops five runs' worth of "library volume offline" reports reading as "the book is gone". Same tri-state discipline as #94. 4 regression tests (probe returns None on a hanging stat and returns promptly; probe reports real answers; unreachable volume yields null; one probe for five hits in one root). SKILL.md documents the tri-state in the hit shape and adds a "When something fails" bullet. All 364 tests pass; ruff + pyright clean. |
| #94 resolve-citation names a paranum that has no row | done (2026-08-10) | `fix: refuse to name a paranum with no row in the book's canon table` — root cause confirmed before coding: every naming path resolves by *nearest preceding* heading or sutta_info row (`_lookup_sutta_info`'s `CAST(cst_paranum AS INTEGER) <= ?` … `DESC`; `_canon_heading_lookup` returning a truthy book-only dict on empty `ids`), so none could distinguish "this paranum exists" from "this paranum is somewhere after a heading I recognise". New `_canon_paranum_exists()` checks the book's own table once, up front, and `resolve_citation` returns early with `paranum_exists: False` and a `NO SUCH PARANUM … do not cite this reference` human label instead of interpolating one; the CLI exits 1 so a shell loop or `&&` chain can't carry it forward silently. Deliberately tri-state: `None` (no `VICAYA_CANON_DB`, or the book has no table there) means unverifiable, not bogus, and leaves the old label untouched — the check can never turn a working offline setup into false accusations. `paranum_exists` threaded through all six return paths and added to the `Citation` dataclass. Verified against the real canon DB, reproducing the reported case: `e0102n_mul 84` now flagged, `e0101n_mul 176` still resolves to the Visuddhimagga chapter. 7 regression tests (5 on a synthetic canon DB needing no env config, 2 live). SKILL.md documents the field in the Citation shape, the Phase 2 resolve-citation section, and Hard Rule 9. All 360 tests pass; ruff + pyright clean. |
| #86 scratch-init --force to replace a stale/crashed dossier | dropped (2026-08-09) | single sighting (20260715-140000), never recurred across the 21 runs since — verified by grepping `runs/processed/` for the term, which returns only that one file. #60's reuse warning already makes the stale dossier visible, and the remedy is one `rm`. Revive only if a run actually reports being blocked by it. |
| #42 dhammatalks.org AN URL pattern | dropped (2026-07-06) misdiagnosed premise, not a real bug — the original run was logged `Scope: local` (should never have been promoted to a global backlog item) and its own proposed fix was a documentation caveat, not a URL fix; live-tested against the real site: `AN/AN7_6.html` and `AN/AN7_80.html` (translated) both return 200, `AN/AN7_55.html` returns 404 only because Ṭhānissaro never translated that sutta. The URL pattern already matches the MN scheme exactly; there is no pattern bug to fix. |
| #93 Gather fork ran the whole pipeline unsupervised, published, deleted siblings' work | done (2026-08-14) | `docs: add hard-stop dispatch SCOPE block and fan-out cleanup rules` — mechanism verified before writing: the per-phase template already carried phase prohibitions, but the incident was a *custom batch-worker fork* (the #101 lexicographic shape) that no template covered, plus a cleanup recipe that legitimately sweeps `temp/<slug>/`. Four coordinated SKILL.md changes: (1) dispatch rules list goes five→six, new rule 6 "Your assignment ends at your own output — finishing the run is never your job" (no sibling-file reads/writes/deletes, no synthesis/5/6/7, no vault write, no publish, no git; sibling files appearing = the fan-out working); (2) the dispatch prompt template gains a literal SCOPE block after `Phase assigned:` carrying the same prohibitions; (3) new "Custom dispatches (batch workers, forks, external-CLI sub-agents) carry the same hard stop" paragraph after the template — every custom dispatch prompt must include the SCOPE block adapted to name the worker's own output file, with the incident named as the unauthorized-publish path; plus two standing fan-out rules: shared tooling and sibling outputs the coordinator still needs live under `data/scratch/<slug>-shared/` (durable, Hard Rule 11), never `temp/` (disposable, swept at Phase 7 exit), and only the orchestrator runs the Phase 7 exit sequence — once, after every worker returned and every output was read; (4) the Phase 7 cleanup block now states orchestrator-only/once-at-the-end and why nothing needed-later may live in `temp/`. Docs-only; all 382 tests pass (1 expected env skip). |
| #68 residue of #58: Obsidian installer-update banner also produces non-JSON stdout on `search_vault` | done (2026-08-15) | `fix: strip Obsidian update banners from vault search output` — mechanism verified before coding: the banner is prepended to a *successful* (exit 0) CLI run, while a genuinely absent app exits non-zero via the other branch, so the old "app may not be running" message on the non-JSON path was never the right diagnosis. `search_vault` now: (1) treats the zero-hit sentinel behind a banner as zero hits; (2) on JSON-parse failure, extracts the JSON payload between the first `{`/`[` and last `}`/`]` before giving up (banner-tolerant parse); (3) the new no-JSON error names the banner cause and the update-and-restart remedy plus the `rg` fallback, and explicitly says a missing app exits non-zero instead. SKILL.md "When Obsidian isn't running" documents the banner-tolerant behavior and the one-command remedy. 4 regression tests (banner+JSON parses; banner before sentinel → []; noise on both sides parses; pure banner raises naming "banner" and NOT "app may not be running"). All 385 tests pass; ruff + pyright clean. |
| #103 Cross-check chain fails silently; pi doc line suppressed real reviews | done (2026-08-15) | `fix: name the failing cross-check entry and preflight the chain` — both halves live on this machine (052550 got a real 5-issue review; 101028 got a silent sentinel after 180s), and the machine directive's discounting of the 7 resident sightings doesn't change the fix. **Code:** `_run_chain_subprocess` split into a status-returning engine (`_run_chain_subprocess_status → (text, reason)`) with four distinct reasons — `timed out after Ns` / `exited N: <stderr tail, ANSI-stripped>` / `could not start` / `no output` — while the old `str|None` wrapper stays for the #71 process-group regression tests; `_run_opencode`/`_run_agy` return the tuple; `cross_check()` collects per-entry failures and builds a sentinel whose header either says "VICAYA_CROSS_CHECK_CHAIN is not set" or lists "- app:model — reason" plus "fix the named cause and retry once"; unknown-app entries now named instead of skipped silently. New `cross-check --preflight --timeout 60` (no stdin needed) probes every entry with the tiny prompt "Reply with exactly: OK" and prints per-entry status JSON, exit 0/1. **Verified live on this machine:** real preflight against the configured deepseek-v4-pro chain → `ok: true` in seconds; bogus model → sentinel naming `opencode:no-such-model — exited 1: Error: …`. **Docs:** harness-fallbacks line rewritten from "SELF_REVIEW is the expected outcome" to "run the cross-check; never pre-assume the fallback — preflight first; on sentinel read the named cause, fix, retry once; never re-invoke after a substantive review (a re-run clobbered a real review once)"; Phase 6 recipe gains the preflight line + the retry-once/no-reinvoke rules; helper table and env-var bullet updated. 7 new tests (sentinel names entries+reasons; unconfigured-chain distinction; unknown-app naming; four live engine probes; preflight ok/failure/tiny-prompt/unconfigured). All 392 tests pass; ruff + pyright clean. |
| #102 Parallel gather dispatch works but is undocumented | done (2026-08-15) | `docs: sanction parallel gather dispatch with three safety rules` — all three sighting runs confirmed bdhrs by git before writing (machine directive). The Sub-agent dispatch mandate now reads: sequential (spawn, spot-check, spawn next) is the default shape; parallel dispatch of the applicable gather agents as one concurrent wave is sanctioned — three real runs, zero misfiling, zero `phase-source: run-pointer` leaks, substantial wall-clock savings — subject to three rules: gates are still written ascending (a finished agent waits; one cheap backfill pass at the end), spot-checks still run per agent (batched after the wave returns: content, run-pointer markers, top-citation re-verify, before synthesis builds on anything), and one-agent-per-phase still holds (a wave is not permission for one agent to run several phases). The spot-check heading now names the wave variant. Docs-only; all 392 tests pass. |
| #105 Thematic-run gate documentation cluster | done (2026-08-15) | `docs: add a thematic gate map naming exactly which gates auto-skip` — three confusions, one root: the rules lived in prose far from the call sites. The Sub-agent dispatch thematic paragraph is now a compact gate map stating exactly two gates auto-skip on `--class thematic` (2.5, 3b), every other gather gate (1, 2, 3, 4, 4b, 4c) is gated normally, an explicit call on an auto-skipped gate demands logged evidence, and gating Phase 4 does not gate 4a/4b/4c. Callouts at the three places agents act: Critical-execution-rules item 2 names the two auto-skipped gates explicitly; the Phase 2.5 exit line warns thematic runs not to call it explicitly (work still runs when angle 16 is applicable); the Phase 4 exit line states 4b/4c still need their own explicit gates on every run. Docs-only; all 392 tests pass. |
| #107 Comparative Indo-Aryan dictionary access notes | done (2026-08-15) | `docs: record comparative Indo-Aryan dictionary access in Phase 4a` — all three sighting runs confirmed bdhrs by git. New Phase 4a paragraph: DSAL CDIAL search CGI 404s (platform migrated) and the Internet Archive Turner copy is lending-only, so Wiktionary root entries are the working proxy for the Mayrhofer/Turner consensus; the Cologne `csl-orig` plain-text dictionaries (`mw.txt`, `ap90.txt`) fetch verbatim MW/Apte entries from raw.githubusercontent.com but use SLP1-style transliteration (ā=A, ś=S, ṛ=f, ṇ=R) — search `darSiv` not `darśivas`; and Mayrhofer EWA / Turner CDIAL / Whitney Roots are typically scanned/OCR-less, so budget a curl of Cologne CDSD or an archive.org full-text copy up front. Docs-only; all 392 tests pass. |
| #101 No documented run shape for lexicographic/glossary tasks | done (2026-08-15) | `docs: document the lexicographic/glossary run shape in Phase 7` — both sighting runs are bdhrs and are the same 65-word task run two ways (one serial, one parallel), so the shape is a verified consensus. The "Caller-supplied fixed formats" paragraph is now "…and non-essay deliverables (series; glossaries, catalogues, comparative tables)" and a new "Lexicographic / glossary tasks" block documents the adapted shape: build the shared lookup tool once from raw dictionary source files before fan-out; find the primary text first via `search-library-folders` (nīti literature lives there, not the canon DB) and never trust a gloss over the attested verse (the DPD *vibudha* backwards-gloss case named); batch-parallel gather in ~13-word batches as one concurrent wave; single synthesis; and the note shape (frontmatter/Question/Findings/tail + a Summary Table and Word-by-Word Findings replacing the evidence sections). The two other global findings from these runs (rogue-fork hard-stop, check-citation-shape path) were already closed as #93 and #95 — not re-raised. Docs-only; all 392 tests pass. |
| #116 (doc half) absence claims need a concept-family sweep | done (2026-09-20), residue closed 2026-10-18 | `feat: add research budget, absence rule, and OpenAlex scholarly search` (`1e76682`) — Hard Rule 13 "absence is a claim"; the structural half is the `sweep-canon` row below. |
| Library index empty or ~15% built mid-run; library-folders-check said ok (20260902-174106, 20260903-120116) | dropped (stale, 2026-10-17) | both runs predate the durable-refresh work of 2026-09-03 (`8b56f5e` reinstate OCR with per-chunk timeouts and durable refresh, `2b1a99a` scope index deletion to walked roots); no later run reports an empty index. |
| sync_run_report.py pre-commit hook fails: No module named pre_commit (20260902-174106) | dropped (stale, 2026-10-17) | fixed by `ff82b5b` (2026-09-03) — pre-commit kept in the dev group so the hook works. |
| #123 second-reviewer prompt is Claude-Code-specific | merged (2026-10-17) | folded into #126 (the Phase 6 second reviewer cannot do its job outside Claude Code). |
| #113 Library books cited by the wrong number; coverage check knew one spelling (24 runs) | done (2026-10-17) | `fix: credit every spelling of a library citation and flag folder numbers` — mechanism traced before coding, and the runs' own fix was rejected: they proposed citing the Calibre folder number because it "survives rebuilds", but only 20,762 of 46,427 indexed files (45%) have one, and the numbers repeat across libraries (915 is one book in the Bodhirasa library and another in Susima). Root cause of the folder-number mistakes: the index writes each Calibre book's own number into its searchable text as "Calibre #<N>", the same label the skill uses for the `document_id`, so agents copied the wrong number in good faith. Drift is real but one-time: `_upsert_document` keeps each id by path across ordinary refreshes, and every id changed only in the 2026-09-03 full rebuild (all rows indexed from that date, ids 1..46427), as the user confirmed. User chose to keep the index number. `scratch_check_coverage` now credits `calibre-<id>`, `Calibre #<id>` and bare `#<id>` (so `(#11854)`, `#765, #860`, and both ids of `#a/#b` count; HTML entities do not); reports a hit cited by its folder number under `folder_number_cited` with a `cite_as` token (makes `ok` false); lists Calibre-tagged numbers matching no gathered hit under `cited_not_gathered` (advisory). SKILL.md: hit shape, Rule F4 (folder-number trap with the real 2097/8904 example, refresh-vs-rebuild), the rejection-row note, and the coverage section (accepted forms + response shape, which also closes #89's "undocumented keys" sub-point). 5 regression tests from real run data; reverting the checker fails 3 of the first 4 (the 4th guards against false matches by design). CodeRabbit found one real gap — a correct citation elsewhere in the note hid a folder-number citation of the same book — fixed by checking the folder number first, with a 5th test that fails on the old order; its second point (a folder number equal to another gathered document's id) left as is, since only a title match could tell which book is meant. Live over 73 post-rebuild dossiers: false "unaccounted" 5107 → 4876, and 45 real folder-number citations surfaced in finished notes — split off as #152. 500 tests pass (1 skipped: live Obsidian); ruff + pyright clean. |
| #153 Note prose is dense academic English (user-ranked; 1 run + vault measurement) | done (2026-10-17) | `feat: warn on long sentences and require plain-English note prose` — parked at triage as a single sighting (20261010-171500, user: "five separate ideas in one sentence"); the user ranked it second regardless of run count, and a vault measurement confirmed it is a pattern, not one note: across 300 notes, mean sentence length 20–23 words but the slowest decile runs past 49 words, and Sep–Oct Findings sections alone held 538 sentences over 45 words (real worst cases 78 and 89 words, four ideas chained with colons and dashes). Because prose rules alone did not hold this cycle (#116), the fix has a structural half: `note_checks.py` gains a `long-sentence` warning for every explanatory sentence over 45 words — prose only (blockquotes, tables, code, footnote definitions, Bibliography / Sources Investigated / Critical Gaps / Angles Not Pursued excluded), list items checked one at a time, footnote markers and wikilinks stripped, abbreviations such as "e.g." not treated as sentence ends; Phase 7 already requires clearing every warning, so each one must be split. SKILL.md Style notes gain the plain-English rule (one idea per sentence, ~15–20 words, 45 max, split by ideas never by shaving words, long citation runs become bullet lists, normal subject-verb-object order, verbs over abstract nouns, no clause chains, example in the next sentence, quotes in blockquotes, precision kept) with a real 89-word sentence and its rewrite; Phase 5 says to draft plainly from the first sentence; the validator paragraph explains the warning. Limit chosen by the user after an independent Sonnet review and a before/after on real sentences: first shipped at 40 (10.4% of sentences, median 22 warnings per Sep–Oct note), the reviewer called that "somewhat too drastic" (forced rewrites of 20+ sentences invite word-shaving and choppy prose; suggested 55–60), and the user picked 45 (7.3% of sentences, median 16 per note; 50 → 5.0%/11, 60 → 2.5%/5). Review fixes: `no`/`p`/`c`/`ed` count as abbreviations only before a number ("he said no. The…" was one sentence); lines labelled `English:`/`Pāḷi:`/`Translation:` (also as bullet items) and mostly-quoted paragraphs are skipped, since quoted canon text must stay verbatim; a sentence-final `…` ends a sentence. Not adopted: exempting citation-list sentences in code (the rule says to make them bullet lists instead). 8 regression tests, real vault fixtures where the behaviour depends on real text; disabling the check fails the 2 positive tests, and each review fix's test fails when that fix is removed. Over the existing vault the check reports 2,863 warnings, so an enrichment run that re-validates an old note will have to split its long sentences. 507 tests pass (1 skipped: live Obsidian); ruff + pyright clean. |
| #155 REGRESSION: two runs on one `opencode serve` share one state file (1 run, mechanism confirmed on disk) | done (2026-10-18) | `fix: key the per-run state file to the opencode session id` — the report was right: `_run_key()` took the parent of the shell's session leader, which under a long-lived `opencode serve` is the server for every session. The per-session id the run asked us to look for exists: the binary's shell tool sets `OPENCODE_SESSION_ID` on every command (read from the opencode v2.0.32 binary, not probed in a live session). `_run_key()` now returns it when set, else the old process key, so no prose pin rule is needed. A sub-agent has its own session id, but its first step, `scratch-resume <slug>`, writes its own state file, so the gather dispatch still works. SKILL.md wording updated. Old process-keyed state files stay on disk, inert. 1 regression test; with the env check disabled it fails, with it restored it passes. 577 tests pass (1 skipped); ruff clean. Not verified: a live two-session opencode run. (20261017-054516) |
| #129 Library search times out on multi-word queries (8 runs) | done (2026-10-18) | `fix: drop function words from library search phrases` — reproduced live: "Buddhist Analysis of Matter", "suffering of change", "Manual of Insight", "Heart of Buddhist Meditation Nyanaponika" and "Vimuttimagga path of freedom" all hit the 20 s abort (21–25 s each), while "Nyanaponika" alone took 1.9 s. Cause: FTS5 joins the words with AND, and a word like "of" sits in almost every book, so the engine must score a huge share of the index. The empty-result shape the newest run saw was this same timeout, read by an agent as "no hits". Fix: `_search_rows` drops a small stopword list (`a an and as at by for from in is of on or the to with`) from a plain phrase; a query using quotes, AND/OR/NOT/NEAR, `*` or `:`, or made only of stopwords, runs as written. After the fix the same five queries return the right book in 2.4–4.3 s. Not reproduced: the "non-JSON line" — stdout is JSON on timeout (Done #87); the plain error line goes to stderr, so it only mixes in when a caller merges 2>&1. Not fixed: a distinctive-word-plus-common-word query can still time out; the SKILL.md retry advice stays. 1 integration test plus 6 table cases; with the fix disabled the integration test fails. 100 library tests pass; ruff clean. (20261017-054516, 20261011-062929, 20261008-133440, 20260928-020423, 20260904-161608, +3 more) |
| #128 The cross-check times out on long notes (8 runs) | done (2026-10-18) | `fix: scale the cross-check wait to the draft size` — half of the report was already fine. Falling through to the next chain entry on any failure (rate limit, 402, timeout, non-zero exit) is how `cross_check` already worked, with tests; the runs that saw a stall were waiting on the user or on a single entry. The real defect was the flat 180 s default: a ~20 KB draft needs 420–480 s (two successful retries in the runs; n is small). Now `--timeout` defaults to unset and the wait per entry is 120 s + 18 s per KB of prompt, minimum 180 s, maximum 600 s (20 KB → 480 s; short prompts unchanged); an explicit `--timeout` wins and preflight keeps 60 s. SKILL.md table and the preflight advice updated. The opencode syntax break in one run is not reproduced: `opencode run -m <model> <prompt>` matches v2.0.32 `run --help`. Not fixed: a hung first entry now costs up to 480 s before the next entry runs, so preflight stays the guard. 2 new tests; with the scaling removed the pass-through test fails. 586 tests pass (1 skipped); ruff clean. Not verified: a live full-draft cross-check (it spends model credit). (20260817-034516, 20260903-bhikkhu-upahana-vinaya, 20260908-saccanurakkhana-speech-ethics, 2026-09-22-rebirth-cosmology-modern-research-ebt, 20261005-180920, +3 more) |
| #130 Scripted and batched edits fail silently, so fixes do not land (8 runs) | done (2026-10-18) | `feat: add apply-edits for all-or-nothing note patches` — a tool, not another rule (the prose rule for #116 failed six times). The new `apply-edits FILE` reads a JSON list of `{old, new}` on stdin. Every `old` must be found, exactly once unless `"all": true`; otherwise nothing is written, the exit code is 1 and each edit gets `applied` / `not-found` / `ambiguous`. That removes the three reported shapes: the one-character no-op, the crash after "patched", and the unescaped apostrophe (JSON in a quoted heredoc). Writes are atomic (temp file, then replace) and keep line endings and file mode. Each applied edit reports `old_remaining`, the copies of the old text still in the file. SKILL.md gains a helper-table row and a Phase 6 paragraph that makes it the way to apply corrections. Not solved by the tool: a claim stated in two different wordings (the "correction lands in one of two places" shape) — the paragraph tells the agent to grep for the other statements; no tool can know the other wording. Live run on a copy with Pāḷi text and apostrophes: a batch with one missing target changed nothing and exited 1; the corrected batch applied. 7 tests; with the all-or-nothing guard removed, 1 fails. 593 tests pass (1 skipped); ruff clean. (20260904-233205, 20260905-032829, 20260911-163831, 20260927-111500, 20260928-020423, +3 more) |
| #125 resolve-citation names the wrong sutta in books whose numbering restarts (9 runs) | done (2026-10-18) | `fix: flag restarting paranums instead of naming one sutta` — audited every canon table (n=23 mūla tables with sutta_info rows; counts read from the db, not from the runs). Two real causes. (1) **Restart:** when a paranum sits in more than one row of the book's own table, the nearest-earlier lookup in sutta_info picks one sutta at random. s0513m_mul has 99% of its paranum rows repeated (§88 occurs 16 times — the report's "Sarambha instead of Dasaratha"), s0514m_mul 47%, and the aṭṭhakathā/ṭīkā path inherited the same flaw (`s0506a_att 5` said "VVa1 para 5"; 10 commentary tables restart). `resolve_citation` now counts the rows first and, above one, skips both sutta_info paths so the existing candidate list answers ("paranum repeats per section, near: …"). (2) **Incomplete list:** sutta_info lists 27 of ~110 jātakas for s0514m_mul, so §57 (in JA521) read JA527 and everything past the last row read JA545; that table and s0513m joined the unreliable-stems list that already held Khp and Snp. Not wrong, so not changed: Dhammapada labelled "DHP1-20 Yamakavaggo" is the true vagga for verse 20 (the unique-paranum DHP table is fine, so F2 does not manufacture a false vagga), and AN3 §80 returns only the book label, with no wrong sutta name, so the "Cūḷanikā" claim did not reproduce. Not fixed: unique Jātaka-2 paragraphs get chapter and subhead only (§2113 → "22. Mahānipāto, Dārakapabbaṃ"), because the table has no jātaka-title row there; the label is true but incomplete. Cūḷaniddesa and the Visuddhimagga placement difference were not checked. 3 new tests on real db rows; with the restart check removed the commentary test fails, with the unreliable-stems entries removed the Jātaka-2 test fails (1 each, run separately). 596 tests pass (1 skipped); ruff clean. (20260818-190500, 20260902-165800, 20260903-120116, 20260905-045500, 20260908-084542, +4 more) |
| #132 scratch-* helpers reject `--quiet` (6 runs) | done (2026-10-18) | `fix: accept --quiet on every helper subcommand` — read from `--help` of all 37 subcommands: 13 lacked `--quiet` (`scratch-init/log/gate/set-note/self-audit/verify/check-coverage/resume/which`, `apply-edits`, `env`, `library-folders-refresh`, `library-folders-duplicates`) and `check-citation-shape` / `check-quotes` lacked `--slug`. A loop after the last subcommand is defined now adds a no-op `--quiet` to any command without its own, so a new command cannot drift; the two note checks also accept an ignored `--slug` (they read the note file, not a scratch). SKILL.md line on the uniform template updated. The `while read` report did not reproduce: `resolve-citation --quiet` printed its JSON in a piped loop, with and without `</dev/null`. 41 tests: one per subcommand checks `--help` lists `--quiet`, plus parse checks; with the loop removed 16 fail. 637 tests pass (1 skipped); ruff clean. (20260908-084542, 20260911-110444, 20261004-190500, 20260905-010740, 20260905-004416, +1 more) |
| #112 resolve-citation answers in CST numbering, not the one readers use (9 runs) | done (2026-10-18) | `feat: show the SuttaCentral number and add sutta-numbers` — the user pointed at the DPD `sutta_info` table, which holds both numberings per sutta (`dpd_code` and `sc_code`); 1,106 of its 5,116 rows differ (22%). Two changes. (1) `resolve-citation` now returns a `suttacentral` field next to `human` whenever the sutta's SuttaCentral code differs from the DPD code in `human` (`AN3.66 Kesamuttisuttaṃ` → `AN3.65`; `TH174` → `THAG3.5`; `SNP11` → `SNP1.11`); `human` itself is unchanged, so Rule F2 (copy `human` verbatim into `canon_refs`) and every existing label still hold. A code that is only a coarser form of the other (`SN45` vs `SN45.1`) is not reported as a difference. (2) New `sutta-numbers CODE` looks a number up in both schemes and lists every match with both codes, name, canon table and paranum: `AN3.65` returns Sarabha (DPD) and Kesamutti (SuttaCentral), which is exactly the collision that made reviewer "corrections" go the wrong way. SKILL.md states the house convention once, taken from the existing vault notes (`canon_refs` and `db:` citations use `human` verbatim; prose gives the name with the SuttaCentral number, "Kālāma Sutta (AN 3.65)"), and tells agents to run `sutta-numbers` before accepting or correcting any number that did not come from `resolve-citation`. Not covered: aṭṭhakathā/ṭīkā labels (`MNa60`) and book-level labels (`AN 03 §66`) carry no `suttacentral` value, and Kathāvatthu paragraphs with no debate number are unchanged. 4 new tests on real db rows; with the field disabled the "shown" test fails, with the equality guard removed the "absent" test fails. 642 tests pass (1 skipped); ruff clean. (20260902-133109, 20260904-233205, 20260928-004814, 20261007-025707, 20260913-104226, +4 more) |
| #127 Enrichment runs carry wrong claims forward from the old note (9 runs) | done (2026-10-18; claim-level residue open) | `feat: add audit-note to test an old note before enriching it` — the proposed fix was a Phase 1 step running verify/resolve over `canon_refs`; measured first, that part is useless: over all 300 vault notes the `canon_refs` existence check reported 79 "not found" and every one was a commentary or book-level code the lookup cannot read (`MNa43`, `UDa73`, `Abhidhamma02 §26`), none a real error, because the reference exists — the issue's own point. So `audit-note NOTE` tests the claims instead: it runs the quote check, then resolves every footnote's `db:` paragraph and compares the sutta code in the footnote with the sutta the paragraph falls in (`label-mismatch`), flags a paragraph the book lacks (`no-such-paragraph`), and lists the Critical Gaps as `gaps_to_retest`. Real corpus run (300 notes, 76 s): 134 quotes not found in 65 notes, 45 quotes under another paragraph in 29, 39 label mismatches in 22 notes, 29 row-id citations in 4. Spot-checked two mismatches against the db: a footnote labelled "DN1 Brahmajālasuttaṃ para 190" cites the Tathāgata-arises passage, which is DN2 §190; "SN55.1" for SN55.5 §1001. SKILL.md: new helper row and an "Audit the old note first" paragraph in the enrichment section. Open: claim-level errors (a sequence, an attribution such as "tividhena in AN8.63", which is SN47.3) are not read by any tool; the paragraph tells agents to re-check them with `sweep-canon` / `get-paragraph`. Not done: repairing the 22 notes with mismatches, which edits the vault and waits for the user (see #152, #154). 5 tests with real footnote and gap lines; with the label comparison disabled 2 fail. 648 tests pass (1 skipped); ruff clean. (20260912-063554, 20260912-153500, 20260912-nibbida-viraga-nirodha-enrichment, 20260905-005804, 20260818-054108, +4 more) |
| #109 Huge dossiers cost a run its time (5 runs) | done (2026-10-18) | `feat: add scratch-digest to read a dossier without cat-ing it` — measured the real cause before choosing a fix. 431 dossiers hold 196 MB; median 88 KB, p90 1.3 MB, max 7.4 MB. By volume: `sc-parallels` 33% (avg 112 KB per call), `search-canon` 28%, `search-library-folders` 14%, `fetch-transcript` 6%. But size on disk costs little: an append rewrites the file, 66 ms on the 7.3 MB dossier (median of 5), about 4 of the 160 minutes in the worst report. The real cost is reading: Phase 5 told the agent to `cat "$SCRATCH"`, which puts up to 7 MB (over a million tokens) into context, forcing compaction, compression scripts and "evidence pack" agents — the exact reports. So the fix is a reader, not smaller logs. `scratch-digest` prints your own notes and gates in full and each auto-logged call as one line with its hit count and first two hits, each with an `L<line>` number for `sed`; `--phase`, `--top`, `--width` adjust it. Over all 431 dossiers (no errors): 196 MB → 7 MB; for the 53 dossiers over 1 MB the median digest is 45 KB and the largest 169 KB (the 7.3 MB one: 169 KB; 97 KB of that is the agent's own summaries, the floor). SKILL.md: Phase 5 `cat` step replaced, helper row added, compaction line points at it. Not done, on purpose: an excerpt mode for auto-log (the dossier stays whole so the digest can point back into it, and disk size is not the cost) and a new ceiling on id-window pulls (the Phase 0 research target and Hard Rule 13 already cap them; the runs that blew up predate or ignored them, and 20261007-025707 is one run). Not fixed: append cost grows with file size (66 ms at 7.3 MB). 5 tests with real dossier entries; with the JSON reading broken 2 fail. 654 tests pass (1 skipped); ruff clean. Not verified: a real run that reads the digest instead of the dossier. (20260912-150000, 20260928-004814, 20261007-025707, 20260905-032829, +1 more) |
| #54 REGRESSION: placeholder detector trips on a sutta quote (4 runs) | done (2026-10-18) | `fix: ignore logged results and quotes when checking for placeholders` — reproduced on the real dossiers: 4 of 431 flagged a phase as placeholder, all Phase 2, all from the poisoned-arrow simile ("he would search for the arrow with a probe") inside auto-logged JSON. The scan now skips fenced blocks and `>` quote lines and reads only what the agent wrote. After the fix 3 of the 4 still match, but only because the agent's own summary line explains the false alarm in the same words; new runs will not write those. 1 test through the real logger; with the filter removed it fails. Not fixed: a placeholder phrase quoted inside the agent's own summary line. (20260902-133318, 20260902-165800, 20260905-005804, 20260905-033059) |
| #131 WisdomLib is behind a Cloudflare challenge (4 runs) | done (2026-10-18) | `feat: add fetch-wisdomlib with a Wayback fallback` — the user asked to find a way in or drop it. Tested today: a plain browser-style request to wisdomlib.org returns 200 with the real page (13 definitions for nibbāna; the only Cloudflare trace is a passive script), so the late-September 403 comes and goes by address and tool. The Wayback Machine also serves snapshots (nibbāna: Feb 2026, 12 definitions; gzip-compressed; it rate-limits bursts with 429, so one retry is built in; a page that was never archived times out). New `fetch-wisdomlib TERM` builds the ASCII URL, tries live, then the archive, parses each definition into section, text and source (blocks with no `Source:` line are site text and are dropped; text is cut at 2,500 characters unless `--full`), and when both fail returns `blocked: true` with the reasons and an instruction to log one gap and not retry. A term WisdomLib has no page for is `found: false`, not a block. SKILL.md Phase 4c now uses it and says not to use WebFetch/curl for this site. 10 tests (excerpt cut from the real page; fake network for 403, challenge page, gzip, 429, 404, both-blocked). Live: saddhā 17 definitions via the live page, nibbāna 12 via the archive. Not decided for the user: the phase stays mandatory; a blocked result lets it pass with a recorded gap. (20260927-033629, 20260927-111500, 20260928-004814, 20260928-020423) |
| #133 + #134 + #135 + #118 parallel-wave gate and pin friction (4 + 4 + 3 + 3 runs) | done (2026-10-18) | `fix: let parallel gather gates land in any order` — one cause for #133: `scratch-gate` required every earlier gate, so a 4b or 4c agent that finished first was refused (one retried 14 times in 9 minutes). Gather phases (2, 2.5, 3, 3b, 4, 4b, 4c) now need only Phases 0 and 1 gated; `scratch-gate 5` and `scratch-verify` still require all of them, and 5/6/7 keep full ordering, so nothing can be skipped. `scratch-resume` now names the first phase without a gate instead of the one after the highest gate (it would have said "5" after a lone 4c gate). #134: Phase 4a is one phase stored as 4; the gate result carries an `alias` line and refusals say so; SKILL.md states it once at the phase table. #135: `scratch-set-note --pdf` now refuses a PDF that does not exist yet (a path other than `skipped`); the "no logged evidence" refusal tells a batched caller to rerun the gate alone; SKILL.md says to run state-changing scratch calls one at a time. #118: the pin rule now covers any agent working more than one phase, not only sub-agents. The dispatch template tells an agent never to retry a gate refusal in a loop. 8 tests; with the order change removed 3 fail. Not fixed: nothing stops two scratch calls from being batched; only the message and the rule. (20260908-saccanurakkhana-speech-ethics, 20260911-khandhaka-anadara-anapatti, 20260927-033629, 20261007-025707, 20260818-170240, 20260822-133000, 20260814-101028, +more) |
| #124 Row id cited as the paragraph number (16 runs) + #96 Pāḷi quotes finished from memory (11 runs) + #147 direct SQL pulls not auto-logged (2 runs) | done (2026-10-17) | `feat: add get-paragraph and an advisory check-quotes for Pāḷi quotes` — cause traced before coding: the skill sent agents to raw `id BETWEEN` SQL for full paragraphs, which shows an `id` on every row and a `paranum` only on a paragraph's first row, and finding the owning paragraph was a separate manual step that got skipped; one published note cites "s0304m_mul id 1739" for a verse in paragraph 409. New `tools/canon_paragraphs.py`. **`get-paragraph <table> <paranum>` / `--row-id N`** returns every row of the paragraph (continuations included, headings end it, rows after a heading form an unnumbered block), joined, with markup and inline `<note>` variant readings stripped, under its real number; restart books return every occurrence with a warning; range cells parse (`583-4`, `1699-700`, `18-19-20`); auto-logged (closes #147); `--quiet` never shortens the text. **`check-quotes <note>`** (advisory, Phase 7, after the citation shape check) pairs each Pāḷi blockquote with the `db: <table>, para N` footnote on it, on its translation twin, or on the bold label directly above (commentary labels excluded), and tests it against that paragraph ignoring case, punctuation, spacing (`na tveva`/`natveva`), variant readings, speaker labels (the mūla text has 0 colons), `-aṃ''nti` sandhi, a lengthened final vowel and a differing last word; verdicts `in-other-paragraph` (with `found_in`), `not-found` (with `matched_words` and `closest_paragraph`), `no-such-paragraph`, `row-id-citation` (with `cite_as`); `unpaired` counts untestable quotes. Prototyped on the vault first; each false-positive class found in hand samples was fixed and re-measured. An independent Sonnet review found per-run (not per-quote) pairing, borrowed prose and commentary-label citations, abbreviated range footnotes losing their upper bound, unchecked `id N` footnotes, `--quiet` clipping the paragraph text, and odd paranum cells — all fixed, each with a test that fails when the fix is reverted; it also showed Hard Rule 9's "title row is stamped with the previous sutta's paranum" was wrong about the db (0 heading rows carry a paranum; `search-canon`'s fill is the real mechanism), now corrected. SKILL.md: Hard Rule 9 row-id rule, helper table, Phase 2 quoting recipe (quote from `get-paragraph`, never from a snippet; window SQL is for discovery), new "Quote check (advisory)" section, Phase 7 exit line. Vault: 1,007 quotes checked, 208 findings in 80 notes, mean 1.5 per Sep–Oct note, 7/10 real in a hand sample — residue split off as #154. 33 new tests on real canon rows; 540 tests pass (1 skipped: live Obsidian); ruff + pyright clean. |
| #89 Coverage check buried the real miss under broad-sweep noise (14 runs) | done (2026-10-17) | `fix: parse every logged library hit and rank the coverage list` — measured before designing: over 73 post-rebuild dossiers, books that 3+ distinct searches returned were accounted for in the note 50% of the time against 22% for one-off hits, and top-3-ranked hits 32% against 9% below rank 10. `scratch_check_coverage` now orders `unaccounted` by distinct queries (search terms with flags stripped, so a re-run with another `--limit` counts once), then best rank; the first ten keep path, snippet, `queries`, `best_rank`, the rest only id and title; `unaccounted_count` added; `--note <draft>` checks the Phase 5 draft so a miss is pulled in before review (2 runs asked). Output on the largest dossier 128 KB → 29 KB. **The Sonnet review found a much bigger, older bug:** hits were read with a flat-object regex that skipped any hit whose `possible_duplicate_of` holds nested objects — 22% of documents across 148 dossiers never reached the coverage check at all (karuna dossier: 15 logged hits, 7 seen) — and later hits got better ranks than they earned; now each fenced JSON block is parsed whole (regex kept only as fallback): gathered books over 73 dossiers 6,468 → 8,116. Re-measured honestly after that fix, on non-trivial lists only: a cited book, re-ranked among the unaccounted, lands in the first ten 49% of the time against 35% for random order (1,416 trials) — the ordering helps but does not decide, and the skill says so (scan the remaining titles). SKILL.md: coverage section (ordering, fields, measured figure) and a Phase 5 draft-durability line (run it on the draft, read only the first ten there). 5 new regression tests (ordering, compact tail, draft, nested duplicate record from a real dossier, flag-stripped query), each failing when its fix is reverted; 545 tests pass (1 skipped: live Obsidian); ruff + pyright clean. |
| #126 Phase 6 second reviewer could not check anything on pi (13 runs, absorbs #123) | done (2026-10-17) | `feat: add a shell-capable pi reviewer agent for Phase 6` — cause confirmed in the pi config: `~/.pi/agent/agents/reviewer.md` declares `tools: read, grep, find, ls` (no bash), so it could not run `resolve-citation`; `scout` has bash but is a code-recon persona. Pi's `subagent` extension reads `~/.pi/agent/agents/`, accepts symlinks there, and passes the agent's `tools` straight to `pi --tools` (verified in `extensions/subagent/agents.ts`/`index.ts`). New `config/pi/agents/vicaya-reviewer.md` (read, grep, find, ls, bash; reviewer-not-editor rules; append each finding to the named output file); `just sync` now links it into `~/.pi/agent/agents/`. SKILL.md Phase 6: "Which agent, by harness" (Claude Code Agent with Bash; pi `vicaya-reviewer`, never `reviewer`/`scout`, background `pi -p --tools …` fallback; an output file under `data/scratch/<slug>-shared/` appended as it goes, stop after 10 minutes without growth and check inline; no shell-capable agent → inline checks, a file-tools reviewer may only raise doubts); the prompt template gains `get-paragraph` and `check-quotes`, "say so and stop if you cannot run these", and the output-file line; the SendMessage prohibition moved out of the shared prompt into a per-harness note (Claude Code: do not use it; RLM/prime: must use `agent_message.send`), closing #123; the verification pass on pi passes the reviewer its own findings file, since each `subagent` call is a new process; one pointer in the pi harness-fallbacks block. Not run live: `just sync` (changes the user's pi setup) and a pi review (spends model calls) — the user runs both. Docs/config only; 545 tests pass (1 skipped). |
| #116 Absence claims skip the synonym family — the prose rule did not hold (12 runs) + #121 stratum-distribution scan is hand-written SQL (2 runs) | done (2026-10-18) | `feat: add sweep-canon to count a term family across every canon table by tier` — cause read from the 12 reports before coding: six separate failures sat behind one rule. A quoted phrase in one case ending found nothing while the stems occur together in DN 17 §269 and MN 83; a sweep of `s*_mul` was called "canon-wide" and missed the Paṭṭhāna (§417, bhavaṅga's first technical use); a ṭīkā search was reported as the aṭṭhakathā being silent; long-vowel *āvho* missed the short *-avho* set; a row count was written up as "every occurrence"; and an *ogha* count was mostly *mogha* and *goghaṃsikā*. The tenth failure — searching *siṅga* when the text has *visāṇa* — no tool can fix, so the skill says so. New `tools/canon_sweep.py` and `sweep-canon TERM… [--books] [--exclude PREFIX…] [--quiet]`: one pass over all 217 tables (422,698 rows, 10–15 s), complete uncapped counts per table and per tier (T1a early mūla, T1b later mūla, T2 exegetical mūla / aṭṭhakathā / ṭīkā, then post-canonical; the same T1a list as dpd-db's `ebts`, pinned by a test), rows and occurrences kept apart, the word forms matched, a stem probe, phrase word-stem co-occurrence, a vowel-length probe in the text's real spelling, variant-reading-only rows, hints, and a "not canon-wide" warning (a stratum a `--books` sweep did not read says `searched: false`, never 0). `--exclude` drops by prefix (so *kāmoghaṃ* survives *mogha*) and lists what each prefix removed. It also gives #121's first-attestation table: `by_stratum`, earliest stratum first. Auto-logged; `--quiet` clips only stdout. SKILL.md: Hard Rule 13 and its counting clause, helper table, return shape, and a Phase 2 recipe that says how to read the result. Two Sonnet reviews found real faults, all fixed with tests that fail when the fix is undone: the quiet view's "forms not shown" count dropped the full result's own count (20 shown for a true 589); an unreadable table was counted as searched and marked its stratum searched; non-text tables entered the sweep; block tags glued verse lines together (2,385 rows); `--exclude` was ignored by the vowel probe; a `--books` pattern matching nothing reported ok. Checking my own mutation runs caught a stale bytecode cache that made a restored file run its mutated code, so every mutation was rerun with the cache cleared. 576 tests pass (1 skipped: live Obsidian); ruff + pyright clean. Residue: #156. |

## Remaining — prioritized

### High severity

_(2026-08-14 single-sighting rule, per user: an issue reported by one run is
not an issue yet — it parks until a second run reports it. Parked from this
section: none; from Medium: #96, #97, #100, #101 keeps 2 runs, #111, #112;
from Low: #106, #108, #109, #110, #117, #118, #120, #121, #122, #123 —
see `### Parked`.)_

_(#61 moved to Done — FTS5 search now aborts on a wall-clock timeout instead of hanging, 2026-07-05)_

_(#69 moved to Done — range uids now expand into member uids at index
build, 2026-07-17)_

_(#70 moved to Done — parallel content-check IRON RULE documented in
Phase 2's EBC pull, Phase 2.5, and the EBC vault section, 2026-07-17)_

_(#92 moved to Done — each source root is probed once with a bounded stat and
`source_available` is tri-state, 2026-08-10)_

_(#93 moved to Done — every dispatch prompt, standard or custom, now carries a
hard-stop SCOPE block; shared fan-out tooling is durable data under
data/scratch/, and the Phase 7 cleanup sweep is orchestrator-only, 2026-08-14)_

- **#154 Quote-check findings already in the vault, and the check's known blind spots (residue of #124/#96).** Measured 2026-10-17 over 300 notes: 208 findings in 80 notes — 45 quotes cited to the wrong paragraph, 134 not found as written, 29 footnotes citing a row `id` — and in a hand sample 7 of 10 were real errors. Repairing them edits the vault, so it waits for the user's go-ahead, like #152. Known false negatives, from the 2026-10-17 Sonnet review: 2,141 Pāḷi quotes carry no `db:` footnote and are not tested (the skill now asks for one on every Pāḷi blockquote); in books whose paragraph numbers restart (99 of 217 tables), a quote passes if it matches any occurrence of the number; fragments under 4 words and quotes with fewer than 3 Pāḷi diacritics are skipped; a changed last word is ignored by design. Elided forms (`pan'imassa` for `pana imassa`) still cause false flags. (evidence: measurement and review 2026-10-17; underlying runs as #124 and #96)

- **#152 Finished vault notes cite library books by the wrong number (residue of #113).** The #113 fix stops new mistakes, but notes already published still carry them. Measured 2026-10-17 by running the new checker over the 73 dossiers written since the 2026-09-03 index rebuild (with the hit parser later found to skip 22% of logged books — see Done #89 — so this undercounts): 45 citations in finished notes use a book's Calibre folder number, which names a different document in the index (bhavaṅga note: Anālayo's *Luminous Mind* cited as Calibre #8904, which is a Piya Tan essay; madhupindaka note: Ñāṇananda cited as #696, which is an Ajahn Sumedho anthology). The checker's `cited_not_gathered` list adds more suspects (a Nyanatiloka *Buddhist Dictionary* citation whose number names an Anālayo paper). Whole-vault scan the same day (every `Calibre #N` / `calibre-N` mention, title on the citation line compared with the index title for N): 2,687 mentions name the right book; a strict match (citation line names the title, exactly one document has folder number N and that title) finds **945 fixable mentions in 123 notes**, 15/15 random samples correct (e.g. Gombrich *Theravada Buddhism* 923 → 10253, Sujato *Mystique of the Abhidhamma* 904 → 2560); a looser match (2,332) had false positives in long prose lines, so use the strict one; ~3,200 mentions in 198 notes cannot be matched by machine — mostly pre-rebuild index ids (no copy of the old index survives) and bare id lists in rejection tables. So most older notes cited the folder number, not the index number — the de facto vault convention until now. **User decision 2026-10-17: leave the vault for now.** When picked: apply the strict set only, keep each note's numbers consistent (footnote markers, frontmatter `library_refs`), skip a note where N also correctly names another book, regenerate those notes' PDFs, show the changed-notes list before syncing. The new `cited_not_gathered` list flags old numbers whenever a run reworks a note in the meantime. (evidence: measurements 2026-10-17; underlying runs as #113)

- **#90 REGRESSION — sub-agent summaries still restate their own tool output wrongly.** Done #90 (2026-07-17) made "copy citations verbatim from your resolve log" a dispatch rule. Later runs: a Phase 2 report called a sutta "SN36 Samādhisuttaṃ" when its own resolve output said "SN36.3 Pahānasuttaṃ"; gather summaries repeated Pc rule numbers and a speaker attribution the DB does not support; a library agent reported a snippet inference ("seven perfections" from Endo) as Appleton's content. The orchestrator spot-check caught all three. Fix direction: decide whether the dispatch template lost the rule, or the rule needs a mechanical form (summary lines must quote a logged tool block id). (seen in 3 runs: 20260924-190415, 20260927-061700, 20261011-062929)

### Medium severity

_(#7 moved to Done — gate content check added 2026-06-20)_

_(#49 moved to Done — see Done table above)_

_(#56 moved to Done — --quiet flag added and verified live 2026-07-06)_

_(#59 moved to Done — under-quoted-evidence check now scopes to T1/T2
evidence-section footnotes only, 2026-07-06)_

_(#60 moved to Done — scratch-init now surfaces a reuse warning, 2026-07-06)_

_(#64 moved to Done — re-scoped after empirical audit found the broad
"thin drafts" hypothesis unsupported; a narrower library-coverage check
shipped instead, 2026-07-05)_

_(#71 moved to Done — chain entries now run in their own process group
with a hard kill on timeout; per-entry-timeout + redirect gotchas
documented in Phase 6, 2026-07-17)_

_(#72 moved to Done — phase 6 added to the gate content check, 2026-07-17)_

_(#73, #74, #75, #76 moved to Done — batched docs commit, 2026-07-17)_

_(#77 doc half moved to Done — consolidated-row convention + per-id token
rule documented in the coverage-check section and mirrored in the Phase 7
template example, 2026-07-17; tool residue split off as #89)_

_(#78 moved to Done — harness-fallbacks block added to Sub-agent dispatch
plus three "When something fails" bullets, 2026-07-17)_

_(#79 residue moved to Done — every scratch-* subcommand now accepts
--slug, 2026-07-17)_

_(#80 moved to Done — batched docs commit, 2026-07-17)_

_(#90 moved to Done — resolve-log-verbatim citation rule added to the
dispatch rules list and the dispatch prompt template, 2026-07-17)_

_(#95 moved to Done — vault-relative paths now resolve through one shared
resolver used by both commands, 2026-08-10)_

_(#98 moved to Done — --summary-file/--answer-file give the shell no chance
to eat logged prose, 2026-08-10)_

_(#99 moved to Done — any (T1)-tagged evidence heading now satisfies the
required section, 2026-08-10)_

_(#101 moved to Done — lexicographic/glossary run shape documented in
Phase 7 (shared lookup tool, primary-text-first, batch-parallel gather,
summary table + word-by-word findings), 2026-08-15)_

_(#102 moved to Done — parallel gather dispatch sanctioned with the
ascending-gate, batched-spot-check, one-agent-per-phase rules, 2026-08-15)_

_(#103 moved to Done — the sentinel names the failing entry and reason,
preflight probes the chain for seconds before the long wait, and the stale
"expect self-review" doc line is gone, 2026-08-15)_

- **#97 Scholarly attributions and bibliographic details are written from memory.** *(Revived from Parked — 6 new runs.)* A guessed publisher and volume for a Gethin article; a prior note citing a conference paper as a fabricated "Cambridge UP 2023" book; a lateness claim pinned on Anālayo with no source; Childers 1872 credited for a PED 1921-25 gloss — twice, because the library file name looked like PED; a figure from one author's snippet assigned to another. Fix: extend the cite-from-memory rule to bibliographic metadata and named-scholar positions — name a scholar only with a source read this session, and confirm a dictionary's edition from its title page. (seen in 7 runs: 20260818-190500, 20260904-161444, 20260925-043036, 20260927-090500, 20260927-111500, +2 more — 20260730-045620, 20260924-190415)

- **#111 Gather citations are verified only after the draft is written.** *(Revived from Parked.)* A sub-agent's citation (DN3 §256 for a phrase from DN5 §331) was used unverified until review; GRETIL verse numbers (Maitrāyaṇī, Ṛgveda off-by-one) need the same treatment — GRETIL stamps the verse number at the end of the line. Overlaps #124/#125: once those helpers exist, a pre-draft sweep over every gather citation becomes cheap. (seen in 3 runs: 20260813-155241, 20260912-151050, 20260925-112009)

- **#100 Āgama texts that exist in the EBC vault are reported missing.** *(Revived from Parked.)* `get-agama MA211` returned `found: []` while the BDK file was on disk; earlier, `text_gaps` from sc-parallels was logged as a gap though the Patton translation existed. Fix: get-agama falls back to a file-name scan of `Agamas BDK/` and `Agamas Dhamma pearls/`; Phase 2.5 checks those folders before logging a gap. (seen in 2 runs: 20260730-060651, 20260830-120431)

### Low severity

_(#38 moved to Done — WisdomLib skip clause added 2026-06-20)_
_(#51 moved to Done — thematic gate-vs-work clarification added 2026-06-20)_
_(#52 moved to Done — comparative-religion T1 section documented 2026-06-20)_
_(resolve-citation shell-loop pitfall moved to Done 2026-06-20)_
_(#68 moved to Done — search_vault now strips update banners from CLI
output, parses the JSON underneath, and its error names the real cause,
2026-08-15)_

_(#81 moved to Done — --quiet added to get-ebc-overview, 2026-07-17)_

_(#82 moved to Done — aṭṭhakathā-name table added to the book-code map, 2026-07-17)_

_(#83 moved to Done — N/A gate recipe + thematic explicit-gate caveat documented, 2026-07-17)_

_(#84 moved to Done — document_id instability warning at Rule F4, 2026-07-17)_

_(#85 moved to Done — obsidian create gotchas documented in Phase 7, 2026-07-17)_

_(#86 dropped 2026-08-09 — see Done; single sighting, never recurred across
the 21 runs since, and the workaround is one `rm`)_

_(#87 moved to Done — the timeout diagnostic now lands on stdout as JSON,
not stderr only, 2026-08-10)_

_(#88 moved to Done — search-craft one-liners folded into Phase 2 and Hard Rule 9, 2026-07-17)_

_(#91 moved to Done — --quiet accepted on resolve-citation, lookup-book,
verify-citation, and fetch-transcript, 2026-07-17)_

_(#104 moved to Done — --quiet accepted, folded into the #95 commit,
2026-08-10)_

_(#105 moved to Done — thematic gate map: exactly 2.5/3b auto-skip, every
other gather gate explicit, explicit calls on auto-skipped gates demand
evidence, 2026-08-15)_

_(#107 moved to Done — comparative Indo-Aryan dictionary access recorded
in Phase 4a: DSAL 404 + Wiktionary proxy, csl-orig SLP1 transliteration,
2026-08-15)_

- **#114 Wikipedia craft for Phase 4a is undocumented.** Two complementary
  findings: (a) the plain-text extracts API
  (`api.php … prop=extracts&explaintext=1&redirects=1`, with a UA header and
  an inter-request sleep after a rate-limited first batch) returned clean
  citable text for ~34 articles with zero HTML-stripping — far cleaner than
  html2text on raw HTML, and none of it is in the skill; (b) for niche
  clusters where many articles are stubs or redirects (Buddhist manuscript
  finds), cite the one comprehensive article and log the stubs in Sources
  Investigated, Not Used. Fix: both as a short recipe in the Phase 4a / pi
  fallback guidance. A third run (pi, no WebSearch) hit Brave rate limits after ~5 queries and DuckDuckGo challenge pages, and fell back to the Wikipedia REST/action API with a UA — same recipe. (seen in 3 runs: 20260814-052550, 20260813-081200, 20260911-103350)

- **#115 Thematic non-doctrinal notes: T1-section handling is allowed but
  undocumented.** A pure archaeology/epigraphy run renamed `## Canon
  Evidence (T1)` to `## Inscriptional Evidence (T1)` / `## Manuscript
  Evidence (T1)` and the validator accepted (post-#99, confirmed live) —
  but the agent had to discover the allowance; a directory run then had to
  read `tools/note_checks.py` to confirm that *omitting* the T1 section
  yields only a soft warning and is the correct choice when there is no
  canon content. Fix: one paragraph extending the comparative-religion
  clause to thematic material-culture/directory questions (artefact-
  appropriate headings; omission = soft warning = correct), plus the
  one-line statement in Phase 7. A secular run also read "fix every
  validator warning" as requiring a T1 section it could not honestly fill.
  (seen in 3 runs: 20260813-081200, 20260814-052550, 20260904-200000)

- **#119 Run retrospectives don't record the vicaya repo commit they ran
  against.** The 2026-08-10 triage found 9 of 21 runs came from a machine
  whose checkout version can't be confirmed, forcing staleness to be
  reconstructed from commit authorship — which is why #96's evidence needed
  an authorship caveat and #108 needed a verify-first flag. Fix: add a
  `vicaya_commit:` field to the reflection template's frontmatter
  (`git rev-parse --short HEAD` at Phase 0) so every run's code vintage is
  self-declared. (evidence: triage 2026-08-10 note 14, confirmed again
  2026-08-14 while annotating #96)

- **#136 Footnote ids drift or go undefined in long drafts.** Inline `[^id]` used before defined, stray `[^web-8?]`, a footnote attached to the wrong source. Fix: a used-vs-defined footnote check in validate_note.py. (seen in 3 runs: 20260902-174106, 20260904-200000, 20261011-024434)

- **#137 Vault index edits clip rows or miss their anchor.** An insert into summary-vicaya.md clipped the next table row; byte-exact anchors on `Pāḷi` vs `Pāli` failed; one run found a bullet appended to all 33 catalog sections. The 2026-09-08 index check (`4ffeb30`) catches damage after the fact. Fix: anchor on the section heading, never a body line, and grep that the new line appears exactly once. (seen in 3 runs: 20260908-084542, 20260912-150000, 20260919-041931)

- **#138 Enrichment date and footer rule is unclear.** Runs disagree on whether an in-place enrichment keeps the original note date, takes the run date, or keeps the filename but updates the frontmatter date, and the footer convention is unstated. Fix: one sentence in Phase 7. (seen in 3 runs: 20260911-162500, 20260911-163831, 20260912-053133)

- **#139 Term-meaning searches skip the ṭīkā and Abhidhamma tables.** The key statement often lives only in `*_tik` (uddhacca-kukkucca: s0401t_tik §14) or in `abh*_mul` (Paṭṭhāna §417 for bhavaṅga), but Phase 2 targets name `s*_mul` and aṭṭhakathā. Fix: the Phase 2 dispatch target line lists `*_tik`, `abh*_mul`, Niddesa and Visuddhimagga for term questions. (seen in 3 runs: 20260911-163831, 20260925-043036, 20260925-142300)

- **#140 Validator rules for T1 sections surprise agents.** H3 subsections under a `(T1)` H2 count against its quote ratio; a heading with a suffix after `(T1)` does not match. Fix: state both in the Phase 7 template. (seen in 2 runs: 20260925-112009, 20261010-171500)

- **#141 Gather sub-agents stall at the 600-second watchdog.** In parallel waves, several agents stopped with "no progress for 600s"; one had logged real content and could be gated, others succeeded on retry with a prescriptive numbered search list. Fix: check the dossier before relaunching; give gather prompts a numbered search list. (seen in 2 runs: 20260904-213800, 20260904-221900)

- **#142 Dispatch briefs do not carry the user's shell rules.** Sub-agents ran `awk`/`sed` against the user's standing rules because the brief did not repeat them, and left helper scripts in `temp/`. Fix: a fixed shell-rules line in the dispatch template. (seen in 2 runs: 20261007-025707, 20261011-062929)

- **#143 Obsidian update banner blocks vault search until the update finishes.** Post-#68 the banner is parsed around, but while an update is in progress the CLI prints only the banner and a relaunch does not clear it; `rg` fallback worked. Fix: add "wait for the update, then restart" to the banner note. (seen in 2 runs: 20260905-sangha-light-item-borrow, 20260908-saccanurakkhana-speech-ethics)

- **#144 The full ceremony runs on questions the user considers simple.** The user redirected twice to "just answer"; another bounded question needed >1000 lines of skill. `1e76682` added a research budget; 20261008-133440 postdates it. Fix: a Phase 0 cost triage that offers vicaya-quick for bounded questions. (seen in 2 runs: 20260912-151050, 20261008-133440)

- **#145 check-citation-shape flags things that are not citations.** A PTS page reference inside a rejection-table row (DN 2.222) and a manuscript siglum with a percentage ("KP 5.5%") were read as depth errors. Fix: skip table rows marked as rejected, whitelist sigla near `%`, document the roman-PTS form. (seen in 2 runs: 20260902-133109, 20260905-014337)

- **#146 Phase 1 vault search misses existing notes on the same topic.** An overlapping note surfaced only via summary-vicaya.md because the query lacked its key word; two adjacent bhavaṅga notes were found only at the index update. Fix: Phase 1 also greps the summary-vicaya.md rows for the topic terms. (seen in 2 runs: 20260904-161608, 20260925-142300)

- **#148 The tier of a GRETIL Sanskrit text is unclear.** One run tiered non-Buddhist Sanskrit primary texts as T1 (should be T3); another found the skill's blanket "GRETIL is T3" wrong for Buddhist canonical Sanskrit (Mahāvastu → T1b). Fix: tier by the text's own canonicity, not by the website. (seen in 2 runs: 20260912-151050, 20260924-190415)

- **#149 No rule for "enrich the old note or write a new one".** One run found an un-migrated older note on the same topic and wrote a sibling; another followed a handoff's "enrichment" label when the user wanted a full rewrite. Fix: one paragraph — when to enrich in place, when to write a sibling, cross-link either way, confirm a handoff's run type with the user. (seen in 2 runs: 20260920-023254, 20260927-061700)

- **#150 sync_notes.py cannot carry a deletion or rename.** A remote-side delete blocked the local push of the catalog; a `git mv` fix for a wrong date could not be staged by the script. Separate single sighting: an SSH "Repository not found" with valid https auth (20261016-112900). Fix: stage deletions/renames under the Vicaya/ pathspec; print the remote URL and protocol on failure. (seen in 2 runs: 2026-09-22-rebirth-cosmology-modern-research-ebt, 20260928-004814)

- **#151 Commentaries get flattened into one voice.** A note presented the tradition's deflationary reading of nibbāna as settled, and another described a "commentarial consensus" that hid a real DN-a vs MN-a/AN-a divergence. Fix: treat each commentary as a separate witness; pull the other side of a known dispute before drafting. (seen in 2 runs: 20261001-134330, 20261016-112900)

- **#156 sweep-canon blind spots (residue of #116, from the 2026-10-18 reviews).** Not fixed because each needs a design choice, none caused a wrong answer in a check: (a) noise words are hard to find in `forms` for a common term (*ogha* has 459 distinct forms, 30 shown) — group forms by the letters before the match; (b) the stem probe ignores `--exclude`, so a hint can be satisfied by noise (*ogh* 2,524 rows against 938 real); (c) `rows` are database rows, not paragraphs, and nothing yet gives a paragraph count; (d) `variant_only_rows` also counts cross-references inside `<note>`, not only manuscript variants; (e) `tables[].paranums` carries no row id, and in restarting-paranum books three entries cannot be told apart; (f) a hit in a heading row takes the previous sutta's last paranum; (g) `vin04t_nrf` (Dvemātikā, a root Vinaya text), `vin05t_nrf` and `abh07t_nrf`/`abh09t_nrf` fall in the ṭīkā stratum by their file name, although the text is not a ṭīkā; (h) the vowel probe folds ā→a, so a root like *siṅga* picks up *siṃgāla*. Also still open: `canon_paragraphs.clean_text` deletes block tags without a space, the same fusion fixed here in the sweep. Revive on a run that reports a wrong answer from any of these. (evidence: reviews 2026-10-17 and 2026-10-18; underlying runs as #116)

### Parked — minor, revive only if it resurfaces

Two populations live here (user rule, 2026-08-14): single-sighting issues —
one run reported it, so it is not an issue yet; park it and revive only when
a *second, independent* run reports the same thing (ranked on this machine's
runs per the same day's machine directive) — and older dormant items with
real historical evidence. Never ranked in Phase 6; pull back into the ranked
list at original severity on a fresh report.

**Single-sighting (parked 2026-08-14):**

- **#106 Gather dispatch prompts should name the hypothesis to test, not only
  the search terms.** A Phase 2 agent given the explicit proposition to check
  ("whether paṭigha ceasing at the anāgāmī stage implies domanassa ends before
  arahantship") searched the fetter/citta classification rather than thematic
  stems, and produced the run's cleanest structural argument. Fix: add to the
  dispatch-prompt guidance. (seen in 1 run: 20260730-060651)
  *(parked 2026-08-14 under the single-sighting rule — revive on a second report)*

- **#108 Several Khuddaka texts have empty `english_translation` in the canon
  DB.** SNP7 Vasalasuttaṃ para 136 carried Pāḷi with no English; the run
  reports the same shape for other SNP and Thag rows. Not a skill bug — a data
  completeness question worth an audit (which books/how many rows) before
  deciding whether it needs filling or just documenting.
  *(Verify-first: the reporting run is SBS-resident with an unconfirmable
  checkout — audit the canon DB on this machine before treating it as a
  live data gap.)* (seen in 1 run: 20260726-logical-fallacies)
  *(parked 2026-08-14 under the single-sighting rule — revive on a second report)*

- **#110 Undocumented what `subagent_type: "fork"` actually does in this
  harness.** A run planning a 5-way parallel fan-out found Agent calls
  resolving synchronously ("you are now the fork") rather than backgrounding,
  and fell back to serial in-session batch processing at high context cost.
  Fix: state the observed behavior in the Sub-agent dispatch section so a
  large task doesn't have to discover it mid-run.
  (seen in 1 run: 20260801-150452)
  *(parked 2026-08-14 under the single-sighting rule — revive on a second report)*

- **#117 Teacher-identity runs need setup guardrails.** A teacher with a
  short, commonly-shared name ("Ajahn Poh") let the Phase 4a agent conflate
  two different monks (the Malaysian Chinese Kittisobhano/Huat Poh and an
  "Ajahn Poh" at Dipabhāvan/Suan Mokkh) — caught only by the orchestrator.
  Same run: for teachers with minimal English-language presence (two
  auto-captioned YouTube transcripts as primary source), the run shape
  (YouTube-heavy, T4-only) should be flagged at Phase 0 so expectations are
  set before dispatch. Fix: dispatch guidance for teacher questions —
  require the full formal name in retrieved content before treating an
  identity as established, and a Phase 0 note to flag YouTube-heavy shapes
  early. *(Sighting run is SBS-resident/outdated — verify the gap still
  bites on this machine before spending a session.)*
  (seen in 1 run: 20260813-155241)
  *(parked 2026-08-14 under the single-sighting rule — revive on a second report)*

- **#120 Library availability is discovered mid-run, not at Phase 0.** A
  run lost the whole modern-scholarship gather (Anālayo, Bhikkhu Bodhi,
  Nyanaponika, Gethin, Ledi Sayadaw — all unreachable) because the offline
  library volume was only noticed at Phase 3; the blocker then had to be
  carried as a `blocker`-severity gap in the note. Since #92 the probe is
  cheap and honest (tri-state `source_available`). Fix: run
  `library-folders-check` at Phase 0, before gather dispatch, so an offline
  volume is a known condition the run plans around, not a mid-run surprise.
  *(Sighting run is SBS-resident/outdated — the offline-volume friction it
  reports is environment, though, and #92's tri-state probe is current
  here; the preflight idea stands on its own merits.)*
  (seen in 1 run: 20260809-230226)
  *(parked 2026-08-14 under the single-sighting rule — revive on a second report)*

- **#122 Enrichment triage re-reads the old note by hand every time.** A
  run noted that identifying what an existing note already covers required
  manual re-reading; a helper that diffs a proposed topic against existing
  notes' frontmatter (`canon_refs`, tags) and highlights the uncovered
  residue would speed enrichment triage. Related Working-well discipline:
  the existing note's Critical Gaps table *is* the research plan — this
  would automate its discovery, not replace it.
  (seen in 1 run: 20260810-042343)
  *(parked 2026-08-14 under the single-sighting rule — revive on a second report)*

**Single-sighting (parked 2026-10-17, triage of 98 runs 20260815→20261016 — one line each, revive on a second report):**

- Append-a-section enrichment runs have no placement/footnote guidance (20260816-164754).
- Practice section for a multi-topic theory programme should be one built theme (20260817-034516).
- No `scratch-rename-slug` when the question is replaced mid-run (20260818-170240).
- GRETIL reformat counted as an independent witness — check the corpus provenance file (20260818-170240).
- sacred-texts.com 403s; local library holds the Ganguli Mahābhārata as text (20260818-170240).
- User-requested evidence heading form not covered by the template (20260818-191105).
- Quoted multi-word phrases to search-youtube 0-hit while keywords work (20260831-172511).
- Quality-form vs factor-form of a term stratify differently (dhutaguṇa / dhutaṅga) (20260831-185500).
- `scratch-log --summary-file` run twice duplicates a block (20260902-174106).
- SQLite rejects ORDER BY inside a UNION ALL subquery in canon-SQL recipes (20260903-bhikkhu-upahana-vinaya).
- `find` without `-iname`; `env` eval fails outside the repo root (20260904-161444).
- Chat-mode drift: agent answered instead of running the loaded workflow (20260904-200000).
- PubMed E-utilities needs retry-with-backoff (20260904-200000).
- get-agama / sc-parallels for mn36 returned DN3 material — compare fetched title to the requested code (20260904-213000).
- cross-check should auto-log its output path at write time (20260904-223000).
- EBC frontmatter titles can contradict the text (MĀ 101/102) (20260904-233056).
- Vault writes >10 KB should go through a subprocess `obsidian create` (20260904-233205).
- WisdomLib HTML stripping recipe for pi (20260904-233205).
- Peyyāla compression: refrains live only in a cross-referenced sutta (MN22 → MN54) (20260905-010740).
- Read 2–3 surrounding paragraphs before naming a verse's speaker (20260905-010740).
- Old note's textual claim ("BJT has no pe") contradicted the machine texts (20260905-014337).
- Double backgrounding (`nohup … &` inside a background call) produced an empty review file (20260905-033059).
- A promoted vicaya-quick run cannot backfill Phase 1 evidence into Phases 2–4c (20260905-sangha-light-item-borrow).
- Multi-session run: gate state had to be reconstructed (20260905-sangha-light-item-borrow).
- Parallel dispatch spent half the user's rate-limit quota; each agent re-reads the ~40k-token SKILL.md (20260908-084542).
- Integration delegated to a fork leaves no reviewer to message back (20260911-105106).
- search-canon returned empty for Vinaya queries in Phase 6 that worked in Phase 2 (20260911-162500).
- Term-meaning runs should state the DPD headword count from a query (20260911-163831).
- Channel promotions should record the name exactly as search-youtube returns it (20260911-163831).
- Parivāra/multi-section structural claims need a direct-SQL check (20260911-khandhaka-anadara-anapatti).
- A lighter Phase 3–4c path for narrow named-source enrichment runs (20260912-043103).
- Three Phase 6 review passes are unconditional; make the verification pass conditional (20260912-150000).
- Agent claimed completion of steps whose files were stale; raised a false misfiling alarm (20260912-160000).
- Agent interrupted the user with questions the sources could settle (20260912-160000).
- search-sanskrit `--folder` scoping under-returns and GRETIL index files dominate output (20260912-151050).
- Pre-2026 notes need `tool:` and `## Bibliography` backfilled on enrichment (20260913-154500).
- Machine English of *_att tables is unreliable — quote the Pāḷi (20260913-181500).
- T2 convention (Paṭis/Niddesa/Netti are T2) missing from the reviewer prompt (20260919-041931).
- Phase 5 draft filename diverged from the scratch stem (20260915-105500).
- DN book-code table wrong for this DB build: DN33/DN34 are in s0103m_mul; LIKE is case-sensitive on non-ASCII (20260915-105500).
- Second-reviewer verification pass as a checklist of finding ids (20260915-105500).
- Bare `--slug` created a new dossier instead of attaching to the dated one (20260924-100023).
- Thematic 3b auto-skip message reads as "not applicable" on cross-canon questions (20260924-190415).
- pi dispatch pin should be `VICAYA_SCRATCH=<absolute path>` + `VICAYA_PHASE` (20260925-045957).
- `search-chinese --text` ids are not Taishō numbers; wrong id returns an unrelated text (20260927-033629).
- "An earlier version of this note claimed X" sentences in Findings break Hard Rule 2 (20260927-100000).
- Dispatch prompts omitted step 1 (`scratch-resume`), so calls did not auto-log (20260927-111500).
- search-84000 body search misses TEI `<term>` glossary entries (20260927-111500).
- Note dated from the UTC clock, not local time (20260928-004814).
- Library PDFs that the index says are ok extract empty with pdftotext (20261002-123216).
- Vault path not in the shell env at the Phase 7 write (20261004-190500).
- vicaya-quick's scratch-init omits Target/Falsifier lines (20261008-133440).
- Enrichment rewrites should re-run set-note / citation-shape / validate (20261009-032200).
- DPD inflection tables: grey cells come from corpus membership at render time (20261010-171500).
- WebFetch returns summaries — fetch with curl for anything to be quoted (20261011-024434).
- Lexicographic runs: DPD/PED case frames right after the frequency scan (20261012-120548).
- Caller-named comparison artifacts (before/after) should be built and shown first, inside the note (20261013-103225).
- validate_note.py passes `canon_refs` entries that YAML parses as mappings (20261016-112900).
- Phase 7 should say the vault git repo is the Vicaya/ subfolder (20261016-112900).

**Single-sighting (parked 2026-10-17, second pass):**

- A count that reaches the note must name its basis — rows, occurrences, or paragraphs ("exactly ten times" was ten rows, eighteen occurrences) (20261017-054516).
- A journal article blocked at a third-party host (academia.edu 403) was open access at the publisher's own site — try the publisher before recording it as unobtainable (20261017-054516).
- `scratch-check-coverage` has no token to accept a reviewed, consolidated tail row, so it keeps reporting the tail as unaccounted. By design since Done #77 (a reviewed nonzero residual is an acceptable advisory outcome), and the run predates the #89 ranking; the ask is an `ack` / `Calibre #set:` marker (20261017-054516).
- The vault-index check and the coverage check report findings that belong to a different run's note; say in Phase 7 that those are not this run's to fix, or scope the checks to the run (20261017-054516).

**Older dormant items:**

- **#10 residue: optional `vault-write` wrapper** — disk fallback and
  final-report declaration are already documented (see Done); build the
  wrapper only if macOS demand recurs. (was Medium; 8+ runs, all macOS)
- **#22 Obsidian vault path assumptions across machines** — ongoing
  (iCloud path vs ~/MyFiles), handled per-run each time it comes up.
- **#8 Scope lock for user-named seeds** (was Medium) — original proposal
  (20260527-092930): a Phase 5 checklist confirming every user-named seed
  source was processed or explicitly deferred. Never actually built, and no
  confirmed violation has recurred since the single 2026-05-27 sighting; its
  only other citation was logged `Scope: local`, which shouldn't have counted
  as backlog evidence at all. Revive only if a real violation is reported.
- **#19 Weak-model design — explicit control points** (was Medium) — a
  standing direction, not a single bug: #29, #31, #33, #6, and #45 were all
  closed under this umbrella and #45 (the last-named concrete instance) has
  been Done since 2026-06-20. No live instance remains. Revive if a new
  weak-model-design gap is reported; don't reopen on the strength of this
  stale text alone.

### Content-specific guidance (lower urgency)

- **Phase 0b** — read user-provided vault note paths before angle triage
- **SN 12.15 (Kaccānagotta)** as standing pointer for any
  atthi/natthi/existence-language question; add to Devil's Advocate Q3
- **Ñāṇavīra Thera + pabhassara citta** as default search targets for
  Nibbāna-ontology questions
- **Niddesa** as systematiser for therapeutic bhāvanā pairings
- **Two-note (English + Russian) frontmatter rule** — unchanged
- **Cross-check correction logging** — unchanged
- **Vinaya/philological questions**: EBC Patimokkha + bmc1 folders are the
  primary Phase 1 source, not general vault search (20260531-113545); for
  uncertain Vinaya compounds, DPD lookup before perspective labels
  (20260610-071644)
- **Jhāna questions**: separate sutta vs Abhidhamma reading explicitly;
  never read kaṇṭaka (thorn) as cessation (20260601-135900)
- **Ritual/practice questions**: name the Gombrich/Schopen apotropaic
  counter-position and the Mahāyāna dhāraṇī parallel as standing angles
  (20260605-025640, 20260605-030917)
- **Sense-faculty topics**: also search the diṭṭhasutamutaviññāta formula
  (20260604-162500)
- **Compound technical terms**: search the inner stem (`nīvaraṇ`, not
  `pañcanīvaraṇa`) (20260605-023426)
- **Saṃyutta-anchored topics**: grep the EBC catalogue TSV first; enumerate
  the whole saṃyutta/vagga before citing (20260603-000323, 20260603-004752)
- **Vinaya lodging/monastery-maintenance questions**: search
  "senāsanacārika" (the lodging-inspector term) as a cross-reference target
  — structurally essential but easy to miss since it's only found
  serendipitously via general senāsana searches (20260706-074500)
- **Philological/word-study questions**: pull DPD headwords (meaning_1,
  meaning_lit, construction, sanskrit) for every term in the question at
  Phase 1, before triage — cheap and sharpens the perspective map
  (20260716-224915)
- **antarābhava/intermediate-state questions**: the Puggalapaññatti §36
  definition of antarāparinibbāyī is the canonical T1b anchor for the
  deflationary reading (stronger than commentarial glosses); search the
  antarā- idiom family before asserting sutta-level absence
  (20260812-093512, 20260812-095506)
- **Chinese-heritage audience questions**: proactively search
  Chinese-tradition teachers (Yin Shun, Sheng Yen, Hsing Yun) in Phases
  3/4 rather than letting cross-check flag the gap (20260711-113434)
- **Single-term series notes**: search the noun stem AND its -dhamma
  adjective form (jāti/jātidhamma) — the adjective is often where the EBTs
  generalize the term (20260715-071232)
- **Vault-heavy aggregation runs** (many prior notes on the topic): build
  an explicit Phase 1 seed map of existing notes + the claims each
  documents, so gather targets gaps instead of re-confirming
  (visuddhimagga-novelties run, 2026-07-15)
- **Open curation runs ("identify N suttas…")**: orchestrator-led
  discovery with sub-agents on the mechanical pulls beat delegated
  discovery (Haiku fabricated content descriptions twice); wide-net
  full-candidate gathering before selection also confirmed
  (20260711-094116, 20260711-042246)

## Working well — preserve

- **Enrichment-run scoping for notes in a series**: confirmed across all four
  brahmavihāra runs (mettā → karuṇā → muditā → upekkhā). A Phase 1 vault search
  that maps the existing series *and* the specific angles each sibling already
  covers, before any writing, let each note go deep on its own contribution with
  explicit wikilinks and no duplication — including distinguishing a practical
  retreat note from an existing taxonomic note on the same term.
  (20260806-174019, 20260808-170741, 20260808-upekkha, karuṇā run)

- **Name the hypothesis to test in a gather dispatch prompt, not just the
  terms**: a Phase 2 agent asked to check a specific proposition searched the
  fetter/citta classification rather than thematic stems and produced the run's
  cleanest structural argument. (20260730-060651; see #106)

- **Treat sub-agent completion reports as leads, not results**: re-reading a
  sutta's second half, chasing an under-harvested passage, and pulling a
  Milindapañha window — all things the reports had touched but not mined —
  produced three of the run's best sources. The same discipline caught two
  claims that would have propagated errors (a Visuddhimagga §84 that doesn't
  resolve, an Āgama declared unavailable while on disk); note both failures were
  in *negative* or *locator* claims rather than in quoted content.
  (20260730-045620, 20260730-060651)

- **The two Phase 6 reviewers have genuinely different failure modes**: the LLM
  cross-check reasons about plausibility without canon access; the source-armed
  reviewer re-runs `resolve-citation`/`search-canon`. On one small note they
  independently caught the same mislabeled Vinaya book, and the source-armed
  reviewer caught a second ṭīkā mis-citation the cross-check missed. Worth
  running both even on a short note. (20260731-183100)
  Confirmed three more times: a sati-sampajañña run's two-stage check caught
  two off-by-one paranums and an etymology error before the vault write — and
  the mūla check caught one *inaccurate cross-check correction* (validate
  before applying, per #75) (20260809-230226); a reviewer armed with an
  independent text source (bilara MS rather than the same CST tables) caught
  the Thag 10.1 citation error the resolver itself had masked
  (20260814-053113); and a reviewer that actually ran the tools caught
  DN21 354→353 and found the KvA 505 anchor (20260812-095506). Give the
  reviewer a *different* source than the one that produced the error.

- **Search the concept family before asserting doctrinal absence**: two
  sibling runs on antarābhava both initially said "the word never occurs in
  the suttas" — true of the compound noun, false of the concept, whose
  antarā- idiom family (antarāparinibbāyī, sambhavesin, opapātika) is
  frequent; foregrounding it re-spined both notes for the better. Read a
  user's "frequently mentioned" as a claim about the family.
  (20260812-093512, 20260812-095506; see #116)

- **Name the positions before searching**: a three-position frame
  (cardio/cephalo/non-local) carried a whole cross-tradition synthesis, and a
  five-ecosystem framing gave a 34-centre directory its spine — both decided
  at Phase 1, both made every later source land in a labelled bucket.
  (20260814-101028, 20260814-052550)

- **Wikipedia plain-text extracts API for web-primary surveys**:
  `prop=extracts&explaintext=1` (plus a UA header and an inter-request sleep)
  returned clean citable text for ~34 articles with zero HTML-stripping —
  far cleaner than html2text on raw HTML. (20260814-052550; see #114)

- **One compact paragraph of `calibre #<id>` tokens clears a noisy coverage
  check honestly**: after a library sweep of near-duplicate noise hits, one
  paragraph listing every document ID with its rejection reason took the
  check from 88 unaccounted to 0 — the efficient form of the sanctioned
  consolidated-row pattern. (20260813-155241)

- **Multi-agent sibling isolation is cheap and works**: two agents on the
  *same* question (deliberately) never collided — distinct slugs chosen at
  Phase 0, sibling file names checked before writing. Keep checking
  `data/scratch/` and the vault for sibling slugs before `scratch-init` on
  multi-agent topics. (20260812-095506)

- **A small reusable temp script beats dozens of helper calls for
  structural scans**: one `temp/scan_names.py` counting each name-stem
  across every mūla/att table turned a fuzzy first-attestation question
  into an exact table. (20260814-053113; see #121 for promoting it)

- **Thematic auto-skip fits non-doctrinal questions cleanly**: a pure
  archaeology/epigraphy run with `--class thematic` skipped the
  sutta-anchored gates and spent its budget where the question lives.
  (20260813-081200)

- **Build shared tooling once before fanning out**: one unified `lookup.py`
  written against the raw source files under `dpd-db/resources/other-dictionaries`
  turned every subsequent word lookup into a single command across 9 dictionaries
  (Cone, CPD, CPED, PEU, MW, Apte, Nyanatiloka, DPR, DPD), instead of 5 forks
  each re-discovering 9 file formats. Generalizes: for any lexicographic task,
  check for raw source files underneath a repo's exporter/build tooling before
  assuming a dictionary is unqueryable. (20260801-150452, 20260801-171000)

- **Search library-folders for the primary text before assuming canon-DB-only**:
  a plain `search-library-folders "Dhammaniti"` surfaced the brand-new 2026
  translation the user's word-list annotations were actually drawn from (the
  footnote style matched), letting nearly every word be checked in real verse
  context. Non-canonical and paracanonical texts — nīti literature, modern
  translations — live there, not in the canon DB. (20260801-150452)

- **Query the DPD `lookup` table for the full inflected surface form**, not only
  headword lookups for its hypothesized components: the lookup table parsed
  *pārājikassa/dukkaṭassa/pācittiyassa* as plain dat/gen -a-stem endings with no
  fused pronoun at all — a fourth position that both the commentary and the
  submitter's proposal had missed, and the run's best finding. (20260731-183100)

- **`scratch-check-coverage` doubles as an incidental fabrication detector**: a
  gathered-but-uncited library document flagged by the advisory check turned out
  to be the very source a from-memory claim had misrepresented. Its docs frame it
  as bookkeeping; this is a second, arguably higher-value use. (20260730-045620)
  It also rescues near-misses, not just errors: two of a run's load-bearing
  sources (a Saptabhavasūtra translation, a bardo teaching) were pulled out of
  the unaccounted list and cited. (20260812-093512)

- **Explicit target taxonomy in the dispatch prompt for enumerable
  questions**: when the question decomposes into enumerable parts (e.g. the
  8 Beatitudes), naming each part as an explicit search target in the gather
  agent's dispatch prompt produced one consolidated mapping note with
  resolve-checked anchors per part, making synthesis nearly mechanical.
  (20260717-140500)

- **Per-phase gather sub-agent + parent-synthesis split (#46)**: confirmed
  live 2026-06-20 (20260620-133500) — the gatherer/parent division of labour
  kept the main context clean and focused. Keep delegating all gather phases.
  Re-confirmed with Haiku gather sub-agents on a sati-sampajañña run:
  every phase's citations landed verified and clean (20260809-230226).
- **Definitional loci for "is X a vice/virtue?" questions**: DPD/WisdomLib
  glosses for the specific key terms (*vasavattī*, *issariya-mada*, *dama*)
  gave sharper polarity evidence than thematic stem searches for a
  "Christian spirit of control" comparison; lead with the lexicon on any
  vice/virtue angle. (20260622-053000)
- **Per-run scratch isolation + RESUME protocol**: clean cold resumes across
  compaction and multi-day sessions (many runs); staged context-break system
  completed a ~16.5k-line dossier across 5+ passes with no loss
  (20260604-082408); phase7-draft two-pass vault write keeps partial notes
  out of the vault.
- **Cross-check earns its keep**: caught genuine omissions (hirī/kukkucca,
  SN35.95), misattributions (SN19.1), and tier errors — but its corrections
  must themselves be verified against the mūla (20260605-055802,
  20260606-000000); the validate-before-apply discipline is load-bearing.
- **Devil's-Advocate pass**: caught suppressed evidence pre-draft twice.
- **Search craft**: stem-truncation; id-range/whole-saṃyutta structural
  dumps; per-stratum term-counts as evidence for "later accretion" claims
  (20260603-232301); zero-hit-as-finding move (20260604-143000); searching
  early vocabulary instead of later category names (20260605-093500);
  direct-SQL inspection of CST `<note>` apparatus (20260605-023536);
  well-chosen stems (nekkhamm, pabbajj, brahmacari) plus whole-range pulls
  for cluster suttas gave a thematic run a verbatim Pāḷi+English core
  (20261017-140000).
- **DPD-first + GRETIL whole-corpus** for lexical/etymological questions
  (20260606-000000, 20260610-044213).
- **Library-folders FTS5 index**: excellent results from day one — 32k+
  docs, fast, diacritic-preserving (20260609-012118, 20260609-112239).
- **Vault-first Phase 1** + reading sibling series notes before drafting.
- **Restricted-source runs**: skip-phase logging + self-review recording
  handled user source constraints cleanly (20260608-141608, 20260609-221756).
- **Comparative-religion dual-T1-heading + 3-table shape**: separate
  `## Canon Evidence (T1)` / `## Biblical Evidence (T1)` headings plus three
  comparison tables (matches / differs / one-side-only) cleanly delivered a
  two-tradition comparison end to end; confirmed twice as a recommended
  template for any two-tradition question (20260702-064633, 20260704-230000).
- **vicaya-quick → full-note promotion**: continues to work cleanly across
  multiple runs — scratch-resume reattaches prior auto-logs and gathered
  evidence without loss (20260625-035310, 20260701-205200, 20260706-074500).
- **Paired *_att sutta-title search**: searching the commentary table for
  the sutta-title string ("abhayasutt" in s0402a_att) finds direct
  sutta-specific commentary that thematic stem-search misses
  (20260710-091726)
- **0-hit-as-confirmed-absence**: methodically searching a term in `s*_mul`
  and reporting the 0-hit as positive evidence of absence (after Hard Rule
  12's book-code check) carried 7 of 17 entries in the Vism-novelties
  catalogue (2026-07-15)
- **Phase 3b GRETIL stays high-value/low-cost for EBT doctrinal terms**:
  Udānavarga parallels landed in one search (sankhara run); a
  negative-but-useful Ṛgvedic śoka="flame" finding modeled honest
  light-touch angle reporting (sokaparideva run)
- **Enrichment runs: read the existing note in full first** — its Critical
  Gaps table is the research plan; confirmed clean again (20260715-092000,
  20260715-140000)
- **Direct id-range / anapatti-clause SQL reads beat search-canon snippets**
  for close philological or statistical questions: surfaced the Sekhiya 53
  anapatti-clause asymmetry that a keyword search alone would likely have
  missed (20260701-135123), and a SQL-filtered query cleanly separated the
  Buddha's own locomotion from other flying/vanishing events for a
  quantitative comparison (20260705-053727).

- **Source-armed second reviewer (triage 2026-10-17)**: the single most-praised mechanism of the cycle — 25 runs credit it with catching real errors the external cross-check missed (memory-completed Pāḷi, wrong paranums, carried-over claims, misattributed speakers). Preserve it; #126 is about making it work on pi, not about trimming it. Confirmed again 2026-10-17: cross-check plus source-armed reviewer caught a wrong Citta/Hatthaka citation, a Visuddhimagga Pāḷi typo and an unflagged commentarial rule (20261017-140000). (seen in 26 runs: 20261017-140000, 20260904-223000, 20260912-153500, 20260928-020423, 20261007-025707, +21 more)

- **Verify every reviewer claim against the mūla, in both directions (triage 2026-10-17)**: external reviewers made confident false corrections in at least ten runs (AN7.45 "is AN7.63", DN33 "contains paramattha-sacca", MN40 §435, NP30/PC34 reversed, EA12.1); each was caught because the rule is followed, and verifying a wrong finding sometimes produced the run's best evidence. The same applies to the run's own numbers: two reviewers on one draft plus re-measuring every count against the mūla caught two wrong counts before the vault write — never integrate a reviewer's number without re-measuring it (20261017-054516). (seen in 11+ runs: 20261017-054516, 20260902-133109, 20260904-221900, 20260905-045500, 20260915-031056, 20261012-120548, +5 more)

- **Cross-check `--preflight` (triage 2026-10-17)**: caught a dead chain (429 cap + 402 balance) in ~10 s instead of a 10-minute wait. (seen in 5 runs: 20260831-172511, 20260904-213000, 20260910-042426, 20260911-110444, 20260925-045957)

- **scratch-check-coverage finds real misses despite its noise (triage 2026-10-17)**: it surfaced load-bearing uncited sources (Schumacher; Sujato, Chatchai, Pa-Auk; Jones's Mahāvastu, Endo, Conze) — the case for fixing #113/#89 rather than retiring it. (seen in 3 runs: 20260822-133000, 20260912-150000, 20260924-190415)

- **Count lists and terms programmatically (triage 2026-10-17)**: temp/ SQL counts settled list-stability and first-attestation questions (31 vs 32 body parts across 8+ texts; frequency-matrix-first for lexicographic runs). (seen in 3 runs: 20260817-045540, 20260831-185500, 20261012-120548)

## Notes for the next session

1. The structural direction keeps winning: the three biggest recurring
   failure families of this cycle (.active hijacking, Calibre fragility,
   verifier false negatives #29) were all closed structurally — removing
   shared state, removing the fragile component, teaching the verifier the
   DB's actual storage forms — not by more prose rules.

2. Pāḷi-quote verification (Phase 2 follow-up to citation verification)
   remains on the table; with #29 fixed the verifier can now confirm
   verse-level citations, so this is unblocked.

3. #5 was re-scoped and dropped (2026-06-10): the staged routers already
   solved the context problem in practice, so the kernel/reference
   restructure is shelved unless context complaints recur. The heading-based
   routing is now guarded by `tests/test_skill_routes.py`. #36's doc gaps are
   closed. #19 (structural control points — #33 closed 2026-06-11 with
   `scratch-set-note`, #6 closed 2026-06-11 with `scratch-self-audit`, #45
   closed 2026-06-20) has no live instance left as of 2026-07-06 — parked,
   see Remaining.

4. The 2026-06-11 verification sweep (log: `temp/issue-verify-20260611.md`)
   closed #9, #16, #23/#24, #25, #34, #39, the doc halves of #10, and the
   gate-refusal half of #41; escalated #43 to High as a regression (the
   sequencing rule was lost when `shared/core.md` was removed — closed later
   the same day: helper appends turned out to be flock-protected since
   `ee5917a`, so the rule was restored scoped to hand-edits only, with a
   guard test); and added #45. Every surviving issue now carries a
   "verified 2026-06-11" line.
   Still untestable on Linux: (#14's 403 remains macOS-only, doc-fallback fix
   landed 2026-06-11; #27 cache re-scope — confirm on the next macOS run.)

5. Triage 2026-06-20 (26 runs, 06-11→06-19): the cycle's dominant signal was
   **sub-agent context exhaustion**, fixed structurally (#46) by going to one
   single-phase sub-agent per phase + a `--quiet` helper mode (full data still
   to scratch, only stdout compacted) + a hard transcript cap in Phase 4b.
   This is the same structural-over-prose pattern as prior cycles: remove the
   thing that fills context rather than telling agents to be careful. #35
   (lookup-book) turned out NOT to be the predicted macOS-path issue — dpd-db's
   translator changed to read its TSV path at import time and the loader's
   `lambda: None` ProjectPaths stub broke; fixed by stubbing the TSV path. The
   All High/Medium issues from this triage cycle are now closed. #47 residue
   closed 2026-06-20: `scratch-verify` checks gate *content* (empty/placeholder
   → `content_issues`) and the full 0–4c set; the empty-but-gated silent gap is
   now caught by the verifier structurally. #49 closed 2026-06-20: Hard Rule 12
   (0-hit in expected book → run `lookup-book` before "absent") + orchestrator
   re-verify step (run `verify-citation` on the 2–3 top cited suttas from each
   sub-agent's report before spawning the next). The remaining backlog is all
   Low severity — longer-term structural items (#7 gate-content evidence,
   #19 weak-model control points) and isolated issues (#42 EBC Snp code
   mismatch, #50 .doc extraction, etc.). Quick wins #41 and #45 closed
   2026-06-20. Channel note: "Ego (buddhism
   podcast)" hit 3 sightings this cycle — evaluate for promotion. AGENTS.md
   added at repo root (CLAUDE.md symlinks to it): tests go green *after* the
   main issue is done.

6. Triage 2026-07-05 (21 runs, 06-22→07-05): `64e074a` (2026-06-30) restricted
   vicaya from self-editing SKILL.md/tools, so this cycle's runs all carry
   "Improvement suggestions" instead of direct fixes. The cycle's most
   important discovery wasn't a new bug but a **false negative in the triage
   process itself**: 20260630-040739 recorded "What I changed this run:
   tools/scratch.py word-boundary placeholder fix," but `git log` and the
   current code showed it was never committed — the run's own self-report was
   wrong, and the identical bug reproduced 5 days later. Lesson: "What I
   changed this run" claims need verifying against actual code/git state
   during triage, not taken at face value, even when phrased as a completed
   diff. #54 was picked as this triage's issue and fixed for real this
   session (word-boundary regex on word-final placeholder patterns, keeping
   plain substring matching for punctuation-final patterns like `<fill in>`).
   The other dominant signal, #55 (multi-agent-on-one-scratch phase
   bookkeeping: auto-logged content filing under the wrong phase heading when
   more than one gather sub-agent shares a run), was picked as a follow-on
   issue and closed the same session. Root cause turned out to be simpler
   than the candidate structural fixes floated at triage time (gate-state
   reconciliation against the highest gate written, or moving gating
   authority to the orchestrator): reconciling against the file's own gates
   doesn't actually help, because the shared state file and the file's gates
   are written together and agree by construction — the real gap was that
   SKILL.md's own guidance ("there is nothing to pin or export") talked
   sub-agents out of the one mechanism (`VICAYA_PHASE` pinned inline on every
   helper call) that makes filing immune to the race regardless of dispatch
   timing. Fixed by making that pin mandatory in the dispatch template, plus
   a `phase-source: run-pointer` marker in `tools/scratch.py`'s auto-log so
   any future unpinned call is visible to the post-agent spot-check instead
   of silent. "Ego (buddhism podcast)" (flagged 3 sightings in the prior
   cycle) surfaced again — now past the promotion-evaluation threshold, still
   not auto-promoted per the no-sightings-alone rule.

7. `/vicaya-improve` run 2026-07-05 (no unprocessed runs; picked from the
   existing backlog): closed #61 (`search-library-folders` hangs). Root cause
   was scale, not query syntax — the index is 12.8GB, and a stopword or one
   word of an unquoted phrase forces SQLite to score/sort nearly the whole
   corpus before `ORDER BY … LIMIT` can trim it. Fixed with a
   `set_progress_handler` wall-clock deadline (default 20s, `--timeout` flag)
   that aborts the query and raises a clear `LibraryFoldersSearchTimeout`
   instead of hanging past the caller's own foreground timeout. This also
   partially de-risks #57 (Bash foreground timeout) for this specific helper,
   though #57's broader external-subprocess-dispatch fix is still open.

8. Follow-up session 2026-07-05: before building #64's originally-proposed
   coverage-diff tool, measured the actual problem first — hand-checked one
   scratch/note pair and forked a 6-note survey. Lesson worth repeating: a
   single flagged run (even with a strong, explicit user complaint) is not
   enough evidence to justify a structural fix at the scale first proposed;
   measuring against several real scratch/note pairs upgraded a
   "the agent throws away most of what it gathers" diagnosis into the much
   narrower, verified "library sources occasionally slip past both citation
   and the rejection table" — a smaller, cheaper, better-targeted fix
   (`scratch-check-coverage`). If a future run reports thin drafts again,
   check whether it used a weak/cheap sub-agent model first (the one
   confirmed severe case did) before assuming the general Phase 5 flow
   regressed.

9. `/vicaya-improve` run 2026-07-06 (no unprocessed runs; picked from the
   existing backlog): closed #56 (`search-youtube` missing `--quiet`).
   Verified live against real yt-dlp/YouTube calls, not mocked: `main`
   raised `unrecognized arguments: --quiet` (exit 2), the fix accepts the
   flag and returns identical, valid JSON. A first attempt at a mocked
   `--quiet` regression test was dropped mid-session — it broadly
   monkeypatched `subprocess.run` on the shared stdlib module object, which
   also intercepted the internal `ps` call inside `tools.scratch._run_key()`
   (a `functools.cache`d function keyed to the OS session) and permanently
   poisoned the cached run-key for the rest of the pytest process, causing
   11 unrelated `TestScratchDossier` failures. Lesson: when mocking
   `subprocess.run` broadly for one helper's test, scope the fake to the
   specific command (e.g. check `cmd[0]`) rather than replacing it
   unconditionally — anything else in-process sharing the same `subprocess`
   module object is affected too, and a `functools.cache`d caller can lock
   in the corruption for the rest of the run.

10. `/vicaya-improve` run 2026-07-06 (1 unprocessed run: 20260706-074500, a
    vicaya-quick → full-note promotion for a Vinaya monastery-maintenance
    question): added #67 (vicaya-quick's own SKILL.md never states that
    auto-logs file under whatever phase is active — Phase 1 by default —
    regardless of evidence type, which the main SKILL.md documents but
    vicaya-quick's doesn't inherit into its own text) and one
    content-specific guidance line (search "senāsanacārika" for Vinaya
    lodging/maintenance questions). No regressions, no stale issues found,
    no channel-tuning actions this run. Closed #60 the same session
    (scratch-init now warns when a slug's dossier already exists, naming the
    last gate and note status). #67 closed 2026-07-06 (vicaya-quick's
    auto-logging paragraph now states the Phase-1 default explicitly).
    #58 and #62 also closed 2026-07-06 (see Done table).

11. Triage 2026-07-17 (25 runs, 07-10→07-16): first cycle with heavy pi-harness
    usage — a whole family of findings (#78, #79, and the SELF_REVIEW noise)
    is environment adaptation, not skill defects; the runs' own workarounds
    were consistent and just need documenting. The verification discipline
    paid off again: two claims were rejected against code/git before entering
    the backlog (thematic auto-skip "not working" — by-design; PDF subfolder —
    fixed same day by 90f7781), and the sc-parallels range-uid bug (#69) was
    reproduced live with its mechanism pinned before being ranked High. The
    recurring meta-pattern of the cycle is prose drifting from data at every
    level: EBC parallel metadata vs actual parallel text (#70), sub-agent
    summaries vs raw JSON (#74), reviewer claims vs mūla (#75) — all fixes
    are variations of "read the underlying data before trusting the label."
    Channel note: Ajahn Punnadhammo reached 3 sightings (promotion-evaluation
    threshold); "Ego (buddhism podcast)" saw no new sightings this cycle.
    #69 was picked as this triage's issue and fixed the same session (range
    uids expand into member uids at index build; query's own range uid
    skipped at lookup; verified live on sn12.2 before and after). #70 closed
    as a follow-on the same session (parallel content-check IRON RULE in
    Phase 2 EBC pull + Phase 2.5 + EBC vault section) — both High-severity
    items from this triage are now done. #77's doc half also closed the same
    session (consolidated-row convention + per-id token rule + template
    example fix); its tool residue is #89, parked behind a design decision
    on what "investigated" means mechanically. #78 closed the same session
    too (harness-fallbacks block, folding in #79's doc half; #79's residue
    is the optional CLI --slug arg). #72 closed the same session as well —
    Phase 6 joined the gate content check, making the cross-check/self-review
    structurally unskippable (the same structural-over-prose pattern as #7).
    #71 closed the same session: cross-check chain entries now run in their
    own process group and are group-killed on timeout, ending the
    pipe-held-by-grandchildren hang. The five remaining Medium doc clusters
    (#73, #74, #75, #76, #80) were batched into one docs commit the same
    session — every Medium from this triage is now closed. A final Low batch
    closed #81–#85 and #88 the same session (one small code fix + docs).
    Everything remaining is either parked pending capture/design (#68, #87,
    #89), a nicety (#86 scratch-init --force; #79's --slug closed in the
    second pass), or dormant.

12. Second pass 2026-07-17 (1 run: 20260717-140500, the Beatitudes
    comparative run): two new issues — #90 (gather agent misattributed two
    DN citations by summarising from memory instead of its resolve log;
    caught by the #74 orchestrator spot-check, so the net works) and #91
    (resolve-citation rejects --quiet, verified against the current parser).
    #90 was picked and closed the same session: dispatch rule 5 + a CITATIONS
    block in the dispatch prompt template make resolve-log-verbatim citation
    mandatory for every gather agent. Also this session, per user request:
    the vicaya-improve Phase 6 questionnaire must now be written in plain
    English (rule added to that SKILL.md). One new probationary channel
    recorded (Dalai Lama & Laurence Freeman dialogues — no transcripts, low
    citation value on first sighting). #79's residue was closed as a
    follow-on the same session: every scratch subcommand now accepts
    --slug, so the pi fresh-shell state loss has a first-class fix instead
    of the env-pin workaround. #91 closed as a second follow-on: --quiet
    audited across all subcommands and added to the four lookup helpers
    that lacked it, so uniform prefixed call templates can no longer hit
    an argparse error. The ranked backlog is now empty above the parked
    and capture-blocked items (#68, #87, #89) and the #86 nicety.

13. Triage 2026-08-09 (21 runs, 07-20→08-08). Three things worth carrying
    forward. **(a) The hypothesis-testing rule paid for itself again.** The
    single most-cited complaint of the cycle — `search-library-folders` hanging
    minutes past its documented timeout — came with a confident diagnosis
    ("a common-word query bypasses the FTS guard") that is simply wrong; the
    guard is intact and covers the query. Reading the code found the stat loop
    at `library_folders.py:1325` running outside it, which additionally
    explains five other runs' "library volume offline / PermissionError"
    friction as the same root cause rather than five environment complaints.
    Had the run's own fix been implemented, it would have hardened a guard that
    was already working. **(b) The prose-drifts-from-data family has moved down
    a layer.** Last cycle it was locators (parallel codes, sub-agent summaries,
    reviewer claims); this cycle the same failure appears in *quoted Pāḷi* — a
    verse fabricated outright at SNP13 §226, MN7's cloth simile replaced by an
    unrelated passage, MN21's saw simile garbled — plus scholarly position
    attributions (#97), which slip past every existing rule because those rules
    all name verses and page numbers. Phase 6 caught all of them, so the net
    holds; the open question is whether the fix belongs at Phase 5 (verify each
    blockquote as it is typed) or stays a Phase 6 responsibility. **(c) #93 is
    the cycle's most serious single event and is not really a "bug":** a fork
    given a narrow batch task inferred from sibling files appearing that it
    should finish the job, ran synthesis through git publish unsupervised, and
    then swept the shared `temp/` directory including two siblings' unread
    output. Both halves are absences of a prohibition rather than broken code —
    the dispatch template never says "stop at your own file", and the cleanup
    recipe only guards `data/scratch/`. Worth treating as the structural item of
    this cycle. Also of note: the cross-check chain fell back to SELF_REVIEW in
    8 of 21 runs (#103), so "independent review" is currently the exception, not
    the rule, on these hosts. Channel tally: "Ego (buddhism podcast)" sighted
    again across cycles and is past the promotion-evaluation threshold —
    proposed to the user, not auto-promoted.

14. Session 2026-08-10: **#94 picked and closed.** Two things worth recording.
    First, the triage ranking was challenged and corrected mid-session: of the
    19 new issues only 5 are genuine tool defects (#92, #94, #95, #104, #108);
    the rest are agent discipline, doc gaps, or environment. Ranking by
    run-count alone had put a mostly-behavioural item (#93) second. Worth
    sorting future cycles by *defect vs. discipline* before ranking by
    frequency. Second, run authorship matters for evidence weight: 9 of this
    cycle's 21 runs came from SBS-resident, whose checkout version cannot be
    confirmed, and 12 from bdhrs (current). All five verified defects trace to
    bdhrs runs and were checked against HEAD rather than trusted from the run's
    prose, so they stand — but #103 (7 of 8 sightings resident) is most likely
    one machine missing cross-check config, #108 may be an older canon DB on
    that machine, and #96's evidence is 2/3 resident and may predate #90's
    rules. **Still to apply:** demote #103, mark #108 verify-first, trim #96's
    evidence, and add an issue for recording the repo commit SHA in the run
    reflection frontmatter — right now staleness has to be reconstructed from
    commit authorship, which is why this ambiguity existed at all. Also noticed
    in passing: this file repeatedly cites `tests/test_skill_routes.py` as the
    route-list guard, but that file no longer exists (skills were renamed in
    `ecee2b1`) — the guard it describes may have been lost.
    **Applied/resolved 2026-08-14:** #108 now carries a verify-first flag,
    #96 an authorship caveat (the three runs' authorship can't be resolved
    from here, so annotation beat deletion), the commit-SHA ask is #119, and
    the route-guard worry is a non-issue — `rg` finds no route lists anywhere
    in skill/vicaya/SKILL.md; staged routers were removed entirely (kamma
    20260618), so the test wasn't lost, its subject was. This file's
    references to the guard are historical. #103's demote was overtaken by
    events: the 08-14 runs show the chain configured on this host (one real
    review, one silent sentinel), so it stays Medium, rewritten around the
    stale doc line + fail-slowly diagnostics.

15. Triage 2026-08-14 (9 runs, 08-09→08-14): 13 new issues (#111–#123),
    zero regressions, zero drops. Two themes. **(a) Verification timing**
    keeps producing findings one layer at a time: this cycle an AN6.9/6.10
    off-by-one reached the Phase 5 draft (#111) because the rules verify a
    sample of citations, not all — the same shape as #96 (quotes verified
    only at Phase 6) and #112 (the resolver's own label is the error). The
    system catches these at review; the backlog is steadily moving each
    check earlier. **(b) The environment went quiet:** no library-volume
    hangs (post-#92), no state-loss (post---slug), and the cross-check chain
    produced a real review on pi for the first time (#103's flip) — the
    remaining #103 harm is a stale doc line plus a silent-timeout mode.
    Channel note: the 2026-08-14 directory run's promotes (Al Jazeera
    English, ThePrint, The Quint, TibetTV, Dalai Lama, Karmapa, Root
    Institute, Tushita) were applied directly to data/youtube_channels.md by
    the run and are sitting uncommitted in the working tree — commit them
    with the next batch. Ranking followed note 14's defect-vs-discipline
    rule: the only new tool defect is #112; everything else is doc or
    discipline. **User directive (2026-08-14, applied):** rank and pick on
    THIS machine's (bdhrs) evidence only — the SBS-resident checkout is
    outdated, so its runs may report already-fixed bugs as live. Git
    authorship of the run files is now the provenance source
    (this cycle: 7 bdhrs, 2 resident); #119 (commit SHA in every run's
    frontmatter) will make this self-declared instead of reconstructed.
    **#93 picked and closed this session** (the user's choice from the
    re-ranked bdhrs-only shortlist). Note 13's "treat as the structural
    item of this cycle" held up: both halves were absent prohibitions
    rather than broken code, and the fix adds the boundary at three
    layers (rules list, dispatch template, custom-dispatch paragraph)
    plus the durable-tooling rule that would have saved the siblings'
    files.

16. User rule (2026-08-14, applied immediately): **an issue reported by one
    run is not an issue yet.** Asked to work #112 (verse-book citation
    numbering) the user first asked how many runs reported it — the answer
    was 1 — and directed that single-sighting items are never ranked or
    worked; they park until a *second, independent* run reports the same
    thing (sightings counted on this machine's runs only, per the same
    session's machine directive). Applied retroactively: 14 one-sighting
    issues (#97, #100, #106, #108, #109, #110, #111, #112, #117, #118,
    #120, #121, #122, #123) plus #96 (3 raw sightings, 1 after discounting
    the two resident runs) moved to `### Parked`. Still ranked: only
    multi-run issues (#103 9, #68 4, #102/#105/#107 3, #101/#113–#116 2,
    #89 as 8-run residue) and #119 (evidence is recurring triage cost, not
    retrospectives). Consequence for future triages: a new finding's first
    sighting parks it; the second unparks it at its recorded severity.
    Baked into skill/vicaya-improve/SKILL.md the same session (Phase 3
    new-item rule, Phase 6 revival semantics, Parked-section description)
    so every future triage applies it by default rather than by memory.
17. Session 2026-08-15: **#68 picked and closed** (the user's choice from
    the re-ranked list; #119 was flagged as zero-sighting under the new rule
    and stays parked unless the user orders it as tooling). The fix honored
    the machine directive end to end: the mechanism was confirmed in current
    code (banner rides an exit-0 run; absent app exits non-zero — so the old
    error message was a misdiagnosis, and #58's sentinel work had left the
    banner variant one branch away). Test-writing note: a speculative
    "noise on both sides" case with brackets inside the noise broke the
    first parser sketch — kept the fix to the reported shape (prepended
    banners, bracket-free tail) rather than complicating it for input no run
    has reported.
18. Session 2026-08-15 (second pick): **#103 closed.** The live preflight
    against this machine's real chain returned ok in seconds — direct proof
    of the issue's premise that the stale doc line was suppressing a working
    reviewer. Two implementation notes: (a) keeping `_run_chain_subprocess`
    as a thin `str|None` wrapper over the new status engine meant the #71
    process-group regression tests (real bash children, no mocks) survived
    the refactor untouched — prefer that over updating live-subprocess tests
    to the new contract; (b) live verification caught ANSI color codes
    leaking from opencode's stderr into the diagnostic tail — stripped in
    the reason formatter, worth remembering for any stderr-surfacing code.
    Ranked backlog after this session: #102 (3), #105 (3), #107 (3), then
    the 2-run items (#101, #113-#116) and #119 (zero-sighting, stays parked
    unless ordered).
19. Session 2026-08-15 (third pick): **#102 closed** — docs-only; the three
    evidence runs were re-confirmed bdhrs via git before writing, per the
    machine directive (worth noting the run files moved to runs/processed/
    mid-cycle, so authorship lookups need `--all` and the historic path
    runs/<id>.md). Ranked backlog after: #105 (3), #107 (3), then 2-run
    items #101, #113–#116; #119 parked.
20. Session 2026-08-15 (fourth pick): **#105 closed** — the issue's own fix
    (a compact block where agents look) was implemented literally: the gate
    map replaced the ambiguous thematic paragraph, with callouts at the
    three documented call sites (execution rules item 2, Phase 2.5 exit,
    Phase 4 exit). Docs-only; the machinery (2.5/3b auto-skip, explicit-call
    evidence demand) was already correct per #83 — this closes the
    readability gap, not a mechanism bug. Ranked backlog after: #107 (3),
    then 2-run items #101, #113–#116; #119 parked.
21. Session 2026-08-15 (fifth pick): **#107 closed** — docs-only; the three
    evidence runs were bdhrs and the facts (DSAL 404, Wiktionary proxy,
    csl-orig SLP1) were re-read from the run files, not the issue text, so
    the transliteration table is exactly what the runs verified. Ranked
    backlog after: the 2-run doc items #101, #113–#116; #119 parked.
22. Session 2026-08-15 (sixth pick): **#101 closed** — docs-only. The two
    evidence runs turned out to be the same 65-word task run twice (serial
    and parallel), so the shape is one consensus, not two independent
    reports — noted because it slightly overstates the recurrence count;
    the frequency signal is unaffected. The runs' other globals (fork
    hard-stop, check-citation-shape path) were already Done as #93 and #95.
    Ranked backlog after: the 2-run doc items #113–#116; #89 (8-run
    residue), #119 parked.
23. Triage 2026-10-17 (98 runs, 08-15→10-16): the user asked to work only on the most frequent issues and warned that separate extraction agents would describe one cause in different words. So the 7 batch agents only extracted; all clustering was done in one pass by mechanism and by the component named, and two clusters that looked alike were kept apart on purpose: #113 (wrong library id / one accepted spelling) vs #89 (broad-sweep noise), and #124 (row id cited as paranum) vs #125 (right paranum, wrong sutta name) — each pair needs a different fix. Ranked by run count: #113 (24), #124 (16), #89 (14), #126 (13), #116 (12), #96 (11). Note that `document_id` drift may have been a one-time effect of the 2026-09-02 index rebuild — verify on a normal refresh before building #113 around it. 20260912-150000 and 20260912-160000 describe the same brahmavihāra run; count them once.
24. Session 2026-10-17 (first pick): **#113 closed** in code, not prose — the checker change plus the Rule F4 trap. Two corrections to the triage-time text: the runs' "switch to the stable folder number" fix was wrong (45% coverage, numbers repeat across libraries), and `document_id` drift is a one-time rebuild effect, not ongoing. The fix exposed #152 (45 wrong citations already published), which needs the user's go-ahead to repair. #89 shrank: its "undocumented keys" sub-point is closed; the broad-sweep noise remains. Next pick per the user: note prose must be plain English (parked one-liner from 20261010-171500 — the user ranks it second regardless of run count).
25. Session 2026-10-17 (second pick, user-chosen): **#153 closed** — plain-English note prose, rule plus a `long-sentence` validator warning at 45 words (user's choice after review; 40 was judged too drastic). The candidate limits were measured on the vault, not guessed. Watch the next few runs: if Phase 7 rewrites of 25+ warnings per note prove costly, the fix is earlier drafting discipline, not a looser limit. Old vault notes were not rewritten.
26. Session 2026-10-17 (third pick): **#124 + #96 + #147 closed** in one structural fix (paragraph helper + advisory quote check). The prototype-first approach paid: the first vault run showed 27% of quotes flagged, mostly checker artefacts (inline variant readings, "..." gaps, spacing, sandhi, labels, per-run pairing); each was fixed against real data before shipping. Two vault-repair residues now wait for the user (#152 library numbers, #154 quote findings). Next by frequency: #89 (coverage noise, 14), #126 (reviewer on pi, 13), #116 (absence sweep, 12).
27. Session 2026-10-17 (fourth pick): **#89 closed**. Lesson: the review of a small ranking change found that the coverage check had been blind to a fifth of all library hits since it was written — a parser assumption (flat JSON objects) that no test exercised because every fixture was flat. Build fixtures from real logged blocks. Next by frequency: #126 (reviewer on pi, 13), #116 (absence sweep, 12).
28. Session 2026-10-17 (fifth pick): **#126 closed** (with #123). Not yet verified live: confirm on the next pi run that `vicaya-reviewer` is listed by the `subagent` tool and actually runs a helper; if pi changes its agent discovery, `just sync` is where to fix it. Next by frequency: #116 (absence sweep, 12) — closed 2026-10-18, see item 30.
29. Triage 2026-10-17 (second pass, 2 runs): one finding outweighs the rest. **#155 is a regression of the oldest fixed bug in this file** (.active hijacking): the per-run key assumes one agent process per run, and `opencode serve` breaks that — every session on the server shares one state file. The run's report was a hypothesis until the state file on disk was checked; it is keyed to the server's pid and names the other run's dossier. Before writing a prose pin rule, probe for a per-session id in opencode's environment (the global "claiming something is impossible" rule). Next by frequency stays #116 (absence sweep, 12); #155 ranks above it on severity.
30. Session 2026-10-17/18 (sixth pick, user: "highest count is next"): **#116 closed with #121** — a tool, not another rule: `sweep-canon`. Two lessons. First, the prose rule had landed and failed six more times, so the fix put the evidence in the dossier instead of asking agents to run a sweep. Second, a mutation check lied: restoring a file within the same second, with the same byte count, left Python running the mutated bytecode, so a test failed on clean code and a hang read like a failure. Clear `tools/__pycache__` before and after every mutation, and give each mutation a timeout. The first reviewer's report was lost with the session; its three unfixed defects were found again in this one's context and fixed, the rest are #156. Next by frequency: #125 (resolver mislabels in restarting books, 9); #155 closed (state file now keyed to the opencode session id).
