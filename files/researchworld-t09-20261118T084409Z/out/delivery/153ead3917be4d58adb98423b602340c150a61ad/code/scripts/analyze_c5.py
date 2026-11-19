"""C5: mechanism x method map (grid e6; Bernoulli p = 0.5, n_eff = 2000 (ER, SBM, BA, WS) or the thinned real graphs, sigma_idio = 0.5, R = 100).
Reads results/raw/e6.parquet and results/summary/e6.csv; writes
  c5_table1.csv  per estimator x mechanism: median and worst over the six graphs of the normalised RMSE (RMSE / (|beta|+|gamma|) = RMSE/2),
                 with the cell's bootstrap CI (median: median of the cell CI ends; worst: the CI of the worst graph), the squared-bias share, graphs run
  c5_cells.csv   the full grid (graph x mechanism x estimator): normalised RMSE with CI, normalised bias, normalised sd
  c5_flex.csv    flexible / alternative estimator vs REG-L on the same draws: paired-bootstrap CI of the RMSE difference (win/tie/loss for the alternative)
  c5_best.csv    per (graph, mechanism): the best non-oracle estimator, REG-L's rank and its ratio to the best, REG-L vs DM
'Non-oracle' excludes REG-O (true functional form known); HT-exact is the exact design sd of the full-exposure HT (no draw is needed)."""
import numpy as np
import pandas as pd

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from netgate.summ import cell_cols  # noqa: E402

B = 500
rng = np.random.default_rng(0)
raw = pd.read_parquet("results/raw/e6.parquet")
s = pd.read_csv("results/summary/e6.csv")


def mech(r):
    if r["out.kind"] == "count":
        return "count"
    k, sh = r["out.kappa"], r["out.shape"]
    if r["out.w2"] == 0.5:
        return "linear-2hop" if k == 0 else "convex-2hop"
    if not np.isnan(r["out.het_beta"]):
        return "het-direct"
    if not np.isnan(r["out.het_gamma"]):
        return "het-indirect"
    if k == 0:
        return "linear"
    return f"thresh{r['out.theta']:.1f}" if sh == "thresh" else sh


s["mech"] = s.apply(mech, axis=1)
raw["mech"] = raw.apply(mech, axis=1)
s["graph"] = s["graph.kind"]
raw["graph"] = raw["graph.kind"]
he = s.est == "HT-exact"      # summarize.py leaves the normalised columns empty for the exact-variance row
for c in ("rmse", "rmse_lo", "rmse_hi"):
    s.loc[he, c + "_norm" if c == "rmse" else c.replace("rmse", "rmse_norm")] = s.loc[he, c] / s.loc[he, "scale"]
s.loc[he, "bias_norm"], s.loc[he, "bias_norm_se"] = 0.0, np.nan
s.loc[he, "n_nan"] = 0
s["sd_norm"] = s.sd / s.scale
s["bias2_share"] = np.where(s.rmse > 0, (s.bias ** 2) / (s.rmse ** 2), np.nan)
s.loc[s.est == "HT-exact", "bias2_share"] = 0.0
EST = ["DM", "HT-exact", "HAJEK", "HAJEK-r0.25", "REG-L", "REG-Lc", "REG-Q", "REG-G", "REG-GBM", "REG-GCN", "REG-O"]
s = s[s.est.isin(EST) & ~((s.n_nan == s.n_rep) & s.est.ne("HT-exact"))]   # GCN was not run on Stanford3 (n = 10 481): rows with every replicate NaN are dropped
s[["graph", "mech", "est", "n", "n_nan", "rmse_norm", "rmse_norm_lo", "rmse_norm_hi", "bias_norm", "bias_norm_se", "sd_norm", "bias2_share"]] \
    .to_csv("results/summary/c5_cells.csv", index=False)

rows = []
for (est, mc), g in s.groupby(["est", "mech"]):
    w = g.loc[g.rmse_norm.idxmax()]
    rows.append(dict(est=est, mech=mc, n_graphs=len(g), median=g.rmse_norm.median(), median_lo=g.rmse_norm_lo.median(),
                     median_hi=g.rmse_norm_hi.median(), worst=w.rmse_norm, worst_lo=w.rmse_norm_lo, worst_hi=w.rmse_norm_hi,
                     worst_graph=w.graph, bias2_share_median=g.bias2_share.median()))
t1 = pd.DataFrame(rows)
t1.to_csv("results/summary/c5_table1.csv", index=False)

# paired comparison against REG-L on the same draws
ALT = ["REG-Q", "REG-G", "REG-GBM", "REG-GCN", "HAJEK-r0.25", "REG-Lc", "REG-O", "DM"]
rows = []
for (gr, mc), g in raw.groupby(["graph", "mech"]):
    eL = (g["REG-L"] - g.tau).to_numpy()
    idx = rng.integers(0, len(g), (B, len(g)))
    rL = np.sqrt((eL[idx] ** 2).mean(1))
    for a in ALT:
        e = (g[a] - g.tau).to_numpy()
        if np.isnan(e).all():
            continue
        ok = ~np.isnan(e)
        ii = idx if ok.all() else rng.integers(0, ok.sum(), (B, ok.sum()))
        ra = np.sqrt((e[ok][ii] ** 2).mean(1)) if not ok.all() else np.sqrt((e[idx] ** 2).mean(1))
        rl = rL if ok.all() else np.sqrt((eL[ok][ii] ** 2).mean(1))
        diff = (ra - rl) / 2.0       # alt - REG-L in outcome-scale units
        lo, hi = np.quantile(diff, [0.025, 0.975])
        rows.append(dict(graph=gr, mech=mc, alt=a, rmse_regL_norm=float(np.sqrt((eL[ok] ** 2).mean()) / 2), rmse_alt_norm=float(np.sqrt((e[ok] ** 2).mean()) / 2),
                         diff_lo=lo, diff_hi=hi, outcome="alt wins" if hi < 0 else ("alt loses" if lo > 0 else "tie")))
fx = pd.DataFrame(rows)
fx.to_csv("results/summary/c5_flex.csv", index=False)

# best non-oracle estimator per cell
NONOR = [e for e in EST if e != "REG-O"]
rows = []
for (gr, mc), g in s.groupby(["graph", "mech"]):
    g = g[g.est.isin(NONOR)].set_index("est").rmse_norm
    best = g.idxmin()
    rows.append(dict(graph=gr, mech=mc, best=best, best_rmse=g.min(), regL=g["REG-L"], regL_rank=int(g.rank()["REG-L"]), ratio_to_best=g["REG-L"] / g.min(),
                     dm=g["DM"], regL_worse_than_dm=bool(g["REG-L"] > g["DM"])))
bt = pd.DataFrame(rows)
bt.to_csv("results/summary/c5_best.csv", index=False)

pd.set_option("display.width", 250); pd.set_option("display.max_columns", 30); pd.set_option("display.max_rows", 200)
print("median over graphs of normalised RMSE")
print(t1.pivot(index="mech", columns="est", values="median")[EST].round(3))
print("worst over graphs")
print(t1.pivot(index="mech", columns="est", values="worst")[EST].round(3))
print("worst graph for REG-L"); print(t1[t1.est == "REG-L"].set_index("mech")[["worst", "worst_graph"]].round(3))
print("paired vs REG-L (alt wins / tie / alt loses over 60 cells)")
print(fx.groupby(["alt", "outcome"]).size().unstack(fill_value=0))
print(fx.groupby(["alt", "mech", "outcome"]).size().unstack(fill_value=0).loc[["REG-Q", "REG-G", "REG-GBM", "REG-GCN", "HAJEK-r0.25"]])
print("best non-oracle by mechanism"); print(bt.groupby(["mech", "best"]).size().unstack(fill_value=0))
print("REG-L ratio to best: median", bt.ratio_to_best.median(), " share <= 1.25:", (bt.ratio_to_best <= 1.25).mean(), " worse than DM:", int(bt.regL_worse_than_dm.sum()), "of", len(bt))
