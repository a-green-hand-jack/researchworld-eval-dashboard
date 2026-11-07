"""[reads] results/headline_ols_real.csv  [writes] tables/tab_ols.tex  (run via run_all.sh)
C4 table: OLS on census_income (income on age, sex; no intercept), 2000 replicates per cell.  Left block: paired width ratio to ppi_py PPI++
(<1 narrower); right block: coverage of the 95% interval (Monte Carlo SE ~0.005). 
Input: data_in/headline_ols_real.csv.  Output: tables/tab_ols.tex"""
import pandas as pd
h = pd.read_csv("data_in/headline_ols_real.csv", keep_default_na=False)
R = [("classical", "classical"), ("ppi_lib", "PPI"), ("cv_f_full", "cv.\\ $f$"), ("cv_cf_lin_fX_full", "lin.\\ $(f,X)$"), ("cv_cf_gbm_fX_full", "GBM $(f,X)$")]
C = [("ppi++_lib", "PPI++"), ("classical", "classical"), ("cv_cf_lin_fX_full", "lin.\\ $(f,X)$"), ("cv_cf_gbm_fX_full", "GBM $(f,X)$")]
name = {0: "age", 1: "sex"}
rows = []
for n in sorted(h.n.unique()):
    for c in (0, 1):
        r = h[(h.n == n) & (h.coord == c)].iloc[0]
        rows.append(" & ".join([str(n) if c == 0 else "", name[c]] + [f"{r['ratio_vs_ppi++:' + m]:.3f}" for m, _ in R] + [f"{r['cov:' + m]:.3f}" for m, _ in C]) + " \\\\")
hdr = ("$n$ & coef. & " + " & ".join(c for _, c in R) + " & " + " & ".join(c for _, c in C) + " \\\\")
tex = ("\\scriptsize\\setlength{\\tabcolsep}{3pt}\\renewcommand{\\arraystretch}{0.84}\\begin{tabular}{rl" + "r" * len(R) + "|" + "r" * len(C) + "}\n\\toprule\n"
       f" & & \\multicolumn{{{len(R)}}}{{c}}{{width / PPI++ width}} & \\multicolumn{{{len(C)}}}{{|c}}{{coverage}} \\\\\n"
       f"\\cmidrule(lr){{3-{2+len(R)}}}\\cmidrule(l){{{3+len(R)}-{2+len(R)+len(C)}}}\n" + hdr + "\n\\midrule\n" + "\n".join(rows) + "\n\\bottomrule\n\\end{tabular}\n")
open("tables/tab_ols.tex", "w").write(tex)
