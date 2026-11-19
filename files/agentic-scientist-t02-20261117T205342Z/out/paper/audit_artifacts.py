import hashlib
import json
import re
from pathlib import Path

import jsonschema
import pymupdf
from PIL import Image

INPUT_EVIDENCE = "@evidence[[paper_data.json#/final_evaluation]]"


def digest(path):
    return "sha256:" + hashlib.sha256(Path(path).read_bytes()).hexdigest()


def provenance(path, kind, inputs):
    payload = {"schema_name": "scientific-evidence.artifact-manifest",
               "artifact": {"path": str(path), "kind": kind},
               "derived_from": [chr(64) + "evidence[[" + item + "]]" for item in inputs],
               "generated_by": {"script_path": "audit_artifacts.py", "command": ["python", "audit_artifacts.py"], "cwd": "."}}
    Path(str(path) + ".prov.json").write_text(json.dumps(payload, indent=2) + "\n")


def main():
    data = json.loads(Path("paper_data.json").read_text())
    final = data["final_evaluation"]
    assert digest("source_evidence/evaluate_final.py") == final["evaluator_sha256"]
    assert digest("source_evidence/evaluation_evidence.json") == final["evaluation_evidence"]["sha256"]
    evidence = json.loads(Path("source_evidence/evaluation_evidence.json").read_text())
    assert evidence["episodes"] == final["evaluation_evidence"]["episodes"]
    source_ids = set(data["grounding_sources"])
    references = json.loads(Path("references_provenance.json").read_text())["references"]
    source_ids.update(reference["id"] for reference in references)
    claims = json.loads(Path("claims_grounding.json").read_text())["claims"]
    assert all(set(claim["source_ids"]) <= source_ids for claim in claims)

    manuscript = Path("paper.tex").read_text()
    for table in ("full_observations", "diagnostics"):
        assert Path(f"tables/{table}.tex").read_text().strip() in manuscript
    checked_pointers = set()
    for path in [Path("paper.tex"), Path("build_artifacts.py"), *Path("tables").glob("*.tex")]:
        for target, pointer in re.findall(r"@evidence\[\[([^#\]]+)#(/[^\]]*)\]\]", path.read_text()):
            if not target.endswith(".json"):
                continue
            payload = json.loads(Path(target).read_text())
            for component in pointer.split("/")[1:]:
                component = component.replace("~1", "/").replace("~0", "~")
                payload = payload[int(component)] if isinstance(payload, list) else payload[component]
            checked_pointers.add((target, pointer))

    schema = json.loads(Path(".codex/skills/validate-paper/templates/figure_manifest.schema.json").read_text())
    manifest = json.loads(Path("figure_manifest.json").read_text())
    jsonschema.validate(manifest, schema)
    specs = {entry["figure_id"]: entry for entry in json.loads(Path("paper_strategy.json").read_text())["figure_specs"]}
    checks = []
    for entry in manifest["figures"]:
        spec = specs[entry["figure_id"]]
        assert entry["n_panels"] <= spec["max_panels"]
        assert entry["panels_per_row"] <= spec["max_panels_per_row"]
        assert max(entry["categories_per_panel"]) <= spec["max_categories_per_panel"]
        assert max(entry["series_per_panel"]) <= spec["max_series_per_panel"]
        assert entry["estimated_min_rendered_font_pt"] >= spec["minimum_rendered_font_pt"]
        image = Image.open(entry["path_png"])
        assert image.width >= 2400
        if entry["generator"] == "matplotlib":
            assert Path(entry["path_pdf"]).is_file()
            assert f"{{{entry['path_pdf']}}}" in manuscript
        checks.append({"figure_id": entry["figure_id"], "pixels": [image.width, image.height],
                       "panel_count": entry["n_panels"], "local_schema_and_density_checks": "passed"})
    assert set(specs) <= {entry["figure_id"] for entry in manifest["figures"]}

    text = re.sub(r"(?<!\\)%[^\n]*", "", manuscript)
    text = re.sub(r"\\texttt\{[^}]*\}", "", text)
    forbidden = ["idea", "ideas", "program", "programs", "attempt", "attempts", "eligible", "worker_01", "worker_02", "combined_score", "rubric"]
    violations = [word for word in forbidden if re.search(r"\b" + re.escape(word) + r"\b", text, re.I)]
    assert not violations, violations

    document = pymupdf.open("paper.pdf")
    reference_page = next(index for index, page in enumerate(document) if re.search(r"\bREFERENCES\b", page.get_text()))
    supplement_page = next(index for index, page in enumerate(document) if "SUPPLEMENTARY INFORMATION" in page.get_text())
    assert supplement_page > reference_page
    last_body = document[reference_page - 1]
    lines = [line for block in last_body.get_text("dict")["blocks"] if block["type"] == 0 for line in block["lines"]
             if line["dir"] == (1., 0.) and line["bbox"][0] >= 107 and line["bbox"][2] <= 505
             and line["bbox"][1] > 80 and line["bbox"][3] < 720]
    last_bottom = max(line["bbox"][3] for line in lines)
    overview_pending = not bool(json.loads(Path("figures/study_overview.prompts.json").read_text()))
    readiness = {
        "status": "not_submission_ready",
        "scientific_draft_and_claim_map": "written_and_locally_checked",
        "qualification": {name: data["grounding_sources"]["final.qualification." + name]["value"] for name in ("status", "outcome", "correct")},
        "qualification_interpretation": "Recorded acceptance does not establish generalization, a mechanism, or comprehensive integrity certification",
        "consulted_reference_count": len(references), "required_minimum_references": 25, "maximum_references": 30,
        "unresolved_requirements": [
            "The strategy permits only eight exact approved literature identities; the requested minimum is 25. No unrelated or unconsulted citations were added.",
            "The canonical compile wrapper requires unavailable pdftotext and its recorder check rejects a system texmf.cnf symlink; sanitized LaTeX/BibTeX compilation passes. Rendered Supplementary Information is checked separately using PyMuPDF extraction and the canonical validation function.",
            "The bundled canonical figure validator imports unavailable parent orchestration code; local schema and density checks pass, but authoritative parent figure/page validation is pending."
        ] + (["The concept overview is an orchestrator placeholder; final rendering is pending."] if overview_pending else []),
        "reproduction_limitation": "The original external RPC broker launcher is not supplied; readable neural training code and data are included, but no unsupported standalone launcher command is claimed.",
        "overview_render_pending": overview_pending,
        "training_or_evaluation_rerun": False,
        "local_validation": {"claim_count": len(claims), "source_and_observation_hashes": "matched",
            "json_pointer_locations_checked": len(checked_pointers), "figures": checks,
            "forbidden_visible_terms_outside_literal_paths": violations,
            "pdf_pages": len(document), "main_body_pages": reference_page,
            "references_start_page": reference_page + 1, "supplement_start_page": supplement_page + 1,
            "last_body_text_bottom_pt": last_bottom,
            "page_occupancy_note": "Geometric text bound, not a character-count proxy and not the authoritative parent occupancy validator"}}
    Path("submission_readiness.json").write_text(json.dumps(readiness, indent=2) + "\n")
    for path, kind, inputs in [
        ("paper.tex", "manuscript", ["paper_data.json#/final_evaluation", "claims_grounding.json", "references.bib", "source_evidence/evaluate_final.py"]),
        ("paper.pdf", "manuscript", ["paper.tex", "references.bib", "figure_manifest.json"]),
        ("claims_grounding.json", "derived", ["paper_data.json#/grounding_sources", "references_provenance.json"]),
        ("references.bib", "derived", ["references_provenance.json", *[reference["local_path"] for reference in references]]),
        ("references_provenance.json", "derived", ["literature/retrieve_approved.py", *[reference["local_path"] for reference in references]]),
        ("analysis/plotting_requirements.txt", "other", ["build_artifacts.py"]),
        ("submission_readiness.json", "derived", ["paper.tex", "paper.pdf", "claims_grounding.json", "figure_manifest.json", "references_provenance.json"]),
    ]:
        provenance(path, kind, inputs)
    print(f"Local grounding checks passed for {len(claims)} claims and {len(checked_pointers)} JSON pointers.")
    print(f"PDF: {reference_page} main-body pages, {len(document)} total; reference quota NOT met ({len(references)}/25).")


if __name__ == "__main__":
    main()
