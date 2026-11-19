"""Fetch real bibliographic records from OpenAlex by title and rebuild references.bib + provenance.
Keeps already-retrieved relevant entries (SubLIME, SimBA, From Benchmarks to Skills, Mapping Overlaps)."""
import json, re, sys, time, urllib.parse, urllib.request, datetime
TITLES = [
 ("Hoerl1970Ridge","Ridge Regression: Biased Estimation for Nonorthogonal Problems"),
 ("Lawson1974NNLS","Solving Least Squares Problems"),
 ("Krause2007ObservationSelection","Near-optimal observation selection using submodular functions"),
 ("Perlitz2023EfficientBenchmarking","Efficient Benchmarking of Language Models"),
 ("Srivastava2023BIGbench","Beyond the Imitation Game: Quantifying and extrapolating the capabilities of language models"),
 ("Vania2021ComparingTestSets","Comparing Test Sets with Item Response Theory"),
]
def norm(s): return re.sub(r'[^a-z0-9]+',' ',s.lower()).strip()
def get(url):
    for i in range(3):
        try:
            return json.load(urllib.request.urlopen(urllib.request.Request(url,headers={"User-Agent":"mailto:none@example.com"}),timeout=30))
        except Exception as e:
            time.sleep(2)
    return None
out=[]
for key,title in TITLES:
    url="https://api.openalex.org/works?search="+urllib.parse.quote(title)+"&per-page=8"
    d=get(url)
    best=None
    for w in (d or {}).get("results",[]):
        t=w.get("title") or ""
        if norm(t)==norm(title) or norm(t).startswith(norm(title)[:60]):
            if best is None or (w.get("cited_by_count") or 0)>(best.get("cited_by_count") or 0): best=w
    if not best:
        print("NOTFOUND",key); continue
    auth=" and ".join(a["author"]["display_name"] for a in best.get("authorships",[])[:12])
    if len(best.get("authorships",[]))>12: auth+=" and others"
    loc=(best.get("primary_location") or {}).get("source") or {}
    out.append(dict(key=key,title=best["title"],year=best.get("publication_year"),authors=auth,venue=loc.get("display_name"),
        oid=best["id"].rsplit("/",1)[-1],cites=best.get("cited_by_count"),doi=best.get("doi"),query=title,url=url))
    print("OK",key,"|",best["title"],"|",best.get("publication_year"),"|",loc.get("display_name"),"|",auth[:60])
json.dump(out,open("scripts/_fetched_refs2.json","w"),indent=1)
