# Handoff — Vicaya depth / Gemini under-quoting (20260618_vicaya_depth_gemini)

Date: 2026-06-19. **Status: Phase 4 COMPLETE, all open items empirically confirmed. 6 real Gemini runs measured (1 pre-enforcement-fix regression, patched mid-Phase-4; 4 clean post-fix runs, including 1 under the new `error` severity and 1 that specifically exercised the nested-blockquote indentation fix). `under-quoted-evidence` is `severity="error"`. The `agent` frontmatter format was also fixed (host app, not model slug) and confirmed live (`"Gemini 3.5 Flash (Antigravity)"`). Nothing functional outstanding — only loose end is the no-commit state noted below.**

> This thread spans fresh sessions and model switches. Assume zero conversation
> memory. Read `spec.md` + `plan.md` + this file before acting. Update this file
> at every phase boundary and before any window/model switch.

---

## The problem (diagnosed, not assumed)
Gemini-orchestrated Vicaya notes are 3–5× shorter/shallower than Claude ones.
Root cause found by measuring vault notes (each note records its model in the
`agent:` frontmatter field): **Gemini footnotes its sources but does not quote
them** — it collapses full Pāḷi/English passages into inline prose summary.
Failure mode = *summarized-held-text / under-quoting*, NOT "too few words."

Measured baseline (the numbers to beat):

| Note | Model (`agent:`) | Words | Blockquote lines (`^>`) | Footnote defs (`^[^…]:`) |
|---|---|---|---|---|
| integrity-manipulative-tools-ebt | Gemini 3.5 Flash | 1,786 | **0** | 9 |
| santana-nibbana-abhidhamma | Gemini CLI | 1,205 | 6 | 7 |
| papanca-pali-canon (Claude ref) | Claude Sonnet 4.6 | 9,623 | 42 | 25 |

The lever is therefore MORE verbatim quotation, not more prose. A word/paragraph
minimum was explicitly REJECTED (it amplifies the prose-summary defect).

---

## The fix (3 build phases + 1 verification phase) — see plan.md
1. **Prompt rule** in `skill/vicaya/SKILL.md` Phase 5 + Phase 7: every footnoted
   source must also appear as a full blockquote; a footnote without its
   blockquote is a defect. Do NOT rename headings `### Phase 5 — Synthesis` /
   `### Phase 7 — Write the note` (siblings route to them).
2. **Mechanical check** in `tools/note_checks.py::_validate_body` (line ~186):
   emit `ValidationIssue("under-quoted-evidence", …, severity="warning")` when
   `footnote_defs >= 3` AND `blockquote_lines < footnote_defs`. Reuse the
   existing `^\[\^[^\]]+\]:` footnote regex; add a `^>` counter. Verifies on the
   baseline: integrity (9/0) fires, santana (7/6) fires, papanca (25/42) silent.
   Tests live in `tests/test_note_checks.py` / `tests/test_validate_note.py`.
3. **Sibling routers**: heading-stability check ONLY. Copy nothing into
   `vicaya-2-synthesize-review` / `vicaya-3-complete` (they are routers per
   `kamma/project.md`).
4. **Phase 4 — human-in-the-loop** (the real acceptance gate; see below).

---

## Phase 4 measurement commands (for the cold advanced-model session)
After the user runs one real Gemini `/vicaya` task and a new note lands in
`vault/Vicaya/`, measure it and compare to the baseline table above:

```bash
cd /Users/deva/Documents/dps/vicaya
NOTE="vault/Vicaya/<new-note-filename>.md"
wc -w "$NOTE"                                 # word count
grep -c "^>" "$NOTE"                          # blockquote lines
grep -cE "^\[\^[^]]+\]:" "$NOTE"              # footnote defs
grep -i "^agent:" "$NOTE"                      # confirm Gemini model
```
Also run the mechanical check directly (no CLI entrypoint on `note_checks.py`,
call the library function):
```bash
python3 -c "
from tools.note_checks import validate_note_file
from pathlib import Path
issues = validate_note_file(Path('vault/Vicaya/<new-note-filename>.md'))
for i in issues: print(i)
print('count:', len(issues))
"
```
Also read the matching `runs/<timestamp>.md` retrospective for that session —
context on what the agent itself noticed.

Success = blockquote lines now scale with footnotes (roughly `bq >= fn`) and word
count rises toward the Claude range. Then decide per plan Phase 4: Success →
consider promoting the check warning→error; Partial → re-tune threshold/wording;
No change → escalate (hard gate, or deferred gather-phase Phases 1–4 probe).

### Results so far (5 runs measured, in order)

| # | Note | Words | Blockquotes | Footnote defs | Validator | Notes |
|---|---|---|---|---|---|---|
| 1 | `2026-06-18 - balancing-faculties-excess-and-deficit.md` | 2,174 | 14 | 6 | 0 issues | First post-Phase-1-3 run. `bq >= fn`, pass. |
| 2 | `2026-06-18 - knowing-the-knowing.md` | 2,852 | **0** | 6 | **fired `under-quoted-evidence`** | **Regression.** Confirmed root cause: `validate_note.py` (skill/vicaya/SKILL.md ~line 1973) runs *after* the note is already written to the vault, and as a `warning` it doesn't fail the command (exit 0) — so nothing in the workflow forced Gemini to act on it. The SKILL.md "MANDATORY RULE" text alone (lines ~1568, ~1661) was not consistently followed. |
| — | — | — | — | — | — | **Mid-Phase-4 fix applied** (this thread, same session): `skill/vicaya/SKILL.md` ~line 1972-1981 now instructs the agent to read `validate_note.py` output including warnings, fix every warning by editing the note, and re-run validate_note.py until clean *before* proceeding to `generate_note_pdf.py` / the Phase 7 gate. |
| 3 | `2026-06-18 - salayatananirodha.md` | 4,390 | 33 | 18 | 0 issues | First run since the enforcement fix. Clean pass, best ratio yet (bq/fn ≈ 1.8, matches/exceeds Claude reference's 42/25 ≈ 1.7). Only 1 clean data point *after* the fix — not yet enough to promote severity. |
| 4 | `2026-06-19 - dana-with-ones-own-hands.md` | 3,125 | 35 | 14 | 0 issues | Gemini 3.5 Flash (High). bq/fn ≈ 2.5 — best ratio yet, exceeds Claude reference's 1.7. **2nd clean post-fix run.** Run's own retrospective: validator's `line.startswith(">")` blockquote counter doesn't count indented/nested blockquotes (e.g. under a list item); Gemini hit a false-positive `under-quoted-evidence` warning mid-run and worked around it by flattening blockquotes to root level. |
| 5 | `2026-06-19 - piti-sukha-difference.md` | 3,163 | 27 | 15 | 0 issues | Gemini 3.5 Flash (Medium). bq/fn ≈ 1.8, matches Claude reference. **3rd clean post-fix run, 1st run measured after `under-quoted-evidence` was promoted to `error`** — still passes clean, confirming the promotion didn't introduce a regression. No nested/indented blockquotes appeared in this note (column-0 count and `lstrip()` count both = 27), so the indentation fix from run 4 still hadn't been exercised by real note content at this point. |
| 6 | `2026-06-19 - sugata-span-vinaya.md` | 3,541 | 0 (col-0) / 35 (indented) | 20 | 0 issues | `agent: "Gemini 3.5 Flash (Antigravity)"`. **Confirms both remaining open items in one run.** Question was deliberately phrased to request an enumerated list of quoted instances ("give all quotes and references"), which made Gemini format its evidence as a list with blockquotes nested under each item — exactly the shape the indentation bug missed. With the old `line.startswith(">")` logic this note would have scored 0/20 and hard-failed under the new `error` severity; with the fix (`line.lstrip().startswith(">")`) it correctly counts 35 and passes clean. Also confirms the `agent` field fix landed correctly: host app ("Antigravity"), not a redundant model slug. |

**Current read:** the enforcement-gap fix (forcing fix-up on warnings before continuing,
not just printing them) is confirmed by 2/2 clean post-fix runs (3 and 4), with run 4
showing the best quote ratio of all 4 runs (2.5, vs. Claude reference's 1.7). Decision made
(user-approved 2026-06-19): promoted `under-quoted-evidence` to `severity="error"` in
`tools/note_checks.py`, and in the same change fixed the indentation bug found in run 4
(`line.startswith(">")` → `line.lstrip().startswith(">")` at tools/note_checks.py:244) so
nested/indented blockquotes count correctly — this was fixed first so the promotion to a
hard error doesn't hard-block notes with legitimately nested blockquotes. Tests in
`tests/test_note_checks.py` updated: `test_under_quoted_evidence_warning` renamed to
`test_under_quoted_evidence_error` (asserts `severity == "error"`), plus a new
`test_under_quoted_evidence_counts_indented_blockquotes` test. Full test_note_checks.py +
test_validate_note.py suite (25 tests) passes. Re-validated run 4's note after the fix —
still 0 issues.

---

## State of files (build complete and verified)
| File | Planned change | Done? |
|---|---|---|
| `skill/vicaya/SKILL.md` | Phase 5 + Phase 7 quotation rule | ☑ |
| `skill/vicaya/SKILL.md` (~line 1972-1981) | **mid-Phase-4 addition:** force fix-up on `validate_note.py` warnings before continuing to PDF/gate | ☑ |
| `tools/note_checks.py` | under-quoted-evidence check in `_validate_body` | ☑ |
| `tests/test_note_checks.py` | detector fire/silent test | ☑ |
| `skill/vicaya-2-synthesize-review/SKILL.md` | heading-resolves check only (no edit expected) | ☑ |
| `skill/vicaya-3-complete/SKILL.md` | heading-resolves check only (no edit expected) | ☑ |
| `tools/note_checks.py` (~line 244, 250-254) | promote `under-quoted-evidence` to `severity="error"`; fix blockquote counter to `line.lstrip().startswith(">")` so indented/nested blockquotes count | ☑ |
| `tests/test_note_checks.py` | renamed `test_under_quoted_evidence_warning` → `test_under_quoted_evidence_error`; added `test_under_quoted_evidence_counts_indented_blockquotes` | ☑ |

No commits made this session (uncommitted SKILL.md changes flagged by `runs/20260618-043147.md`'s
own retrospective as causing a `git pull --rebase` stash workaround in `sync_run_report.py` —
be aware uncommitted local changes exist when next syncing).

---

## Unrelated fix this session: `agent` field format (user-reported, 2026-06-19)
User noticed the `agent` frontmatter field was writing redundant model slugs, e.g.
`"Gemini 3.5 Flash (Medium) (gemini-3.5-flash)"` — the parenthetical just restated the
family+version already in the string. Fixed in `skill/vicaya/SKILL.md` Rule F5 (~line
1899-1920) and its two reference examples (~line 1710, ~1939): the parenthetical now names
the **host app/harness** (e.g. "Claude Code", "Antigravity", "Gemini CLI", "Codex CLI"),
never the raw model slug. User chose to apply this universally (not just for Gemini) and
to let the agent pick its own host-app label rather than prescribing exact strings. No
code/validator change — `note_checks.py` doesn't validate the `agent` string's contents,
only that it's present. **Confirmed live in run 6**: note's frontmatter reads
`agent: "Gemini 3.5 Flash (Antigravity)"` — host app, no model-slug duplication.

## Next action
Phase 4 decision is made, implemented, and now fully confirmed by real runs:
- `under-quoted-evidence` at `severity="error"` — confirmed not to false-fire on 3
  consecutive post-fix runs (3, 4, 5), including 1 run (5) under the new severity.
- Blockquote-indentation fix — confirmed live in run 6, which had 0 column-0 blockquotes
  but 35 indented ones; without the fix this would have hard-failed as a false positive
  under the new `error` severity.
- `agent` field host-app format — confirmed live in run 6.

Nothing functional remains open. If the thread is to be closed out formally, run
`/kamma:4-finalize` for `20260618_vicaya_depth_gemini` (not done this session — only on
request).

## Constraints for next session
- Validation is project-local per-file (follow `kamma/tech.md`); report tested vs not.
- No commit/push made this session (uncommitted changes: `tools/note_checks.py`,
  `tests/test_note_checks.py`, plus the prior session's uncommitted SKILL.md changes) —
  no commit/push unless the user asks.
- Do NOT copy content into sibling skills; do NOT rename the two routed headings.
