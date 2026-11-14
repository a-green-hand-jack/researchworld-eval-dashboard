"""Bootstrap of the empirical headroom caps (request experiment-repo#7).
Usage: python3 code/capboot.py DATASET OUT_CSV [--B 1000] [--seed 0]     DATASET: ollb | helm
The caps emp99 / emp95 (OLLB, per task) and emp99T / emp95T (HELM, the OLLB MMLU-PRO quantile on every task) are q-quantiles of the 540
(fine-tune minus base model) gain pairs. Each draw resamples the 540 pairs with replacement (scheme `pairs`: whole rows, keeps the
cross-task dependence of the gains; scheme `indep`: every task's column resampled separately), recomputes the quantile caps and the
feasibility of every target with mean rank >= 2 under mean, median and min. Feasibility is exact and closed-form here: for these
monotone rules a target can be made strictly first iff the rule value at its caps y = min(x + h, 100) is >= the best rival's value + eps
(eps = 1e-3), or it already is first. Ordinal rules are not bootstrapped (MILP per target and draw).
Output rows: dataset, scheme, cap, rule, group (`all`, rank strata as in frontier.py, or `frontier`), and the point value (observed
caps), the bootstrap mean and the 2.5 / 97.5 percentiles of: feas_frac (stratum rows) or max_feasible_rank / prefix_rank (frontier rows).
Selection bias of the 540 published pairs is not covered: only sampling noise of the quantile is.
"""
import sys, pathlib, argparse
import numpy as np, pandas as pd
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from scipy.stats import rankdata
from mti import scorerules as sr, data as dt

ap = argparse.ArgumentParser(); ap.add_argument("dataset"); ap.add_argument("out")
ap.add_argument("--B", type=int, default=1000); ap.add_argument("--seed", type=int, default=0); ap.add_argument("--eps", type=float, default=1e-3)
a = ap.parse_args()
rng = np.random.default_rng(a.seed)
X, names, tasks, meta = dt.load(a.dataset); M, n = X.shape
G = dt._gains(); P = len(G); MP = dt.dt_index("MMLU-PRO")
BINS = {"ollb": [(2, 5), (6, 10), (11, 30), (31, 100), (101, 300), (301, 10**6)], "helm": [(2, 3), (4, 5), (6, 10), (11, 20), (21, 40), (41, 10**6)]}
lab = lambda lo, hi: f"{lo}-{hi}" if hi < 10**6 else f">{lo-1}"
rank = rankdata(-X.mean(axis=1), method="min"); keep = rank >= 2; rk = rank[keep].astype(float)
RULES = ["mean", "median", "min"]
val = {r: sr.RULES[r][0](X) for r in RULES}
def rival_best(v):
    o = np.argsort(-v); b1, b2 = v[o[0]], v[o[1]]
    return np.where(np.arange(len(v)) == o[0], b2, b1)
tau = {r: rival_best(val[r]) for r in RULES}

def hvec(gains, q):
    hq = np.percentile(gains, q, axis=0)
    return hq if a.dataset == "ollb" else np.full(n, hq[MP])        # OLLB per task; HELM transfer cap

def feasible(h, rule):
    C = np.minimum(X + np.maximum(h, 0), 100.0)
    return ((sr.RULES[rule][0](C) >= tau[rule] + a.eps) | (val[rule] > tau[rule]))[keep]

def prefix(f):
    o = np.argsort(rk, kind="stable"); bad = ~f[o]
    return rk[o][bad.argmax()] - 1 if bad.any() else rk.max()

def stats(f):
    out = {"all": f.mean()}
    for lo, hi in BINS[a.dataset]:
        m = (rk >= lo) & (rk <= hi)
        if m.any(): out[lab(lo, hi)] = f[m].mean()
    out["frontier:max_feasible_rank"] = rk[f].max() if f.any() else 0.0
    out["frontier:prefix_rank"] = prefix(f)
    return out

rows = []
for q, cap in ((99, "emp99"), (95, "emp95")):
    cap = cap + ("T" if a.dataset == "helm" else "")
    for rule in RULES:
        pt = stats(feasible(hvec(G, q), rule))
        for scheme in ("pairs", "indep"):
            B = []
            for _ in range(a.B):
                if scheme == "pairs": Gb = G[rng.integers(0, P, P)]
                else: Gb = np.column_stack([G[rng.integers(0, P, P), t] for t in range(G.shape[1])])
                B.append(stats(feasible(hvec(Gb, q), rule)))
            B = pd.DataFrame(B)
            for k in pt:
                grp, _, m = k.partition(":")
                rows.append(dict(dataset=a.dataset, scheme=scheme, cap=cap, rule=rule, group=grp, measure=m or "feas_frac", point=pt[k],
                                 boot_mean=B[k].mean(), lo=np.percentile(B[k], 2.5), hi=np.percentile(B[k], 97.5), B=a.B))
        print(cap, rule, "done", flush=True)
pd.DataFrame(rows).to_csv(a.out, index=False)
