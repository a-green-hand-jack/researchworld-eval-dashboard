"""Stretch: spillover variant (assumption A3 relaxed). Targeted effort d_t >= 0 on task t changes ALL scores:
    y_s = x_s + d_s - kappa * (D - d_s),   D = sum d,   kappa = lam / (n-1)    (a total of lam*d points is lost spread evenly over the other tasks)
subject to 0 <= y_s <= c_s. Investment = D (total effort, L1) or number of tasks with d_t>0 (K). lam=0 is the main model (validated against the main solvers).
Rules (exact MILP): mean (LP), min, median (n odd, binary 'task ends >= b'). Usage: python3 src/run_spillover.py DATASET CAPS OUT [--nsample 40]
"""
import sys, pathlib, argparse
import numpy as np, pandas as pd
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from scipy.optimize import milp, LinearConstraint, Bounds
from scipy.stats import rankdata
from mti import scorerules as sr, data as dt

def solve(rule, x, c, b, kappa, objective):
    n = len(x); m = (n + 1) // 2
    # vars: d(n), r(n) [raised], z(n) [task ends >= b] ; y_s = x_s + (1+kappa) d_s - kappa D
    N = 3 * n; rows, lo, hi = [], [], []
    def add(r, l, u): rows.append(r); lo.append(l); hi.append(u)
    Y = np.zeros((n, N))                                  # y = x + Y @ var
    for s in range(n): Y[s, :n] = -kappa; Y[s, s] += 1 + kappa
    for s in range(n): add(Y[s], -x[s], c[s] - x[s])      # 0 <= y_s <= c_s  (lower bound on y: >= 0)
    rg = 100.0
    for s in range(n):
        r = np.zeros(N); r[s] = 1; r[n + s] = -rg; add(r, -np.inf, 0)         # d_s <= rg r_s
    if rule == "mean":
        add(Y.sum(0), n * b - x.sum(), np.inf)
    elif rule == "min":
        for s in range(n): add(Y[s], b - x[s], np.inf)
    elif rule == "median":
        big = 200.0
        for s in range(n):
            r = Y[s].copy(); r[2 * n + s] = -big; add(r, b - x[s] - big, np.inf)    # y_s >= b - big (1 - z_s)
        r = np.zeros(N); r[2 * n:] = 1; add(r, m, np.inf)
    cost = np.zeros(N)
    if objective == "L1": cost[:n] = 1
    else: cost[n:2 * n] = 1
    integ = np.zeros(N); integ[n:] = 1
    ub = np.concatenate([np.full(n, 100.0), np.ones(2 * n)])
    res = milp(cost, constraints=LinearConstraint(np.array(rows), lo, hi), integrality=integ, bounds=Bounds(np.zeros(N), ub), options={"time_limit": 60})
    if res.status in (2, 3): return np.inf
    if not res.success or res.x is None: return np.nan
    return float(res.fun)

if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("dataset"); ap.add_argument("caps"); ap.add_argument("out")
    ap.add_argument("--nsample", type=int, default=40); ap.add_argument("--lams", default="0,0.1,0.25"); ap.add_argument("--eps", type=float, default=1e-3)
    a = ap.parse_args()
    X, names, tasks, meta = dt.load(a.dataset); M, n = X.shape
    rules = ["mean", "min"] + (["median"] if n % 2 else [])
    mr = rankdata(-X.mean(axis=1), method="min"); order = np.argsort(mr, kind="stable"); tail = order[21:]
    pos = np.unique(np.round(np.exp(np.linspace(0, np.log(len(tail)), a.nsample))).astype(int) - 1)
    targets = np.concatenate([order[1:21], tail[pos]]); rows = []
    for cap_name in a.caps.split(","):
        for rule in rules:
            fv = sr.RULES[rule][0](X)
            for lam in map(float, a.lams.split(",")):
                for i in targets:
                    x = X[i]; tau = np.delete(fv, i).max(); c = np.maximum(dt.make_cap(cap_name, X, i), x); b = tau + a.eps
                    if fv[i] > tau: L1 = K = 0.0
                    else: L1 = solve(rule, x, c, b, lam / (n - 1), "L1"); K = solve(rule, x, c, b, lam / (n - 1), "K")
                    rows.append(dict(dataset=a.dataset, cap=cap_name, rule=rule, lam=lam, target=names[i], rank_mean=int(mr[i]), L1=L1, K=K,
                                     feasible=bool(np.isfinite(L1) and np.isfinite(K))))
            print(cap_name, rule, "done", flush=True); pd.DataFrame(rows).to_csv(a.out, index=False)
    pd.DataFrame(rows).to_csv(a.out, index=False)
