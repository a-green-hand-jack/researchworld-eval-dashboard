"""Direct paired contrasts between ablation pairs (macro over 13 benchmarks, CI by bootstrap over repetitions, independent per benchmark), MAE and Spearman.
usage: python analysis_review_pairs.py tier1/metrics_by_seed.csv OUT.csv [B]
Contrasts (A - B): stratification given DR (strat+lowrank_dr - random+lowrank_dr); correction given stratified items (strat+lowrank_dr - strat+lowrank);
correction given random items (random+lowrank_dr - random+lowrank); stratification given the plain mean (strat+mean - random+mean); EB vs DR."""
import sys, numpy as np, pandas as pd
ms = pd.read_csv(sys.argv[1]); B = int(sys.argv[3]) if len(sys.argv) > 3 else 2000
rng = np.random.default_rng(1)
C = [("strat+lowrank_dr", "random+lowrank_dr", "stratification, given DR"), ("strat+lowrank_dr", "strat+lowrank", "DR correction, given stratified items"),
     ("random+lowrank_dr", "random+lowrank", "DR correction, given random items"), ("strat+mean", "random+mean", "stratification, plain mean"),
     ("strat+lowrank_eb", "strat+lowrank_dr", "EB shrinkage vs DR")]
rows = []
for sp in ("random", "extrap"):
    for n in (10, 20, 50, 100):
        for a, b, lab in C:
            reps = {m: [] for m in ("mae", "rmse", "spearman", "kendall")}; pts = {}; nb = 0
            for bench, g in ms[(ms.split_type == sp) & (ms.n == n)].groupby("benchmark"):
                ga = g[g.method == a].set_index("seed"); gb = g[g.method == b].set_index("seed"); nb += 1
                bi = rng.integers(0, len(ga), (B, len(ga)))
                for m in reps:
                    d = (ga[m] - gb.loc[ga.index, m]).values; reps[m].append(d[bi].mean(1)); pts.setdefault(m, []).append(d.mean())
            r = dict(split_type=sp, n=n, contrast=lab, a=a, b=b, n_benchmarks=nb)
            for m in reps:
                v = np.mean(reps[m], 0); r[m + "_diff"] = np.mean(pts[m]); r[m + "_diff_lo"], r[m + "_diff_hi"] = np.percentile(v, [2.5, 97.5])
            rows.append(r)
pd.DataFrame(rows).to_csv(sys.argv[2], index=False)
