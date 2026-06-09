# Review — Folder Corpus: extract more file types

## Outcome: ACCEPTED

## What shipped
- `tools/folder_corpus.py`: ebook-convert extractor for the Kindle/Mobipocket
  family + `.rtf`; stdlib `.mht`/`.mhtml` (email) and `.pptx` (zip) extractors;
  misc text/HTML extensions (`.json`, `.jsonl`, `.py`, `.shtml`, `.xhtml`,
  `.xht`, `.xml`); audio/image/video extensions reclassified as noise.
- Re-extraction path: `refresh(retry_failed=...)` + `_should_skip()` retries
  only non-`ok` rows; `--retry-failed` CLI flag.
- `tools/research_sources.py`: wired the `--retry-failed` flag.
- `justfile`: `fc-refresh` (fast) and `fc-refresh-retry` (re-extract failures).
- Docs: `README.md`, `kamma/tech.md` updated.
- Tests: 7 new cases in `tests/test_folder_corpus.py`.

## Verification
- ruff clean; pyright 0 errors; pyrefly 0 errors.
- `tests/test_folder_corpus.py`: 36 passed / 1 skipped (pre-existing weasyprint
  PDF test). Full suite earlier: 156 passed / 2 skipped.
- Real-file spot check via integrated `extract_text`: `.mobi`/`.azw3`/`.azw`/
  `.prc`/`.lit`/`.rtf`/`.mht`/`.pptx`/`.json`/`.shtml` all return text; `.chm`
  degrades to `empty` gracefully.

## Findings addressed during the thread
- **Bug (user-found):** first live refresh re-extracted nothing because
  unchanged size+mtime files are skipped. Fixed with the `retry_failed` path.
- **Simplicity (user-asked):** split into two `just` recipes rather than one
  flag-laden command.

## Notes / deferred (the wall)
- Recovery requires running `just fc-refresh-retry` once (~30–40 min for the
  ebooks). Not run here — the user runs refreshes themselves against the live
  index.
- Deferred: `.zip`/`.7z` archive recursion (~1,213), `empty` image-only PDFs
  needing OCR (~764), `.djvu`/spreadsheets/corrupt PDFs (~40).

## Quality caveats (consistent with existing behavior, not regressions)
- `.mht`/`.shtml` leave `&nbsp;`/`<style>` body text — same `_strip_xml` limits
  as the existing HTML path.
