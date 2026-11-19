"""Numerical checks of the analytic statements used in the paper, on real score matrices (not only the random unit tests).
 T1 mean:    L1 = n*(tau+eps) - sum(x) when caps are slack; solver == independent LP (scipy linprog) on sampled targets.
 T2 mean:    K = fewest tasks whose headroom sum covers the need; Linf = (n*(tau+eps)-sum x)/n when slack (the uniform raise).
 T3 geomean/harmonic: water-filling optimum == generic constrained optimiser (SLSQP) on sampled targets.
 T4 min:     K = #tasks below tau_min+eps, L1 = sum of shortfalls. median (n odd): K = max(0,(n+1)/2 - #{x>=b}) if enough tasks can reach b.
 T5 rank rules on real data: Borda / Condorcet / plurality MILP == exhaustive enumeration on random 6-model x 4-task subsamples of real data.
 T6 ordering: for any target and caps, K_mean <= K_L1-greedy bound n; L1 >= Linf for all rules (an L-inf jump of d on k tasks costs <= k*d).
Prints PASS/FAIL lines and a summary table (results/theory_checks.csv).
"""
import sys, pathlib, itertools
import numpy as np, pandas as pd
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from scipy.optimize import linprog, minimize
from mti import scorerules as sr, ordinal as od, data as dt

rng = np.random.default_rng(0); EPS = 1e-3; rows = []
def rec(name, ds, n, maxerr, ok): rows.append(dict(check=name, dataset=ds, n_cases=n, max_abs_err=maxerr, passed=bool(ok))); print(("PASS" if ok else "FAIL"), name, ds, n, f"max err {maxerr:.2e}", flush=True)

for ds, cap_name in [("ollb", "ceil"), ("ollb", "gain10"), ("helm", "ceil"), ("helm", "front0")]:
    X, names, tasks, _ = dt.load(ds); M, n = X.shape
    mean_v = X.mean(1); order = np.argsort(-mean_v)
    targets = rng.choice(np.arange(1, M), min(60, M - 1), replace=False)
    e1 = e2 = e3 = e3h = e4 = e6 = 0.0; k1 = k2 = k4 = True
    for i in targets:
        cap = dt.make_cap(cap_name, X, i); c = np.maximum(cap, X[i]); x = X[i]
        out = sr.min_investment("mean", X, i, cap, EPS)
        tau = np.delete(mean_v, i).max(); need = n * (tau + EPS) - x.sum()
        # T1: LP
        if need > 0:
            r = linprog(np.ones(n), A_ub=-np.ones((1, n)), b_ub=-need, bounds=list(zip(np.zeros(n), c - x)))
            lp = r.fun if r.success else np.inf
        else: lp = 0.0
        e1 = max(e1, 0 if np.isinf(lp) and np.isinf(out["L1"]) else abs(lp - out["L1"]))
        if not np.isinf(out["L1"]) and (c - x).sum() >= need and np.isfinite(out["L1"]): e2 = max(e2, abs(out["L1"] - max(need, 0)))
        # T2: K greedy and Linf
        h = np.sort(c - x)[::-1]; kk = int(np.searchsorted(np.cumsum(h), need - 1e-12) + 1) if need > 0 else 0
        k1 &= (kk == out["K"]) or (np.isinf(out["K"]) and kk > n)
        if np.isfinite(out["Linf"]) and need > 0 and (c - x).min() >= out["Linf"]: e6 = max(e6, abs(out["Linf"] - need / n))
        # T6: L1 >= Linf, L1 <= n*Linf
        for rule in ("mean", "geomean", "median", "min"):
            o = sr.min_investment(rule, X, i, cap, EPS)
            if np.isfinite(o["L1"]): k4 &= (o["L1"] >= o["Linf"] - 1e-6) and (o["L1"] <= n * o["Linf"] + 1e-6)
        # T3 geomean / harmonic by SLSQP
        for rule, p, store in (("geomean", 0.0, "g"), ("harmonic", -1.0, "h")):
            o = sr.min_investment(rule, X, i, cap, EPS, measures=("L1",))
            if o["L1"] in (0.0, np.inf): continue
            vals = sr.RULES[rule][0](X); tau_r = np.delete(vals, i).max()
            f = lambda y: np.sum(y - x); g = lambda y: sr.RULES[rule][0](y) - (tau_r + EPS)
            best = np.inf
            for start in (np.minimum(x + 1, c), c):
                r = minimize(f, start, bounds=list(zip(x, c)), constraints=[{"type": "ineq", "fun": g}], method="SLSQP", options={"maxiter": 500, "ftol": 1e-12})
                if r.success and g(r.x) >= -1e-7: best = min(best, r.fun)
            if np.isfinite(best):
                err = abs(best - o["L1"]); (e3 if store == "g" else e3h).__class__
                if store == "g": e3 = max(e3, err)
                else: e3h = max(e3h, err)
        # T4: min / median(n odd)
        om = sr.min_investment("min", X, i, cap, EPS); b = np.delete(X.min(1), i).max() + EPS
        want_K = int((x < b).sum()) if (c >= b).all() else np.inf
        k2 &= (om["K"] == want_K)
        if n % 2:
            medv = np.median(X, axis=1); bb = np.delete(medv, i).max() + EPS
            ok = sr.min_investment("median", X, i, cap, EPS, measures=("K",))["K"]
            if medv[i] <= np.delete(medv, i).max():
                have = int((x >= bb).sum()); extra = int(((x < bb) & (c >= bb)).sum()); m = (n + 1) // 2
                w = max(0, m - have) if m - have <= extra else np.inf; k2 &= (ok == w)
    rec(f"T1 mean L1 == LP [{cap_name}]", ds, len(targets), e1, e1 < 1e-6)
    rec(f"T1 mean L1 == n(tau+eps)-sum x if slack [{cap_name}]", ds, len(targets), e2, e2 < 1e-9)
    rec(f"T2 mean K == greedy headroom cover [{cap_name}]", ds, len(targets), 0.0, k1)
    rec(f"T2 mean Linf == uniform raise need/n (slack) [{cap_name}]", ds, len(targets), e6, e6 < 1e-5)
    rec(f"T3 geomean water-filling == SLSQP [{cap_name}]", ds, len(targets), e3, e3 < 1e-3)
    rec(f"T3 harmonic water-filling == SLSQP [{cap_name}]", ds, len(targets), e3h, e3h < 1e-3)
    rec(f"T4 min / median(n odd) K closed forms [{cap_name}]", ds, len(targets), 0.0, k2)
    rec(f"T6 Linf <= L1 <= n*Linf (mean,geomean,median,min) [{cap_name}]", ds, len(targets), 0.0, k4)

# T5: rank rules vs exhaustive enumeration on real-data subsamples
def brute(rule, X, i, cap, obj):
    M, n = X.shape; x = X[i]; c = np.maximum(cap, x); f = od.FIRST[rule]
    opts = []
    for t in range(n):
        s = np.unique(np.delete(X[:, t], i)); lv = [x[t]] + [v for v in np.concatenate([s, s + EPS]) if x[t] < v <= c[t] + 1e-12]
        opts.append(lv)
    best = np.inf
    for y in itertools.product(*opts):
        y = np.array(y); Y = X.copy(); Y[i] = y
        if f(Y) == i: best = min(best, (y - x).sum() if obj == "L1" else (y > x).sum())
    return best
for ds in ("ollb", "helm"):
    X0, names, tasks, _ = dt.load(ds)
    for rule in ("borda", "condorcet", "plurality"):
        for obj in ("L1", "K"):
            err = 0; nc = 0; ok = True
            for _ in range(40):
                rr = rng.choice(X0.shape[0], 6, replace=False); cc = rng.choice(X0.shape[1], 4, replace=False)
                X = X0[np.ix_(rr, cc)]; i = int(rng.integers(6)); cap = np.minimum(X[i] + rng.choice([5, 20, 100], 4), 100)
                got = od.MIN_INV[rule](X, i, cap, EPS, obj); want = brute(rule, X, i, cap, obj); nc += 1
                if np.isinf(got) and np.isinf(want): continue
                e = abs(got - want); err = max(err, e if np.isfinite(e) else 1e9); ok &= e < 1e-6
            rec(f"T5 {rule} {obj} MILP == enumeration (6x4 real subsamples)", ds, nc, err, ok)
pd.DataFrame(rows).to_csv(pathlib.Path(__file__).resolve().parents[1] / "results" / "theory_checks.csv", index=False)
print("ALL PASS" if all(r["passed"] for r in rows) else "SOME FAIL")
