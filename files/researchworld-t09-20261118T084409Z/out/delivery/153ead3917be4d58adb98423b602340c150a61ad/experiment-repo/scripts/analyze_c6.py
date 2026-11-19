"""C6 evaluation of the pre-registered diagnostic and bias-aware interval (PREREG.md) on grid e7.
python3 scripts/analyze_c6.py -> results/summary/c6_rank.csv (spearman_lo/hi), c6_flag.csv, c6_cover.csv, c6_cover_cells.csv
Thresholds and definitions are those of PREREG.md; nothing here is tuned on e7 except the oracle baseline thresholds
(which PREREG.md grants to the baselines)."""
import numpy as np
import pandas as pd
from scipy.stats import spearmanr
from sklearn.metrics import roc_auc_score

raw = pd.read_parquet("results/raw/e7.parquet")
summ = pd.read_csv("results/summary/e7.csv")
summ = summ[summ.est == "REG-L"].reset_index(drop=True)
CELL = ["graph.kind", "graph.n", "graph.d", "out.kind", "out.kappa", "out.shape", "out.w2", "out.sigma", "out.sigma_alpha",
        "out.gamma", "design.kind", "design.p"]


def mech(r):
    if r["out.kind"] == "count":
        return "count"
    if r["out.shape"] == "thresh":
        return "thresh"
    if r["out.shape"] == "concave":
        return "concave"
    if r["out.shape"] == "convex":
        return "convex-2hop" if r["out.w2"] == 0.5 else "convex"
    return "linear"


summ["mech"] = summ.apply(mech, axis=1)
raw["_c"] = raw.groupby(CELL, dropna=False).ngroup()
keys = raw.groupby(CELL, dropna=False).ngroup().unique()
# align cells of raw and summary by merge on CELL columns
cid = raw.groupby("_c")[CELL].first().reset_index()
cid = cid.merge(summ[CELL + ["mech", "bias", "bias_se", "scale", "sd", "d_mean"]], on=CELL, how="left")
assert cid.bias.notna().all() and len(cid) == len(summ)
raw = raw.merge(cid[["_c", "mech", "bias", "bias_se", "scale", "sd"]], on="_c")
raw["abs_err"] = (raw["REG-L"] - raw["tau"]).abs()
raw["p_hat"] = raw["p_obs"]
raw["Zcorner"] = np.sqrt(raw["d_mean"] * (1 - raw["p_hat"]) / raw["p_hat"])
raw["thr"] = 0.10 * np.maximum(raw["REG-L"].abs(), raw["sd_y"])

# 95% percentile bootstrap over cells (cells are the resampling unit), BOOT draws, seed SEED; used for every *_lo / *_hi column below
BOOT, SEED = 2000, 20261119
CLASS = {"linear": "inside curvature-rule class", "concave": "inside curvature-rule class", "convex": "inside curvature-rule class",
         "thresh": "violating the curvature rule", "convex-2hop": "violating the curvature rule", "count": "count (own class)"}


def boot_idx(n, rng):
    return rng.integers(0, n, size=(BOOT, n))


def boot_mean_ci(x):
    x = np.asarray(x, float); x = x[~np.isnan(x)]
    m = x[boot_idx(len(x), np.random.default_rng(SEED))].mean(axis=1)
    return np.percentile(m, 2.5), np.percentile(m, 97.5)


def boot_spearman_ci(a, b):
    a = np.asarray(a, float); b = np.asarray(b, float)
    ix = boot_idx(len(a), np.random.default_rng(SEED))
    r = []
    for i in ix:
        if np.ptp(a[i]) == 0 or np.ptp(b[i]) == 0:
            continue
        r.append(spearmanr(a[i], b[i])[0])
    return np.percentile(r, 2.5), np.percentile(r, 97.5)


SCORES = {"D1 extrapolation": "d1", "D1 (REG-Q audited)": "d1q", "D2 family spread": "d2", "D3 curvature bound B": "d3_B",
          "leverage iid-SE (baseline a)": "REG-L_se_iid", "corner distance Z (baseline b)": "Zcorner"}
g = raw.groupby("_c")
med = g[list(SCORES.values())].median()
cells = cid.set_index("_c").join(med)
cells["abs_bias"] = cells.bias.abs()
cells["cls"] = cells.mech.map(CLASS)
cells["positive"] = cells.abs_bias > 0.10 * cells.scale
cells["resolved"] = cells.abs_bias > 2 * cells.bias_se

# ---- rank correlations -------------------------------------------------------------------------------------------
rows = []
for name, col in SCORES.items():
    for grp, m in [("all", cells.index == cells.index)] + [(k, cells.mech == k) for k in sorted(cells.mech.unique())]:
        c = cells[m]
        rho, pv = spearmanr(c[col], c.abs_bias)
        lo, hi = boot_spearman_ci(c[col], c.abs_bias)
        rows.append(dict(score=name, group=grp, level="cell", n=len(c), spearman=rho, p=pv, spearman_lo=lo, spearman_hi=hi))
    pr = raw.groupby("_c").apply(lambda d: spearmanr(d[col], d.abs_err)[0] if d[col].nunique() > 1 else np.nan)
    rows.append(dict(score=name, group="all", level="replicate (median over cells of within-cell rho)", n=int(pr.notna().sum()),
                     spearman=float(pr.median()), p=np.nan))
    rho, pv = spearmanr(raw[col], raw.abs_err, nan_policy="omit")
    rows.append(dict(score=name, group="all", level="replicate pooled", n=len(raw), spearman=rho, p=pv))
rk = pd.DataFrame(rows)
rk.to_csv("results/summary/c6_rank.csv", index=False)

# ---- flag performance -------------------------------------------------------------------------------------------
def prf(flag, pos):
    tp = int((flag & pos).sum()); fp = int((flag & ~pos).sum()); fn = int((~flag & pos).sum())
    return tp, fp, fn, tp / max(tp + fp, 1), tp / max(tp + fn, 1)


ev = cells[cells.resolved]    # PREREG: cells with |bias| <= 2 MC-SE excluded from precision/recall (positives are all resolved: 0.1*scale >> 2 SE)
rows = []
for name, col in SCORES.items():
    auc = roc_auc_score(ev.positive, ev[col])
    # pre-registered rule applies to D1, D2 (flag per replicate; cell flagged if the majority of replicates is flagged)
    if col in ("d1", "d1q", "d2"):
        fl = (raw[col] > raw["thr"]).groupby(raw._c).mean().reindex(ev.index) > 0.5
        tp, fp, fn, pr_, rc = prf(fl, ev.positive)
        rows.append(dict(score=name, rule="pre-registered 0.10*max(|tau_hat|,sd_y)", n_cells=len(ev), n_pos=int(ev.positive.sum()),
                         tp=tp, fp=fp, fn=fn, precision=pr_, recall=rc, auc=auc))
    # oracle threshold (Youden J = recall - false-positive rate on the median score; best-F1 degenerates to flag-everything at a base rate of 0.82)
    best = None
    npos, nneg = int(ev.positive.sum()), int((~ev.positive).sum())
    for t in np.unique(ev[col].dropna()):
        fl = ev[col] >= t
        tp, fp, fn, pr_, rc = prf(fl, ev.positive)
        j = rc - fp / nneg
        if best is None or j > best[0]:
            best = (j, t, tp, fp, fn, pr_, rc)
    rows.append(dict(score=name, rule=f"oracle Youden-J threshold ({best[1]:.3g})", n_cells=len(ev), n_pos=int(ev.positive.sum()),
                     tp=best[2], fp=best[3], fn=best[4], precision=best[5], recall=best[6], auc=auc))
fl = pd.DataFrame(rows)
fl.to_csv("results/summary/c6_flag.csv", index=False)

# AUC by mechanism (within-mechanism, threshold-free)
rows = []
for k in sorted(cells.mech.unique()):
    e = ev[ev.mech == k]
    r = dict(mech=k, n=len(e), n_pos=int(e.positive.sum()))
    for name, col in SCORES.items():
        r["auc " + name] = roc_auc_score(e.positive, e[col]) if 0 < e.positive.sum() < len(e) else np.nan
    rows.append(r)
pd.DataFrame(rows).to_csv("results/summary/c6_auc_by_mech.csv", index=False)

# ---- intervals ----------------------------------------------------------------------------------------------------
cells["regime"] = np.where(cells.abs_bias <= 0.5 * cells.sd, "variance-dominated",
                           np.where(cells.abs_bias > 2 * cells.sd, "bias-dominated", "between"))
IV = {"iid OLS": "iid", "network sandwich": "sandwich", "pairs bootstrap": "bootstrap", "Louvain block bootstrap": "blockboot",
      "sandwich + B (pre-registered)": "biasaware"}
cs = summ.set_index(summ.index)
sm = cid.set_index("_c")[CELL].merge(summ[CELL + [f"cover_{v}" for v in IV.values()] + [f"width_{v}" for v in IV.values()]], on=CELL).set_index(cid["_c"])
for v in IV.values():
    cells[f"cover_{v}"] = sm[f"cover_{v}"].values
    cells[f"width_{v}"] = sm[f"width_{v}"].values
cells.reset_index().to_csv("results/summary/c6_cover_cells.csv", index=False)
rows = []
GROUPS = [("regime", "regime"), ("mech", "mech"), ("class", "cls"), ("all", None)]
for grp, key in GROUPS:
    groups = [(k, d) for k, d in cells.groupby(key)] if key else [("all", cells)]
    for k, d in groups:
        for nm, v in IV.items():
            cl, ch = boot_mean_ci(d[f"cover_{v}"]); wl, wh = boot_mean_ci(d[f"width_{v}"])
            rows.append(dict(by=grp, group=k, interval=nm, n_cells=len(d), mean_coverage=d[f"cover_{v}"].mean(),
                             mean_coverage_lo=cl, mean_coverage_hi=ch,
                             min_coverage=d[f"cover_{v}"].min(), frac_cells_below_0p90=(d[f"cover_{v}"] < 0.90).mean(),
                             mean_width=d[f"width_{v}"].mean(), mean_width_lo=wl, mean_width_hi=wh, median_width=d[f"width_{v}"].median()))
cv = pd.DataFrame(rows)
# width-matched control: inflate the iid-SE and sandwich interval half-widths by a constant k so that mean width equals biasaware
for base, col in [("sandwich", "REG-L_se"), ("iid", "REG-L_se_iid")]:
    w_t = (2 * (1.96 * raw["REG-L_se"] + raw["d3_B"])).mean()
    k = w_t / (2 * 1.96 * raw[col]).mean()
    hit = ((raw["REG-L"] - raw["tau"]).abs() <= k * 1.96 * raw[col])
    c = hit.groupby(raw._c).mean()
    d = cells.assign(cov=c, wid=(2 * k * 1.96 * raw[col]).groupby(raw._c).mean())
    for grp, key in GROUPS:
        groups = [(kk, dd) for kk, dd in d.groupby(key)] if key else [("all", d)]
        for kk, dd in groups:
            cv = pd.concat([cv, pd.DataFrame([dict(by=grp, group=kk, interval=f"{base} SE x{k:.2f} (width-matched to B-interval)", n_cells=len(dd),
                                                   mean_coverage=dd["cov"].mean(), mean_coverage_lo=boot_mean_ci(dd["cov"])[0],
                                                   mean_coverage_hi=boot_mean_ci(dd["cov"])[1], min_coverage=dd["cov"].min(),
                                                   frac_cells_below_0p90=(dd["cov"] < 0.90).mean(),
                                                   mean_width=float(dd["wid"].mean()), mean_width_lo=boot_mean_ci(dd["wid"])[0],
                                                   mean_width_hi=boot_mean_ci(dd["wid"])[1], median_width=np.nan)])])
cv.to_csv("results/summary/c6_cover.csv", index=False)
# how tight is B?  median over cells of B/|bias| in bias-dominated cells, share of cells with B >= |bias|
b = cells[cells.regime == "bias-dominated"]
print("B/|bias| bias-dominated: median", (b.d3_B / b.abs_bias).median(), "share B>=|bias|", (b.d3_B >= b.abs_bias).mean())
print("by mech share B>=|bias| (bias-dominated):\n", b.groupby("mech").apply(lambda d: pd.Series(dict(n=len(d), share=(d.d3_B >= d.abs_bias).mean(), med_ratio=(d.d3_B / d.abs_bias).median()))))
f = cells[cells.cover_biasaware < 0.90]
print("bias-aware failure cells", len(f))
for k in ["graph.kind", "design.p", "graph.d", "out.sigma", "graph.n"]:
    print(f.groupby(k).size().to_dict(), "of", cells.groupby(k).size().to_dict())
cells[["mech", "d3_B", "abs_bias"]].assign(ratio=cells.d3_B / cells.abs_bias).to_csv("results/summary/c6_B_vs_bias.csv")
pd.set_option("display.width", 250, "display.max_columns", 30, "display.max_rows", 200)
print(cells.regime.value_counts()); print(cells.mech.value_counts()); print(cells.positive.mean(), cells.resolved.mean())
print(rk.round(3).to_string()); print(fl.round(3).to_string())
print(pd.read_csv("results/summary/c6_auc_by_mech.csv").round(2).to_string())
print(cv.round(3).to_string())
