"""Write tables/default_budget.tex: Kernel SHAP at the library-default budget on the cells where it is sampled (d > 10).

usage: python3 make_default_table.py TABLES_DIR OUTDIR
"""
import os, sys
import pandas as pd

tab, out = sys.argv[1], sys.argv[2]
os.makedirs(out, exist_ok=True)
b = pd.read_csv(f"{tab}/budget_curve.csv")
ad = pd.read_csv(f"{tab}/adequacy.csv")
names = {"german": "German", "acs_emp": "ACS-Emp"}
x = b[(b.explainer == "kernel") & (b.d > 10) & (b.budget == (2 * b.d + 2048).clip(upper=2 ** b.d - 2))]
a = ad[(ad.explainer == "kernel") & (ad.k == 3) & (ad.tau == 0.9)]
x = x.merge(a[["dataset", "model", "budget", "frac_adequate", "lo", "hi"]], on=["dataset", "model", "budget"]).sort_values(["dataset", "model"], ascending=[False, True])
with open(f"{out}/default_budget.tex", "w") as f:
    f.write("\\begin{tabular}{llrrrrrrrr}\n\\toprule\nData & Model & $B$ & rows & top-1 & top-3 [95\\% CI] & top-5 & pair top-3 & Nogueira & $\\ge0.9$ [Wilson]\\\\\n\\midrule\n")
    for _, r in x.iterrows():
        f.write(f"{names.get(r.dataset, r.dataset)} & {r.model} & {int(r.budget)} & {int(r.rows)} & {r.match_ref_k1:.2f} & {r.match_ref_k3:.2f} [{r.match_ref_k3_lo:.2f}, {r.match_ref_k3_hi:.2f}] & {r.match_ref_k5:.2f} & {r.pair_match_k3:.2f} & {r.nogueira_k3:.2f} & {r.frac_adequate:.2f} [{r.lo:.2f}, {r.hi:.2f}]\\\\\n")
    f.write("\\bottomrule\n\\end{tabular}\n")
