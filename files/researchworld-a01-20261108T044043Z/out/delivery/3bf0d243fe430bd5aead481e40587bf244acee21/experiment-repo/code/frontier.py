"""Feasibility frontier per dataset x cap x rule from a core table.
Usage: python3 code/frontier.py CORE_CSV OUT_CSV
Targets are grouped by their rank under the mean (rank_mean; same targets for every rule). Targets that are already first under
the rule (zero investment) count as feasible; censored (solver time limit) targets are left out of the group and counted in `n_censored`.
Rows (group = rank stratum, or `all` for the whole table):
  n, n_feasible, feas_frac with a 95% bootstrap CI over targets (percentile, 1000 draws, seed 0).
Rows with group `frontier` (per dataset x cap x rule), for the targets with rank_mean >= 2 that were evaluated:
  max_feasible_rank = the largest rank_mean of a feasible target (CI: bootstrap over targets),
  prefix_rank = the largest r such that every evaluated target with rank_mean <= r is feasible (CI: same bootstrap),
  r50 = the smallest stratum lower end whose feasible share is below 0.5 (empty if none).
OLLB ordinal rules cover only the 50 best targets under the mean, so their max_feasible_rank cannot exceed 51 and is a lower bound.
"""
import sys, numpy as np, pandas as pd

inp, outp = sys.argv[1], sys.argv[2]
rng = np.random.default_rng(0)
d = pd.read_csv(inp)
BINS = {"ollb": [(2, 5), (6, 10), (11, 30), (31, 100), (101, 300), (301, 10**6)],
        "helm": [(2, 3), (4, 5), (6, 10), (11, 20), (21, 40), (41, 10**6)]}
BINS["ollb_leaf"] = BINS["ollb6_leafslice"] = BINS["ollb"]      # leaf-task run (499 models)
lab = lambda lo, hi: f"{lo}-{hi}" if hi < 10**6 else f">{lo-1}"
B = 1000

def ci(x):
    return np.percentile(x[rng.integers(0, len(x), (B, len(x)))].mean(axis=1), [2.5, 97.5])

def prefix(rank, feas):
    o = np.argsort(rank, kind="stable"); bad = ~feas[o]
    return rank[o][bad.argmax()] - 1 if bad.any() else rank.max()

rows = []
for (ds, cap, rule), s in d[d.rank_mean >= 2].groupby(["dataset", "cap", "rule"]):
    cens = s.L1.isna()
    t = s[~cens]
    if not len(t): continue
    feas = np.isfinite(t.L1.values); rk = t.rank_mean.values.astype(float)
    for g in [("all", 2, 10**6)] + [(lab(lo, hi), lo, hi) for lo, hi in BINS[ds]]:
        m = (rk >= g[1]) & (rk <= g[2])
        if not m.any(): continue
        f = feas[m].astype(float); lo_, hi_ = ci(f)
        rows.append(dict(dataset=ds, cap=cap, rule=rule, group=g[0], n=int(m.sum()), n_feasible=int(f.sum()), feas_frac=f.mean(),
                         feas_lo=lo_, feas_hi=hi_, n_censored=int(cens[(s.rank_mean >= g[1]) & (s.rank_mean <= g[2])].sum())))
    idx = np.arange(len(t))
    mf = lambda ix: (rk[ix][feas[ix]].max() if feas[ix].any() else 0)
    pf = lambda ix: prefix(rk[ix], feas[ix])
    bm = [mf(rng.integers(0, len(t), len(t))) for _ in range(B)]
    bp = [pf(rng.integers(0, len(t), len(t))) for _ in range(B)]
    fr = {g: feas[(rk >= lo) & (rk <= hi)].mean() for lo, hi in BINS[ds] for g in [lo] if ((rk >= lo) & (rk <= hi)).any()}
    r50 = next((lo for lo, v in sorted(fr.items()) if v < 0.5), np.nan)
    rows.append(dict(dataset=ds, cap=cap, rule=rule, group="frontier", n=len(t), n_feasible=int(feas.sum()), feas_frac=feas.mean(),
                     max_feasible_rank=mf(idx), max_feasible_lo=np.percentile(bm, 2.5), max_feasible_hi=np.percentile(bm, 97.5),
                     prefix_rank=pf(idx), prefix_lo=np.percentile(bp, 2.5), prefix_hi=np.percentile(bp, 97.5), r50=r50,
                     n_censored=int(cens.sum())))
pd.DataFrame(rows).to_csv(outp, index=False)
