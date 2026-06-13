# Review — Translation Aligner

**GitHub issue:** #23

Two independent reviews were run: a subagent review and a second external
review. Findings reconciled below.

## Blocking (fixed)

- **Range-file alignment bug** (found by subagent; missed by the external
  review, which only tested `mn1`-style suttas). SuttaCentral stores verse
  collections in range-named files — `dhp279:1` lives in
  `dhp273-289_root-pli-ms.json`. The original code globbed
  `<uid>_root-pli-*.json`, so Dhammapada / Theragāthā / Sutta Nipāta produced a
  **silently empty table**. Reproduced live on `dhp279`.
  **Fix:** `locate_segments` now carries the matched file path (`_Located`) from
  the grep hit; the Pāḷi row reads that exact file and the English authors are
  globbed by the file stem (`dhp273-289`), not the uid. Regression test
  `test_range_file_verse_aligns` added.

## Should-fix (fixed)

- `not_found` message wrongly claimed "search is exact" — reworded to say case
  and niggahita are ignored.
- Locale-dependent case folding: considered forcing a UTF-8 locale, but that
  adds an `os` dependency and can fail where `C.UTF-8` is absent. Left plain
  `grep -i` (folds the common ASCII sentence-initial capital under any locale);
  simpler and more robust.

## Doc hygiene (fixed)

- README layout now lists `tools/align_translations.py`.
- `plan.md` task markers updated.
- `spec.md` example corrected (was fictional `mn1`; now a real `an4.31` run) and
  notes the range-file requirement.

## Invalid finding

- External review flagged a `pytestmark` "typo". Verified against the file —
  it is correctly spelled `pytestmark` at line 25; no change needed.

## Accepted as-is (nice-to-have, by design)

- Multi-segment join (` … `) can merge distinct occurrences into one cell — fine
  for a "where it occurs" view.
- `_LOCATE_LIMIT` can undercount the candidate list for very common words; the
  ambiguity gate (>1) still fires correctly.

## Verification

- `ruff`, `pyright`, `pyrefly`: clean on the two files.
- `pytest tests/test_align_translations.py -q`: 11 passed.
- Live: `dhp279` range file now fills; `cakkāni` ambiguity gate fires; scoped
  `an4.31` run produces the full table + EBC file list.

**Verdict:** Ready for `/kamma:4-finalize` (which will commit, comment on, and
close issue #23) once the user gives the go-ahead.
