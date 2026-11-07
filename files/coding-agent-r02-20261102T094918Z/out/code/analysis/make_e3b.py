import sys; sys.path.insert(0, "/work/analysis")
import numpy as np, pandas as pd
from style import LAB
df = pd.read_csv("/work/results/e3b_misfit.csv"); df["G"] = df[["G_conf", "G_min"]].max(axis=1)
pm = df.groupby(["s_err", "T", "score", "prob"])[["cov", "G", "G_conf", "lm1", "kl_pred"]].mean().reset_index()
pm["dlm"] = pm.lm1 - pm.groupby(["s_err", "T", "prob"]).lm1.transform("min")
m = pm.groupby(["s_err", "T", "score"])[["G", "dlm", "kl_pred", "cov"]].mean()
order = ["euclid", "tv", "hellinger", "chi2", "kl", "aitchison_1e-2"]
G, d = m["G"].unstack("score")[order], m["dlm"].unstack("score")[order]
kl = m["kl_pred"].unstack("score").iloc[:, 0]
print(G.round(3)); print(d.round(2)); print(kl.round(3)); print(m["cov"].unstack("score").round(3))
lab = {**LAB, "aitchison_1e-2": r"Ait. $10^{-2}$"}
lines = []
for (s, T) in G.index:
    gb = G.loc[(s, T)].min()
    c1 = [("\\mathbf{%.3f}" if G.loc[(s, T), o] <= gb + 0.0025 else "%.3f") % G.loc[(s, T), o] for o in order]
    c2 = [("\\mathbf{%.2f}" if d.loc[(s, T), o] <= 0.05 else "%.2f") % d.loc[(s, T), o] for o in order]
    lines.append(f"{s:g} & {T:g} & {max(kl.loc[(s, T)], 0.0):.2f} & " + " & ".join("$" + c + "$" for c in c1) + "\\\\")
    lines.append(" & & & " + " & ".join("$" + c + "$" for c in c2) + "\\\\[-1pt]")
open("/work/paper/tables/e3b.tex", "w").write("\\begin{tabular}{rrr" + "c" * len(order) + "}\\toprule\n$s_{\\rm err}$ & $T$ & $\\mathrm{KL}_{\\rm pred}$ & " + " & ".join(lab[o] for o in order) + "\\\\\\midrule\n" + "\n".join(lines) + "\n\\bottomrule\\end{tabular}\n")
