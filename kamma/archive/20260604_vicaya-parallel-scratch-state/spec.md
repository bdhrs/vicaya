# Spec - Make Vicaya scratch run state safe for parallel and restarted sessions

No GitHub issue is associated with this thread.

## Overview

Vicaya research helpers persist the current scratch path and phase in
`data/scratch/.active`. That is convenient for a single uninterrupted session,
but it is not reliable when more than one research run is active or when a
session is restarted and needs to reattach to a specific scratch file.

The current resolver in `tools/research_sources.py` prefers the shared
`.active` pointer before an explicit slug. In practice, this means
`scratch-resume <slug>` can report or reattach to the wrong scratch if another
run updated `.active`. Manual `scratch-log` calls and auto-logged helper calls
can then append evidence to the wrong dossier unless the caller pins
`VICAYA_SCRATCH`.

This thread makes explicit run identity reliable while preserving `.active` as
a convenience fallback for normal one-session use.

## What it should do

- Treat an explicitly supplied scratch slug or scratch path as the intended run,
  not as a weaker fallback behind `.active`.
- Make `scratch-resume <slug>` reliably resolve that slug and reattach the
  helper state to the selected scratch.
- Preserve `VICAYA_SCRATCH` as a supported way to pin a run when commands do not
  otherwise identify the target scratch.
- Keep `data/scratch/.active` available for simple single-session use, but do
  not let it override an explicit run target.
- Keep scratch markdown format, phase gate semantics, and existing phase
  evidence requirements unchanged.
- Update the canonical Vicaya scratch instructions only as needed to describe
  the safer behavior and the remaining parallel-run rule.
- Add focused tests that reproduce the wrong-scratch behavior and confirm the
  corrected precedence.

## Assumptions & uncertainties

- The affected implementation is expected to be limited to
  `tools/research_sources.py`, `tests/test_research_sources.py`, and the
  scratchpad documentation in `skill/vicaya/SKILL.md`.
- `.active` should remain a best-effort convenience pointer, not a locking or
  multi-run registry.
- Fully automatic no-env parallel auto-logging is not possible while `.active`
  remains a single shared pointer. Parallel sessions still need to pin their
  scratch path, or use an explicit scratch option if one is added.
- `scratch-resume <slug>` should set the active scratch state for the selected
  run so a restarted single session can continue without manually editing
  `.active`.
- If existing tests already cover some scratch behavior, they should be reused
  or extended rather than replaced.

## Constraints

- Do not introduce a second scratch system or new workflow state outside the
  existing scratch file plus `.active` convenience state.
- Do not change final note generation, bibliography rules, phase gate checklists,
  or research-source search behavior.
- Do not modify secrets, local `.env` files, or machine-specific configuration.
- Run only validation scoped to touched files. Project-wide pytest, ruff,
  pyright, and pyrefly runs are out of scope unless explicitly approved.

## How we'll know it's done

- A test demonstrates that when `.active` points to run A,
  `scratch-resume run-b` resolves run B rather than run A.
- A test demonstrates that `scratch-resume <slug>` updates active scratch state
  to the selected run and appropriate next phase.
- A test or direct helper check demonstrates that explicit scratch selection
  and `VICAYA_SCRATCH` still work for manual scratch commands and auto-logging.
- Existing scratch helper tests still pass.
- The canonical scratch instructions accurately describe the precedence and the
  parallel-session requirement.

## What's not included

- No redesign of Vicaya research phases.
- No changes to staged skills or skill distribution.
- No multi-agent locking, file locks, or concurrent-write queue.
- No attempt to make unpinned parallel auto-logging safe while `.active` remains
  a single shared pointer.
- No migration of existing scratch files.
