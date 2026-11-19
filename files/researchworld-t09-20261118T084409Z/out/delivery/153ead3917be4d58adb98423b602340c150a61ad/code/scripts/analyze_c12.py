"""C6 / D4 (degree transport; PREREG.md addendum): evaluation on grid e12.  python3 scripts/analyze_c12.py
Reads results/raw/e12.parquet; writes results/summary/c12_cells.csv, c12_rank.csv, c12_flag.csv, c12_estimator.csv, c12_by_graph.csv.
Groups: graph class = heterogeneous (ba, stanford3, egofb) / control (er); response group = no degree dependence (concave, convex, thresh)
/ stress (het-gamma concave, het-gamma convex, count).  Positive = |bias| > 0.10 (|beta|+|gamma|) (cells with |bias| <= 2 MC-SE excluded from flag/AUC);
flag rule for D1, D2, D4 = score > 0.10 max(|tau_hat|, sd(y)), a cell flagged if the majority of its replicates is.
Bootstrap: 95% percentile, 2000 draws over cells, seed 20261119 (the same as analyze_c6.py)."""
import numpy as np
import pandas as pd
from scipy.stats import spearmanr
from sklearn.metrics import roc_auc_score

BOOT, SEED = 2000, 20261119
raw = pd.read_parquet("results/raw/e12.parquet")
CELL = ["graph.kind", "graph.n", "graph.d", "graph.q", "out.kind", "out.kappa", "out.shape", "out.het_gamma", "design.p"]


def mech(r):
    if r["out.kind"] == "count":
        return "count"
    het = r["out.het_gamma"] > 0
    return f"{r['out.shape']}+het-gamma" if het else r["out.shape"]


raw["_c"] = raw.groupby(CELL, dropna=False).ngroup()
raw["mech"] = raw.apply(mech, axis=1)
raw["gclass"] = np.where(raw["graph.kind"] == "er", "control (ER)", "heterogeneous (BA, Stanford3, ego-Facebook)")
raw["rgroup"] = np.where(raw.mech.isin(["concave", "convex", "thresh"]), "no degree dependence", "stress (degree-dependent)")
raw["Zcorner"] = np.sqrt(raw["d_mean"] * (1 - raw["p_obs"]) / raw["p_obs"])
raw["thr"] = 0.10 * np.maximum(raw["REG-L"].abs(), raw["sd_y"])
raw["err_L"] = raw["REG-L"] - raw["tau"]
raw["err_D4"] = raw["d4_tau"] - raw["tau"]
SCORES = {"D4 degree transport": "d4", "D1 extrapolation": "d1", "D1 (REG-Q audited)": "d1q", "D2 family spread": "d2",
          "D3 curvature bound B": "d3_B", "leverage iid-SE (baseline a)": "REG-L_se_iid", "corner distance Z (baseline b)": "Zcorner"}
g = raw.groupby("_c")
cells = g[["mech", "gclass", "rgroup"] + CELL].first()
cells = cells.join(g[list(SCORES.values()) + ["d4_gmax", "d4_nref", "gscale"]].median())
cells["n_rep"] = g.size()
cells["d4_defined"] = g["d4"].apply(lambda x: x.notna().mean())
cells["bias_L"] = g["err_L"].mean(); cells["bias_L_se"] = g["err_L"].std() / np.sqrt(g.size())
cells["bias_D4"] = g["err_D4"].mean(); cells["bias_D4_se"] = g["err_D4"].std() / np.sqrt(g["err_D4"].count())
cells["rmse_L"] = g["err_L"].apply(lambda x: np.sqrt((x ** 2).mean())); cells["rmse_D4"] = g["err_D4"].apply(lambda x: np.sqrt((x ** 2).mean()))
cells["sd_D4"] = g["err_D4"].std(); cells["sd_L"] = g["err_L"].std()
cells["abs_bias"] = cells.bias_L.abs()
cells["positive"] = cells.abs_bias > 0.10 * cells.gscale
cells["resolved"] = cells.abs_bias > 2 * cells.bias_L_se
cells["flag_D1"] = (raw["d1"] > raw["thr"]).groupby(raw._c).mean() > 0.5
cells["flag_D2"] = (raw["d2"] > raw["thr"]).groupby(raw._c).mean() > 0.5
cells["flag_D4"] = (raw["d4"] > raw["thr"]).groupby(raw._c).mean() > 0.5
cells.reset_index().to_csv("results/summary/c12_cells.csv", index=False)


def boot_idx(n):
    return np.random.default_rng(SEED).integers(0, n, size=(BOOT, n))


def ci_mean(x):
    x = np.asarray(x, float); x = x[~np.isnan(x)]
    if len(x) == 0:
        return np.nan, np.nan
    m = x[boot_idx(len(x))].mean(axis=1)
    return float(np.percentile(m, 2.5)), float(np.percentile(m, 97.5))


def ci_spearman(a, b):
    a = np.asarray(a, float); b = np.asarray(b, float)
    r = [spearmanr(a[i], b[i])[0] for i in boot_idx(len(a)) if np.ptp(a[i]) > 0 and np.ptp(b[i]) > 0]
    return float(np.percentile(r, 2.5)), float(np.percentile(r, 97.5))


SUBS = [("all", cells.index == cells.index)]
for gc in sorted(cells.gclass.unique()):
    SUBS.append((gc, cells.gclass == gc))
for gc in sorted(cells.gclass.unique()):
    for rg in sorted(cells.rgroup.unique()):
        SUBS.append((f"{gc} | {rg}", (cells.gclass == gc) & (cells.rgroup == rg)))
SUBS += [(rg, cells.rgroup == rg) for rg in sorted(cells.rgroup.unique())]

# ---- rank correlation with |bias| over cells
rows = []
for name, col in SCORES.items():
    for sub, m in SUBS:
        c = cells[m & cells[col].notna()]
        if len(c) < 5:
            continue
        lo, hi = ci_spearman(c[col], c.abs_bias)
        rows.append(dict(score=name, subset=sub, n=len(c), spearman=spearmanr(c[col], c.abs_bias)[0], spearman_lo=lo, spearman_hi=hi))
rk = pd.DataFrame(rows)
rk.to_csv("results/summary/c12_rank.csv", index=False)

# ---- flag performance
rows = []
ev_all = cells[cells.resolved]
for sub, m in SUBS:
    ev = ev_all[m[ev_all.index]]
    for name, col in SCORES.items():
        e = ev[ev[col].notna()]
        ok = 0 < e.positive.sum() < len(e)
        r = dict(subset=sub, score=name, n_cells=len(e), n_pos=int(e.positive.sum()), auc=roc_auc_score(e.positive, e[col]) if ok else np.nan)
        fl = {"d4": "flag_D4", "d1": "flag_D1", "d2": "flag_D2"}.get(col)
        if fl:
            f = e[fl]
            tp, fp, fn = int((f & e.positive).sum()), int((f & ~e.positive).sum()), int((~f & e.positive).sum())
            r.update(rule="pre-registered 0.10*max(|tau_hat|,sd_y)", tp=tp, fp=fp, fn=fn, precision=tp / max(tp + fp, 1), recall=tp / max(tp + fn, 1))
        rows.append(r)
fl = pd.DataFrame(rows)
fl.to_csv("results/summary/c12_flag.csv", index=False)

# ---- D4 as an estimator against REG-L (paired by cell)
rows = []
for sub, m in SUBS:
    c = cells[m & cells.bias_D4.notna()]
    if len(c) < 2:
        continue
    r = dict(subset=sub, n_cells=len(c))
    for nm, f in [("mean |bias| REG-L", c.bias_L.abs()), ("mean |bias| D4", c.bias_D4.abs()), ("mean RMSE REG-L", c.rmse_L), ("mean RMSE D4", c.rmse_D4),
                  ("mean sd REG-L", c.sd_L), ("mean sd D4", c.sd_D4), ("share cells |bias| D4 < REG-L", (c.bias_D4.abs() < c.bias_L.abs()).astype(float)),
                  ("share cells RMSE D4 < REG-L", (c.rmse_D4 < c.rmse_L).astype(float))]:
        r[nm] = float(f.mean()); r[nm + " lo"], r[nm + " hi"] = ci_mean(f)
    rows.append(r)
es = pd.DataFrame(rows)
es.to_csv("results/summary/c12_estimator.csv", index=False)
pd.set_option("display.width", 250, "display.max_columns", 40, "display.max_rows", 300)
print(cells.mech.value_counts().to_dict(), "cells", len(cells), "D4 defined share", cells.d4_defined.mean())
print(rk.round(2).to_string()); print(fl.round(2).to_string()); print(es.round(3).T.to_string())

# ---- by graph family x response group: D4 as an estimator against REG-L (medians over cells; bias is signed, tau_hat - tau)
rows = []
for (k, rg), c in cells.groupby(["graph.kind", "rgroup"]):
    rows.append(dict(graph=k, rgroup=rg, n_cells=len(c), median_abs_bias_L=c.bias_L.abs().median(), median_abs_bias_D4=c.bias_D4.abs().median(),
                     median_signed_bias_D4=c.bias_D4.median(), median_sd_L=c.sd_L.median(), median_sd_D4=c.sd_D4.median(),
                     median_rmse_L=c.rmse_L.median(), median_rmse_D4=c.rmse_D4.median(), median_d4_gmax=c.d4_gmax.median(),
                     share_rmse_D4_lt_L=float((c.rmse_D4 < c.rmse_L).mean())))
pd.DataFrame(rows).to_csv("results/summary/c12_by_graph.csv", index=False)
print(pd.DataFrame(rows).round(3).to_string())
