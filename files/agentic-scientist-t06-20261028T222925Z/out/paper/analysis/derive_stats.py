"""Derive per-case statistics for the paper from the sealed final evaluation record.

Every number is read from paper_data.json (final_evaluation); nothing is hardcoded.
Outputs analysis/derived_stats.json (+ .prov.json sidecar).
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
# @evidence[[paper_data.json#final_evaluation.evaluation_evidence.episodes]]
# @evidence[[paper_data.json#final_evaluation.metrics]]
data = json.loads((ROOT / "paper_data.json").read_text(encoding="utf-8"))
final = data["final_evaluation"]
metrics = final["metrics"]
episodes = final["evaluation_evidence"]["episodes"]

# Verified sizes must be identical across seeds (determinism); keep seed-level record.
per_seed = {int(ep["seed"]): ep["solution"]["verified_k"] for ep in episodes}
seeds = sorted(per_seed)
case_ids = sorted(per_seed[seeds[0]])
identical = all(per_seed[s] == per_seed[seeds[0]] for s in seeds)
k = per_seed[seeds[0]]

# Row counts n per source, derived exactly from k and the evaluator-reported fraction k/n.
# Single-source families: n = k_drop_top1 / top1_drop_frac.
# @evidence[[paper_data.json#final_evaluation.metrics.arena140k_top1_drop_frac]]
# @evidence[[paper_data.json#final_evaluation.metrics.mtbench_human_top1_drop_frac]]
# @evidence[[paper_data.json#final_evaluation.metrics.mtbench_gpt4_top1_drop_frac]]
n = {}
for fam in ("arena140k", "mtbench_human", "mtbench_gpt4"):
    n[fam] = k[f"{fam}_drop_top1"] / metrics[f"{fam}_top1_drop_frac"]
# NBA family reports the mean fraction over two seasons for drop and for flip:
#   (kd14/n14 + kd15/n15)/2 = Fd,  (kf14/n14 + kf15/n15)/2 = Ff  -> solve 2x2 linear system in 1/n.
# @evidence[[paper_data.json#final_evaluation.metrics.nba_top1_drop_frac]]
# @evidence[[paper_data.json#final_evaluation.metrics.nba_top1_flip_frac]]
a11, a12, r1 = k["nba2014_drop_top1"], k["nba2015_drop_top1"], 2 * metrics["nba_top1_drop_frac"]
a21, a22, r2 = k["nba2014_flip_top1"], k["nba2015_flip_top1"], 2 * metrics["nba_top1_flip_frac"]
det = a11 * a22 - a12 * a21
inv14 = (r1 * a22 - a12 * r2) / det
inv15 = (a11 * r2 - r1 * a21) / det
n["nba2014"], n["nba2015"] = 1.0 / inv14, 1.0 / inv15
n_int = {s: int(round(v)) for s, v in n.items()}

SOURCES = ["arena140k", "mtbench_human", "mtbench_gpt4", "nba2014", "nba2015"]
TOPK = {"arena140k": 5, "mtbench_human": 3, "mtbench_gpt4": 3, "nba2014": 5, "nba2015": 5}
cases = []
for src in SOURCES:
    for pert, tgt in (("drop", "top1"), ("flip", "top1"), ("drop", f"top{TOPK[src]}")):
        cid = f"{src}_{pert}_{tgt}"
        kv = k[cid]
        cases.append({"case": cid, "source": src, "perturbation": pert, "target": tgt,
                      "k": kv, "n": n_int[src], "frac_pct": 100.0 * kv / n_int[src]})

ratios = {src: k[f"{src}_drop_top1"] / k[f"{src}_flip_top1"] for src in SOURCES}
topk_over_top1 = {src: k[f"{src}_drop_top{TOPK[src]}"] / k[f"{src}_drop_top1"] for src in SOURCES}

out = {
    "seeds": seeds,
    "verified_k_identical_across_seeds": identical,
    "episode_durations_seconds": {int(ep["seed"]): ep["duration_seconds"] for ep in episodes},
    "n_rows_derived": n_int,
    "n_rows_derived_unrounded": n,
    "cases": cases,
    "drop_over_flip_top1": ratios,
    "topk_over_top1_drop": topk_over_top1,
    "controls": {"synthetic_drop_top1_k": k["synthetic_drop_top1"],
                 "synthetic_control_score": metrics["synthetic_control_score"],
                 "perm_arena140k_drop_top1_k": k["perm_arena140k_drop_top1"],
                 "permutation_control_score": metrics["permutation_control_score"]},
    "comparators": {key: metrics[key] for key in metrics if key.startswith("mean_log2_ratio")},
    "random_ratio_x": 2.0 ** metrics["mean_log2_ratio_vs_random"],
    "random_ratio_ci_x": [2.0 ** metrics["mean_log2_ratio_vs_random_ci_low"],
                          2.0 ** metrics["mean_log2_ratio_vs_random_ci_high"]],
    "nba_mean_drop_frac_pct": 100 * metrics["nba_top1_drop_frac"],
    "nba_mean_flip_frac_pct": 100 * metrics["nba_top1_flip_frac"],
}
dst = ROOT / "analysis" / "derived_stats.json"
dst.write_text(json.dumps(out, indent=2), encoding="utf-8")
(ROOT / "analysis" / "derived_stats.json.prov.json").write_text(json.dumps({
    "schema_name": "scientific-evidence.artifact-manifest",
    "artifact": {"path": "analysis/derived_stats.json", "kind": "derived-data"},
    "derived_from": ["@evidence[[paper_data.json#final_evaluation]]",
                     "@evidence[[analysis/derive_stats.py]]"],
}, indent=2), encoding="utf-8")
print(json.dumps(out, indent=1))
