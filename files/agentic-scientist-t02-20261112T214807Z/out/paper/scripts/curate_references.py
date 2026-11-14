"""Curate only the exact authorized originals; never expand citation neighborhoods."""

import datetime
import hashlib
import json
from pathlib import Path

import pymupdf


ROOT = Path(__file__).resolve().parents[1]
ORIGINALS = Path("/tmp/paper-originals")
RECORDS = [
    ("2201.02177", "Power2022GrokkingGB", "Alethea Power and Yuri Burda and Harri Edwards and Igor Babuschkin and Vedant Misra", "Grokking: Generalization Beyond Overfitting on Small Algorithmic Datasets", 2022, "arXiv preprint arXiv:2201.02177"),
    ("2210.01117", "Liu2022OmnigrokGB", "Ziming Liu and Eric J. Michaud and Max Tegmark", "Omnigrok: Grokking Beyond Algorithmic Data", 2023, "International Conference on Learning Representations"),
    ("2310.06110", "Kumar2023GrokkingAT", "Tanishq Kumar and Blake Bordelon and Samuel J. Gershman and Cengiz Pehlevan", "Grokking as the Transition from Lazy to Rich Training Dynamics", 2024, "International Conference on Learning Representations"),
    ("2309.02390", "Varma2023ExplainingGT", "Vikrant Varma and Rohin Shah and Zachary Kenton and J{\\'a}nos Kram{\\'a}r and Ramana Kumar", "Explaining Grokking Through Circuit Efficiency", 2023, "arXiv preprint arXiv:2309.02390"),
    ("2301.05217", "Nanda2023Progress", "Neel Nanda and Lawrence Chan and Tom Lieberum and Jess Smith and Jacob Steinhardt", "Progress Measures for Grokking via Mechanistic Interpretability", 2023, "International Conference on Learning Representations"),
    ("2303.06173", "Davies2023Unifying", "Xander Davies and Lauro Langosco and David Krueger", "Unifying Grokking and Double Descent", 2023, "arXiv preprint arXiv:2303.06173"),
    ("1912.02292", "Nakkiran2020Double", "Preetum Nakkiran and Gal Kaplun and Yamini Bansal and Tristan Yang and Boaz Barak and Ilya Sutskever", "Deep Double Descent: Where Bigger Models and More Data Hurt", 2020, "International Conference on Learning Representations"),
    ("1711.05101", "Loshchilov2019AdamW", "Ilya Loshchilov and Frank Hutter", "Decoupled Weight Decay Regularization", 2019, "International Conference on Learning Representations"),
]


def main():
    bibliography = []
    references = []
    consulted_at = datetime.datetime.now(datetime.timezone.utc).isoformat()
    for identifier, key, authors, title, year, venue in RECORDS:
        pdf = ORIGINALS / (identifier + ".pdf")
        document = pymupdf.open(pdf)
        excerpt = "\n".join(document[index].get_text() for index in range(2))
        target = ROOT / "source_evidence/literature" / (identifier + "_opening.txt")
        target.parent.mkdir(exist_ok=True, parents=True)
        target.write_text(excerpt)
        references.append({"id": "ref.arxiv." + identifier, "citation_key": key,
                           "title": title, "year": year, "venue": venue,
                           "source_url": "https://arxiv.org/pdf/" + identifier,
                           "retrieved_at": datetime.datetime.fromtimestamp(pdf.stat().st_mtime, datetime.timezone.utc).isoformat(),
                           "consulted_at": consulted_at, "consulted_pages": [1], "extracted_pages": [1, 2],
                           "consultation_scope": "Abstract and opening first-page text; full-paper review is not claimed.",
                           "consulted_excerpt": str(target.relative_to(ROOT)),
                           "original_pdf_sha256": hashlib.sha256(pdf.read_bytes()).hexdigest(),
                           "scope": "exact user-authorized original; no citation/recommendation traversal"})
        bibliography.append("@misc{" + key + ",\n  author = {" + authors + "},\n  title = {{" + title + "}},\n  year = {" + str(year) + "},\n  howpublished = {" + venue + "},\n  eprint = {" + identifier + "},\n  archivePrefix = {arXiv}\n}\n")
    (ROOT / "references.bib").write_text("\n".join(bibliography))
    (ROOT / "references_provenance.json").write_text(json.dumps({
        "count": len(references), "generated_at": consulted_at, "references": references,
        "queries": [record["source_url"] for record in references],
        "scope_limitation": "The strategy limits consultation to eight authorized originals. The requested minimum of 25 references cannot be met without broadening that contract; unrelated retrieved records were excluded, not cited to fill a quota."
    }, indent=2) + "\n")


if __name__ == "__main__":
    main()
