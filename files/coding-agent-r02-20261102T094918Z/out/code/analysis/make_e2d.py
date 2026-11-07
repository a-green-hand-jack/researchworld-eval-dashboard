import sys; sys.path.insert(0, "/work/analysis")
import numpy as np, pandas as pd
from style import LAB
df = pd.read_csv("/work/results/e2d_ellipsoid.csv")
pm = df.groupby(["family", "D", "kappa", "score", "prob"])[["G", "lm1"]].mean().reset_index()
pm["dlm"] = pm.lm1 - pm.groupby(["family", "D", "kappa", "prob"]).lm1.transform("min")
m = pm.groupby(["family", "D", "kappa", "score"])[["G", "dlm"]].mean()
order = ["euclid", "chi2", "aitchison", "mahal_ilr"]
lab = {**LAB, "mahal_ilr": "Mahalanobis (ilr)"}
fam = {"dirichlet": "Dirichlet", "logistic_normal": "Logistic-normal", "additive": "Additive"}
lines = []
for (f, D, k), g in m.groupby(level=[0, 1, 2], sort=False):
    g = g.droplevel([0, 1, 2])
    lines.append(f"{fam[f]} & {D} & {k} & " + " & ".join(f"${g.loc[o, 'G']:.3f}$ / ${g.loc[o, 'dlm']:.2f}$" for o in order) + "\\\\")
open("/work/paper/tables/e2d.tex", "w").write("\\begin{tabular}{lrr" + "c" * len(order) + "}\\toprule\nnoise & $D$ & $\\kappa$ & " + " & ".join(lab[o] for o in order) + "\\\\\\midrule\n" + "\n".join(lines) + "\n\\bottomrule\\end{tabular}\n")
print(open("/work/paper/tables/e2d.tex").read())
