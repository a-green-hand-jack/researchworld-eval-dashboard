"""A3: pairwise mis-ranking. For every pair of scores in a configuration, how often does the estimated worst-cell ordering
(from a finite test set) differ from the true ordering, as a function of the true gap?
Units: (config, stratification, n_te, score pair, replication or replication block).
 scheme 'rep'      : one replication; estimated gap vs the TRUE gap of that same replication (grid truth), binned by |true gap|
 scheme 'rep_pop'  : one replication; estimated gap vs sign of the population gap (mean over all replications of the config), binned by |population gap|
 scheme 'blockR'   : average of R replications (disjoint blocks); est gap of the block mean vs the true gap of the block mean (R = 25, 100)
Estimated ties count as half a flip. Inputs: A1_* (100-200 reps, 15 scores) and A3hs_* (1000 reps, 15 scores).
Outputs: results/tables/A3_flip_pairs.csv (one row per config, strat, n_te, scheme, pair),
         results/tables/A3_flip_bins.csv (pooled by gap bin; CI = bootstrap over configs, 2000 draws), A3_flip_threshold.csv."""
import glob, itertools
import numpy as np, pandas as pd

NN = (500, 2000, 10000)
STRATA = ("x0_10", "bd_10")
BINS = [0, 0.005, 0.01, 0.02, 0.03, 0.05, 0.1, 0.2, 1.0]
rng = np.random.default_rng(7)
rows = []        # per pair summary
obs = []         # long records for the binned table: config, group, strat, n_te, scheme, gap, flip
files = sorted(glob.glob("results/raw/A1_*.csv*")) + sorted(glob.glob("results/raw/A3hs_*.csv*"))
for f in files:
    d = pd.read_csv(f)
    cfg = d.config.iloc[0]
    grp = "A1" if cfg.startswith("A1_") else "A3hs"
    meths = list(d.method.unique()); seeds = np.sort(d.seed.unique()); nrep = len(seeds)
    pairs = list(itertools.combinations(range(len(meths)), 2))
    I, J = np.array([p[0] for p in pairs]), np.array([p[1] for p in pairs])
    for st in STRATA:
        T = d.pivot(index="seed", columns="method", values=f"true_{st}_min").loc[seeds, meths].values
        for nn in NN:
            E = d.pivot(index="seed", columns="method", values=f"est_{st}_min_{nn}").loc[seeds, meths].values
            dT, dE = T[:, I] - T[:, J], E[:, I] - E[:, J]              # (rep, pair)
            flip = lambda dt, de: (np.sign(dt) != np.sign(de)).astype(float) * np.where(de == 0, 0, 1) + 0.5 * (de == 0)
            pop = dT.mean(0)
            schemes = {"rep": (np.abs(dT), flip(dT, dE)), "rep_pop": (np.abs(pop)[None, :].repeat(nrep, 0), flip(pop[None, :], dE))}
            for R in (25, 100):
                nb = nrep // R
                if nb < 2:
                    continue
                bT = dT[:nb * R].reshape(nb, R, -1).mean(1); bE = dE[:nb * R].reshape(nb, R, -1).mean(1)
                schemes[f"block{R}"] = (np.abs(bT), flip(bT, bE))
            for sc, (gap, fl) in schemes.items():
                for k in range(len(pairs)):
                    rows.append(dict(config=cfg, group=grp, strat=st, n_te=nn, scheme=sc, a=meths[I[k]], b=meths[J[k]],
                                     gap=gap[:, k].mean(), p_flip=fl[:, k].mean(), n_units=len(fl)))
                bi = np.digitize(gap.ravel(), BINS[1:-1])                       # bin index 0..len(BINS)-2 (right=False edges)
                cnt = np.bincount(bi, minlength=len(BINS) - 1); sm = np.bincount(bi, weights=fl.ravel(), minlength=len(BINS) - 1)
                for k in range(len(BINS) - 1):
                    if cnt[k]:
                        obs.append(dict(config=cfg, group=grp, strat=st, n_te=nn, scheme=sc, bin=k, flip_sum=sm[k], count=cnt[k]))
pd.DataFrame(rows).to_csv("results/tables/A3_flip_pairs.csv", index=False)
O = pd.DataFrame(obs)
out = []
for (grp, st, nn, sc), g in O.groupby(["group", "strat", "n_te", "scheme"]):
    cfgs = g.config.unique()
    S = g.pivot_table(index="config", columns="bin", values="flip_sum", aggfunc="sum").reindex(columns=range(len(BINS) - 1)).fillna(0).values
    C = g.pivot_table(index="config", columns="bin", values="count", aggfunc="sum").reindex(columns=range(len(BINS) - 1)).fillna(0).values
    pt = S.sum(0) / np.maximum(C.sum(0), 1)
    bs = np.empty((2000, S.shape[1]))
    for b in range(2000):
        ii = rng.integers(0, len(cfgs), len(cfgs))
        bs[b] = S[ii].sum(0) / np.where(C[ii].sum(0) > 0, C[ii].sum(0), np.nan)
    lo, hi = np.nanquantile(bs, .025, axis=0), np.nanquantile(bs, .975, axis=0)
    for k in range(S.shape[1]):
        if C[:, k].sum() > 0:
            out.append(dict(group=grp, strat=st, n_te=nn, scheme=sc, gap_lo=BINS[k], gap_hi=BINS[k + 1], n_obs=int(C[:, k].sum()),
                            n_configs=int((C[:, k] > 0).sum()), p_flip=pt[k], ci_lo=lo[k], ci_hi=hi[k]))
B = pd.DataFrame(out); B.to_csv("results/tables/A3_flip_bins.csv", index=False)
# threshold: smallest gap-bin lower edge from which all larger bins have upper CI bound < level (0.05, 0.10) and flip prob < level
th = []
for (grp, st, nn, sc), g in B.groupby(["group", "strat", "n_te", "scheme"]):
    g = g.sort_values("gap_lo")
    for lev in (0.05, 0.10, 0.25):
        ok = (g.p_flip < lev).values
        t = np.nan
        for k in range(len(g)):
            if ok[k:].all() and g.n_obs.values[k:].min() >= 30:
                t = g.gap_lo.values[k]; break
        th.append(dict(group=grp, strat=st, n_te=nn, scheme=sc, level=lev, gap_threshold=t))
pd.DataFrame(th).to_csv("results/tables/A3_flip_threshold.csv", index=False)
pd.set_option("display.width", 250)
print(B[(B.strat == "x0_10") & (B.scheme.isin(["rep", "block25"]))].pivot_table(index=["group", "scheme", "n_te"], columns="gap_lo", values="p_flip").round(3).to_string())
print(pd.DataFrame(th).pivot_table(index=["group", "strat", "scheme", "n_te"], columns="level", values="gap_threshold").round(3).to_string())
