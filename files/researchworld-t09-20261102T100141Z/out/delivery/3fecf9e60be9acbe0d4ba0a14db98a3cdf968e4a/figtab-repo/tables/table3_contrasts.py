"""Table 3: paired MSE contrasts over all experiments. For each experiment (rows) and comparison A vs B (columns) the number of cells
where A has the smaller / statistically indistinguishable / larger MSE than B on the same assignments and noise (95% bootstrap CI of the
MSE ratio A/B, results/contrasts.csv, excludes 1 or not). Output: tables/table3_contrasts.tex."""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "figures"))
import pandas as pd
import common as C

ct = pd.read_csv(os.path.join(C.RESULTS, "contrasts.csv"))
cols = [("ols_f", "dm", r"\shortstack{OLS\\vs DM}"), ("ols_f", "hajek_q0.75", r"\shortstack{OLS vs\\Hajek}"), ("ols_f", "ols_poly", r"\shortstack{OLS vs\\quadr.}"),
        ("ols_f", "ols_f_adj", r"\shortstack{OLS vs\\OLS$+$cov.}"), ("ols_f2", "ols_f", r"\shortstack{2-hop\\vs OLS}"), ("gbm", "ols_f", r"\shortstack{GBM\\vs OLS}"), ("ridge_rich", "ols_f", r"\shortstack{ridge\\vs OLS}")]
rows_ = [("MAIN", "main grid"), ("MAIN_s2", "main grid, seed 2"), ("E1_size", "E1 size $n$"), ("E2_degree", "E2 degree"), ("E3_gamma", "E3 $\\rho$"),
         ("E4_curv", "E4 curvature $\\times p$"), ("E5_graphs", "E5 graph families"), ("E6_spec", "E6 specification"), ("E7_model", "E7 model class"),
         ("E8_design", "E8 design"), ("E9_noise", "E9 noise"), ("E10_coverage", "E10 coverage"), ("E11_grapherr", "E11 graph error")]
body = []
for e, lab in rows_:
    cells = []
    for A, B, _ in cols:
        c = ct[(ct.experiment == e) & (ct.A == A) & (ct.B == B)]
        if c.empty:
            cells.append("--")
        else:
            w, l = int((c.ratio_hi < 1).sum()), int((c.ratio_lo > 1).sum())
            cells.append(f"{w}/{len(c) - w - l}/{l}")
    body.append(f"{lab} & " + " & ".join(cells) + r" \\")
tex = r"""\begin{tabular}{@{}l""" + "c" * len(cols) + r"""@{}}
\toprule
 & """ + " & ".join(c[2] for c in cols) + r""" \\
\midrule
""" + "\n".join(body) + r"""
\bottomrule
\end{tabular}
"""
os.makedirs(C.TABOUT, exist_ok=True)
open(os.path.join(C.TABOUT, "table3_contrasts.tex"), "w").write(tex)
print(tex)
