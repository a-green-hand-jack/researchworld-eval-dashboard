"""[reads] results/headroom_population.csv  [writes] tables/tab_headroom.tex  (run via run_all.sh)
Appendix table (C1/C5): asymptotic width ratio to PPI++ of each adjuster class, N->infinity (rho=0), mean (SD over 10 splits).
Input: data_in/headroom_population.csv.  Output: tables/tab_headroom.tex"""
import pandas as pd
h = pd.read_csv("data_in/headroom_population.csv"); h = h[h.rho == 0]
order = ["galaxies", "forest", "alphafold", "gene_expression", "census_income", "census_healthcare", "census_education"]
cols = [("ppi", "PPI"), ("cf_lin_f", "lin.\\ $f$"), ("cf_iso_f", "isot.\\ $f$"), ("cf_gbm_f", "GBM $f$"),
        ("cf_lin_fX", "lin.\\ $(f,X)$"), ("cf_gbm_fX", "GBM $(f,X)$")]
rows = []
for d in order:
    cells = []
    for m, _ in cols:
        r = h[(h.dataset == d) & (h.method == m)]
        cells.append("--" if r.empty else f"${r.width_ratio.iloc[0]:.3f}{{\\pm}}{r.width_ratio_sd_splits.iloc[0]:.3f}$".replace("{\\pm}0.", "{\\pm}."))
    rows.append(" & ".join([d.replace("_", "\\_")] + cells) + " \\\\")
tex = ("\\scriptsize\\setlength{\\tabcolsep}{3pt}\\begin{tabular}{l" + "r" * len(cols) + "}\n\\toprule\npool & " + " & ".join(c for _, c in cols) + " \\\\\n\\midrule\n"
       + "\n".join(rows) + "\n\\bottomrule\n\\end{tabular}\n")
open("tables/tab_headroom.tex", "w").write(tex)
