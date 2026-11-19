import concurrent.futures
import hashlib
import json
from pathlib import Path
import re
from datetime import datetime, timezone

from bs4 import BeautifulSoup
import requests


PAPERS = {
    "MMLU": "2009.03300", "BBH": "2210.09261", "HELM": "2211.09110",
    "Lottery": "2107.07002", "SocialChoice": "2312.03121",
    "Cheater": "2311.01964", "Rephrased": "2311.04850",
    "GPQA": "2311.12022", "IFEval": "2311.07911", "MMLUPro": "2406.01574",
    "MATH": "2103.03874", "MuSR": "2310.16049", "BIGBench": "2206.04615",
    "Datasheets": "1803.09010", "ModelCards": "1810.03993",
    "CheckList": "2005.04118", "Underspecification": "2011.03395",
    "ImageNetReplication": "1902.10811", "TruthfulQA": "2109.07958",
    "NumPy": "2006.10256", "SciPy": "1907.10121",
}
DIRECT = {
    "Demsar": "https://www.jmlr.org/papers/v7/demsar06a.html",
    "Cawley": "https://www.jmlr.org/papers/v11/cawley10a.html",
    "Huber": "https://api.crossref.org/works/10.1214/aoms/1177703732",
    "Efron": "https://api.crossref.org/works/10.1214/aos/1176344552",
}


def retrieve(item):
    key, identifier = item
    path = Path("literature") / (key + ".json")
    if path.exists():
        return json.loads(path.read_text())
    url = "https://arxiv.org/abs/" + identifier if key in PAPERS else identifier
    response = requests.get(url, timeout=60)
    response.raise_for_status()
    if "api.crossref" in url:
        record = response.json()["message"]
        title = record["title"][0]
        authors = [author.get("given", "") + " " + author["family"] for author in record["author"]]
        year = record.get("published", record["created"])["date-parts"][0][0]
        abstract = BeautifulSoup(record.get("abstract", ""), "html.parser").get_text(" ", strip=True)
        if not abstract:
            landing = requests.get("https://api.openalex.org/works/https://doi.org/" + record["DOI"], timeout=60)
            landing.raise_for_status()
            inverted = landing.json().get("abstract_inverted_index", {})
            abstract = " ".join(word for _, word in sorted((position, word) for word, positions in inverted.items() for position in positions))
        bib = f"@article{{{key},\n title={{{title}}},\n author={{{' and '.join(authors)}}},\n year={{{year}}},\n journal={{{record.get('container-title', [''])[0]}}},\n doi={{{record['DOI']}}}\n}}"
    else:
        soup = BeautifulSoup(response.text, "html.parser")
        def metadata(name):
            return [node.get("content", "") for node in soup.find_all("meta", {"name": name})]
        title = metadata("citation_title")[0]
        authors = metadata("citation_author")
        date = metadata("citation_date") or metadata("citation_publication_date")
        year = re.search(r"\d{4}", date[0]).group()
        section = soup.select_one("blockquote.abstract") or soup.select_one("#abstract") or soup.select_one(".abstract")
        abstract = section.get_text(" ", strip=True) if section else ""
        bib = f"@article{{{key},\n title={{{title}}},\n author={{{' and '.join(authors)}}},\n year={{{year}}},\n journal={{{'arXiv preprint arXiv:' + identifier if key in PAPERS else 'Journal of Machine Learning Research'}}},\n url={{{url}}}\n}}"
    if not abstract:
        raise RuntimeError("No substantive abstract for " + key)
    if len(authors) > 8:
        bib = bib.replace(" and ".join(authors), " and ".join(authors[:6]) + " and others")
    result = {"id": key, "title": title, "authors": authors, "year": year, "url": url,
              "abstract": abstract, "bibtex": bib, "retrieved_utc": "2026-11-17",
              "access_scope": "Canonical record metadata and abstract only; no citation graph or related links followed."}
    path.write_text(json.dumps(result, indent=2))
    return result


def main():
    Path("literature").mkdir(exist_ok=True)
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        records = list(executor.map(retrieve, list(PAPERS.items()) + list(DIRECT.items())))
    for record in records:
        authors = record["authors"]
        if len(authors) > 8:
            record["bibtex"] = record["bibtex"].replace(" and ".join(authors), " and ".join(authors[:6]) + " and others")
        record["bibtex"] = record["bibtex"].replace("&", r"\&").replace("_", r"\_").replace("%", r"\%")
        record["bibtex"] = record["bibtex"].replace("title={" + record["title"].replace("&", r"\&") + "}", "title={{" + record["title"].replace("&", r"\&") + "}}")
    Path("references.bib").write_text("\n\n".join(record["bibtex"] for record in records) + "\n")
    provenance = []
    for record in records:
        path = "literature/" + record["id"] + ".json"
        provenance.append({"id": record["id"], "citation_key": record["id"], "title": record["title"],
                           "paper_id": record["url"], "query": "Exact permitted canonical record: " + record["title"],
                           "source_url": record["url"], "retrieved_at": record["retrieved_utc"],
                           "url": record["url"], "source": "arxiv" if record["id"] in PAPERS else "publisher",
                           "evidence_path": path, "sha256": hashlib.sha256(Path(path).read_bytes()).hexdigest(),
                           "reading_scope": record["access_scope"]})
    Path("references_provenance.json").write_text(json.dumps({"references": provenance, "count": len(provenance),
        "generated_at": datetime.now(timezone.utc).isoformat(), "queries": [item["query"] for item in provenance]}, indent=2))
    for record in records:
        print(record["id"], record["title"], "\n", record["abstract"], "\n")


if __name__ == "__main__":
    main()
