import datetime
import html
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def main():
    raw = (ROOT / "literature/retrieved.bib").read_text()
    entries = {match.group(1): match.group(0) for match in re.finditer(r"@\w+\{([^,]+),.*?\n\}", raw, re.S)}
    registry = json.loads((ROOT / "literature/retrieved_provenance.json").read_text())
    refs = {value["citation_key"]: value for value in registry["references"]}
    keep = ["Angelopoulos2023PPI", "BrownCaiDasGupta2001",
            "Golub1979GCV", "HoerlKennard1970", "Stone1974", "EfronStein1981", "Hastie2009",
            "Glasserman2004", "Sarndal1992", "DevilleSarndal1992", "LittleRubin2019", "Robinson1988"]
    entries = {key: entries[key] for key in keep}
    refs = {key: refs[key] for key in keep}
    corrections = [value for value in json.loads((ROOT / "literature/corrections.json").read_text())
                   if value["ref"]["citation_key"] != "NeweyMcFadden1994"]
    corrections.append(json.loads((ROOT / "literature/bootstrap_reference.json").read_text()))
    corrections.append(json.loads((ROOT / "literature/asymptotic_reference.json").read_text()))
    corrections.extend(json.loads((ROOT / "literature/interval_references.json").read_text()))
    for value in corrections:
        key = value["ref"]["citation_key"]
        refs[key] = value["ref"]
        entries[key] = value["bib"]
    for key, identifier in [("Angelopoulos2023PPIpp", "2311.01453"), ("MaurerPontil2009", "0907.3740")]:
        page = (ROOT / "literature" / (key + ".html")).read_text()
        def metadata(name):
            return [html.unescape(value) for value in re.findall(r'<meta name="' + name + r'" content="([^"]+)"', page)]
        title = metadata("citation_title")[0]
        authors = metadata("citation_author")
        year = metadata("citation_date")[0][:4]
        author_field = " and ".join(authors)
        entries[key] = f"@misc{{{key},\n  title = {{{{{title}}}}},\n  author = {{{author_field}}},\n  year = {{{year}}},\n  eprint = {{{identifier}}},\n  archivePrefix = {{arXiv}},\n  url = {{https://arxiv.org/abs/{identifier}}}\n}}\n"
        refs[key] = {"id": "ref.arxiv." + identifier, "paper_id": identifier, "citation_key": key,
                     "title": title, "year": int(year), "venue": "arXiv", "query": "Exact permitted arXiv identifier " + identifier,
                     "source_url": "https://arxiv.org/abs/" + identifier,
                     "consulted_text_path": "literature/" + key + "_consulted.txt"}
    consultation_paths = {
        "Angelopoulos2023PPI": ("Angelopoulos2023PPI_consulted.txt", "Selected primary PDF pages"),
        "Angelopoulos2023PPIpp": ("Angelopoulos2023PPIpp_consulted.txt", "Selected primary PDF pages"),
        "MaurerPontil2009": ("MaurerPontil2009_consulted.txt", "Primary PDF pages including empirical-Bernstein theorem"),
        "Audibert2009": ("Audibert2009_consulted.json", "HAL abstract for the exact historical work"),
        "Glasserman2004": ("Glasserman2004_consulted.json", "Publisher synopsis"),
        "Hastie2009": ("Hastie2009_consulted.json", "Publisher synopsis; full text unavailable"),
        "Sarndal1992": ("Sarndal1992_consulted_excerpt.json", "Book synopsis"),
        "EfronTibshirani1993": ("EfronTibshirani1993_consulted_excerpt.json", "Publisher synopsis"),
    }
    notes = ["# Citation consultation scope", "", "Abstract and synopsis consultation is distinguished from primary-text reading. No full-book reading is claimed.", "", "| Key | Consultation | Local excerpt |", "|---|---|---|"]
    for key, ref in sorted(refs.items()):
        filename, scope = consultation_paths.get(key, (key + ".json", "Abstract, not full paper"))
        assert (ROOT / "literature" / filename).is_file()
        ref["consulted_text_path"] = "literature/" + filename
        ref["consultation_scope"] = scope
        notes.append(f"| `{key}` | {scope} | `{filename}` |")
    notes.extend(["", "Original Wilson and Clopper--Pearson records and the Newey--McFadden chapter were not retained as citations because substantive access was not established. The final interval-context citations are consulted comparison works, not fabricated primary-text reading.", "", "Wrong DOI/title matches from exploratory lookup were rejected; their titles and measurements do not enter the paper. No citation-network traversal or prohibited-work search was performed."])
    (ROOT / "literature/CONSULTATION.md").write_text("\n".join(notes) + "\n")
    assert len(entries) == 25, len(entries)
    (ROOT / "references.bib").write_text("\n\n".join(entries[key] for key in sorted(entries)) + "\n")
    (ROOT / "references_provenance.json").write_text(json.dumps({
        "generated_at": datetime.datetime.now(datetime.timezone.utc).isoformat(), "count": len(refs),
        "queries": ["Exact permitted starter identifiers and pre-screened historical DOI lookups; no citation network traversal"],
        "references": [refs[key] for key in sorted(refs)]}, indent=2) + "\n")
    print("Wrote", len(entries), "verified-identity references; consult literature excerpts for reading scope.")


if __name__ == "__main__":
    main()
