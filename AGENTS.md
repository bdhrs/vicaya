# Agent guidance — vicaya

Project-specific rules for any agent working in this repository. These
complement the global rules and the canonical `/vicaya` workflow in
`skill/vicaya/SKILL.md`.

## Working with tests

- **Finish the task first, then make the suite green.** When a test failure
  surfaces while you are mid-change, stay on the main issue and see it through
  to completion. Once the issue is done, turn to the failures and resolve every
  one before wrapping up — a change is not finished while the suite is red.
- Treat unrelated, pre-existing failures the same way: surface them, and fix
  them as part of closing out the work rather than leaving them for later.
- Always run the relevant tests after a change, and add regression coverage for
  any bug you fix or behaviour you add.

## Static analysis

- **Fix every diagnostic in every file you touch.** When the linter or type
  checker flags an error or warning in a file you have edited — even if the
  issue predates your change — fix it before closing the task. Leave touched
  files cleaner than you found them.
