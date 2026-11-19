"""The library title matcher, on citations and hits copied from real runs.

Every citation below is a `library_refs` entry from a vault note, and every
hit is a library hit logged in that note's run dossier (paths shortened to
the parts the matcher reads: file name and folder).
"""

from __future__ import annotations

import pytest

from tools.scratch import library_title_matches

EBOOKS = "Bodhirasa eBook Library"


def _hit(relative_path: str, cite_as: str | None = None) -> dict:
    hit = {"relative_path": relative_path, "title": relative_path.rsplit("/", 1)[-1]}
    if cite_as is not None:
        hit["cite_as"] = cite_as
    return hit


MATCHES = [
    # A diacritic title against Calibre's accent-free folder and file name.
    (
        "Satipaṭṭhāna Meditation: A Practice Guide — Bhikkhu Anālayo",
        _hit(
            f"{EBOOKS}/Bhikkhu Analayo/Satipatthana Meditation _ A Practice Guide "
            "(13851)/Satipatthana Meditation _ A Practice Guide - Bhikkhu Analayo.pdf"
        ),
    ),
    # The same book after a move: another library, another folder number.
    (
        "Buddhist Romanticism — Thanissaro Bhikkhu",
        _hit(
            "Susima/Thanissaro Bhikkhu/Buddhist Romanticism (1284)/"
            "Buddhist Romanticism - Thanissaro Bhikkhu.epub"
        ),
    ),
    (
        "Buddhist Romanticism — Thanissaro Bhikkhu",
        _hit(
            f"{EBOOKS}/Thanissaro Bhikkhu/Buddhist Romanticism (1283)/"
            "Buddhist Romanticism - Thanissaro Bhikkhu.mobi"
        ),
    ),
    # Calibre cuts the title mid-word ("Ear") in the file name and keeps more
    # of it in the folder.
    (
        "Memento Mori — Recollection of Death in Early Buddhist Meditation — "
        "Bhikkhu Anālayo",
        _hit(
            f"{EBOOKS}/Bhikkhu Analayo/Memento Mori_ Recollection of Death in Early "
            "Buddhist Meditation (8757)/Memento Mori_ Recollection of Death in Ear "
            "- Bhikkhu Analayo.pdf"
        ),
    ),
    # A non-Calibre file name.
    (
        "The Heart of Buddhist Meditation — Nyanaponika Thera",
        _hit(
            "Buddhist (English) eBooks, Journals, Dictionaries, Encyclopeadias & "
            "Articles in English/03. Guides to the Titpitaka & Other Works/04. "
            "Satipatthana/Ven. Nyanaponika Thera/the_heart_of_buddhist_meditation.pdf"
        ),
    ),
    # Calibre cut the folder name too; the title starts the citation.
    (
        "Buddhist Forest Monasteries and Meditation Centres in Sri Lanka — "
        "Bhikkhu Nyanatusita",
        _hit(
            f"{EBOOKS}/Bhikkhu Nyanatusita/Buddhist Forest Monasteries and Med "
            "(1515)/Buddhist Forest Monasteries and - Bhikkhu Nyanatusita.pdf"
        ),
    ),
    # An EPUB/MOBI pair, where the note drops the subtitle Calibre keeps.
    (
        "The Ego Tunnel — Thomas Metzinger",
        _hit(
            f"{EBOOKS}/Thomas Metzinger/The Ego Tunnel_ The Science of the Mind and "
            "the Myth of the Self (5758)/The Ego Tunnel_ The Science of the Mind an "
            "- Thomas Metzinger.epub"
        ),
    ),
    (
        "The Ego Tunnel — Thomas Metzinger",
        _hit(
            f"{EBOOKS}/Thomas Metzinger/The Ego Tunnel_ The Science of the Mind and "
            "the Myth of the Self (5758)/The Ego Tunnel_ The Science of the Mind an "
            "- Thomas Metzinger.mobi"
        ),
    ),
    # Calibre ends the main title with a full stop.
    (
        "Wings to Awakening — Thanissaro Bhikkhu",
        _hit(
            "Susima/Thanissaro Bhikkhu/Wings to Awakening. An Anthology from the "
            "Pali Canon (1287)/Wings to Awakening. An Anthology from the - "
            "Thanissaro Bhikkhu.txt"
        ),
    ),
    # Calibre's own metadata misspells the author.
    (
        "Anagarika Dharmapala: A Biographical Sketch — Bhikkhu Sangharakshita",
        _hit(
            f"{EBOOKS}/Bhikkhu Sanhgarakshita/Anagarika Dharmapala - A Biographic "
            "(3023)/Anagarika Dharmapala - A Biogra - Bhikkhu Sanhgarakshita.pdf"
        ),
    ),
    # Piya Tan's file writes "sd.04.9" for the note's "SD 4.9".
    (
        "SD 4.9 Dhananjani Sutta (MN97) — Piya Tan",
        _hit(
            f"{EBOOKS}/Piya Tan/sd.04.9.Dhananjani.mn.97 (16982)/"
            "sd.04.9.Dhananjani.mn.97 - Piya Tan.pdf"
        ),
    ),
    # The file name leads with the author.
    (
        "Early Buddhist Transmission and Trade Networks — Jason Neelis",
        _hit(
            "Buddhist (English) eBooks, Journals, Dictionaries, Encyclopeadias & "
            "Articles in English/17. Buddhism in Verious Topics/Neelis-ed-Early-"
            "Buddhist-Transmission-and-Trade-Networks-Mobility-and-Exchange-Within-"
            "and-Beyond-the-Northwestern-Borderlands-of-South-Asia.pdf"
        ),
    ),
    # A one-word title, backed by the author named in the folder above.
    (
        "Udana — Peter Masefield",
        _hit(
            "Buddhist (English) eBooks, Journals, Dictionaries, Encyclopeadias & "
            "Articles in English/02. Tipitika & Other Canonical Works/02. Suttas/"
            "Khuddaka Nikaya/03. Udana/P. Masefield, Tr/154343752-the-udana.pdf"
        ),
    ),
    # An older note's plain dash before the author.
    (
        "The Secret - Rhonda Byrne",
        _hit(f"{EBOOKS}/Rhonda Byrne/The Secret (8456)/The Secret - Rhonda Byrne.pdf"),
    ),
    # A hit logged with `cite_as` matches on Calibre's exact title.
    (
        "Satipaṭṭhāna Meditation : A Practice Guide — Bhikkhu Anālayo",
        _hit(
            f"{EBOOKS}/Bhikkhu Analayo/Satipatthana Meditation _ A Practice Guide "
            "(13851)/Satipatthana Meditation _ A Practice Guide - Bhikkhu Analayo.pdf",
            cite_as="Satipaṭṭhāna Meditation : A Practice Guide — Bhikkhu Anālayo",
        ),
    ),
    # A Roman numeral that ends a file name is the volume number.
    (
        "The Mahāvastu, Vol. I — trans. J.J. Jones",
        _hit(
            "Buddhist (English) eBooks, Journals, Dictionaries, Encyclopeadias & "
            "Articles in English/02. Tipitika & Other Canonical Works/09. Other - "
            "Mahavastu/73180057-Mahāvastu-I.pdf"
        ),
    ),
    # "ch. 19" is the file's "Chapter Nineteen".
    (
        "The Wisdom of the Lotus Sutra, ch. 19 — Soka Gakkai study",
        _hit(
            "SBS Textual/Texts English/2 Mahayana/Names/Nichiren/Wisdom Of The Lotus "
            "Sutra/The Wisdom Of The Lotus Sutra-Chapter Nineteen.doc"
        ),
    ),
    # Two plain dashes: the author is in any part after the first.
    (
        "Journal - Sayagyi U Ba Khin - S.N. Goenka",
        _hit(
            f"{EBOOKS}/Sayagyi U Ba Khin/Journal (17358)/Journal - Sayagyi U Ba Khin.pdf"
        ),
    ),
    # Calibre's own title misspells "Unconscious"; the author agrees.
    (
        "Buddhist Influences on the Idea of the Unconscious — Irvin A. Hansen",
        _hit(
            f"{EBOOKS}/Irvin A. Hansen/Buddhist Influences on the Idea of the "
            "Uconscious (8921)/Buddhist Influences on the Idea of the Uco - Irvin A. "
            "Hansen.pdf"
        ),
    ),
    # The file name leads with the author and keeps only the main title.
    (
        "Buddhist Modernism and the Rhetoric of Meditative Experience — Robert Sharf",
        _hit(
            "Na Uyana eBook Library/Buddhist Books/Journals, Articles etc/Robert "
            "Sharf, Buddhist Modernism.pdf"
        ),
    ),
    (
        "Positive Psychology: The Science of Happiness and Flourishing - William C. "
        "Compton",
        _hit(
            f"{EBOOKS}/William C. Compton/Positive Psycholog_ The Science of "
            "Happiness and Flourishing, 2nd ed_ (8708)/Positive Psycholog_ The "
            "Science of Happine - William C. Compton.pdf"
        ),
    ),
    # A compound one folder splits ("NIBBĀNA GĀMINIPAŢIPADĀ"); "pp." is "Page".
    (
        "Nibbānagāminīpaṭipadā, vol. 4, pp. 474–500 — Pa-Auk Sayadaw",
        _hit(
            "SBS Textual/Texts English/1 Theravada/01 Authors/1 Monks/Pa-Auk Sayadaw/"
            "1 Collection of Pa-Auk Dhamma books in English/05 NIBBĀNA GĀMINIPAŢIPADĀ "
            "2010/vol 4, Page 474-500.pdf"
        ),
    ),
]

NOT_MATCHES = [
    # Two translations of one text.
    (
        "The Yoga Sutras of Patanjali — Edwin F. Bryant",
        _hit(
            f"{EBOOKS}/Michael Beloved/Yoga Sutras of Patanjali (10957)/"
            "Yoga Sutras of Patanjali - Michael Beloved.pdf"
        ),
    ),
    # One author's two different books that share title words.
    (
        "Pāli: A Grammar of the Language of the Theravāda Tipiṭaka — Thomas Oberlies",
        _hit(
            f"{EBOOKS}/Thomas Oberlies/Pali Grammar_ The language of the canonical "
            "texts of Theravada Buddhism. Part I_ Phonology and (17242)/Pali Grammar_ "
            "The language of the canonica - Thomas Oberlies.pdf"
        ),
    ),
    (
        "The Gospel of Judas — Rodolphe Kasser",
        _hit(
            f"{EBOOKS}/Elaine Pagels/Reading Judas_ The Gospel of Judas and the "
            "Shaping of Christianity (9914)/Reading Judas_ The Gospel of Judas and "
            "the - Elaine Pagels.pdf"
        ),
    ),
    (
        "Merit — Douglas Osto",
        _hit(
            f"{EBOOKS}/Ven. Nanadassana/Ten Ways Of Making Merit (712)/Ten Ways Of "
            "Making Merit - Ven. Nanadassana.pdf"
        ),
    ),
    # A cut title ("…in Cu") must not start every Brahmavihara title.
    (
        "The Role of the Brahmavihara in Psychotherapeutic Practice — Akincano M. "
        "Weber",
        _hit(
            f"{EBOOKS}/Akincano M. Weber/What is the Role of the Brahmavihara in "
            "Cultiavting Presence in Core Process Psychotherapy and (7887)/What is "
            "the Role of the Brahmavihara in Cu - Akincano M. Weber.pdf"
        ),
    ),
    # A one-word encyclopedia entry by the same author is another work.
    (
        "Satipatthana Meditation: A Practice Guide — Bhikkhu Anālayo",
        _hit(
            "SBS Textual/Texts English/1 Theravada/01 Authors/1 Monks/Analayo, Ven/"
            "Encyclopedia of Indian Religions/Satipatthana.pdf"
        ),
    ),
    # "Vol. 1" against Vol. II of the same series.
    (
        "A Comparative Study of the Majjhima Nikāya, vol. 1 — Bhikkhu Anālayo",
        _hit(
            "SBS Textual/Texts English/1 Theravada/01 Authors/1 Monks/Analayo, Ven/"
            "Comparative Study of the Majjhima Nikaya, Vol. II, Suttas 91 - 152.pdf"
        ),
    ),
    # Another chapter of the same work.
    (
        "The Wisdom of the Lotus Sutra, ch. 19 — Soka Gakkai study",
        _hit(
            "SBS Textual/Texts English/2 Mahayana/Names/Nichiren/Wisdom Of The Lotus "
            "Sutra/The Wisdom of the Lotus Sutra-Chapter Eleven.doc"
        ),
    ),
    # Every word shared, but the main titles differ.
    (
        "Positive Psychology: The Science of Happiness and Flourishing - William C. "
        "Compton",
        _hit(
            f"{EBOOKS}/Corey L. M. Keyes/Flourishing_ Positive Psychology and the "
            "LIfe Well Lived (8804)/Flourishing_ Positive Psychology and the L - "
            "Corey L. M. Keyes.pdf"
        ),
    ),
    # Another volume or part of the same work.
    (
        "Abhidharmakośabhāṣyam, Volume II — Vasubandhu, trans. Leo Pruden",
        _hit(
            f"{EBOOKS}/Vasubandhu/Abhidharmakosabhasyam Volume I (5080)/"
            "Abhidharmakosabhasyam Volume I - Vasubandhu.pdf"
        ),
    ),
    (
        "Pali Grammar Part I (Phonology) — Thomas Oberlies",
        _hit(
            f"{EBOOKS}/Thomas Oberlies/Pali Grammar_ The language of the canonical "
            "texts of Theravada Buddhism. Part II_ `Conspectus' (17243)/Pali Grammar_ "
            "The language of the canonica - Thomas Oberlies.pdf"
        ),
    ),
]


@pytest.mark.parametrize(("citation", "hit"), MATCHES)
def test_citation_names_its_book(citation, hit):
    assert library_title_matches(citation, hit)


@pytest.mark.parametrize(("citation", "hit"), NOT_MATCHES)
def test_citation_does_not_name_another_book(citation, hit):
    assert not library_title_matches(citation, hit)


def test_renumbering_the_index_changes_no_check_result(tmp_path):
    """The same library indexed in another order gets other ids, same verdicts.

    Index ids are row numbers handed out in walk order; a note that names
    books by title must get the same coverage, gate and bibliography results
    from either index.
    """
    import json

    from tools.library_folders import (
        LibraryFoldersConfig,
        read_document,
        refresh,
        search,
    )
    from tools.note_audit import check_bibliography
    from tools.scratch import scratch_check_coverage, unread_library_citations

    books = {
        "Bhikkhu Analayo/Satipatthana Meditation _ A Practice Guide (13851)/"
        "Satipatthana Meditation _ A Practice Guide - Bhikkhu Analayo.txt": (
            "satipatthana practice guide on contemplation of feelings"
        ),
        "Thanissaro Bhikkhu/Buddhist Romanticism (1283)/"
        "Buddhist Romanticism - Thanissaro Bhikkhu.txt": (
            "romanticism and contemplation of feelings in modern buddhism"
        ),
    }
    order = list(books)

    def build(name: str, first: list[str]) -> tuple[LibraryFoldersConfig, str]:
        root = tmp_path / name / "library"
        config = LibraryFoldersConfig(roots=[root], index=tmp_path / name / "i.db")
        for group in (first, [p for p in order if p not in first]):
            for rel in group:
                path = root / rel
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(books[rel], encoding="utf-8")
            refresh(config)
        hits = search("contemplation feelings", config)
        read = read_document(
            next(h["document_id"] for h in hits if "Romanticism" in h["title"]),
            config,
        )
        dossier = (
            "### 2026-11-19T10:00:00 · search-library-folders\n- args: `x`\n"
            f"- results:\n```json\n{json.dumps(hits)}\n```\n"
            "### 2026-11-19T10:01:00 · read-library\n- args: `x`\n"
            f"- results:\n```json\n{json.dumps(read)}\n```\n"
        )
        return config, dossier

    note_text = (
        '---\nlibrary_refs:\n  - "Satipaṭṭhāna Meditation: A Practice Guide — '
        'Bhikkhu Anālayo"\n  - "Buddhist Romanticism — Thanissaro Bhikkhu"\n---\n'
        "# Note\n\n## Bibliography\n\n### Secondary Sources\n\n"
        "Anālayo, Bhikkhu. *Satipaṭṭhāna Meditation: A Practice Guide*.\n\n"
        "Thanissaro Bhikkhu. *Buddhist Romanticism*.\n"
    )
    note = tmp_path / "note.md"
    note.write_text(note_text, encoding="utf-8")

    results = []
    ids = []
    for name, first in (("a", order), ("b", order[::-1][:1])):
        config, dossier = build(name, first)
        scratch = tmp_path / f"{name}.md"
        scratch.write_text(dossier, encoding="utf-8")
        ids.append(
            sorted(
                json.loads(dossier.split("```json\n")[1].split("\n```")[0]),
                key=lambda h: h["title"],
            )
        )
        coverage = scratch_check_coverage(
            scratch=scratch, note=note, index=config.index
        )
        gate = unread_library_citations(note_text, dossier, index=config.index)
        results.append(
            (
                {k: coverage[k] for k in ("ok", "unaccounted", "cited_not_gathered")},
                {k: [e["book"] for e in v] for k, v in gate.items()},
                check_bibliography(note_text, dossier),
            )
        )

    assert [h["document_id"] for h in ids[0]] != [h["document_id"] for h in ids[1]]
    assert results[0] == results[1]
    assert results[0][1]["cited_not_read"] == [
        "Satipaṭṭhāna Meditation: A Practice Guide — Bhikkhu Anālayo"
    ]
    assert results[0][0]["ok"] is True


def test_a_cited_volume_matches_only_that_volume():
    cite = "A Comparative Study of the Majjhima Nikāya, vol. 1 — Bhikkhu Anālayo"
    vol1 = _hit(
        "Bodhirasa eBook Library/Bhikkhu Analayo/A Comparative Study Of The Majjhima Nikaya 1 (344)/A Comparative Study Of The Majjhima Nikaya - Bhikkhu Analayo.pdf"
    )
    vol2 = _hit(
        "Bodhirasa eBook Library/Bhikkhu Analayo/A Comparative Study Of The Majjhima Nikaya 2 (345)/A Comparative Study Of The Majjhima Nikaya - Bhikkhu Analayo.pdf"
    )
    assert library_title_matches(cite, vol1)
    assert not library_title_matches(cite, vol2)


def test_the_exact_label_of_an_authorless_file_names_it():
    hit = _hit(
        "Buddhist (English) eBooks, Journals, Dictionaries, Encyclopeadias & "
        "Articles in English/05. Pali Grammar, Dictionaries & Text/05. Sample Pali "
        "Texts/Buddhavacana/Buddhavacana.pdf"
    )
    assert library_title_matches("Buddhavacana", hit)
    assert not library_title_matches(
        "Buddhavacana — Ñāṇatiloka",
        _hit(
            "Bodhirasa eBook Library/Thanissaro Bhikkhu/Buddhist Romanticism (1283)/"
            "Buddhist Romanticism - Thanissaro Bhikkhu.mobi"
        ),
    )
