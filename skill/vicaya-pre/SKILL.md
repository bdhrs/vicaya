---
name: vicaya-pre
description: Search existing Obsidian vault notes to check if any already partially answer the research question before starting a full /vicaya run.
---

# Vault pre-check

Quick scan of the user's Obsidian vault for notes that already partially or fully address the research question. Run this before committing to a full `/vicaya` session.

## Input

The research question, topic, or audience/constraint description — passed as the argument after `/vicaya-pre`.

## Steps

All commands run from the vicaya repo root.

**0. Ensure Obsidian is running** — before any `search-vault` call, if Obsidian is not running the CLI will fail with "unable to find Obsidian". Launch it and wait ~5 seconds before proceeding. Use the OS-appropriate command — **never bare `obsidian`** (that resolves to the CLI, not the app, on Linux):
- **Linux:** `setsid xdg-open "obsidian://" >/dev/null 2>&1 & sleep 5`
- **macOS:** `open -a Obsidian && sleep 5`
- **Windows:** `start "" "obsidian://" && timeout /t 5`

Run this once at the start of the skill, before step 1.

**0b. Count the corpus** — before any search, count total notes under `Vicaya/` so truncation is always visible in the report:

```bash
find "$VICAYA_VAULT_PATH/Vicaya" -name "*.md" | wc -l
```

Report this count in the output as "Vicaya/ corpus: N notes".

**0c. Detect input mode** — examine the argument before searching:

- **Topic mode** (default): argument names a concept, term, or question. Proceed with Steps 1–2.
- **Survey mode**: argument describes an audience, constraint, or request without a clear searchable topic (e.g. "45-min talk for 0–3 vassa monks"). Switch to the survey path in Step 1b instead.

**1. Topic mode — run up to 3 search variations** — try the Pāḷi term, English gloss, and a related concept if the first two return nothing. Use a `--limit` equal to the corpus count (from Step 0b) or at least 50, whichever is larger.

```bash
uv run tools/research_sources.py search-vault "<term>" --folder Vicaya --limit <N>
```

If `search-vault` returns 0 results or reports `No matches found.` on a term you'd expect to find, fall back to `rg`:

```bash
rg -l "<term>" "$VICAYA_VAULT_PATH/Vicaya" --glob "*.md"
```

**1b. Survey mode — full-corpus triage** — when no clear topic exists, list every note under `Vicaya/` recursively and skim titles for audience/constraint fit. Do not run a term search. Instead:

```bash
find "$VICAYA_VAULT_PATH/Vicaya" -name "*.md" | sort
```

Read the titles and identify notes that could suit the stated audience or constraints. Select up to 10 candidates and note why each fits.

**2. Recursive Vicaya subfolder sweep (topic mode only)** — prior research notes live at `$VICAYA_VAULT_PATH/Vicaya/`, including nested subfolders. Run a recursive sweep covering every `.md` file under `Vicaya/` with no subfolder restriction. Use the same high limit as Step 1.

```bash
rg -l "<term>" "$VICAYA_VAULT_PATH/Vicaya" --glob "*.md"
```

Merge results with Step 1 findings before reporting.

**3. Report findings** using this format:

---

## Vault pre-check: `<question>`

**Vicaya/ corpus: N notes**

### Existing notes found

| Note | Snippet | Relevance |
|------|---------|-----------|
| `[[Note Title]]` | *brief excerpt* | high / partial / tangential |

*(or: **No relevant notes found.** The vault has no existing coverage on this topic.)*

*(Survey mode: list up to 10 candidate notes with a one-line reason each instead of the table above.)*

### Verdict

One of:

- **Proceed with `/vicaya`** — no meaningful prior coverage.
- **Review first** — `[[Note Title]]` partially covers this; the `/vicaya` run should build on it rather than duplicate it. Link the existing note as a seed.
- **May already be answered** — `[[Note Title]]` directly addresses this question. Consider reviewing it before starting a full research run.
- **Survey complete** — (survey mode only) no single topic to research; here are the existing notes that best fit the stated audience/constraints. No `/vicaya` run needed unless a specific gap is chosen.

### Suggested new research message

Include a copy-ready message only when new research should proceed:

```text
/vicaya <clear research question>
```

If the verdict is **Review first**, include the existing note in the message as context to build on, not as a separate command flag:

```text
/vicaya <clear research question>. Build on [[Note Title]] and avoid duplicating its existing coverage.
```

If the verdict is **Survey complete**, omit the suggested message unless the user wants to drill into a specific gap identified during triage.

---

## Rules

- Do not start a research session. This skill only reads and reports.
- Do not suggest edits to existing notes.
- Keep the output short — this is a 30-second pre-check, not a summary of the notes themselves.
- Never cap search results below the corpus count. If `--limit` is needed, set it to the corpus size or higher.
- If the question is ambiguous (e.g. speech-to-text corruption), search for the most plausible interpretation and name it in the verdict.
- Use the user's original wording for the suggested message when clear; otherwise use the plausible clarified question named in the verdict.
