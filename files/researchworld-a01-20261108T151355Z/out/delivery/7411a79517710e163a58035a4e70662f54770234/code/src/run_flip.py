"""Claim C7(iv): how robust is 'first' to evaluation noise?  For the *uniform* strategy (raise every task by d, clipped at the cap),
  d_eps  = smallest d that makes the target first on the observed scores (margin eps),
  p_eps  = probability that the target is still first when every cell of the (raised) matrix is redrawn with its sampling noise,
  d_95   = smallest d with P(first) >= 0.95 under that noise   (extra investment needed to *stay* first with 95% probability).
Noise: independent N(0, se^2) per cell (binomial SE from item counts, as in run_robust.py), common random numbers across d.
Usage: python3 src/run_flip.py DATASET RULES CAP OUT [--R 200] [--seed 0] [--ntail 40]
"""
import sys, json, pathlib, argparse
import numpy as np, pandas as pd
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from scipy.stats import rankdata
from mti import scorerules as sr, ordinal as od, data as dt

ap = argparse.ArgumentParser()
for k in ("dataset", "rules", "cap", "out"): ap.add_argument(k)
ap.add_argument("--R", type=int, default=200); ap.add_argument("--seed", type=int, default=0); ap.add_argument("--ntail", type=int, default=40)
a = ap.parse_args(); rng = np.random.default_rng(a.seed)
X, names, tasks, meta = dt.load(a.dataset); M, n = X.shape; eps = 1e-3

def se_matrix():
    if a.dataset == "helm":
        ne = pd.read_csv(dt.PROC / "helm_mmlu_neval.csv", index_col=0).loc[tasks, "n_eval"].values
        p = np.clip(X / 100, 0.001, 0.999); return 100 * np.sqrt(p * (1 - p) / ne)
    j = json.load(open(dt.PROC / "ollb_noise.json"))
    N = np.array([j["n_items"][t] for t in dt.OLLB_TASKS], float); L = np.array([j["floor"][t] for t in dt.OLLB_TASKS])
    praw = np.clip(L + (1 - L) * X / 100, 0.001, 0.999); return 100 * np.sqrt(praw * (1 - praw) / N) / (1 - L)
SE = se_matrix()

def value(rule, Y):
    if rule in sr.RULES: return sr.RULES[rule][0](Y)
    if rule == "borda": return od.borda_points(Y)
    raise KeyError(rule)

def is_first(rule, Y, i, margin):
    v = value(rule, Y); return v[i] > np.delete(v, i).max() + margin * (rule != "borda") + 1e-12 * 0

def raised(i, d):
    Y = X.copy(); Y[i] = np.minimum(X[i] + d, dt.make_cap(a.cap, X, i)); return Y

def bisect(pred, hi, tol=1e-3):
    if not pred(hi): return np.inf
    lo = 0.0
    if pred(lo): return 0.0
    while hi - lo > tol:
        mid = (lo + hi) / 2
        if pred(mid): hi = mid
        else: lo = mid
    return hi

mean_rank = rankdata(-X.mean(axis=1), method="min"); order = np.argsort(mean_rank, kind="stable")
tail = order[21:]
pos = np.unique(np.round(np.exp(np.linspace(0, np.log(len(tail)), a.ntail))).astype(int) - 1); targets = np.concatenate([order[1:21], tail[pos]])
rows = []
for rule in a.rules.split(","):
    for i in targets:
        Z = rng.standard_normal((a.R,) + X.shape)             # common random numbers across d
        def p_first(d):
            Y = raised(i, d); k = 0
            for r in range(a.R):
                Yn = np.clip(Y + SE * Z[r], 0, 100); k += is_first(rule, Yn, i, 0.0)
            return k / a.R
        d_eps = bisect(lambda d: is_first(rule, raised(i, d), i, eps), 100.0)
        if not np.isfinite(d_eps): rows.append(dict(rule=rule, target=names[i], rank_mean=int(mean_rank[i]), d_eps=np.inf, p_eps=np.nan, d95=np.inf, feasible=False, seed=a.seed)); continue
        p_eps = p_first(d_eps); d95 = bisect(lambda d: p_first(d) >= 0.95, 100.0, tol=0.01)
        rows.append(dict(rule=rule, target=names[i], rank_mean=int(mean_rank[i]), d_eps=d_eps, p_eps=p_eps, d95=d95, feasible=bool(np.isfinite(d95)), seed=a.seed))
    print(rule, "done", flush=True); pd.DataFrame(rows).to_csv(a.out, index=False)
pd.DataFrame(rows).to_csv(a.out, index=False)
