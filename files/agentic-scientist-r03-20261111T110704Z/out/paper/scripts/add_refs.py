"""Fetch real bibliographic records from OpenAlex by title and rebuild references.bib + provenance.
Keeps already-retrieved relevant entries (SubLIME, SimBA, From Benchmarks to Skills, Mapping Overlaps)."""
import json, re, sys, time, urllib.parse, urllib.request, datetime
TITLES = [
 ("Hendrycks2021MMLU","Measuring Massive Multitask Language Understanding"),
 ("Muennighoff2023MTEB","MTEB: Massive Text Embedding Benchmark"),
 ("Liang2023HELM","Holistic Evaluation of Language Models"),
 ("Zheng2023MTBench","Judging LLM-as-a-judge with MT-Bench and Chatbot Arena"),
 ("Polo2024TinyBenchmarks","tinyBenchmarks: evaluating LLMs with fewer examples"),
 ("Kipnis2024Metabench","metabench - A Sparse Benchmark of Reasoning and Knowledge in Large Language Models"),
 ("Perlitz2024BenchBench","Do These LLM Benchmarks Agree? Fixing Benchmark Evaluation with BenchBench"),
 ("Ruan2024ObservationalScaling","Observational Scaling Laws and the Predictability of Language Model Performance"),
 ("Polo2024Sloth","Sloth: scaling laws for LLM skills to predict multi-benchmark performance across families"),
 ("Zhuo2024BigCodeBench","BigCodeBench: Benchmarking Code Generation with Diverse Function Calls and Complex Instructions"),
 ("Dempster1977EM","Maximum Likelihood from Incomplete Data Via the EM Algorithm"),
 ("Wolpert1992Stacked","Stacked generalization"),
 ("Breiman1996Stacked","Stacked regressions"),
 ("Candes2009MatrixCompletion","Exact Matrix Completion via Convex Optimization"),
 ("Mazumder2010SoftImpute","Spectral Regularization Algorithms for Learning Large Incomplete Matrices"),
 ("Salakhutdinov2007PMF","Probabilistic Matrix Factorization"),
 ("Krause2008NearOptimalSensor","Near-Optimal Sensor Placements in Gaussian Processes: Theory, Efficient Algorithms and Empirical Studies"),
 ("Nemhauser1978Submodular","An analysis of approximations for maximizing submodular set functions—I"),
 ("Rubin1976Inference","Inference and missing data"),
 ("Little2019Missing","Statistical Analysis with Missing Data"),
 ("Hastie2009ESL","The Elements of Statistical Learning: Data Mining, Inference, and Prediction"),
 ("Chaloner1995BayesianDesign","Bayesian Experimental Design: A Review"),
 ("Embretson2000IRT","Item Response Theory for Psychologists"),
 ("Vania2021ComparingTestSets","Comparing Test Sets with Item Response Theory"),
 ("Vivek2024AnchorPoints","Anchor Points: Benchmarking Models with Much Fewer Examples"),
 ("Srivastava2023BIGbench","Beyond the Imitation Game: Quantifying and extrapolating the capabilities of language models"),
 ("Zellers2019HellaSwag","HellaSwag: Can a Machine Really Finish Your Sentence?"),
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
json.dump(out,open("scripts/_fetched_refs.json","w"),indent=1)
