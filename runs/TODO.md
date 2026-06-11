# Vicaya skill improvements — work in progress

This file replaces the run-by-run reflection backlog. Processed reflections
live in `runs/processed/`. Last triage: 2026-06-10, covering 81 runs from
2026-05-28 to 2026-06-10. Three structural refactors landed during that
window and resolved whole families of findings: per-run scratch isolation
(`ee5917a`, 06-07), Calibre removal in favour of the library-folders index
(`888be14`, 06-09), and the scratch/helper simplification (`9a77539`, 06-10).

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

## Remaining — prioritized

### High severity

None open.

### Medium severity

**#6 Agent failure checklist before final response.** Unchanged proposal
(`scratch-self-audit` printing a fixed checklist). Supporting evidence this
cycle: the Devil's-Advocate pass caught suppressed evidence twice
(20260605-022801, 20260603-232301) and validate-before-apply flipped a wrong
cross-check tier claim (20260606-000000) — the checklist pattern works when
it exists; it should be structural.

**#33 Helper to set the scratch `**Vault note:**`/PDF header.** The Phase 7
hard gate only scans `[REJECTED]` when that header holds the saved note path,
but there is no subcommand to set it — agents hand-edit the scratch header.
(seen in 4 runs: 20260602-144756, 20260603-225147, 20260604-123434,
20260606-103820)

**#34 search-vault returns 0 results for valid queries — including plain
ASCII.** "parents" → [] while rg finds 12 files; same for samvega, urgency,
abhibhāyatana, kasiṇa. The traceback and launch-command bugs were fixed in
`b1f71a7`, but the empty-index behaviour needs verification post-fix — if it
persists it's an index-staleness/coverage bug, not a diacritic bug. (seen in
4 runs: 20260530-030129, 20260603-044544, 20260606-000000, 20260609-230426)
(verify against current build)

**#14 Web search 403 / parameter failures.** Refreshed: Google Search API
returned 403 on every query in 3 recent runs (20260605-025640,
20260609-112239, 20260609-230046). WebFetch on direct URLs/arXiv worked as
fallback. Either fix credentials or document web search as
best-effort-with-WebFetch-fallback.

**#32 Phase-key naming mismatch.** SKILL.md headings say "Phase 4a/4b/4c"
but the helper accepts `4`; `scratch-log 4a` errors. Reported in the second
run ever (20260528-143000) and again 12 days later (20260609-230046) — still
unfixed. Quick win: accept aliases or print the valid phase list in the
error. 

**#7 Phase exit criteria missing for non-scratch dimensions.** Unchanged —
gate checklists are still tick-by-agent. Related fresh evidence: scratch-gate
7 leaves checklist boxes unchecked even after passing (20260603-225147);
Phase 7 audit checks headings but not footer/bibliography style
(20260603-225147).

**#8 Scope lock for user-named seeds.** Unchanged; no new violations this
cycle (seed-note handoff worked well in 20260606-110638).

**#10 Obsidian CLI bypass.** Refreshed: on the macOS machine Obsidian is
frequently unavailable to the CLI (app not registered, socket discovery
fails, `ls` subcommand missing), so disk fallback is the de-facto norm and
runs handle it correctly. `b1f71a7` fixed the launch command. Remaining
value: the `vault-write` wrapper idea + declaring the fallback in the final
report. (seen in 8+ runs, all macOS)

**#16 Tool failure operational rules.** Unchanged — consolidate "when X
fails, do Y" into one actionable reference. This cycle added candidates:
lookup-book → resolve-citation + direct sqlite; Google 403 → WebFetch;
verifier false-negatives → CST table+para citation.

**#19 Weak-model design — explicit control points.** Unchanged direction;
#33 remains a concrete instance (#29 and #31 were closed structurally).

**#35 lookup-book broken on machines where `cst_book_translator.py` is not
at the expected sibling path.** Fell back to resolve-citation + direct
SQLite. Add a path fallback or env var. (seen in 2 runs: 20260609-221756,
20260610-044213)

**#27 uv cache needs escalated access (macOS sandbox).** Refreshed, promoted
from Low: 4 recent runs hit it; working convention is repo-local
`UV_CACHE_DIR` (`temp/uv-cache` or `.uv-cache`). Document one standard
location in SKILL.md. (seen in: 20260601-075124, 20260606-112752,
20260609-221756, 20260610-071644)

### Low severity

- **#9 YouTube transcript fetch failures / hangs** — (stale — verify): zero
  sightings in 81 runs since 05-28.
- **#17 Transcript-mining helper** — demoted from Medium: no demand in 81
  runs.
- **#18 Claim ledger output mode** — unchanged, no new demand.
- **#20 Inline Python blocked by CLAUDE.md hook** — demoted: only early-cycle
  sightings; the temp/-script workflow is now routine.
- **#22 Obsidian vault path assumptions across machines** — ongoing
  (iCloud path vs ~/MyFiles), handled per-run.
- **#23 Milinda paranum / #24 CST Extra books** — unchanged.
- **#25 wisdomlib.org failures** — refreshed: 403s (20260531-091930) and
  302-redirects-to-homepage extracted as content (20260604-032539); Phase 4c
  needs redirect detection + search fallback.
- **#28 Movement-internal term mapping** — unchanged.
- **#38 WisdomLib "mandatory on every run" wrong for non-Indological
  topics** — add skip clause (20260609-230046); same run suggests "arXiv IDs
  cannot be guessed — use the search endpoint".
- **#39 search-canon JSON-parsing notes** — `jq` may be absent (2 runs);
  parse helper JSON with python3; never read verify-citation via `tail -1`
  (20260604-004624).
- **#40 Non-doctrinal thematic runs: tier headings map awkwardly** — allow
  relabelling note in Phase 7 template (20260610-025816); nrf-table texts
  (Milindapañha) need tier-classification guidance (20260605-025640).
- **#41 scratch-gate missing-gate name hard to spot in JSON output**
  (20260529-silabbataparamasa); validate_note.py silent on success
  (2 runs) — print an explicit PASS line.
- **#42 EBC overview code mismatch for Suttanipāta** (Sn 2.2 → SN2.2 wrong
  sutta, 20260604-034355); dhammatalks.org AN URL pattern 404s
  (20260605-082000).
- **#43 Same-run parallel auto-logging corrupted scratch (UTF-8)** — one
  sighting post-isolation (20260606-110638); the cross-run case is fixed,
  same-run parallel helper calls against one scratch file should be a
  documented hard rule.

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

## Working well — preserve

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
   closed. #6 and #19 (structural control points, e.g. #33) remain the live
   direction for prose-rule sprawl.

4. Several "(stale — verify)" items (#9, #34-post-fix, UV_CACHE_DIR
   scratch-state loss) need one cheap verification run each before being
   either closed or re-prioritized.
