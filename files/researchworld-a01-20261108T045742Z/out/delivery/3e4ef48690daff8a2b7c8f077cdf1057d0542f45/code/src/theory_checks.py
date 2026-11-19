"""Numerical verification of the closed-form propositions against the exact solvers (all targets, HELM and OLLB).
  P1 mean:   L1 = n(tau+eps) - sum(x) when feasible (under any cap); Linf (uncapped) = tau + eps - mean(x);
             K >= ceil(need / max headroom).
  P2 min:    L1 = sum_t max(0, b - x_t), K = #{x_t < b}, Linf = b - min(x), b = tau + eps (all caps >= b, else infeasible).
  P3 median (n odd, ceil cap): K = max(0, (n+1)/2 - #{x_t >= b});  L1 = sum of the (n+1)/2 smallest gaps max(0, b - x_t).
  P4 monotonicity in headroom: ceil <= front2 <= front0 and gain20 <= gain10 <= gain5 (cost never decreases when the cap tightens).
Usage: python3 src/theory_checks.py OUT_CSV
"""
import sys, pathlib, numpy as np, pandas as pd
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from mti import scorerules as sr, data as dt

eps = 1e-3; rows = []
def rec(ds, prop, quantity, err, n_checked):
    rows.append(dict(dataset=ds, proposition=prop, quantity=quantity, max_abs_err=float(err), n_checked=int(n_checked)))

for ds in ("helm", "ollb"):
    X, names, tasks, meta = dt.load(ds); M, n = X.shape
    for rule in ("mean", "min", "median"):
        v = sr.RULES[rule][0](X)
        errs = {"L1": [], "K": [], "Linf": []}
        for i in range(M):
            tau = np.delete(v, i).max()
            if v[i] > tau: continue
            x = X[i]; b = tau + eps; cap = dt.make_cap("ceil", X, i)
            o = sr.min_investment(rule, X, i, cap, eps)
            if rule == "mean":
                need = n * b - x.sum()
                errs["L1"].append(abs(o["L1"] - need))
                errs["Linf"].append(abs(o["Linf"] - need / n) if need / n <= (cap - x).min() else np.nan)
                h = np.sort(cap - x)[::-1]; errs["K"].append(float(o["K"] < max(int(np.ceil(need / h[0] - 1e-9)), 1)))   # 1 = lower bound violated
            elif rule == "min":
                errs["L1"].append(abs(o["L1"] - np.maximum(0, b - x).sum()))
                errs["K"].append(abs(o["K"] - (x < b).sum()))
                errs["Linf"].append(abs(o["Linf"] - (b - x.min())))
            elif n % 2:
                m = (n + 1) // 2; gaps = np.maximum(0, b - x)
                errs["K"].append(abs(o["K"] - max(0, m - (x >= b).sum())))
                errs["L1"].append(abs(o["L1"] - np.sort(gaps)[:m].sum()))
        for q, e in errs.items():
            if e:
                e = np.array(e, float)
                note = {"mean": "P1", "min": "P2", "median": "P3"}[rule]
                if rule == "mean" and q == "K":      # K >= bound only (equality when one task absorbs everything)
                    rec(ds, "P1", "mean:K violations of K >= ceil(need/max headroom)", e.sum(), len(e)); continue
                rec(ds, note, f"{rule}:{q}", np.nanmax(e) if np.isfinite(e).any() else np.nan, np.isfinite(e).sum())
    # P4 monotone in headroom
    rng = np.random.default_rng(0); ids = rng.choice(M, min(M, 150), replace=False)
    for rule in ("mean", "geomean", "median", "min"):
        v = sr.RULES[rule][0](X); viol = 0; cnt = 0
        for chain in (["ceil", "front2", "front0"], ["gain20", "gain10", "gain5"]):
            for i in ids:
                prev = -np.inf
                for c in chain:
                    cap = dt.make_cap(c, X, i); o = sr.min_investment(rule, X, i, cap, eps, measures=("L1",))["L1"]
                    if o < prev - 1e-9: viol += 1
                    prev = max(prev, o) if np.isfinite(o) else np.inf; cnt += 1
        rec(ds, "P4", f"{rule}: violations of cost monotone in cap", viol, cnt)
pd.DataFrame(rows).to_csv(sys.argv[1], index=False); print(pd.DataFrame(rows).to_string())
