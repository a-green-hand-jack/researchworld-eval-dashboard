"""Table 2 (claims C2/C3 headline): E1 at alpha=0.1 for chosen configurations (file stems on the command line; default: dirichlet and lognormal, D=5, het., linear).
Rows: every score under plain split, locally normalised and Mondrian variants.  Columns per configuration, mean +/- half-width of the 95% t-CI over the 100 replicates:
marginal coverage, worst-slab coverage (wsc), oracle conditional-coverage gap (mean |c(x)-0.9|, Monte-Carlo bias ~0.012-0.016, compare with the null spread of Fig 5),
and region mass (pool_frac: mass of the marginal law of y inside the region; smaller = more informative).
Means only (CI half-widths in a comment line of the table). Bold = best in column (largest wsc, smallest gap, smallest mass); no significance claim, see Fig 2/3 for paired ratios and null band.
"""
import sys
from common import *

d = load_e1()
files = [f if f.endswith(".csv") else f + ".csv" for f in sys.argv[1:]] or ["main_dirichlet_D5_h1_linear.csv", "main_lognormal_D5_h1_linear.csv"]
d = d[d.file.isin(files)]
mets = [("cov10", "cov.", 3), ("wsc", "wsc", 2), ("or_gap", "or.\\ gap", 3), ("pool_frac", "mass", 3)]
BEST = {"wsc": max, "or_gap": min, "pool_frac": min}
order = [("plain", ["l2", "l1", "linf", "hell", "kl", "ait", "nll"]), ("locally normalised", ["l2_n", "linf_n", "hell_n", "kl_n", "ait_n"]), ("Mondrian", ["l2_m", "hell_m", "ait_m"])]
label = lambda m: SCORE_LAB[split_method(m)[0]]
cells = {(f, c): agg(d[d.file == f], c).set_index("method") for f in files for c, _, _ in mets}
nc = len(mets)
hw = {}
L = [r"\begin{tabular}{l" + "r" * nc * len(files) + "}", r"\toprule"]
L.append(" & " + " & ".join(rf"\multicolumn{{{nc}}}{{c}}{{{cfg_label(d[d.file == f].iloc[0])}}}" for f in files) + r" \\")
L.append(" ".join(rf"\cmidrule(lr){{{2 + nc * i}-{1 + nc * (i + 1)}}}" for i in range(len(files))))
L.append("score & " + " & ".join(" & ".join(n for _, n, _ in mets) for _ in files) + r" \\")
for title, ms in order:
    L.append(r"\midrule")
    L.append(rf"\multicolumn{{{1 + nc * len(files)}}}{{l}}{{\emph{{{title}}}}} \\")
    for m in ms:
        row = [label(m)]
        for f in files:
            for c, _, nd in mets:
                A = cells[(f, c)]
                r = A.loc[m]
                t = f"{r['mean']:.{nd}f}"
                if c in BEST:
                    ok = A.index[(cells[(f, "cov10")]["mean"] - 0.9).abs() < 0.01]
                    if r["mean"] == BEST[c](A.loc[ok, "mean"]):
                        t = r"\textbf{" + t + "}"
                hw[c] = max(hw.get(c, 0), (r.hi - r.lo) / 2)
                row.append(t)
        L.append(" & ".join(row) + r" \\")
L += [r"\bottomrule", r"\end{tabular}"]
L.insert(0, "% means only; largest 95% CI half-width over all cells: " + ", ".join(f"{c} {v:.3f}" for c, v in hw.items()))
write_table("\n".join(L) + "\n", "tab2_e1_headline.tex")
