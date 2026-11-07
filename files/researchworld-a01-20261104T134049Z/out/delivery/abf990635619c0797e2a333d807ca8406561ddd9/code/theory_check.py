"""Numerical check of P1-P3 (THEORY.md): closed forms (mti.theory) vs the exact solvers (mti.scorerules) on all targets,
and, on a seeded sample of targets, vs a generic LP / MILP built directly from the problem statement.
Usage: python3 code/theory_check.py OUT.csv      -> one row per dataset x cap x rule x comparison.
Odd-n median is checked on HELM (n=57); OLLB has n=6 (even): median there has no closed form and is solver-only,
checked against brute force in tests/test_scorerules.py.
"""
import sys, pathlib
import numpy as np, pandas as pd
from scipy.optimize import linprog, milp, LinearConstraint, Bounds
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from mti import scorerules as sr, theory as th, data as dt

EPS = 1e-3
CAPS = {"ollb": ["ceil", "front0", "gain5", "gain10", "gain20", "emp95", "emp99"],
        "helm": ["ceil", "front0", "gain5", "gain10", "gain20", "emp95T", "emp99T", "emp99P"]}
FV = {"mean": lambda X: X.mean(1), "min": lambda X: X.min(1), "median": lambda X: np.median(X, 1)}
CF = {"mean": th.p1_mean, "min": th.p2_min, "median": th.p3_median_odd}


def generic(rule, x, tau, c):
    """L1 and K from a generic LP (L1) / MILP (K) over y in [x, c] and binary task indicators."""
    n = len(x); lvl = tau + EPS; h = c - x
    if rule == "mean":          # LP: min sum(y-x) s.t. sum y >= n lvl
        r = linprog(np.ones(n), A_ub=-np.ones((1, n)), b_ub=[-(n * lvl)], bounds=list(zip(x, c)), method="highs")
        L1 = r.fun - x.sum() if r.status == 0 else np.inf
    # MILP variables: y_t (n), r_t (n, raised), b_t (n, above level); constraints depend on the rule
    nv = 3 * n
    cons, lo, hi = [], [], []
    A = np.zeros((n, nv)); A[np.arange(n), np.arange(n)] = 1; A[np.arange(n), n + np.arange(n)] = -h   # y - x <= h r
    cons.append(A); lo.append(np.full(n, -np.inf)); hi.append(x)
    if rule == "mean":
        a = np.zeros((1, nv)); a[0, :n] = 1; cons.append(a); lo.append([n * lvl]); hi.append([np.inf])
    elif rule == "min":
        a = np.zeros((n, nv)); a[np.arange(n), np.arange(n)] = 1; cons.append(a); lo.append(np.full(n, lvl)); hi.append(np.full(n, np.inf))
    else:   # median, n odd: at least m tasks with y_t >= lvl : y_t >= lvl b_t + x_t (1-b_t)  (b_t=1 -> y_t >= lvl)
        m = (n + 1) // 2
        a = np.zeros((n, nv)); a[np.arange(n), np.arange(n)] = 1; a[np.arange(n), 2 * n + np.arange(n)] = -(lvl - x)
        cons.append(a); lo.append(x.copy()); hi.append(np.full(n, np.inf))
        a = np.zeros((1, nv)); a[0, 2 * n:] = 1; cons.append(a); lo.append([m]); hi.append([np.inf])
    lb = np.concatenate([x, np.zeros(2 * n)]); ub = np.concatenate([c, np.ones(2 * n)])
    integ = np.concatenate([np.zeros(n), np.ones(2 * n)])
    out = {}
    for name, cvec in (("L1", np.concatenate([np.ones(n), np.zeros(2 * n)])), ("K", np.concatenate([np.zeros(n), np.ones(n), np.zeros(n)]))):
        res = milp(cvec, constraints=[LinearConstraint(A_, l, u) for A_, l, u in zip(cons, lo, hi)], integrality=integ,
                   bounds=Bounds(lb, ub), options={"mip_rel_gap": 0.0})
        out[name] = (res.fun - x.sum() if name == "L1" else res.fun) if res.status == 0 else np.inf
    if rule == "mean": out["L1"] = L1
    return out["L1"], out["K"]


def dev(a, b):
    if np.isinf(a) and np.isinf(b): return 0.0, 0
    if np.isinf(a) or np.isinf(b): return np.nan, 1
    return abs(a - b), 0


rows = []
rng = np.random.default_rng(0)
for ds in ("ollb", "helm"):
    X, names, tasks, meta = dt.load(ds); M, n = X.shape
    sample = rng.choice(M, size=min(M, 60), replace=False)
    for cap_name in CAPS[ds]:
        for rule in ("mean", "min", "median"):
            if rule == "median" and n % 2 == 0:
                rows.append(dict(dataset=ds, cap=cap_name, rule=rule, comparison="closed_form_vs_solver", n_targets=M,
                                 note="n even: no closed form; solver-only (brute-force verified in tests)")); continue
            V = FV[rule](X)
            acc = {k: dict(l1=0.0, k=0.0, mism=0, nT=0, ninf=0) for k in ("solver", "generic")}
            for i in range(M):
                x = X[i]; c = np.maximum(dt.make_cap(cap_name, X, i), x); tau = np.delete(V, i).max()
                cl = CF[rule](x, tau, c, EPS)
                s = sr.min_investment(rule, X, i, c, EPS, measures=("L1", "K"))
                comps = {"solver": (s["L1"], s["K"])}
                if i in sample and V[i] <= tau: comps["generic"] = generic(rule, x, tau, c)
                for key, (l1, kk) in comps.items():
                    d1, m1 = dev(cl[0], l1); d2, m2 = dev(float(cl[1]), float(kk))
                    a = acc[key]; a["nT"] += 1; a["mism"] += int(m1 or m2); a["ninf"] += int(np.isinf(cl[0]))
                    a["l1"] = max(a["l1"], 0 if np.isnan(d1) else d1); a["k"] = max(a["k"], 0 if np.isnan(d2) else d2)
            for key, a in acc.items():
                rows.append(dict(dataset=ds, cap=cap_name, rule=rule, comparison=f"closed_form_vs_{key}", n_targets=a["nT"],
                                 n_infeasible=a["ninf"], max_abs_dev_L1=a["l1"], max_abs_dev_K=a["k"], feasibility_mismatches=a["mism"]))
        print(ds, cap_name, flush=True)
pd.DataFrame(rows).to_csv(sys.argv[1], index=False)
