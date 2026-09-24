"""Probe 84000 data-tei: layout, titles, translators, toh ids, search speed."""

import re
import statistics
import time
from pathlib import Path

ROOT = Path.home() / "MyFiles/2_Resources/84000"
TAG_RE = re.compile(r"<[^>]+>")

print("top:", sorted(p.name for p in ROOT.iterdir()))
for sub in (
    "translations/kangyur/translations",
    "translations/tengyur/translations",
    "translations/tengyur/publications",
    "translations/tengyur/placeholders",
    "translations/kangyur/placeholders",
):
    p = ROOT / sub
    print(sub, "->", len(list(p.glob("*.xml"))) if p.exists() else "missing")

files = sorted((ROOT / "translations/kangyur/translations").glob("*.xml"))
f = next(x for x in files if "toh297" in x.name)
raw = f.read_text(encoding="utf-8")
print("\nfile:", f.name, len(raw))
for tag in ("title", "author", "editor", "bibl", "idno", "sourceDesc"):
    ms = re.findall(rf"<{tag}\b[^>]*>(.*?)</{tag}>", raw, re.S)[:4]
    print(tag, [re.sub(r"\s+", " ", TAG_RE.sub("", m))[:80] for m in ms])
print("title attrs:", re.findall(r"<title\b[^>]*>", raw)[:6])
print("author attrs:", re.findall(r"<author\b[^>]*>", raw)[:4])
print(
    "idno/bibl key attrs:",
    re.findall(r'<bibl\b[^>]*key="[^"]*"', raw)[:3],
    re.findall(r"<idno\b[^>]*>", raw)[:3],
)
print(
    "body <p> count:",
    len(re.findall(r"<p\b", raw)),
    "notes:",
    len(re.findall(r"<note\b", raw)),
)

# publications folder check
pub = ROOT / "translations/tengyur/publications"
if pub.exists():
    pf = sorted(pub.rglob("*.xml"))
    print("\ntengyur publications files:", len(pf), [x.name for x in pf[:3]])
    if pf:
        r = pf[0].read_text(encoding="utf-8")
        print("  first has <p>:", len(re.findall(r"<p\b", r)), "size", len(r))


def search(q):
    ql = q.lower()
    hits = 0
    for x in files:
        body = x.read_text(encoding="utf-8").split("<text", 1)[-1]
        body = re.sub(r"<note\b.*?</note>", "", body, flags=re.S)
        for p in re.findall(r"<p\b[^>]*>(.*?)</p>", body, re.S):
            if ql in re.sub(r"\s+", " ", TAG_RE.sub("", p)).lower():
                hits += 1
    return hits


n = search("four immeasurables")  # warm-up
ts = []
for _ in range(3):
    t = time.time()
    n = search("four immeasurables")
    ts.append(time.time() - t)
print(
    f"\nsearch 'four immeasurables': {[round(x, 1) for x in ts]} median {statistics.median(ts):.1f}s paragraphs {n}"
)
