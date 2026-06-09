# Handoff — Library Folders: archives (.zip/.7z/.bz2)

## Status
New thread, not started. The predecessor thread `library-folders-extraction`
(archived at `kamma/archive/20260609_library-folders-extraction/`) added ebook/
mht/pptx/misc extractors + a `retry_failed` refresh path. Archives were
explicitly deferred there; this thread is that deferred work. User said "zips
are up next."

## Where everything lives
- Extraction logic: `tools/library_folders.py`. The dispatcher is
  `extract_text(path) -> ExtractedText` (~line 460). It routes by
  `path.suffix.lower()` through these sets/branches:
  `TEXT_EXTENSIONS`, `HTML_EXTENSIONS`, `EPUB_EXTENSIONS`, `MHTML_EXTENSIONS`,
  `EBOOK_CONVERT_EXTENSIONS`, and explicit `.docx`/`.pptx`/`.odt`/`.pdf`/`.doc`.
  Anything unmatched returns `ExtractedText("", "unsupported: <ext>")`.
- `NOISE_EXTENSIONS` (~line 32): extensions skipped entirely at the *walk* stage
  (`_accepted_file` / `_iter_files`) — they never reach `extract_text`. NOTE:
  noise filtering happens on the OUTER file's extension during the walk; it does
  NOT yet apply to archive *members*. You must filter members yourself.
- `ExtractedText` dataclass: `{text: str, status: str}`. `status` is `"ok"`,
  `"empty"`, `"unsupported: ..."`, or `"error: ..."`. `text.strip()` truthiness
  decides ok vs empty in most extractors.

## The pattern you almost certainly want to reuse
`_extract_zip_members(path, accept: Callable[[str], bool]) -> ExtractedText`
(~line 325). It opens the zip, reads every member where `accept(name)` is true
and `not name.endswith("/")`, runs each through `_xmlish_text`, concatenates,
collapses whitespace. epub/docx/odt/pptx all delegate to it. For a generic
archive you want the same shape but route each member through the right
extractor (by member extension), not just `_xmlish_text` — e.g. a `.zip` holding
`.txt`/`.html`/`.pdf` members. Watch out: `.pdf`/`.doc`/ebook members need a real
file on disk (pdftotext/ebook-convert take paths), so you'd extract them to a
temp dir — `tempfile` is already imported and `_extract_ebook` shows the
TemporaryDirectory idiom (~line 432).

## Key correctness constraint — the retry path
A plain refresh skips files whose size+mtime are unchanged, so improving
`extract_text` does NOTHING to already-indexed rows. To re-process the existing
~1,213 archive rows you MUST run `just lf-refresh-retry` (or
`library-folders-refresh --retry-failed`). The gate is `_should_skip(...)` (~line
500): it skips only when size+mtime match AND `extraction_status == "ok"`. This
is the single biggest gotcha — I forgot it last thread and the live refresh
recovered 0 files. See `kamma/lessons.md` 2026-06-09 [BEHAVIOR].

## Hazards specific to archives
- **Zip bombs / huge archives.** Cap uncompressed size and member count. Use
  `ZipInfo.file_size` to budget BEFORE reading. Current ebook timeout is 180s;
  archives have no timeout because they're stdlib — a bomb would OOM/hang.
- **Member extension routing.** Reuse the existing extension sets so you don't
  re-index binary members. Skip anything in `NOISE_EXTENSIONS`.
- **Encrypted / bad zips.** `_extract_zip_members` already catches
  `zipfile.BadZipFile` → `"error: bad zip"`. Encrypted members raise
  `RuntimeError` on read — catch per-member, don't abort the whole archive.
- **Nested archives.** A zip-in-zip — decide a recursion cap (probably depth 1;
  don't recurse by default).

## Design decision still open (resolve first)
Single-row-per-archive (concatenate member text, simplest, matches epub/docx)
vs one-document-per-member (needs a synthetic rel_path like `a.zip!inner.txt`
and touches dedup/search/`_delete_missing_documents`). I lean **single-row** for
a first cut — far less schema churn, and search snippets still point at the
archive. Per-member can be a follow-up if granularity is wanted.

## Validate-first habit (worked well last thread)
Before coding, run the candidate approach against REAL corpus files and measure.
Find samples with:
```
python3 -c "import sqlite3;c=sqlite3.connect('file:/home/bodhirasa/MyFiles/2_Resources/Libraries.sqlite?mode=ro',uri=True);print('\n'.join(r[0] for r in c.execute(\"SELECT source_path FROM documents WHERE extension='.zip' LIMIT 20\")))"
```
Then open a few with `python3 -c "import zipfile; print(zipfile.ZipFile(p).namelist()[:50])"` to see what's actually inside — this corpus's zips vary wildly (ebook bundles vs software vs image dumps). That recon should drive the member-filter rules.

## Tooling already on PATH
`ebook-convert`, `pandoc`, `catdoc`, `7z` (`/usr/bin/7z`), `unzip`, `pdftotext`.
stdlib `zipfile` and `bz2` cover zip+bz2 with no deps. `.7z`/`.bz2` are only 4
files total — judge whether they're worth bespoke handling.

## Verification bundle (this project's standard)
```
uv run ruff check <changed .py>
uv run pyright <changed .py>
uv run pyrefly check --search-path . <changed .py>
uv run pytest tests/test_library_folders.py -q
```
Tests live in `tests/test_library_folders.py`; follow the existing
`tmp_path` + real-`refresh()` + `search()` style. Use `zipfile.ZipFile(...)` to
build fixtures in-test (see `test_zip_based_extractors_index_epub_docx_and_odt`).

## Pre-existing diagnostics to ignore
`weasyprint`/`youtube_transcript_api` unresolved-import warnings and a
macOS-`textutil` "unreachable" note are pre-existing and unrelated — don't chase
them.

## Don't
- Don't run git commands or commit without explicit user permission.
- Don't run the live `lf-refresh`/`lf-refresh-retry` against the real index
  yourself — the user runs those (the index is `Libraries.sqlite`, ~32k docs).
