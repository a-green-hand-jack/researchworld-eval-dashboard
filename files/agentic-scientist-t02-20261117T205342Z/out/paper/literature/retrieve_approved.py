import hashlib
import html
import json
import re
from datetime import datetime, timezone
from pathlib import Path

import requests

APPROVED = [
    ("2201.02177", "Power2022GrokkingGB"),
    ("1711.05101", "Loshchilov2017DecoupledWD"),
    ("2210.01117", "Liu2023Omnigrok"),
    ("2309.02390", "Varma2023ExplainingGT"),
    ("2310.06110", "Kumar2024LazyRich"),
    ("2303.06173", "Davies2023Unifying"),
    ("1912.02292", "Nakkiran2020DoubleDescent"),
    ("1611.03530", "Zhang2017Rethinking"),
]


def clean(text):
    return html.unescape(re.sub(r"<[^>]+>", "", text)).strip()


def retrieve():
    references = []
    entries = []
    for identifier, citation_key in APPROVED:
        url = f"https://arxiv.org/abs/{identifier}"
        response = requests.get(url, timeout=60)
        response.raise_for_status()
        document = response.text
        metadata = {}
        for name, value in re.findall(r'<meta\s+name="([^"]+)"\s+content="([^"]*)"', document):
            metadata.setdefault(name, []).append(html.unescape(value))
        title = metadata["citation_title"][0]
        authors = metadata["citation_author"]
        abstract_match = re.search(r'<blockquote class="abstract[^>]*>(.*?)</blockquote>', document, re.S)
        abstract = clean(abstract_match.group(1)).removeprefix("Abstract:").strip()
        text = f"Title: {title}\nAuthors: {'; '.join(authors)}\nSource: {url}\n\nAbstract consulted:\n{abstract}\n"
        path = Path(f"literature/{identifier}.txt")
        path.write_text(text)
        year = metadata["citation_date"][0].split("/")[0].split("-")[0]
        entries.append("@article{" + citation_key + ",\n  title={" + title + "},\n  author={" + " and ".join(authors) + "},\n  year={" + year + "},\n  journal={arXiv preprint arXiv:" + identifier + "},\n  url={" + url + "}\n}\n")
        references.append({"id": "ref.arxiv." + identifier, "citation_key": citation_key, "title": title,
                           "source_url": url, "year": int(year), "retrieved_at": datetime.now(timezone.utc).isoformat(),
                           "consulted_scope": "Title, authors, and abstract only; no citation graph or recommendations read",
                           "local_path": str(path), "sha256": hashlib.sha256(path.read_bytes()).hexdigest()})
    Path("references.bib").write_text("\n".join(entries))
    Path("references_provenance.json").write_text(json.dumps({"count": len(references), "references": references,
        "safety_boundary": "Only the eight exact identities approved by paper_strategy and the task starter list",
        "minimum_reference_count_unmet": True}, indent=2) + "\n")


if __name__ == "__main__":
    retrieve()
