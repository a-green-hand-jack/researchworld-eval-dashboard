import sys; sys.path.insert(0, "/work/analysis")
import numpy as np, pandas as pd
from style import LAB
pd.set_option("display.width", 250); pd.set_option("display.max_columns", 30)
df = pd.read_csv("/work/results/e2c_dirmult.csv"); df["G"] = np.maximum(df.worst_conf, df.worst_min)
pm = df.groupby(["D", "N_ann", "kappa", "score", "prob"])[["cov", "G", "lm1", "lm05", "zero_frac"]].mean().reset_index()
for c in ("lm1", "lm05"):
    pm["d" + c] = pm[c] - pm.groupby(["D", "N_ann", "kappa", "prob"])[c].transform("min")
m = pm.groupby(["D", "N_ann", "kappa", "score"])[["G", "dlm1", "dlm05", "zero_frac"]].mean()
order = ["euclid", "tv", "hellinger", "chi2", "kl", "aitchison_1e-3", "aitchison_1e-2"]
G, d1, d5 = (m[c].unstack("score")[order] for c in ("G", "dlm1", "dlm05"))
zf = m["zero_frac"].unstack("score").iloc[:, 0]
print(G.round(3)); print(d1.round(2)); print(d5.round(2)); print(zf.round(3))
lab = {**LAB, "aitchison_1e-3": r"Ait. $10^{-3}$", "aitchison_1e-2": r"Ait. $10^{-2}$"}
lines = []
for (D, N, k) in G.index:
    gb, db = G.loc[(D, N, k)].min(), d1.loc[(D, N, k)].min()
    cells = [("\\mathbf{%.3f}" if G.loc[(D, N, k), s] <= gb + 0.0025 else "%.3f") % G.loc[(D, N, k), s] for s in order]
    cells2 = [("\\mathbf{%.2f}" if d1.loc[(D, N, k), s] <= 0.05 else "%.2f") % d1.loc[(D, N, k), s] for s in order]
    lines.append(f"{D} & {N} & {k} & {zf.loc[(D, N, k)]*100:.0f}\\% & " + " & ".join("$" + c + "$" for c in cells) + "\\\\")
    lines.append(f" & & & & " + " & ".join("$" + c + "$" for c in cells2) + "\\\\[-1pt]")
hdr = "\\begin{tabular}{rrrr" + "c" * len(order) + "}\\toprule\n$D$ & $N_{\\rm ann}$ & $\\kappa$ & zeros & " + " & ".join(lab[s] for s in order) + "\\\\\\midrule\n"
open("/work/paper/tables/e2c.tex", "w").write(hdr + "\n".join(lines) + "\n\\bottomrule\\end{tabular}\n")
print("cell-level winner by dlm1:", d1.idxmin(axis=1).value_counts().to_dict(), " by G:", G.idxmin(axis=1).value_counts().to_dict(), " by dlm05:", d5.idxmin(axis=1).value_counts().to_dict())
