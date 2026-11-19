import hashlib
import importlib.util
import json
from pathlib import Path
import re
import subprocess
from datetime import datetime, timezone

from jsonschema import validate
from pypdf import PdfReader


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    source = Path("paper.tex").read_text()
    registry = json.loads(Path("paper_data.json").read_text())
    summary = json.loads(Path("derived/summary.json").read_text())
    report = {"checked_at": datetime.now(timezone.utc).isoformat(), "checks": {}, "pending": []}
    checks = report["checks"]
    claims = json.loads(Path("claims_grounding.json").read_text())["claims"]
    references = json.loads(Path("references_provenance.json").read_text())
    validate(references, json.loads(Path(".codex/skills/retrieve-references/templates/provenance.schema.json").read_text()))
    checks["reference_provenance_schema"] = True
    validate(json.loads(Path("figure_manifest.json").read_text()), json.loads(Path(".codex/skills/validate-paper/templates/figure_manifest.schema.json").read_text()))
    checks["figure_manifest_schema"] = True
    assert 25 <= references["count"] <= 30
    checks["reference_count"] = references["count"]
    identifiers = set(registry["grounding_sources"]) | {item["id"] for item in references["references"]}
    assert all(set(claim["source_ids"]) <= identifiers for claim in claims)
    checks["grounded_claims"] = len(claims)
    selected = "source_evidence/downstream/program/src/program.py"
    baseline = "source_evidence/downstream/baseline/src/program.py"
    assert digest(selected) == digest(baseline)
    checks["selected_source_identical_to_baseline"] = True
    for item in summary["central"]:
        assert item["contrasts"]["0.5"]["mean"] < 0 < item["contrasts"]["1.0"]["mean"]
        assert len(item["slots"]) == item["count"]
    checks["exact_fixed_cohort_signs"] = True
    final = registry["final_evaluation"]
    checks["independent_final_qualification"] = {key: registry["grounding_sources"]["final.qualification."+key]["value"]
                                                  for key in ["status", "outcome", "correct"]}
    assert checks["independent_final_qualification"]["outcome"] == final["outcome"]
    for filename in ["source_evidence/evaluation/evaluate_final.py", "scripts/build_paper_artifacts.py", "scripts/map_claims.py", "scripts/curate_references.py"]:
        compile(Path(filename).read_text(), filename, "exec")
    checks["python_syntax"] = True
    reader = PdfReader("paper.pdf")
    texts = [page.extract_text() or "" for page in reader.pages]
    visible = "\n".join(texts)
    visible_without_paths = re.sub(r"\S*(?:program\.py|program_spec\.toml|/program/|/program/src/)\S*", "", visible)
    forbidden = re.findall(r"\b(?:idea|ideas|program|programs|attempt|attempts|eligible|combined_score|rubric|worker_01|worker_02)\b", visible_without_paths, re.I)
    assert not forbidden, forbidden
    checks["visible_language"] = True
    assert not re.search(r"Citation.*undefined|Reference.*undefined|Overfull", Path("paper.log").read_text())
    checks["latex_unresolved_or_overfull"] = False
    checks["pdf_pages"] = len(reader.pages)
    checks["pdf_sha256"] = digest("paper.pdf")
    spec = importlib.util.spec_from_file_location("compile_inputs", ".codex/skills/validate-paper/scripts/validate_compile_inputs.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.validate_bibtex_aux_dependencies(Path.cwd(), "paper.aux")
    checks["canonical_bibliography_inputs"] = True
    original_recorder = Path("paper.fls").read_text()
    canonical_roots = [Path(path).resolve() for path in module.LATEX_SYSTEM_INPUT_ROOTS]
    normalized = []
    changed = 0
    for line in original_recorder.splitlines():
        if line.startswith("INPUT "):
            path = Path(line[6:])
            if path.is_absolute() and path.exists() and not path.is_relative_to(Path.cwd()):
                realpath = path.resolve()
                assert any(realpath.is_relative_to(root) for root in canonical_roots), str(path)
                changed += realpath != path
                line = "INPUT " + str(realpath)
        normalized.append(line)
    Path("derived/canonical_inputs.fls").write_text("\n".join(normalized)+"\n")
    module.validate_latex_recorder_inputs(Path.cwd(), "derived/canonical_inputs.fls")
    checks["resolved_recorder_inputs"] = True
    checks["approved_system_symlink_normalizations"] = changed
    try:
        from src.orchestrator.paper_step import measure_last_body_page_fill_ratio, find_reference_start_page, find_supplement_start_page
        reference = find_reference_start_page(texts)
        supplement = find_supplement_start_page(texts)
        body = reference-1
        fill = measure_last_body_page_fill_ratio(Path("paper.pdf"), last_body_page_number=body,
                                                reference_start_page=reference, body_columns=1)
        assert 8 <= body <= 9 and (body != 8 or fill >= .75)
        checks["body_budget"] = {"body_pages": body, "last_page_geometric_fill": fill,
                                 "reference_start_page": reference, "supplement_start_page": supplement,
                                 "method": "Canonical geometric occupancy; VENUE.md bounds applied explicitly."}
    except ImportError:
        report["pending"].append("Canonical page-geometry library unavailable; use the recorded derived/page_budget.json or parent validator.")
    if Path("figures/investment_overview.prompts.json").read_text().strip() == "{}":
        report["pending"].append("Orchestrator-owned concept rendering and subsequent full figure validation; placeholder is mandated by the writer-stage contract.")
    evidence_report = json.loads(Path("scientific-evidence/verification-report.json").read_text())
    assert evidence_report["summary"]["dangling_references"] == 0
    checks["dangling_evidence_links"] = 0
    Path("derived/writer_validation.json").write_text(json.dumps(report, indent=2)+"\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
