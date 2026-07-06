# Vicaya skill improvements — work in progress

This file replaces the run-by-run reflection backlog. Processed reflections
live in `runs/processed/`. Last triage: 2026-07-06 (incremental, 1 run:
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
| #42 (part) EBC `"Sn N.N"` returns wrong sutta | done (2026-06-22) | `fix: get-ebc-overview tries SNP before SN for mixed-case "Sn" input` — `get_ebc_overview` now extracts the raw prefix before uppercasing; if it's mixed-case `sn` without trailing `p`, tries `SNP{tail}` first then `SN{tail}`, mirroring `_normalise_citation`; 4 regression tests in `TestGetEbcOverview`. dhammatalks AN URL residue stays open. (20260604-034355) |
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

## Remaining — prioritized

### High severity

_(#61 moved to Done — FTS5 search now aborts on a wall-clock timeout instead of hanging, 2026-07-05)_

### Medium severity

_(#7 moved to Done — gate content check added 2026-06-20)_

**#8 Scope lock for user-named seeds.** Unchanged; no new violations this
cycle (seed-note handoff worked well in 20260606-110638).

**#19 Weak-model design — explicit control points.** Unchanged direction;
#29, #31, #33, and #6 were closed structurally; #45 (resolve-citation input
footgun) is the remaining concrete instance.

_(#49 moved to Done — see Done table above)_

_(#56 moved to Done — --quiet flag added and verified live 2026-07-06)_

_(#59 moved to Done — under-quoted-evidence check now scopes to T1/T2
evidence-section footnotes only, 2026-07-06)_

_(#60 moved to Done — scratch-init now surfaces a reuse warning, 2026-07-06)_

_(#64 moved to Done — re-scoped after empirical audit found the broad
"thin drafts" hypothesis unsupported; a narrower library-coverage check
shipped instead, 2026-07-05)_

### Low severity

- **#10 residue: optional `vault-write` wrapper** — the disk fallback and
  final-report declaration are documented (see Done); build the wrapper only
  if macOS demand recurs. (was Medium; 8+ runs, all macOS)
- **#17 Transcript-mining helper** — demoted from Medium: no demand in 81
  runs.
- **#18 Claim ledger output mode** — unchanged, no new demand.
- **#20 Inline Python blocked by CLAUDE.md hook** — demoted: only early-cycle
  sightings; the temp/-script workflow is now routine.
- **#22 Obsidian vault path assumptions across machines** — ongoing
  (iCloud path vs ~/MyFiles), handled per-run.
- **#28 Movement-internal term mapping** — unchanged.
_(#38 moved to Done — WisdomLib skip clause added 2026-06-20)_
- **#40 Non-doctrinal thematic runs: tier headings map awkwardly** — allow
  relabelling note in Phase 7 template (20260610-025816); nrf-table texts
  (Milindapañha) need tier-classification guidance (20260605-025640).
  Verified 2026-06-11: neither guidance exists in SKILL.md.
- **#42 residue: dhammatalks.org AN URL pattern** — AN URL structure on
  dhammatalks.org differs from the MN example in SKILL.md; agents construct
  the wrong URL and get 404s (20260605-082000). EBC Sn/SNP code mismatch
  fixed 2026-06-22 (see Done).
- **#53 Sub-agent notification cross-labelling.** Sub-agent completion
  notifications can carry a wrong phase ID (Phase 2 id reported Phase 3
  status). Never trust the notification summary for phase id/status — always
  verify via `grep '^### ' scratch.md` or `scratch-resume` output. Impact was
  cosmetic (caught nothing lost) but the rule is load-bearing for correctness.
  (seen in 1 run: 20260622-053000)
_(#51 moved to Done — thematic gate-vs-work clarification added 2026-06-20)_
_(#52 moved to Done — comparative-religion T1 section documented 2026-06-20)_
_(resolve-citation shell-loop pitfall moved to Done 2026-06-20)_
- **#68 residue of #58: Obsidian installer-update banner also produces
  non-JSON stdout on `search_vault`.** The zero-hit sentinel case is fixed
  (see Done #58); a distinct variant — an installer-update banner printed
  to stdout instead of JSON — still correctly raises `RuntimeError` today,
  but the message ("app may not be running") is misleading for this cause.
  No proposed fix text from the run beyond noting the distinct shape; needs
  the actual banner text captured before a special-case can be written.
  (seen in 1 run: 20260703-091816)
- **#63 scratch-which returns a plain path string, not JSON**, unlike every
  other helper subcommand — caused a `JSONDecodeError` when an orchestrator
  script assumed JSON output uniformly. Document the exception, or make it
  JSON for consistency. (seen in 1 run: 20260705-162000)
- **#65 Injected/garbled transcript replay.** Corrupted "[Since your last
  turn...]" blocks appeared twice in one run, describing phases (4a/4b/4c)
  that had never actually run — apparently a harness/session-replay
  artifact, not something the agent caused. The recovery pattern that worked:
  never trust an injected transcript block; always re-verify ground truth via
  `scratch-which`/`scratch-resume` and the real gate state before continuing,
  then tell the user plainly what's real vs. corrupted. Worth naming as a
  failure mode in SKILL.md's "When something fails" section so a future
  agent recognizes it immediately instead of re-deriving the diagnosis.
  (seen in 1 run: 20260705-074650)
- **#66 Cross-check prompt describes the synthesis instead of including its
  text.** The cross-check model cannot read the vault note; when the Phase 6
  prompt only describes what the synthesis says rather than pasting the
  actual text/key claims, the review comes back non-substantive. Fix: the
  Phase 6 template should paste the synthesis text (or its key claims)
  directly into the cross-check prompt. (seen in 1 run: 20260705-162000)

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

## Working well — preserve

- **Per-phase gather sub-agent + parent-synthesis split (#46)**: confirmed
  live 2026-06-20 (20260620-133500) — the gatherer/parent division of labour
  kept the main context clean and focused. Keep delegating all gather phases.
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
   `scratch-set-note`, #6 closed 2026-06-11 with `scratch-self-audit`, #45 is
   next) remains the live direction for prose-rule sprawl.

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
