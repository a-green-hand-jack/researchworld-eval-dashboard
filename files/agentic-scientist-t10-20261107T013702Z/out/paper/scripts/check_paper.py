import importlib.util
import json
import re
from pathlib import Path

import jsonschema
import pymupdf

ROOT = Path(__file__).resolve().parent.parent


def main():
    data = json.loads((ROOT / "paper_data.json").read_text())
    strategy = json.loads((ROOT / "paper_strategy.json").read_text())
    manifest = json.loads((ROOT / "figure_manifest.json").read_text())
    schema = json.loads((ROOT / ".codex/skills/validate-paper/templates/figure_manifest.schema.json").read_text())
    jsonschema.validate(manifest, schema)
    specifications = {item["figure_id"]: item for item in strategy["figure_specs"]}
    manuscript = (ROOT / "paper.tex").read_text()
    declared_paths = set()
    for figure in manifest["figures"]:
        spec = specifications[figure["figure_id"]]
        assert figure["figure_type"] == spec["figure_type"], figure["figure_id"]
        assert figure["n_panels"] <= spec["max_panels"]
        assert max(figure["categories_per_panel"]) <= spec["max_categories_per_panel"]
        assert max(figure["series_per_panel"]) <= spec["max_series_per_panel"]
        assert figure["panels_per_row"] <= spec["max_panels_per_row"]
        assert figure["estimated_min_rendered_font_pt"] >= 8
        assert set(figure["source_ids"]) <= set(data["grounding_sources"])
        for field in ["path_png", "path_pdf", "prompt_log_path"]:
            if field in figure:
                assert (ROOT / figure[field]).is_file()
                declared_paths.add(figure[field])
    for included in re.findall(r"\\includegraphics(?:\[[^\]]*\])?\{([^}]+)\}", manuscript):
        assert included in declared_paths, included
    assert set(specifications) == {item["figure_id"] for item in manifest["figures"]}
    resolved_json = 0
    resolved_lines = 0
    for token in re.findall(r"@evidence\[\[([^\]]+)\]\]", manuscript):
        target, separator, locator = token.partition("#")
        path = ROOT / target
        assert path.is_file(), token
        if path.suffix == ".json" and locator.startswith("/"):
            value = json.loads(path.read_text())
            for part in locator[1:].split("/"):
                part = part.replace("~1", "/").replace("~0", "~")
                value = value[int(part)] if isinstance(value, list) else value[part]
            resolved_json += 1
        if re.fullmatch(r"L\d+(?:-L?\d+)?", locator):
            numbers = [int(value) for value in re.findall(r"\d+", locator)]
            assert max(numbers) <= len(path.read_text().splitlines()), token
            resolved_lines += 1
    pdf = pymupdf.open(ROOT / "paper.pdf")
    texts = [page.get_text() for page in pdf]
    reference_index = next(index for index, text in enumerate(texts) if re.search(r"\bREFERENCES\b", text))
    supplement_index = next(index for index, text in enumerate(texts) if "SUPPLEMENTARY INFORMATION" in text)
    assert reference_index in [8, 9], reference_index
    assert supplement_index > reference_index
    assert "LLM USAGE" in "\n".join(texts)
    forbidden = r"\b(?:ideas?|programs?|attempts?|eligible|worker_01|worker_02|combined_score|rubric)\b"
    for page_text in texts:
        scrubbed = re.sub(r"program\.py", "source-file", page_text)
        assert not re.search(forbidden, scrubbed, re.I), re.search(forbidden, scrubbed, re.I)
    body_last = pdf[reference_index - 1]
    rectangles = []
    for block in body_last.get_text("dict")["blocks"]:
        for line in block.get("lines", []):
            spans = [span for span in line["spans"] if span["bbox"][0] >= 106 and span["bbox"][2] <= 506
                     and 70 <= span["bbox"][1] < 730 and not span["text"].isdigit()]
            rectangles.extend(span["bbox"] for span in spans)
    extent = max(rectangle[3] for rectangle in rectangles) - min(rectangle[1] for rectangle in rectangles)
    fill = extent / 648
    assert fill >= .75 if reference_index == 8 else True
    specification = importlib.util.spec_from_file_location("rendered_si", ROOT / ".codex/skills/validate-paper/scripts/validate_rendered_si.py")
    validator = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(validator)
    body_texts = [page.get_text(clip=pymupdf.Rect(105, 65, 507, 750), sort=True) for page in pdf]
    errors = validator.validate_rendered_supplementary_information(body_texts)
    assert not errors, errors
    summary = json.loads((ROOT / "scientific-evidence/verification-report.json").read_text())["summary"]
    assert summary["dangling_references"] == 0
    report = {"status": "local_checks_passed", "body_pages": reference_index, "total_pages": len(pdf),
              "last_body_page_vertical_extent_fraction": fill,
              "geometry_note": "Local text-span extent, excluding margin counters; not the parent orchestrator's authoritative occupancy metric.",
              "figure_schema": "passed", "strategy_figure_budgets": "passed", "figures": len(manifest["figures"]),
              "resolved_manuscript_json_pointers": resolved_json, "resolved_source_line_locators": resolved_lines,
              "rendered_supplement": "passed canonical heading/content function on PyMuPDF text within the official text frame",
              "dangling_evidence_references": 0,
              "canonical_tooling_limits": [
                  "Standalone figure-validator entrypoint cannot import the absent parent src.orchestrator module; canonical JSON schema and strategy budgets checked locally.",
                  "compile_latex.sh recorder checker rejects a system texmf.cnf symlink crossing two approved TeX roots. Sanitized pdflatex/BibTeX commands compile successfully; parent revalidation remains authoritative.",
                  "System pdftotext is unavailable. Rendered SI checked from independent PyMuPDF extraction within the official text frame, excluding margin counters.",
                  "Concept image is an orchestrator-owned placeholder until synchronous post-draft rendering."
              ]}
    (ROOT / "local_validation_report.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
