import json
import re
import html
import glob

SC = "/home/bodhirasa/MyFiles/3_Active/dpd-db/resources/sc-data"
d = json.load(open(f"{SC}/relationship/parallels.json"))
grp = [
    g["parallels"]
    for g in d
    if "parallels" in g
    and any(r.split("#")[0].lstrip("~") in ("sn36.6",) for r in g["parallels"])
]
print("sn36.6 groups:", grp)


def read(uid):
    fs = glob.glob(f"{SC}/html_text/lzh/**/{uid}.html", recursive=True)
    if not fs:
        return None
    t = open(fs[0], encoding="utf-8").read()
    body = t.split("</header>", 1)[-1]
    body = re.sub(r"<a class='ref t' id='t(\w+)'[^>]*>.*?</a>", r"[\1]", body)
    paras = [
        html.unescape(re.sub(r"<[^>]+>", "", p)).strip()
        for p in re.findall(r"<p[^>]*>(.*?)</p>", body, re.S)
    ]
    return fs[0], "\n".join(p for p in paras if p)


res = read("sa470")
assert res is not None
p, txt = res
print(p)
print(txt[:300])
print("marker 0119c29 present:", "[0119c29]" in txt)
flat = re.sub(r"\[\w+\]", "", txt)
print(
    "phrase 身觸生諸受 in stripped:",
    "身觸生諸受" in flat,
    "| in raw file:",
    "身觸生諸受" in open(p).read(),
)
# coverage: how many lzh parallel uids across parallels.json resolve to html vs bilara
uids = set()
for g in d:
    for r in g.get("parallels", []):
        u = r.split("#")[0].lstrip("~")
        if re.match(r"(sa|ma|ea|da)(-\d)?[\d.]", u):
            uids.add(u)
html_ids = {
    f.rsplit("/", 1)[1][:-5]
    for f in glob.glob(f"{SC}/html_text/lzh/**/*.html", recursive=True)
}
bil = {
    f.rsplit("/", 1)[1].split("_root")[0]
    for f in glob.glob(f"{SC}/sc_bilara_data/root/lzh/**/*.json", recursive=True)
}
print(
    "agama uids in parallels:",
    len(uids),
    "in bilara:",
    len(uids & bil),
    "in html:",
    len(uids & html_ids),
    "in either:",
    len(uids & (bil | html_ids)),
)
print("sample missing:", sorted(uids - (bil | html_ids))[:15])
