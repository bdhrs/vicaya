import re
import statistics
import time
import collections
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
import cbeta_probe as cp

ROOT = cp.ROOT


def count(args):
    f, q = args
    text, _, _ = cp.flatten(Path(f))
    return f, text.count(q)


def run(files, q, w):
    per = collections.Counter()
    with ProcessPoolExecutor(max_workers=w) as ex:
        for f, c in ex.map(count, [(str(x), q) for x in files], chunksize=16):
            if c:
                per[Path(f).stem] += c
    return per


if __name__ == "__main__":
    raw = next(ROOT.rglob("T02n0099.xml")).read_text()
    print("title tags:", re.findall(r"<title[^>]*>[^<]*</title>", raw)[:5])
    text, marks, _ = cp.flatten(next(ROOT.rglob("T02n0099.xml")))
    gs = set(re.findall(r'<g ref="#(CB\d+)"', raw))
    decl = set(m.group(1) for m in cp.CHAR_RE.finditer(raw))
    print("gaiji refs", len(gs), "resolved by charDecl", len(gs & decl))
    print("leftover tags/entities in flat:", len(re.findall(r"[<>&]", text)))
    for coll, w in (("T", 8), ("T", 12), ("ALL", 12)):
        files = (
            sorted((ROOT / "T").rglob("*.xml"))
            if coll == "T"
            else [
                f
                for d in ROOT.iterdir()
                if d.is_dir() and d.name not in (".git", "schema")
                for f in d.rglob("*.xml")
            ]
        )
        per = run(files[:50], "涅槃", w)  # warm-up
        ts = []
        for _ in range(3):
            t = time.time()
            per = run(files, "涅槃", w)
            ts.append(time.time() - t)
        print(
            coll,
            len(files),
            "files workers",
            w,
            [round(x, 1) for x in ts],
            "median",
            round(statistics.median(ts), 1),
            "hits",
            sum(per.values()),
        )
