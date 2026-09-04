# Scope audit: T1 re-verification of `swap_scope.md`

Independent audit of `kamma/threads/20260903_ocr_bakeoff/swap_scope.md` against the working tree on 2026-09-04, by reading and `rg --hidden`, not by trusting the note. `tools/library_folders.py` is dirty in the working tree; every line number below is the working-tree line.

Verdict: the symbol table is **exact** — all 14 symbols sit at the stated lines. The sweep for *readers* is not complete: it misses an entire architecture document, three status strings, two `SKILL.md` lines, and the degradation mechanism it claims to be keeping. Four findings are blocking.

---

## BLOCKING 1 — `pikepdf` is not importable in the project venv, and the plan adds no dependency

`swap_scope.md:37` says pikepdf is "already present as an ocrmypdf dependency". That is true of the **apt** package and false of the environment the code runs in.

- `/home/bodhirasa/MyFiles/3_Active/vicaya/.venv/pyvenv.cfg` → `include-system-site-packages = false`
- `python3 -c "import pikepdf"` → `system pikepdf 8.7.1`
- `.venv/bin/python -c "import pikepdf"` → `ModuleNotFoundError: No module named 'pikepdf'`

`pyproject.toml:6-15` lists no pikepdf, and `swap_scope.md:30-36` / `plan.md:30` (T4) only *remove* dependencies. So the T6 pre-decrypt step — the fix for 43 of 1,735 books — cannot import its own library after `uv sync`.

**Fix:** add `pikepdf` to `pyproject.toml` `[project] dependencies` in the same change that removes `pdf-inspector` and `onnxruntime`, and re-run `uv sync`. Do not rely on the apt copy; the venv cannot see it.

---

## BLOCKING 2 — the planned invocation has no timeout, and the note contradicts itself on the backstop

`swap_scope.md:26` puts `OCR_SUBPROCESS_TIMEOUT` in the **delete** table while its own comment says "a whole-book backstop is still wanted, see §5" — and §5 (`swap_scope.md:52-60`) never mentions it. `plan.md:29` (T3) then instructs deletion of "the four timeout constants", and `plan.md:28` (T2) specifies the replacement as `--jobs 4 --sidecar <tmp> --output-type pdf` with no timeout at all.

Executed literally, that replaces a subprocess with three layered bounds (`tools/library_folders.py:696`, `700`) with an unbounded one. The whole reason the machinery exists is `tools/library_folders.py:726-731` — an unkillable wait. A2 (`spec.md:68`) explicitly concedes ocrmypdf's zero-stall record covers only 1.3 % of the population.

**Fix:** keep a whole-book bound — rename it or keep `OCR_SUBPROCESS_TIMEOUT = 1800` — and pass it as `subprocess.run(..., timeout=...)` with `kill()` on `TimeoutExpired`. Resolve the note's own contradiction in the deviation log before T3 runs.

---

## BLOCKING 3 — the kill switch is *not* the graceful-degradation mechanism, and the test that proves degradation is not in the carry-forward list

`swap_scope.md:37` and `spec.md:75` both say a missing binary "must degrade gracefully via the existing kill switch". It cannot. `OCR_KILL_SWITCH_ENV` is an explicit user opt-out:

- `tools/library_folders.py:566` — `if os.environ.get(OCR_KILL_SWITCH_ENV) == "0": return None`

The thing that actually handles an absent engine is the availability probe immediately after, which the swap deletes with `pdf-inspector`:

- `tools/library_folders.py:568-571` — `try: import pdf_inspector ... except ImportError: return None`

Returning `None` there is what makes `tools/library_folders.py:404` keep pdftotext's own status instead of writing an OCR error over every scanned PDF in the library. `swap_scope.md:62-66` (§6) names only the hung-subprocess test and the two §3 behaviours as must-carry — it omits the test that covers exactly this:

- `tests/test_library_folders.py:1339` — `test_pdf_ocr_fallback_keeps_original_status_without_pdf_inspector`

**Fix:** replace the import probe with a binary probe, mirroring the sibling pattern already in the file at `tools/library_folders.py:408` (`shutil.which("pdftotext") is None`) — `if shutil.which("ocrmypdf") is None: return None`, returning `None` not an `unsupported:` status. Add it to §6's carry-forward list and rewrite test 1339 against a missing binary.

---

## BLOCKING 4 — `kamma/tech.md` is a status-and-architecture carrier that `swap_scope.md` never mentions

§5 (`swap_scope.md:52-60`) enumerates `SKILL.md`, `README.md` and the `justfile` as the cross-file contract. It misses `kamma/tech.md`, which is the largest carrier in the repo — and `extraction_succeeded`'s own docstring names it:

- `tools/library_folders.py:486` — "relied on by `_should_skip`, the two just recipes, README.md, **kamma/tech.md** and skill/vicaya/SKILL.md"

What is in `kamma/tech.md` and goes stale:

| Lines | Content |
|---|---|
| 13 | project summary: "a fallback runs pdf-inspector selective OCR in a timeout-bounded subprocess over the first 1,000 pages" |
| 22-37 | `## PDF OCR fallback` — names `_OCR_WORKER_SNIPPET`, `_ocr_worker_chunks`, `_collect_ocr_chunks`, `OCR_SUBPROCESS_TIMEOUT`, `OCR_PAGE_CAP` |
| 39-45 | the `ok: ocr truncated at 1000 of 1678 pages` status and its `--retry-failed` semantics |
| 47-50 | `_OCR_REPLY_MARKER` and why framing exists |
| 52-67 | `OCR_CHUNK_TIMEOUT`, `partial: ocr stalled at page N of M`, the 2-of-12 stall measurement |
| 69-71 | the reader-thread rationale |
| 73-89 | the whole cap-pricing table (150/500/1000) |
| 91-98 | `OCR_FIRST_CHUNK_TIMEOUT` and the cold-start caveat |
| 110-120 | **Install:** "`uv sync` — OCR deps are main dependencies; nothing extra needed", the PDFium download steps, `PDFIUM_LIB_PATH`, `ORT_DYLIB_PATH`, the model download |
| 122-129 | a **Verify it works** snippet that sources `.env` and calls `lf._extract_pdf` |

Line 111 is the one that hurts: it is the project's install instruction and becomes actively wrong the moment OCR depends on an apt package `uv sync` will not install.

**Fix:** add `kamma/tech.md` to §5's carrier list and rewrite lines 13, 22-98 and 110-129 in the same commit. The install section needs a new step for `apt install ocrmypdf` plus a stated check for the binary.

---

## SERIOUS 5 — the `partial:` half of the vocabulary cannot survive ocrmypdf, and §5 does not notice

§5 and `plan.md:31` (T5) worry only about `ok: ocr truncated …` disappearing with the page cap. The bigger loss is `partial:`. The incumbent can emit it because the worker streams text per 10-page chunk (`tools/library_folders.py:472-479`), so a stall leaves real text behind (`tools/library_folders.py:614-628`). ocrmypdf writes its sidecar once, at the end — a killed or hung run leaves **no text**, so there is nothing for a `partial:` status to describe.

That silently invalidates every reader of the `partial:` branch:

- `skill/vicaya/SKILL.md:1520` — "`partial: …` — some text is indexed and the book is queued for another attempt"
- `skill/vicaya/SKILL.md:1504` — "A `partial:` status also has usable text — just less of it"
- `kamma/tech.md:56-60` — the deliberate not-`ok…` retry design
- `justfile:11, 34-38` — pass 3 of 3 exists solely to recover intermittent stalls
- `tools/library_folders.py:491-492` — the `extraction_succeeded` docstring's own definition of `partial:`
- the live index already holds **23 `partial:` rows** (read-only query against `VICAYA_LIBRARY_FOLDERS_INDEX`, `.env:8`)

**Fix:** make the vocabulary change an explicit T5 decision alongside the page cap. Either drop `partial:` and update all five carriers plus `extraction_succeeded`'s docstring, or define what `partial:` now means under ocrmypdf. Do not leave the SKILL telling the agent a status the code can no longer emit.

---

## SERIOUS 6 — deleting `OCR_PAGE_CAP` breaks the whole test module at collection, not just the OCR tests

- `tests/test_library_folders.py:1190` — `_OVER_CAP = library_folders.OCR_PAGE_CAP * 2 + 78`

That is module scope. Remove the constant and the import raises `AttributeError`, so **every** test in the file fails to collect — not the ~29 OCR tests, all of them. The spec's gate "452 passed, 1 skipped or better" (`spec.md:62`) would read as a total collapse and hide whatever else broke.

**Fix:** delete line 1190 and its dependents in the same edit as the constant. Sequence T3 so the constant and its module-level reader go together.

---

## SERIOUS 7 — the real-hung-subprocess test needs a seam that the plan does not create, and half of its assertion is unachievable

The test to preserve is at `tests/test_library_folders.py:1955-1985`, `test_real_hanging_worker_is_killed_and_partial_text_kept`. It works only because the child's *source* is a monkeypatchable module constant:

- `tests/test_library_folders.py:1973` — `monkeypatch.setattr(library_folders, "_OCR_WORKER_SNIPPET", hang_snippet)`

An `ocrmypdf` call has no such seam unless one is built. `plan.md:28` (T2) specifies the flags but no module-level binary name, so there is nothing to substitute a hanging stub for, and `plan.md:37` (T8) asserts the equivalent test as if it were free.

Assessment of achievability, split:

- **The bounded-recovery half is achievable** — expose the executable as a module constant (e.g. `OCRMYPDF_BIN = "ocrmypdf"`) or a `_ocrmypdf_command()` helper, point it at a stub script that sleeps past the timeout, and assert `elapsed < 30` exactly as line 1985 does. This is the half that matters, and it requires a deliberate design choice in T2, not T8.
- **The "partial text kept" half is not achievable** — per SERIOUS 5, a hung ocrmypdf produces no sidecar. Lines 1982-1983 (`status == "partial: ocr stalled at page 10 of 150"`, `text == "first ten"`) have no equivalent. The honest replacement asserts a bounded kill and a retryable non-`ok` status with empty text.

**Fix:** add the seam to T2's acceptance criteria. Restate T8's target as "bounded kill and retryable status", and record in Deviations that partial-text retention is a capability the swap gives up.

---

## SERIOUS 8 — four emitted OCR statuses are absent from §5's contract

§5 and the thread brief list `ok`, `ok: ocr truncated …`, `partial: ocr stalled …`, `empty`, `unsupported:`, `error:`. The code emits four more specific strings, two of which are pinned by tests:

- `tools/library_folders.py:621-623` — `partial: ocr worker died at page {N} of {M}` (pinned at `tests/test_library_folders.py:1894` and `1922`)
- `tools/library_folders.py:633-635` — `error: pdf ocr stalled before any pages (no chunk in {N}s)` (pinned at `tests/test_library_folders.py:1569`)
- `tools/library_folders.py:639` — `error: pdf ocr worker returned junk: {…}`
- `tools/library_folders.py:589` — `error: pdf ocr subprocess: {exc}`

All four contain the substring `ocr`, which is load-bearing: `skill/vicaya/SKILL.md:1504` and `1521` both instruct the agent on "a scanned PDF whose status mentions `ocr`". Any replacement status must keep that substring or those two passages send the agent to the `pdftotext` dead end they were written to prevent.

**Fix:** enumerate all seven OCR statuses in the deletion note, and make "the new status text contains `ocr`" an explicit acceptance criterion in T2/T7.

---

## MINOR 9 — two `SKILL.md` carriers unnamed, and one stale claim elsewhere

§5 names `skill/vicaya/SKILL.md:1504, 1519, 1521`. All three verified correct. Two more lines in the same block are carriers:

- `skill/vicaya/SKILL.md:1517` — "Read `extraction_status` by prefix, not by equality" (the block header)
- `skill/vicaya/SKILL.md:1520` — the `partial: …` bullet (see SERIOUS 5)

Separately, and outside the OCR block:

- `skill/vicaya/SKILL.md:2491` — "No other PDF extraction tool is reliably available on this system." Once ocrmypdf and tesseract are the sanctioned path (`/usr/bin/ocrmypdf` 15.2.0, tesseract 5.3.4 both confirmed installed), this misinforms the agent about a scanned PDF fetched from the web.
- `skill/vicaya/SKILL.md:2469` — same, for known book files.

**Fix:** widen the carrier list to 1504, 1517, 1519-1521, and decide whether 2469/2491 should now offer ocrmypdf.

---

## MINOR 10 — two imports go unused and will block the pre-commit hook

After the deletion:

- `tools/library_folders.py:10` — `import queue`; its only uses are `678` and `705`, both inside `_collect_ocr_chunks`
- `tools/library_folders.py:25` — `from collections.abc import Iterator`; its only use is `442`, the deleted generator's return type

`threading` (line 18) survives — `1671` uses it in `_exists_probe`. `json`, `tempfile`, `subprocess` all survive.

`.pre-commit-config.yaml` runs `uv run ruff check --fix` and `uv run pyright` on every commit, so these are F401 failures at commit time, and the project rule is to leave touched files clean.

**Fix:** drop both imports in T3.

---

## MINOR 11 — the `.env` claim is imprecise, and `.env.example` is clean

`swap_scope.md:34` says of `PDFIUM_LIB_PATH` that "the only consumer is `tools/library_folders.py`". No code in this repo reads it — `tools/library_folders.py:547` only *mentions* it in a docstring; the real consumer is `pdf-inspector` reading the env var after `_load_dotenv`. Verified carriers: `.env:20` and `kamma/tech.md:112-116`. `.env.example` does **not** contain the key, so nothing is needed there.

The instruction not to edit `.env` is correct and matches the global rule. Just report the key as unused and cover `kamma/tech.md:112-116` in the same change.

---

## MINOR 12 — two arithmetic slips in the notes

- `swap_scope.md:9` — "Roughly lines 42–60 and 430–742, ~230 lines". The range 430-742 is 313 lines; excluding the surviving `extraction_succeeded` (482-495) leaves ~299. The estimate understates by a third.
- `plan.md:29` (T3) — "the four timeout constants". There are three timeouts (`OCR_CHUNK_TIMEOUT`, `OCR_FIRST_CHUNK_TIMEOUT`, `OCR_SUBPROCESS_TIMEOUT`) plus `OCR_CHUNK_PAGES` (a page count) and `OCR_PAGE_CAP` (deferred to T5). `swap_scope.md:64`'s "all five timeout/cap constants" is the accurate phrasing.

---

## MINOR 13 — no stranded-row migration needed today, but say so explicitly

If the page cap is removed, rows already recorded `ok: ocr truncated …` would be skipped forever by `_should_skip` (`tools/library_folders.py:1171` via `extraction_succeeded`), because `ok…` counts as done. Measured against the live index (read-only, `.env:8`): **0 rows** match `ok: ocr truncated%`, 23 match `partial:%`, 44,658 are `ok`, 1,474 `empty`. So the hazard is currently nil — the OCR pass never reached the cap.

**Fix:** record that count in Deviations so the next reader knows the migration was checked, not assumed. If the cap is kept and later raised, `SCHEMA_VERSION` (`tools/library_folders.py:61`, honoured at `202-223`) is the lever that forces a rebuild.

---

## Test impact — the exact list

Module-level breakage: `tests/test_library_folders.py:1190` (see SERIOUS 6).

Helpers that go with the code: `_drain_ocr_worker` (1193), `_FakeWorkerStdout` (1383), `_FakePopen` (1410), `_ocr_stream`/`_meta`/`_chunk` (~1467-1481), `_fake_worker`.

Tests that die outright — 29 functions, 30 items:

| Lines | Tests |
|---|---|
| 1227, 1250, 1259, 1275, 1304, 1322 | worker-generator tests, via `_drain_ocr_worker` |
| 1339 | missing-engine degradation — **must be carried forward**, see BLOCKING 3 |
| 1484 | escalation from every non-`ok` status (parametrized ×2) — behaviour worth preserving |
| 1503, 1520, 1537, 1560, 1573, 1589, 1605, 1622, 1636, 1651, 1664, 1679 | framed-protocol / stall / crash / noise / junk / snippet tests |
| 1689, 1700 | `_ort_dylib_path` |
| 1706 | `--retry-failed` leaves an `ok: ocr truncated` row alone — the `_should_skip` contract; preserve against whatever status survives |
| 1904 | `_ocr_status` will not claim `ok` without a page count |
| 1909 | crashed worker labelled `died` not `stalled` |
| 1927 | first chunk gets a longer deadline |
| 1943 | worker pipe is closed |
| 1955 | **the real-hung-subprocess regression** — see SERIOUS 7 |

Passes but is silently weakened: `1351` `test_pdf_ocr_fallback_kill_switch`. Its `boom` guard is installed as a `pdf_inspector` stub (1355-1356), which becomes inert. Rewrite it to `boom` on the new invocation seam so it still proves the switch prevents the call.

Passes and stays valid, but with stale fixture strings: `1846` (fixture `partial: ocr stalled at page 20 of 150`), `1888-1900` (`extraction_succeeded` parametrization, including `partial: ocr worker died at page 20 of 150`). Update the strings when the vocabulary is decided in T5.

---

## What `swap_scope.md` got right

Stated plainly, because most of it is right and was clearly checked:

- **All 14 symbols are at the exact stated lines.** `_ort_dylib_path` 430, `_ocr_worker_chunks` 442, `_ocr_status` 498, `_OCR_REPLY_MARKER` 521, `_OCR_WORKER_SNIPPET` 522, `_parse_ocr_worker_reply` 531, `_extract_pdf_ocr_fallback` 543, `_OcrOutcome` 648 (its `@dataclass` on 647), `_collect_ocr_chunks` 658, `OCR_PAGE_CAP` 51, `OCR_CHUNK_PAGES` 52, `OCR_CHUNK_TIMEOUT` 53, `OCR_FIRST_CHUNK_TIMEOUT` 58, `OCR_SUBPROCESS_TIMEOUT` 59. Nothing moved, nothing missing, nothing misnamed.
- **`OCR_KILL_SWITCH_ENV` at 45 and `extraction_succeeded` at 482 — both correct, and both genuinely engine-independent.** `extraction_succeeded` is pure string-prefix logic (495) with one production caller (`1171`); the kill switch is one `os.environ.get` (566). Keeping them is right. The only caveat is that `extraction_succeeded`'s *docstring* (486-493) names `OCR_PAGE_CAP` and `kamma/tech.md`, so it needs a docstring edit even though its body does not change.
- **`justfile:9-11, 26, 30-46` — verified.** Lines 9-11 are the three-pass header, 26 the recipe comment, 30-38 the three passes with the intermittent-stall rationale at 34-36, 42-48 the two recipe doc-comments. The observation that pass 3 loses its rationale under ocrmypdf is correct and is a real simplification.
- **`README.md:187-194` — verified** (the paragraph actually runs to 195). It documents the fallback, the 1,000-page cap, the `ok: ocr truncated at 1000 of 1678 pages` status and `VICAYA_LIBRARY_FOLDERS_OCR=0`.
- **`skill/vicaya/SKILL.md:1504, 1519, 1521` — all three verified**, and the reasoning about the `pdftotext` dead end is exactly right.
- **`pyproject.toml:8-9` — verified.** `pdf-inspector>=1.17,<2` and `onnxruntime` are the only declarations, and no file outside `tools/library_folders.py` and `tests/test_library_folders.py` imports either. `ORT_DYLIB_PATH` likewise appears nowhere else in the repo.
- **The two mandatory behaviours (§3) are the right two**, and the warning at §5 that the status vocabulary is the trap is correct — it is just under-scoped, per BLOCKING 4 and SERIOUS 5 and 8.
- **`ocrmypdf` 15.2.0 and tesseract 5.3.4 are installed** at `/usr/bin/ocrmypdf`, as §2 claims.
