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

## Database edits

- **Never modify dpd.db or any SQLite database unless explicitly asked.**
  Answer questions about data, suggest edits, analyse entries — but do not
  execute INSERT, UPDATE, DELETE, or DDL without a direct instruction from
  the user.

## Static analysis

- **Fix every diagnostic in every file you touch.** When the linter or type
  checker flags an error or warning in a file you have edited — even if the
  issue predates your change — fix it before closing the task. Leave touched
  files cleaner than you found them.

## Verifying a Fix or Dependency
- Verify in the interpreter the code actually runs under. This project's venv sets `include-system-site-packages = false`, so a `python3 -c "import x"` success proves nothing about `.venv/bin/python3`.

## Measurement Discipline
- A candidate must never score itself, and figures from different sample slices or administrations do not belong in the same table — least of all selecting a committed threshold.
- When a zero (zero failures, zero stalls) justifies deleting a safeguard, state the confidence interval. 0/20 has a 95% upper bound of 16%.
- Before writing a mitigation, check the thing it depends on still exists after the change it is meant to survive.
