"""Verify existence/metadata of cited arXiv papers (metadata only, via the public arXiv API).
Run: python code/arxiv_check.py   -> prints id | title | first-version date | first authors.
Used to make sure every arXiv reference in the paper exists and the metadata in references.bib is right."""
import re
import urllib.parse
import urllib.request

ids = ["1305.6156", "1305.6979", "1404.7530", "1808.08683", "2012.08591", "2205.14552", "2302.04997", "2311.14042",
       "1102.2166", "1711.06399", "2009.02297", "2111.04219", "2312.04026"]
titles = ["Estimating the total treatment effect in randomized experiments with unknown network structure",
          "Random graph asymptotics for treatment effect estimation under network interference",
          ]


def show(x):
    for e in re.findall(r"<entry>(.*?)</entry>", x, re.S):
        print(re.search(r"<id>(.*?)</id>", e).group(1), "|", re.sub(r"\s+", " ", re.search(r"<title>(.*?)</title>", e, re.S).group(1)), "|",
              re.search(r"<published>(.*?)</published>", e).group(1)[:10], "|", re.findall(r"<name>(.*?)</name>", e)[:3])


x = urllib.request.urlopen("http://export.arxiv.org/api/query?id_list=%s&max_results=50" % ",".join(ids), timeout=60).read().decode()
show(x)
print("--- title queries")
for t in titles:
    q = urllib.parse.quote('ti:"%s"' % t)
    show(urllib.request.urlopen("http://export.arxiv.org/api/query?search_query=%s&max_results=2" % q, timeout=60).read().decode())
