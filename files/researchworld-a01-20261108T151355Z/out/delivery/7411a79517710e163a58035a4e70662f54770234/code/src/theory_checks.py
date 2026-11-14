"""Numerical verification of closed-form propositions against the solver outputs (HELM, cap=ceil, eps=1e-3).
Independent re-derivation from the score matrix X (not calling the solvers):
  P1 mean   : L1* = n(tau+eps) - sum(x);  K* = fewest tasks whose headroom (100-x) sums to >= L1*;  Linf* = tau+eps - mean(x)  (uniform raise)
  P2 min    : L1* = sum (b-x)+, K* = #{x<b}, Linf* = max(b-x), b = tau+eps
  P3 median (n odd): K* = (n+1)/2 - #{x>=b};  L1* = sum of the (n+1)/2 smallest (b-x)+
Usage: python3 src/theory_checks.py results/helm_main.csv OUT.csv
"""
import sys, pathlib, numpy as np, pandas as pd
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from mti import data as dt
X, names, tasks, meta = dt.load("helm"); M, n = X.shape; eps = 1e-3
d = pd.read_csv(sys.argv[1]); d = d[(d.cap == "ceil")]
idx = {m: i for i, m in enumerate(names)}
fv = {"mean": X.mean(1), "min": X.min(1), "median": np.median(X, 1)}
rows = []
for rule in ("mean", "min", "median"):
    for _, r in d[d.rule == rule].iterrows():
        i = idx[r.target]; x = X[i]; tau = np.delete(fv[rule], i).max(); b = tau + eps
        if fv[rule][i] > tau: L1 = K = Linf = 0.0
        elif rule == "mean":
            L1 = n * b - x.sum(); h = np.sort(100 - x)[::-1]; K = float(np.searchsorted(np.cumsum(h), L1 - 1e-9) + 1); Linf = b - x.mean()
        elif rule == "min":
            g = np.maximum(0, b - x); L1, K, Linf = g.sum(), float((g > 0).sum()), g.max()
        else:
            g = np.maximum(0, b - x); m = (n + 1) // 2; L1 = np.sort(g)[:m].sum(); K = float(max(0, m - (x >= b).sum())); Linf = np.sort(g)[:m].max()
        # the uniform-raise closed form for mean-Linf is valid only while no task hits the cap (x + Linf <= 100)
        if rule == "mean" and L1 > 0 and (x + Linf > 100).any(): Linf = np.nan
        rows.append(dict(rule=rule, target=r.target, dL1=r.L1 - L1, dK=r.K - K, dLinf=r.Linf - Linf))
R = pd.DataFrame(rows); R.to_csv(sys.argv[2], index=False)
print(R.groupby("rule")[["dL1", "dK", "dLinf"]].agg(lambda s: np.nanmax(np.abs(s))).round(6))
