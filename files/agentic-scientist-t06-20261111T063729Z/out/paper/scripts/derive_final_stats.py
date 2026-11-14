"""Derive per-case budget statistics for the sealed final evaluation from paper_data.json.

Reads the host-generated registry read-only; writes derived/final_stats.json.
@evidence[[paper_data.json#final_evaluation.evaluation_evidence.episodes]]
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
data = json.loads((ROOT / "paper_data.json").read_text(encoding="utf-8"))
episodes = data["final_evaluation"]["evaluation_evidence"]["episodes"]

cases0 = episodes[0]["solution"]["cases"]
identical = all(e["solution"]["cases"] == cases0 for e in episodes)
seeds = [e["seed"] for e in episodes]

out = {"episode_seeds": seeds, "episodes_identical": identical, "cases": {}}
for cid, c in cases0.items():
    n, cap = c["n_rows"], c["k_cap"]
    out["cases"][cid] = {
        "n_rows": n, "n_models": c["n_models"], "k_cap": cap,
        "cap_percent_of_rows": 100.0 * cap / n,
        "studied_k": c["k"], "studied_percent": 100.0 * c["k"] / n,
        "studied_score": c["score"],
        "b1_flips": c["B1_flips"], "b1_draws": c["B1_draws"], "b1_score": c["B1_score"],
        "b2_k": c["B2_k"], "b2_percent": 100.0 * c["B2_k"] / n, "b2_score": c["B2_score"],
        "b3_k": c["B3_k"], "b3_percent": 100.0 * c["B3_k"] / n, "b3_score": c["B3_score"],
        "k_over_cap": c["k"] / cap,
        "empty_flip": c["B0_empty_flip"],
        "mean_comparisons_per_participant": 2.0 * n / c["n_models"],
        "studied_percent_of_mean_participant_comparisons": 100.0 * c["k"] / (2.0 * n / c["n_models"]),
    }
cs = out["cases"]
out["ratios"] = {
    "top_sports_over_crowd_percent": cs["F3"]["studied_percent"] / cs["F1"]["studied_percent"],
    "mid_sports_over_crowd_percent": cs["F4"]["studied_percent"] / cs["F2"]["studied_percent"],
    "table_size_ratio_crowd_over_sports": cs["F1"]["n_rows"] / cs["F3"]["n_rows"],
    "b3_over_studied_k": {c: cs[c]["b3_k"] / cs[c]["studied_k"] for c in ("F1", "F2", "F3", "F4")},
}
out["studied_equals_b2_all_real_and_perm_cases"] = all(
    cs[c]["studied_k"] == cs[c]["b2_k"] for c in cs)
out["permutation_controls"] = episodes[0]["solution"]["permutation_controls"]
out["copy_control"] = episodes[0]["solution"]["copy_control"]
out["empty_set_control_ok"] = episodes[0]["solution"]["empty_set_control_ok"]
(ROOT / "derived").mkdir(exist_ok=True)
(ROOT / "derived" / "final_stats.json").write_text(json.dumps(out, indent=1), encoding="utf-8")
print(json.dumps(out, indent=1))
