"""Derived statistics for the paper (reads paper_data.json and per-variant metrics files).

Writes derived/derived_stats.json. Run: python scripts/derive_stats.py
"""
import json
import math
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
# @evidence[[paper_data.json#final_evaluation]]
D = json.loads((ROOT / "paper_data.json").read_text(encoding="utf-8"))
M = D["final_evaluation"]["metrics"]
EP = D["final_evaluation"]["evaluation_evidence"]["episodes"]

out = {}
sc = np.array([e["score"] for e in EP])
out["final_per_seed"] = {"seeds": [e["seed"] for e in EP], "scores": sc.tolist(),
                         "mean": float(sc.mean()), "sd_ddof1": float(sc.std(ddof=1)),
                         "min": float(sc.min()), "max": float(sc.max()),
                         "durations_s": [e["duration_seconds"] for e in EP]}
loss = 1.0 - M["final_score"]
base_loss = 1.0 - M["best_baseline_score"]
size_term = 0.25 * M["mean_set_size_ratio"]
slice_term = 0.25 * M["worst_slice_coverage_gap"]
marg_term = loss - size_term - slice_term
out["final_loss_decomposition"] = {
    "mean_loss": loss, "best_baseline_mean_loss": base_loss,
    "relative_loss_reduction_vs_best_baseline": (base_loss - loss) / base_loss,
    "size_term_0.25x": size_term, "slice_term_0.25x": slice_term,
    "implied_marginal_term_0.5x": marg_term,
    "implied_mean_clipped_marginal_gap_over_alpha": marg_term / 0.5,
    "note": "marginal term obtained by subtraction; assumes loss is the 0.5/0.25/0.25 combination "
            "averaged identically to the reported case-mean metrics",
    "full_set_score_analytic": 1.0 - 0.25,
}
# Search-stage variants (per-variant evaluator metric files and per-seed evidence)
progs = sorted(D["all_programs"], key=lambda p: p["eval_index"])
var = {}
for tag, p in zip(["V1", "V2", "V3"], progs):
    mp = ROOT / "source_evidence" / tag / "metrics.json"
    m = json.loads(mp.read_text(encoding="utf-8"))
    s = [e["score"] for e in p["evaluation_evidence"]["episodes"]]
    var[tag] = {"metrics": m, "per_seed": s, "seeds": [e["seed"] for e in p["evaluation_evidence"]["episodes"]],
                "mean": float(np.mean(s)), "sd_ddof1": float(np.std(s, ddof=1)), "metrics_file": str(mp.relative_to(ROOT))}
out["variants"] = var
d21 = np.array(var["V2"]["per_seed"]) - np.array(var["V1"]["per_seed"])
d32 = np.array(var["V3"]["per_seed"]) - np.array(var["V2"]["per_seed"])
out["paired_diffs"] = {"V2_minus_V1": d21.tolist(), "V2_minus_V1_mean": float(d21.mean()),
                       "V3_minus_V2": d32.tolist(),
                       "min_two_sided_exact_signflip_p_n3": 2.0 / 2 ** 3}
# Margin-theory constants: expected one-sided shortfall of a N(mu, sigma^2) coverage, in units of sigma
def phi(x): return math.exp(-x * x / 2) / math.sqrt(2 * math.pi)
def sf(x): return 0.5 * math.erfc(x / math.sqrt(2))
f = lambda z: phi(z) - z * sf(z)
out["margin_constants"] = {"f(0)": f(0.0), "f(0.6)": f(0.6), "f(0.7)": f(0.7), "ratio_f(0.7)/f(0)": f(0.7) / f(0.0)}
(ROOT / "derived").mkdir(exist_ok=True)
(ROOT / "derived" / "derived_stats.json").write_text(json.dumps(out, indent=1), encoding="utf-8")
print(json.dumps(out, indent=1))
