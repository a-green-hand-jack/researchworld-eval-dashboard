"""Citation-enrichment pass: add component-benchmark and adaptive-evaluation references via OpenAlex,
drop four peripheral entries to stay within the 30-reference cap. Idempotent."""
import json, re, time, urllib.parse, urllib.request, datetime
ADD = [
 ("Hofmann2025Fluid","Fluid Language Model Benchmarking","arXiv preprint"),
 ("Zhou2023IFEval","Instruction-Following Evaluation for Large Language Models","arXiv preprint"),
 ("Suzgun2023BBH","Challenging BIG-Bench Tasks and Whether Chain-of-Thought Can Solve Them","Findings of the Association for Computational Linguistics: ACL 2023"),
 ("Rein2023GPQA","GPQA: A Graduate-Level Google-Proof Q&A Benchmark","arXiv preprint"),
 ("Sprague2023MuSR","MuSR: Testing the Limits of Chain-of-thought with Multistep Soft Reasoning","arXiv preprint"),
 ("Wang2024MMLUPro","MMLU-Pro: A More Robust and Challenging Multi-Task Language Understanding Benchmark","Advances in Neural Information Processing Systems"),
 ("Hendrycks2021MATH","Measuring Mathematical Problem Solving With the MATH Dataset","arXiv preprint"),
]
DROP = {"Zhuo2024BigCodeBench","Zheng2023MTBench","Vania2021ComparingTestSets","Krause2007ObservationSelection"}
def norm(s): return re.sub(r'[^a-z0-9]+',' ',s.lower()).strip()
def get(url):
    for i in range(3):
        try: return json.load(urllib.request.urlopen(urllib.request.Request(url,headers={"User-Agent":"mailto:none@example.com"}),timeout=30))
        except Exception: time.sleep(2)
bib=open("references.bib").read()
prov=json.load(open("references_provenance.json"))
entries=re.split(r'\n(?=@)',bib.strip())
keep=[e for e in entries if re.match(r'@\w+\{([^,]+),',e).group(1) not in DROP]
prov["references"]=[r for r in prov["references"] if r.get("citation_key") not in DROP]
have={re.match(r'@\w+\{([^,]+),',e).group(1) for e in keep}
for key,title,venue in ADD:
    if key in have: continue
    url="https://api.openalex.org/works?search="+urllib.parse.quote(title)+"&per-page=8"
    d=get(url); best=None
    for w in d["results"]:
        if norm(w["title"])==norm(title) and (best is None or (w.get("cited_by_count") or 0)>(best.get("cited_by_count") or 0)): best=w
    assert best,key
    auth=" and ".join(a["author"]["display_name"] for a in best["authorships"])
    kind="inproceedings" if "Conference" in venue or "Advances" in venue or "Findings" in venue else "article"
    fld="booktitle" if kind=="inproceedings" else "journal"
    keep.append("@%s{%s,\n  author = {%s},\n  title = {{%s}},\n  year = {%s},\n  %s = {%s}\n}"%(kind,key,auth,best["title"],best["publication_year"],fld,venue))
    prov["references"].append(dict(citation_count=best.get("cited_by_count"),citation_key=key,id="ref.openalex."+best["id"].rsplit("/",1)[-1],
        paper_id=best["id"].rsplit("/",1)[-1],query=title,retrieved_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),
        source_url=url,title=best["title"],venue=venue,year=best["publication_year"]))
    print("added",key,best["publication_year"],auth[:70])
open("references.bib","w").write("\n\n".join(keep)+"\n")
prov["count"]=len(prov["references"])
json.dump(prov,open("references_provenance.json","w"),indent=1)
print(len(keep),prov["count"])
