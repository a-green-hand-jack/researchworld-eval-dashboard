#!/usr/bin/env python3
"""Derive secondary quantities from the sealed final-evaluation metrics (read-only inputs).

Every input is read from paper_data.json; nothing is hardcoded.
Output: analysis/derived_metrics.json
"""
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
# @evidence[[paper_data.json#final_evaluation.metrics]]
data = json.loads((ROOT / "paper_data.json").read_text(encoding="utf-8"))
m = data["final_evaluation"]["metrics"]
eps = data["final_evaluation"]["evaluation_evidence"]["episodes"]

score = m["combined_score"]            # = 1 - MSE of the diagnostic
mse = {
    "diagnostic": 1.0 - score,
    "always_reliable": 1.0 - score + m["skill_vs_always_reliable"],
    "constant_half": 1.0 - score + m["skill_vs_constant_half"],
    "split_half_gap": 1.0 - score + m["skill_vs_gap_heuristic"],
    "permuted_control": 1.0 - m["control_permuted_score"],
}
rmse = {k: math.sqrt(v) for k, v in mse.items()}
skill_always = m["skill_vs_always_reliable"]
ctrl_gain = m["combined_score"] - m["control_permuted_score"]   # instance-specific gain
retained_under_permutation = mse["always_reliable"] - mse["permuted_control"]

low, high = m["mean_label_low_budget"], m["mean_label_high_budget"]
out = {
    "mse": mse,
    "rmse": rmse,
    "relative_mse_reduction": {
        "vs_always_reliable": 1 - mse["diagnostic"] / mse["always_reliable"],
        "vs_constant_half": 1 - mse["diagnostic"] / mse["constant_half"],
        "vs_split_half_gap": 1 - mse["diagnostic"] / mse["split_half_gap"],
        "vs_permuted_control": 1 - mse["diagnostic"] / mse["permuted_control"],
    },
    "diagnostic_minus_control": ctrl_gain,
    "decomposition_of_gain_over_always_reliable": {
        "total": skill_always,
        "retained_under_pairing_permutation": retained_under_permutation,
        "instance_specific": ctrl_gain,
        "share_retained_under_permutation": retained_under_permutation / skill_always,
        "share_instance_specific": ctrl_gain / skill_always,
    },
    # Jaccard of two 3-sets with overlap c is c/(6-c): 1, 1/2, 1/5, 0 -> loss 0, .5, .8, 1.
    # With deficiency D = 1 - mean label, the fraction q of non-identical rerun pairs satisfies D <= q <= 2D.
    "non_identical_top3_fraction_bounds": {
        "low_budget": {"lower": 1 - low, "upper": 2 * (1 - low)},
        "high_budget": {"lower": 1 - high, "upper": 2 * (1 - high)},
    },
    "label_budget_gap": high - low,
    "per_seed_scores": {str(e["seed"]): e["score"] for e in eps},
    "per_seed_score_difference": abs(eps[0]["score"] - eps[1]["score"]),
}
# Budget-prior constants of the selected configuration, parsed from its source file.
# @evidence[[source_evidence/selected_config_program.py#L43]]
import re
src = (ROOT / "source_evidence" / "selected_config_program.py").read_text(encoding="utf-8")
prior = {float(a): float(b) for a, b in re.findall(r"(\d\.\d+): (\d\.\d+)", re.search(r"_PRIOR_BY_RATIO = \{(.*?)\}", src).group(0))}
out["budget_prior_minus_final_label"] = {
    "low_budget": prior[2.0] - low,
    "high_budget": prior[4.0] - high,
}
(ROOT / "analysis" / "derived_metrics.json").write_text(json.dumps(out, indent=2), encoding="utf-8")
print(json.dumps(out, indent=2))
