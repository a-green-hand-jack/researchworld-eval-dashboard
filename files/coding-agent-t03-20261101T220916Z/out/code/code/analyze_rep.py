"""Replicate (second split + model seed) vs main results, d<=10 datasets -> paper/gen/tab_rep.tex"""
import numpy as np, pandas as pd
a = pd.read_parquet("/work/results/summary/inst_level.parquet"); b = pd.read_parquet("/work/results/summary_rep1/inst_level.parquet")
rows = []
L = ["\\begin{tabular}{llcccccc}", "\\toprule", "Dataset & Model & \\multicolumn{3}{c}{top-3 set correct (\\%), $m{=}128$} & \\multicolumn{3}{c}{top-3 set correct (\\%), $m{=}256$}\\\\",
     "\\cmidrule(lr){3-5}\\cmidrule(lr){6-8}", " & & main & replicate & AUC (m/r) & main & replicate & AUC (m/r)\\\\", "\\midrule"]
KN = {"lr": "LR", "mlp": "MLP", "rf": "RF", "xgb": "XGB"}
res = []
for ds in ["pima", "gmsc", "acsincome"]:
    for k in ["lr", "mlp", "rf", "xgb"]:
        cells = []
        for m in (128, 256):
            x = a[(a.ds == ds) & (a.kind == k) & (a.est == "kernel") & (a.m == m)].t_topk
            y = b[(b.ds == ds) & (b.kind == k) & (b.est == "kernel") & (b.m == m)].t_topk
            cells.append((100 * x.mean() if len(x) else np.nan, 100 * y.mean() if len(y) else np.nan))
        import pickle, glob
        auc = [pickle.load(open(sorted(glob.glob(f"/work/results/{d}/{ds}_{k}/inst_*.pkl"))[0], "rb"))["auc"] for d in ("main", "main_rep1")]
        f = lambda v: "enum." if np.isnan(v) else f"{v:.1f}"
        L.append(f"{ds} & {KN[k]} & {f(cells[0][0])} & {f(cells[0][1])} & {auc[0]:.3f}/{auc[1]:.3f} & {f(cells[1][0])} & {f(cells[1][1])} & {auc[0]:.3f}/{auc[1]:.3f}\\\\")
        res.append((ds, k, cells))
L += ["\\bottomrule", "\\end{tabular}"]
open("/work/paper/gen/tab_rep.tex", "w").write("\n".join(L))
d = np.array([[c[0][1] - c[0][0], c[1][1] - c[1][0]] for _, _, c in res if not np.isnan(c[0][0])])
print("mean abs difference (points) m=128, m=256:", np.nanmean(np.abs(d), 0), "mean signed", np.nanmean(d, 0))
