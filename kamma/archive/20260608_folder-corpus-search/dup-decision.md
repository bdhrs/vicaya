# Duplicate-Handling Policy Decision

> Phase 5 (Pro) decision doc. Analysis only — no code was changed in this phase.
> Decides the final duplicate policy from `dup-evidence.json` and `spec.md`, and
> defines the exact deltas from the Phase 3 safe placeholder that Phase 6 (Fast)
> must implement.

## Evidence Base (and its limits)

Source: `dup-evidence.json`, a **bounded `--limit 1000`** sample of
`/Users/deva/filesrv1/share2/Textual/Non-Canonical English`. Of 1000 files,
**92 were text-extracted, 908 metadata-only**. Two extraction facts dominate the
reading of this evidence and must be held in mind:

1. `.doc` is **not extracted** by the current implementation (only `.txt/.md`,
   `.htm/.html`, `.epub`, `.docx`, `.odt`, and `.pdf`-via-`pdftotext`). The corpus
   is `.doc`-heavy.
2. `pdftotext` was **absent in the build sandbox**, so every `.pdf` in this sample
   indexed as metadata-only. On the user's real machine `pdftotext` may be present,
   which would raise PDF coverage without any code change.

Consequence: **`text_hash` coverage in this sample is artificially low.** The
single `text_hash` cluster is not evidence that text-level duplication is rare; it
is evidence that we extracted text for very little of the corpus. Do not read the
low `text_hash` count as "text dedupe doesn't matter."

## Decision Summary

| Grouping key | Evidence (sample) | Decision | False-positive risk |
|---|---|---|---|
| `content_hash` (identical bytes) | 7 clusters / 14 files | **Auto-suppress (keep)** | None |
| `text_hash` (identical normalized text) | 1 cluster / 2 files | **Auto-suppress (keep)** | None |
| `normalized_filename` | 40 clusters / 90 files | **Surface only — reject promotion** | High |
| `normalized_filename` + `size` | 1 cluster / 2 files | **Reject promotion; fold away** | Low gain, nonzero |
| `size` alone | 37 clusters / 82 files | **Drop entirely (not even a hint)** | Pure noise |

Net policy: **auto-suppression stays exactly at the Phase 3 baseline —
`content_hash` ∪ `text_hash`, transitively merged, representative =
lexicographically-first `rel_path`.** No weak signal is promoted. The weak-hint
surface is *narrowed*, not widened, and one extraction gap is closed.

## Per-tier rationale

### content_hash — auto-suppress (KEEP)
Seven clean pairs of byte-identical files under different names/locations (e.g.
`De N8P1.doc` ≡ `Knocking at the Right Door.doc`; `Mindfully Facing Disease and
Death (secured).pdf` ≡ `… Death.pdf`; `Analayo's Encyclopedia [DO NOT SHARE].pdf`
≡ `… Entries - Complete.pdf`). Identical bytes are identical content by
definition; **zero false-positive risk.** No change.

### text_hash — auto-suppress (KEEP)
One pair — `ebdha121.htm` ≡ `Dhamma without Rebirth.htm` (Bhikkhu Bodhi): same
normalized text, different bytes/filename. This is precisely the case `text_hash`
exists for (same readable content under different markup/metadata). **Zero
false-positive risk** (identical normalized text). The low count is an extraction
artifact (see above), not a reason to drop the tier. No change. Coverage will rise
once `.doc` extraction lands and `pdftotext` is present at refresh time.

### normalized_filename — surface only, REJECT promotion to auto-suppress
40 clusters / 90 files, but the signal is **contaminated**:

- **True same-work, different format** (desirable to flag): `Reading the Buddha's
  Discourses in Pāli` as `.epub/.mobi/.pdf`; `A Meditator's Life of the Buddha`
  as `.epub/.mobi`. These differ in bytes *and* text, so neither hash collapses
  them — only the filename does.
- **False positives that would destroy distinct content if suppressed:**
  - Generic/junk names: `metadata.opf` across four different books; `Picasa.ini`
    across four folders. Same name, **entirely different files.**
  - Same-title, different-author works: **`War and Peace`** as three separate
    essays by Amaro, Analayo, and Bodhi; **`Satipatthana`** spanning two different
    encyclopedia entries plus an unrelated Anandajoti `.mobi`.

Auto-suppressing on filename would silently hide genuinely distinct documents.
**Reject promotion.** Keep it as a *surfaced* `possible_duplicate_of` hint where a
human/agent judges it. It is the one filename-based signal worth surfacing.

### normalized_filename + size — REJECT promotion; fold away
Only 1 cluster (`z-inside covers.doc` ×2, size 31744) — and that pair is **already
caught by `content_hash`**. So promoting this rule would suppress **nothing new**
in the evidence, while adding nonzero risk (two genuinely different files sharing a
name and coincidentally the same byte size — plausible for templated `.doc`s).
Gain ≈ 0, risk > 0 → **reject.** It does not earn a separate surfaced signal
either; `normalized_filename` already carries the filename hint.

### size alone — DROP entirely (remove even as a hint)
37 clusters / 82 files of almost-entirely-unrelated documents. `.doc` files
collide on byte size because of Word block allocation and shared boilerplate: size
`31744` groups `z-inside covers`, `Sabbattataya in Metta meditation`, and `Peace
of Mind` — three different works. The Samyutta Nikaya `.DOC` chapters collide on
`106496`, `119296`, `137216` while being different chapters. As a suppression
rule it is unthinkable; **as a surfaced hint it is actively harmful**, because it
would attach a noisy `possible_duplicate_of` to nearly every `.doc` hit and train
the agent to ignore the hint field. **Remove `size` from the weak-signal set.**

### title — DROP (redundant)
In the current code `title` = `_normalize_title_key(filename)` and
`normalized_filename` = the same key minus copy/version tokens. For this corpus
there is no independent document-title metadata; `title` is derived from the
filename and is therefore **almost always identical to `normalized_filename`.** It
adds a duplicate signal with no independent information. **Remove `title` from the
weak-signal set.** (Revisit only if real embedded title metadata is parsed later.)

### Representative selection — KEEP lexicographically-first rel_path
Within an auto-suppressed group every member is, by construction, identical
content (`content_hash`) or identical extracted text (`text_hash`), so extraction
status and searchability are uniform across the group. Representative choice is
therefore low-stakes; the existing deterministic `min(rel_path)` is fine. **No
change.** (No tie-break on extraction status is needed because it cannot vary
within these groups.)

## Extraction gap to close — the one real lever

`non_text_extracted_duplicate_candidates` = **138 files**, dominated by:

| ext | count | action |
|---|---|---|
| `.doc` | 81 | **Close the gap** (highest value) |
| `.pdf` | 27 | No code change — `pdftotext` already wired; absent only in build sandbox |
| `.mobi` | 15 | Leave metadata-only (out of scope) |
| `.opf` | 4 | Junk/metadata — also filter from filename hints |
| `.ini` | 4 | Junk — filter from filename hints |
| `.azw3` | 2 | Leave metadata-only |
| `.htm`/`.mht`/`.xml` | 5 | Marginal; no action |

**`.doc` is 81/138 ≈ 59% of all duplicate candidates** and the corpus is
`.doc`-dominated. Because `.doc` is not extracted, `text_hash` is blind to the
majority of likely text-level duplication. **Closing the `.doc` extraction gap is
the single highest-value change** and directly improves the `text_hash`
auto-suppress tier (no weak-signal promotion required).

Recommended approach — mirror the existing optional-tool pattern of `_extract_pdf`
(check `shutil.which`, subprocess with timeout, clear status strings, graceful
metadata-only fallback). On macOS (`darwin`, this machine) `textutil -convert txt`
is **built in and always present**; `antiword`/`catdoc` are the cross-platform
fallbacks if on `PATH`. **No new Python dependency.** If none is available, `.doc`
stays metadata-only exactly as today.

`.pdf`: no code change. Note for the operator — re-run `folder-corpus-refresh` on
the real machine with `pdftotext` installed to realize PDF text/`text_hash`
coverage that the build sandbox could not.

`.mobi`/`.azw3`: leave metadata-only. Their content is usually recoverable through
sibling `.epub`/`.pdf`/`.docx` of the same work (see the
`analayo s encyclopedia entries complete` cluster), and ebook decoding is heavier
than this thread's stdlib/optional-CLI budget allows.

## Net deltas for Phase 6 (from the Phase 3 placeholder)

1. **Narrow weak signals** in `_weak_duplicate_hints` (`tools/folder_corpus.py`
   ~L624-628): remove `size` and `title`; keep only `normalized_filename`.
2. **Filter junk from filename hints**: skip generic stop-names
   (`metadata`, `picasa`, `index`, `contents`, `cover`, `title`) and
   non-document extensions (`.ini`, `.opf`) so `metadata.opf` / `Picasa.ini`
   stop generating hints.
3. **Close the `.doc` extraction gap**: add an optional `.doc` extractor
   (`textutil` on macOS, else `antiword`/`catdoc` if present) following the
   `_extract_pdf` pattern; graceful metadata-only fallback; no new dependency.
4. **No change** to: `content_hash`/`text_hash` auto-suppression, transitive
   grouping, lexicographically-first representative, `--include-duplicates`,
   `.pdf` handling.

Phase 6 must also update tests to lock in: `size`/`title` no longer appear as
hint signals; junk filenames generate no hints; `.doc` text is extracted (test
skips when no `.doc` extractor is available, mirroring the `pdftotext` skip).
