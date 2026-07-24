# Plan — digest-skill

## Tasks

### Phase 1 — Write the skill

- [x] 1.1 Create `skill/digest/SKILL.md` with frontmatter (`name: digest`,
      `description:` covering the `/digest <topic>` trigger phrasing), modeled
      structurally on `skill/vicaya-quick/SKILL.md` (single-session, no
      phase gates) and `skill/what-the-suttas-say/SKILL.md` (fixed output
      format, dedup check before writing).
- [x] 1.2 Define the essay skeleton in the skill file exactly per spec.md
      (In short / Background / Main ideas / Why it matters / Key takeaways /
      Further reading), ~1200 words, plain English, no inline footnotes.
- [x] 1.3 Define the research procedure: default to `WebSearch`/`WebFetch`;
      conditionally reuse `tools/research_sources.py` vicaya helpers when the
      topic is Pāḷi/Buddhist (point to the relevant `vicaya/SKILL.md`
      sections rather than duplicating helper docs, same pattern as
      `vicaya-quick`).
- [x] 1.4 Define output path/frontmatter:
      `<vault>/Vicaya Digest/${TODAY} - <topic-slug>.md`, and the
      pre-write duplicate-topic check against that folder.

### Phase 2 — Wire into project docs and cross-agent sync

- [x] 2.1 `kamma/tech.md` — add `skill/digest/SKILL.md` to the
      "Documentation Ownership" list with a one-line description.
- [x] 2.2 `config/opencode/commands/digest.md` — OpenCode command stub
      (mirror `vicaya-quick.md`'s frontmatter shape, `topic` arg).
- [x] 2.3 `config/pi/prompts/digest.md` — Pi prompt stub (mirror
      `vicaya-quick.md`'s frontmatter + `$ARGUMENTS` body).
- [x] 2.4 `README.md` — added `digest` to the OpenCode skill loop, the
      OpenCode command loop, the Antigravity loop, the Claude Code loop, the
      autonomous-agent-setup symlink + verification blocks, and a
      `/digest <topic>` summary line near the top.

### Phase 3 — Validation

- [x] 3.1 Read the finished `skill/digest/SKILL.md` back end-to-end and
      confirm it's self-contained enough for a fresh agent to run it (no
      missing tool references, no contradiction with the spec).
- [x] 3.2 Confirmed `skill/digest/` is picked up by the `just sync` loop
      (simulated the discovery condition — `digest` appears alongside the
      other skills) and both `config/pi/prompts/digest.md` and
      `config/opencode/commands/digest.md` stub files exist on disk.
