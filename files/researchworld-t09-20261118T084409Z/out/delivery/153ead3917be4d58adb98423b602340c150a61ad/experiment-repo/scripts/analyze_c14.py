"""C7 / review M4: graph cluster randomisation crossed with the design-based estimators.  python scripts/analyze_c14.py   (needs results/raw/e13.parquet)
Grid e13 replays the draws of e5 (same graphs, frozen heterogeneity, Louvain partitions, assignments and noise) and adds the relaxed-exposure Hajek
estimators with their exact cluster-design propensities, delta in {0.1, 0.25, 0.5}.  Estimators per (graph, response, cluster scale): REG-L, REG-Q, REG-O,
DM, HAJEK (exact exposure: own cluster-closed neighbourhood all in one arm), HT, HAJEK-r(delta).
Oracle choices, all granted to every competitor: the cluster scale (Louvain resolution) is picked in hindsight for each estimator separately (ER 0.7 is one
giant cluster and excluded), and for the relaxed Hajek the best of the three delta is also picked in hindsight, so the table favours the design-based side.
Writes results/summary/c14_cells.csv (every estimator x cell: RMSE and 95% bootstrap CI) and c14_best.csv (per graph x response: the best-scale
RMSE of each estimator, the best design-based competitor, the ratio REG-L / competitor with a bootstrap CI)."""
import numpy as np
import pandas as pd

d = pd.read_parquet("results/raw/e13.parquet")
g = d["graph.kind"].str.upper()
d["graph"] = np.where(d["graph.kind"] == "sbm", "SBM mu=" + d["graph.kw.mu"].astype(str), np.where(d["graph.kind"] == "ws", "WS", g))
d["resp"] = np.where(d["out.kappa"] == 0, "linear", np.where(d["out.w2"] > 0, "2-hop convex", np.where(d["out.shape"] == "thresh", "threshold", "convex")))
d["res"] = d["design.res"].where(d["design.kind"] == "gcr", np.nan)
EST = ["DM", "HAJEK", "HAJEK-r0.1", "HAJEK-r0.25", "HAJEK-r0.5", "HT", "REG-L", "REG-Q", "REG-O"]
DESIGN = ["DM", "HAJEK", "HAJEK-r0.1", "HAJEK-r0.25", "HAJEK-r0.5"]
SCALE = 2.0                                   # |beta| + |gamma|
rng = np.random.default_rng(0)
B = 1000


def err(x):
    return (x[0].to_numpy(float) - x[1].to_numpy(float))


def boot(e):
    e = e[~np.isnan(e)]
    i = rng.integers(0, len(e), (B, len(e)))
    return np.sqrt(np.mean(e[i] ** 2, axis=1))


cells, boots = [], {}
for key, c in d.groupby(["graph", "resp", "design.kind", "res"], dropna=False):
    for est in EST:
        e = c[est].to_numpy(float) - c["tau"].to_numpy(float)
        b = boot(e)
        boots[key + (est,)] = b
        ok = ~np.isnan(e)
        cells.append(dict(graph=key[0], resp=key[1], design=key[2], res=key[3], est=est, n=int(ok.sum()), bias=float(e[ok].mean()) / SCALE,
                          rmse=float(np.sqrt(np.mean(e[ok] ** 2))) / SCALE, lo=float(np.quantile(b, .025)) / SCALE, hi=float(np.quantile(b, .975)) / SCALE))
cl = pd.DataFrame(cells)
cl.to_csv("results/summary/c14_cells.csv", index=False)

rows = []
for (gr, rp), c in cl.groupby(["graph", "resp"]):
    gc = c[(c.design == "gcr") & ~((gr == "ER") & (c.res == 0.7))]
    bern = c[c.design == "bern"].set_index("est")
    row = dict(graph=gr, resp=rp)
    best = {}
    for est in EST:
        x = gc[gc.est == est].sort_values("rmse").iloc[0]
        best[est] = (x.res, x.rmse)
        row[f"{est}_gcr"], row[f"{est}_res"], row[f"{est}_bern"] = x.rmse, x.res, bern.loc[est, "rmse"]
    dsg = min(DESIGN, key=lambda e: best[e][1])
    row["design_best"], row["design_best_rmse"], row["design_best_res"] = dsg, best[dsg][1], best[dsg][0]
    bern_dsg = min(DESIGN, key=lambda e: bern.loc[e, "rmse"])
    row["design_best_bern"], row["design_best_bern_rmse"] = bern_dsg, bern.loc[bern_dsg, "rmse"]
    k1 = (gr, rp, "gcr", best["REG-L"][0], "REG-L"); k2 = (gr, rp, "gcr", best[dsg][0], dsg)
    ratio = boots[k1] / boots[k2]
    row["ratio_regL_over_design"] = best["REG-L"][1] / best[dsg][1]
    row["ratio_lo"], row["ratio_hi"] = float(np.quantile(ratio, .025)), float(np.quantile(ratio, .975))
    rows.append(row)
bst = pd.DataFrame(rows)
bst.to_csv("results/summary/c14_best.csv", index=False)
pd.set_option("display.width", 250); pd.set_option("display.max_columns", 40); pd.set_option("display.max_rows", 100)
print(bst[["graph", "resp", "REG-L_bern", "REG-L_gcr", "REG-L_res", "design_best_bern", "design_best_bern_rmse", "design_best", "design_best_rmse", "design_best_res",
           "ratio_regL_over_design", "ratio_lo", "ratio_hi"]].round(3).to_string())
r = bst.ratio_regL_over_design
print("REG-L (own best scale) vs best design-based (own best scale and delta): REG-L better in", int((bst.ratio_hi < 1).sum()), "of", len(bst), "(CI excludes 1);",
      "tie in", int(((bst.ratio_lo <= 1) & (bst.ratio_hi >= 1)).sum()), "; design-based better in", int((bst.ratio_lo > 1).sum()))
print("ratio median", r.median(), "min", r.min(), "max", r.max())
print(bst[bst.ratio_lo > 1][["graph", "resp", "ratio_regL_over_design", "design_best"]])
