import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent


def main():
    output = ROOT / "data"
    output.mkdir(exist_ok=True)
    for name in ["helm", "openllm", "protocol"]:
        origin = ROOT / "task/resources/final" / (name + ".json")
        target = output / (name + ".json")
        target.write_bytes(origin.read_bytes())
        payload = json.loads(target.read_text())
        upstream = sorted({record["source_url"] for row in payload.get("rows", []) for record in row["provenance"]})
        token = "@" + "evidence[["
        sources = [token + url + "]]" for url in upstream] + ["@evidence[[scripts/acquire_scores.py]]", "@evidence[[paper_data.json#/final_evaluation/evaluation_evidence/episodes]]"]
        sidecar = {"schema_name": "scientific-evidence.artifact-manifest",
                   "artifact": {"path": str(target.relative_to(ROOT)), "kind": "source",
                                "sha256": hashlib.sha256(target.read_bytes()).hexdigest()},
                   "derived_from": sources,
                   "generated_by": {"script_path": "scripts/stage_resources.py"},
                   "notes": ["Byte-identical local staging of supplied frozen final resource; original location: " + str(origin.relative_to(ROOT)),
                             "No score data were reacquired or changed. Redistribution rights remain uncertain."]}
        Path(str(target) + ".prov.json").write_text(json.dumps(sidecar, indent=2))
        print(target.relative_to(ROOT), sidecar["artifact"]["sha256"])


if __name__ == "__main__":
    main()
