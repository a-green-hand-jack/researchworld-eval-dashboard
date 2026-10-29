import re
x=open("tmp/arxiv.xml").read()
for e in x.split("<entry>")[1:]:
    t=re.search(r"<title>(.*?)</title>",e,re.S).group(1); s=re.search(r"<summary>(.*?)</summary>",e,re.S).group(1)
    print("##",t.strip()); print(" ".join(s.split())[:1500]); print()
