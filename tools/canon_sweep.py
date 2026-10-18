"""Count a family of Pāḷi terms across every canon table, grouped by evidence tier.

Absence claims kept failing the same few ways (issue #116): a quoted phrase in
one case ending found nothing while the stem was everywhere; a sweep of the
sutta tables was called "canon-wide" and missed the Abhidhamma; a ṭīkā search
was reported as the aṭṭhakathā being silent; a long-vowel spelling missed the
short-vowel forms; a row count was written up as "every occurrence"; and a stem
count was mostly other words (ogha inside mogha). The prose rule naming these
did not hold, so `sweep_canon` makes the evidence itself: complete counts per
table and per tier for every term, the word forms that matched, a stem probe
and a vowel-length probe. Dating questions ("when does X first appear") need
the same per-tier table (issue #121).
"""

from __future__ import annotations

import fnmatch
import re
import sqlite3
import unicodedata
from collections import Counter
from contextlib import closing
from pathlib import Path

_NOTE_RE = re.compile(r"<note>(.*?)</note>", re.S)
_TAG_RE = re.compile(r"<[^>]+>")
# Block tags end a line of verse or a heading. Deleting them outright would
# glue the last word of one line to the first of the next (2,385 real rows).
_BLOCK_TAG_RE = re.compile(r"</?(?:p|head|trailer)\b[^>]*>")
_WS_RE = re.compile(r"\s+")
_LETTER_RE = re.compile(r"[^\W\d_]")
# Inflectional endings trimmed to reach a stem: vowels, the niggahita, and the
# commonest case endings. A stem is only probed when it keeps 3+ letters.
_ENDING_RE = re.compile(r"(?:ehi|ebhi|ānaṃ|asmiṃ|amhi|assa|āya|ena|ato|[aāiīuūeoṃ])+$")
_LENGTH_FOLD = str.maketrans({"ā": "a", "ī": "i", "ū": "u", "ṅ": "ṃ"})

# The EBT set dpd-db uses for its own word frequencies
# (dpd-db tools/pali_text_files.py: ebts); SKILL.md's T1a row names the same.
_T1A = frozenset(
    {
        "vin01m_mul",
        "vin02m1_mul",
        "s0101m_mul",
        "s0102m_mul",
        "s0103m_mul",
        "s0201m_mul",
        "s0202m_mul",
        "s0203m_mul",
        "s0301m_mul",
        "s0302m_mul",
        "s0303m_mul",
        "s0304m_mul",
        "s0305m_mul",
        "s0401m_mul",
        "s0402m1_mul",
        "s0402m2_mul",
        "s0402m3_mul",
        "s0403m1_mul",
        "s0403m2_mul",
        "s0403m3_mul",
        "s0404m1_mul",
        "s0404m2_mul",
        "s0404m3_mul",
        "s0404m4_mul",
        "s0501m_mul",
        "s0502m_mul",
        "s0503m_mul",
        "s0504m_mul",
        "s0505m_mul",
        "s0508m_mul",
        "s0509m_mul",
    }
)
# Canonically root-classed but exegetical in genre: SKILL.md tiers them T2.
_EXEGETICAL_MULA = frozenset(
    {
        "s0515m_mul",  # Mahāniddesa
        "s0516m_mul",  # Cūḷaniddesa
        "s0517m_mul",  # Paṭisambhidāmagga
        "s0519m_mul",  # Nettippakaraṇa
        "e0101n_mul",  # Visuddhimagga
        "e0102n_mul",  # Visuddhimagga
    }
)
# Stored as nrf but canonical in the Burmese Tipiṭaka.
_LATER_MULA_NRF = frozenset({"s0518m_nrf", "s0520m_nrf"})  # Milinda, Peṭakopadesa
# Named *_att in the CST file set, but the text is the Visuddhimagga-mahāṭīkā.
_TIKA_ATT = frozenset({"e0103n_att", "e0104n_att"})

# Output order runs earliest stratum first, so a first attestation reads top down.
STRATA = (
    ("mula-ebt", "T1a"),
    ("mula-later", "T1b"),
    ("exegetical-mula", "T2"),
    ("atthakatha", "T2"),
    ("tika", "T2"),
    ("post-canonical", None),
)
_STRATUM_TIER = dict(STRATA)


def stratum(table: str) -> str:
    """The text layer a CST table belongs to (see STRATA for its tier)."""
    if table in _T1A:
        return "mula-ebt"
    if table in _EXEGETICAL_MULA:
        return "exegetical-mula"
    if table in _TIKA_ATT:
        return "tika"
    if table.endswith("_mul") or table in _LATER_MULA_NRF:
        return "mula-later"
    if table.endswith("_att"):
        return "atthakatha"
    # *t_nrf: anuṭīkās and the Vinaya/Abhidhamma handbooks built on the ṭīkās
    # (vin05–13t), plus Dvemātikāpāḷi (vin04t): a Vinaya mātikā compendium CST
    # files under t. Exegetical genre, so T2 — but read its by_stratum rows as
    # "tika" knowing the text itself is a mātikā list, not a commentary.
    if table.endswith("_tik") or re.search(r"t\d*_nrf$", table):
        return "tika"
    return "post-canonical"


def _normalise(text: str) -> str:
    text = unicodedata.normalize("NFC", _TAG_RE.sub("", _BLOCK_TAG_RE.sub(" ", text)))
    text = text.replace("ṁ", "ṃ").replace("ŋ", "ṃ")
    return _WS_RE.sub(" ", text).strip().casefold()


def _split_variants(raw: str) -> tuple[str, str]:
    """(main text, variant readings): CST keeps variants inline in <note>."""
    if "<note" not in raw:
        return _normalise(raw), ""
    variants = " ".join(_NOTE_RE.findall(raw))
    return _normalise(_NOTE_RE.sub(" ", raw)), _normalise(variants)


def _forms(text: str, needle: str, shown: str | None = None) -> list[str]:
    """Each match widened to whole words, so noise forms (mogha for ogha) show.

    `shown` is the text to cut the forms from when `text` is a folded copy of
    it: folding maps one character to one, so the positions carry over and the
    real spelling is reported.
    """
    shown = text if shown is None else shown
    out = []
    start = 0
    while (i := text.find(needle, start)) != -1:
        lo, hi = i, i + len(needle)
        while lo > 0 and _LETTER_RE.match(text[lo - 1]):
            lo -= 1
        while hi < len(text) and _LETTER_RE.match(text[hi]):
            hi += 1
        out.append(shown[lo:hi])
        start = i + len(needle)
    return out


def _stem(word: str) -> str | None:
    stem = _ENDING_RE.sub("", word)
    if len(stem) < 3 or stem == word:
        return None
    return stem


# Only CST text tables are swept: the same shape canon_paragraphs enforces, so
# a stray non-text table in the db cannot silently join the counts.
_TABLE_RE = re.compile(r"^[a-z0-9]+_(mul|att|tik|nrf)$")


def _resolve_tables(conn, books: list[str] | None) -> list[str]:
    names = [
        r[0]
        for r in conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
        )
        if _TABLE_RE.match(r[0])
    ]
    if not books:
        return names
    picked: list[str] = []
    for spec in books:
        for name in names:
            if fnmatch.fnmatchcase(name, spec) and name not in picked:
                picked.append(name)
    return picked


def _book_name(conn, table: str) -> str:
    row = conn.execute(
        f"SELECT pali_text FROM {table} WHERE rend IN ('book', 'chapter') "
        "ORDER BY rend = 'book' DESC, id LIMIT 1"
    ).fetchone()
    return _WS_RE.sub(" ", _TAG_RE.sub("", row[0] or "")).strip() if row else ""


class _Probe:
    """Rows a looser key finds, per stratum, with a few places to read."""

    def __init__(self) -> None:
        self.rows: Counter[str] = Counter()
        self.refs: dict[str, list[str]] = {}

    def add(self, layer: str, table: str, paranum: str) -> None:
        self.rows[layer] += 1
        refs = self.refs.setdefault(layer, [])
        ref = f"{table} {paranum}".strip()
        if len(refs) < 3 and ref not in refs:
            refs.append(ref)

    def report(self) -> dict:
        return {
            "rows": sum(self.rows.values()),
            "by_stratum": {
                s: {"rows": self.rows[s], "examples": self.refs[s]}
                for s, _ in STRATA
                if self.rows[s]
            },
        }


class _Tally:
    def __init__(self) -> None:
        self.rows = 0
        self.occurrences = 0
        self.variant_rows = 0
        self.loose_rows = 0
        self.forms: Counter[str] = Counter()
        self.excluded: Counter[str] = Counter()
        self.loose_forms: Counter[str] = Counter()
        self.refs: list[str] = []


def sweep_canon(
    terms: list[str],
    books: list[str] | None = None,
    exclude: list[str] | None = None,
    canon_db: Path | None = None,
    max_forms: int = 30,
) -> dict:
    """Complete per-table and per-tier counts for each term, in one pass.

    A row counts for a term when the term occurs in its main text as part of
    a word form that begins with none of the `exclude` prefixes. Rows where the
    term occurs only inside a variant reading are counted apart. Nothing is
    capped: these are the counts an absence or frequency claim can rest on.
    """
    if canon_db is None or not Path(canon_db).exists():
        return {"ok": False, "error": "canon db not found (VICAYA_CANON_DB)"}
    needles = [_normalise(t) for t in terms]
    if not all(needles):
        return {"ok": False, "error": "every term must contain text"}
    excl = [_normalise(e) for e in exclude or [] if _normalise(e)]
    loose = [n.translate(_LENGTH_FOLD) for n in needles]
    probes: dict[str, str] = {}
    for n in needles:
        for word in n.split(" "):
            if (s := _stem(word)) is not None:
                probes[s] = word

    totals = {n: _Tally() for n in needles}
    per_table: dict[str, dict[str, _Tally]] = {}
    family: dict[str, set[tuple[str, int]]] = {s: set() for s, _ in STRATA}
    probe_rows = {s: _Probe() for s in probes}
    cooccur = {n: _Probe() for n in needles if " " in n}
    rows_searched = 0

    uri = f"file:{Path(canon_db)}?immutable=1"
    scanned: list[str] = []
    with closing(sqlite3.connect(uri, uri=True)) as conn:
        for table in _resolve_tables(conn, books):
            layer = stratum(table)
            try:
                cursor = conn.execute(
                    f"SELECT id, paranum, pali_text FROM {table} ORDER BY id"
                )
            except sqlite3.OperationalError:
                # A table that cannot be read was not searched: counting it
                # would let it mark its stratum searched while empty.
                continue
            scanned.append(table)
            paranum = ""
            for row_id, para, raw in cursor:
                rows_searched += 1
                if para not in (None, ""):
                    paranum = str(para)
                if not raw:
                    continue
                main, variants = _split_variants(raw)
                folded = None
                for n, ln in zip(needles, loose):
                    tally = None
                    if n in main:
                        kept = []
                        for form in _forms(main, n):
                            # Prefix, not substring: "mogha" inside
                            # kāmoghaṃ is the flood of sensuality, a real hit.
                            if form.startswith(tuple(excl)):
                                totals[n].excluded[form] += 1
                            else:
                                kept.append(form)
                        if kept:
                            tally = per_table.setdefault(table, {}).setdefault(
                                n, _Tally()
                            )
                            for t in (tally, totals[n]):
                                t.rows += 1
                                t.occurrences += len(kept)
                                t.forms.update(kept)
                            if len(tally.refs) < 3 and paranum not in tally.refs:
                                tally.refs.append(paranum)
                            family[layer].add((table, row_id))
                    elif variants and n in variants:
                        totals[n].variant_rows += 1
                        per_table.setdefault(table, {}).setdefault(
                            n, _Tally()
                        ).variant_rows += 1
                    if n not in main:
                        if folded is None:
                            folded = main.translate(_LENGTH_FOLD)
                        if ln in folded:
                            # Same exclusions as the exact pass, or the probe
                            # re-counts the noise the caller just removed.
                            kept = [
                                f
                                for f in _forms(folded, ln, main)
                                if not f.startswith(tuple(excl))
                            ]
                            if kept:
                                totals[n].loose_rows += 1
                                totals[n].loose_forms.update(kept)
                for s, probe in probe_rows.items():
                    if s in main:
                        probe.add(layer, table, paranum)
                for n, probe in cooccur.items():
                    if all((_stem(w) or w) in main for w in n.split(" ")):
                        probe.add(layer, table, paranum)
        names = {t: _book_name(conn, t) for t in per_table}

    return _report(
        terms,
        needles,
        scanned,
        rows_searched,
        totals,
        per_table,
        names,
        family,
        probes,
        probe_rows,
        cooccur,
        books,
        max_forms,
        excl,
    )


def _by_prefix(excluded: Counter[str], prefixes: list[str]) -> list[dict]:
    """What each --exclude prefix removed, so a wrongly dropped word can be seen.

    Grouped per prefix with its own count: one flat capped list once hid a
    whole prefix's forms behind a hundred forms of another.
    """
    out = []
    for prefix in prefixes:
        mine = Counter({f: c for f, c in excluded.items() if f.startswith(prefix)})
        if not mine:
            continue
        out.append(
            {
                "prefix": prefix,
                "occurrences": sum(mine.values()),
                "distinct_forms": len(mine),
                "forms": [{"form": f, "count": c} for f, c in mine.most_common(10)],
            }
        )
    return out


def _tier_rollup(
    per_table: dict[str, dict[str, _Tally]], needle: str, searched: set[str]
) -> list[dict]:
    out = []
    for layer, tier in STRATA:
        if layer not in searched:
            # A zero here would read as absence; nothing was looked at.
            out.append({"stratum": layer, "tier": tier, "searched": False})
            continue
        rows = occ = tables = 0
        for table, by_term in per_table.items():
            t = by_term.get(needle)
            if t and t.rows and stratum(table) == layer:
                rows += t.rows
                occ += t.occurrences
                tables += 1
        out.append(
            {
                "stratum": layer,
                "tier": tier,
                "rows": rows,
                "occurrences": occ,
                "tables": tables,
            }
        )
    return out


def _report(
    terms,
    needles,
    tables,
    rows_searched,
    totals,
    per_table,
    names,
    family,
    probes,
    probe_rows,
    cooccur,
    books,
    max_forms,
    excl,
) -> dict:
    searched_layers = {stratum(t) for t in tables}
    results = []
    for term, n in zip(terms, needles):
        tot = totals[n]
        entry: dict = {
            "term": term,
            "rows": tot.rows,
            "occurrences": tot.occurrences,
            "by_stratum": _tier_rollup(per_table, n, searched_layers),
            "tables": [
                {
                    "table": table,
                    "book": names.get(table, ""),
                    "stratum": stratum(table),
                    "tier": _STRATUM_TIER[stratum(table)],
                    "rows": by_term[n].rows,
                    "occurrences": by_term[n].occurrences,
                    "paranums": by_term[n].refs,
                    **(
                        {"variant_only_rows": by_term[n].variant_rows}
                        if by_term[n].variant_rows
                        else {}
                    ),
                }
                for table, by_term in per_table.items()
                if n in by_term and by_term[n].rows
            ],
            "forms": [
                {"form": f, "count": c} for f, c in tot.forms.most_common(max_forms)
            ],
        }
        if len(tot.forms) > max_forms:
            entry["forms_not_shown"] = len(tot.forms) - max_forms
        if tot.excluded:
            entry["excluded"] = _by_prefix(tot.excluded, excl)
        if tot.variant_rows:
            entry["variant_only_rows"] = tot.variant_rows
        if tot.loose_rows:
            entry["vowel_length_variants"] = {
                "extra_rows": tot.loose_rows,
                "forms": [
                    {"form": f, "count": c} for f, c in tot.loose_forms.most_common(10)
                ],
            }
        stems = [
            {"stem": s, "from": w, **probe_rows[s].report()}
            for s, w in probes.items()
            if w in n.split(" ")
        ]
        if stems:
            entry["stem_probes"] = stems
        if n in cooccur:
            entry["rows_with_every_word_stem"] = cooccur[n].report()
        entry["hints"] = _hints(entry, n)
        results.append(entry)

    if not tables:
        return {
            "ok": False,
            "error": f"--books {books} matched no canon table",
        }
    out: dict = {
        "ok": True,
        # Nothing is capped, but a --books sweep is not the whole canon.
        "complete": not books,
        "tables_searched": len(tables),
        "rows_searched": rows_searched,
        "strata_searched": [s for s, _ in STRATA if s in searched_layers],
        "terms": results,
    }
    if len(needles) > 1:
        out["family"] = [
            {"stratum": s, "tier": t, "rows": len(family[s])} for s, t in STRATA
        ]
    missing = [s for s, _ in STRATA[:5] if s not in searched_layers]
    if books and missing:
        out["not_searched"] = missing
        out["warning"] = (
            "this sweep is not canon-wide: it skipped "
            + ", ".join(missing)
            + ". Do not call a zero here absence from the canon."
        )
    return out


def _hints(entry: dict, needle: str) -> list[str]:
    hints = []
    zero_layers = [s["stratum"] for s in entry["by_stratum"][:5] if s.get("rows") == 0]
    # A phrase is judged by rows holding all its words, never by its commonest
    # word alone (cattār- occurs in a thousand early rows that are not the
    # brahmavihāra formula).
    if "rows_with_every_word_stem" in entry:
        probe = entry["rows_with_every_word_stem"]
        key = "every word's stem occurs in one row"
    elif entry.get("stem_probes"):
        probe = max(entry["stem_probes"], key=lambda p: p["rows"])
        key = f"the stem {probe['stem']} occurs"
    else:
        probe, key = None, ""
    found = [
        f"{layer} {probe['by_stratum'][layer]['rows']}"
        for layer in zero_layers
        if probe and layer in probe["by_stratum"]
    ]
    if found:
        hints.append(
            "This exact form is absent from some strata where "
            f"{key} ({', '.join(found)} rows): the ending or word order is "
            "missing, not necessarily the word. Read the examples before "
            "writing 'absent'."
        )
    if entry["rows"] == 0 and " " in needle:
        hints.append(
            "A phrase found nowhere says nothing about its words: sweep each "
            "word's stem."
        )
    if entry.get("vowel_length_variants"):
        hints.append(
            "Spellings differing only in vowel length (or ṅ/ṃ) match rows this "
            "term misses: read vowel_length_variants.forms and sweep the real "
            "spelling."
        )
    if entry["rows"] and entry["forms"]:
        hints.append(
            "Read forms: a stem also matches unrelated words. Re-run with "
            "--exclude <prefix> for each noise word (it drops forms that begin "
            "with the prefix) so the counts hold only the term."
        )
    return hints
