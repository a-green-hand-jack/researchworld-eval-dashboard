import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
import re
import urllib.request


REVISION = "9c09a7cae43334062a82cb164f2ef255013dafa2"
SOURCE_URL = f"https://huggingface.co/datasets/open-llm-leaderboard/contents/raw/{REVISION}/README.md"
KEY = "OpenLLMContents"
FIELDS = ["IFEval Raw", "BBH Raw", "MATH Lvl 5 Raw", "GPQA Raw", "MUSR Raw", "MMLU-PRO Raw"]


def main():
    source_path = Path("literature/OpenLLMContents.README.md")
    if not source_path.exists():
        request = urllib.request.Request(SOURCE_URL, headers={"User-Agent": "reproducible-paper-source-check/1.0"})
        with urllib.request.urlopen(request, timeout=60) as response:
            source_path.write_bytes(response.read())
    text = source_path.read_text()
    names = re.findall(r"^  - name: (.+)$", text, re.MULTILINE)
    assert [name for name in names if name.endswith(" Raw")] == FIELDS
    assert all(name.removesuffix(" Raw") in names for name in FIELDS)
    title = "Open LLM Leaderboard contents: dataset card and raw-score schema"
    bibtex = (
        "@misc{" + KEY + ",\n"
        " title={{" + title + "}},\n"
        " author={{Open LLM Leaderboard maintainers}},\n"
        " year={2025},\n"
        " howpublished={Hugging Face dataset},\n"
        " url={" + SOURCE_URL + "},\n"
        " note={Revision " + REVISION + "; accessed 2026-11-17}\n}"
    )
    scope = "Entire pinned official dataset-card YAML schema only; no links, citation graphs, or other pages followed."
    record = {
        "id": KEY, "title": title, "authors": ["Open LLM Leaderboard maintainers"],
        "year": 2025, "url": SOURCE_URL, "revision": REVISION,
        "retrieved_utc": "2026-11-17", "access_scope": scope,
        "source_path": str(source_path), "source_sha256": hashlib.sha256(source_path.read_bytes()).hexdigest(),
        "inspected_fields": FIELDS, "bibtex": bibtex,
    }
    record_path = Path("literature/OpenLLMContents.json")
    record_path.write_text(json.dumps(record, indent=2) + "\n")
    bib_path = Path("references.bib")
    bibliography = bib_path.read_text()
    if not re.search(r"@\w+\{\s*" + KEY + r"\s*,", bibliography):
        bib_path.write_text(bibliography.rstrip() + "\n\n" + bibtex + "\n")
    provenance_path = Path("references_provenance.json")
    provenance = json.loads(provenance_path.read_text())
    query = "Exact pinned official Open LLM contents dataset card: six Raw fields and their parallel score fields"
    entry = {
        "id": KEY, "citation_key": KEY, "title": title, "year": 2025,
        "paper_id": SOURCE_URL, "query": query, "source_url": SOURCE_URL,
        "retrieved_at": "2026-11-17", "url": SOURCE_URL, "source": "official_dataset_card",
        "evidence_path": str(record_path), "sha256": hashlib.sha256(record_path.read_bytes()).hexdigest(),
        "reading_scope": scope,
    }
    provenance["references"] = [item for item in provenance["references"] if item["id"] != KEY] + [entry]
    provenance["count"] = len(provenance["references"])
    provenance["generated_at"] = datetime.now(timezone.utc).isoformat()
    if query not in provenance["queries"]:
        provenance["queries"].append(query)
    provenance_path.write_text(json.dumps(provenance, indent=2) + "\n")
    sidecar = {
        "schema_name": "scientific-evidence.artifact-manifest",
        "artifact": {"path": str(record_path), "kind": "derived", "sha256": hashlib.sha256(record_path.read_bytes()).hexdigest()},
        "derived_from": ["@evidence" + "[[" + str(source_path) + "]]"],
        "generated_by": {"script_path": "scripts/enrich_panel_reference.py"},
    }
    Path(str(record_path) + ".prov.json").write_text(json.dumps(sidecar, indent=2) + "\n")
    print(f"Verified {KEY}: {len(FIELDS)} raw fields; {provenance['count']} references total.")


if __name__ == "__main__":
    main()
