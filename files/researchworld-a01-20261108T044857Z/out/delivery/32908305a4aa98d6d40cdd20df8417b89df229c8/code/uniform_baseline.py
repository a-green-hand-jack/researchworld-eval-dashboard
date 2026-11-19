"""Capped uniform-raise baseline (request experiment-repo#10).
Usage: python3 code/uniform_baseline.py CORE_CSV DATASET OUT_TARGETS_CSV OUT_SUMMARY_CSV
For every row of a core table (dataset x cap x rule x target): the uniform strategy raises EVERY task by d, truncated at the cap,
y_t = min(x_t + d, c_t), and d is the smallest value that makes the target strictly first (margin 1e-3 for the score rules, strict
comparisons for the ordinal rules). That is exactly the `Linf` column of the core table (bisection, tolerance 1e-7 / 1e-6), so no rule
is re-solved here. The actual cost of the vector is L1_unif = sum_t min(d, h_t), h_t = c_t - x_t, and K_unif = #{t : min(d, h_t) > 0};
infeasible when no d works (same targets as the optimal solution: both are feasible iff the all-at-cap vector wins).
Targets file: dataset, cap, rule, target, target_idx, rank_mean, status, d, L1_unif, K_unif, L1_opt, K_opt, ratio_L1 (L1_unif / L1_opt),
ratio_K, on targets with L1_opt > 0. For the ordinal rules L1_opt is the cost of a witness at most eps above the infimum per raised task
while L1_unif is the infimum of the uniform strategy, so ratio_L1 can fall below 1 by up to n * 1e-3 / L1_opt (n = number of tasks); `n_below_one` counts it.
Summary: per cap x rule x rank stratum, targets feasible under both: n, median ratio_L1 with a 95% bootstrap CI over targets
(1000 draws, seed 0), share of targets with ratio_L1 > 1 + 1e-6, medians of L1_opt, L1_unif, K_opt, K_unif.
"""
import sys, pathlib
import numpy as np, pandas as pd
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from mti import data as dt

core, ds, out_t, out_s = sys.argv[1:5]
d = pd.read_csv(core); X, names, tasks, meta = dt.load(ds)
BINS = {"ollb": [(2, 5), (6, 10), (11, 30), (31, 100), (101, 300), (301, 10**6)], "helm": [(2, 3), (4, 5), (6, 10), (11, 20), (21, 40), (41, 10**6)]}
lab = lambda lo, hi: f"{lo}-{hi}" if hi < 10**6 else f">{lo-1}"
rng = np.random.default_rng(0)
capc = {}
rows = []
for r in d[d.rank_mean >= 2].itertuples():
    i = int(r.target_idx); key = (r.cap, i)
    if key not in capc: capc[key] = np.maximum(dt.make_cap(r.cap, X, i), X[i]) - X[i]
    h = capc[key]
    if np.isnan(r.L1) or np.isnan(r.Linf): dd = l1u = ku = np.nan
    elif np.isinf(r.Linf): dd = l1u = np.inf; ku = np.inf
    else: step = np.minimum(r.Linf, h); dd = r.Linf; l1u = float(step.sum()); ku = float((step > 0).sum())
    rows.append(dict(dataset=r.dataset, cap=r.cap, rule=r.rule, target=r.target, target_idx=i, rank_mean=r.rank_mean, status=r.status,
                     d=dd, L1_unif=l1u, K_unif=ku, L1_opt=r.L1, K_opt=r.K))
t = pd.DataFrame(rows)
pos = np.isfinite(t.L1_opt) & (t.L1_opt > 0) & np.isfinite(t.L1_unif)
t["ratio_L1"] = np.where(pos, t.L1_unif / t.L1_opt.where(t.L1_opt > 0), np.nan)
t["ratio_K"] = np.where(pos, t.K_unif / t.K_opt.where(t.K_opt > 0), np.nan)
t.to_csv(out_t, index=False)

def ci(v):
    return np.percentile(np.median(v[rng.integers(0, len(v), (1000, len(v)))], axis=1), [2.5, 97.5])
S = []
for (c, rule), s in t.groupby(["cap", "rule"]):
    for g, lo, hi in [("all", 2, 10**6)] + [(lab(a, b), a, b) for a, b in BINS[ds]]:
        m = s[(s.rank_mean >= lo) & (s.rank_mean <= hi)]
        n_feas_opt = int((np.isfinite(m.L1_opt)).sum()); n_feas_unif = int(np.isfinite(m.L1_unif).sum())
        b = m[np.isfinite(m.ratio_L1)]
        if not len(m): continue
        row = dict(dataset=ds, cap=c, rule=rule, group=g, n_targets=len(m), n_feasible_opt=n_feas_opt, n_feasible_unif=n_feas_unif, n_both=len(b))
        if len(b):
            v = b.ratio_L1.values; lo_, hi_ = ci(v)
            row.update(ratio_med=float(np.median(v)), ratio_lo=lo_, ratio_hi=hi_, share_gt1=float((v > 1 + 1e-6).mean()),
                       n_below_one=int((v < 1 - 1e-6).sum()), L1_opt_med=float(b.L1_opt.median()), L1_unif_med=float(b.L1_unif.median()),
                       K_opt_med=float(b.K_opt.median()), K_unif_med=float(b.K_unif.median()))
        S.append(row)
pd.DataFrame(S).to_csv(out_s, index=False)
