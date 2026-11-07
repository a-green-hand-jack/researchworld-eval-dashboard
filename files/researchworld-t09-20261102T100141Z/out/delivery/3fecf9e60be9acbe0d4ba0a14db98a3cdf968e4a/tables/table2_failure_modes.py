"""Table 2: when does regression adjustment beat difference-in-means, and when does it fail?
One row per mechanism x design condition, over the six main-grid graphs: median [min, max] relative RMSE of
DM and OLS(z, f); median relative bias of OLS(z, f); and, from the paired MSE contrast in results/contrasts.csv
(OLS(z,f) vs DM, same assignments and noise, bootstrap CI), the number of graphs where OLS has smaller / larger MSE
(95% CI of the MSE ratio excludes 1) out of 6. Output: tables/table2_failure_modes.tex."""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "figures"))
import numpy as np
import pandas as pd
import common as C

df = C.load_replicates()
df = df[(df.experiment == "MAIN") & df.estimator.isin(["dm", "ols_f"])]
agg = C.aggregate(df, ["tag", "mechanism", "dsg", "graph", "estimator"])
ct = pd.read_csv(os.path.join(C.RESULTS, "contrasts.csv"))
ct = ct[(ct.experiment == "MAIN") & (ct.A == "ols_f") & (ct.B == "dm")].set_index("tag")
rows = []
for m in C.MECH_LABEL:
    for d in C.DESIGN_LABEL:
        a = agg[(agg.mechanism == m) & (agg.dsg == d)]
        o, b = a[a.estimator == "ols_f"], a[a.estimator == "dm"]
        tags = o.tag.tolist()
        win = int((ct.loc[tags, "ratio_hi"] < 1).sum()); lose = int((ct.loc[tags, "ratio_lo"] > 1).sum())
        f = lambda s: f"{s.median():.2f} [{s.min():.2f}, {s.max():.2f}]"
        rows.append(f"{m} & {C.DESIGN_LABEL[d]} & {f(b.rel_rmse)} & {f(o.rel_rmse)} & {o.bias.median():+.2f} & {win} / {lose} / {len(tags) - win - lose} \\\\")
    rows.append("\\addlinespace")
tex = r"""\begin{tabular}{@{}llccrc@{}}
\toprule
 & & \multicolumn{2}{c}{rel.\ RMSE, median [min, max]} & rel.\ bias & OLS better /\\
mech. & design & DM & OLS$(z,f)$ & OLS$(z,f)$ & worse / n.s.\ \\
\midrule
""" + "\n".join(rows[:-1]) + r"""
\bottomrule
\end{tabular}
"""
os.makedirs(C.TABOUT, exist_ok=True)
open(os.path.join(C.TABOUT, "table2_failure_modes.tex"), "w").write(tex)
print(tex)
