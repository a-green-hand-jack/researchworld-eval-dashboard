"""Rank-stratified full-board sample of OLLB targets beyond rank 50 for the ordinal rules Borda and Condorcet-winner (issue #11).
Usage: python3 code/ordinal_sample.py OUT.csv [--per-stratum 10] [--seed 0] [--caps emp99,ceil] [--rules borda,condorcet] [--shard k/m] [--tl 120]
Board: all 4,496 unflagged OLLB models (dataset `ollb`), six tasks, eps = 1e-3. Targets: per_stratum models drawn at random (fixed seed) from each stratum of
rank_mean (rank under the six-task mean, ties get the best rank): 51-100, 101-300, 301-1000, 1001-max. Every model of the stratum is a candidate.
Per (target, cap, rule): (1) screen: put the target at the cap-saturated vector; if it is not strictly first there the rule is monotone, so no feasible
investment exists (status infeasible_screen, certain, no solver). (2) otherwise exact MILP (HiGHS, finite grid {s, s+eps}) for L1 and K with the time limit
--tl (wall-clock seconds); status ok / censored (limit hit: value NaN, not infeasible) / infeasible_milp (screen passed, grid MILP infeasible: possible
only at cap edges, reported separately). Linf by bisection on the saturated uniform lift (ordinal.linf_ordinal). Memory-lean MILPs: mti/ordinal_lean.py.
"""
import sys, time, argparse, pathlib
import numpy as np, pandas as pd
from scipy.stats import rankdata
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import mti.data as dt, mti.ordinal as od, mti.ordinal_lean as ol

ap = argparse.ArgumentParser(); ap.add_argument("out"); ap.add_argument("--per-stratum", type=int, default=10); ap.add_argument("--seed", type=int, default=0)
ap.add_argument("--caps", default="emp99,ceil"); ap.add_argument("--rules", default="borda,condorcet"); ap.add_argument("--shard", default="0/1")
ap.add_argument("--tl", type=int, default=120); ap.add_argument("--linf", type=int, default=1); ap.add_argument("--eps", type=float, default=1e-3)
a = ap.parse_args()
od.TIME_LIMIT = a.tl
X, names, tasks, meta = dt.load("ollb"); M = len(X)
rk = rankdata(-X.mean(1), method="min").astype(int)
STRATA = [(51, 100), (101, 300), (301, 1000), (1001, 10**6)]
rng = np.random.default_rng(a.seed); sample = []
for lo, hi in STRATA:
    pool = np.where((rk >= lo) & (rk <= hi))[0]; pool = pool[np.argsort(rk[pool], kind="stable")]
    pick = rng.choice(pool, size=min(a.per_stratum, len(pool)), replace=False)
    sample += [(int(i), f"{lo}-{hi}" if hi < 10**6 else f">{lo-1}") for i in pick[np.argsort(rk[pick], kind="stable")]]
sk, sm = map(int, a.shard.split("/")); jobs = [(i, s) for k, (i, s) in enumerate(sample) if k % sm == sk]
FIRST = od.FIRST; LEAN = {"borda": ol.borda_min_investment, "condorcet": ol.condorcet_min_investment}
rows = []; t0 = time.time()
for cap_name in a.caps.split(","):
    for rule in a.rules.split(","):
        for i, stratum in jobs:
            cap = dt.make_cap(cap_name, X, i); c = np.maximum(cap, X[i]); ts = time.time()
            Y = X.copy(); Y[i] = c; screen = FIRST[rule](Y) == i
            r = dict(dataset="ollb", cap=cap_name, rule=rule, target=names[i], target_idx=i, rank_mean=int(rk[i]), stratum=stratum, saturated_first=bool(screen))
            if FIRST[rule](X) == i: r.update(status="already_first", L1=0.0, K=0, Linf=0.0)
            elif not screen: r.update(status="infeasible_screen", L1=np.inf, K=np.inf, Linf=np.inf)
            else:
                L1 = LEAN[rule](X, i, cap, a.eps, "L1")
                if np.isnan(L1): r.update(status="censored", L1=np.nan, K=np.nan, Linf=np.nan)
                elif np.isinf(L1): r.update(status="infeasible_milp", L1=np.inf, K=np.inf, Linf=np.inf)
                else:
                    K = LEAN[rule](X, i, cap, a.eps, "K"); Linf = od.linf_ordinal(rule, X, i, cap, a.eps) if a.linf else np.nan
                    r.update(status="ok" if not np.isnan(K) else "censored_K", L1=L1, K=K, Linf=Linf)
            r["secs"] = round(time.time() - ts, 1); rows.append(r)
            print(cap_name, rule, names[i], r["rank_mean"], r["status"], r.get("L1"), r["secs"], flush=True)
            pd.DataFrame(rows).to_csv(a.out, index=False)
print(f"done {time.time()-t0:.0f}s", flush=True)
