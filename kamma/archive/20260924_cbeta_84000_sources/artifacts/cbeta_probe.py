"""Probe CBETA xml-p5: layout, titles, gaiji, line-joined search, speed."""

import collections
import re
import statistics
import sys
import time
from pathlib import Path

ROOT = Path.home() / "MyFiles/2_Resources/cbeta"
T = ROOT / "T"

LB_RE = re.compile(r'<lb\b[^>]*\bn="([0-9a-z]+)"[^>]*/>')
DROP_RE = re.compile(
    r"<(note|rdg|teiHeader|back|mulu|cb:mulu|cb:docNumber|figure|charDecl)\b.*?</\1>",
    re.S,
)
TAG_RE = re.compile(r"<[^>]+>")
TITLE_RE = re.compile(r"<title[^>]*>(.*?)</title>", re.S)
CHAR_RE = re.compile(
    r'<char xml:id="(CB\d+)">.*?(?:<charProp>\s*<localName>normalized form</localName>\s*<value>(.*?)</value>|<mapping type="unicode">(.*?)</mapping>)',
    re.S,
)
G_RE = re.compile(r'<g ref="#(CB\d+)"\s*/?>(?:</g>)?')


def flatten(path: Path):
    """Return (text, [(offset, lb)]) with lb markers removed, lines joined."""
    raw = path.read_text(encoding="utf-8")
    gaiji = {}
    for m in CHAR_RE.finditer(raw):
        val = m.group(2) or m.group(3) or ""
        if val.startswith("U+"):
            val = chr(int(val[2:], 16))
        gaiji[m.group(1)] = val
    body = raw.split("<text", 1)[-1]
    body = DROP_RE.sub("", body)
    body = G_RE.sub(lambda m: gaiji.get(m.group(1), ""), body)
    out, marks, pos = [], [], 0
    last = 0
    for m in LB_RE.finditer(body):
        chunk = TAG_RE.sub("", body[last : m.start()])
        chunk = re.sub(r"\s+", "", chunk)
        out.append(chunk)
        pos += len(chunk)
        marks.append((pos, m.group(1)))
        last = m.end()
    tail = re.sub(r"\s+", "", TAG_RE.sub("", body[last:]))
    out.append(tail)
    return "".join(out), marks, raw


def line_at(marks, off):
    lb = marks[0][1] if marks else "?"
    for p, n in marks:
        if p > off:
            break
        lb = n
    return lb


def layout():
    files = sorted(T.rglob("*.xml"))
    print(
        "T files:",
        len(files),
        "size MB:",
        round(sum(f.stat().st_size for f in files) / 1e6),
    )

    def text_id(stem):
        m = re.match(r"T\d+n(\w+?)(?:_\d+)?$", stem)
        return m.group(1) if m else stem

    ids = collections.Counter(text_id(f.stem) for f in files)
    print(
        "sample stems:",
        [f.stem for f in files[:3]],
        [f.stem for f in files if "0220" in f.stem][:5],
    )
    print(
        "distinct text ids:",
        len(ids),
        "suffix-letter ids:",
        [i for i in ids if re.search(r"[a-z]$", i)][:8],
    )
    print("ids split over >1 file:", [(i, c) for i, c in ids.items() if c > 1][:8])
    print(
        "other collections:",
        sorted(
            p.name for p in ROOT.iterdir() if p.is_dir() and not p.name.startswith(".")
        )[:40],
    )
    return files


def check_t99():
    f = next(T.rglob("T02n0099.xml"))
    text, marks, raw = flatten(f)
    print(
        "\nT99 titles:",
        [TITLE_RE.sub(r"\1", t)[:60] for t in TITLE_RE.findall(raw)[:4]],
    )
    print(
        "T99 <g> count:",
        len(G_RE.findall(raw)),
        "charDecl in file:",
        "<charDecl" in raw,
    )
    print("T99 flat chars:", len(text), "lb marks:", len(marks), "first:", marks[:2])
    # phrase that crosses the lb at 0120a06 in SA 470 (…凡夫身觸 | 生諸受…)
    for q in ("凡夫身觸生諸受", "諸比丘白佛"):
        i = text.find(q)
        print(f"  {q!r} at {i} -> line {line_at(marks, i) if i >= 0 else None}")
    # is the crossing real? show raw around 0120a06
    j = raw.find('n="0120a06"')
    print("  raw around 0120a06:", re.sub(r"\s+", " ", raw[j - 120 : j + 60]))
    print("  flat sample:", text[text.find("如是我聞") : text.find("如是我聞") + 60])


def speed(files, q):
    def run():
        n_hits, per = 0, collections.Counter()
        for f in files:
            text, _, _ = flatten(f)
            c = text.count(q)
            if c:
                per[f.stem] += c
                n_hits += c
        return n_hits, per

    n, per = run()  # warm-up
    ts = []
    for _ in range(3):
        t = time.time()
        n, per = run()
        ts.append(time.time() - t)
    print(
        f"\nspeed {q!r}: runs {[round(x, 1) for x in ts]} median {statistics.median(ts):.1f}s hits {n} texts {len(per)} top {per.most_common(3)}"
    )


if __name__ == "__main__":
    files = layout()
    check_t99()
    if "--speed" in sys.argv:
        speed(files, "涅槃")
