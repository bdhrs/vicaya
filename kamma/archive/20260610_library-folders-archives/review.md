## Thread
- **ID:** library-folders-archives
- **Objective:** Make text inside `.zip`/`.bz2`/`.7z` archives searchable via the library-folders index (one row per archive).

## Files Changed
- `tools/library_folders.py` — archive constants + `_skip_member`, `_route_member_bytes`, `_archive_result`, `_extract_zip_archive`, `_extract_bz2`, `_extract_7z`; three dispatch branches in `extract_text()`.
- `tests/test_library_folders.py` — 13 new archive tests (text/noise/bad-zip/member-cap/size-cap/wallclock/encrypted/pdf-routing/no-recursion/concat/bz2-tar/bz2-fallback/7z).
- `README.md`, `kamma/tech.md` — document archive support and per-archive caps.
- `kamma/threads/library-folders-archives/plan.md` — marked done; deviations recorded.

## Findings
| # | Severity | Location | What | Why | Fix |
|---|----------|----------|------|-----|-----|
| 1 | minor | `tools/library_folders.py` `_extract_7z` | Size/member caps are applied *after* `7z x` extracts the whole archive to a tempdir; only the 300 s subprocess timeout bounds extraction. | A hypothetical 7z bomb could fill disk before the cap trips. | Left as documented residual risk — only 3 small `.7z` files exist in the corpus and the wall-clock timeout bounds the run. Not worth pre-extraction list parsing (the fragile path the plan flagged). |
| 2 | nit (process) | working tree | `skill/vicaya/SKILL.md`, `tools/research_sources.py`, `tests/test_research_sources.py` are modified but belong to the separate in-progress `obsidian-cli-fix` thread. | They must not be committed as part of this thread. | Stage only this thread's files at finalize/commit. |

## Fixes Applied
- During implementation: replaced the plan's `_extract_pdf`-test approach assumption — encrypted-member test now builds a real AES zip via `7z` (stdlib can't write encrypted zips).
- Design deviations from plan (simpler/more robust), recorded in `plan.md`: route every member through existing `extract_text()` instead of a second routing dict; `7z` extract-to-tempdir-then-walk instead of `7z l -slt` parsing; `.css`/`.opf` skipped as noise.

## Test Evidence
- `uv run pytest` → 164 passed, 1 skipped (was 151; +13).
- `uv run ruff check` → clean. `uv run pyright` → 0 errors. `uv run pyrefly check` → 0 errors.
- Read-only real-data probe over real corpus archives: smallest zips `ok`; worst-case `Translations Series.zip` (869 MB, 49 PDFs) `ok` in 45.5 s (< 300 s cap); `Python Docs.bz2` (tar→HTML) `ok` 23 M chars; `Scientific American.7z` `empty` (all `.idx`, noise-filtered); damaged SciAm 7z `empty` (extracts to a scanned PDF with no text layer — honest). Zero exceptions; caps never falsely tripped.

## Verdict
PASSED
- Review date: 2026-06-10
- Reviewer: Claude (same agent as implementer — noted as less independent; compensated with adversarial diff pass + real-data probe)
