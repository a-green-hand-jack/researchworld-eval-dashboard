import hashlib
import json
from pathlib import Path


def main():
    contracts = [
        ("paper.tex", "manuscript", "scripts/build_paper_artifacts.py", ["paper_data.json", "derived/summary.json", "source_evidence/downstream/program/src/program.py", "source_evidence/evaluation/evaluate_final.py", "references_provenance.json"]),
        ("paper.pdf", "manuscript", "scripts/compile_paper.sh", ["paper.tex", "references.bib", "iclr2026_conference.sty", "iclr2026_conference.bst", "figures/investment_overview.png", "figures/exact_rule_contrast.pdf", "figures/attainability_and_support_scope.pdf"]),
        ("claims_grounding.json", "derived", "scripts/map_claims.py", ["paper_data.json", "derived/summary.json", "references_provenance.json"]),
        ("figure_manifest.json", "derived", "scripts/build_paper_artifacts.py", ["paper_strategy.json", "derived/summary.json"]),
        ("references.bib", "derived", "scripts/enrich_panel_reference.py", [str(path) for path in sorted(Path("literature").glob("*.json"))]),
        ("references_provenance.json", "derived", "scripts/enrich_panel_reference.py", [str(path) for path in sorted(Path("literature").glob("*.json"))]),
        ("derived/writer_validation.json", "derived", "scripts/audit_manuscript.py", ["paper.tex", "paper.pdf", "claims_grounding.json", "figure_manifest.json", "scientific-evidence/verification-report.json"]),
    ]
    for filename, kind, script, inputs in contracts:
        sidecar = {"schema_name": "scientific-evidence.artifact-manifest",
                   "artifact": {"path": filename, "kind": kind,
                                "sha256": hashlib.sha256(Path(filename).read_bytes()).hexdigest()},
                   "derived_from": ["@evidence"+"[["+item+"]]" for item in inputs],
                   "generated_by": {"script_path": script}}
        Path(filename+".prov.json").write_text(json.dumps(sidecar, indent=2)+"\n")


if __name__ == "__main__":
    main()
