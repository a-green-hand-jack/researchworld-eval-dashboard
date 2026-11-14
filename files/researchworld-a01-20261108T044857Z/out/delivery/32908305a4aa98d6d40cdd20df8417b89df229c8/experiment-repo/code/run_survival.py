"""Fixed-policy survival under evaluation noise (request experiment-repo#8).
Usage: python3 code/run_survival.py DATASET OUT_CSV [--R 300] [--seed 0]
For the targets of the evaluation-noise runs (OLLB: mean ranks 2,3,5,10,20,50,100, cap emp99; HELM: ranks 2,3,5,10,20,40, cap emp99T) and each
rule, take an optimal L1 raise vector y* computed ON THE OBSERVED DATA (score rules: margin eps in {0.001, 1, 2} points, vectors from
mti/policies.py, mean = raise concentrated on the largest headrooms; ordinal rules: strict comparisons, MILP solution, eps = 0.001 is
only the witness granularity), then draw evaluation noise exactly as run_robust.py noise does (same seed, same standard-normal stream:
rivals' cells X_jt + se_jt z_jt clipped to [0, 100], independent Gaussian with binomial SE from the item counts; OLLB counts come from
one results file and are assumed equal for all models) and apply it ALSO to the target's raised row (y*_t + se(y*_t) z_it, clipped;
the target's un-raised cells keep their usual noise). Report the share of draws in which the target is strictly first under the rule
(ties are not wins), with a Wilson 95% interval, and the number of draws. The policy is NOT re-optimised on the noisy data.
Rows: dataset, cap, rule, eps, target, rank_mean, status (ok | already_first | infeasible | censored), cost_L1 (L1 of y*), K, wins, draws,
survival, wilson_lo, wilson_hi, and `survival_noraise` (same draws, target not raised: its own noisy row) for context.
"""
import sys, json, pathlib, argparse, time
import numpy as np, pandas as pd
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from scipy.stats import rankdata
from mti import scorerules as sr, ordinal as od, data as dt, policies as pol

ap = argparse.ArgumentParser(); ap.add_argument("dataset"); ap.add_argument("out")
ap.add_argument("--R", type=int, default=300); ap.add_argument("--seed", type=int, default=0)
a = ap.parse_args()
X0, names, tasks, meta = dt.load(a.dataset); M, n = X0.shape
if a.dataset == "ollb":
    CAP, STRATA, SCORE, ORD = "emp99", [2, 3, 5, 10, 20, 50, 100], ["mean", "median", "min"], ["borda", "condorcet", "plurality"]
else:
    CAP, STRATA, SCORE, ORD = "emp99T", [2, 3, 5, 10, 20, 40], ["mean", "median", "min"], ["borda", "condorcet", "plurality"]
MARGINS = [1e-3, 1.0, 2.0]

def se_of(X):
    """per-cell SE in score points (same as run_robust.standard_errors)"""
    if a.dataset == "helm":
        ne = pd.read_csv(dt.PROC / "helm_mmlu_neval.csv", index_col=0).loc[tasks, "n_eval"].values
        p = np.clip(X / 100, 0.001, 0.999); return 100 * np.sqrt(p * (1 - p) / ne)
    j = json.load(open(dt.PROC / "ollb_noise.json"))
    N = np.array([j["n_items"][t] for t in dt.OLLB_TASKS], float); L = np.array([j["floor"][t] for t in dt.OLLB_TASKS])
    praw = np.clip(L + (1 - L) * X / 100, 0.001, 0.999)
    return 100 * np.sqrt(praw * (1 - praw) / N) / (1 - L)

def wilson(k, m, z=1.959964):
    p = k / m; d = 1 + z * z / m; c = p + z * z / (2 * m); h = z * np.sqrt(p * (1 - p) / m + z * z / (4 * m * m))
    return (c - h) / d, (c + h) / d

rank = rankdata(-X0.mean(axis=1), method="min"); order0 = np.argsort(rank, kind="stable")
targets = [int(order0[r - 1]) for r in STRATA]
SE0 = se_of(X0)
# noise draws, identical to run_robust.py noise: one standard-normal (M, n) array per draw
rng = np.random.default_rng(a.seed); Z = [rng.standard_normal(X0.shape) for _ in range(a.R)]

def first(rule, Xn, i):
    if rule in sr.RULES: v = sr.RULES[rule][0](Xn); return v[i] > np.delete(v, i).max()
    return od.FIRST[rule](Xn) == i

rows = []; t0 = time.time()
for i in targets:
    cap = dt.make_cap(CAP, X0, i); x = X0[i]
    for rule in SCORE + ORD:
        for eps in (MARGINS if rule in SCORE else MARGINS[:1]):
            if rule in SCORE:
                v = sr.RULES[rule][0](X0); tau = np.delete(v, i).max()
                already = v[i] > tau
                y = x.copy() if already else pol.Y[rule](x, tau, cap, eps)
            else:
                res = od.MIN_INV[rule](X0, i, cap, eps, "L1", return_y=True); already = res[0] == 0.0
                y = res[1]
                if isinstance(res[0], float) and np.isnan(res[0]): y = "censored"
            row = dict(dataset=a.dataset, cap=CAP, rule=rule, eps=eps, target=names[i], rank_mean=int(rank[i]))
            if isinstance(y, str) or y is None:
                row.update(status="censored" if isinstance(y, str) else "infeasible"); rows.append(row); continue
            row.update(status="already_first" if already else "ok", cost_L1=float((y - x).sum()), K=int((y > x + 1e-12).sum()))
            se_y = se_of(y[None, :])[0]; w = w0 = 0
            for r in range(a.R):
                Xn = np.clip(X0 + SE0 * Z[r], 0, 100); Xr = Xn.copy()
                Xr[i] = np.clip(y + se_y * Z[r][i], 0, 100)
                w += bool(first(rule, Xr, i)); w0 += bool(first(rule, Xn, i))
            lo, hi = wilson(w, a.R)
            row.update(wins=w, draws=a.R, survival=w / a.R, wilson_lo=lo, wilson_hi=hi, survival_noraise=w0 / a.R); rows.append(row)
        print(f"target rank {rank[i]} rule {rule} {time.time()-t0:.0f}s", flush=True)
        pd.DataFrame(rows).to_csv(a.out, index=False)
pd.DataFrame(rows).to_csv(a.out, index=False)
