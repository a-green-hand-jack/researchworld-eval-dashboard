"""[reads] results/datasets.csv  [writes] tables/tab_datasets.tex  (run via run_all.sh)
Table of the real pools (context for C0-C2). Input: data_in/datasets.csv (experiment-repo results/datasets.csv).
Output: tables/tab_datasets.tex (booktabs fragment, \\input into the paper)."""
import pandas as pd

d = pd.read_csv("data_in/datasets.csv")

def num(x, p=3):
    s = f"{x:.{p}g}"
    if "e" in s:
        m, e = s.split("e"); return f"${m}{{\\times}}10^{{{int(e)}}}$"
    return s.replace("-", "$-$")

rows = []
for _, r in d.iterrows():
    out = "binary" if r["outcome"] == "binary" else "continuous"
    rows.append(" & ".join([r["dataset"].replace("_", "\\_"), f"{int(r['pool_size']):,}".replace(",", "{,}"), out,
                            num(r["y_mean"]), num(r["skew"], 2), f"{r['corr_y_yhat']:.2f}",
                            str(int(r["n_features"]))]) + " \\\\")
tex = ("\\small\\begin{tabular}{lrlrrrr}\n\\toprule\n"
       "pool & $N_{\\mathrm{pool}}$ & outcome & mean $Y$ & skew $Y$ & corr$(Y,\\hat Y)$ & $\\dim X$ \\\\\n\\midrule\n"
       + "\n".join(rows) + "\n\\bottomrule\n\\end{tabular}\n")
open("tables/tab_datasets.tex", "w").write(tex)
