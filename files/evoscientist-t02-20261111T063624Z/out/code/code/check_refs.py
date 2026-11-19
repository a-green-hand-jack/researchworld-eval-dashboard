"""Fetch arXiv abstract-page titles for the starter-literature IDs we cite (sanity check that they exist)."""
import re, urllib.request
ids = ["2201.02177", "2301.05217", "2210.01117", "2309.02390", "2310.06110", "2303.06173", "2505.24832",
       "2205.10770", "1611.03530", "1912.02292", "1711.05101"]
for i in ids:
    try:
        html = urllib.request.urlopen(f"https://arxiv.org/abs/{i}", timeout=30).read().decode("utf8", "ignore")
        t = re.search(r"<title>(.*?)</title>", html, re.S).group(1).strip().replace("\n", " ")
        print(i, "|", t)
    except Exception as e:
        print(i, "ERR", e)
