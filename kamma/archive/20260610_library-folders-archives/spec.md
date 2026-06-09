# Spec — Library Folders: extract text from archives

## Plain-language summary (read this first)

The library folders index can already read text out of regular files like PDFs, Word
docs, ebooks, HTML, and so on. It cannot read text *inside* `.zip`, `.bz2`, or
`.7z` archives. There are 1,267 such archives on disk (1,263 zips, 3 sevens,
1 bz2). Most are ebook bundles (zips), but the set also includes Scientific
American magazines (7z) and Python documentation (bz2-compressed tar). The
archives are spread across three library directories, and the majority are
**not** excluded from the library-folders walk — they are being walked right
now but silently skipped because `.zip` has no extractor.

This thread adds a new extractor that opens each archive, finds the text
files inside, runs the right extraction tool on each, and squashes the result
into one row in the index per archive.

**The single design choice the rest of the spec defends:** one row per
archive, not one row per file inside. A search hit on text inside a zip
surfaces the archive itself, with a snippet drawn from all the text inside
it concatenated. This means a 1,267-row growth in the index, not a
~9,300-row growth.

**Impact is immediate for 1,209 archives.** Only 58 of the 1,263 zips live
inside the excluded Calibre library (`Bodhirasa eBook Library/`). The other
1,205 zips are in `Susima/` and 12 in `Na Uyana eBook Library/`, both of
which the library-folders walk covers today. The 3 `.7z` files are in
`Na Uyana eBook Library/` (not excluded). So the archive extractor will
make 1,209 archives searchable as soon as it lands — no config changes
needed. The remaining 58 excluded zips become searchable only if you
choose to remove the Calibre exclude later.

**Things we explicitly do not do in this thread:**
- We do not change whether your nested Calibre library is excluded from the
  library-folders walk. The exclude stays as-is. The 58 archives inside that
  excluded path remain dormant until you choose to remove the exclude. That
  choice is a finalize-time decision, not a do-time one.
- We do not run OCR. A minority of PDFs inside zips are scanned paper with
  no text layer. `pdftotext` returns nothing for those. We mark them empty
  honestly. OCR is a separate, much bigger piece of work.

## Real-data probe (2026-06-09, validate-first before designing)

Walked `/home/bodhirasa/MyFiles/2_Resources/Libraries` (the library-folders
source root) with `rglob` and Python `zipfile`/`bz2` inspection.

### Archive counts and locations

| Format | Count on disk |
|---|---|
| `.zip` | 1,263 |
| `.7z` | 3 |
| `.bz2` | 1 |
| **Total** | **1,267** |

**Distribution across library directories:**

| Directory | Zips | 7z | Excluded from walk? |
|---|---|---|---|
| `Susima/` | 1,191 | 0 | No |
| `Bodhirasa eBook Library/` | 58 | 0 | Yes |
| `Na Uyana eBook Library/` | 12 | 3 | No |
| `Software/` | 2 | 0 | No |

The library-folders config excludes only
`~/MyFiles/2_Resources/Libraries/Bodhirasa eBook Library`. So 1,209 of the
1,267 archives are already being walked — they are silently skipped because
`.zip` has no extractor. The archive extractor will make them searchable
immediately, with no config changes.

### Aggregate across all 1,263 zips

- Total members: 9,289
- Total uncompressed: 1.64 GB
- Max members in one archive: 2,823 (the Sri Lankan Tipitaka, in
  `Bodhirasa eBook Library/` — excluded)
- Max uncompressed in one archive: 890 MB (`Translations Series.zip`:
  49 PDFs + 2 docx, in `Na Uyana eBook Library/` — not excluded)
- Encrypted members: 0
- Archives containing nested .zip members: 0

### Top 20 member extensions across all zips

```
.html    4,018   main text-bearing payload
(none)   1,258   mostly epub 'mimetype' (no-op)
.xml     1,248   epub spine
.opf     1,247   epub packaging
.mp3       664   audio — already in NOISE_EXTENSIONS
.jpg       256   images — already noise
.pdf       144   text-bearing — needs pdftotext
.png       116   noise
.mobi       92   ebook — needs ebook-convert via tempdir
.htm        74   text-bearing
.css        60   mostly noise
.js         38   noise
.php        20   noise
.gif        14   noise
.doc        13   text-bearing — needs catdoc
.webp        6   noise
.txt         4   text-bearing
.rtf         4   text-bearing — needs ebook-convert
.json        2   text-bearing
.jpg-old     2   noise
```

The 144 PDFs and 13 .doc files inside zips are the surprise. If the new
extractor only handled text/html, it would miss `Translations Series.zip`
entirely (the worst-case archive, with 49 PDFs).

### Size-stratified samples (5)

| Size bucket | Archive | Members | Uncomp | Encrypted | Nested zip | Text-bearing? |
|---|---|---|---|---|---|---|
| 1,587 B (min) | It's Like This — Ajahn Chah | 4 | 1,760 | 0 | 0 | html |
| 7,786 B (Q1) | Vipassana Meditation Course 7 — U Janaka | 4 | 22,319 | 0 | 0 | html |
| 35,802 B (median) | What is Right Effort — Bhikkhu Samahita | 4 | 35,802 | 0 | 0 | html |
| 25,359 B (Q3) | Advice for meditation — Kor Khao-Suan-Luang | 4 | 77,554 | 0 | 0 | html |
| 890 MB (max) | Translations Series | 51 | 890 MB | 0 | 0 | 49 PDF + 2 docx |

The vast majority of zips are small (median ~36 KB) ebook bundles (Calibre
epub-style: `mimetype`, `META-INF/container.xml`, `content.opf`, one
`.html`). The big outliers are: the Sri Lankan Tipitaka (2,823 HTML
members, 96 MB uncompressed) and `Translations Series.zip` (49 PDFs, 890 MB
uncompressed, the worst case for `_extract_pdf` time).

### PDF text-layer reality (real-data check)

Sampled 15 PDFs from across the corpus (not just the worst-case archive)
by running `pdftotext -layout` on the raw decompressed bytes:

- **11 of 15** had a text layer (73%)
- **4 of 15** were scanned images (0 words extracted)

Estimated across all 144 PDF members: ~105 text-bearing, ~39 empty. The
worst-case archive (`Translations Series.zip`) is the outlier — its PDFs
are mostly scanned PTS publications. Other archives (e.g. Pa Auk meditation
manuals, JPTS journal issues) have much better text-layer coverage. We do
not add OCR (tesseract etc.) in this thread; that would be a separate, much
bigger piece of work.

### BZ2 inner format (real-data check)

The single `.bz2` file (`Python Docs - Python Documentation Authors.bz2`,
8.0 MB compressed) decompresses to a **tar archive** containing 1,070
files — Python 3.12.4 HTML documentation. The extractor must handle
bz2 → tar → HTML routing, not bz2 → single text file.

### 7z inner format (real-data check)

All three `.7z` files are in `Na Uyana eBook Library/` (not excluded):

| Archive | Contents | Text-bearing? |
|---|---|---|
| `Scientific American.7z` (48 MB) | 4 `.idx` index files | No — index data, not prose |
| `SciAm 2007-02 (damaged).7z` (5 MB) | 1 `.pdf` | Depends on PDF text layer |
| `SciAm 2005-11 (damaged).7z` (8 MB) | 1 `.pdf` | Depends on PDF text layer |

The `7z` CLI is available on PATH (`/usr/bin/7z`). `7z l -slt` produces
parseable output with per-member paths and sizes.

## Recommendation (what this thread does)

Build the new archive extractor with these specific decisions:

1. **One row per archive** in the index, with the text from all the files
   inside concatenated. A search hit on text inside an archive shows the
   archive itself as the source.

2. **Hard caps per archive:** at most 5,000 files inside, at most 2 GB of
   text uncompressed, and a hard 5-minute (300 s) wall-clock timeout. An
   archive that exceeds any cap is aborted with a structured status
   (`"error: archive too large"` or `"error: archive timed out"`) and the
   partial text-so-far is discarded.

3. **No recursion.** If a member of a zip is itself a zip, we skip it.
   Data shows zero nested zips in the corpus.

4. **Filter binary noise via the existing `NOISE_EXTENSIONS` set.**
   This skips mp3, jpg, png, css, js, gif, php, and the rest of the
   noise set at the member level.

5. **Member routing by extension:**
   - html, htm, xhtml, xht, shtml, xml, opf, txt, md, json, jsonl, py,
     css → existing helper that strips tags
   - mht, mhtml → existing mhtml extractor
   - pdf → `pdftotext` (already on PATH)
   - doc → `catdoc` (already on PATH; antiword is not installed but
     catdoc is, and the existing code falls through to it)
   - docx, odt, pptx → existing zip-based dispatchers (already in the
     codebase)
   - epub → existing zip-based dispatcher
   - mobi, azw3, azw, prc, lit, pdb, chm, rtf → `ebook-convert` via a
     tempdir (already on PATH)
   - unknown → skip, not error

6. **`.bz2` and `.7z` support, yes to both.** `.bz2` covers one file
   (Python Docs, 8.0 MB compressed) using stdlib `bz2`, then decompresses
   to a tar of 1,070 HTML files. `.7z` covers three files (Scientific
   American magazines) using the `7z` CLI guarded by `shutil.which("7z")`.
   Total fixed cost is small.

7. **No OCR.** Scanned PDFs will be marked empty.

8. **Leave the Calibre exclude alone.** The new code lands and the tests
   pass. The 58 excluded archives remain dormant. The 1,209 non-excluded
   archives become searchable immediately — no config changes needed.

## Why this is the right shape (defending the decisions)

- **Why one row per archive and not per member?** The probe found 9,289
  members across 1,263 zips. Per-member rows would inflate the index by
  that factor for no FTS gain — the search would still return snippets
  drawn from the concatenated text. Single-row also keeps the existing
  dedup and `_delete_missing_documents` contract intact.

- **Why these specific caps?** Worst observed is 2,823 members and 890 MB
  uncompressed, with zero encryption and zero nesting. 5,000 / 2 GB /
  300 s sit at roughly 1.7× and 2.2× above the observed maxima. Generous
  enough to never trigger on real data, tight enough to bound the worst
  case.

- **Why no recursion?** Zero nested zips in the corpus. If you ever do
  get a zip-in-a-zip, you'll see it in a status of `"unsupported"` and
  can decide then.

- **Why not OCR?** Out of scope, much bigger piece of work. The probe
  shows it's a real limitation but a known and honest one.

- **Why leave the Calibre exclude alone?** The 1,209 non-excluded archives
  become searchable as soon as the code lands — no config changes needed.
  The 58 excluded archives are a separate decision. The 2-do step of the
  kamma workflow is for code and tests, not for config changes.

## Constraints (inherited)

- No new hard dependencies; stdlib `zipfile` / `bz2` cover zip and bz2,
  the `7z` CLI is guarded with `shutil.which`.
- Refresh must stay incremental; reuse the `retry_failed` path so existing
  archive rows get re-extracted via `just lf-refresh-retry`.
- Indexes live outside the repo; search must not walk the source tree.
- This thread does not modify the Calibre-exclude path. The 58 excluded
  archives remain dormant. If you want library-folders to also index inside
  the nested Calibre library, that's a separate config change.

## Done when

- Text inside `.zip` archives is searchable via `search-library-folders`,
  with snippets drawn from the concatenated text.
- `.bz2` and `.7z` are also searchable, where applicable.
- Binary noise is filtered at the member level; size / member / time
  caps bound the worst cases.
- Unit tests cover the new path.
- ruff / pyright / pyrefly / pytest all green.
- `kamma/tech.md` and `README.md` updated to mention archive support.
- After merge, you can run `just lf-refresh-retry` to re-process the
  1,209 non-excluded archive rows. (You run this, not me. The handoff's
  "Don't" list is explicit about it.)
