---
date: 2026-05-28
question_original: "Hiriottappa how to develop - all depth - sutta / com / modern autors"
question_polished: "How are hiri (moral shame) and ottappa (moral dread) understood and cultivated according to the Pāḷi canon, commentarial tradition, and modern teachers?"
note_path: "~/Library/Mobile Documents/iCloud~md~obsidian/Documents/Notes/Vicaya/2026-05-28 - hiri-ottappa-development.md"
slug: hiri-ottappa-development
duration_min: ~90 (across two sessions with context compaction mid-run)
canon_hits: 17
library_hits: 13 books (FTS active)
youtube_transcripts: 3 (all auto-captions)
web_sources: 4 (dhammatalks.org x3, accesstoinsight.org x1, wisdomlib.org x2)
---

## What surprised me

- **SN1.18 Hirīsuttaṃ** was not on the initial search list but emerged from web search. The *apālambo* (support/prop) framing is an important structural image alongside the SNP1.4 plough-pole — these two together give hiri a dual spatial metaphor: directional (steering pole) and supportive (prop against collapse).

- **The hirī/kukkucca distinction** was flagged by the OpenRouter cross-check as absent from the synthesis — a genuine omission. This is the most practically critical distinction for meditators: practitioners often confuse hirī (wholesome, forward-looking, preventive) with kukkucca (unwholesome remorse that dwells and agitates). The cross-check added significant value here.

- **Ṭhānissaro's ottappa-atappa resonance** is pedagogically powerful but the cross-check correctly identified it as non-standard Pāḷi philology. Standard etymology goes to *ava + tappati* (to be tormented), not atappa (ardency). Presented as interpretive reading in the note.

- **AN7.65 bidirectionality**: The liberation chain is not strictly one-way — samādhi deepens hiri-ottappa sensitivity. The cross-check caught this nuance.

- **Calibre FTS was active** (snippets returned). All 13 key library hits had substantive content. The tags-based search (--tags Hiri) failed silently; free-text worked.

- **Context compaction mid-run** erased all Phase 1-3 findings that had not yet been written to scratch. The scratch file was initialised but never populated. This required re-running all canon queries in Session 2 to reconstruct the dossier. Iron Rule violation cost approximately 30 minutes.

## Errors and repeated mistakes

- **Iron Rule violation (Phase 1-3 scratch write)**: Scratch file was created at Phase 0 but content was never written before context compaction. ALL Phase 1-3 findings had to be reconstructed from re-running queries in Session 2. This is the second time this pattern has appeared. The fix is to call `scratch-log` or Write to scratch at the *end of every individual query*, not just at the end of a phase.

- **Inline Python attempt**: Attempted `python -c "..."` heredoc to parse transcript JSON — blocked by CLAUDE.md hook. Fixed correctly by writing `temp/read_transcript.py` and using `uv run python`.

- **Heredoc for scratch creation**: In Session 1, attempted `cat > file << 'EOF'` in fish shell. Fish does not support heredoc. Should have used the `Write` tool.

- **sqlite3 path assumption**: The symlinked `data/tipitaka-translation-data.db` was empty (0B). The actual DB is at `~/Documents/dpd-db/resources/tipitaka_translation_db/tipitaka-translation-data.db` per `.env`. Always read `.env` before attempting direct DB access.

- **Column name mismatch**: Direct sqlite3 queries used `pali` and `english` column names (which the CLI helper maps internally) but actual columns are `pali_text` and `english_translation`. The CLI `search-canon` is preferred for text retrieval; raw sqlite3 needs the actual column names.

## What I'd change in the skill

- **scratch-log should be called after every query, not every phase**: The compaction risk is too high. Even a one-line stub ("Phase 2: found AN7.65 - see next log entry") would survive compaction better than nothing.

- **Initial scratch population**: The scratch-init step creates the file but leaves placeholders. A better approach would be to write the angle triage and perspective map immediately into scratch as they are derived in Phase 0 — before any queries run.

- **Cross-check adds significant value**: The hirī/kukkucca omission and the bidirectionality point were genuine additions. The cross-check should not be skipped even when confidence is high.

## What I changed this run

- Nothing in SKILL.md (no process changes implemented this run)

## Channel tuning

- Promote to trusted: none (BrianArnell / Springboard Meditation Sangha had relevant content but auto-captions; probationary maintained)
- Demote to excluded: none
- New probationary channels seen: Candana Bhikkhu (uW09u167Nqg) — substantive dhamma content, auto-captions only
- lkt4MncSrmA (U Pandita 60-day retreat) — general vipassanā instruction, hiri-ottappa not explicitly addressed in this talk; supplemented by Calibre book instead
