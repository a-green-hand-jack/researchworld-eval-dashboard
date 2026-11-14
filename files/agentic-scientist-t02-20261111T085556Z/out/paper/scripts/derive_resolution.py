"""Derive resolution / interpretation quantities for the width-slope test from existing artifacts.

Inputs are read, never typed in:
  paper_data.json (final_evaluation.metrics, final_evaluation.evaluation_evidence.episodes)
  source_evidence/workload/final_manifest.json   (widths, step limit, probe interval, modulus, ...)
  source_evidence/final/final_manifest.json      (compute usage)
  source_evidence/search_variants/variant{1,2,3}_{metrics,evidence}.json
Output: derived/resolution.json
"""
import json, math, statistics
from math import comb
from pathlib import Path

root = Path(__file__).resolve().parent.parent
pd = json.loads((root / "paper_data.json").read_text())
wl = json.loads((root / "source_evidence/workload/final_manifest.json").read_text())
fm = json.loads((root / "source_evidence/final/final_manifest.json").read_text())

fe = pd["final_evaluation"]
m = fe["metrics"]  # @evidence[[paper_data.json#final_evaluation.metrics]]
eps = fe["evaluation_evidence"]["episodes"]  # @evidence[[paper_data.json#final_evaluation.evaluation_evidence.episodes]]
full = wl["full"]  # @evidence[[source_evidence/workload/final_manifest.json#full]]
widths, T, probe, p = full["widths"], full["max_steps"], full["probe_every"], full["modulus"]
n_seeds = len(wl["seeds"])
n_primary = len(widths) * n_seeds
doublings = math.log2(widths[-1] / widths[0])
slope, lo, hi, ref = (m["grok_delay_log_slope"], m["grok_delay_slope_ci_low"],
                      m["grok_delay_slope_ci_high"], m["reference_delay_log_slope"])

xs = [math.log2(w) for w in widths]
xbar = sum(xs) / len(xs)
sxx = sum((x - xbar) ** 2 for x in xs)
ols_w = [(x - xbar) / sxx for x in xs]  # slope = sum_d ols_w[d] * (mean over seeds of ln delay at width d)
# exact maximum |slope| over all delay profiles confined to [probe, T]: step profile, cap where weight<0, floor where >0
bound = math.log(T / probe) * sum(w for w in ols_w if w > 0)
loglinear = math.log(T / probe) / doublings  # slope of a profile falling log-linearly from the cap at 16 to the floor at 256
scores = [e["score"] for e in eps]
n_train = int(wl["train_fraction"] * p * p)
d = lambda w: 12 * w * w + (2 * p + 9) * w  # parameter count of the one-layer transformer (see program.py)

if slope < 0 and hi < 0:
    verdict = "supported"
elif lo >= 0:
    verdict = "refuted"
else:
    verdict = "inconclusive"

out = {
    "verdict_from_interval_rule": verdict,
    "widths": widths, "n_seeds": n_seeds, "n_primary_runs": n_primary,
    "n_censored_runs": round(m["censored_fraction"] * n_primary),
    "width_doublings": doublings,
    "n_train_pairs": n_train, "n_heldout_pairs": p * p - n_train,
    "n_checkpoints": T // probe,
    "delay_floor_steps": probe, "delay_cap_steps": T, "max_delay_ratio": T / probe,
    "max_abs_slope_attainable": bound, "loglinear_full_range_slope": loglinear, "ols_weights": ols_w,
    "slope": slope, "ci_low": lo, "ci_high": hi,
    "ci_width": hi - lo, "ci_lower_arm": slope - lo, "ci_upper_arm": hi - slope,
    "ci_fraction_of_attainable_range": (hi - lo) / (2 * bound),
    "per_doubling_factor": {"point": math.exp(slope), "low": math.exp(lo), "high": math.exp(hi)},
    "range_factor_256_vs_16": {"point": math.exp(slope * doublings), "low": math.exp(lo * doublings),
                               "high": math.exp(hi * doublings), "reference": math.exp(ref * doublings)},
    "reference_slope": ref, "reference_minus_point": ref - slope,
    "reference_inside_ci": lo <= ref <= hi,
    "reference_position_in_ci_fraction_from_low": (ref - lo) / (hi - lo),
    "point_slope_needed_for_supported_if_same_upper_arm": -(hi - slope),
    "reference_plus_upper_arm_illustration": ref + (hi - slope),
    "hidden_and_output_multipliers": {str(w): (128 / w) ** 0.5 for w in widths},  # REF_WIDTH=128, exponents 0.5 (frozen_model/program.py)
    "distinct_bootstrap_seed_multisets": comb(2 * n_seeds - 1, n_seeds),
    "bootstrap_draws_with_all_seeds_identical_prob": n_seeds / n_seeds ** n_seeds,
    "seed_scores": scores,
    "seed_score_mean": statistics.mean(scores),
    "seed_score_sd": statistics.stdev(scores),
    "seed_score_min": min(scores), "seed_score_max": max(scores),
    "seed_score_mean_matches_summary": math.isclose(statistics.mean(scores), m["combined_score"], abs_tol=1e-9),
    "params_by_width": {str(w): d(w) for w in widths},
    "compute": {k: fm["compute_usage"][k] for k in ("elapsed_seconds", "rpc_calls", "max_rpc_calls")},
    "episode_total_duration_seconds": sum(e["duration_seconds"] for e in eps),
}

# search-plane summary (separate data plane; reported for context only)
sw = json.loads((root / "source_evidence/workload/search_manifest.json").read_text())["full"]
search = []
for i in (1, 2, 3):
    mm = json.loads((root / f"source_evidence/search_variants/variant{i}_metrics.json").read_text())
    ee = json.loads((root / f"source_evidence/search_variants/variant{i}_evidence.json").read_text())["episodes"]
    n_ep = len(sw["widths"]) * len(ee)
    search.append({"variant": i, "score": mm["combined_score"], "final_val_acc_mean": mm["final_val_acc_mean"],
                   "censored_fraction": mm["censored_fraction"],
                   "n_censored_runs": round(mm["censored_fraction"] * n_ep), "n_runs": n_ep,
                   "seed_scores": {str(e["seed"]): e["score"] for e in ee},
                   "control_max_val_acc": mm["control_max_val_acc"]})
out["search"] = {"modulus": sw["modulus"], "train_fraction": json.loads(
    (root / "source_evidence/workload/search_manifest.json").read_text())["train_fraction"],
    "widths": sw["widths"], "max_steps": sw["max_steps"], "probe_every": sw["probe_every"],
    "seeds": json.loads((root / "source_evidence/workload/search_manifest.json").read_text())["seeds"],
    "variants": search}

(root / "derived").mkdir(exist_ok=True)
(root / "derived/resolution.json").write_text(json.dumps(out, indent=1))
print(json.dumps(out, indent=1))
