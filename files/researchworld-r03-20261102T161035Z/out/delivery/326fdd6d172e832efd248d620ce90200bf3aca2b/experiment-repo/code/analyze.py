"""Aggregate raw per-(rep,model) errors into curves with bootstrap CIs and paired comparisons.
usage: analyze.py RAW_DIR OUT_DIR   (reads RAW_DIR/{dataset}_{split}.csv)"""
import sys, glob, os, numpy as np, pandas as pd
from scipy import stats
raw, out = sys.argv[1:3]; B = 1000; rng = np.random.default_rng(0)
curves, paired, kneed = [], [], []
def rmse(d): return np.sqrt(d.sez2.sum() / d.n.sum())
for f in sorted(glob.glob(os.path.join(raw, "*_*.csv"))):
    name = os.path.basename(f)[:-4]
    if name.startswith("pilot"): continue
    d = pd.read_csv(f); d["unit"] = d.model.astype(str)   # cluster bootstrap over test models (a model recurs across repeated splits)
    units = d.unit.unique(); ui = {u: i for i, u in enumerate(units)}; d["u"] = d.unit.map(ui)
    bs = rng.integers(0, len(units), (B, len(units)))
    cnt = np.stack([np.bincount(b, minlength=len(units)) for b in bs])      # bootstrap multiplicities (B,U)
    def stat(g):                                                         # g has columns u, sez2, n -> z-RMSE per bootstrap
        s = np.zeros(len(units)); nn = np.zeros(len(units)); np.add.at(s, g.u.values, g.sez2.values); np.add.at(nn, g.u.values, g.n.values)
        return s, nn
    cache = {}
    for (sel, inf, k), g in d.groupby(["sel", "inf", "k"]):
        s, nn = stat(g); cache[(sel, inf, k)] = (s, nn)
        est = np.sqrt(s.sum() / nn.sum()); bt = np.sqrt((cnt @ s) / (cnt @ nn)); lo, hi = np.percentile(bt, [2.5, 97.5])
        raw_rmse = np.sqrt(g.se2.sum() / g.n.sum())
        curves.append((name, sel, inf, k, est, lo, hi, raw_rmse, g.model.nunique(), g.rep.nunique()))
    # skill vs the no-information mean predictor on the same targets (mean predictor is selection independent)
    for sel_a, inf_a, sel_b, inf_b in [("greedy_bayes", "fa", "random", "fa"), ("greedy_ridge", "ridge", "random", "ridge"),
                                       ("greedy_ridge", "fa", "random", "fa"), ("greedy_bayes", "ridge", "random", "ridge"),
                                       ("greedy_ridge", "ridge", "greedy_bayes", "ridge"), ("greedy_ridge", "ridge", "qr", "ridge"),
                                       ("greedy_ridge", "ridge", "coverage", "ridge"), ("greedy_ridge", "ridge", "variance", "ridge"),
                                       ("greedy_ridge", "ridge", "corr_mean", "ridge"), ("greedy_ridge", "ridge", "farthest", "ridge"),
                                       ("greedy_ridge", "ridge", "greedy_ridge", "knn"), ("greedy_ridge", "ridge", "greedy_ridge", "rank1"),
                                       ("greedy_ridge", "ridge", "greedy_ridge", "fa"), ("greedy_ridge", "ridge", "greedy_ridge", "mean")]:
        for k in sorted(d.k.unique()):
            if (sel_a, inf_a, k) not in cache or (sel_b, inf_b, k) not in cache: continue
            (sa, na), (sb, nb) = cache[(sel_a, inf_a, k)], cache[(sel_b, inf_b, k)]
            n = np.maximum(na, 1); ok = (na > 0) & (nb > 0)
            diff = np.sqrt(sa.sum() / na.sum()) - np.sqrt(sb.sum() / nb.sum())
            bt = np.sqrt((cnt @ sa) / (cnt @ na)) - np.sqrt((cnt @ sb) / (cnt @ nb)); lo, hi = np.percentile(bt, [2.5, 97.5])
            # paired per-unit mean z^2 error, Wilcoxon signed rank
            da, db = (sa / np.maximum(na, 1))[ok], (sb / np.maximum(nb, 1))[ok]
            p = stats.wilcoxon(da, db).pvalue if np.any(da != db) else 1.0
            paired.append((name, sel_a, inf_a, sel_b, inf_b, k, diff, lo, hi, p, ok.sum()))
cv = pd.DataFrame(curves, columns="data sel inf k zrmse lo hi rmse_raw n_models n_reps".split())
base = cv[(cv.inf == "mean") & (cv.sel == "random")].set_index(["data", "k"]).zrmse
cv["skill"] = [1 - (r.zrmse / base[(r.data, r.k)]) ** 2 for r in cv.itertuples()]
cv.to_csv(os.path.join(out, "curves.csv"), index=False)
pd.DataFrame(paired, columns="data sel_a inf_a sel_b inf_b k diff_zrmse lo hi wilcoxon_p n_units".split()).to_csv(os.path.join(out, "paired.csv"), index=False)
print(cv[cv.sel.isin(["random", "greedy_ridge"]) & cv.inf.isin(["ridge", "fa", "mean"])].pivot_table(index=["data", "sel", "inf"], columns="k", values="zrmse").round(2).to_string())
