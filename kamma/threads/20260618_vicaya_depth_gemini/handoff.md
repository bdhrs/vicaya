# Handoff — Vicaya depth / Gemini under-quoting (20260618_vicaya_depth_gemini)

Date: 2026-06-18. **Status: Phase 4 (empirical verification) IN PROGRESS. 3 real Gemini runs measured so far (1 pre-enforcement-fix regression found and patched mid-Phase-4; 1 clean post-fix run). Need ≥1 more post-fix run before deciding on promoting the check to `severity="error"`.**

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

### Results so far (3 runs measured, in order)

| # | Note | Words | Blockquotes | Footnote defs | Validator | Notes |
|---|---|---|---|---|---|---|
| 1 | `2026-06-18 - balancing-faculties-excess-and-deficit.md` | 2,174 | 14 | 6 | 0 issues | First post-Phase-1-3 run. `bq >= fn`, pass. |
| 2 | `2026-06-18 - knowing-the-knowing.md` | 2,852 | **0** | 6 | **fired `under-quoted-evidence`** | **Regression.** Confirmed root cause: `validate_note.py` (skill/vicaya/SKILL.md ~line 1973) runs *after* the note is already written to the vault, and as a `warning` it doesn't fail the command (exit 0) — so nothing in the workflow forced Gemini to act on it. The SKILL.md "MANDATORY RULE" text alone (lines ~1568, ~1661) was not consistently followed. |
| — | — | — | — | — | — | **Mid-Phase-4 fix applied** (this thread, same session): `skill/vicaya/SKILL.md` ~line 1972-1981 now instructs the agent to read `validate_note.py` output including warnings, fix every warning by editing the note, and re-run validate_note.py until clean *before* proceeding to `generate_note_pdf.py` / the Phase 7 gate. |
| 3 | `2026-06-18 - salayatananirodha.md` | 4,390 | 33 | 18 | 0 issues | First run since the enforcement fix. Clean pass, best ratio yet (bq/fn ≈ 1.8, matches/exceeds Claude reference's 42/25 ≈ 1.7). Only 1 clean data point *after* the fix — not yet enough to promote severity. |

**Current read:** the enforcement-gap fix (forcing fix-up on warnings before continuing,
not just printing them) looks like the right lever — run 3 is the strongest result of
the three. But it's only one post-fix sample. Do not promote `under-quoted-evidence` to
`severity="error"` until at least one more post-fix run confirms it's not a fluke.

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

No commits made this session (uncommitted SKILL.md changes flagged by `runs/20260618-043147.md`'s
own retrospective as causing a `git pull --rebase` stash workaround in `sync_run_report.py` —
be aware uncommitted local changes exist when next syncing).

---

## Next action
User will run one more real `/vicaya` Gemini task and report the note path + run path back
to this thread/handoff. Next session: measure it with the commands above, add it as row 4 to
the results table, and decide:
- **Pass again (2/2 post-fix clean)** → promote `under-quoted-evidence` in `tools/note_checks.py`
  to `severity="error"`, update `tests/test_note_checks.py` expectations, report back to user
  before making the change (per global rules: get approval before the change, not just before
  reporting it).
- **Regresses again** → the enforcement-gap fix isn't sufficient on its own; re-open the prompt
  wording in SKILL.md (lines ~1568, ~1661, ~1972-1981) rather than touching the checker threshold.

## Constraints for next session
- Validation is project-local per-file (follow `kamma/tech.md`); report tested vs not.
- No commit/push unless the user asks.
- Do NOT copy content into sibling skills; do NOT rename the two routed headings.
- Do NOT promote the check severity without presenting the decision to the user first (this is
  a behavior-changing, hard-gate-affecting change, not a pure bugfix).
