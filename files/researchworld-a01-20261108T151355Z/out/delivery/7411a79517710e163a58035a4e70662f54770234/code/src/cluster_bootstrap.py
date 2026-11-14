"""Cluster bootstrap for the OLLB comparisons whose targets are not independent: fine-tunes of one base model score alike.
Cluster key = the leaderboard's `Base Model` entry; a model with no usable entry (placeholder strings 'Removed', '(Merge)', '[...]' or empty) is its own cluster
(`mti.data.base_clusters`). Clusters are resampled with replacement (B=1000, seed 0), all targets of a drawn cluster enter the replicate.
Statistics (ceil cap, ranks >= 2): C2 median ratio L1(min)/L1(mean) -- all targets and by terciles of the CV fixed on the full sample -- and its share min<mean;
C4 R^2 of log L1 on log rank vs log gap and their difference, per rule. The iid columns repeat the target-level percentile bootstrap (same B, same statistic) for comparison.
HELM has no clusters (79 independently developed API models; no `Base Model`-like field), so its intervals stay target-level (summary/c2_min_vs_mean.csv, c4_rank_vs_gap.csv).
Writes results/summary/cluster_bootstrap_ollb.csv and cluster_sizes_ollb.csv.  Usage: python3 src/cluster_bootstrap.py"""
import sys, pathlib, numpy as np, pandas as pd
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from mti import data as dt
import analyze as an
R = an.R; OUT = an.OUT; B = 1000
rng = np.random.default_rng(0)

def cluster_ids(names):
    key = dt.base_clusters(names)
    codes, uniq = pd.factorize(pd.Series(key)); return codes, len(uniq)

def draw_clusters(codes, ncl, rows_of_cluster):
    """one replicate: row indices (into the array that `codes` indexes) of the targets of ncl clusters drawn with replacement"""
    pick = rng.integers(0, ncl, ncl); return np.concatenate([rows_of_cluster[c] for c in pick])

def boot(df, stat, codes_by_target, ncl, nrep=B):
    """percentile CIs of stat(df rows) under target-level (iid) and cluster resampling"""
    codes = df.target.map(codes_by_target).values; order = np.argsort(codes, kind="stable"); sc = codes[order]
    cuts = np.flatnonzero(np.diff(sc)) + 1; groups = np.split(order, cuts); uniq = sc[np.r_[0, cuts]]
    gmap = dict(zip(uniq, groups)); rows_of = [gmap[c] for c in uniq]; k = len(rows_of)
    iid, cl = [], []
    for _ in range(nrep):
        iid.append(stat(df.iloc[rng.integers(0, len(df), len(df))]))
        pick = rng.integers(0, k, k); cl.append(stat(df.iloc[np.concatenate([rows_of[c] for c in pick])]))
    f = lambda v: np.nanpercentile(v, [2.5, 97.5])
    return stat(df), f(iid), f(cl), k

if __name__ == "__main__":
    X, names, tasks, meta = dt.load("ollb")
    codes, ncl = cluster_ids(names); cl_of = dict(zip(names, codes))
    sizes = pd.Series(codes).value_counts()
    pd.DataFrame(dict(n_models=len(names), n_clusters=ncl, singleton_clusters=int((sizes == 1).sum()), largest_cluster=int(sizes.max()), mean_cluster_size=float(sizes.mean()),
                      share_models_in_clusters_ge2=float((sizes[sizes >= 2].sum()) / len(names))), index=[0]).to_csv(OUT / "cluster_sizes_ollb.csv", index=False)
    d = pd.read_csv(R / "ollb_score.csv"); d = d[(d.cap == "ceil") & (d.rank_mean >= 2)]
    cv = dict(zip(names, X.std(axis=1) / X.mean(axis=1)))
    rows = []
    # C2
    s = d[d.rule.isin(["mean", "min"]) & d.feasible].pivot_table(index=["target", "rank_mean"], columns="rule", values="L1", aggfunc="first").dropna().reset_index()
    s = s[s["mean"] > 0].copy(); s["ratio"] = s["min"] / s["mean"]; s["cv"] = s.target.map(cv)
    s["terc"] = pd.qcut(s.cv.rank(method="first"), 3, labels=["low", "mid", "high"]).astype(str)
    for terc in ("all", "low", "mid", "high"):
        g = s if terc == "all" else s[s.terc == terc]
        for nm, fn in (("C2 median L1(min)/L1(mean)", lambda x: float(np.median(x.ratio))), ("C2 share min cheaper than mean", lambda x: float((x.ratio < 1).mean()))):
            est, iid, clb, k = boot(g.reset_index(drop=True), fn, cl_of, ncl)
            rows.append(dict(claim="C2", statistic=nm, subset=f"CV tercile {terc}", n_targets=len(g), n_clusters=k, estimate=est, iid_lo=iid[0], iid_hi=iid[1], cluster_lo=clb[0], cluster_hi=clb[1]))
    # C4: R^2 of log L1 on log rank vs log gap
    r2 = lambda x, y: np.corrcoef(x, y)[0, 1] ** 2
    parts = [(d, "score")] + [(pd.read_csv(R / "ollb_ord_ceil.csv").query("rank_mean >= 2"), "ordinal sample")]
    for dd, src in parts:
        for (cap, rule), g in dd.groupby(["cap", "rule"]):
            if rule in ("borda", "plurality", "condorcet"): g = g.assign(gap=an.ordinal_gap("ollb", rule, g))
            g = g[g.feasible & (g.L1 > 0) & (g.gap > 0)].reset_index(drop=True)
            if rule == "mean" or len(g) < 10 or g.rank_rule.nunique() < 5: continue
            lr, lg, ly = np.log(g.rank_rule.values.astype(float)), np.log(g.gap.values), np.log(g.L1.values)
            g = g.assign(lr=lr, lg=lg, ly=ly)
            for nm, fn in (("C4 R2 rank", lambda x: r2(x.lr.values, x.ly.values)), ("C4 R2 gap", lambda x: r2(x.lg.values, x.ly.values)),
                           ("C4 R2 gap - R2 rank", lambda x: r2(x.lg.values, x.ly.values) - r2(x.lr.values, x.ly.values))):
                est, iid, clb, k = boot(g, fn, cl_of, ncl)
                rows.append(dict(claim="C4", statistic=f"{nm} ({rule})", subset=f"{src}, ceil", n_targets=len(g), n_clusters=k, estimate=est, iid_lo=iid[0], iid_hi=iid[1], cluster_lo=clb[0], cluster_hi=clb[1]))
    out = pd.DataFrame(rows); out.to_csv(OUT / "cluster_bootstrap_ollb.csv", index=False); print(out.round(3).to_string())
