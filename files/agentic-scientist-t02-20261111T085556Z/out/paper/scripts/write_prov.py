"""Write .prov.json sidecars for generated figures and derived data (scientific-evidence contract)."""
import json, hashlib
from pathlib import Path
root = Path(__file__).resolve().parent.parent
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def sidecar(artifact, kind, derived, script):
    a = root / artifact
    meta = {"schema_name": "scientific-evidence.artifact-manifest",
            "artifact": {"path": artifact, "kind": kind, "sha256": sha(a)},
            "derived_from": derived,
            "generated_by": {"script_path": script, "script_sha256": sha(root / script)}}
    (root / (artifact + ".prov.json")).write_text(json.dumps(meta, indent=1))
sidecar("derived/resolution.json", "derived",
        ["@evidence[[paper_data.json#final_evaluation.metrics]]",
         "@evidence[[paper_data.json#final_evaluation.evaluation_evidence.episodes]]",
         "@evidence[[source_evidence/workload/final_manifest.json]]",
         "@evidence[[source_evidence/final/final_manifest.json]]",
         "@evidence[[source_evidence/search_variants/variant1_metrics.json]]"],
        "scripts/derive_resolution.py")
for fig in ("slope_interval_vs_decision_rule", "search_variants_descriptive"):
    for ext in ("pdf", "png"):
        sidecar(f"figures/{fig}.{ext}", "figure", ["@evidence[[derived/resolution.json]]", "@evidence[[scripts/build_figures.py]]"],
                "scripts/build_figures.py")
