import concurrent.futures
import datetime
import html
import json
import re
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parent.parent
RECORDS = [
    ("Angelopoulos2023PPI", "10.1126/science.adi6000"),
    ("Chernozhukov2018DML", "10.1111/ectj.12097"),
    ("Wilson1927", "10.1080/01621459.1927.10502953"),
    ("ClopperPearson1934", "10.1093/biomet/26.4.404"),
    ("AgrestiCoull1998", "10.1080/00031305.1998.10480550"),
    ("BrownCaiDasGupta2001", "10.1214/ss/1009213286"),
    ("Hoeffding1963", "10.1080/01621459.1963.10500830"),
    ("Audibert2009", "10.1016/j.tcs.2009.01.012"),
    ("Golub1979GCV", "10.1080/00401706.1979.10489751"),
    ("HoerlKennard1970", "10.1080/00401706.1970.10488634"),
    ("Stone1974", "10.1111/j.2517-6161.1974.tb00994.x"),
    ("EfronStein1981", "10.1214/aos/1176345462"),
    ("Hastie2009", "10.1007/978-0-387-84858-7"),
    ("Glasserman2004", "10.1007/978-0-387-21617-1"),
    ("Sarndal1992", "10.1007/978-1-4612-4378-6"),
    ("DevilleSarndal1992", "10.1080/01621459.1992.10475217"),
    ("LittleRubin2019", "10.1002/9781119013563"),
    ("Neyman1934", "10.2307/2342197"),
    ("Student1908", "10.1093/biomet/6.1.1"),
    ("Holm1979", "10.2307/4615733"),
    ("Cochran1977", "10.1002/9781118162934"),
    ("Newey1994", "10.2307/2951755"),
    ("Robinson1988", "10.2307/1912705"),
]


def clean(text):
    return html.unescape(re.sub("<[^>]+>", " ", text or "")).strip()


def retrieve(record):
    key, doi = record
    url = "https://api.crossref.org/works/" + requests.utils.quote(doi, safe="")
    response = requests.get(url, timeout=50)
    response.raise_for_status()
    message = response.json()["message"]
    title = clean(message["title"][0])
    abstract = clean(message.get("abstract"))
    if not abstract:
        try:
            lookup = requests.get("https://api.openalex.org/works/https://doi.org/" + doi, timeout=30)
            if lookup.ok:
                inverted = lookup.json().get("abstract_inverted_index") or {}
                words = {position: word for word, positions in inverted.items() for position in positions}
                abstract = " ".join(words[position] for position in sorted(words))
        except requests.RequestException:
            pass
    authors = " and ".join((author.get("given", "") + " " + author.get("family", "")).strip() for author in message.get("author", []))
    year = message.get("published", message.get("issued"))["date-parts"][0][0]
    container = message.get("container-title", [""])[0] if message.get("container-title") else ""
    kind = "book" if message.get("type") == "book" else "article"
    fields = {"title": "{" + title + "}", "author": authors, "year": str(year), "doi": doi}
    if container:
        fields["journal"] = container
    if message.get("publisher") and kind == "book":
        fields["publisher"] = message["publisher"]
    for field in ["volume", "issue", "page"]:
        if message.get(field):
            fields[{"issue": "number", "page": "pages"}.get(field, field)] = message[field]
    bib = "@" + kind + "{" + key + ",\n" + ",\n".join("  " + field + " = {" + str(value) + "}" for field, value in fields.items()) + "\n}\n"
    excerpt = {"title": title, "doi": doi, "metadata_source": url, "abstract": abstract,
               "scope": "Exact allowlisted work only; no references, cited-by lists, or related-work pages accessed."}
    (ROOT / "literature" / (key + ".json")).write_text(json.dumps(excerpt, indent=2) + "\n")
    provenance = {"id": "ref.doi." + doi.lower(), "paper_id": doi, "citation_key": key, "title": title,
                  "year": year, "venue": container, "query": "Exact DOI " + doi, "source_url": url,
                  "retrieved_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
                  "consulted_text_path": "literature/" + key + ".json", "abstract_available": bool(abstract)}
    return key, bib, provenance, abstract


def main():
    output = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as pool:
        for future in concurrent.futures.as_completed([pool.submit(retrieve, record) for record in RECORDS]):
            try:
                result = future.result()
                output.append(result)
                print(result[0], result[2]["title"], "ABSTRACT", result[3][:160], flush=True)
            except Exception as error:
                print("FAILED", str(error), flush=True)
    output.sort(key=lambda value: value[0])
    (ROOT / "literature" / "retrieved.bib").write_text("\n".join(value[1] for value in output))
    (ROOT / "literature" / "retrieved_provenance.json").write_text(json.dumps({
        "generated_at": datetime.datetime.now(datetime.timezone.utc).isoformat(), "count": len(output),
        "queries": ["Exact pre-screened DOI lookup; no citation graph traversal"],
        "references": [value[2] for value in output]}, indent=2) + "\n")


if __name__ == "__main__":
    main()
