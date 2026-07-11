---
description: Search existing Obsidian vault notes to check if any already partially answer the research question before starting a full /vicaya run
args:
  - name: topic
    description: The research topic
    required: true
---

Load the skill at `~/.agents/skills/vicaya-pre/SKILL.md` and execute it with the research topic `{{args}}`.
