# Vicaya skill improvements — work in progress

This file replaces the run-by-run reflection backlog. Processed reflections
live in `runs/processed/`. Last triage: 2026-08-14, covering 9 runs from
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

## Remaining — prioritized

### High severity

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

- **#96 Pāḷi blockquotes drafted from memory reach the Phase 5 draft.** Four
  distinct instances across three runs: a *fabricated* Ratana Sutta verse at
  SNP13 §226 that direct SQL confirmed exists in neither `s0501m_mul` nor
  `s0505m_mul`; MN7's cloth simile replaced in the draft by an unrelated
  mind-reading passage (*cetasā ceto paricca pajānāti*); MN21's saw simile
  mis-quoted (`Ubhosu cepi me…hatthesu` for `Ubhatodaṇḍakena cepi…`); and a
  ṭīkā paranum cited for a claim the cited paragraphs don't discuss. All were
  caught at Phase 6 — which means the net works, but the existing rules
  (never cite a verse from memory; Hard Rule 9) are aimed at *locators*, and
  these are *quoted text*. Fix as proposed by two of the runs: a Phase 5
  pre-writing hard check — every Pāḷi blockquote is grep/SQL-verified against
  the canon DB at the moment it is typed into the draft, not left for Phase 6.
  *(Authorship caveat, confirmed by git 2026-08-14: 2 of the 3 sighting runs
  (20260806-174019, 20260808T065938Z) are SBS-resident, i.e. an outdated
  checkout whose mistakes may simply be pre-fix code — per the user's
  2026-08-14 directive, rank on this-machine evidence only, so the live
  weight is 1 run (20260731-183100, bdhrs) plus the same-family locator
  instance caught pre-note in 20260812-095506, also bdhrs.)*
  (seen in 3 runs: 20260806-174019, 20260808T065938Z, 20260731-183100)

- **#97 Position attributions written from model memory escape the
  cite-from-memory rule.** A sentence attributing to Nattier a position on the
  Mahādeva five theses was written mid-draft from memory and was substantively
  backwards (Nattier and Prebish argue Mahādeva is *later* and unconnected to
  the primary schism), in a paragraph where every numbered citation around it
  was correctly sourced. The existing rule targets verses and page numbers, so
  a claim of the form "X argues that…" / "modern scholarship holds…" passes
  straight through. Fix: extend the Phase 5 drafting check to scholarly
  position attributions — route each through a source read this session or
  soften to tradition-level attribution. Caught, incidentally, by
  `scratch-check-coverage` (see Working well). (seen in 1 run: 20260730-045620)

_(#98 moved to Done — --summary-file/--answer-file give the shell no chance
to eat logged prose, 2026-08-10)_

_(#99 moved to Done — any (T1)-tagged evidence heading now satisfies the
required section, 2026-08-10)_

- **#100 sc-parallels `text_gaps` needs an explicit EBC fallback step.** A
  Phase 2.5 agent reported SA 470 as a "hard text gap … cannot be
  content-checked from local sources"; the Patton translation was sitting in
  the EBC vault, and it turned out to be one of the most valuable sources in
  the run (its closing verse forecloses a misreading the note would otherwise
  have carried). The agent checked only the offline SuttaCentral archive and
  treated absence there as absence everywhere. Fix: make the fallback an
  explicit numbered step in the Phase 2.5 instructions — on non-empty
  `text_gaps`, check `Agamas Dhamma pearls/<nik>-patton/` and
  `Agamas BDK/<nik>-bdk/` before logging a gap. Same family as #70: a
  metadata-level claim logged without checking the text underneath.
  (seen in 1 run: 20260730-060651)

- **#101 No documented run shape for lexicographic/glossary tasks.** A
  65-word dictionary cross-reference task does not map onto the standard
  one-question / seven-gather-phase structure. Both runs adapted the same way
  — merge canon+library into one ad hoc "dictionary gather" phase per batch,
  skip 4a/4b/4c with logged justification, and replace the evidence sections
  with a summary table plus per-word findings — but had to improvise it,
  since SKILL.md's fixed-format guidance names only the series and
  comparative-religion templates. Fix: generalize "Caller-supplied fixed
  formats" to cover structurally non-essay deliverables (glossaries,
  catalogues, comparative tables) under the existing rule (keep frontmatter /
  Question / Findings overview / tail sections; substitute the evidence
  headings), and name the batch-parallel-gather + single-synthesis shape.
  (seen in 2 runs: 20260801-150452, 20260801-171000)

- **#102 Parallel gather dispatch works but is undocumented.** Three runs
  dispatched the gather phases (2.5, 3, 3b, 4a, 4b, 4c) as parallel sub-agents
  instead of sequentially; all three report substantial wall-clock savings,
  zero misfiling, and zero `phase-source: run-pointer` leaks — helper writes
  are lock-serialized and the phases are independent source domains. The only
  cost is that gates must still be *written* ascending, so a parallel 4b/4c
  refuses its gate until 3 and 4 have gated, needing one cheap backfill pass.
  The skill currently mandates sequential dispatch (for orchestrator
  spot-checks between agents). Fix: document parallel dispatch as sanctioned
  for independent gather phases, with the ascending-backfill expectation and a
  note that the post-agent spot-check still has to happen — just batched
  afterwards rather than between each. (seen in 3 runs: 20260721-172000,
  20260730-045620, 20260730-060651)

- **#103 The cross-check chain fails slowly, and the pi doc line is now
  stale in the harmful direction.** Originally 8 runs fell back to the
  `# SELF_REVIEW:` sentinel (7 of them from one machine whose checkout and
  config can't be confirmed). The 2026-08-14 pair flips the picture on this
  host: the chain IS configured (deepseek-v4-pro via opencode/openrouter) and
  one run got a genuine 5-issue review, while the other got a silent sentinel
  after 180s with no error surfaced — so both halves are live: the skill
  still says SELF_REVIEW is "the expected outcome on pi" (now wrong here, and
  it suppresses running the check at all), and a failing chain entry waits
  out its full timeout before failing without saying which entry failed or
  why. Fix, ascending: correct the pi cross-check line to "run it, don't
  assume the fallback"; preflight the chain with a tiny prompt before a long
  wait and report which entry failed; capture first-successful-output (don't
  re-invoke a chain that already returned a substantive review).
  (seen in 9 runs: 20260723-032557, 20260724-vassa-split-two-places,
  20260726-cognitive-biases, 20260726-logical-fallacies, 20260801-132709,
  20260806-174019, 20260808-170741, 20260808-upekkha-brahmavihara-
  practical-retreat, 20260814-101028; +1 contrary success: 20260814-052550)

- **#111 Gather citations are verified only after the draft is written.** A
  thematic teacher-comparison run's Phase 2 agent cited AN6.10 for content
  that is AN6.9 (*Anussatiṭṭhānasuttaṃ*, s0403m2_mul:9); the off-by-one
  propagated into two locations of the Phase 5 draft and was caught only at
  Phase 6 self-review. The existing rules verify a *sample*, not the set:
  #49 has the orchestrator re-verify the 2–3 highest-priority citations per
  agent, #90 requires citations to be copied verbatim from a resolve log
  (which was silent here because the gather agent never resolved this one).
  Fix as the run proposes: before the Phase 5 draft is written, run
  `resolve-citation`/`verify-citation` over *every* sutta citation the gather
  agents produced — off-by-one paranums should fail at gather time, not in
  Phase 6. Same defect-vs-discipline family as #96, one layer down
  (locators, not quoted text). *(Evidence caveat: the sighting run is
  SBS-resident — an outdated checkout per the user — so per the 2026-08-14
  directive this is ranked only if it reproduces on this machine; #49's
  sample-only rule exists in the current SKILL.md regardless, so the
  discipline gap is plausible here too.)* (seen in 1 run: 20260813-155241)

- **#112 resolve-citation answers in CST-internal numbering for the verse
  books, diverging from conventional citations.** Asked to resolve the
  Theragāthā row standard scholarship cites as Thag 10.1, resolve-citation
  returned "TH233 Kāḷudāyittheragāthā" — CST's per-book sutta index, not the
  chapter.verse form every modern edition and the note's readers use. The
  reverse direction is already handled (`verify-citation "Thag 10.1"`
  resolves correctly; SKILL.md tells agents to cite by chapter.verse), but
  resolve-citation's own label silently produces citations nobody recognises,
  and in this run it took an independent reviewer re-checking against the
  bilara text to catch it. Fix: for Thag/Thig/Khp, surface the conventional
  chapter.verse alongside (or instead of) the internal index, and flag the
  divergence in the book-code map. Distinct from Done #29 (Thag/Thig/Kp
  *aliases* in verify-citation) — this is the numbering layer.
  (seen in 1 run: 20260814-053113)

### Low severity

_(#38 moved to Done — WisdomLib skip clause added 2026-06-20)_
_(#51 moved to Done — thematic gate-vs-work clarification added 2026-06-20)_
_(#52 moved to Done — comparative-religion T1 section documented 2026-06-20)_
_(resolve-citation shell-loop pitfall moved to Done 2026-06-20)_
- **#68 residue of #58: Obsidian installer-update banner also produces
  non-JSON stdout on `search_vault`.** The zero-hit sentinel case is fixed
  (see Done #58); a distinct variant — an installer-update banner printed
  to stdout instead of JSON — still correctly raises `RuntimeError` today,
  but the message ("app may not be running") is misleading for this cause.
  **No longer capture-blocked:** 20260726-cognitive-biases records the actual
  shape — Obsidian's desktop CLI prepends startup lines such as
  `Loading updated app package…` before the JSON — and 20260813-155241
  reports the banner blocking the CLI for an entire run (all searches via
  `rg` fallback, note written via direct disk). Fix is now writable: strip
  leading non-JSON lines before parsing (or detect the banner and retry),
  and reserve the "app may not be running" message for genuine absence.
  Both new sightings fell back to `rg` over `$VICAYA_VAULT_PATH` successfully.
  (seen in 4 runs: 20260703-091816, 20260723-032557,
  20260726-cognitive-biases, 20260813-155241)

_(#81 moved to Done — --quiet added to get-ebc-overview, 2026-07-17)_

_(#82 moved to Done — aṭṭhakathā-name table added to the book-code map, 2026-07-17)_

_(#83 moved to Done — N/A gate recipe + thematic explicit-gate caveat documented, 2026-07-17)_

_(#84 moved to Done — document_id instability warning at Rule F4, 2026-07-17)_

_(#85 moved to Done — obsidian create gotchas documented in Phase 7, 2026-07-17)_

_(#86 dropped 2026-08-09 — see Done; single sighting, never recurred across
the 21 runs since, and the workaround is one `rm`)_

_(#87 moved to Done — the timeout diagnostic now lands on stdout as JSON,
not stderr only, 2026-08-10)_

- **#89 (residue of #77) scratch-check-coverage counts raw index hits, not
  investigated candidates.** The doc half is closed (consolidated rows are
  the sanctioned account for FTS-noise tails), but the underlying signal
  quality stands: the advisory count is dominated by shelf noise from broad
  sweeps (50–300 hits), which buries the one real miss the check was built
  to catch (see Done #64). Possible tool follow-ups, none picked yet:
  distinguish hits whose files were actually extracted/read from raw index
  hits; a relevance/snippet threshold; or excluding hits matched only via a
  generic query word. Needs a design decision on what "investigated" means
  mechanically before any code. Re-reported 2026-07-30 ("137 of 147
  unaccounted" read as alarming until the skill's expected-tail guidance was
  recalled) with a cheaper interim proposal than the full design decision:
  print a one-line reminder in the tool's own output that a large residual is
  the expected outcome of a broad FTS sweep. Re-reported twice more this
  cycle: 20260814-052550 (43 unaccounted after a consolidated row — "the
  residual COUNT can stay high and still be fine" needs saying up front) —
  the reminder proposal stands. (residue of the 8-run evidence
  under #77; +2 runs: 20260730-060651, 20260814-052550)

_(#88 moved to Done — search-craft one-liners folded into Phase 2 and Hard Rule 9, 2026-07-17)_

_(#91 moved to Done — --quiet accepted on resolve-citation, lookup-book,
verify-citation, and fetch-transcript, 2026-07-17)_

_(#104 moved to Done — --quiet accepted, folded into the #95 commit,
2026-08-10)_

- **#105 Thematic-run gate documentation cluster.** Three confusions, one
  root: the thematic auto-skip rules live in prose far from the call sites.
  (a) The original sighting: gating Phase 4 does not auto-gate 4b/4c — only
  2.5 and 3b auto-skip on `--class thematic`, and a run assumed the Phase 4
  gate covered 4a–4c, with `scratch-verify` reporting 4b/4c missing
  afterwards (20260801-155704). (b) Muscle memory from sutta-anchored runs
  had an agent call `scratch-gate 2.5` explicitly on a thematic run and get
  the by-design refusal (20260813-081200). (c) The work-vs-gate rule ("DO
  the work for applicable angles, let the gate auto-write, never call it
  explicitly") remains easy to misread mid-run (20260814-053113). Fix: one
  compact block in the thematic section naming exactly which phases
  auto-skip, which need explicit gates, and that an explicit gate call on an
  auto-skipped phase demands evidence by design — plus a one-line callout
  at each gate example. (#83 documented the mechanics; this issue is about
  putting them where the agent looks.)
  (seen in 3 runs: 20260801-155704, 20260813-081200, 20260814-053113)

- **#106 Gather dispatch prompts should name the hypothesis to test, not only
  the search terms.** A Phase 2 agent given the explicit proposition to check
  ("whether paṭigha ceasing at the anāgāmī stage implies domanassa ends before
  arahantship") searched the fetter/citta classification rather than thematic
  stems, and produced the run's cleanest structural argument. Fix: add to the
  dispatch-prompt guidance. (seen in 1 run: 20260730-060651)

- **#107 Comparative Indo-Aryan dictionary access notes.** Three runs
  re-derived the same access facts: DSAL's CDIAL search CGI
  (`dsal.uchicago.edu/cgi-bin/romad/cdial.pl`) now 404s after a platform
  migration and the Internet Archive Turner copy is lending-only, but
  Wiktionary's root entries encode the Mayrhofer/Turner consensus and work as
  a proxy; the Cologne `csl-orig` plain-text dictionaries (mw.txt, ap90.txt)
  are directly fetchable from raw.githubusercontent.com but need SLP1
  transliteration (ā=A, ś=S, ṛ=f, ṇ=R) — search `darSiv`, not `darśivas`.
  Fix: record both in the Phase 4a/web guidance.
  (seen in 3 runs: 20260721-154716, 20260721-172000, 20260801-155704)

- **#108 Several Khuddaka texts have empty `english_translation` in the canon
  DB.** SNP7 Vasalasuttaṃ para 136 carried Pāḷi with no English; the run
  reports the same shape for other SNP and Thag rows. Not a skill bug — a data
  completeness question worth an audit (which books/how many rows) before
  deciding whether it needs filling or just documenting.
  *(Verify-first: the reporting run is SBS-resident with an unconfirmable
  checkout — audit the canon DB on this machine before treating it as a
  live data gap.)* (seen in 1 run: 20260726-logical-fallacies)

- **#109 No per-phase summary helper for very large scratch dossiers.** A
  650KB scratch file needed careful offset/limit reads plus grep to navigate
  after compaction; a 42k-line one recurred later in the cycle. Resume works
  correctly — this is a navigation-cost nicety, not a correctness gap. Fix
  sketch: a `scratch-summary` subcommand extracting the key findings per phase.
  (seen in 1 run: 20260720-141435)

- **#110 Undocumented what `subagent_type: "fork"` actually does in this
  harness.** A run planning a 5-way parallel fan-out found Agent calls
  resolving synchronously ("you are now the fork") rather than backgrounding,
  and fell back to serial in-session batch processing at high context cost.
  Fix: state the observed behavior in the Sub-agent dispatch section so a
  large task doesn't have to discover it mid-run.
  (seen in 1 run: 20260801-150452)

- **#113 The `Calibre #<id>` token has two candidate ids and only one is
  right.** Two runs stumbled over the same ambiguity from different sides:
  library-folders hits carry an FTS `document_id`, while file paths carry a
  *parenthesised Calibre-library id* that is a different number — and the
  note convention `Calibre #<id>` doesn't say which one to cite. Rule F4
  says the `book_id` must come from the hit's `document_id`, but doesn't
  name the path-id trap; one run flagged that a mismatched id silently
  *passes* the coverage check (both numbers happened to match in its case).
  Fix: one clarifying clause at Rule F4 and the coverage-check section —
  the token is always the FTS `document_id`; the parenthesised path number
  is a separate Calibre id never used in notes.
  (seen in 2 runs: 20260813-155241, 20260814-101028)

- **#114 Wikipedia craft for Phase 4a is undocumented.** Two complementary
  findings: (a) the plain-text extracts API
  (`api.php … prop=extracts&explaintext=1&redirects=1`, with a UA header and
  an inter-request sleep after a rate-limited first batch) returned clean
  citable text for ~34 articles with zero HTML-stripping — far cleaner than
  html2text on raw HTML, and none of it is in the skill; (b) for niche
  clusters where many articles are stubs or redirects (Buddhist manuscript
  finds), cite the one comprehensive article and log the stubs in Sources
  Investigated, Not Used. Fix: both as a short recipe in the Phase 4a / pi
  fallback guidance. (seen in 2 runs: 20260814-052550, 20260813-081200)

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
  one-line statement in Phase 7.
  (seen in 2 runs: 20260813-081200, 20260814-052550)

- **#116 Absence claims need a synonym-family sweep, and the rule exists
  only in the series format.** Two sibling runs on antarābhava made the
  same mistake from opposite sides: asserting "the word never occurs in the
  suttas" without sweeping the *concept family* — the antarā- idiom
  (antarāparinibbāyī, sambhavesin, opapātika, AN 9.12) is frequent even
  though the compound noun is absent, and foregrounding it re-spined the
  note. SKILL.md's absence-search rule (stem + synonyms, Hard Rule 12) is
  written only inside the series-format section. Fix: generalize it to
  Phase 2 as a checklist item — before asserting a doctrinal term is absent,
  search near-synonyms and grammatical variants and count them; a doctrinal
  term can be absent while its concept is frequent. Also: when the *user*
  says a concept is "frequently mentioned", read that as a claim about the
  family, not the compound. (seen in 2 runs: 20260812-093512, 20260812-095506)

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

- **#118 The orchestrator's own inline calls are exempted from the phase
  pin by implication.** SKILL.md says there is "nothing to pin" while a
  single agent works Phases 0/1 and 5–7, and the harness-fallback block
  frames `VICAYA_PHASE` as a sub-agent rule — so an orchestrator's own
  Phase 1/2 inline calls ran unpinned and surfaced `phase-source:
  run-pointer` markers (harmless while phases run linearly, but the marker
  exists precisely to be absent). Fix: one clause in the harness-fallback
  block — pin on every helper call once you are working more than one phase
  in a session, orchestrator or not.
  (seen in 1 run: 20260814-101028)

- **#119 Run retrospectives don't record the vicaya repo commit they ran
  against.** The 2026-08-10 triage found 9 of 21 runs came from a machine
  whose checkout version can't be confirmed, forcing staleness to be
  reconstructed from commit authorship — which is why #96's evidence needed
  an authorship caveat and #108 needed a verify-first flag. Fix: add a
  `vicaya_commit:` field to the reflection template's frontmatter
  (`git rev-parse --short HEAD` at Phase 0) so every run's code vintage is
  self-declared. (evidence: triage 2026-08-10 note 14, confirmed again
  2026-08-14 while annotating #96)

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

- **#121 Stratum-distribution scan is hand-written SQL every time.** The
  single most useful operation for "when does X first appear" questions —
  counting each name-stem across every mūla/att table classified T1a/T1b/T2
  — turned a fuzzy biographical question into an exact first-attestation
  table, but the run had to write a one-off `temp/scan_names.py` to get it.
  Fix: promote it to a helper subcommand (per-term tier-classified counts
  across all canon tables). Same shape as the Working-well entry on
  per-stratum term-counts as accretion evidence.
  (seen in 1 run: 20260814-053113)

- **#122 Enrichment triage re-reads the old note by hand every time.** A
  run noted that identifying what an existing note already covers required
  manual re-reading; a helper that diffs a proposed topic against existing
  notes' frontmatter (`canon_refs`, tags) and highlights the uncovered
  residue would speed enrichment triage. Related Working-well discipline:
  the existing note's Critical Gaps table *is* the research plan — this
  would automate its discovery, not replace it.
  (seen in 1 run: 20260810-042343)

- **#123 The second-reviewer prompt carries a Claude-Code-specific
  prohibition.** The "Do NOT use SendMessage" line in the Phase 6
  second-reviewer dispatch is wrong on RLM/prime harnesses, where child
  agents MUST reply via `agent_message.send(receiver_role='parent')` — a
  run had to override the prompt's own instruction to make the reviewer
  work. Fix: a harness note next to the line (mirrors the #78
  harness-fallbacks pattern). (seen in 1 run: 20260812-095506)

### Parked — minor, revive only if it resurfaces

Real evidence exists but demand is currently dormant. Not ranked in Phase 6;
pull back into the main Low severity list only if a new run reports it.

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
  direct-SQL inspection of CST `<note>` apparatus (20260605-023536).
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
