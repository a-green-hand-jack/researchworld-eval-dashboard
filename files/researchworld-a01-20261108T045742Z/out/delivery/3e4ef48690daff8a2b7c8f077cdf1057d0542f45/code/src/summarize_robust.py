"""Summaries of the robustness CSVs.
  tasksub : median L1/K per (rule, target_rank, n) with percentile-bootstrap 95% CI over task-subset draws, and the log-log slopes of
            the median and of the mean of L1 and K against n (investment ~ n^slope); the mean-based interval is the informative one.
  noise / taskboot : per (rule, target) quantiles over draws, and the share of draws in which the draw-wise cost is within a factor 2
            of the cost on the observed data; spread of the relative cost across rules.
Usage: python3 src/summarize_robust.py MODE IN_CSV OUT_PREFIX [BASE_CSV helm_main.csv CAP]
"""
import sys, numpy as np, pandas as pd
mode, inp, outp = sys.argv[1:4]
rng = np.random.default_rng(0); d = pd.read_csv(inp)
def bmed(v, B=1000):
    v = np.asarray(v, float)
    if (~np.isfinite(v)).mean() > 0.5: return np.inf, np.nan, np.nan
    m = np.median(v); bs = np.median(rng.choice(v, (B, len(v))), axis=1)
    return m, *np.percentile(bs, [2.5, 97.5])
if mode == "tasksub":
    rows = []
    for (r, k, n), s in d.groupby(["rule", "target_rank", "n"]):
        row = dict(rule=r, target_rank=k, n=n, n_draws=len(s), frac_infeasible=float((~np.isfinite(s.L1)).mean()))
        for q in ("L1", "K", "gap_own"):
            row[q + "_med"], row[q + "_lo"], row[q + "_hi"] = bmed(s[q].values)
        rows.append(row)
    S = pd.DataFrame(rows); S.to_csv(outp + "_by_n.csv", index=False)
    # log-log slope of the per-n median cost against n; CI by resampling the task-subset draws within each (rule, rank, n) cell
    sl = []
    for (r, k), g in d.groupby(["rule", "target_rank"]):
        ns = np.array(sorted(g.n.unique())); cells = {n: g[g.n == n] for n in ns}
        def slope(q, idx=None, stat=np.median):
            m = []
            for n in ns:
                v = cells[n][q].values; v = v if idx is None else v[idx[n]]
                # the median keeps infeasible (inf) draws; the mean is over feasible draws only (feasible share reported in _by_n)
                if stat is np.median: m.append(np.median(v))
                else: m.append(stat(v[np.isfinite(v)]) if np.isfinite(v).any() else np.nan)
            m = np.array(m); ok = np.isfinite(m) & (m > 0)
            return np.polyfit(np.log(ns[ok]), np.log(m[ok]), 1)[0] if ok.sum() >= 3 else np.nan
        row = dict(rule=r, target_rank=k)
        boots = {(q, st): [] for q in ("L1", "K") for st in ("med", "mean")}
        for b in range(500):
            idx = {n: np.random.default_rng(1000 * b + int(n)).integers(0, len(cells[n]), len(cells[n])) for n in ns}
            for q, st in boots: boots[(q, st)].append(slope(q, idx, np.median if st == "med" else np.mean))
        for q in ("L1", "K"):
            # median-based slope (integer medians: the bootstrap interval is discrete and can touch the estimate) and mean-based slope
            # (the mean of the draws varies smoothly with n; its bootstrap interval is the one that conveys uncertainty)
            for st, f in (("med", np.median), ("mean", np.mean)):
                tag = "" if st == "med" else "_mean"
                row[f"slope_{q}{tag}_vs_n"] = slope(q, None, f); lo, hi = np.nanpercentile(boots[(q, st)], [2.5, 97.5])
                row[f"slope_{q}{tag}_lo"], row[f"slope_{q}{tag}_hi"] = lo, hi
        sl.append(row)
    pd.DataFrame(sl).to_csv(outp + "_slopes.csv", index=False); print(pd.DataFrame(sl).round(2).to_string())
else:
    base_csv, cap = sys.argv[4], sys.argv[5]
    b = pd.read_csv(base_csv); b = b[b.cap == cap].set_index(["rule", "target"])
    rows = []
    for (r, t), s in d.groupby(["rule", "target"]):
        L = s.L1.values; fin = np.isfinite(L)
        obs = b.L1.get((r, t), np.nan) if (r, t) in b.index else np.nan
        rows.append(dict(rule=r, target=t, n_draws=len(s), L1_obs=obs, L1_q05=np.nanpercentile(L[fin], 5) if fin.any() else np.nan,
                         L1_med=np.median(L[fin]) if fin.any() else np.nan, L1_q95=np.nanpercentile(L[fin], 95) if fin.any() else np.nan,
                         frac_infeasible=float((~fin).mean()), K_med=np.median(s.K.values[fin]) if fin.any() else np.nan,
                         abs_spread_q05_q95=(np.nanpercentile(L[fin], 95) - np.nanpercentile(L[fin], 5)) if fin.any() else np.nan,
                         rel_cv=np.std(L[fin]) / max(np.mean(L[fin]), 1e-9) if fin.any() else np.nan))
    S = pd.DataFrame(rows); S.to_csv(outp + "_per_target.csv", index=False)
    R = S.groupby("rule").agg(L1_med_over_targets=("L1_med", "median"), rel_cv_med=("rel_cv", "median"), abs_spread_q05_q95_med=("abs_spread_q05_q95", "median"),
                              frac_infeasible=("frac_infeasible", "mean"), obs_med=("L1_obs", "median"))
    R.to_csv(outp + "_by_rule.csv"); print(R.round(3).to_string())
