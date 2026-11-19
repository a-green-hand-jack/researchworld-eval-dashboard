"""Linf as a cap-saturated uniform lift, and what that lift costs in L1 and K compared with the L1-/K-optimal investment.
For every rule here the Linf column of the core tables is the smallest d such that raising EVERY task to min(x_t + d, c_t) makes
the target strictly first (monotone rules: any plan whose largest raise is <= d is dominated by that saturated uniform lift).
Where caps bind, the lift moves fewer points than d on those tasks, so the literal 'raise every task by d' overstates its own cost.
Per feasible target we recompute the lift's real cost:  L1_unif = sum_t min(Linf, c_t - x_t),  K_unif = #tasks with c_t > x_t,
and report L1_unif / L1_opt, K_unif / K_opt, the share of targets for which at least one cap binds at Linf, and Linf / (L1_opt/n)
(the uniform raise relative to the average raise of the optimum).
Usage: python3 code/uniform_lift.py OUT_DIR   (reads OUT_DIR/core_*.csv, writes OUT_DIR/summary/uniform_vs_optimal_*.csv + per-target file)"""
import sys, pathlib
import numpy as np, pandas as pd
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from mti import data as dt

out = pathlib.Path(sys.argv[1]); rng = np.random.default_rng(0)
CAPS = {"ollb": ["emp99", "ceil"], "helm": ["emp99T", "ceil"]}
bins = [(2, 2), (3, 5), (6, 10), (11, 30), (31, 100), (101, 10**6)]
lab = lambda lo, hi: f"{lo}" if lo == hi else (f"{lo}-{hi}" if hi < 10**6 else f">{lo-1}")
grp = lambda r: next(lab(lo, hi) for lo, hi in bins if lo <= r <= hi)

def bmed(v, B=1000):
    v = np.asarray(v, float); v = v[np.isfinite(v)]
    if len(v) == 0: return (np.nan,) * 3
    return (np.median(v), *np.percentile([np.median(rng.choice(v, len(v))) for _ in range(B)], [2.5, 97.5]))

for ds in ("ollb", "helm"):
    X, names, tasks, meta = dt.load(ds); n = X.shape[1]
    core = pd.read_csv(out / f"core_{ds}.csv")
    core = core[core.cap.isin(CAPS[ds]) & (core.status == "ok") & (core.rank_mean >= 2) & core.rule.isin(
        ["mean", "median", "min", "geomean", "harmonic", "pow-2", "borda", "condorcet", "plurality", "copeland"])]
    rows = []
    for r in core.itertuples():
        head = np.maximum(dt.make_cap(r.cap, X, r.target_idx) - X[r.target_idx], 0)
        l1u = float(np.minimum(r.Linf, head).sum()); ku = int((head > 0).sum())
        rows.append(dict(dataset=ds, cap=r.cap, rule=r.rule, target=r.target, target_idx=r.target_idx, rank_mean=r.rank_mean,
                         L1_opt=r.L1, K_opt=r.K, Linf=r.Linf, L1_unif=l1u, K_unif=ku, cap_binds=bool((head < r.Linf - 1e-6).any()),
                         n_capped=int((head < r.Linf - 1e-6).sum()), L1_ratio=l1u / r.L1, K_ratio=ku / r.K, Linf_over_mean_raise=r.Linf / (r.L1 / n)))
    P = pd.DataFrame(rows); P.to_csv(out / "summary" / f"uniform_vs_optimal_{ds}_targets.csv", index=False)
    P["group"] = [grp(r) for r in P.rank_mean]
    S = []
    for (cap, rule, g), s in list(P.groupby(["cap", "rule", "group"])) + list(P.assign(group="all").groupby(["cap", "rule", "group"])):
        d = dict(dataset=ds, cap=cap, rule=rule, group=g, n_feasible=len(s), share_cap_binds=s.cap_binds.mean(), mean_n_capped=s.n_capped.mean())
        for m in ("L1_ratio", "K_ratio", "Linf_over_mean_raise"):
            d[m + "_med"], d[m + "_lo"], d[m + "_hi"] = bmed(s[m])
        d["L1_ratio_max"] = s.L1_ratio.max(); d["share_L1_ratio_le_1.01"] = float((s.L1_ratio <= 1.01).mean())
        S.append(d)
    S = pd.DataFrame(S); S.to_csv(out / "summary" / f"uniform_vs_optimal_{ds}.csv", index=False)
    print(ds); print(S[S.group == "all"].round(3).to_string())
