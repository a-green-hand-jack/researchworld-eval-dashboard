"""Append verified metadata-backed references (arXiv API id lookup / Crossref DOI lookup) to references.bib
and references_provenance.json. Only works that were looked up by identifier are added."""
import urllib.request, re, json, time, datetime
ARXIV = {  # key: (arxiv id, venue string or None)
 "Wang2024MMLUPro": ("2406.01574", "Advances in Neural Information Processing Systems, Datasets and Benchmarks Track"),
 "Khattab2023DSPy": ("2310.03714", None),
 "OpsahlOng2024MIPRO": ("2406.11695", "Conference on Empirical Methods in Natural Language Processing"),
 "Polo2024EfficientMultiPrompt": ("2405.17202", "Advances in Neural Information Processing Systems"),
 "Shi2024PromptBAI": ("2402.09723", "Advances in Neural Information Processing Systems"),
 "Sclar2023Quantifying": ("2310.11324", "International Conference on Learning Representations"),
 "Blum2015Ladder": ("1502.04585", "International Conference on Machine Learning"),
 "Chernozhukov2013Gaussian": ("1212.6906", "Annals of Statistics"),
 "Jamieson2016SuccessiveHalving": ("1502.07943", "Artificial Intelligence and Statistics"),
 "Recht2019ImageNet": ("1902.10811", "International Conference on Machine Learning"),
 "Qwen2024Qwen25": ("2412.15115", None),
 "Hardt2014Hard": ("1408.1655", "Foundations of Computer Science"),
 "Miller2024ErrorBars": ("2411.00640", None),
}
CROSSREF = {
 "Berk2013ValidPSI": "10.1214/12-AOS1077",
 "Gneiting2007Scoring": "10.1198/016214506000001437",
 "Andrews2024InferenceOnWinners": "10.1093/qje/qjad043",
 "Efron2011Tweedie": "10.1198/jasa.2011.tm11181",
 "Efron1973Stein": "10.1080/01621459.1973.10481350",
 "Wilson1927Probable": "10.1080/01621459.1927.10502953",
 "Efron1997Bootstrap632": "10.1080/01621459.1997.10474007",
}
# Entries retrieved by an earlier broad query that are unrelated to this paper (clinical / unrelated-domain items)
# are pruned; only the adaptive-data-analysis entries and the identifier-verified works below remain.
KEEP_OLD = {"Dwork2014PreservingSV", "Dwork2015TheRH", "Dwork2015GeneralizationIA", "Feldman2017CalibratingNT",
            "Dwork2017GuiltfreeDR", "Marchant2024AdaptiveDA", "Ullman2017TechnicalPB"}
import os
have = set(re.findall(r'@\w+\{([^,]+),', open('references.bib').read()))
ARXIV = {k: v for k, v in ARXIV.items() if k not in have}; CROSSREF = {k: v for k, v in CROSSREF.items() if k not in have}
NEW_KEYS = set(ARXIV) | set(CROSSREF) | {"Wang2024MMLUPro","Khattab2023DSPy","OpsahlOng2024MIPRO","Polo2024EfficientMultiPrompt","Shi2024PromptBAI","Sclar2023Quantifying","Blum2015Ladder","Chernozhukov2013Gaussian","Jamieson2016SuccessiveHalving","Recht2019ImageNet","Qwen2024Qwen25","Berk2013ValidPSI","Gneiting2007Scoring","Andrews2024InferenceOnWinners"}
now = datetime.datetime.now(datetime.timezone.utc).isoformat()
bib, prov = [], []
def fam_given(n):
    n = n.strip(); p = n.split()
    return n
for key, (aid, venue) in ARXIV.items():
    u = f"https://export.arxiv.org/api/query?id_list={aid}"
    t = urllib.request.urlopen(urllib.request.Request(u, headers={'User-Agent': 'paper-agent/1.0'}), timeout=30).read().decode()
    e = t.split('<entry>')[1]
    title = re.sub(r'\s+', ' ', re.search(r'<title>(.*?)</title>', e, re.S).group(1)).strip()
    authors = [a.strip() for a in re.findall(r'<name>(.*?)</name>', e) if a.strip() not in (':',)]
    year = re.search(r'<published>(\d{4})', e).group(1)
    if key == "Qwen2024Qwen25":
        authors = ["Qwen Team"]
    bib.append(f"@Article{{{key},\n author = {{{' and '.join(authors)}}},\n journal = {{arXiv preprint arXiv:{aid}}},\n title = {{{title}}},\n year = {{{year}}}\n}}\n")
    prov.append(dict(citation_key=key, id=f"ref.arxiv.{aid}", paper_id=f"arXiv:{aid}", title=title, venue=venue or "arXiv", year=int(year),
                     source_url=u, retrieved_at=now, query="identifier lookup (arXiv API)", citation_count=None))
    time.sleep(3)
for key, doi in CROSSREF.items():
    u = "https://api.crossref.org/works/" + doi
    r = json.load(urllib.request.urlopen(urllib.request.Request(u, headers={'User-Agent': 'paper-agent/1.0 (mailto:none@example.com)'}), timeout=30))['message']
    authors = [f"{a.get('family','')}, {a.get('given','')}" for a in r['author']]
    year = r['issued']['date-parts'][0][0]
    journal = r['container-title'][0]
    f = [f" author = {{{' and '.join(authors)}}}", f" journal = {{{journal}}}", f" title = {{{r['title'][0]}}}", f" volume = {{{r.get('volume','')}}}"]
    if r.get('issue'): f.append(f" number = {{{r['issue']}}}")
    if r.get('page'): f.append(f" pages = {{{r['page']}}}")
    f += [f" year = {{{year}}}", f" doi = {{{doi}}}"]
    bib.append(f"@Article{{{key},\n" + ",\n".join(f) + "\n}\n")
    prov.append(dict(citation_key=key, id=f"ref.crossref.{doi}", paper_id=f"doi:{doi}", title=r['title'][0], venue=journal, year=year,
                     source_url=u, retrieved_at=now, query="identifier lookup (Crossref DOI)", citation_count=None))
entries = [e for e in re.split(r'\n(?=@)', open('references.bib').read().strip()) if e.strip()]
entries = [e for e in entries if re.match(r'@\w+\{([^,]+),', e).group(1) in KEEP_OLD or re.match(r'@\w+\{([^,]+),', e).group(1) in have - KEEP_OLD and False or re.match(r'@\w+\{([^,]+),', e).group(1) in NEW_KEYS]
open('references.bib', 'w').write("\n\n".join(entries + bib) + "\n")
p = json.load(open('references_provenance.json'))
p['references'] = [r for r in p['references'] if r['citation_key'] in KEEP_OLD or r['citation_key'] in NEW_KEYS] + prov; p['count'] = len(p['references'])
json.dump(p, open('references_provenance.json', 'w'), indent=1)
print(len(prov), 'added')
