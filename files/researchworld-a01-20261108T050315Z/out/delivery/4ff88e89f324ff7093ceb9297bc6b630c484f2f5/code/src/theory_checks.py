"""Numerical check of the closed-form propositions (claim C7) against the exact solvers.
  P1 mean   : need = n (tau+eps) - sum(x); L1* = need (0 if <= 0); K* = fewest tasks whose headrooms sum to >= need; Linf* = water-filling level;
              feasible iff total headroom >= need.
  P2 median (odd n): b = tau+eps; m = (n+1)/2; K* = max(0, m - #{x_t >= b}); L1* = sum of the K* smallest (b - x_t) over tasks below b with cap_t >= b;
              Linf* = the largest of those; infeasible iff fewer than K* such tasks.
  P3 min    : b = tau+eps; K* = #{x_t < b}; L1* = sum (b-x_t)^+; Linf* = max (b-x_t)^+; feasible iff cap_t >= b on every task below b.
  P4 Linf* = uniform lift d* (smallest d with y = min(x+d, cap) first), all rules (monotone in own scores).
tau = best rival's rule value (rivals fixed). Usage: python3 src/theory_checks.py OUT.csv [--seed 0]
"""
import sys, json, pathlib, argparse, itertools
import numpy as np, pandas as pd
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from mti import data as dt, scorerules as sr, feas

ap = argparse.ArgumentParser(); ap.add_argument("out"); ap.add_argument("--seed", type=int, default=0); a = ap.parse_args()
rng = np.random.default_rng(a.seed); EPS = 1e-3
INF = np.inf

def predict(rule, x, c, tau):
    n = len(x); b = tau + EPS; h = np.maximum(c - x, 0)
    if rule == "mean":
        need = n * b - x.sum()
        if need <= 0: return 0.0, 0, 0.0
        if h.sum() < need - 1e-12: return INF, INF, INF
        K = int(np.searchsorted(np.cumsum(np.sort(h)[::-1]), need - 1e-12) + 1)
        hs = np.sort(h); cs = np.concatenate([[0], np.cumsum(hs)]); k = 0           # water level d: sum_t min(d, h_t) = need
        for k in range(n):
            d = (need - cs[k]) / (n - k)
            if d <= hs[k] + 1e-15: break
        return need, K, d
    if rule == "min":
        g = np.maximum(b - x, 0); low = g > 0
        if (c[low] < b - 1e-12).any(): return INF, INF, INF
        return float(g.sum()), int(low.sum()), float(g.max())
    if rule == "median":
        m = (n + 1) // 2; have = int((x >= b).sum())
        if have >= m: return 0.0, 0, 0.0
        K = m - have; elig = np.sort((b - x)[(x < b) & (c >= b - 1e-12)])
        if len(elig) < K: return INF, INF, INF
        return float(elig[:K].sum()), K, float(elig[K - 1])

rows = []; iid = 0
def check(dsname, X, tasks_idx, i, cap_name, rule):
    global iid
    Xs = X[:, tasks_idx]; n = Xs.shape[1]; x = Xs[i]; M = len(Xs)
    cap = dt.make_cap(cap_name, Xs, i, "helm" if dsname == "helm" else "ollb") if not cap_name.startswith("emp") else None
    c = np.maximum(cap, x)
    fv = sr.RULES[rule][0]; v = fv(Xs); tau = float(np.delete(v, i).max())
    sol = sr.min_investment(rule, Xs, i, cap, EPS)
    pL1, pK, pLinf = predict(rule, x, c, tau)
    ok = lambda p, s: (np.isinf(p) and np.isinf(s)) or abs(p - s) <= 1e-6 * max(1, abs(p))
    fail = "none"
    if np.isinf(pL1): fail = "cap binds: infeasible"
    elif pL1 == 0: fail = "already first"
    rows.append(dict(proposition={"mean": "P1", "median": "P2", "min": "P3"}[rule], rule=rule, instance_id=iid,
                     params=json.dumps(dict(dataset=dsname, n=n, tasks=[int(t) for t in tasks_idx], target_idx=int(i), cap=cap_name, eps=EPS)),
                     pred_L1=pL1, pred_K=pK, pred_Linf=pLinf, solver_L1=sol["L1"], solver_K=sol["K"], solver_Linf=sol["Linf"],
                     agree=int(ok(pL1, sol["L1"]) and ok(pK, sol["K"]) and ok(pLinf, sol["Linf"])), failure_condition=fail))
    iid += 1
    # P4: Linf* equals the uniform lift (also for non-closed-form rules)
    for r4 in (rule, "geomean", "borda", "condorcet"):
        riv = feas.Rival(Xs, i, r4, EPS); d = feas.uniform_lift(riv, c)
        if r4 in sr.RULES: Ls = sr.min_investment(r4, Xs, i, cap, EPS, measures=("Linf",))["Linf"]
        else:
            from mti import ordinal as od; Ls = od.linf_ordinal(r4, Xs, i, cap, EPS)
        rows.append(dict(proposition="P4", rule=r4, instance_id=iid, params=json.dumps(dict(dataset=dsname, n=n, tasks=[int(t) for t in tasks_idx], target_idx=int(i), cap=cap_name, eps=EPS)),
                         pred_L1=np.nan, pred_K=np.nan, pred_Linf=d, solver_L1=np.nan, solver_K=np.nan, solver_Linf=Ls,
                         agree=int((np.isinf(d) and np.isinf(Ls)) or abs(d - Ls) < 1e-4),   # tol 1e-4: both sides are bisections (bracket ~1e-5 score points; observed max |diff| 5e-5)
                         failure_condition="cap binds: infeasible" if np.isinf(d) else "none"))
        iid += 1

Xh = dt.load("helm")[0]; Xo = dt.load("ollb")[0]
for dsname, X, sizes, nsub, ntg in (("helm", Xh, [3, 5, 9, 15, 25, 57], 12, 6), ("ollb", Xo, [3, 5, 6], 6, 12)):
    M, nt = X.shape
    for n in sizes:
        subs = [np.arange(nt)] if n == nt else [np.sort(rng.choice(nt, n, replace=False)) for _ in range(nsub)]
        for ti in subs:
            for i in rng.choice(np.arange(1, M), ntg, replace=False):
                for cap_name in ("ceil", "gain10", "gain5", "front0"):
                    for rule in ("mean", "min") + (("median",) if n % 2 == 1 else ()):
                        check(dsname, X, ti, int(i), cap_name, rule)
d = pd.DataFrame(rows); d.to_csv(a.out, index=False)
print(d.groupby(["proposition", "rule"]).agg(n=("agree", "size"), agree=("agree", "mean"),
      infeasible=("failure_condition", lambda s: (s == "cap binds: infeasible").mean())).round(4).to_string())
