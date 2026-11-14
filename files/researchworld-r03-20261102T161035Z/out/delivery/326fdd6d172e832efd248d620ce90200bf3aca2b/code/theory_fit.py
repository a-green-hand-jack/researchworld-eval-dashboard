"""Fit the theory's functional form MSE_z(k) = a (1 + r_eff / k) to the observed random-selection curves (ct_curves.csv) over k >= kmin,
compare with the fitted-FA prediction and the spectrum-based effective rank. usage: theory_fit.py OUT_DIR"""
import sys, os, numpy as np, pandas as pd
out = sys.argv[1]; c = pd.read_csv(os.path.join(out, "ct_curves.csv")); rows = []
for (data, inf, sel), g in c[(c.k != 9999) & c.inf.isin(["ridge", "fa", "knn"]) & c.sel.isin(["random", "greedy_ridge"])].groupby(["data", "inf", "sel"]):
    for kmin in (2, 4, 8):
        h = g[g.k >= kmin].sort_values("k")
        if len(h) < 3: continue
        x = 1 / h.k.values; y = h.zrmse.values ** 2
        A = np.stack([np.ones_like(x), x], 1); (a, b), res, *_ = np.linalg.lstsq(A, y, rcond=None)
        pred = A @ np.array([a, b]); r2 = 1 - ((y - pred) ** 2).sum() / ((y - y.mean()) ** 2).sum()
        rows.append((data, inf, sel, kmin, len(h), a, b, b / a if a > 0 else np.nan, r2, np.sqrt(np.abs(y - pred)).max() if False else float(np.abs(np.sqrt(np.maximum(pred, 0)) - h.zrmse.values).max())))
pd.DataFrame(rows, columns="data inf sel kmin n_points floor_a b r_eff_b_over_a r2 max_abs_err_zrmse".split()).to_csv(os.path.join(out, "theory_fit.csv"), index=False)
print(pd.DataFrame(rows, columns="data inf sel kmin n floor b r_eff r2 maxerr".split()).query("kmin==4 and sel=='random'").round(3).to_string())
