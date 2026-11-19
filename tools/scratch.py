"""Scratch-dossier subsystem for Vicaya research runs."""

from __future__ import annotations

import fcntl
import functools
import json
import os
import re as _re
import subprocess
from contextlib import contextmanager
from pathlib import Path

from tools._common import resolve_vault_path

_SCRATCH_DIR = Path(__file__).resolve().parents[1] / "data" / "scratch"

# Phases auto-skipped for thematic (non-sutta-anchored) runs.
_AUTO_SKIP_PHASES = ("2.5", "3b")


@functools.cache
def _run_key() -> str:
    """A stable per-run identifier shared by every tool call in one research run.

    Keyed to OPENCODE_SESSION_ID when set: opencode's shell tool exports it per
    session, and a long-lived `opencode serve` runs every session's shell under
    one server process, so the process key below would give two parallel runs
    one shared state file (issue #155). Otherwise keyed to the agent process —
    the parent of the POSIX session leader. Every helper subprocess an agent
    launches in one run resolves to the same key; two parallel runs have
    different agent processes and therefore different keys.

    An opencode sub-agent has its own session id, so it does not see its
    parent's state until its first step, `scratch-resume <slug>`, writes one.

    Set VICAYA_SCRATCH (and VICAYA_PHASE) as a deterministic override: those
    env pins are checked before the state-file is read, so no ps spawn occurs
    on the env-pinned path.
    """
    session = os.environ.get("OPENCODE_SESSION_ID")
    if session:
        return session
    try:
        sid = os.getsid(0)
        out = subprocess.run(
            ["ps", "-o", "ppid=", "-p", str(sid)],
            capture_output=True,
            text=True,
            timeout=5,
        ).stdout.strip()
        if out:
            return out
    except Exception:
        pass
    try:
        return str(os.getppid())
    except Exception:
        return "default"


def _state_file() -> Path:
    """Path to this run's active-state pointer, keyed to the agent process."""
    return _SCRATCH_DIR / f".active-{_run_key()}.json"


@contextmanager
def _file_lock(target: Path):
    """Serialize concurrent read-modify-write of `target` across processes.

    A run's subagents all auto-log to the same scratch file; without this, two
    concurrent appends race on the read→splice→write cycle and one clobbers the
    other (a lost append). A blocking flock on a companion `.lock` file queues
    the writers; each append is sub-millisecond, so contention is negligible.
    Degrades to unlocked rather than crashing if the lock can't be created.
    """
    try:
        target.parent.mkdir(parents=True, exist_ok=True)
        fh = open(target.with_name(target.name + ".lock"), "w")
    except Exception:
        yield
        return
    try:
        fcntl.flock(fh.fileno(), fcntl.LOCK_EX)
        yield
    finally:
        try:
            fcntl.flock(fh.fileno(), fcntl.LOCK_UN)
        finally:
            fh.close()


def _read_state() -> dict:
    try:
        return json.loads(_state_file().read_text(encoding="utf-8"))
    except Exception:
        return {}


_STATE_PHASE_UNSET = object()


def _write_state(scratch=None, phase=_STATE_PHASE_UNSET) -> None:
    """Persist the active scratch path / phase so they survive between shell calls."""
    try:
        _SCRATCH_DIR.mkdir(parents=True, exist_ok=True)
        with _file_lock(_state_file()):
            state = _read_state()
            if scratch is not None:
                state["scratch"] = str(scratch)
            if phase is None:
                state.pop("phase", None)
            elif phase is not _STATE_PHASE_UNSET:
                state["phase"] = str(phase)
            _state_file().write_text(json.dumps(state), encoding="utf-8")
    except Exception:
        pass


# (phase_id, title, expected_evidence)
_SCRATCH_PHASES: list[tuple[str, str, list[str]]] = [
    (
        "0",
        "Phase 0 — Request understanding",
        [
            "question_polished recorded",
            "scope_assumptions recorded",
            "ambiguity_status set (clear|minor_uncertainty|unclear)",
        ],
    ),
    (
        "1",
        "Phase 1 — Vault / EBC",
        [
            "Angle triage recorded (applicable + not-applicable with reasons)",
            "Vault hits list logged",
            "Perspective map: 2–5 positions named (or 'no interpretive dispute')",
            "Counter-perspective search targets logged",
        ],
    ),
    (
        "2",
        "Phase 2 — Canon",
        [
            "Mūla searches logged per applicable Nikāya/text class",
            "Every hit has full pali + english + resolve-citation reference",
            "0-hit queries logged with stems tried",
            "Commentary/ṭīkā searched where doctrinal question",
        ],
    ),
    (
        "2.5",
        "Phase 2.5 — SC Parallels",
        [
            "sc-parallels called for each sutta-anchored citation",
            "text_gaps logged explicitly",
        ],
    ),
    (
        "3",
        "Phase 3 — Library",
        [
            "library-folders-check called at phase start",
            "Tag-scoped searches per applicable angle",
            "Author searches for named scholars in perspective map",
            "0-hit queries logged",
        ],
    ),
    (
        "3b",
        "Phase 3b — Other canons",
        [
            "Other canons (GRETIL / CBETA / 84000) searched where applicable (or 'not applicable')",
        ],
    ),
    (
        "4",
        "Phase 4 — Web",
        [
            "Web sources fetched with date + URL + summary",
            "Wisdomlib / SuttaCentral / 84000 checked where applicable",
        ],
    ),
    (
        "4b",
        "Phase 4b — YouTube",
        [
            "Trusted-tier channels queried where modern-teacher angle applies",
            "Transcript segments logged with timestamps",
            "is_auto flagged per transcript",
        ],
    ),
    (
        "4c",
        "Phase 4c — WisdomLib",
        [
            "Terms looked up with tradition + source labels",
        ],
    ),
    (
        "5",
        "Phase 5 — Synthesis",
        [
            "scratch-verify exit 0 confirmed before drafting",
            "Draft pasted under '## Phase 5 — Synthesis draft'",
        ],
    ),
    (
        "6",
        "Phase 6 — Cross-check",
        [
            "Cross-check raw output pasted verbatim (citations pre-annotated)",
            "Every [REJECTED] claim dropped — not integrated",
            "Integrations logged with source attribution",
        ],
    ),
    (
        "7",
        "Phase 7 — Note written",
        [
            "Vault path recorded via scratch-set-note (sets the path for the [REJECTED] hard gate)",
            "PDF path or 'skipped' recorded via scratch-set-note --pdf",
            "Zero [REJECTED] tags anywhere in the vault note (enforced by gate)",
            "Failure checklist answered via scratch-self-audit (enforced by gate)",
        ],
    ),
]

_PHASE_INDEX = {
    pid: (i, title, evidence)
    for i, (pid, title, evidence) in enumerate(_SCRATCH_PHASES)
}

# SKILL.md names the web phase "4a" but the phase table stores it as "4".
_PHASE_ALIASES = {"4a": "4"}
_PHASE_ALIAS_NOTE = (
    "Phase 4a is stored as Phase 4: log it, pin it and gate it as 4 or 4a, "
    "they are the same phase."
)

# Gather phases that sub-agents may run side by side. Each needs only the
# briefing (Phases 0 and 1) before it; the order among them is not checked
# here, because `scratch-gate 5` and `scratch-verify` still require every one
# of them, and a wave agent that finishes early was otherwise refused until
# its siblings gated (issue #133: one retried 14 times over 9 minutes).
_PARALLEL_GATHER_PHASES = frozenset({"2", "2.5", "3", "3b", "4", "4b", "4c"})


def _normalize_phase(phase: str) -> str:
    p = _PHASE_ALIASES.get(str(phase).strip().lower(), str(phase).strip())
    if p not in _PHASE_INDEX:
        raise ValueError(
            f"unknown phase {phase!r}; valid: {list(_PHASE_INDEX)} (alias: 4a → 4)"
        )
    return p


def _next_worked_phase(text: str, idx: int) -> str | None:
    nxt = idx + 1
    if _run_class(text) == "thematic":
        while (
            nxt < len(_SCRATCH_PHASES) and _SCRATCH_PHASES[nxt][0] in _AUTO_SKIP_PHASES
        ):
            nxt += 1
    if nxt < len(_SCRATCH_PHASES):
        return _SCRATCH_PHASES[nxt][0]
    return None


def _dated_slug(slug: str) -> str:
    """Prefix the slug with today's date (YYYY-MM-DD-), unless it already carries one."""
    if _re.match(r"\d{4}-\d{2}-\d{2}-", slug):
        return slug
    import datetime as _dt

    return f"{_dt.date.today().isoformat()}-{slug}"


def _scratch_path(slug: str | None = None) -> Path:
    """Resolve the scratch path. Explicit slug > env override > active-state file > error."""
    if slug:
        direct = _SCRATCH_DIR / f"{slug}.md"
        if direct.exists():
            return direct
        dated_re = _re.compile(r"^\d{4}-\d{2}-\d{2}-" + _re.escape(slug) + r"\.md$")
        matches = sorted(p for p in _SCRATCH_DIR.glob("*.md") if dated_re.match(p.name))
        if matches:
            return matches[-1]
        return direct
    env = os.environ.get("VICAYA_SCRATCH")
    if env:
        return Path(env)
    state = _read_state().get("scratch")
    if state:
        return Path(state)
    raise ValueError(
        "no scratch path: set VICAYA_SCRATCH, run scratch-init, or pass a slug"
    )


def _run_class(text: str) -> str:
    m = _re.search(r"\*\*Run class:\*\*\s*(\S+)", text)
    return m.group(1) if m else "sutta-anchored"


_AMBIGUITY_VALUES = ("clear", "minor_uncertainty", "unclear")


def scratch_init(
    slug: str,
    run_class: str = "sutta-anchored",
    *,
    question_original: str | None = None,
    question_polished: str | None = None,
    scope_assumptions: str | None = None,
    ambiguity: str | None = None,
) -> Path:
    """Create the scratch file with header + section skeleton. Idempotent — refuses to overwrite.

    When question_polished, scope_assumptions, and ambiguity are all provided,
    the Phase 0 evidence is recorded in the header, so the Phase 0 exit gate is
    written immediately — otherwise agents forget `scratch-gate 0` and every
    later gate refuses until it is backfilled.
    """
    if ambiguity is not None and ambiguity not in _AMBIGUITY_VALUES:
        raise ValueError(
            f"ambiguity must be one of {_AMBIGUITY_VALUES}, got {ambiguity!r}"
        )
    _SCRATCH_DIR.mkdir(parents=True, exist_ok=True)
    path = _scratch_path(slug)
    if path.exists():
        _write_state(path)
        return path
    path = _SCRATCH_DIR / f"{_dated_slug(slug)}.md"
    lines = [
        f"# Vicaya dossier — {slug}",
        f"**Question original:** {question_original or '<fill in>'}",
        f"**Question polished:** {question_polished or '<fill in>'}",
        f"**Scope assumptions:** {scope_assumptions or '<fill in>'}",
        f"**Ambiguity status:** {ambiguity or '<clear|minor_uncertainty|unclear>'}",
        f"**Slug:** {slug}",
        f"**Run class:** {run_class}",
        "**Vault note:** <set at Phase 7>",
        "",
        "## Phase log",
        "",
    ]
    for _, title, _ in _SCRATCH_PHASES:
        lines.append(f"## {title}")
        lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")
    _write_state(path, "0")
    if question_polished and scope_assumptions and ambiguity:
        scratch_gate("0", scratch=path)
    return path


def _phase_section_header(phase: str) -> str:
    return f"## {_PHASE_INDEX[_normalize_phase(phase)][1]}"


def _append_under_phase(path: Path, phase: str, block: str) -> None:
    """Append `block` immediately under the named phase's section heading."""
    header = _phase_section_header(phase)
    # Lock the whole read→splice→write so concurrent subagent appends to one
    # run's scratch can't clobber each other (lost append).
    with _file_lock(path):
        text = path.read_text(encoding="utf-8")
        if header not in text:
            text = text.rstrip() + f"\n\n{header}\n\n{block.rstrip()}\n"
            path.write_text(text, encoding="utf-8")
            return
        # Insert at the end of the section (before the next "## " or EOF).
        lines = text.splitlines(keepends=True)
        out: list[str] = []
        i = 0
        while i < len(lines):
            out.append(lines[i])
            if lines[i].rstrip() == header:
                i += 1
                # find end of this section
                section_end = i
                while section_end < len(lines) and not lines[section_end].startswith(
                    "## "
                ):
                    section_end += 1
                # copy section body, then append our block
                out.extend(lines[i:section_end])
                if out and not out[-1].endswith("\n"):
                    out.append("\n")
                out.append(block.rstrip() + "\n\n")
                i = section_end
                continue
            i += 1
        path.write_text("".join(out), encoding="utf-8")


def scratch_log(
    phase: str,
    tool: str,
    args: list[str] | None = None,
    summary: str | None = None,
    results_file: Path | None = None,
    hits: int | None = None,
    scratch: Path | None = None,
) -> Path:
    """Append a single structured entry under the named phase."""
    import datetime as _dt

    phase = _normalize_phase(phase)
    path = scratch or _scratch_path()
    if not path.exists():
        raise FileNotFoundError(
            f"scratch not initialised: {path}; run scratch-init <slug>"
        )
    ts = _dt.datetime.now().isoformat(timespec="seconds")
    body = [f"### {ts} · {tool}"]
    if args:
        body.append(f"- args: `{' '.join(args)}`")
    if hits is not None:
        body.append(f"- hits: {hits}")
    if summary:
        body.append(f"- summary: {summary}")
    if results_file is not None and Path(results_file).exists():
        body.append("- results:")
        body.append("```json")
        body.append(Path(results_file).read_text(encoding="utf-8").rstrip())
        body.append("```")
    _append_under_phase(path, phase, "\n".join(body))
    return path


def _gate_marker(phase: str) -> str:
    return f"### PHASE {phase} EXIT GATE"


# Phrases a crashed or lazy sub-agent leaves instead of doing the search.
_PLACEHOLDER_PATTERNS = (
    "would be searched",
    "would search",
    "would query",
    "would fetch",
    "would look up",
    "to be searched",
    "<fill in>",
)

# Gather/search phases whose section body must carry real evidence once gated.
# Phase 0 is header-driven; 5/6/7 hold the draft/cross-check/note, not searches.
# Phases whose gate requires at least one logged entry. The gather phases
# need logged searches; Phase 6 needs the cross-check output (or self-review)
# logged, so the review step cannot be silently skipped between synthesis and
# the vault write. Phases 0 (header fields), 5, and 7 (draft/finalization
# content) are exempt.
_CONTENT_PHASES = ("1", "2", "2.5", "3", "3b", "4", "4b", "4c", "6")


def _phase_body(text: str, pid: str) -> str:
    """Return the lines under a phase's `## ` heading, up to the next `## ` heading."""
    header = f"## {_PHASE_INDEX[pid][1]}"
    out: list[str] = []
    collecting = False
    for line in text.splitlines():
        if line.startswith("## "):
            if collecting:
                break
            collecting = line.strip() == header
            continue
        if collecting:
            out.append(line)
    return "\n".join(out)


def _agent_written_text(body: str) -> str:
    """The body without fenced blocks and blockquotes.

    Auto-logged results sit in ```json fences and quoted canon text in `>` lines.
    That text is source material, so a sutta saying "he would search for the
    arrow" is not a sign that the agent left a placeholder (issue #54).
    """
    kept: list[str] = []
    in_fence = False
    for line in body.splitlines():
        if line.lstrip().startswith("```"):
            in_fence = not in_fence
            continue
        if in_fence or line.lstrip().startswith(">"):
            continue
        kept.append(line)
    return "\n".join(kept)


def _phase_content_issue(body: str) -> str | None:
    """Classify a gated phase's body: 'placeholder', 'empty', or None (has evidence).

    Auto-skipped phases (gate marked AUTO-SKIPPED) are legitimately empty. Real
    evidence is any logged block (`### <ts> · tool`) or hand-written note under
    the heading — the exit-gate block alone does not count, so a crashed agent
    that gated a phase without searching is caught instead of passing verify.
    """
    if "AUTO-SKIPPED" in body:
        return None
    low = _agent_written_text(body).lower()
    for pat in _PLACEHOLDER_PATTERNS:
        # Patterns ending in a word character (e.g. "would search") need a
        # trailing word boundary so they don't false-match an inflected form
        # inside quoted canonical text (e.g. "would searching still be
        # found" in a translated passage). Patterns ending in punctuation
        # (e.g. "<fill in>") have no word-char tail to bound, so fall back
        # to plain substring matching.
        if pat[-1].isalnum():
            if _re.search(_re.escape(pat) + r"\b", low):
                return "placeholder"
        elif pat in low:
            return "placeholder"
    seen_heading = False
    for line in body.splitlines():
        if line.startswith("### "):
            seen_heading = True
            if "EXIT GATE" not in line:
                return None
            continue
        if not seen_heading and line.strip():
            return None
    return "empty"


_SELF_AUDIT_MARKER = "### SELF-AUDIT"

_SELF_AUDIT_QUESTIONS = [
    "Easy-source bias: did any conclusion lean on vault/web hits because canon "
    "or library searching was harder? Name the claim, or 'none'.",
    "User seeds: was every source, note, or constraint the user named actually "
    "engaged, not just mentioned?",
    "Early stopping: is any applicable angle or named position thin because the "
    "evidence felt 'enough'? Name it, or 'none'.",
    "Artifact vs completion: does every step claimed done (note, PDF, gates, "
    "sync) have its artifact verified on disk?",
    "Stale instructions: was any secondary or stale instruction followed "
    "mechanically against the user's actual request this run?",
    "Cross-check corrections: was every applied correction verified against "
    "the mūla before integration?",
]


def scratch_self_audit(
    answers: list[str] | None = None, scratch: Path | None = None
) -> dict:
    """Record the pre-completion failure checklist under Phase 7.

    The checklist targets the recurring end-of-run failure modes (easy-source
    bias, dropped user seeds, early stopping, artifact-vs-completion confusion,
    stale instructions, unverified cross-check corrections). Called without
    answers it prints the questions; called with one answer per question it
    appends the Q/A block the Phase 7 gate requires. Honest one-liners are the
    point — a named problem means fixing the note before gating, not wordsmithing
    the answer.
    """
    import datetime as _dt

    path = scratch or _scratch_path()
    if not path.exists():
        raise FileNotFoundError(
            f"scratch not initialised: {path}; run scratch-init <slug>"
        )
    if _SELF_AUDIT_MARKER in path.read_text(encoding="utf-8"):
        return {"ok": True, "note": "self-audit already recorded; not duplicated"}
    if not answers:
        return {
            "ok": False,
            "questions": _SELF_AUDIT_QUESTIONS,
            "message": (
                f"answer the checklist: re-run with {len(_SELF_AUDIT_QUESTIONS)} "
                "--answer values, one per question in order — scratch-gate 7 "
                "refuses until the audit is recorded"
            ),
        }
    if len(answers) != len(_SELF_AUDIT_QUESTIONS) or not all(
        a.strip() for a in answers
    ):
        return {
            "ok": False,
            "error": (
                f"expected {len(_SELF_AUDIT_QUESTIONS)} non-empty --answer values "
                f"(one per question, in order), got {len(answers)}"
            ),
            "questions": _SELF_AUDIT_QUESTIONS,
        }
    ts = _dt.datetime.now().isoformat(timespec="seconds")
    block = [_SELF_AUDIT_MARKER, f"- timestamp: {ts}"]
    for q, a in zip(_SELF_AUDIT_QUESTIONS, answers):
        block.append(f"- Q: {q}")
        block.append(f"  A: {a.strip()}")
    _append_under_phase(path, "7", "\n".join(block))
    return {"ok": True, "scratch": str(path), "answers_recorded": len(answers)}


def scratch_gate(phase: str, scratch: Path | None = None) -> dict:
    """Append the canonical exit-gate checklist for `phase`.

    Refuses if any earlier phase's gate is missing — returns {ok: False, missing: ...}
    without writing.
    """
    import datetime as _dt

    phase = _normalize_phase(phase)
    path = scratch or _scratch_path()
    if not path.exists():
        raise FileNotFoundError(
            f"scratch not initialised: {path}; run scratch-init <slug>"
        )
    text = path.read_text(encoding="utf-8")
    idx = _PHASE_INDEX[phase][0]
    # Thematic (non-sutta-anchored) runs auto-skip SC-parallels (2.5) and Sanskrit
    # (3b): inapplicable, so the agent shouldn't hand-log empty searches to pass them.
    if _run_class(text) == "thematic":
        for skip_id in _AUTO_SKIP_PHASES:
            if _PHASE_INDEX[skip_id][0] < idx and _gate_marker(skip_id) not in text:
                stitle = _PHASE_INDEX[skip_id][1]
                _append_under_phase(
                    path,
                    skip_id,
                    f"{_gate_marker(skip_id)}\n- AUTO-SKIPPED (thematic run): "
                    f"{stitle} not applicable to a non-sutta-anchored question.",
                )
                text = path.read_text(encoding="utf-8")
    # Verify every prior phase has a gate (a parallel gather phase needs only
    # the briefing phases, 0 and 1).
    required = (
        _SCRATCH_PHASES[: _PHASE_INDEX["2"][0]]
        if phase in _PARALLEL_GATHER_PHASES
        else _SCRATCH_PHASES[:idx]
    )
    for prev_id, prev_title, prev_expected in required:
        if _gate_marker(prev_id) not in text:
            return {
                "ok": False,
                "missing_phase": prev_id,
                "missing_title": prev_title,
                "expected_evidence": prev_expected,
                "message": (
                    f"cannot write Phase {phase} gate: Phase {prev_id} "
                    f"({prev_title}) gate is missing — "
                    f"run scratch-gate {prev_id} first. "
                    + (_PHASE_ALIAS_NOTE if "4" in (phase, prev_id) else "")
                ).strip(),
            }
    # Already gated?
    if _gate_marker(phase) in text:
        return {
            "ok": True,
            "phase": phase,
            "note": "gate already present; not duplicated",
        }
    # Phase 7 hard gate: failure checklist answered, then scan the vault note
    # for [REJECTED] tags.
    if phase == "7":
        if _SELF_AUDIT_MARKER not in text:
            return {
                "ok": False,
                "phase": "7",
                "reason": "self-audit missing",
                "message": (
                    "Phase 7 gate refused: run scratch-self-audit first — "
                    "answer the failure checklist (one --answer per question) "
                    "before gating."
                ),
            }
        vault_match = _re.search(r"\*\*Vault note:\*\*\s*(.+)", text)
        if vault_match:
            raw = vault_match.group(1).strip()
            if raw and not raw.startswith("<"):
                vault_path = Path(raw)
                if vault_path.exists():
                    note_text = vault_path.read_text(encoding="utf-8")
                    if "[REJECTED" in note_text:
                        offending = [
                            line.strip()
                            for line in note_text.splitlines()
                            if "[REJECTED" in line
                        ][:5]
                        return {
                            "ok": False,
                            "phase": "7",
                            "reason": "vault note contains [REJECTED] tags",
                            "vault_note": str(vault_path),
                            "offending_lines": offending,
                            "message": (
                                "Phase 7 gate refused: the vault note contains "
                                "[REJECTED] citation tags. Remove those claims and "
                                "the inline tags before gating."
                            ),
                        }
                    unread = unread_library_citations(note_text, text)
                    if any(unread.values()):
                        return {
                            "ok": False,
                            "phase": "7",
                            "reason": "library documents cited, flagged or rejected unread "
                            "without a read-library entry",
                            "vault_note": str(vault_path),
                            **unread,
                            "message": (
                                "Phase 7 gate refused: the index holds the full "
                                "text of these books, mounted volume or not. For "
                                "each book in cited_not_read, run `read-library "
                                '<id> --around "<phrase>"` with an id from its '
                                "read_library list, and replace every 'unread / "
                                "snippet-only' line naming a book in "
                                "flagged_unread_but_readable with what the book "
                                "actually says. For each book in rejected_unread, "
                                "read it once (`--chars 1500` is enough), then "
                                "give the rejection a real reason or use the "
                                "source. The ids are handles for this run only: "
                                "the note names each book by title and author."
                            ),
                        }
    # For gather phases and the Phase 6 cross-check, require at least one real
    # logged entry before gating. Phase 0 uses header fields (no tool logs);
    # phases 5 and 7 hold draft/finalization content — those are exempt.
    # AUTO-SKIPPED thematic phases are also exempt.
    if phase in _CONTENT_PHASES:
        body = _phase_body(text, phase)
        if "AUTO-SKIPPED" not in body and _phase_content_issue(body) == "empty":
            action = (
                "run the cross-check (or record the self-review) and log it"
                if phase == "6"
                else "run the searches first"
            )
            return {
                "ok": False,
                "phase": phase,
                "reason": "no logged evidence",
                "message": (
                    f"Phase {phase} gate refused: the phase section has no logged "
                    f"tool calls — {action}, then gate. If you just ran the "
                    f"search or scratch-log in the same batch as this gate, run "
                    f"the gate again on its own once they have finished. "
                    f"Expected evidence: {_PHASE_INDEX[phase][2]}"
                ),
            }
    ts = _dt.datetime.now().isoformat(timespec="seconds")
    _, title, evidence = _PHASE_INDEX[phase]
    block_lines = [_gate_marker(phase), f"- timestamp: {ts}", f"- title: {title}"]
    for item in evidence:
        block_lines.append(f"- [ ] {item}")
    _append_under_phase(path, phase, "\n".join(block_lines))
    # Advance the active phase so the next phase's searches auto-log correctly
    # without the agent re-exporting VICAYA_PHASE. Thematic runs skip over the
    # auto-skipped phases so logs land on the next phase actually worked.
    next_phase = _next_worked_phase(text, idx)
    if next_phase is not None:
        _write_state(phase=next_phase)
    result = {"ok": True, "phase": phase, "title": title}
    if phase == "4":
        result["alias"] = _PHASE_ALIAS_NOTE
    return result


def scratch_set_note(
    note_path: str, pdf: str | None = None, scratch: Path | None = None
) -> dict:
    """Record the saved vault note (and optionally PDF) path in the scratch header.

    The Phase 7 hard gate reads the `**Vault note:**` header to scan the saved
    note for [REJECTED] tags — this subcommand is the supported way to set it;
    never hand-edit the header. A relative path that doesn't exist from the
    current directory is retried against VICAYA_VAULT_PATH, so the
    vault-relative form used by the Obsidian CLI works directly.
    """
    path = scratch or _scratch_path()
    if not path.exists():
        raise FileNotFoundError(
            f"scratch not initialised: {path}; run scratch-init <slug>"
        )
    note = resolve_vault_path(note_path)
    if not note.exists():
        return {
            "ok": False,
            "note_path": str(note),
            "message": (
                f"vault note not found: {note} — pass the path exactly as saved "
                "(absolute, or vault-relative with VICAYA_VAULT_PATH set); "
                "the Phase 7 gate scans this file for [REJECTED] tags"
            ),
        }
    if pdf is not None and pdf.strip().lower() != "skipped":
        pdf_file = resolve_vault_path(pdf)
        if not pdf_file.exists():
            return {
                "ok": False,
                "pdf": pdf,
                "message": (
                    f"PDF not found: {pdf_file} — generate the PDF first, then "
                    "record it. Run scratch-set-note after the PDF step has "
                    "finished, not in the same parallel batch."
                ),
            }
    note = note.resolve()
    note_line = f"**Vault note:** {note}"
    with _file_lock(path):
        text = path.read_text(encoding="utf-8")
        new_text, n = _re.subn(
            r"^\*\*Vault note:\*\*.*$",
            lambda _: note_line,
            text,
            count=1,
            flags=_re.M,
        )
        if n == 0:
            # Header line absent (pre-skeleton scratch): insert after **Run class:**.
            lines = new_text.splitlines(keepends=True)
            insert_at = 1
            for i, line in enumerate(lines):
                if line.startswith("**Run class:**"):
                    insert_at = i + 1
                    break
            lines.insert(insert_at, note_line + "\n")
            new_text = "".join(lines)
        if pdf is not None:
            pdf_line = f"**PDF:** {pdf}"
            new_text, n = _re.subn(
                r"^\*\*PDF:\*\*.*$",
                lambda _: pdf_line,
                new_text,
                count=1,
                flags=_re.M,
            )
            if n == 0:
                new_text = new_text.replace(note_line, f"{note_line}\n{pdf_line}", 1)
        path.write_text(new_text, encoding="utf-8")
    result = {"ok": True, "scratch": str(path), "vault_note": str(note)}
    if pdf is not None:
        result["pdf"] = pdf
    return result


def scratch_verify(through: str | None = None, scratch: Path | None = None) -> dict:
    """Verify gather phases (and, past 5, the cross-check) are gated AND carry real content.

    Without `through`, checks every pre-synthesis phase (0 through 4c) — the same
    set Phase 5's gate requires — so verify and `scratch-gate 5` never disagree
    over whether 4b/4c are needed. Thematic runs skip the 2.5/3b gates. With an
    explicit `through`, checks phases 0..through.

    A gated phase whose body is empty or only placeholder text ("would search
    …") makes ok False: gate presence alone does not prove the phase was worked.

    Returns {ok, checked_through, missing: [...], content_issues: [...]}.
    """
    path = scratch or _scratch_path()
    if not path.exists():
        return {"ok": False, "error": f"scratch not initialised: {path}"}
    text = path.read_text(encoding="utf-8")
    thematic = _run_class(text) == "thematic"
    if through is not None:
        try:
            through = _normalize_phase(through)
        except ValueError as e:
            return {"ok": False, "error": str(e)}
        upper = _PHASE_INDEX[through][0] + 1
    else:
        # Default: every pre-synthesis phase (the set scratch-gate 5 requires).
        upper = _PHASE_INDEX["5"][0]
    missing = []
    content_issues = []
    for pid, title, expected in _SCRATCH_PHASES[:upper]:
        if thematic and pid in _AUTO_SKIP_PHASES and _gate_marker(pid) not in text:
            continue
        if _gate_marker(pid) not in text:
            missing.append(
                {
                    "phase": pid,
                    "title": title,
                    "expected_evidence": expected,
                }
            )
            continue
        if pid in _CONTENT_PHASES:
            issue = _phase_content_issue(_phase_body(text, pid))
            if issue:
                content_issues.append({"phase": pid, "title": title, "issue": issue})
    return {
        "ok": not missing and not content_issues,
        "checked_through": upper,
        "missing": missing,
        "content_issues": content_issues,
    }


# Unaccounted hits shown with full detail; the rest list id and title only.
_COVERAGE_REVIEW_FIRST = 10
_LIBRARY_SEARCH_BLOCK_RE = _re.compile(
    r"^### \S+ · search-library-folders\n(.*?)(?=^### |\Z)", _re.M | _re.S
)
_HIT_JSON_RE = _re.compile(r"\{[^{}]*\"document_id\"\s*:\s*\d+[^{}]*\}")
_FENCED_JSON_RE = _re.compile(r"```json\n(.*?)\n```", _re.S)
_QUERY_FLAG_RE = _re.compile(r"\s--[\w-]+(?:\s+\d+(?:\.\d+)?)?")


def _logged_library_hits(text: str) -> list[dict]:
    """Library hits in logged results, in their logged order.

    Each fenced JSON block is parsed whole. A flat-object regex alone skipped
    every hit whose `possible_duplicate_of` holds nested objects — 22% of
    documents across 148 real dossiers never reached the coverage check. The
    regex stays only for a block that does not parse as JSON.
    """
    hits: list[dict] = []
    for block in _FENCED_JSON_RE.finditer(text):
        try:
            data = json.loads(block.group(1))
        except json.JSONDecodeError:
            for m in _HIT_JSON_RE.finditer(block.group(1)):
                try:
                    data_item = json.loads(m.group(0))
                except json.JSONDecodeError:
                    continue
                if isinstance(data_item.get("document_id"), int):
                    hits.append(data_item)
            continue
        items = data if isinstance(data, list) else [data]
        hits.extend(
            item
            for item in items
            if isinstance(item, dict) and isinstance(item.get("document_id"), int)
        )
    return hits


_TITLE_STOPWORDS = frozenset(
    "the and for from with into onto that this these those its are was were "
    "upon about over under between through his her their our your not but "
    "all any some other what which who whom how why when where "
    "vol volume part chapter page pages".split()
)
# Share of a citation's title words that must appear among a hit's words.
_TITLE_MATCH_SHARE = 0.8
_NUMBER_WORDS = {
    word: str(n)
    for n, word in enumerate(
        "zero one two three four five six seven eight nine ten eleven twelve "
        "thirteen fourteen fifteen sixteen seventeen eighteen nineteen "
        "twenty".split()
    )
}
_ROMAN_NUMERALS = {
    word: str(n)
    for n, word in enumerate("i ii iii iv v vi vii viii ix x".split(), start=1)
}
_NUMBERED_PARTS = frozenset({"vol", "volume", "part", "chapter", "ch", "book"})


def _folded_words(text: str) -> list[str]:
    """Lowercase words with accents dropped; `_` and punctuation split words.

    Letters and digits split apart and a number loses its leading zeros:
    Piya Tan's files write `sd.04.9` for the "SD 4.9" a note cites, and notes
    write "SD33.8" for `sd.33.8`. Number words become digits, and so does a
    Roman numeral after "Vol.", "Part" or "Chapter": notes write "ch. 19" for
    a file's "Chapter Nineteen" and "Vol. I" for its "1".
    """
    import unicodedata

    plain = "".join(
        c for c in unicodedata.normalize("NFKD", text) if not unicodedata.combining(c)
    )
    words: list[str] = []
    for w in _re.findall(r"\d+|[^\W\d_]+", plain.casefold()):
        if w.isdigit():
            w = w.lstrip("0") or "0"
        elif w in _NUMBER_WORDS:
            w = _NUMBER_WORDS[w]
        elif w in _ROMAN_NUMERALS and words and words[-1] in _NUMBERED_PARTS:
            w = _ROMAN_NUMERALS[w]
        words.append(w)
    # A numeral that ends a title is a volume too ("73180057-Mahāvastu-I").
    if len(words) > 1 and words[-1] in _ROMAN_NUMERALS:
        words[-1] = _ROMAN_NUMERALS[words[-1]]
    return words


def _word_set(text: str) -> set[str]:
    """A text's folded words, plus each pair of neighbours joined.

    Pāḷi compounds split in different places in different files: a note's
    "Nibbānagāminīpaṭipadā" is a folder's "NIBBĀNA GĀMINIPAŢIPADĀ", and a
    note's "Loka,dhamma" a file's "Lokadhamma".
    """
    words = _folded_words(text)
    return set(words) | {a + b for a, b in zip(words, words[1:]) if a.isalpha()}


def _title_sequence(title: str) -> list[str]:
    """A title's content words in order: no stop words, no download ids.

    A run of six or more digits is a download id ("122209229-A-Study-of…"),
    not part of the title.
    """
    return [
        w
        for w in _folded_words(title)
        if not (w.isdigit() and len(w) >= 6)
        and ((len(w) >= 3 and w not in _TITLE_STOPWORDS) or w.isdigit())
    ]


def _title_words(title: str) -> set[str]:
    words = [w for w in _folded_words(title) if not (w.isdigit() and len(w) >= 6)]
    return set(_title_sequence(title)) or set(words)


def _title_tries(title: str) -> list[set[str]]:
    """A title's words, then looser forms of it.

    The looser forms drop bracketed notes ("(4th ed.)", "(MN22)") and then the
    subtitle after a colon (Calibre writes `_ ` for one, and many titles use
    " - "): Calibre's cut names lose the subtitle, and notes drop or misquote
    it.
    """
    tries = [_title_words(title)]
    for looser in (_unbracketed(title), _main_title(title)):
        words = _title_words(looser)
        if words and words not in tries:
            tries.append(words)
    return [words for words in tries if words]


def _unbracketed(title: str) -> str:
    return _re.sub(r"\([^)]*\)|\[[^\]]*\]", " ", title)


def _main_title(title: str) -> str:
    return _re.split(r":|_ | - | — ", _unbracketed(title), maxsplit=1)[0]


def _split_citation(citation: str) -> tuple[str, set[str], set[str]]:
    """(title, author words sure enough to rule a hit out, author words).

    The author follows the last " — ": notes also write "Dying to Live — The
    Role of Kamma in Dying and Rebirth — Aggacitta Bhikkhu". Older notes write
    "The Secret - Rhonda Byrne", but " - " also ends main titles ("Mahavamsa
    - The Great Chronicle"), so an author read that way can back a match but
    never rule one out.
    """
    title, dash, author = citation.rpartition(" — ")
    if dash:
        sure = _author_words(author)
        return _FILE_EXTENSION_RE.sub("", title), sure, sure
    title = _FILE_EXTENSION_RE.sub("", citation)
    # "Journal - Sayagyi U Ba Khin - S.N. Goenka": any part after the first
    # dash may be the author.
    _, dash, rest = title.partition(" - ")
    return title, set(), _author_words(rest) if dash else set()


_CALIBRE_FOLDER_RE = _re.compile(r"^(.*?)\s*\(\d+\)$")
_AUTHOR_STOPWORDS = frozenset(
    "bhikkhu bhikkhuni ven venerable ajahn ajaan thera mahathera sayadaw "
    "editor editors trans translator prof professor unknown various "
    "anonymous".split()
)


def _author_words(text: str) -> set[str]:
    return {
        w for w in _folded_words(text) if len(w) >= 3 and w not in _AUTHOR_STOPWORDS
    }


def _authors_agree(left: set[str], right: set[str]) -> bool:
    """Do two author lists share a name, allowing a typo?

    Calibre's own metadata misspells names ("Sanhgarakshita", "Russel T.
    Hulbert"), so an exact match alone rejected the right book.
    """
    from difflib import SequenceMatcher

    if left & right:
        return True
    return any(
        len(a) >= 5
        and a[0] == b[0]
        and abs(len(a) - len(b)) <= 2
        and SequenceMatcher(None, a, b).ratio() >= 0.8
        for a in left
        for b in right
    )


class _HitNames:
    """How a library hit can be named: its titles, authors and cut words."""

    __slots__ = (
        "titles",
        "tries",
        "authors",
        "hints",
        "cut",
        "words",
        "file_code",
        "seqs",
    )

    def __init__(self, hit: dict) -> None:
        """Read the names from the `cite_as` string, the file name and folders.

        Only the file name and its folder give titles: the folders above are
        categories ("1 Theravada", "Articles") that match unrelated citations.
        Inside a Calibre book folder a file is named `<title> - <author>` (the
        title may hold " - " itself); elsewhere " - " is no such sign ("The
        five Khandhas - Their treatment…"). Outside Calibre the two folders
        above a file often name its author ("P. Masefield, Tr", "Analayo,
        Ven") but as often a category, so they only `hints`: they can back a
        short title, never rule a match out. Calibre cuts a long title
        mid-word in its folder and file names ("…Lord of Deat (3197)"), so the
        last word of each may be a prefix.
        """
        titles: list[str] = []
        authors: set[str] = set()
        cut: set[str] = set()
        file_code = ""
        cite_as = hit.get("cite_as")
        if isinstance(cite_as, str) and cite_as.strip():
            title, _, author = cite_as.partition(" — ")
            titles.append(title)
            authors |= _author_words(author)
        rel = hit.get("relative_path")
        rel = rel if isinstance(rel, str) else ""
        parts = rel.split("/")
        folder = parts[-2] if len(parts) >= 2 else ""
        calibre = _CALIBRE_FOLDER_RE.match(folder)
        name = hit.get("title")
        name = name if isinstance(name, str) and name else parts[-1]
        if name:
            stem = name.rsplit(".", 1)[0] if "." in name else name
            head, _, author = stem.rpartition(" - ")
            # The title part of a Calibre name: "Comparative-Dhammapada -
            # Unknown" is coded by "Comparative-Dhammapada".
            code_words = _folded_words(head if calibre and head else stem)
            if len(code_words) <= 2 and len("".join(code_words)) >= 5:
                file_code = "".join(code_words)
            if calibre and head:
                titles.append(head)
                authors |= _author_words(author)
            else:
                titles.append(stem)
            cut.update(_folded_words(head or stem)[-1:])
        if folder:
            titles.append(calibre.group(1) if calibre else folder)
            if calibre:
                cut.update(_folded_words(calibre.group(1))[-1:])
        self.titles = titles
        self.tries = [_title_tries(t) for t in titles]
        self.authors = authors
        self.hints = (
            set() if calibre else _author_words(" ".join(parts[-3:-1]))
        ) - authors
        self.cut = {w for w in cut if len(w) >= 3}
        self.words = authors.union(*(_word_set(t) for t in titles))
        # A file named by a code ("pettit991", "baum2", "dreyfus"): notes name
        # such files by that code, as no title exists to name them by.
        self.file_code = file_code
        self.seqs = [_title_sequence(t) for t in titles]


def _word_found(
    word: str, have: set[str], cut: set[str], word_cut: bool, typo: bool = False
) -> bool:
    """Is `word` among `have`, allowing a plural, a cut word and maybe a typo?

    `cut` holds words of `have` that may be cut short; `word_cut` says `word`
    itself may be. `typo` lets a long word differ by a slip ("Uconscious",
    "VIijnaptimatratasiddhi" in Calibre's own titles); 0.93 keeps
    "Dhammapada"/"Dhammapāla" and "Abhidhamma"/"Abhidharma" (0.9) apart.
    """
    if word in have or word + "s" in have or word + "es" in have:
        return True
    if word.endswith("s") and (word[:-1] in have or word[:-2] in have):
        return True
    if any(word.startswith(c) for c in cut):
        return True
    if word_cut and any(h.startswith(word) for h in have):
        return True
    if not typo or len(word) < 8:
        return False
    from difflib import SequenceMatcher

    return any(
        h[0] == word[0]
        and abs(len(h) - len(word)) <= 2
        and SequenceMatcher(None, word, h).ratio() >= 0.93
        for h in have
    )


def _share_found(
    wanted: set[str],
    have: set[str],
    cut: set[str],
    wanted_cut: set[str],
    typo: bool = False,
) -> bool:
    found = sum(1 for w in wanted if _word_found(w, have, cut, w in wanted_cut, typo))
    return found >= _TITLE_MATCH_SHARE * len(wanted)


def _names_hit(
    words: set[str],
    names: _HitNames,
    author_words: set[str],
    cited_title: str | None = None,
) -> bool:
    """Do these words (a note line's, or a citation's) hold one of the hit's titles?

    A title of one or two words ("Merit", "Buddhist Romanticism") names many
    books, so it counts only when the author is named too, or when the hit
    has no known author and its two title words are the citation's title. A
    hit's shortened title must be found within a citation's main title, not
    anywhere in it: "Pāli: A Grammar of the Language of the Theravāda
    Tipiṭaka" holds Oberlies's other book "Pali Grammar" in its subtitle.
    A typo in a title word is forgiven only when the author is named.
    `author_words` are the words the hit's author is looked for in. A folder
    word that is also the title being tried ("Library", "Articles") is no
    evidence of an author: it let any line holding that word name the hit.
    """
    known = _authors_agree(names.authors, author_words)
    cited_words = _title_words(cited_title) if cited_title is not None else None
    cited_main = (
        set(_folded_words(_main_title(cited_title)))
        if cited_title is not None
        else words
    )
    for tries in names.tries:
        for n, wanted in enumerate(tries):
            author_named = known or _authors_agree(names.hints - wanted, author_words)
            if len(wanted) < 3 and not (
                author_named
                or (not names.authors and len(wanted) == 2 and wanted == cited_words)
            ):
                continue
            if _share_found(
                wanted,
                cited_main if n else words,
                set(),
                wanted & names.cut,
                author_named,
            ):
                return True
    return False


def _line_sequence(line: str) -> str:
    return " " + " ".join(_title_sequence(line)) + " "


def _line_names_hit(
    line_words: set[str], names: _HitNames, line_seq: str = "", codes: bool = True
) -> bool:
    """Does a note line (a Not Used row, a sentence) name this library hit?

    `line_words` is `_word_set(line)` and `line_seq` is `_line_sequence(line)`,
    built once per line by the caller. A line also names a hit when it holds
    the start of the hit's title, word for word: four title words, or three
    beside the author ("Malalgoda, *Buddhism in Sinhalese Society*" for the
    file "Buddhism in Sinhalese Society 1"; "Mihita, 'Buddha as Progenitor of
    Pali'" for a cut Calibre name). `codes=False` drops the file-code match:
    a code can be an ordinary word ("Visuddhimagga - Buddhaghosa.pdf" codes
    "visuddhimagga"), which is harmless for coverage but let any gate line
    mentioning the text refuse a run.
    """
    if codes and names.file_code and names.file_code in line_words:
        return True
    if line_seq:
        named = None
        for seq in names.seqs:
            if len(seq) >= 4 and f" {' '.join(seq[:4])} " in line_seq:
                return True
            if len(seq) < 3 or f" {' '.join(seq[:3])} " not in line_seq:
                continue
            if named is None:
                named = _authors_agree(names.authors | names.hints, line_words)
            if named:
                return True
    return _names_hit(line_words, names, line_words)


def _volume_numbers(title: str, trailing: bool = True) -> set[str]:
    """Numbers a title gives after "Vol.", "Part" or "Chapter".

    With `trailing`, a number ending the title counts too: Calibre names
    Anālayo's second volume "A Comparative Study Of The Majjhima Nikaya 2".
    """
    words = _folded_words(_unbracketed(title))
    numbers = {
        b for a, b in zip(words, words[1:]) if a in _NUMBERED_PARTS and b.isdigit()
    }
    if trailing and len(words) > 1 and words[-1].isdigit() and len(words[-1]) <= 2:
        numbers.add(words[-1])
    return numbers


def _volumes_conflict(cited: set[str], names: _HitNames) -> bool:
    """Does the hit give a volume, part or chapter other than the cited one?"""
    if not cited:
        return False
    found = set().union(*(_volume_numbers(t) for t in names.titles))
    return bool(found) and not cited & found


def library_title_matches(citation: str, hit: dict | _HitNames) -> bool:
    """Does a note's citation (`<Title> — <Author>`) name this library hit?

    Notes name a book by title and author because the index id is a row
    number that changes on every rebuild, move or rename. Copies of one book
    (PDF and EPUB, two folders) all match. The hit's names come from its
    `cite_as`, file name and folder, so a hit logged before `cite_as` existed
    still matches on its file name and Calibre folder.

    The match runs both ways. The citation's title must be found among the
    hit's words, and one of the hit's titles among the citation's words: one
    way alone joined "The Gospel of Judas" to "Reading Judas: The Gospel of
    Judas and the Shaping of Christianity". When both name an author, they
    must share one, or every translation of the Yoga Sutras matches.
    """
    names = hit if isinstance(hit, _HitNames) else _HitNames(hit)
    title, sure_authors, cited_authors = _split_citation(citation)
    if names.authors and sure_authors:
        if not _authors_agree(names.authors, sure_authors):
            return False
    if _volumes_conflict(_volume_numbers(title, trailing=False), names):
        return False
    # The exact label the library tool emits for an authorless file
    # ("Dhammapada") names that file, however short.
    if (
        not names.authors
        and names.titles
        and _folded_words(title) == _folded_words(names.titles[0])
    ):
        return True
    # The cited author's name inside the hit's own name counts too
    # ("Aorist in Pali_Ruiz-Falques_SSBU OPEN DAY_" for "— A. Ruiz-Falqués").
    author_named = bool(cited_authors) and _authors_agree(
        names.authors | names.hints | names.words, cited_authors
    )
    if _title_prefix_match(title, names, author_named, cited_authors):
        return True
    if not any(
        _share_found(w, names.words, names.cut, set(), author_named)
        for w in _title_tries(title)
    ):
        return False
    if not _names_hit(_word_set(citation), names, cited_authors, title):
        return False
    # The words alone ignore which title is the main one: Keyes's "Flourishing:
    # Positive Psychology and the Life…" holds every word of Compton's
    # "Positive Psychology: … Happiness and Flourishing". Main titles that
    # share no word, author names aside, are two books. A main title of
    # author names only ("Marcus Aurelius - Meditations", "Bhikkhu Anālayo:
    # Overeating…") says nothing either way.
    author_like = names.authors | cited_authors | _AUTHOR_STOPWORDS
    cited_main = _title_words(_main_title(title)) - author_like
    if not cited_main:
        return True
    for hit_title in names.titles:
        main = _title_words(_main_title(hit_title)) - author_like
        if not main or any(
            a == b
            or (min(len(a), len(b)) >= 4 and (a.startswith(b) or b.startswith(a)))
            for a in main
            for b in cited_main
        ):
            return True
    return False


_FILE_EXTENSION_RE = _re.compile(
    r"\.(?:pdf|epub|mobi|azw3|docx?|txt|html?|rtf|odt|djvu)\s*$", _re.I
)


def _starts_with(longer: list[str], prefix: list[str], last_cut: bool) -> bool:
    if not prefix or len(prefix) > len(longer):
        return False
    if longer[: len(prefix) - 1] != prefix[:-1]:
        return False
    end, last = longer[len(prefix) - 1], prefix[-1]
    return end == last or (last_cut and end.startswith(last))


def _title_prefix_match(
    title: str, names: _HitNames, author_named: bool, cited_authors: set[str]
) -> bool:
    """Does one title begin with the other, word for word?

    Calibre ends a main title with a full stop or a comma as often as a colon
    ("Wings to Awakening. An Anthology from the"), and cuts a long one short
    ("Buddhist Forest Monasteries and Med"); in both, one title starts the
    other. One word never counts ("Satipatthana" starts dozens of titles). A
    shared start of two words ("Buddhist Ethics") also starts unrelated books,
    so it counts only when the authors agree, or when the two words are the
    whole of both titles and the hit has no known author ("Collett 2009").
    A file name may lead with the cited author ("Neelis-ed-Early-Buddhist-
    Transmission…"); those leading words are skipped.
    """
    cited = _title_sequence(_unbracketed(title))
    for hit_title in names.titles:
        seq = _title_sequence(hit_title)
        named = author_named
        while seq and seq[0] in cited_authors and seq[0] not in cited[:1]:
            # The file name itself names the cited author ("Robert Sharf,
            # Buddhist Modernism.pdf").
            seq, named = seq[1:], True
        last_cut = bool(seq) and seq[-1] in names.cut
        # A cut that leaves a fragment too short to be a title word ("…in
        # Cu") still ends the title there; dropping it let "The Role of the
        # Brahmavihara in Cu" start any Brahmavihara title by the author.
        tail = _folded_words(hit_title)[-1:]
        if tail and tail[0] not in seq[-1:] and tail[0] not in _TITLE_STOPWORDS:
            if not tail[0].isdigit() and len(tail[0]) < 3:
                seq, last_cut = [*seq, tail[0]], True
        shorter = min(len(cited), len(seq))
        whole_pair = not names.authors and len(cited) == len(seq) == 2
        if shorter < 2 or (shorter < 3 and not (named or whole_pair)):
            continue
        if _starts_with(seq, cited, False):
            return True
        # A shorter hit title that is whole and has no author behind it is a
        # folder of parts ("Wisdom Of The Lotus Sutra"), not the cited part.
        if (last_cut or named) and _starts_with(cited, seq, last_cut):
            return True
    return False


def _library_hit_stats(text: str) -> dict[int, tuple[int, int]]:
    """{document_id: (distinct queries that returned it, best 1-based rank)}.

    Only `search-library-folders` blocks are ranked. A query is its search
    terms without flags, so one search re-run with another `--limit` counts once.
    """
    queries: dict[int, set[str]] = {}
    best: dict[int, int] = {}
    for block in _LIBRARY_SEARCH_BLOCK_RE.finditer(text):
        body = block.group(1)
        args = _re.search(r"^- args: `(.*)`$", body, _re.M)
        raw = args.group(1) if args else body[:40]
        query = _QUERY_FLAG_RE.sub("", " " + raw).strip().casefold()
        for rank, hit in enumerate(_logged_library_hits(body), start=1):
            doc_id = hit["document_id"]
            queries.setdefault(doc_id, set()).add(query)
            best[doc_id] = min(best.get(doc_id, rank), rank)
    return {d: (len(q), best[d]) for d, q in queries.items()}


_READ_LIBRARY_BLOCK_RE = _re.compile(
    r"^### \S+ · read-library\n(.*?)(?=^### |\Z)", _re.M | _re.S
)
_LIBRARY_REF_RE = _re.compile(r"""^\s*-\s*["']?(?:\d+\s*:\s*)?(.*?)["']?\s*$""")
_LIB_FOOTNOTE_DEF_RE = _re.compile(
    r"^\[\^((?:lib|calibre)-[^\]]*)\]:[ \t]*(.+)$", _re.M
)
_LIB_FOOTNOTE_MARK_RE = _re.compile(r"\[\^((?:lib|calibre)-[^\]]*)\]")
_UNREAD_FLAG_RE = _re.compile(
    r"snippet[- ]only|snippets? only|\bunread\b|\bnot (?:yet )?read\b|"
    r"could not (?:be )?(?:read|opened)",
    _re.I,
)
_SNIPPET_FLAG_RE = _re.compile(
    r"snippet[- ]only|snippets? only|could not (?:be )?(?:read|opened)", _re.I
)
# In the Not Used table any snippet mention marks a snippet-based rejection
# ("seen only as passing mentions in snippets", "Snippet showed ..."); in the
# body the word is ordinary narration and stays unflagged.
_REJECT_FLAG_RE = _re.compile(_UNREAD_FLAG_RE.pattern + r"|\bsnippets?\b", _re.I)
# Blaming the mount is a false claim about the text wherever it appears.
_MOUNT_FLAG_RE = _re.compile(r"\bunmounted\b|\bnot mounted\b", _re.I)


def _logged_library_docs(text: str) -> dict[int, dict]:
    """{document_id: hit} over every logged library result, fields merged.

    A `read-library` result logs the same `document_id` without the title
    and path a search hit holds; letting it replace the hit left the title
    matcher nothing to match.
    """
    docs: dict[int, dict] = {}
    for hit in _logged_library_hits(text):
        merged = {**hit, **docs.get(hit["document_id"], {})}
        # The latest extraction status wins: a `--retry-failed` refresh can
        # make a document readable later in the same run.
        if hit.get("extraction_status"):
            merged["extraction_status"] = hit["extraction_status"]
        docs[hit["document_id"]] = merged
    return docs


def _clean_citation(text: str) -> str:
    """A citation without wikilink brackets or emphasis marks."""
    text = _re.sub(r"\[\[([^\]|]*)(?:\|[^\]]*)?\]\]", r"\1", text)
    return text.replace("*", "").strip()


def _note_library_refs(note_text: str) -> list[str]:
    """Entries listed under `library_refs:` in the note's frontmatter.

    An old entry's `<n>:` prefix is dropped: the number is an index row id,
    not the book.
    """
    refs: list[str] = []
    lines = note_text.splitlines()
    # Only the opening frontmatter: a body example of a `library_refs:` list
    # is not the note's citations.
    if not lines or lines[0].rstrip() != "---":
        return refs
    in_refs = False
    for line in lines[1:]:
        if line.rstrip() == "---":
            break
        if line.startswith("library_refs:"):
            in_refs = True
            continue
        if in_refs:
            if not line.strip():
                continue
            if not line.startswith((" ", "-")):
                break
            match = _LIBRARY_REF_RE.match(line)
            if match and match.group(1).strip():
                refs.append(_clean_citation(match.group(1)))
    return refs


_FENCE_RE = _re.compile(r"^(```|~~~).*?^\1[^\n]*$", _re.M | _re.S)


def _note_footnotes(note_text: str) -> dict[str, str]:
    """{footnote label: citation} for the note's library footnotes.

    Fenced code is skipped: a format example is not a citation.
    """
    return {
        m.group(1): _clean_citation(m.group(2))
        for m in _LIB_FOOTNOTE_DEF_RE.finditer(_FENCE_RE.sub("", note_text))
    }


def _note_citations(note_text: str) -> list[str]:
    """The note's library citations: `library_refs` and library footnotes."""
    cites = _note_library_refs(note_text) + list(_note_footnotes(note_text).values())
    return list(dict.fromkeys(c for c in cites if c))


def _not_used_rows(note_text: str) -> list[tuple[str, str]]:
    """(row, first cell) for each data row of the Not Used tables."""
    rows: list[tuple[str, str]] = []
    for section in _NOT_USED_SECTION_RE.finditer(note_text):
        for line in section.group(0).splitlines():
            cells = line.strip().split("|")
            if len(cells) < 3 or not line.lstrip().startswith("|"):
                continue
            first = cells[1].strip()
            if not first or set(first) <= set("-: ") or first.lower() == "source":
                continue
            rows.append((line, _clean_citation(first)))
    return rows


# Characters of a book's indexed text searched for its cited title: a title
# page, a header and a contents list fit (the five probe hits sat at 0-1,074).
_OPENING_CHARS = 3000
# Words of that text that count as the title page (see _title_in_opening).
_TITLE_PAGE_WORDS = 60


class _IndexText:
    """Read-only look-ups of logged hits' text in the library index.

    A hit is found by its `source_path`: its `document_id` moves on a rebuild.
    The index is opened only when a citation needs it, and a missing or
    unreadable index makes every look-up come back empty.
    """

    def __init__(self, index: Path | None) -> None:
        self._index = index
        self._conn = None
        self._failed = False
        self._openings: dict[str, str] = {}

    def _connection(self):
        import sqlite3

        if self._conn is not None or self._failed:
            return self._conn
        index = self._index
        if index is None:
            from tools.library_folders import default_config

            index = default_config().index
        if index is None or not index.exists():
            self._failed = True
            return None
        try:
            self._conn = sqlite3.connect(f"file:{index}?mode=ro", uri=True)
        except sqlite3.Error:
            self._failed = True
        return self._conn

    def opening(self, hit: dict) -> str:
        """The hit's first words as ` w1 w2 … `, or "" when unknown."""
        import sqlite3

        path = hit.get("source_path")
        if not isinstance(path, str):
            return ""
        if path not in self._openings:
            conn = self._connection()
            text = ""
            if conn is not None:
                try:
                    row = conn.execute(
                        "SELECT substr(f.text, 1, ?) FROM documents d "
                        "JOIN document_fts f ON f.rowid = d.id "
                        "WHERE d.source_path = ?",
                        (_OPENING_CHARS, path),
                    ).fetchone()
                except sqlite3.Error:
                    row = None
                text = row[0] if row and row[0] else ""
            self._openings[path] = " " + " ".join(_folded_words(text)) + " "
        return self._openings[path]

    def close(self) -> None:
        if self._conn is not None:
            self._conn.close()
            self._conn = None


def _title_in_opening(citation: str, names: _HitNames, opening: str) -> bool:
    """Is the cited title printed on the hit's title page?

    For a file whose name holds no title ("prebish-article.pdf",
    "2008_LutzA_PlosOne{CompassionMeditation}.pdf"). Measured on 38 real
    look-ups: right ones sat within the first 60 words, while wrong ones were
    other books naming the title later, in an "Also by" list or a reference
    (word 91-418). So the title must have three or more title words, start
    within the first 60 words, and, when the citation names an author, that
    name must be on the same page; one-word titles ("Satipatthana") and
    generic phrases otherwise matched the author's other books.
    """
    words = opening.split()
    if not words:
        return False
    title, sure_authors, cited_authors = _split_citation(citation)
    if names.authors and sure_authors:
        if not _authors_agree(names.authors, sure_authors):
            return False
    page = set(words[: _TITLE_PAGE_WORDS * 2])
    if cited_authors and not _authors_agree(cited_authors, page):
        return False
    head = " " + " ".join(words[: _TITLE_PAGE_WORDS + 40]) + " "
    for form in (_unbracketed(title), _main_title(title)):
        phrase = _folded_words(form)
        if len(_title_words(form)) < 3:
            continue
        found = head.find(f" {' '.join(phrase)} ")
        if found != -1 and head[:found].count(" ") <= _TITLE_PAGE_WORDS:
            return True
    return False


def _hits_cited(
    citation: str,
    names: dict[int, _HitNames],
    docs: dict[int, dict],
    index_text: _IndexText | None,
) -> set[int]:
    """Logged hits a citation names: by name, else by the title in their text."""
    ids = {d for d, n in names.items() if library_title_matches(citation, n)}
    if ids or index_text is None:
        return ids
    cited_volumes = _volume_numbers(_split_citation(citation)[0], trailing=False)
    return {
        d
        for d, n in names.items()
        if not _volumes_conflict(cited_volumes, n)
        and _title_in_opening(citation, n, index_text.opening(docs[d]))
    }


def _hits_named_in_line(line: str, names: dict[int, _HitNames]) -> set[int]:
    """Hits a gate line names by title; file codes do not count here."""
    words = _word_set(line)
    seq = _line_sequence(line)
    return {
        d
        for d, n in names.items()
        if not n.words.isdisjoint(words) and _line_names_hit(words, n, seq, codes=False)
    }


def _read_under_own_author(
    citation: str, names: dict[int, _HitNames], read: set[int]
) -> bool:
    """Was a read hit this citation's book, credited to another author?

    Notes credit a translator ("— Bhikkhu Ñāṇamoli") where Calibre credits
    the author ("— Buddhaghosa"); the author check then rules out the copy
    that was read while an authorless copy still matches, and the gate asked
    for a book already read. Copies of one book count as that book.
    """
    title, dash, _ = citation.rpartition(" — ")
    if not dash or not title.strip():
        return False
    # Only when every copy the citation matches has no known author: a
    # citation that matched an edition by name (Bryant's Yoga Sutras) is not
    # read by reading another translator's edition (Beloved's).
    matched = [n for n in names.values() if library_title_matches(citation, n)]
    if not matched or any(n.authors for n in matched):
        return False
    for d in read:
        hit = names.get(d)
        if hit is None:
            continue
        own = " ".join(sorted(hit.authors))
        if library_title_matches(f"{title} — {own}" if own else title, hit):
            return True
    return False


def _book_label(hit: dict) -> str:
    cite_as = hit.get("cite_as")
    if isinstance(cite_as, str) and cite_as.strip():
        return cite_as
    title = str(hit.get("title") or hit.get("relative_path") or "")
    return title.rsplit("/", 1)[-1].rsplit(".", 1)[0] if "." in title else title


# Any heading level, trailing whitespace and CRLF: a missed match would count
# every rejected hit in the table as a citation and refuse the gate en masse.
# The section ends at the next heading of its own level or higher, so a
# `### Findings` after a `### ...Not Used` is still checked for citations.
_NOT_USED_SECTION_RE = _re.compile(
    r"^(#{2,4})[ \t]+Sources Investigated, Not Used[ \t]*\r?\n.*?"
    r"(?=^(?!\1#)#+[ \t]|\Z)",
    _re.M | _re.S | _re.I,
)


def unread_library_citations(
    note_text: str, dossier_text: str, index: Path | None = None
) -> dict:
    """Library books the note cites, or calls unreadable, without reading them.

    A note names a book by title and author; the match to the run's logged
    hits is by title (`library_title_matches`), and copies of one book count
    as that book, so reading any copy reads it. Only books the dossier shows
    with successfully extracted text count: their full text is in the index
    whether or not the source volume is mounted, so `read-library` can always
    read them. A book whose extraction failed is exempt (its gap is real), and
    a run with no library hits logged checks nothing.

    The "Sources Investigated, Not Used" table is skipped for citations and
    snippet-only flags: it names every rejected hit (scratch-check-coverage
    asks for that), and rejecting a tangential hit on its snippet is triage,
    not a citation. Over 8 real runs that table held 9-55 books each, against
    2-4 `library_refs`. A line there that blames an unmounted volume is still
    flagged — that is the false claim this catches. A row there that rejects a
    readable book as not read or on its snippet (any mention of "snippet") is
    reported under `rejected_unread` until one successful `read-library` call
    has looked at it: a rejection needs one look, not a full reading (0-5
    such rows in most of 57 real runs, up to 26 in one).

    Each list holds `{"book": <title>, "read_library": [<document_id>, …]}`:
    the title to fix in the note, and the ids this run can pass to
    `read-library`. The ids are handles inside this run only; a note never
    carries them.
    """
    from tools.library_folders import extraction_succeeded

    empty: dict = {
        "cited_not_read": [],
        "flagged_unread_but_readable": [],
        "rejected_unread": [],
    }
    docs = _logged_library_docs(dossier_text)
    if not docs:
        return empty
    readable = {
        d
        for d, hit in docs.items()
        if extraction_succeeded(str(hit.get("extraction_status") or ""))
    }
    read: set[int] = set()
    for block in _READ_LIBRARY_BLOCK_RE.finditer(dossier_text):
        for hit in _logged_library_hits(block.group(1)):
            if hit.get("ok") is True:
                read.add(hit["document_id"])
    names = {d: _HitNames(hit) for d, hit in docs.items()}
    index_text = _IndexText(index)
    footnotes = _note_footnotes(note_text)

    def named_in(line: str) -> set[int]:
        ids = _hits_named_in_line(line, names)
        for label in _LIB_FOOTNOTE_MARK_RE.findall(line):
            if label in footnotes and not line.lstrip().startswith(f"[^{label}]:"):
                ids |= _hits_cited(footnotes[label], names, docs, index_text)
        return ids

    def entry(book: str, ids: set[int]) -> dict:
        return {"book": book, "read_library": sorted(ids & readable)}

    try:
        body = _NOT_USED_SECTION_RE.sub("", note_text)
        cited_not_read = []
        for citation in _note_citations(body):
            ids = _hits_cited(citation, names, docs, index_text)
            if (
                ids & readable
                and not ids & read
                and not _read_under_own_author(citation, names, read)
            ):
                cited_not_read.append(entry(citation, ids))

        flagged: dict[str, set[int]] = {}
        for line in note_text.splitlines():
            if _MOUNT_FLAG_RE.search(line):
                for d in named_in(line) & readable:
                    flagged.setdefault(_book_label(docs[d]), set()).add(d)
        # "Snippet-only" is a claim about the run; "not read" and "unread" are
        # also ordinary English ("Gombrich does not read anattā as …"), so they
        # flag only a book this run did not read.
        for line in body.splitlines():
            if not _UNREAD_FLAG_RE.search(line) or _MOUNT_FLAG_RE.search(line):
                continue
            strong = _SNIPPET_FLAG_RE.search(line)
            for d in named_in(line) & readable:
                if strong or d not in read:
                    flagged.setdefault(_book_label(docs[d]), set()).add(d)

        rejected_unread = []
        for row, first_cell in _not_used_rows(note_text):
            if not _REJECT_FLAG_RE.search(row):
                continue
            # The first cell is what the row rejects; a book named only in the
            # reason ("repeats Bodhi's …[^lib-3]") is a comparison, not the
            # rejection. One row may reject several books ("A — X; B — Y"):
            # each part is checked with its own footnote markers only.
            cell = next((c for c in row.split("|")[1:] if c.strip()), first_cell)
            for part in [p.strip() for p in cell.split(";") if p.strip()]:
                ids = named_in(part) | _hits_cited(
                    _clean_citation(_LIB_FOOTNOTE_MARK_RE.sub("", part)),
                    names,
                    docs,
                    index_text,
                )
                label = _clean_citation(_LIB_FOOTNOTE_MARK_RE.sub("", part))
                if (
                    ids & readable
                    and not ids & read
                    and not _read_under_own_author(label, names, read)
                ):
                    rejected_unread.append(entry(label, ids))
    finally:
        index_text.close()
    return {
        "cited_not_read": cited_not_read,
        "flagged_unread_but_readable": [
            entry(book, ids) for book, ids in sorted(flagged.items())
        ],
        "rejected_unread": rejected_unread,
    }


def scratch_check_coverage(
    scratch: Path | None = None,
    note: Path | None = None,
    index: Path | None = None,
) -> dict:
    """Flag library-folder hits gathered but mentioned nowhere in the final note.

    Advisory, not gating: a 2026-07-05 audit of 6 recent notes found canon/web
    hits are dominated by stem-search noise and near-duplicate passages that
    the Devil's Advocate / rejection-table process already self-curates well
    (62-87% citation rate against the note's own funnel, with reasons logged
    for the rest). The one confirmed gap was a library document with an
    on-topic snippet that never appeared in the note's citations or its
    Sources Investigated, Not Used table. This checks for that pattern by
    title: a hit is accounted for when a `library_refs` entry, a library
    footnote or a Not Used row names it (`library_title_matches`), or a note
    line holds its title. Name each rejected book in its Not Used row to
    clear it. Index numbers prove nothing here: they change on every rebuild.

    `cited_not_gathered` lists citations that name no hit logged this run:
    a book cited from memory or carried from an older note. Advisory.

    Broad sweeps leave dozens of tangential hits unaccounted (median 42 per
    dossier over 73 real runs), which buried the one real miss (issue #89).
    So `unaccounted` is ordered by how likely a hit is to matter — returned by
    more distinct queries first, then by best rank — and only the first ten
    keep their path and snippet. The ordering helps but does not decide: in
    those dossiers a book the note did cite, removed and re-ranked among more
    than ten unaccounted, landed in the first ten 49% of the time against 35%
    for random order (1,416 trials). `note` checks a draft instead of the
    recorded vault note, so a miss can be pulled in before the Phase 6 review.
    """
    path = scratch or _scratch_path()
    if not path.exists():
        return {"ok": False, "error": f"scratch not initialised: {path}"}
    text = path.read_text(encoding="utf-8")

    if note is not None:
        note_path = note
    else:
        note_match = _re.search(r"^\*\*Vault note:\*\*\s*(.+)$", text, _re.M)
        note_path_str = note_match.group(1).strip() if note_match else ""
        if not note_path_str or note_path_str == "<set at Phase 7>":
            return {
                "ok": False,
                "error": "no vault note recorded — run scratch-set-note first, "
                "or pass --note <draft>",
            }
        note_path = Path(note_path_str)
    if not note_path.exists():
        return {"ok": False, "error": f"note not found: {note_path}"}
    note_text = note_path.read_text(encoding="utf-8")

    docs = _logged_library_docs(text)
    names = {d: _HitNames(hit) for d, hit in docs.items()}
    index_text = _IndexText(index)
    accounted: set[int] = set()
    cited_not_gathered = []
    try:
        for citation in _note_citations(note_text):
            ids = _hits_cited(citation, names, docs, index_text)
            if ids:
                accounted |= ids
            else:
                cited_not_gathered.append(citation)
        for _row, first_cell in _not_used_rows(note_text):
            accounted |= _hits_cited(first_cell, names, docs, index_text)
    finally:
        index_text.close()
    # Citation lines were matched above, with the author and volume checks;
    # the looser prose pass would credit a sibling volume through them.
    lines = [
        (_word_set(line), _line_sequence(line))
        for line in note_text.splitlines()
        if line.strip() and not _LIB_FOOTNOTE_DEF_RE.match(line)
    ]
    for doc_id, hit_names in names.items():
        if doc_id in accounted:
            continue
        if any(
            (not hit_names.words.isdisjoint(words) or hit_names.file_code in words)
            and _line_names_hit(words, hit_names, seq)
            for words, seq in lines
        ):
            accounted.add(doc_id)

    unaccounted = [
        {
            "document_id": doc_id,
            "title": hit.get("title"),
            "cite_as": _book_label(hit),
            "relative_path": hit.get("relative_path") or "",
            "snippet": (hit.get("snippet") or "")[:200],
        }
        for doc_id, hit in sorted(docs.items())
        if doc_id not in accounted
    ]
    stats = _library_hit_stats(text)
    unaccounted.sort(
        key=lambda d: (
            -stats.get(d["document_id"], (0, 0))[0],
            stats.get(d["document_id"], (0, 10**6))[1],
            d["document_id"],
        )
    )
    for position, entry in enumerate(unaccounted):
        queries, best_rank = stats.get(entry["document_id"], (0, 0))
        if position < _COVERAGE_REVIEW_FIRST:
            entry["queries"] = queries
            entry["best_rank"] = best_rank or None
        else:
            unaccounted[position] = {
                "document_id": entry["document_id"],
                "cite_as": entry["cite_as"],
            }

    return {
        "ok": not unaccounted,
        "note": str(note_path),
        "library_hits_gathered": len(docs),
        "unaccounted_count": len(unaccounted),
        "unaccounted": unaccounted,
        "cited_not_gathered": cited_not_gathered,
    }


_DIGEST_SNIPPET_KEYS = (
    "english",
    "snippet",
    "translation_en",
    "abstract",
    "quote",
    "pali",
)
_DIGEST_REF_KEYS = (
    "ref",
    "url",
    "openalex_id",
    "video_id",
    "path",
    "document_id",
    "id",
)


def _digest_ref(hit: dict) -> str:
    if hit.get("book_code") and hit.get("paranum") is not None:
        return f"{hit['book_code']}:{hit['paranum']}"
    for key in ("title", "relative_path", *_DIGEST_REF_KEYS):
        if hit.get(key):
            return str(hit[key])
    return "?"


def _digest_snippet(hit: dict, width: int) -> str:
    for key in _DIGEST_SNIPPET_KEYS:
        value = hit.get(key)
        if isinstance(value, str) and value.strip():
            return _re.sub(r"\s+", " ", value).strip()[:width]
    return ""


def _digest_results(payload: str, top: int, width: int) -> list[str]:
    """Short lines for one auto-logged JSON result: a count and the first hits."""
    try:
        data = json.loads(payload)
    except ValueError:
        return ["  (results are not valid JSON; read the entry in the dossier)"]
    if isinstance(data, dict) and isinstance(data.get("hits"), list):
        head = f"  total_hits={data.get('total_hits', len(data['hits']))}"
        data = data["hits"]
    elif isinstance(data, dict):
        keys = ", ".join(
            f"{k}({len(v)})" if isinstance(v, (list, dict)) else k
            for k, v in list(data.items())[:12]
        )
        return [f"  keys: {keys}"]
    else:
        head = ""
    if not isinstance(data, list):
        return []
    out = [head] if head else []
    for hit in data[:top]:
        if not isinstance(hit, dict):
            out.append(f"  · {str(hit)[:width]}")
            continue
        snippet = _digest_snippet(hit, width)
        out.append(f"  · {_digest_ref(hit)}" + (f" — {snippet}" if snippet else ""))
    if len(data) > top:
        out.append(f"  … {len(data) - top} more in the dossier entry")
    return out


def scratch_digest(
    scratch: Path | None = None,
    slug: str | None = None,
    phase: str | None = None,
    top: int = 2,
    width: int = 90,
) -> str:
    """A short, line-numbered digest of a dossier, to read instead of the whole file.

    The dossier stores every hit in full, so a long run reaches megabytes; reading
    it whole fills the context and has cost runs hours (issue #109). The digest
    keeps what the agent wrote itself (summaries, gates) in full, and shows each
    auto-logged call as one header line, a hit count and its first `top` hits.
    Every entry carries `L<line>`: `sed -n '<line>,+40p' <dossier>` reads it whole.
    """
    path = scratch or _scratch_path(slug)
    lines = path.read_text(encoding="utf-8").splitlines()
    wanted = _PHASE_ALIASES.get(str(phase).strip().lower(), phase) if phase else None
    out: list[str] = []
    counts: dict[str, int] = {}
    current = ""
    current_id = ""
    i = 0
    n = len(lines)
    while i < n:
        line = lines[i]
        if line.startswith("## "):
            current = line[3:].strip()
            m = _re.match(r"Phase\s+(\S+)", current)
            current_id = m.group(1) if m else ""
            show = wanted is None or current_id == wanted
            if show:
                out.append(f"\n## {current}")
            i += 1
            continue
        if not line.startswith("### "):
            i += 1
            continue
        end = i + 1
        while end < n and not lines[end].startswith(("### ", "## ")):
            end += 1
        entry = lines[i:end]
        i = end
        if not current.startswith("Phase") or (
            wanted is not None and current_id != wanted
        ):
            continue
        title = entry[0][4:].strip()
        if title.startswith("PHASE") and "EXIT GATE" in title:
            out.append(f"L{i - len(entry) + 1} gate: {title}")
            continue
        parts = title.split(" · ", 1)
        cmd = parts[1] if len(parts) == 2 else title
        counts[cmd] = counts.get(cmd, 0) + 1
        meta = [
            e[2:].strip()
            for e in entry[1:]
            if e.startswith(("- args:", "- hits:", "- summary:"))
        ]
        summary = [m for m in meta if m.startswith("summary:")]
        brief = [m for m in meta if not m.startswith("summary:")]
        out.append(f"L{i - len(entry) + 1} {cmd} · " + " · ".join(brief))
        for s in summary:
            out.append("  " + s[:1500])
        if "```json" in entry:
            start = entry.index("```json") + 1
            close = next(
                (k for k in range(start, len(entry)) if entry[k] == "```"), None
            )
            if close is not None:
                out.extend(_digest_results("\n".join(entry[start:close]), top, width))
    size_kb = path.stat().st_size // 1024
    head = [
        f"# Digest of {path.name} — {size_kb} KB, {len(lines)} lines in the dossier",
        "Entries by command: "
        + ", ".join(f"{c} {k}" for c, k in sorted(counts.items(), key=lambda x: -x[1])),
        "Read one entry whole: sed -n 'L,+40p' <dossier> with its L number.",
    ]
    return "\n".join(head + out) + "\n"


def scratch_resume(slug: str | None = None, scratch: Path | None = None) -> dict:
    """Print the last gate written and suggest the next phase."""
    path = scratch or _scratch_path(slug)
    if not path.exists():
        return {"ok": False, "error": f"scratch not found: {path}"}
    text = path.read_text(encoding="utf-8")
    last = None
    for pid, title, _ in _SCRATCH_PHASES:
        if _gate_marker(pid) in text:
            last = {"phase": pid, "title": title}
    # The first phase still without a gate, not the one after the highest gate:
    # parallel gather phases can be gated out of order (issue #133).
    thematic = _run_class(text) == "thematic"
    next_phase = next(
        (
            pid
            for pid, _, _ in _SCRATCH_PHASES
            if _gate_marker(pid) not in text
            and not (thematic and pid in _AUTO_SKIP_PHASES)
        ),
        None,
    )
    _write_state(path, next_phase)
    return {"ok": True, "path": str(path), "last_gate": last, "next_phase": next_phase}


def _maybe_autolog(cmd: str, argv: list[str], result_obj) -> None:
    """Append a one-entry log for this helper invocation to the active scratch.

    VICAYA_SCRATCH and VICAYA_PHASE are checked first; the state-file is read
    only when they do not fully answer the lookup, avoiding the ps spawn on
    the env-pinned path. Failures are swallowed — auto-logging must never break
    a search.
    """
    scratch_env = os.environ.get("VICAYA_SCRATCH")
    phase_env = os.environ.get("VICAYA_PHASE")
    if scratch_env and phase_env:
        scratch, phase = scratch_env, phase_env
    else:
        state = _read_state()
        scratch = scratch_env or state.get("scratch")
        phase = phase_env or state.get("phase") or "?"
    pinned = bool(phase_env)
    phase = _PHASE_ALIASES.get(str(phase).strip().lower(), phase)
    if not scratch:
        return
    if cmd in {
        "scratch-init",
        "scratch-log",
        "scratch-gate",
        "scratch-set-note",
        "scratch-self-audit",
        "scratch-verify",
        "scratch-resume",
        "scratch-which",
        "lookup-book",
    }:
        return
    try:
        import datetime as _dt
        import json as _json
        from dataclasses import asdict as _asdict, is_dataclass as _is_dc

        path = Path(scratch)
        if not path.exists():
            return
        ts = _dt.datetime.now().isoformat(timespec="seconds")
        hits: int | None = None
        if isinstance(result_obj, list):
            hits = len(result_obj)
        body = [f"### {ts} · {cmd}"]
        if not pinned:
            # No explicit VICAYA_PHASE: phase came from the shared per-run
            # pointer, which a sibling sub-agent's scratch-gate call can
            # advance mid-flight. Flag it so a spot-check can spot drift
            # instead of silently trusting a possibly-stale phase.
            body.append(
                "- phase-source: run-pointer (not pinned via VICAYA_PHASE — "
                "verify this lands under the calling agent's assigned phase)"
            )
        if argv:
            body.append(f"- args: `{' '.join(argv)}`")
        if hits is not None:
            body.append(f"- hits: {hits}")

        def _default(o):
            if _is_dc(o) and not isinstance(o, type):
                return _asdict(o)
            return str(o)

        try:
            payload = _json.dumps(
                result_obj, ensure_ascii=False, indent=2, default=_default
            )
            body.append("- results:")
            body.append("```json")
            body.append(payload)
            body.append("```")
        except Exception:
            pass
        if phase in _PHASE_INDEX:
            _append_under_phase(path, phase, "\n".join(body))
        else:
            # Unknown phase: append at end of file.
            with open(path, "a", encoding="utf-8") as fh:
                fh.write("\n" + "\n".join(body) + "\n")
    except Exception:
        return
