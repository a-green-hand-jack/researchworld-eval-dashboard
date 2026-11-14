"""Bibliographic-metadata check (arXiv API / JMLR page title) of references cited beyond starter_literature.md.
Already verified via Crossref in the same way: Varma & Simon 2006 (BMC Bioinf. 7:91), Efron & Tibshirani 1997 (JASA 92:548).
Only titles/authors were checked (no full texts were read for these entries)."""
import re, urllib.request
for aid in ["1502.07943", "1603.06560", "2412.15115"]:
    s = urllib.request.urlopen(f"http://export.arxiv.org/api/query?id_list={aid}", timeout=30).read().decode()
    print(aid, re.findall(r"<title>(.*?)</title>", s, re.S)[-1].strip().replace("\n", " "), re.findall(r"<name>(.*?)</name>", s)[:4])
s = urllib.request.urlopen("https://jmlr.org/papers/v11/cawley10a.html", timeout=30).read().decode(errors="ignore")
print("JMLR:", re.findall(r"<title>(.*?)</title>", s, re.S)[:1])
