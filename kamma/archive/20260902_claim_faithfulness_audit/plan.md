# Plan — quote-supports-claim check + falsifier line

Spec: `spec.md`. Two edits to one file.

- [x] **T0 — Baseline.** Run the test suite once and log any pre-existing failures. Nothing in this thread touches `tools/`, so the suite should be unaffected either way.
  → verify: 3 pre-existing failures in the OCR-fallback tests (a parallel thread owns that file); everything else green. Re-run after the edits showed all 420 passing — that file changed under us mid-thread, which is expected on a shared tree.

- [x] **T1 — Confirm the edit sites.** Read the Phase 6 source-armed reviewer brief and the Phase 0 scope-assumptions instruction. Confirm the reviewer brief is a plain prompt block, and that `scope_assumptions` is free text not parsed anywhere downstream.
  → verify: confirmed. The reviewer brief is a literal prompt heredoc with no tooling behind it. `scope_assumptions` is stored in the header and only ever checked for truthiness when deciding whether to auto-write the Phase 0 gate — never parsed, so a trailing falsifier line is safe.

- [x] **T2 — Add review point 6.** Insert the quote-to-claim-fit point into the source-armed reviewer's brief only — not the external cross-check prompt, not the self-review fallback. Match the voice and length of points 1–5.
  → verify: the source-armed brief now lists six points; the external cross-check prompt and the self-review fallback still list five, as intended — neither has database access and both would guess.

- [x] **T3 — Add the falsifier line.** Extend the Phase 0 scope-assumptions instruction so the recorded assumptions end with a falsifier line, and add it to the confirmation template the agent shows the user when scope is ambiguous.
  → verify: the field description and the user-facing confirmation template both carry it; no CLI flag, no caller sweep, no code touched.

- [x] **T4 — Close out.** Full suite, then review.
  → verify: 420 passed, 0 failed. `review.md` written.
