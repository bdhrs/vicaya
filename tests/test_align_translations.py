"""Tests for the translation aligner.

Builds a tiny offline Bilara + EBC tree in a tmp dir so the deterministic
locate/align/render logic is covered without touching real data.
"""

from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tools.align_translations import (  # noqa: E402
    _ebc_translator_files,
    align,
    locate_segments,
    render,
)

pytestmark = pytest.mark.skipif(
    shutil.which("grep") is None, reason="grep not available"
)


def _write_json(path: Path, data: dict[str, str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


@pytest.fixture
def sc_root(tmp_path: Path) -> Path:
    root = tmp_path / "sc"
    base = root / "sc_bilara_data"
    _write_json(
        base / "root/pli/ms/sutta/mn/mn1_root-pli-ms.json",
        {"mn1:0.1": "Majjhima Nikāya 1 ", "mn1:52.1": "sabbe dhammā anattā "},
    )
    _write_json(
        base / "translation/en/sujato/sutta/mn/mn1_translation-en-sujato.json",
        {"mn1:0.1": "Middle Discourses 1 ", "mn1:52.1": "all things are not-self "},
    )
    # A second sutta sharing the word "anattā" → makes a bare word ambiguous.
    _write_json(
        base / "root/pli/ms/sutta/sn/sn22/sn22.59_root-pli-ms.json",
        {"sn22.59:7.1": "rūpaṁ anattā "},
    )
    return root


@pytest.fixture
def ebc_vault(tmp_path: Path) -> Path:
    vault = tmp_path / "ebc"
    texts = vault / "+Suttas" / "Sutta Texts"
    for translator, slug in (("Bodhi", "bodhi"), ("Anīgha", "anigha")):
        f = texts / translator / "mn-{}".format(slug) / "mn1-{}.md".format(slug)
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_text("# MN1\nbody\n", encoding="utf-8")
    return vault


def test_locate_parses_keys_and_uids(sc_root: Path) -> None:
    found = locate_segments("anattā", sc_root=sc_root)
    assert set(found) == {"mn1", "sn22.59"}
    assert found["mn1"].seg_keys == ["mn1:52.1"]
    assert found["mn1"].file_stem == "mn1"
    assert found["sn22.59"].seg_keys == ["sn22.59:7.1"]


def test_distinctive_phrase_builds_table(sc_root: Path, ebc_vault: Path) -> None:
    result = align("sabbe dhammā anattā", sc_root=sc_root, ebc_vault=ebc_vault)
    assert result.status == "ok"
    assert result.uid == "mn1"
    labels = {label for label, _ in result.rows}
    assert "**Pāḷi**" in labels
    assert "Sujato (Bilara)" in labels
    pali = dict(result.rows)["**Pāḷi**"]
    assert "sabbe dhammā anattā" in pali
    assert dict(result.rows)["Sujato (Bilara)"] == "all things are not-self"


def test_common_word_is_ambiguous(sc_root: Path, ebc_vault: Path) -> None:
    result = align("anattā", sc_root=sc_root, ebc_vault=ebc_vault)
    assert result.status == "ambiguous"
    assert result.candidate_uids == ["mn1", "sn22.59"]
    assert result.rows == []
    assert "AMBIGUOUS" in render(result)


def test_scope_resolves_ambiguity(sc_root: Path, ebc_vault: Path) -> None:
    result = align("anattā", scope="MN1", sc_root=sc_root, ebc_vault=ebc_vault)
    assert result.status == "ok"
    assert result.uid == "mn1"
    assert result.seg_keys == ["mn1:52.1"]


def test_scope_not_containing_phrase(sc_root: Path, ebc_vault: Path) -> None:
    result = align("sabbe dhammā anattā", scope="SN22.59", sc_root=sc_root, ebc_vault=ebc_vault)
    assert result.status == "not_in_scope"
    assert "mn1" in result.candidate_uids


def test_ebc_discovery_labels_translators(sc_root: Path, ebc_vault: Path) -> None:
    result = align("sabbe dhammā anattā", sc_root=sc_root, ebc_vault=ebc_vault)
    translators = {t for t, _ in result.ebc_files}
    assert translators == {"Bodhi", "Anīgha"}
    rendered = render(result)
    assert "EBC sources to read for mn1:" in rendered


def test_ebc_discovery_excludes_sibling_numbers(ebc_vault: Path) -> None:
    texts = ebc_vault / "+Suttas" / "Sutta Texts"
    decoy = texts / "Bodhi" / "mn-bodhi" / "mn10-bodhi.md"
    decoy.write_text("# MN10\n", encoding="utf-8")
    files = _ebc_translator_files("mn1", ebc_vault)
    paths = {p.name for _, p in files}
    assert "mn1-bodhi.md" in paths
    assert "mn10-bodhi.md" not in paths


def test_niggahita_folds_to_sc_form(tmp_path: Path) -> None:
    root = tmp_path / "sc"
    _write_json(
        root / "sc_bilara_data/root/pli/ms/sutta/an/an4/an4.31_root-pli-ms.json",
        {"an4.31:1.1": "cattāri cakkāni, yehi samannāgatānaṁ devamanussānaṁ "},
    )
    # Query typed CST-style with dot-below ṃ still hits SC's dot-above ṁ.
    found = locate_segments("samannāgatānaṃ", sc_root=root)
    assert set(found) == {"an4.31"}
    assert found["an4.31"].seg_keys == ["an4.31:1.1"]


def test_case_insensitive_match(tmp_path: Path) -> None:
    root = tmp_path / "sc"
    _write_json(
        root / "sc_bilara_data/root/pli/ms/sutta/an/an4/an4.31_root-pli-ms.json",
        {"an4.31:1.1": "“Cattārimāni, bhikkhave, cakkāni, "},
    )
    found = locate_segments("cattārimāni", sc_root=root)  # lowercase vs capitalised
    assert set(found) == {"an4.31"}
    assert found["an4.31"].seg_keys == ["an4.31:1.1"]


def test_range_file_verse_aligns(tmp_path: Path) -> None:
    # Verse collections store many suttas in one range-named file: dhp279 lives
    # in dhp273-289_*.json. The table must still fill, not silently empty out.
    root = tmp_path / "sc"
    base = root / "sc_bilara_data"
    _write_json(
        base / "root/pli/ms/sutta/kn/dhp/dhp273-289_root-pli-ms.json",
        {"dhp278:1": "sabbe saṅkhārā aniccā ", "dhp279:1": "sabbe dhammā anattā "},
    )
    _write_json(
        base / "translation/en/sujato/sutta/kn/dhp/dhp273-289_translation-en-sujato.json",
        {"dhp278:1": "all conditions are impermanent ", "dhp279:1": "all things are not-self "},
    )
    result = align("sabbe dhammā anattā", sc_root=root, ebc_vault=None)
    assert result.status == "ok"
    assert result.uid == "dhp279"
    assert result.seg_keys == ["dhp279:1"]
    cells = dict(result.rows)
    assert cells["**Pāḷi**"] == "sabbe dhammā anattā"
    assert cells["Sujato (Bilara)"] == "all things are not-self"


def test_not_found(sc_root: Path, ebc_vault: Path) -> None:
    result = align("zzznotaword", sc_root=sc_root, ebc_vault=ebc_vault)
    assert result.status == "not_found"
    assert "No Bilara root match" in render(result)
