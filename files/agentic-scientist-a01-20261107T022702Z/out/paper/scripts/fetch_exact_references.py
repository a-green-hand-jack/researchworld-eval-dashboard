import concurrent.futures
import datetime
import hashlib
import json
from pathlib import Path

import requests


ARXIV = {
    "Hendrycks2020MMLU": "2009.03300",
    "Suzgun2022BBH": "2210.09261",
    "Liang2022HELM": "2211.09110",
    "Dehghani2021Lottery": "2107.07002",
    "Lanctot2023SocialChoice": "2312.03121",
    "Singh2025Illusion": "2504.20879",
    "Zhou2023Cheater": "2311.01964",
    "Yang2023Rephrased": "2311.04850",
    "Chen2026Strategic": "2603.08371",
    "Dodge2019Reporting": "1909.03004",
}
DOIS = {
    "Gao2023Harness": "10.5281/zenodo.10256836",
    "Brandt2016Handbook": "10.1017/CBO9781107446984",
    "Arrow1950Difficulty": "10.1086/256963",
    "Gibbard1973Manipulation": "10.2307/1914083",
    "Satterthwaite1975Strategy": "10.1016/0022-0531(75)90050-2",
    "Huber1964Robust": "10.1214/aoms/1177703732",
    "Hampel1974Influence": "10.1080/01621459.1974.10482962",
    "Bartholdi1989Manipulation": "10.1007/BF00295861",
    "Bartholdi1992Control": "10.1016/0895-7177(92)90085-Y",
    "Faliszewski2009Bribery": "10.1613/jair.2676",
    "Nemhauser1978Submodular": "10.1007/BF01588971",
    "Hoeffding1963Bounds": "10.1080/01621459.1963.10500830",
    "Efron1979Bootstrap": "10.1214/aos/1176344552",
    "Dwork2001Rank": "10.1145/371920.372165",
}


def fetch(item):
    key, identifier, kind = item
    output = Path("literature")
    output.mkdir(exist_ok=True)
    record = {"id": "ref.exact." + key, "citation_key": key,
              "identifier": identifier, "retrieved_at": datetime.datetime.now(datetime.timezone.utc).isoformat()}
    try:
        if kind == "arxiv":
            url = "https://arxiv.org/pdf/" + identifier
            response = requests.get(url, timeout=90)
            response.raise_for_status()
            if not response.content.startswith(b"%PDF"):
                raise ValueError("Not a PDF")
            path = output / (key + ".pdf")
            path.write_bytes(response.content)
            record.update(source_url=url, pdf_path=str(path), sha256=hashlib.sha256(response.content).hexdigest())
        else:
            url = "https://api.openalex.org/works/https://doi.org/" + identifier
            response = requests.get(url, timeout=60)
            response.raise_for_status()
            metadata = response.json()
            path = output / (key + ".metadata.json")
            path.write_text(json.dumps(metadata, indent=2))
            record.update(source_url=url, metadata_path=str(path), title=metadata["title"], year=metadata["publication_year"])
            inverted = metadata.get("abstract_inverted_index") or {}
            ordered = {position: word for word, positions in inverted.items() for position in positions}
            abstract = " ".join(ordered[position] for position in sorted(ordered))
            record["abstract"] = abstract
            if abstract:
                (output / (key + ".abstract.txt")).write_text(abstract)
        record["status"] = "retrieved_not_yet_reviewed"
    except Exception as error:
        record.update(status="failed", error=str(error))
    return record


if __name__ == "__main__":
    items = [(key, value, "arxiv") for key, value in ARXIV.items()]
    items += [(key, value, "doi") for key, value in DOIS.items()]
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        records = list(executor.map(fetch, items))
    Path("literature/retrieval.json").write_text(json.dumps(records, indent=2))
    for record in records:
        print(record["citation_key"], record["status"], record.get("title", ""), len(record.get("abstract", "")))
