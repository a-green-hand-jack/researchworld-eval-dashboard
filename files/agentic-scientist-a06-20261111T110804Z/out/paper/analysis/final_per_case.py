"""Per-case summaries of the sealed final evaluation, derived from the recorded per-seed episodes.
Input:  paper_data.json -> final_evaluation.evaluation_evidence.episodes  (8 seeds x 9 cases)
Output: analysis/final_per_case.json
# @evidence[[paper_data.json#final.evidence.episodes]]
"""
import json, numpy as np
d = json.load(open('paper_data.json'))
eps = d['final_evaluation']['evaluation_evidence']['episodes']
CASES = ["P1","P2","P3","P4","P5","P6","N1","N2","Z1"]
KEYS = {"cand_IS":"proposed_IS","naive_IS":"naive_IS","bonferroni_IS":"bonferroni_IS","resample_IS":"resample_IS",
        "bias":"proposed_bias","naive_bias":"naive_bias","coverage":"coverage","width":"width"}
out = {"seeds":[e['seed'] for e in eps], "cases":{}}
for c in CASES:
    row = {}
    for k, name in KEYS.items():
        v = np.array([e['solution'][c][k] for e in eps])
        row[name] = {"mean": float(v.mean()), "sd": float(v.std(ddof=1)), "per_seed": v.tolist()}
    out["cases"][c] = row
# aggregate (primary cases P1-P6; 0.4 synthetic / 0.6 real), per seed
def plane(vals):  # vals: dict case -> array(8)
    syn = np.mean([vals[c] for c in ("P1","P2")], axis=0)
    real = np.mean([vals[c] for c in ("P3","P4","P5","P6")], axis=0)
    return 0.4*syn + 0.6*real
agg = {}
for name in ["proposed_IS","naive_IS","bonferroni_IS","resample_IS","proposed_bias","naive_bias","coverage","width"]:
    per_seed = plane({c: np.array(out["cases"][c][name]["per_seed"]) for c in CASES})
    agg[name] = {"mean": float(per_seed.mean()), "sd": float(per_seed.std(ddof=1)), "per_seed": per_seed.tolist()}
out["aggregate_primary"] = agg
# paired per-seed differences of proposed vs each baseline in aggregate IS
for b in ("naive_IS","bonferroni_IS","resample_IS"):
    diff = np.array(agg[b]["per_seed"]) - np.array(agg["proposed_IS"]["per_seed"])
    out.setdefault("paired_diff_aggregate", {})[b] = {"mean": float(diff.mean()), "sd": float(diff.std(ddof=1)),
        "min": float(diff.min()), "n_seeds_proposed_better": int((diff>0).sum())}
# per-case paired differences
for c in CASES:
    for b in ("naive_IS","bonferroni_IS","resample_IS"):
        diff = np.array(out["cases"][c][b]["per_seed"]) - np.array(out["cases"][c]["proposed_IS"]["per_seed"])
        out["cases"][c][b+"_minus_proposed"] = {"mean": float(diff.mean()), "sd": float(diff.std(ddof=1)),
            "n_seeds_proposed_better": int((diff>0).sum())}
out["episode_duration_seconds"] = {"mean": float(np.mean([e['duration_seconds'] for e in eps])),
    "total": float(np.sum([e['duration_seconds'] for e in eps])), "min": float(min(e['duration_seconds'] for e in eps)), "max": float(max(e['duration_seconds'] for e in eps))}
out["seed_scores"] = [e['score'] for e in eps]
json.dump(out, open('analysis/final_per_case.json','w'), indent=1)

# Searcher-restricted aggregates with the evaluator's family weights (0.4 synthetic / 0.6 real)
def sub_plane(name, syn, real):
    s = np.mean([out["cases"][c][name]["per_seed"] for c in syn], axis=0)
    r = np.mean([out["cases"][c][name]["per_seed"] for c in real], axis=0)
    v = 0.4*s + 0.6*r
    return {"mean": float(v.mean()), "sd": float(v.std(ddof=1)), "per_seed": v.tolist()}
out["by_searcher"] = {}
for label, syn, real in (("exhaustive", ("P1",), ("P3","P5","P6")), ("halving", ("P2",), ("P4",))):
    out["by_searcher"][label] = {n: sub_plane(n, syn, real) for n in ("proposed_IS","naive_IS","bonferroni_IS","resample_IS","coverage","width","proposed_bias","naive_bias")}
# paired seed differences in naive bias between searchers (matched world / K / N)
for label, a, b in (("syn_halving_minus_exhaustive","P2","P1"), ("real_halving_minus_exhaustive","P4","P3")):
    diff = np.array(out["cases"][a]["naive_bias"]["per_seed"]) - np.array(out["cases"][b]["naive_bias"]["per_seed"])
    out.setdefault("naive_bias_searcher_diff", {})[label] = {"mean": float(diff.mean()), "sd": float(diff.std(ddof=1)), "n_positive": int((diff>0).sum())}
json.dump(out, open('analysis/final_per_case.json','w'), indent=1)
