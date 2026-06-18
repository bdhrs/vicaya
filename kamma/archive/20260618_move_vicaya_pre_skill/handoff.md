# Manual Cleanup Instructions

The old `vicaya-pre` skill lives at `~/.agents/skills/vicaya-pre/` as a **real directory** (not a symlink) — `~/.claude/skills/vicaya-pre` and `~/.gemini/skills/vicaya-pre` are symlinks pointing at it. Remove the real directory and the two symlinks first, then re-create all three as direct symlinks to the repo (matching how `vicaya`/`vicaya-improve` are set up). Open a fresh agent session afterward — skill discovery happens at session start.

```bash
rm ~/.claude/skills/vicaya-pre
rm ~/.gemini/skills/vicaya-pre
rm -rf ~/.agents/skills/vicaya-pre
ln -sf "/Users/deva/Documents/dps/vicaya/skill/vicaya-pre" ~/.agents/skills/vicaya-pre
ln -sf "/Users/deva/Documents/dps/vicaya/skill/vicaya-pre" ~/.gemini/skills/vicaya-pre
ln -sf "/Users/deva/Documents/dps/vicaya/skill/vicaya-pre" ~/.claude/skills/vicaya-pre
ls -la ~/.agents/skills/vicaya-pre ~/.gemini/skills/vicaya-pre ~/.claude/skills/vicaya-pre
```
