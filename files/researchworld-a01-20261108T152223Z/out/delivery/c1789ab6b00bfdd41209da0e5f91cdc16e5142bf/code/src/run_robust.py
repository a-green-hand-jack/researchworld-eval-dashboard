"""Robustness experiments.
  noise    : parametric bootstrap of evaluation noise (binomial SE per cell) -> distribution of minimum investment for fixed targets
  tasksub  : random task subsets of size n (HELM): scaling of the minimum investment with the number of tasks
  taskboot : bootstrap over tasks (resample n tasks with replacement) for fixed targets
Usage: python3 src/run_robust.py MODE DATASET RULES CAP OUT [--R 100] [--seed 0] [--ntargets 10]
"""
import sys, json, time, pathlib, argparse
import numpy as np, pandas as pd
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from scipy.stats import rankdata
from mti import scorerules as sr, ordinal as od, data as dt

ap = argparse.ArgumentParser()
for k in ("mode", "dataset", "rules", "cap", "out"): ap.add_argument(k)
ap.add_argument("--R", type=int, default=100); ap.add_argument("--seed", type=int, default=0)
ap.add_argument("--ntargets", type=int, default=10); ap.add_argument("--eps", type=float, default=1e-3)
ap.add_argument("--sizes", default="3,6,12,24,48")
a = ap.parse_args()
rng = np.random.default_rng(a.seed)
X0, names, tasks, meta = dt.load(a.dataset); M, n0 = X0.shape
rules = a.rules.split(",")

def standard_errors(X):
    """per-cell SE (score points). HELM: binomial with the number of evaluated items; OLLB: binomial with item counts, rescaled by 1/(1-floor)."""
    if a.dataset == "helm":
        ne = pd.read_csv(dt.PROC / "helm_mmlu_neval.csv", index_col=0).loc[tasks, "n_eval"].values
        p = np.clip(X / 100, 0.001, 0.999); return 100 * np.sqrt(p * (1 - p) / ne)
    j = json.load(open(dt.PROC / "ollb_noise.json"))
    N = np.array([j["n_items"][t] for t in dt.OLLB_TASKS], float); L = np.array([j["floor"][t] for t in dt.OLLB_TASKS])
    praw = np.clip(L + (1 - L) * X / 100, 0.001, 0.999)
    return 100 * np.sqrt(praw * (1 - praw) / N) / (1 - L)

def costs(X, i, rule, cap_name):
    cap = dt.make_cap(cap_name, X, i)
    if rule in sr.RULES: out = sr.min_investment(rule, X, i, cap, a.eps, measures=("L1", "K"))
    else: out = od.min_investment_ordinal(rule, X, i, cap, a.eps, measures=("L1", "K"))
    return out

def rank_in(X, i, rule):
    if rule in sr.RULES: v = sr.RULES[rule][0](X)
    elif rule == "borda": v = od.borda_points(X)
    elif rule == "plurality": mx = X.max(axis=0); t = X == mx; v = (t / t.sum(axis=0)).sum(axis=1)
    else: v = od.copeland_values(X)
    if np.isnan(v).any(): return -1
    return int(rankdata(-v, method="min")[i])

rows = []; t0 = time.time()
if a.mode in ("noise", "taskboot"):
    base_rank = rankdata(-X0.mean(axis=1), method="min"); targets = np.argsort(base_rank, kind="stable")[1:1 + a.ntargets]
    se = standard_errors(X0)
    for r in range(a.R):
        if a.mode == "noise": X = np.clip(X0 + se * rng.standard_normal(X0.shape), 0, 100)
        else:
            cols = rng.integers(0, n0, n0); X = X0[:, cols]
        for rule in rules:
            for i in targets:
                rows.append(dict(draw=r, rule=rule, target=names[i], rank_mean_obs=int(base_rank[i]), rank_rule=rank_in(X, i, rule),
                                 **costs(X, i, rule, a.cap)))
        if r % 10 == 0:
            print(f"draw {r} {time.time()-t0:.0f}s", flush=True); pd.DataFrame(rows).to_csv(a.out, index=False)
elif a.mode == "tasksub":
    for n in map(int, a.sizes.split(",")):
        for r in range(a.R):
            cols = rng.choice(n0, n, replace=False); X = X0[:, cols]
            for rule in rules:
                if rule in sr.RULES: v = sr.RULES[rule][0](X)
                elif rule == "borda": v = od.borda_points(X)
                else: mx = X.max(axis=0); t = X == mx; v = (t / t.sum(axis=0)).sum(axis=1)
                order = np.argsort(-v, kind="stable")
                for rk in (2, 5):
                    i = int(order[rk - 1])
                    c = costs(X, i, rule, a.cap)
                    gap = float(v[order[0]] - v[i])
                    rows.append(dict(n=n, draw=r, rule=rule, target_rank=rk, target=names[i], gap_own=gap, **c))
        print(f"n={n} {time.time()-t0:.0f}s", flush=True); pd.DataFrame(rows).to_csv(a.out, index=False)
pd.DataFrame(rows).to_csv(a.out, index=False)
