# Spec — digest-skill

## Problem

The user wants a quick way to get up to speed on a large, complex topic without
reading a whole book or paper — the modern equivalent of a 1960s Monarch Notes
pamphlet (the "cheat on the reading" study-guide series, along with its rival
CliffsNotes). No skill in this repo produces that: `vicaya` and its siblings
are built for Pāḷi/Buddhist research and end in a citation-heavy vault note;
this is a general-purpose, any-topic, plain-language explainer.

## Solution

Add a new skill, `skill/digest/SKILL.md`, invoked as `/digest <topic>`.

### What it produces

One Markdown file, ~1200 words, written in plain English for a layperson —
not for academic use. Modeled on the Monarch Notes / CliffsNotes recipe
(summary, background, main ideas broken into digestible sections, key
takeaways) adapted for a general non-fiction topic instead of a novel.

Structure of the essay itself:

1. **Title** — the topic, plain and direct.
2. **In short** — 2–3 sentence plain-language summary up top; a reader who
   stops here still has the gist.
3. **Background** — why this topic exists / matters, who's involved, minimal
   context needed to follow the rest.
4. **The main ideas** — the core content, broken into a few headed
   subsections (this is the part that replaces "reading the book").
5. **Why it matters / common misconceptions** — brief, grounded.
6. **Key takeaways** — short bullet list, the "if you remember nothing else"
   list.
7. **Further reading** — a list of links at the end for anyone who wants to
   go deeper.

No inline footnotes or citation markers in the body — clean, readable prose
throughout, sourced only from the end-of-essay link list. (This resolves the
contradiction in the original request between "not footnoted" and "with
footnotes": confirmed with the user — no inline markers, links list only.)

### Research

Primarily web research (`WebSearch` / `WebFetch`, already available in this
repo's toolset — no new dependency). When the topic is Pāḷi/Buddhist, the
skill may also draw on `vicaya`'s local sources (vault, canon DB, library
folders) via the existing `tools/research_sources.py` helpers, exactly as
`vicaya-quick` does — but this is topic-conditional, not the default path,
since most digest topics won't be Buddhist-related.

No formal phase gates, no cross-check pass, no PDF generation, no dossier —
this is a lighter-weight, single-session skill in the spirit of
`vicaya-quick`, not the full `vicaya` ceremony.

### Output location

Saved into the Obsidian vault, in a new dedicated folder — one file per
topic, not one subfolder per topic (subfolders were floated in the original
ask but the user's actual answer was a flat dated-filename convention
matching the rest of the vault):

```
<vault>/Vicaya Digest/${TODAY} - <topic-slug>.md
```

Frontmatter: date, topic, tags — matching the style of other vault notes in
this repo (see `skill/vicaya/SKILL.md` note-shell conventions) but without
the citation-tracking fields (`canon_refs`, `library_refs`, `web_refs`) that
don't apply here.

Before writing, check the `Vicaya Digest` folder for an existing note on the
same topic-slug; if one exists, tell the user and ask whether to redo or
skip rather than silently duplicating (same pattern as
`what-the-suttas-say`).

### Naming

Skill name: `digest`. Command: `/digest <topic>`.

## Scope

- New file: `skill/digest/SKILL.md`
- `kamma/tech.md` — add `skill/digest/SKILL.md` to Documentation Ownership
- Sync `digest` the same way every other standalone, user-facing vicaya
  skill (e.g. `vicaya-quick`) is synced across agents (confirmed with user):
  - `config/opencode/commands/digest.md` — OpenCode slash-command stub
  - `config/pi/prompts/digest.md` — Pi prompt stub (`$ARGUMENTS` forwarding;
    required because it takes a `<topic>` argument, same as `vicaya-quick`)
  - `README.md` — add `digest` to the OpenCode skill loop, the OpenCode
    command loop, the Antigravity loop, and the Claude Code loop in the
    Setup section; add a one-line bullet describing `/digest <topic>`
    alongside the existing three-command list
  - `just sync` already auto-discovers `skill/digest/` — no justfile change
    needed, it just needs the stub file above to exist

## Out of scope

- No new Python tooling — this skill is pure Markdown/agent-procedure, same
  as `align` and `what-the-suttas-say`.
- No academic citation machinery, no PDF export, no cross-check model call.
- No automatic Buddhist-topic detection logic beyond "use vicaya's local
  sources when they're obviously relevant" — left to agent judgment, not a
  hard rule.
- `README.md` — not touched. `what-the-suttas-say` (a comparable standalone
  skill layered on this repo) has no README entry either; `just sync`
  auto-discovers every folder under `skill/`, so no manual list needs
  updating for the skill to work.
