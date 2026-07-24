---
name: digest
description: Write a plain-English essay (a 20–30 minute read) that gives a layperson the main points of a large or complex topic without reading the book/paper/field yourself — a modern Monarch Notes / CliffsNotes pamphlet for any subject. No inline footnotes; ends with a further-reading link list. Saved into the vault. Invoke when the user types /digest <topic> or asks for "a digest of X", "the CliffsNotes version of X", "a quick-study summary of X", or "get me up to speed on X in plain English".
---

# Digest

A single-session skill that turns one large topic into one short, readable
essay — the 1960s Monarch Notes / CliffsNotes recipe (plot summary, main
ideas, key points, nothing you need a library card for) applied to any
nonfiction subject instead of a novel.

This is **not** for academic use. It's a quick-study aid for a layperson who
wants the shape of a topic before deciding whether to go deeper — not a
citation-complete research note. For that, use `/vicaya` or `/vicaya-quick`
instead (see **Relationship to vicaya** below).

## What this skill does NOT do

No phase gates, no dossier, no cross-check model pass, no PDF, no
bibliography with per-claim citations, no `sync_notes`/run-report ceremony.
One session, one file, done.

## How to run

### Step 1 — Confirm the topic and check for an existing digest

**X** = the user's topic, exactly as given (or lightly clarified if genuinely
ambiguous — e.g. "quantum computing" vs "the quantum computing industry").

Slugify X (lowercase, ASCII-fold, hyphenate) and check the vault's
`Vicaya Digest` folder for an existing note on that slug (`search-vault` or
list the folder via the Obsidian CLI). If one exists, tell the user and ask
whether to redo it or leave it — never silently overwrite or duplicate.

### Step 2 — Research

Default to `WebSearch` / `WebFetch`. Read enough sources to actually
understand the topic's shape — not just the first hit's summary. Favor
sources that explain the topic itself (overviews, explainers, textbooks,
reputable long-form pieces) over primary technical papers; you're building a
map, not a literature review.

**If the topic is Pāḷi/Buddhist-related**, also draw on this repo's local
vicaya sources — the Obsidian vault, the CST canon DB, library folders — via
the helpers documented in `skill/vicaya/SKILL.md` (**Setup — paths and
tools**, **Calling the helpers**). This is topic-conditional, not the
default: most digest topics won't be Buddhist and should just use the web.
Do not run vicaya's phase-gated workflow here — call the helper functions
directly, the same way `vicaya-quick` does, and stop once you have enough to
write the essay.

There is no minimum source count and no verification pass — read enough to
write an accurate, well-shaped summary, then move on. This skill trades
citation rigor for speed and readability; if a claim later turns out to
matter enough to need a citation, that's a sign the topic wants `/vicaya`
instead.

### Step 3 — Write the essay

Plain English throughout. No jargon left unexplained, no academic hedging,
no inline footnotes or citation markers of any kind in the body — clean
prose only. Target a **20–30 minute read** (roughly **4500–6500 words** at
typical reading speed) — enough room to actually cover a complex topic's
main points, not a skimmable blog post. Flex longer if the user asks for
more depth on a specific topic, but don't pad by default; every paragraph
should be doing work.

Use exactly this structure:

1. **Title** — the topic, plain and direct. This is also the H1 heading and
   the frontmatter `topic` field.
2. **In short** — 2–3 sentences immediately under the title. A reader who
   stops here still has the gist. This is the single most important
   paragraph in the piece — write it last, after you know what actually
   matters.
3. **Background** — why this topic exists, who or what is involved, the
   minimal context a reader needs to follow the rest. A few short
   paragraphs, not a history lecture.
4. **The main ideas** — the core content, broken into headed subsections
   (`###`), one per major sub-topic. This is where most of the essay's
   length lives, and the part that replaces reading the book — cover the
   points someone would actually need to hold an informed conversation
   about the topic. Prefer concrete specifics over vague gestures; a fact
   or example beats an abstraction every time.
5. **Why it matters / common misconceptions** — brief. What people usually
   get wrong, or why this is worth knowing at all.
6. **Key takeaways** — a short bullet list, 4–6 items: "if you remember
   nothing else."
7. **Further reading** — a bulleted list of the sources actually used,
   as plain Markdown links (`[Title](url)`), for anyone who wants to go
   deeper. This is the *only* place sources appear — there is no inline
   citation elsewhere in the essay. A relevant Wikipedia article is a good
   fit here — broad, free, and exactly the kind of next stop this list is
   for — include one when a solid article on the topic exists, alongside
   the other sources actually used.

### Step 4 — Save to the vault

```bash
TODAY=$(date +%Y-%m-%d)
SLUG="<lowercase-hyphenated-topic-slug>"
obsidian vault=Obsidian create \
  path="Vicaya Digest/${TODAY} - ${SLUG}.md" \
  content="<full rendered markdown, frontmatter + essay>" \
  open
```

Same `obsidian create` gotchas as the main `vicaya` skill: pass `overwrite`
explicitly on any create after the first for this path, and never pass a
flag to `--help` (see `skill/vicaya/SKILL.md`'s note on this if unfamiliar).
If the Obsidian CLI can't connect, launch the app per that same skill's Hard
Rule 4 and retry; if it still fails, write the file directly into the vault
path on disk as a fallback and tell the user.

Frontmatter — deliberately lighter than a `vicaya` research note (no
`canon_refs`/`library_refs`/`web_refs` — those are for citation-complete
notes, not this):

```yaml
---
date: 2026-07-24
topic: "<the title, verbatim>"
tool: "https://github.com/bdhrs/vicaya"
tags:
  - digest
---
```

## Relationship to vicaya

This skill shares the vault, the Obsidian CLI conventions, and — when the
topic calls for it — the vicaya local-source helpers, but it is otherwise
independent: it does not read or resume vicaya's scratch dossiers, and a
digest is not a valid input to vicaya's `scratch-resume`/promotion path. If
the user wants a digest turned into a full cited research note, treat that
as a fresh `/vicaya` run on the same topic, not a promotion.

## When something fails

Same fallbacks as `vicaya-quick`: web search comes up thin → widen or
rephrase the query, try 2–3 different angles before concluding the topic is
under-covered; `WebSearch` 403 → fall back to `WebFetch` on a constructed
URL; Obsidian CLI unreachable → launch the app and retry, then fall back to
a direct disk write. If a path or tool is genuinely missing, say so — don't
guess.
