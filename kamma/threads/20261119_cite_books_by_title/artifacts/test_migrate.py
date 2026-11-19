"""Tests for the one-off library citation migration, from real note lines.

Run: uv run pytest kamma/threads/20261119_cite_books_by_title/artifacts/test_migrate.py -q
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from migrate_library_citations import Report, migrate_text  # noqa: E402

SATI = "Satipaṭṭhāna: The Direct Path to Realization — Bhikkhu Anālayo"
MAGADHA = "Greater Magadha: Studies in the Culture of Early India — Johannes Bronkhorst"


def _resolver(table: dict[int, str]):
    return lambda n: [table[n]] if n in table else []


def _body(line: str, table: dict[int, str]) -> tuple[str, Report]:
    report = Report()
    text = "---\ntopic: x\n---\n" + line + "\n"
    out = migrate_text(text, _resolver(table), report)
    return out.split("---\n", 2)[2].rstrip("\n"), report


def test_quoted_library_ref_loses_its_number():
    text = '---\nlibrary_refs:\n  - "905: A History of Mindfulness — Bhikkhu Sujato"\n---\n'
    assert migrate_text(text, _resolver({})) == (
        '---\nlibrary_refs:\n  - "A History of Mindfulness — Bhikkhu Sujato"\n---\n'
    )


def test_unquoted_library_ref_loses_its_number_and_is_quoted():
    text = (
        "---\nlibrary_refs:\n  - 15563: Jhana Training Manual — Tomas Piskacek (2025)\n"
        "  - 2655: The Attainment of Cessation of Perception and Feeling — Keren Arbel\n"
        "web_refs:\n  - https://x\n---\n"
    )
    assert migrate_text(text, _resolver({})) == (
        '---\nlibrary_refs:\n  - "Jhana Training Manual — Tomas Piskacek (2025)"\n'
        '  - "The Attainment of Cessation of Perception and Feeling — Keren Arbel"\n'
        "web_refs:\n  - https://x\n---\n"
    )


def test_footnote_label_with_suffix_is_renumbered_with_its_marker():
    # 2026-05-27 pali-prosody-study-guide, lines 381 and 770.
    text = (
        "---\ntopic: x\n---\n"
        "*Vuttodaya* v. 117 says it more compactly:[^calibre-2917-v117]\n\n"
        "[^calibre-2917-v117]: Vuttodaya v. 117 — db: e0808n_nrf, paranum 117. "
        "Translation by Ānandajoti Bhikkhu (#2917).\n"
    )
    out = migrate_text(text, _resolver({2917: "Vuttodaya — Ānandajoti Bhikkhu"}))
    assert out == (
        "---\ntopic: x\n---\n"
        "*Vuttodaya* v. 117 says it more compactly:[^lib-1]\n\n"
        "[^lib-1]: Vuttodaya v. 117 — db: e0808n_nrf, paranum 117. "
        "Translation by Ānandajoti Bhikkhu.\n"
    )


def test_labels_are_numbered_by_first_use():
    text = (
        "---\ntopic: x\n---\nA.[^calibre-7304] B.[^calibre-223] C.[^calibre-7304]\n\n"
        "[^calibre-223]: [[On Meditation]] — Ajahn Chah\n"
        "[^calibre-7304]: [[The Meditative Dynamics]] — X\n"
    )
    out = migrate_text(text, _resolver({}))
    assert "A.[^lib-1] B.[^lib-2] C.[^lib-1]" in out
    assert "[^lib-2]: [[On Meditation]]" in out and "[^lib-1]: [[The Meditative" in out


def test_number_beside_its_title_is_deleted():
    line, report = _body(
        "- Mahasi Sayadaw, *Dhammacakkappavattana Sutta* (Calibre #634)",
        {634: "Dhammacakkappavattana Sutta — Mahasi Sayadaw"},
    )
    assert line == "- Mahasi Sayadaw, *Dhammacakkappavattana Sutta*"
    assert report.actions["number deleted beside its title"] == 1


def test_grouped_copies_beside_their_title_are_deleted():
    line, _ = _body(
        "Anālayo, Bhikkhu. *Satipaṭṭhāna: The Direct Path to Realization*. "
        "Birmingham: Windhorse Publications, 2003. (Calibre #763, #434, #436, #437, "
        "#438, #440)",
        {n: SATI for n in (763, 434, 436, 437, 438, 440)},
    )
    assert line == (
        "Anālayo, Bhikkhu. *Satipaṭṭhāna: The Direct Path to Realization*. "
        "Birmingham: Windhorse Publications, 2003."
    )


def test_doc_number_beside_a_calibre_number_is_deleted_too():
    line, _ = _body(
        "[^calibre-5853]: [[Greater Magadha: Studies in the Culture of Early India]] "
        "— Johannes Bronkhorst (Calibre #5260, doc 5853)",
        {5260: MAGADHA, 5853: MAGADHA},
    )
    assert line == (
        "[^lib-1]: [[Greater Magadha: Studies in the Culture of Early India]] "
        "— Johannes Bronkhorst"
    )


def test_grouped_numbers_without_a_title_become_titles():
    line, report = _body(
        "| Ñāṇananda duplicate copies (Calibre #15201, #15903) | T3 Scholarly | "
        "Duplicate copies of the same book (canonical copy: #696) |",
        {
            15201: "Nibbāna — The Mind Stilled — Bhikkhu K. Ñāṇananda",
            15903: "Nibbāna — The Mind Stilled — Bhikkhu K. Ñāṇananda",
            696: "Nibbāna — The Mind Stilled — Bhikkhu K. Ñāṇananda",
        },
    )
    assert line == (
        "| Ñāṇananda duplicate copies (Nibbāna — The Mind Stilled) | T3 Scholarly | Duplicate copies of the same book (canonical "
        "copy: Nibbāna — The Mind Stilled — Bhikkhu K. Ñāṇananda) |"
    )
    assert report.actions["number replaced by title"] == 2


def test_a_year_after_a_number_is_kept():
    line, _ = _body(
        "**The concept of papañca in the Pāḷi Suttas** — Jayarava Attwood "
        "(Calibre #5793, 2012): surveys the competing readings",
        {5793: "The concept of papañca in the Pāḷi Suttas — Jayarava Attwood"},
    )
    assert line == (
        "**The concept of papañca in the Pāḷi Suttas** — Jayarava Attwood (2012): "
        "surveys the competing readings"
    )


def test_unresolved_number_is_removed_and_reported():
    line, report = _body("- Anālayo (Calibre #322) notes the shift.", {})
    assert line == "- Anālayo notes the shift."
    assert report.unresolved and "322" in report.unresolved[0][2]


def test_wisdomlib_urls_come_out_byte_identical():
    lines = [
        'Rhys Davids, T. W., trans. "Milindapañha, Chapter 2." *Wisdom Library*. '
        "Accessed July 30, 2026. https://www.wisdomlib.org/buddhism/book/"
        "milindapanha-questions-of-king-milinda/d/doc1460771.html",
        "- [Milindapañha Ch. 2 §4, trans. Rhys Davids](https://www.wisdomlib.org/"
        "buddhism/book/milindapanha-questions-of-king-milinda/d/doc1460771.html) "
        "— retrieved 2026-07-30.",
        "  - https://www.wisdomlib.org/buddhism/book/milindapanha-questions-of-king"
        "-milinda/d/doc1460771.html",
    ]
    for line in lines:
        assert _body(line, {1460771: "Wrong — Book"})[0] == line


def test_numbered_list_and_fenced_code_are_untouched():
    line = (
        "Buddhism drops black (#1) and supremely white (#6) from the "
        "classification system."
    )
    assert _body(line, {1: "Wrong — Book", 6: "Wrong — Book"})[0] == line
    fenced = "```\nCalibre #634\n```"
    assert _body(fenced, {634: "X — Y"})[0] == fenced


def test_line_endings_are_kept():
    text = (
        "---\r\ntopic: x\r\n---\r\n"
        "- Mahasi Sayadaw, *Dhammacakkappavattana Sutta* (Calibre #634)\r\n"
    )
    out = migrate_text(
        text, _resolver({634: "Dhammacakkappavattana Sutta — Mahasi Sayadaw"})
    )
    assert out == (
        "---\r\ntopic: x\r\n---\r\n- Mahasi Sayadaw, *Dhammacakkappavattana Sutta*\r\n"
    )


def test_a_number_inside_a_sentence_becomes_its_title():
    # 2026-11-03 bhikkhu-teaching-vinaya-to-bhikkhunis: deleting it left
    # "Duplicate file of, already cited".
    line, _ = _body(
        "| Dhammavihari, *Buddhist Monastic Discipline* (Calibre #5772) | T3 | "
        "Duplicate file of Calibre #1275, already cited; same work, different "
        "format. |",
        {
            5772: "Buddhist Monastic Discipline — Ven. Dhammavihari",
            1275: "Buddhist Monastic Discipline — Ven. Dhammavihari",
        },
    )
    assert line == (
        "| Dhammavihari, *Buddhist Monastic Discipline* | T3 | Duplicate file of "
        "Buddhist Monastic Discipline — Ven. Dhammavihari, already cited; same "
        "work, different format. |"
    )


def test_a_number_ending_a_table_cell_leaves_no_comma():
    # 2026-06-10 nibbana-nibbuto-parinibbuto-morphology.
    line, _ = _body(
        "| Thanissaro, *The Mind Like Fire Unbound*, Calibre #3730 | T3 "
        "Teacher/scholar | Local file unavailable |",
        {3730: "The Mind Like Fire Unbound — Thanissaro Bhikkhu"},
    )
    assert line == (
        "| Thanissaro, *The Mind Like Fire Unbound* | T3 Teacher/scholar | Local "
        "file unavailable |"
    )


def test_a_title_that_starts_the_long_title_names_the_book():
    # 2026-05-19 simile-of-the-saw-anapanasati.
    line, _ = _body(
        "- [[The Mystery of the Breath Nimitta]] (Calibre #1590) — Bhikkhu Sona.",
        {
            1590: "The Mystery of the Breath Nimitta or The Case of the Missing "
            "Simile — Bhikkhu Sona"
        },
    )
    assert line == "- [[The Mystery of the Breath Nimitta]] — Bhikkhu Sona."


def test_a_list_of_unresolved_numbers_leaves_no_debris():
    # 2026-08-13 ajahn-huat-poh-kittisobhana (shortened).
    line, report = _body(
        "**Additional library documents reviewed and rejected** — all returned by "
        "keyword proximity; topics covered in the Related Notes listed above. "
        "Document IDs: calibre #137, calibre #148, calibre #181.",
        {},
    )
    assert line == (
        "**Additional library documents reviewed and rejected** — all returned by "
        "keyword proximity; topics covered in the Related Notes listed above."
    )
    assert len(report.unresolved) == 3


def test_a_removed_number_inside_a_list_leaves_one_comma():
    # 2026-08-08 khuddaka-late-suttas-metta-ratana-mangala (shortened).
    line, _ = _body(
        "| ~65 further library FTS matches | Mixed T3/T4 | No dating argument "
        "content to add. IDs: Calibre #301, Calibre #1366, Calibre #1844 |",
        {1366: "Paritta Chanting — Unknown"},
    )
    assert line == (
        "| ~65 further library FTS matches | Mixed T3/T4 | No dating argument "
        "content to add. IDs: Paritta Chanting — Unknown |"
    )


def test_a_line_of_only_a_number_leaves_nothing_and_document_id_counts():
    # 2026-07-21 mogha-philology-glm:270 and 2026-06-11
    # early-buddhist-teaching-and-the-work:247.
    assert _body("(Calibre #5046.)", {})[0] == ""
    line, _ = _body(
        '[^lib-1]: Calibre #2345, document id 35290, "Madhupindika Sutta - '
        'Majjhima Nikaya.txt." Readable local file.',
        {},
    )
    assert line == (
        '[^lib-1]: "Madhupindika Sutta - Majjhima Nikaya.txt." Readable local file.'
    )


def test_numbers_inside_a_library_ref_and_library_id_are_removed():
    # 2026-05-24 madhupindaka-mind-simulation-b frontmatter and
    # 2026-10-11 bhikkhu-lay-association-dangers bibliography.
    text = (
        "---\nlibrary_refs:\n"
        '  - "Siderits, Mark — Studies in Buddhist Philosophy (Calibre #10140)"\n'
        '  - "Madhupindika Sutta - Majjhima Nikaya.txt - Thanissaro Bhikkhu '
        'translation, Calibre #2345"\n---\n'
        "Crosby, Kate. *Theravada Buddhism*. 2014. (Library id 30698)\n"
    )
    assert migrate_text(
        text, _resolver({30698: "Theravada Buddhism — Kate Crosby"})
    ) == (
        "---\nlibrary_refs:\n"
        '  - "Siderits, Mark — Studies in Buddhist Philosophy"\n'
        '  - "Madhupindika Sutta - Majjhima Nikaya.txt - Thanissaro Bhikkhu '
        'translation"\n---\n'
        "Crosby, Kate. *Theravada Buddhism*. 2014.\n"
    )


def test_a_book_listed_under_canon_refs_loses_its_number():
    # 2026-05-24 madhupindaka-mind-simulation-b, frontmatter line 48.
    text = (
        "---\ncanon_refs:\n  - MN18 Madhupiṇḍikasuttaṃ para 201\n"
        '  - "Siderits, Mark — Studies in Buddhist Philosophy (Calibre #10140)"\n'
        "---\n"
    )
    assert migrate_text(text, _resolver({})) == (
        "---\ncanon_refs:\n  - MN18 Madhupiṇḍikasuttaṃ para 201\n"
        '  - "Siderits, Mark — Studies in Buddhist Philosophy"\n---\n'
    )


def test_space_separated_numbers_form_one_list_and_a_written_author_is_not_repeated():
    # 2026-11-15 ethics-as-self-love-and-helping-oneself-first (shortened).
    table = {
        964: "The Dhammapada: The Path of the Dhamma — Allan R. Bomhard",
        126: "The Dhammapada: The Buddha's Path of Wisdom — Acharya Buddharakkhita",
        5001: "Postmodern Ethics A Buddhist Response — Pano Skiotis",
        5002: "Ancient Philosophy : A Very Short Introduction — Julia Annas",
    }
    line, _ = _body(
        "| Dhammapada translations (Bomhard #964, Buddharakkhita #126); one "
        "consolidated row — ids #5001 #5002 | T3 Scholarly | tangential |",
        table,
    )
    assert line == (
        "| Dhammapada translations (Bomhard The Dhammapada: The Path of the Dhamma, "
        "Buddharakkhita The Dhammapada: The Buddha's Path of Wisdom); one "
        "consolidated row — ids Postmodern Ethics A Buddhist Response — Pano "
        "Skiotis; Ancient Philosophy : A Very Short Introduction — Julia Annas | T3 "
        "Scholarly | tangential |"
    )
