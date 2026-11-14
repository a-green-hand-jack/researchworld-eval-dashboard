"""Inspect rendered outputs and document checks unavailable in the local harness.

@evidence[[paper_data.json#/final_evaluation]]
@evidence[[paper.tex]]
@evidence[[figure_manifest.json]]
"""

import datetime
import hashlib
import json
import re
import subprocess
from pathlib import Path

import jsonschema
import pymupdf

from build_artifacts import provenance as artifact_provenance


ROOT = Path(__file__).resolve().parents[1]


def main():
    checks = []
    for name, command in [
        ("sections_and_citations", ["python", ".codex/skills/validate-paper/scripts/validate_tex_refs.py", "--tex", "paper.tex", "--bib", "references.bib"]),
        ("claim_mapping_and_evidence", ["python", ".codex/skills/write-paper-standalone/scripts/validate_claims.py", "--paper-data", "paper_data.json", "--references", "references_provenance.json", "--bib", "references.bib", "--claims", "claims_grounding.json", "--paper-dir", "."]),
        ("canonical_figures", ["python", ".codex/skills/validate-paper/scripts/validate_figures.py", "--paper-dir", "."]),
        ("rendered_supplement", ["python", ".codex/skills/validate-paper/scripts/validate_rendered_si.py", "--pdf", "paper.pdf"]),
        ("canonical_compile_inputs", ["python", ".codex/skills/validate-paper/scripts/validate_compile_inputs.py", "recorder", "--paper-dir", ".", "--fls", "paper.fls"]),
    ]:
        outcome = subprocess.run(command, cwd=ROOT, text=True, capture_output=True)
        checks.append({"name": name, "returncode": outcome.returncode, "output": outcome.stdout + outcome.stderr})
    manifest = json.loads((ROOT / "figure_manifest.json").read_text())
    schema = json.loads((ROOT / ".codex/skills/validate-paper/templates/figure_manifest.schema.json").read_text())
    jsonschema.validate(manifest, schema)
    strategy = json.loads((ROOT / "paper_strategy.json").read_text())
    specs = {item["figure_id"]: item for item in strategy["figure_specs"]}
    for figure in manifest["figures"]:
        spec = specs[figure["figure_id"]]
        assert figure["figure_type"] == spec["figure_type"]
        assert figure["panel_count"] <= spec["max_panels"]
        assert figure["panels_per_row"] <= spec["max_panels_per_row"]
        assert figure["estimated_min_rendered_font_pt"] >= spec["minimum_rendered_font_pt"]
        for panel in figure["panels"]:
            assert panel["category_count"] <= spec["max_categories_per_panel"]
            assert panel["series_count"] <= spec["max_series_per_panel"]
        for filename in figure["files"].values():
            assert (ROOT / filename).is_file()
    checks.append({"name": "local_figure_schema_density_and_files", "returncode": 0,
                   "output": "Canonical JSON schema and strategy budgets pass; this is not the unavailable host figure validator."})
    data = json.loads((ROOT / "paper_data.json").read_text())
    assert data["final_evaluation"]["status"] == "completed"
    assert data["final_evaluation"]["outcome"] == "not_qualified"
    assert data["grounding_sources"]["final.qualification.correct"]["value"] is False
    evaluator = ROOT / "source_evidence/task/evaluate_final.py"
    assert hashlib.sha256(evaluator.read_bytes()).hexdigest() == data["final_evaluation"]["evaluator_sha256"].removeprefix("sha256:")
    for evidence_root in [data["best_correct"], data["final_evaluation"]]:
        for episode in evidence_root["evaluation_evidence"]["episodes"]:
            for record in episode["solution"]["widths"]:
                if record is None:
                    continue
                assert all(value["updates"] == record["horizon"] for value in record["arms"].values())
                if record["width"] == 128:
                    studied = record["arms"]["candidate"]
                    matched = record["arms"]["initial_norm"]
                    for key in ["initial_state_sha256", "final_state_sha256"]:
                        assert studied[key] == matched[key]
                    for first, second in zip(studied["curves"], matched["curves"]):
                        assert {key: value for key, value in first.items() if key != "wall_seconds"} == {key: value for key, value in second.items() if key != "wall_seconds"}
    checks.append({"name": "source_identity_and_norm_duplicate", "returncode": 0,
                   "output": "Final evaluator source digest matches; all retained conditions reach recorded horizons; width128 scientific curves and hashes duplicate under norm matching."})
    manuscript = (ROOT / "paper.tex").read_text()
    for table_name in ["final_records.tex", "norm_loss_records.tex", "coverage_table.tex", "development_table.tex"]:
        assert (ROOT / "derived" / table_name).read_text().strip() in manuscript
    document = pymupdf.open(ROOT / "paper.pdf")
    reference_page = next(index for index, page in enumerate(document) if re.search(r"(?m)^REFERENCES\s*$", page.get_text()))
    supplement_page = next(index for index, page in enumerate(document) if "SUPPLEMENTARY INFORMATION" in page.get_text())
    assert supplement_page > reference_page
    assert 8 <= reference_page <= 9
    last_page = document[reference_page - 1]
    spans = [span for block in last_page.get_text("dict")["blocks"] if "lines" in block
             for line in block["lines"] for span in line["spans"]
             if span["bbox"][0] >= 100 and span["bbox"][1] < 720 and span["text"].strip()]
    content_bottom = max(span["bbox"][3] for span in spans)
    frame_top = 84.0
    frame_height = 648.0
    span_fraction = (content_bottom - frame_top) / frame_height
    if reference_page == 8:
        assert span_fraction >= .75
    body_text = "\n".join(page.get_text() for page in list(document)[:reference_page])
    for forbidden in ["idea", "ideas", "program", "programs", "attempt", "attempts", "eligible", "combined_score", "rubric", "worker_01", "worker_02"]:
        assert not re.search(r"\b" + re.escape(forbidden) + r"\b", body_text, re.IGNORECASE), forbidden
    assert "??" not in "\n".join(page.get_text() for page in document)
    checks.append({"name": "local_rendered_layout_and_visible_language", "returncode": 0,
                   "output": "Rendered body has8 pages and its last page exceeds75-percent vertical span; no banned body terms or unresolved cross-references. Parent geometry validation remains authoritative."})
    reference_count = len(json.loads((ROOT / "references_provenance.json").read_text())["references"])
    overview = next(item for item in manifest["figures"] if item["figure_id"] == "study_overview")
    concept_pending = overview.get("generator") not in {"generate-concept-figure", "matplotlib", "tikz", "native_latex", "manual"}
    report = {
        "generated_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "status": "incomplete_production_requirements",
        "scientific_qualification": {"status": "completed", "outcome": "not_qualified", "cause": "unknown"},
        "checks": checks,
        "pdf": {"pages": len(document), "body_pages": reference_page, "references_start_page": reference_page + 1,
                "supplement_start_page": supplement_page + 1,
                "local_last_body_page_vertical_span_fraction": span_fraction,
                "geometry_note": "Actual rendered text bounds in the supplied5.5-by9-inch text geometry; local span is not a substitute for parent geometric occupancy validation."},
        "reference_count": reference_count,
        "unresolved_requirements": [
            {"requirement": "25--30 consulted references", "observed": reference_count,
             "reason": "Framing contract restricts consultation to eight exact authorized originals. Off-scope retrieval contamination was excluded, not cited to fill a quota."},
            {"requirement": "canonical full figure and compile validation", "reason": "Host figure module unavailable; normal TeX config symlink rejected by dependency guard. No validators or system paths were modified."},
        ],
        "orchestrator_pending": ["study_overview rendering replaces guarded placeholder"] if concept_pending else [],
        "grounding_registry_sha256": hashlib.sha256((ROOT / "paper_data.json").read_bytes()).hexdigest(),
        "interpretation": "Compilation, claim mapping, and local readability checks do not upgrade failed scientific qualification. This is not a full validation pass.",
    }
    (ROOT / "repair_validation_report.json").write_text(json.dumps(report, indent=2) + "\n")
    artifact_provenance(ROOT / "repair_validation_report.json",
                        ["paper.pdf", "paper.tex", "claims_grounding.json", "figure_manifest.json", "paper_data.json"],
                        script_path="scripts/check_outputs.py")
    provenance = {"schema_name": "scientific-evidence.artifact-manifest",
                  "artifact": {"path": "paper.pdf", "kind": "manuscript"},
                  "derived_from": ["@evidence[[paper.tex]]", "@evidence[[references.bib]]", "@evidence[[paper.sty]]", "@evidence[[paper.bst]]",
                                   "@evidence[[figures/width_endpoint_comparison.pdf]]", "@evidence[[figures/fit_and_generalization_onsets.pdf]]", "@evidence[[figures/study_overview.pdf]]"],
                  "notes": "Sidecar records dependencies after direct sanitized LaTeX/BibTeX compilation; canonical recorder check remains blocked as documented."}
    (ROOT / "paper.pdf.prov.json").write_text(json.dumps(provenance, indent=2) + "\n")
    print(json.dumps({"body_pages": reference_page, "last_body_vertical_span_fraction": span_fraction,
                      "references": reference_count, "status": report["status"]}, indent=2))


if __name__ == "__main__":
    main()
