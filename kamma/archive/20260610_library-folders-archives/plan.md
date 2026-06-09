# Plan — Library Folders: extract text from archives

## Implementation status (2026-06-10) — DONE, ready for review

All phases implemented and validated. `uv run pytest` → 164 passed, 1 skipped
(was 151; +13 archive tests). `ruff` / `pyright` / `pyrefly` all clean on the
two touched files. Touched files: `tools/library_folders.py`,
`tests/test_library_folders.py`, `README.md`, `kamma/tech.md`. Not committed;
`lf-refresh-retry` not run (user runs it).

**Deviations from the plan as written (simpler / more robust):**
1. **No `_ARCHIVE_MEMBER_TEXT_EXTRACTORS` dict.** Instead every non-noise,
   non-archive member is routed back through the existing, tested
   `extract_text()` — html/text in-memory members go via a tempfile bridge
   (`_route_member_bytes`), 7z members via on-disk `extract_text(path)`. This
   guarantees member routing is *identical* to top-level file routing and
   removes a second routing table that could drift.
2. **No `7z l -slt` parsing.** `_extract_7z` extracts the whole archive to a
   tempdir with `7z x` then walks it with `extract_text()`, sidestepping the
   fragile parse of diacritic/space filenames the plan flagged as a risk.
3. **`.css` / `.opf` are not routed to html** — both are in `NOISE_EXTENSIONS`
   and are correctly skipped at the member level (styling / epub packaging,
   not prose). The plan's html-routing list for them was dead code.
4. **Skip rule** is one shared helper `_skip_member(ext)` → skips empty-suffix,
   `NOISE_EXTENSIONS`, and `ARCHIVE_EXTENSIONS` (the last gives no-recursion for
   nested archives) across all three extractors.

> Single best version, ready for review. All numbers below are
> evidence-backed from the real-data probe in `spec.md`. Phase 0 is closed.
> This plan is for a 2-do step: land the code and the tests. The
> operational question of whether to remove the Calibre exclude is
> intentionally deferred to finalize — but note that 1,209 of 1,267
> archives are already being walked (not excluded), so the extractor
> has immediate effect on landing.

## What this plan does

Adds a new extractor to `tools/library_folders.py` that opens `.zip`, `.bz2`,
and `.7z` archives, finds the text files inside, runs the right extraction
tool on each, and concatenates the result into one row in the index per
archive. The change is local to `tools/library_folders.py` plus new unit
tests in `tests/test_library_folders.py`. The dispatcher in `extract_text()`
gains branches for the three new extensions. Caps and member routing are
exactly as the spec defends.

## Caps (as module-level constants in `tools/library_folders.py`)

- `ARCHIVE_MAX_MEMBERS = 5000`
- `ARCHIVE_MAX_UNCOMPRESSED = 2 * 1024**3`  (2 GB)
- `ARCHIVE_MAX_WALLCLOCK = 300.0`  (5 minutes)

These are well above the worst observed (2,823 members, 890 MB uncompressed)
and bound the worst case from a zip-bomb or a runaway archive.

## Phase 1 — `.zip` member extraction

- [x] Add the three constants above near the top of `tools/library_folders.py`
      (next to the existing extension sets).
- [x] Add `_ARCHIVE_MEMBER_TEXT_EXTRACTORS: dict[str, Callable[[Path], ExtractedText]]`
      that maps a member's file extension to the extractor that handles it
      for the path-on-disk case. The keys are extensions with the leading
      dot, lowercased. The values are the existing `_extract_pdf`,
      `_extract_doc`, `_extract_mhtml`, etc.
- [x] Add a small helper `_extract_member_to_tempfile(name: str, data: bytes)
      -> Path` that writes a member's bytes to a tempdir with the right
      extension and returns the path. Used by the pdf / doc / ebook
      branches that need a real file on disk.
- [x] Add the inner-bytes extractors: `_extract_member_html(data)`,
      `_extract_member_text(data)` — small wrappers. `_extract_member_html`
      delegates to `_xmlish_text` (which already handles xml and tag
      stripping). `_extract_member_text` decodes utf-8 with errors="replace"
      and runs the same whitespace collapse the existing extractors do.
- [x] Add `_extract_zip_archive(path: Path) -> ExtractedText`:
    - Try `zipfile.ZipFile(path)`. On `BadZipFile`, return
      `ExtractedText("", "error: bad zip")`.
    - Walk `infolist()`. Skip directories. Skip members whose extension
      is in `NOISE_EXTENSIONS`. Skip encrypted members
      (`zi.flag_bits & 0x1`).
    - Before reading each member, check member count and cumulative
      uncompressed size against the caps. If either cap is hit, return
      `ExtractedText("", "error: archive too large")`.
    - Before processing each member, check `time.monotonic() - start`
      against `ARCHIVE_MAX_WALLCLOCK`. If exceeded, return
      `ExtractedText("", "error: archive timed out")`.
    - For each surviving member: route by extension.
      - `.html`, `.htm`, `.xhtml`, `.xht`, `.shtml`, `.xml`, `.opf`,
        `.css` → `_extract_member_html(data)` (uses `_xmlish_text`).
      - `.txt`, `.md`, `.json`, `.jsonl`, `.py` → `_extract_member_text(data)`.
      - `.mht`, `.mhtml` → write to tempdir with the right extension,
        then call `_extract_mhtml(tmp_path)`.
      - `.pdf`, `.doc` → write to tempdir, then call
        `_extract_pdf(tmp_path)` or `_extract_doc(tmp_path)`.
      - `.docx`, `.odt`, `.pptx` → write to tempdir, then call
        `_extract_zip_members(tmp_path, accept)` where the accept function
        returns True for any non-noise name.
      - `.epub` → same as docx / odt / pptx.
      - `.mobi`, `.azw3`, `.azw`, `.prc`, `.lit`, `.pdb`, `.chm`, `.rtf`
        → write to tempdir, then call `_extract_ebook(tmp_path)`.
      - anything else → skip silently.
    - Per-member try / except so one bad member does not kill the
      archive. The catch logs the failure as a per-member skip and
      continues with the next member.
    - Concatenate the recovered text from all members with `\n\n`
      separators. Collapse whitespace the same way the existing
      extractors do (`re.sub(r"\s+", " ", " ".join(parts)).strip()`).
    - Return `ExtractedText(text, "ok" if text else "empty")`.
- [x] Wire `.zip` into the dispatcher in `extract_text()` (line 498).
      The branch is one line: `if extension == ".zip": return
      _extract_zip_archive(path)`.

## Phase 2 — `.bz2` and `.7z`

- [x] Add `_extract_bz2(path: Path) -> ExtractedText`:
    - If `shutil.which("python3")` is None (shouldn't happen), return
      `"unsupported"`.
    - Open with `bz2.open(path, "rb")` and read all bytes.
    - Try `tarfile.open(fileobj=io.BytesIO(data))` first — the real bz2
      in the corpus (Python Docs) is a tar of 1,070 HTML files. If that
      works, iterate tar members, skip directories and noise extensions,
      extract each member's bytes, and route by extension through the
      per-member extractor table.
    - Else, try `zipfile.ZipFile(io.BytesIO(data))` — in case the bz2
      wraps a zip. If that works, route the inner zip through
      `_extract_zip_archive` logic.
    - Else, treat the decompressed bytes as a single virtual member.
      Detect its type by the file name's suffix (`path.stem`), then
      route via the same per-member extractor table.
- [x] Add `_extract_7z(path: Path) -> ExtractedText`:
    - If `shutil.which("7z")` is None, return `"unsupported: 7z not
      found"`.
    - Run `7z l -slt <path>` to list members with sizes. Parse the
      output to get the per-member paths and uncompressed sizes.
      Handle filenames with spaces and non-ASCII characters (the
      corpus has Pāḷi filenames with diacritics).
    - Same caps and wall-clock as the zip case.
    - For each member: extract to a tempdir using
      `7z x -so <path> <member>`, then route the extracted file by its
      extension through the same per-member extractor table.
- [x] Wire `.bz2` and `.7z` into the dispatcher in `extract_text()`.
      Each is a one-line branch.

## Phase 3 — Tests in `tests/test_library_folders.py`

- [x] `test_zip_extractor_indexes_text_member`: build a zip with one
      `.txt` member containing "target word", call `extract_text` (or
      refresh + search), assert the search hits the archive.
- [x] `test_zip_extractor_filters_noise_members`: zip with one
      `.html` containing "target word" and one `.mp3`; assert the mp3
      is ignored and the html drives the hit.
- [x] `test_zip_extractor_handles_bad_zip`: write garbage to a file
      with `.zip` extension; assert the extractor returns
      `"error: bad zip"` and does not crash.
- [x] `test_zip_extractor_enforces_member_count_cap`: build a zip with
      more than `ARCHIVE_MAX_MEMBERS` members (use a small
      `_TEST_OVERRIDE` constant to lower the cap for tests); assert
      the extractor returns `"error: archive too large"`.
- [x] `test_zip_extractor_enforces_size_cap`: build a zip with a single
      member whose uncompressed size exceeds `ARCHIVE_MAX_UNCOMPRESSED`
      (use the override); same assertion.
- [x] `test_zip_extractor_enforces_wallclock_cap`: monkeypatch
      `time.monotonic` to fake elapsed time past the cap; assert
      `"error: archive timed out"`.
- [x] `test_zip_extractor_skips_encrypted_members`: build a zip with
      one encrypted member; assert the extractor returns
      `"empty"` (or similar) and does not raise.
- [x] `test_zip_extractor_routes_pdf_member`: monkeypatch
      `_extract_pdf` to return a fixed string; build a zip with one
      `.pdf` member; assert the patched function was called and the
      text made it into the result.
- [x] `test_zip_extractor_does_not_recurse_into_nested_zips`: build a
      zip whose only member is itself a zip; assert the inner zip is
      skipped and the outer returns `"empty"`.
- [x] `test_zip_extractor_concatenates_multiple_text_members`: zip
      with two html members; assert both texts appear in the result.
- [x] `test_bz2_extractor_handles_inner_tar`: build a `.bz2` file
      containing a tar with one `.html` member; assert the text is
      recovered. Also test bz2 wrapping a single text file (fallback
      path).
- [x] `test_7z_extractor_handles_inner_text`: build a `.7z` file with
      one `.txt` member; assert the text is recovered. Skip if `7z`
      is not on PATH.

## Phase 4 — Validation bundle (per `kamma/tech.md`)

- [x] `uv run ruff check tools/library_folders.py tests/test_library_folders.py`
- [x] `uv run pyright tools/library_folders.py tests/test_library_folders.py`
- [x] `uv run pyrefly check --search-path . tools/library_folders.py tests/test_library_folders.py`
- [x] `uv run pytest tests/test_library_folders.py -q`
- [x] If any tool flags something, fix it before handing back for review.

## Phase 5 — Documentation

- [x] Update `kamma/tech.md`: under "Library folders search", add a bullet
      noting that `.zip`, `.bz2`, and `.7z` archives are now extracted
      with caps of 5,000 members, 2 GB uncompressed, and 300 s
      wall-clock per archive.
- [x] Update `README.md`: add a one-line note in the library-folders
      section saying archives are now searchable.

## Phase 6 — Hand back

- [x] Do not run `just lf-refresh-retry`. The handoff's "Don't" list
      is explicit. The user runs it.
- [x] Do not commit. The handoff says no git without explicit
      permission.
- [x] Update `kamma/threads/library-folders-archives/plan.md` to mark
      each task as `[x]` as it completes.
- [x] Hand back to the user for kamma 3-review.

## Open risks and what the second agent should look at

These are the things I'd want a second pair of eyes on:

- **Routing table completeness.** The probe found 9,289 members across
  1,263 zips, with the top 20 extensions covering 9,283 of them. The
  6 uncovered members are presumably a long tail of one-offs. If the
  second agent finds an extension in the data that we should route
  differently, that is worth raising.

- **Tempdir handling.** The pdf / doc / ebook branches all need a real
  file on disk. The plan uses `tempfile.TemporaryDirectory` per
  archive, with one file per member. This is the same pattern the
  existing `_extract_ebook` uses. A second agent should sanity-check
  that the tempdir is cleaned up even on exception (use a
  `with` statement, not manual cleanup).

- **Wall-clock granularity.** `time.monotonic()` is the right call for
  elapsed time. The check happens once per member, so a single very
  slow member (e.g. a 180 s `ebook-convert` for a mobi) could push
  past the 300 s budget and trip the cap. That is the intended
  behavior.

- **Per-member try/except scope.** The plan catches broadly to keep
  one bad member from killing the archive. If a second agent wants
  narrower exception handling (e.g. only catch `OSError`,
  `subprocess.SubprocessError`, `KeyError`), that is a reasonable
  refinement.

- **`.bz2` inner format.** The single `.bz2` file (Python Docs) is a tar
  archive containing 1,070 HTML files. The plan tries tarfile first, then
  zipfile, then falls back to a single virtual member. A second agent
  should verify the tarfile path works with the real data (the bz2 is
  8.0 MB compressed, ~8.0 MB uncompressed — the tar is solidly
  compressed).

- **`.7z` listing parser.** `7z l -slt` output is fairly
  human-readable. The plan parses it with simple line splitting. A
  second agent should check that the parsing handles filenames with
  spaces and non-ASCII characters. The corpus has Pāḷi filenames
  with diacritics, so this matters. The three 7z files are:
  `Scientific American.7z` (48 MB, 4 .idx files), `SciAm 2007-02
  (damaged).7z` (5 MB, 1 PDF), `SciAm 2005-11 (damaged).7z` (8 MB,
  1 PDF). All are in `Na Uyana eBook Library/` (not excluded).

- **The 300 s cap on the worst-case archive.** The probe's worst case
  is 49 PDFs. With `pdftotext` taking a few seconds per PDF, total
  is well under 5 minutes. But if any single PDF in that archive
  turns out to be slow (e.g. encrypted, or just very large), the
  cap could trip and the archive will be marked
  `"error: archive timed out"` with whatever text was recovered
  before the cap. That is the intended behavior. If the user would
  rather have a tighter cap (say 120 s), the constants are easy to
  change.
