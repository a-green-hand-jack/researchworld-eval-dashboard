"""TEST-ONLY synthetic tables with the schema of notes/result_schema_request.md, to smoke-test the plotting code.
Values are random and MEAN NOTHING. Never write outputs of this into a delivered path."""
import sys, numpy as np, pandas as pd, os
out = sys.argv[1]; os.makedirs(out, exist_ok=True)
rng = np.random.default_rng(1)
key = dict(gain_model="G2_0.5", cost="linear", field="all", tie_break="strict", spillover_rho=0, noise_margin=0)
rows = []
for lb, gr, n in [("openllm_v2", "headline", 6), ("openllm_v2", "subtask", 50)]:
    for rule, scale in [("mean", .3), ("median", .6), ("borda", .5), ("win_rate", .5), ("min", .9)]:
        for t in range(300):
            k = max(1, int(rng.exponential(scale * n * .4)) + 1)
            feas = k <= n and rng.random() > scale * .3
            rows.append(dict(leaderboard=lb, granularity=gr, rule=rule, rule_param="", target_id=t, init_rank=t + 1,
                             n_tasks=n, k_min=k if feas else np.nan, G_min=k * 5 if feas else np.nan, feasible=int(feas), exact=1, **key))
pd.DataFrame(rows).to_csv(f"{out}/per_target.csv", index=False)
rows = []
for lb, gr in [("openllm_v2", "headline"), ("openllm_v2", "subtask")]:
    for rule in ["mean", "median", "borda", "win_rate", "min"]:
        for b, nn in zip(["1-2", "3-10", "11-100", "rest"], [2, 8, 90, 4000]):
            f = rng.random(); rows.append(dict(leaderboard=lb, granularity=gr, rule=rule, rank_bin=b, n_targets=nn, frac_feasible=f,
                                                ci_lo=max(0, f - .05), ci_hi=min(1, f + .05), **key))
pd.DataFrame(rows).to_csv(f"{out}/feasibility.csv", index=False)
rows = []
for rule in ["mean", "median", "borda", "min"]:
    for n in [5, 10, 20, 40]:
        for rep in range(30):
            rows.append(dict(leaderboard="openllm_v2", granularity="subtask", rule=rule, n_tasks=n, rep=rep, seed=rep,
                             median_k_min=rng.random() * n, median_k_min_frac=rng.random() * .5, median_G_min=rng.random() * 100,
                             frac_feasible=rng.random(), **key))
pd.DataFrame(rows).to_csv(f"{out}/subsample_curves.csv", index=False)
rows = []
for p in [-np.inf, -4, -2, -1, 0, 1, 2, 4, 8]:
    m = rng.random() * 3 + 1; rows.append(dict(leaderboard="openllm_v2", granularity="headline", rule="power_mean", p=p, median_k_min=m,
                                              ci_lo=m - .5, ci_hi=m + .5, frac_feasible=rng.random(), **key))
for r in ["median", "borda", "win_rate"]:
    rows.append(dict(leaderboard="openllm_v2", granularity="headline", rule=r, p=np.nan, median_k_min=2.5, ci_lo=2, ci_hi=3, frac_feasible=.5, **key))
pd.DataFrame(rows).to_csv(f"{out}/power_mean_curve.csv", index=False)
rows = [dict(leaderboard="openllm_v2", granularity="headline", contrast="mean vs median", metric="k_min", n_pairs=500, estimate=-1.0,
             estimate_type="median paired diff", ci_lo=-1.5, ci_hi=-.5, n_counterexamples=37, **key)]
pd.DataFrame(rows).to_csv(f"{out}/paired_stats.csv", index=False)
pd.DataFrame([dict(instance_type=t, leaderboard="openllm_v2", granularity="headline", rule="mean", match=1, abs_diff=0.0) for t in ["real", "small_exhaustive"] * 3]).to_csv(f"{out}/verification.csv", index=False)
rows = []
for f, lv in [("gain_model", "G1"), ("gain_model", "G2_0.5"), ("noise", "sd=1")]:
    for r in ["mean", "median", "borda"]:
        rows.append(dict(leaderboard="openllm_v2", factor=f, level=lv, rule=r, metric="median_k_min", estimate=rng.random() * 5, ci_lo=0, ci_hi=6,
                         n_targets=100, claim_holds=int(rng.random() > .3)))
pd.DataFrame(rows).to_csv(f"{out}/ablation.csv", index=False)
os.makedirs(f"{out}/../data", exist_ok=True)
import json; json.dump({"sources": [dict(name="mock", snapshot="x", date="d", n_models_raw=1, n_models_used=1, n_tasks=6)]}, open(f"{out}/../data/manifest.json", "w"))
