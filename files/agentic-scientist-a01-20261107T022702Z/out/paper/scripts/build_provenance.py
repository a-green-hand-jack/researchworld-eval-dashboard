import hashlib
import importlib.metadata
import json
import platform
from pathlib import Path

from build_results import ROOT, sidecar


def main():
    paths = ["paper_data.json", "references.bib", "references_provenance.json",
             "data/helm.json", "data/openllm.json", "data/protocol.json",
             "iclr2026_conference.sty", "iclr2026_conference.bst", "official_template.tex"]
    paths += [str(path.relative_to(ROOT)) for path in sorted((ROOT / "source_evidence").rglob("*")) if path.is_file()]
    manifest = {path: hashlib.sha256((ROOT / path).read_bytes()).hexdigest() for path in paths}
    output = ROOT / "derived/checksums.json"
    output.write_text(json.dumps({"algorithm": "sha256", "files": manifest,
                                  "scope_note": "Local file bytes; not interchangeable with source upstream hashes or tree hashes."}, indent=2))
    sidecar(output, ["@evidence[[data/helm.json]]", "@evidence[[data/openllm.json]]",
                     "@evidence[[paper_data.json]]", "@evidence[[source_evidence/evaluation.py]]"], kind="derived")
    source = json.loads((ROOT / "paper_data.json").read_text())
    assert manifest["source_evidence/evaluation.py"] == source["final_evaluation"]["evaluator_sha256"].removeprefix("sha256:")
    environment = {"python": platform.python_version(), "platform": platform.platform(),
                   "paper_packages": {name: importlib.metadata.version(name) for name in
                                      ["numpy", "matplotlib", "requests", "jsonschema", "pyarrow", "pymupdf"]},
                   "evaluated_dependencies_file": "requirements-evaluated.txt",
                   "note": "Paper extraction/plotting environment is distinct from the recorded evaluation environment. No evaluation rerun."}
    (ROOT / "derived/environment.json").write_text(json.dumps(environment, indent=2))
    provenance = {
        "venue": "ICLR 2026 anonymous submission", "repository": "https://github.com/ICLR/Master-Template",
        "download_url": "https://github.com/ICLR/Master-Template/archive/refs/heads/master.zip",
        "retrieved_utc": "2026-11-07", "archive_subdirectory": "Master-Template-master/iclr2026",
        "files": {path: manifest[path] for path in ["iclr2026_conference.sty", "iclr2026_conference.bst", "official_template.tex"]},
        "modifications": "None to official style, bibliography style, or retained reference template. Manuscript omits identifying authors and does not enable final-copy mode.",
        "geometry": {"text_width_inches": 5.5, "text_height_inches": 9.0},
        "checklist": "No separate checklist is included in the official ICLR 2026 template. Supplement includes reproducibility, limitations and LLM usage disclosures; no checklist from another venue is substituted.",
    }
    (ROOT / "template_provenance.json").write_text(json.dumps(provenance, indent=2))
    upstream = {}
    for family in ["helm", "openllm"]:
        resource = json.loads((ROOT / "data" / (family + ".json")).read_text())
        upstream[family] = {"acquired_utc": resource["acquired_utc"], "scale": resource["scale"],
                            "tasks": resource["tasks"], "license_note": resource["license"],
                            "sources": sorted({(record["source_url"], record["source_sha256"]) for row in resource["rows"] for record in row["provenance"]})}
    path = ROOT / "derived/upstream_provenance.json"
    path.write_text(json.dumps(upstream, indent=2))
    sidecar(path, ["@evidence[[data/helm.json]]", "@evidence[[data/openllm.json]]"], kind="derived")
    for name, kind, inputs in [
        ("paper.tex", "manuscript", ["paper_data.json", "references_provenance.json", "source_evidence/downstream/program/src/program.py"]),
        ("claims_grounding.json", "derived", ["paper_data.json", "references_provenance.json", "derived/original_records.json"]),
        ("figure_manifest.json", "derived", ["paper_strategy.json", "derived/original_records.json"]),
        ("paper.pdf", "manuscript", ["paper.tex", "references.bib", "figures/score_space_overview.png", "figures/paired_mean_median_budgets.pdf", "figures/cap_conditioned_reachability.pdf"]),
    ]:
        path = ROOT / name
        if not path.exists():
            continue
        token = "@" + "evidence[["
        payload = {"schema_name": "scientific-evidence.artifact-manifest",
                   "artifact": {"path": name, "kind": kind, "sha256": hashlib.sha256(path.read_bytes()).hexdigest()},
                   "derived_from": [token + item + "]]" for item in inputs]}
        if name in ["paper.pdf", "figure_manifest.json"]:
            payload["artifact"].pop("sha256")
            payload["notes"] = ["Parent orchestration renders the overview and recompiles the PDF after this stage. Mutable output has an input trail but no pre-render content digest."]
        Path(str(path) + ".prov.json").write_text(json.dumps(payload, indent=2))
    print("Wrote file-scope checksums, upstream provenance, template provenance, environment and artifact sidecars.")


if __name__ == "__main__":
    main()
