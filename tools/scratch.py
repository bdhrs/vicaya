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


_SCRATCH_DIR = Path(__file__).resolve().parents[1] / "data" / "scratch"

# Phases auto-skipped for thematic (non-sutta-anchored) runs.
_AUTO_SKIP_PHASES = ("2.5", "3b")


@functools.cache
def _run_key() -> str:
    """A stable per-run identifier shared by every tool call in one research run.

    Keyed to the agent process — the parent of the POSIX session leader. Every
    helper subprocess an agent launches in one run resolves to the same key;
    two parallel runs (whether Claude, Gemini, opencode, or any other agent)
    have different agent processes and therefore different keys. This is what
    makes per-run scratch state collision-proof without env vars, exports, or
    inline pinning: there is no single shared pointer to hijack.

    Set VICAYA_SCRATCH (and VICAYA_PHASE) as a deterministic override: those
    env pins are checked before the state-file is read, so no ps spawn occurs
    on the env-pinned path.
    """
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
        "Phase 3b — Sanskrit",
        [
            "GRETIL searched where comparative-religion angle applies (or 'not applicable')",
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
_CONTENT_PHASES = ("1", "2", "2.5", "3", "3b", "4", "4b", "4c")


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


def _phase_content_issue(body: str) -> str | None:
    """Classify a gated phase's body: 'placeholder', 'empty', or None (has evidence).

    Auto-skipped phases (gate marked AUTO-SKIPPED) are legitimately empty. Real
    evidence is any logged block (`### <ts> · tool`) or hand-written note under
    the heading — the exit-gate block alone does not count, so a crashed agent
    that gated a phase without searching is caught instead of passing verify.
    """
    if "AUTO-SKIPPED" in body:
        return None
    low = body.lower()
    for pat in _PLACEHOLDER_PATTERNS:
        if pat in low:
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
    # Verify every prior phase has a gate.
    for prev_id, prev_title, prev_expected in _SCRATCH_PHASES[:idx]:
        if _gate_marker(prev_id) not in text:
            return {
                "ok": False,
                "missing_phase": prev_id,
                "missing_title": prev_title,
                "expected_evidence": prev_expected,
                "message": (
                    f"cannot write Phase {phase} gate: Phase {prev_id} "
                    f"({prev_title}) gate is missing — "
                    f"run scratch-gate {prev_id} first"
                ),
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
    # For gather phases, require at least one real logged entry before gating.
    # Phase 0 uses header fields (no tool logs); phases 5–7 hold draft/synthesis
    # content — both are exempt. AUTO-SKIPPED thematic phases are also exempt.
    if phase in _CONTENT_PHASES:
        body = _phase_body(text, phase)
        if "AUTO-SKIPPED" not in body and _phase_content_issue(body) == "empty":
            return {
                "ok": False,
                "phase": phase,
                "reason": "no logged evidence",
                "message": (
                    f"Phase {phase} gate refused: the phase section has no logged "
                    f"tool calls — run the searches first, then gate. "
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
    return {"ok": True, "phase": phase, "title": title}


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
    note = Path(note_path).expanduser()
    if not note.exists() and not note.is_absolute():
        vault = os.environ.get("VICAYA_VAULT_PATH")
        if vault:
            candidate = Path(vault).expanduser() / note_path
            if candidate.exists():
                note = candidate
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
    """Verify gather phases are gated AND carry real content.

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


def scratch_resume(slug: str | None = None, scratch: Path | None = None) -> dict:
    """Print the last gate written and suggest the next phase."""
    path = scratch or _scratch_path(slug)
    if not path.exists():
        return {"ok": False, "error": f"scratch not found: {path}"}
    text = path.read_text(encoding="utf-8")
    last = None
    next_phase = _SCRATCH_PHASES[0][0]
    for i, (pid, title, _) in enumerate(_SCRATCH_PHASES):
        if _gate_marker(pid) in text:
            last = {"phase": pid, "title": title}
            next_phase = _next_worked_phase(text, i)
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
