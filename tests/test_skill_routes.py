"""Guard: every heading in the staged routers' route lists exists in SKILL.md.

The staged skills (vicaya-0-scope … vicaya-3-complete) extract sections from
skill/vicaya/SKILL.md by exact heading text and hard-stop when a heading is
missing — so renaming a SKILL.md heading silently breaks a stage. This test
fails at commit time instead of at run time.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

SKILL_DIR = Path(__file__).resolve().parent.parent / "skill"
CANONICAL = SKILL_DIR / "vicaya" / "SKILL.md"
ROUTERS = [
    "vicaya-0-scope",
    "vicaya-1-gather",
    "vicaya-2-synthesize-review",
    "vicaya-3-complete",
]

ROUTE_ITEM = re.compile(r"^- (`+)(.+?)\1$")


def routed_headings(router: str) -> list[str]:
    text = (SKILL_DIR / router / "SKILL.md").read_text(encoding="utf-8")
    in_route_list = False
    headings = []
    for line in text.splitlines():
        if line.startswith("## "):
            in_route_list = line.strip() == "## Route List"
            continue
        if in_route_list:
            m = ROUTE_ITEM.match(line.strip())
            if m:
                headings.append(m.group(2))
    return headings


def canonical_headings() -> set[str]:
    headings = set()
    in_fence = False
    for line in CANONICAL.read_text(encoding="utf-8").splitlines():
        if line.lstrip().startswith("```"):
            in_fence = not in_fence
            continue
        if not in_fence and line.startswith("#"):
            headings.add(line.rstrip())
    return headings


@pytest.mark.parametrize("router", ROUTERS)
def test_route_list_headings_exist_in_skill_md(router):
    routed = routed_headings(router)
    assert routed, f"{router}: no route-list items parsed"
    missing = [h for h in routed if h not in canonical_headings()]
    assert not missing, (
        f"{router} routes headings missing from skill/vicaya/SKILL.md: {missing}"
    )


def test_scratch_hand_edit_sequencing_rule_in_routed_section():
    # This rule was silently lost once in a doc restructure (TODO #43); it must
    # live inside "## Research scratchpad" because all four routers route that
    # section, so every staged run reads it.
    text = CANONICAL.read_text(encoding="utf-8")
    start = text.index("## Research scratchpad")
    end = text.index("\n## ", start + 1)
    section = text[start:end]
    assert "never hand-edit the scratch in the same parallel batch" in section
