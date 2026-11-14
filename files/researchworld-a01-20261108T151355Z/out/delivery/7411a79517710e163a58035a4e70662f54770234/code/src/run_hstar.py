"""Minimum-cap measure h*(rule, target): the smallest uniform per-task gain cap h (cap_t = min(x_t + h, 100)) at which first is feasible
(margin eps). Feasibility is monotone in h, so bisection on the exact solver; h* is reported as the upper end of the final bracket (feasible
cap), bracket width `tol`. h* = inf if first is infeasible even with h = 100 (cap 100 everywhere); NaN if a solver call hit its time limit.
Usage: python3 src/run_hstar.py DATASET RULES TARGETS OUT [--tol 0.05] [--nsample 100] [--eps 1e-3]
"""
import sys, time, pathlib, argparse
import numpy as np, pandas as pd
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from scipy.stats import rankdata
from mti import scorerules as sr, ordinal as od, data as dt

ap = argparse.ArgumentParser(); ap.add_argument("dataset"); ap.add_argument("rules"); ap.add_argument("targets"); ap.add_argument("out")
ap.add_argument("--tol", type=float, default=0.05); ap.add_argument("--eps", type=float, default=1e-3)
ap.add_argument("--seed", type=int, default=0); ap.add_argument("--nsample", type=int, default=100)
a = ap.parse_args()
X, names, tasks, meta = dt.load(a.dataset); M, n = X.shape
mean_rank = rankdata(-X.mean(axis=1), method="min")
if a.targets == "all": targets = np.arange(M)
elif a.targets.startswith("top"): targets = np.argsort(mean_rank, kind="stable")[: int(a.targets[3:])]     # ranks 1..k (rank 1 is already first: h*=0)
else:      # same rank-stratified sample as run_core.py
    order = np.argsort(mean_rank, kind="stable"); head = order[1:21]; tail = order[21:]
    if len(tail) > a.nsample:
        pos = np.unique(np.round(np.exp(np.linspace(np.log(1), np.log(len(tail)), a.nsample))).astype(int) - 1); tail = tail[pos]
    targets = np.concatenate([head, tail])

def first_status(rule, i, h):
    """'ok' | 'inf' | 'nan' for first at gain cap h"""
    cap = np.minimum(X[i] + h, 100.0)
    v = (sr.min_investment(rule, X, i, cap, a.eps, measures=("L1",))["L1"] if rule in sr.RULES
         else od.MIN_INV[rule](X, i, cap, a.eps, "L1"))
    return "nan" if np.isnan(v) else ("inf" if np.isinf(v) else "ok")

rows = []; t0 = time.time()
for rule in a.rules.split(","):
    for i in targets:
        s0 = first_status(rule, i, 0.0)
        if s0 == "ok": hs, st, it = 0.0, "ok", 0
        else:
            sh = first_status(rule, i, 100.0)
            if sh != "ok": hs, st, it = (np.inf if sh == "inf" else np.nan), ("infeasible" if sh == "inf" else "censored"), 1
            else:
                lo, hi, it, st = 0.0, 100.0, 1, "ok"      # lo infeasible, hi feasible
                while hi - lo > a.tol:
                    mid = (lo + hi) / 2; s = first_status(rule, i, mid); it += 1
                    if s == "nan": st = "censored"; break
                    if s == "ok": hi = mid
                    else: lo = mid
                hs = hi if st == "ok" else np.nan
        rows.append(dict(dataset=a.dataset, rule=rule, target=names[i], target_idx=int(i), rank_mean=int(mean_rank[i]), hstar=hs,
                         tol=a.tol if (st == "ok" and hs > 0) else 0.0, status=st, n_solves=it, seed=a.seed))
    print(f"{rule} done {time.time()-t0:.0f}s", flush=True); pd.DataFrame(rows).to_csv(a.out, index=False)
