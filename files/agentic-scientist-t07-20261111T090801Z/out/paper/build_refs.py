"""Rebuild references.bib + references_provenance.json from Semantic Scholar records (arXiv ids / exact titles)."""
import json, re, time, urllib.request, urllib.parse, datetime
ARXIV = ["2309.08638","2402.14992","2407.12844","2409.03563","2410.05952","2506.07673","2601.13885","2406.01574",
 "2412.06745","2211.09110","2405.17202","2308.11696","2306.10512","2301.09633","2009.03300","2210.09261","2311.12022",
 "2311.07911","2310.16049","1803.05457","2110.14168","2308.11462","2009.13081","2406.10229"]
TITLES = ["Evaluation Examples are not Equally Informative: How should that change NLP Leaderboards?",
 "Stacked regressions","Stacked generalization","The equivalence of two extremum problems"]
FIELDS="paperId,title,year,venue,citationCount,citationStyles,url,externalIds"
def get(url, data=None):
    for a in range(8):
        try:
            req=urllib.request.Request(url, data=data, headers={"Content-Type":"application/json"})
            return json.loads(urllib.request.urlopen(req,timeout=40).read())
        except Exception as e:
            print("retry",a,e); time.sleep(3*(a+1))
    return None
recs=[]
r=get(f"https://api.semanticscholar.org/graph/v1/paper/batch?fields={FIELDS}", json.dumps({"ids":["ARXIV:"+a for a in ARXIV]}).encode())
for a,p in zip(ARXIV,r or []):
    print(a, p and p["title"]); 
    if p: recs.append((p,"arXiv:"+a))
for t in TITLES:
    time.sleep(1.5)
    r=get("https://api.semanticscholar.org/graph/v1/paper/search/match?query="+urllib.parse.quote(t)+"&fields="+FIELDS)
    if r and r.get("data"):
        p=r["data"][0]; print(t,"->",p["title"],p.get("year"),p.get("venue")); recs.append((p,t))
json.dump([p for p,_ in recs], open("/tmp/refs_raw.json","w"), indent=1)
