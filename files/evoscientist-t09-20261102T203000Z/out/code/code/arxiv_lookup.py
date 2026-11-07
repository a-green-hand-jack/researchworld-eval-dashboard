"""Verify that cited papers exist: exact-title lookups against the arXiv API (no topical search)."""
import re, sys, time, subprocess, urllib.parse

titles = [l.strip() for l in open(sys.argv[1]) if l.strip()]
for t in titles:
    url = "https://export.arxiv.org/api/query?max_results=2&search_query=" + urllib.parse.quote('ti:"%s"' % t)
    out = subprocess.run(["curl", "-s", url], capture_output=True, text=True).stdout
    print("Q:", t)
    for e in re.findall(r"<entry>(.*?)</entry>", out, re.S):
        print("   ", re.search(r"<id>(.*?)</id>", e).group(1), "|",
              re.sub(r"\s+", " ", re.search(r"<title>(.*?)</title>", e, re.S).group(1)), "|",
              re.search(r"<published>(.*?)</published>", e).group(1)[:10], "|",
              ", ".join(re.findall(r"<name>(.*?)</name>", e)[:4]))
    time.sleep(3)
