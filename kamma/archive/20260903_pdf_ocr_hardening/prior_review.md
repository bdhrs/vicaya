# Honest review — PDF OCR fallback work (e22ef34, f5328e0, 7b85607)

## Verdict

The feature is competently built and unusually well-defended for a first cut: subprocess isolation, a hard timeout, a page cap, a kill switch, and thirteen new tests. That is better discipline than most changes of this size. But the tests all stop at the subprocess boundary, and every genuinely risky decision in the change is on the far side of that boundary. What is proven is the plumbing; what is unproven is everything that actually costs you a corpus.

Findings below, ordered by how much they can hurt.

---

## 1. `PYTHONPATH` is set with `setdefault` — the worker breaks for anyone who has it set

```python
env = dict(os.environ)
env.setdefault("PYTHONPATH", str(_REPO_ROOT))
```

`setdefault` is a no-op when `PYTHONPATH` already exists. On any machine where it is set to something else, the child's `from tools.library_folders import _ocr_worker_main` fails, the worker exits non-zero, and every scanned PDF in the library is recorded as `error: ModuleNotFoundError: No module named 'tools'`. `cwd=_REPO_ROOT` is what saves it today (Python puts the script dir on the path for `-c`... it puts the *cwd* on the path), which means the `PYTHONPATH` line is simultaneously broken and load-bearing-looking. Append, do not `setdefault`:

```python
existing = os.environ.get("PYTHONPATH", "")
env["PYTHONPATH"] = f"{_REPO_ROOT}{os.pathsep}{existing}" if existing else str(_REPO_ROOT)
```

## 2. The chunking comment claims a property the code does not have

```python
# Chunked calls: ... 10-page chunks return in seconds each and keep a hung
# chunk from losing all prior work.
```

Nothing is emitted until every chunk finishes — `parts` is joined and returned at the end. The single 1800s timeout covers the whole file. If chunk 3 of 15 hangs, the subprocess is killed at 1800s and chunks 1–2 are lost with it. The comment describes a design (incremental emit, or a per-chunk bound) that was not implemented. Either implement it (stream one JSON line per chunk and keep the last good prefix) or delete the claim. A comment that asserts a safety property the code lacks is worse than no comment — the next reader will trust it.

## 3. Truncation at 150 pages is silent and permanent

A 600-page scanned book is OCR'd for 150 pages, recorded with status `ok`, and then skipped forever by `_should_skip` because size and mtime never change. Nothing in the row says "this document is 25% indexed". For a research tool whose whole value is "search everything I own and cite it", a document that silently answers *no* to a query it contains is the worst possible failure — it is indistinguishable from the book not existing. At minimum record a distinct status (`ok: ocr truncated at 150 pages`) so it is queryable and so `--retry-failed` can be taught to revisit it later. Right now recovering these requires knowing which files were affected, and that information was never written down.

## 4. Dropping `-layout` silently invalidates the existing index, and nothing forces re-extraction

The extraction algorithm for every PDF in the corpus changed. `_should_skip` compares size, mtime, and status only — it has no notion of extractor version, and `SCHEMA_VERSION` was not bumped. So after this commit the index is a permanent mixture: PDFs indexed before the change keep their `-layout` interleaved text, PDFs indexed after get reading-order text. There is no command that fixes this short of deleting the index by hand, and no note anywhere telling a user to. If extraction behaviour is going to change, either bump the schema version or add an `extractor_version` column that participates in the skip check. Cheap now, archaeology later.

Separately: the change is defensible for two-column books but is not free. Default mode reflows by poppler's heuristics; `-layout` preserves physical alignment. Tables, verse layout, interlinear Pāḷi/English, and side-by-side glossaries get worse. That is very likely a bad trade for parts of this particular library. It was not measured — no before/after on a real two-column book appears in the commit, the spec, or the tests. "Two-column books extract in reading order now" is an assertion, not a result.

## 5. The worker protocol is one stray print away from silent data loss

The contract is "the child's entire stdout is one JSON object". `pdf-inspector`, `onnxruntime`, or PDFium printing a single warning line to stdout turns a successful OCR into `error: pdf ocr worker returned junk` — the extracted text is discarded and the diagnostic does not include what was actually printed, so it is undebuggable from the index. Given this stack loads native ONNX providers, stdout noise is likely, not hypothetical. Use a sentinel-delimited payload, a temp file, or fd 3; and when the JSON fails to parse, put the first line of the offending stdout in the status.

## 6. OCR runs on failure modes where it cannot possibly help

`_extract_pdf` falls back whenever the status is not `ok`, which includes `error: pdftotext timed out`, encrypted PDFs, and corrupt files. A PDF that already burned the pdftotext timeout now gets a further half-hour of OCR before failing anyway. Gate the fallback on `empty` (and arguably the specific "no text layer" cases) rather than "anything not ok".

## 7. Deletion scoping fix (f5328e0) is correct but fragile and unindexed

Scoping deletion to the walked roots is the right fix for the wipe, and the regression test is the right test. Two things:

- It reads every row in `documents` with `fetchall()` and filters in Python. This is a `WHERE source_root IN (...)` query. On a large index that is a needless full materialisation.
- Matching is exact string equality between `str(root)` and the stored `source_root`. If a root is ever configured with a trailing slash, through a symlink, or non-resolved, nothing matches and stale rows are never deleted again — silently. Failing safe is better than wiping, but a silent permanent no-op is still a bug waiting to be found by someone wondering why deleted books keep appearing in results. Normalise (`resolve()`) on both write and compare.

Also: that commit carries an unrelated change to the YouTube channels data file. Keep fix commits clean.

## 8. Dependency weight

`onnxruntime` unpinned as a main dependency is a large native wheel with platform-specific builds, added so that a fallback most users never trigger works without an extras flag. The reasoning (bare `uv sync` strips extras) is legitimate and matches your stated preference for must-have-plus-kill-switch. But `onnxruntime` with no version floor will float to whatever resolves, and this stack is sensitive to ONNX runtime versions. Pin a floor at least.

## 9. Test coverage is honest about what it stubs, and that is the problem

Every OCR test stubs either `pdf_inspector` or `subprocess.run`. Not one test has ever seen real OCR output, a real PDFium load, or a real chunk timing. The tests prove the error-handling ladder — which is genuinely worth having — and prove nothing about whether the feature works. There is no fixture with an actual scanned PDF, not even one marked `skipif` on the dependency being importable. Given the deadlock that motivated the whole subprocess design was found by running it, the suite cannot catch a regression in the thing that actually broke.

Also `_ort_dylib_path` returns the first match of a `sorted()` glob — a lexicographic sort over version-suffixed sonames picks `.so.1.10.0` over `.so.1.9.0`. Fine with one wheel installed, wrong the day there are two.

## 10. Kill switch matches only the literal string `0`

`VICAYA_LIBRARY_FOLDERS_OCR=false`, `=no`, or `=` silently leaves OCR on. For an escape hatch someone reaches for when a refresh is stuck, that is the wrong direction to fail.

---

## What I would do next, in order

1. Fix the `PYTHONPATH` append (5 minutes, prevents a whole class of "OCR does nothing on my machine").
2. Make truncation visible in the status, so partial books are recoverable.
3. Fix or delete the misleading chunking comment.
4. Decide the `-layout` question with an actual measurement on a real two-column book in the library, and add extractor versioning to the skip check either way.
5. Add one real end-to-end OCR test behind a skip guard.
