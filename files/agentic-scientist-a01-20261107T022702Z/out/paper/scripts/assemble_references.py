import concurrent.futures
import datetime
import hashlib
import json
from pathlib import Path

import pymupdf
import requests

from fetch_exact_references import ARXIV, DOIS, fetch


EXCLUDED = {"Arrow1950Difficulty", "Satterthwaite1975Strategy",
            "Bartholdi1989Manipulation", "Bartholdi1992Control"}
ADDED = {
    "Rousseeuw1984Median": "10.1080/01621459.1984.10477105",
    "Bertsimas2004Price": "10.1287/opre.1030.0065",
    "Bertsimas2011Theory": "10.1137/080734510",
    "BenTal1998Robust": "10.1287/moor.23.4.769",
}


def abstract_from_metadata(metadata):
    inverted = metadata.get("abstract_inverted_index") or {}
    words = {position: word for word, positions in inverted.items() for position in positions}
    return " ".join(words[position] for position in sorted(words))


def metadata_arxiv(item):
    key, identifier = item
    path = Path("literature") / (key + ".metadata.json")
    if not path.exists():
        response = requests.get("https://api.openalex.org/works/https://doi.org/10.48550/arXiv." + identifier, timeout=60)
        response.raise_for_status()
        path.write_text(json.dumps(response.json(), indent=2))
    return key


def escape(text):
    return text.replace("&", r"\&").replace("%", r"\%").replace("_", r"\_")


def main():
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
        list(executor.map(metadata_arxiv, ARXIV.items()))
        list(executor.map(fetch, [(key, doi, "doi") for key, doi in ADDED.items()]))
    keys = list(ARXIV) + [key for key in DOIS if key not in EXCLUDED] + list(ADDED)
    records = []
    bib_entries = []
    for key in keys:
        path = Path("literature") / (key + ".metadata.json")
        metadata = json.loads(path.read_text())
        title = metadata["title"]
        names = [author["author"]["display_name"] for author in metadata["authorships"]]
        if key == "Suzgun2022BBH":
            names[:3] = ["Mirac Suzgun", "Nathan Scales", "Nathanael Schärli"]
        if key == "Liang2022HELM":
            names[:3] = ["Percy Liang", "Rishi Bommasani", "Tony Lee"]
        if key == "Lanctot2023SocialChoice":
            names[:3] = ["Marc Lanctot", "Kate Larson", "Yoram Bachrach"]
        authors = " and ".join(names[:3] + ["others"] if len(names) > 5 else names)
        abstract = abstract_from_metadata(metadata)
        content_path = Path("literature") / (key + ".abstract.txt")
        pdf_path = Path("literature") / (key + ".pdf")
        if pdf_path.exists():
            document = pymupdf.open(pdf_path)
            content_path = Path("literature") / (key + ".opening.txt")
            content_path.write_text("\n".join(page.get_text() for page in list(document)[:2]))
            read_scope = "opening pages and abstract; no citation links followed"
        elif abstract:
            content_path.write_text(abstract)
            read_scope = "substantive abstract supplied by OpenAlex; no full-text claim"
        else:
            raise ValueError("No substantive accessible content for " + key)
        identifier = "https://arxiv.org/abs/" + ARXIV[key] if key in ARXIV else metadata.get("doi")
        entry_type = "book" if key == "Brandt2016Handbook" else "article"
        if key == "Gao2023Harness":
            entry_type = "misc"
        authors_field = "editor" if entry_type == "book" else "author"
        extra = ""
        if key in ARXIV:
            extra = "  journal = {arXiv preprint arXiv:" + ARXIV[key] + "},\n"
        elif entry_type == "book":
            extra = "  publisher = {Cambridge University Press},\n"
        elif key == "Gao2023Harness":
            extra = "  howpublished = {Zenodo},\n"
        else:
            location = metadata.get("primary_location") or {}
            source = location.get("source") or {}
            if source.get("display_name"):
                extra += "  journal = {" + escape(source["display_name"]) + "},\n"
            details = metadata.get("biblio") or {}
            if details.get("volume"):
                extra += "  volume = {" + str(details["volume"]) + "},\n"
            if details.get("first_page") and details.get("last_page"):
                extra += "  pages = {" + str(details["first_page"]) + "--" + str(details["last_page"]) + "},\n"
        bib_entries.append("@" + entry_type + "{" + key + ",\n" +
                           "  " + authors_field + " = {" + escape(authors) + "},\n" +
                           "  title = {{" + escape(title) + "}},\n" +
                           "  year = {" + str(metadata["publication_year"]) + "},\n" +
                           extra +
                           "  url = {" + identifier + "}\n}\n")
        records.append({"id": "ref.exact." + key, "citation_key": key,
                        "title": title, "year": metadata["publication_year"],
                        "source_url": identifier, "metadata_path": str(path),
                        "content_path": str(content_path), "consultation_scope": read_scope,
                        "retrieved_at": datetime.datetime.now(datetime.timezone.utc).isoformat()})
    key = "Demsar2006Comparisons"
    pdf_path = Path("literature") / (key + ".pdf")
    document = pymupdf.open(pdf_path)
    content_path = Path("literature") / (key + ".opening.txt")
    content_path.write_text("\n".join(page.get_text() for page in list(document)[:2]))
    bib_entries.append("@article{Demsar2006Comparisons,\n author={Janez Demšar},\n title={{Statistical Comparisons of Classifiers over Multiple Data Sets}},\n journal={Journal of Machine Learning Research},\n volume={7},\n pages={1--30},\n year={2006},\n url={https://jmlr.org/papers/v7/demsar06a.html}\n}\n")
    records.append({"id": "ref.exact." + key, "citation_key": key,
                    "title": "Statistical Comparisons of Classifiers over Multiple Data Sets", "year": 2006,
                    "source_url": "https://jmlr.org/papers/v7/demsar06a.html",
                    "content_path": str(content_path), "consultation_scope": "opening pages and abstract",
                    "retrieved_at": datetime.datetime.now(datetime.timezone.utc).isoformat()})
    Path("references.bib").write_text("\n".join(bib_entries))
    Path("references_provenance.json").write_text(json.dumps({
        "references": records,
        "retrieval_policy": "Exact task-allowed identifiers, exact pre-2010 titles to repair mismatched identifiers, and exact foundational DOI endpoints only. No citation-graph traversal or related-content expansion.",
        "excluded_initial_records": "Off-topic initial metadata hits were not retained. Unavailable-content classics omitted. Incorrect DOI candidate for bribery was discarded after title mismatch; no substantive claim uses it.",
    }, indent=2))
    for record in records:
        print(record["citation_key"], record["title"], record["consultation_scope"])
    print("Total:", len(records))


if __name__ == "__main__":
    main()
