"""Verifies (title/authors/date) of the cited arXiv references via the public arXiv API metadata."""
import re, urllib.request
IDS = ["2301.09633", "2311.01453", "2309.16598", "2403.03208", "2406.04291", "1608.00060", "2108.04884", "1308.3496"]
for i in IDS:
    t = urllib.request.urlopen(f"https://export.arxiv.org/api/query?id_list={i}", timeout=30).read().decode()
    e = t.split("<entry>")[1]
    title = re.search(r"<title>(.*?)</title>", e, re.S).group(1).strip().replace("\n", " ")
    au = ", ".join(re.findall(r"<name>(.*?)</name>", e))
    print(i, "|", title, "|", au[:140], "|", re.search(r"<published>(.*?)</published>", e).group(1))
