"""Reconstruct the evaluator-owned reporters' (naive Wilson / Bonferroni-Wilson / resampling) coverage and width
for the sealed final worlds by replaying the evaluator's own deterministic world builder, searchers and baseline
code (task/evaluate_final.py + task/resources/final). The candidate reporter is NOT run here.
Sanity check: the reconstructed per-case mean interval score and signed bias of each baseline must reproduce
the values recorded in the sealed final evidence.
# @evidence[[paper_data.json#final.evidence.episodes]]
# @evidence[[source_evidence/evaluator/evaluate_final.py]]
"""
import importlib.util, json, sys, os
import numpy as np
os.environ.pop("AGENTIC_TASK_DRAFT_SMOKE", None)
spec = importlib.util.spec_from_file_location("evalfinal", "task/evaluate_final.py")
ef = importlib.util.module_from_spec(spec); spec.loader.exec_module(ef)
os.environ["TASK_SOURCE_DIR"] = os.path.abspath("task")
pool = ef.load_real_pool(False)
rec = json.load(open("paper_data.json"))["final_evaluation"]["evaluation_evidence"]["episodes"]
out = {"cases": {}, "max_abs_diff_vs_recorded": {}}
per = {c: {k: [] for k in ("naive_cov","naive_width","bonf_cov","bonf_width","resample_cov","resample_width",
                            "naive_IS","bonf_IS","resample_IS","naive_bias","resample_bias")} for c in ef.CASE_ORDER}
index = 0
for seed in ef.SEEDS:
    for case in ef.CASE_ORDER:
        ep = ef.build_episode(index, seed, case, False, pool); index += 1
        rows = {n: [ef.score_reporter(r[n], r["truth"]) for r in ep["reps"]] for n in ("naive","bonf","resample")}
        for n in rows:
            per[case][n+"_cov"].append(float(np.mean([x["cov"] for x in rows[n]])))
            per[case][n+"_width"].append(float(np.mean([x["width"] for x in rows[n]])))
            per[case][n+"_IS"].append(float(np.mean([x["IS"] for x in rows[n]])))
        per[case]["naive_bias"].append(float(np.mean([x["bias"] for x in rows["naive"]])))
        per[case]["resample_bias"].append(float(np.mean([x["bias"] for x in rows["resample"]])))
        print(seed, case, flush=True, file=sys.stderr)
maxdiff = {"naive_IS":0,"bonf_IS":0,"resample_IS":0,"naive_bias":0}
names = {"naive_IS":"naive_IS","bonf_IS":"bonferroni_IS","resample_IS":"resample_IS","naive_bias":"naive_bias"}
for si, seed in enumerate(ef.SEEDS):
    for case in ef.CASE_ORDER:
        r = rec[si]["solution"][case]
        for k, rk in names.items():
            maxdiff[k] = max(maxdiff[k], abs(per[case][k][si] - r[rk]))
out["max_abs_diff_vs_recorded"] = maxdiff
for case in ef.CASE_ORDER:
    out["cases"][case] = {k: {"mean": float(np.mean(v)), "sd": float(np.std(v, ddof=1)), "per_seed": v} for k, v in per[case].items()}
def plane(key):
    vals = {c: np.array(per[c][key]) for c in ef.CASE_ORDER}
    return (0.4*np.mean([vals[c] for c in ef.SYN_PRIMARY], axis=0) + 0.6*np.mean([vals[c] for c in ef.REAL_PRIMARY], axis=0))
out["aggregate_primary"] = {k: {"mean": float(plane(k).mean()), "sd": float(plane(k).std(ddof=1))}
                            for k in ("naive_cov","naive_width","bonf_cov","bonf_width","resample_cov","resample_width","naive_bias","resample_bias")}
json.dump(out, open("analysis/reconstructed_baselines.json", "w"), indent=1)
print(json.dumps(out["max_abs_diff_vs_recorded"]))
