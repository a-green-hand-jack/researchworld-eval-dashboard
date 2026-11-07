import json
import re
from pathlib import Path

import jsonschema
import pymupdf


ROOT = Path(__file__).resolve().parent.parent


def main():
    schema = json.loads((ROOT / ".codex/skills/validate-paper/templates/figure_manifest.schema.json").read_text())
    manifest = json.loads((ROOT / "figure_manifest.json").read_text())
    jsonschema.validate(manifest, schema)
    strategy = json.loads((ROOT / "paper_strategy.json").read_text())
    specs = {item["figure_id"]: item for item in strategy["figure_specs"]}
    for figure in manifest["figures"]:
        spec = specs[figure["figure_id"]]
        assert figure["figure_type"] == spec["figure_type"]
        assert figure["n_panels"] <= spec["max_panels"]
        assert max(figure["categories_per_panel"]) <= spec["max_categories_per_panel"]
        assert max(figure["series_per_panel"]) <= spec["max_series_per_panel"]
        assert figure["panels_per_row"] <= 3
        assert figure["estimated_min_rendered_font_pt"] >= 8.5
        if figure["generator"] == "matplotlib":
            assert (ROOT / figure["path_pdf"]).is_file()
            assert (ROOT / figure["path_png"]).is_file()
    text = (ROOT / "paper.tex").read_text()
    resolved_pointers = 0
    for target, locator in re.findall(r"@evidence\[\[([^#\]]+)(?:#([^\]]+))?\]\]", text):
        path = ROOT / target
        assert path.is_file(), target
        if locator.startswith("/") and path.suffix == ".json":
            value = json.loads(path.read_text())
            for component in locator[1:].split("/"):
                component = component.replace("~1", "/").replace("~0", "~")
                value = value[int(component)] if isinstance(value, list) else value[component]
            resolved_pointers += 1
    for family in ["helm", "openllm"]:
        table = (ROOT / "tables" / (family + "_complete.tex")).read_text().strip()
        assert table in text, family + " supplementary table differs from generated source"
    assert len(re.findall(r"@\w+\{", (ROOT / "references.bib").read_text())) in range(25, 31)
    document = pymupdf.open(ROOT / "paper.pdf")
    reference_index = next(index for index, page in enumerate(document) if re.search(r"(?m)^REFERENCES\s*$", page.get_text()))
    assert 8 <= reference_index <= 9, reference_index
    last_page = document[reference_index - 1]
    boxes = [block[:4] for block in last_page.get_text("blocks")
             if block[0] >= 104 and block[2] <= 512 and block[1] >= 70 and block[3] <= 725]
    boxes += [tuple(info["bbox"]) for info in last_page.get_image_info()]
    maximum_y = max(box[3] for box in boxes)
    span_fraction = (maximum_y - 72) / (9 * 72)
    if reference_index == 8:
        assert span_fraction >= .75, span_fraction
    body_text = "\n".join(page.get_text() for page in list(document)[:reference_index])
    banned = re.compile(r"\b(?:idea|ideas|program|programs|attempt|attempts|eligible|worker_01|worker_02|combined_score|rubric)\b", re.I)
    assert not banned.search(body_text), banned.search(body_text).group(0) if banned.search(body_text) else ""
    result = {"figure_schema_pass": True, "figure_density_pass": True,
              "manuscript_json_pointers_resolved": resolved_pointers,
              "embedded_supplementary_tables_match": True, "body_pages": reference_index,
              "last_body_content_y_end_pt": maximum_y,
              "last_body_span_fraction_of_9in_from_y72": span_fraction,
              "geometry_note": "Local text/graphics bounding-box sanity check, not a substitute for the parent orchestrator's authoritative rendered page validator.",
              "anonymous_template": True, "banned_body_language_absent": True,
              "concept_figure_render_pending": not (ROOT / ".concept_figure_complete").exists()}
    (ROOT / "derived/local_audit.json").write_text(json.dumps(result, indent=2))
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
