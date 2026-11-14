"""Appendix tables (claims C2/C3 across the whole E1 grid), one per family: rows = (D, het., predictor), 100 replicates each, alpha=0.1.
Columns (means over replicates; CI half-widths are in a comment line):
 marginal coverage range over all 16 methods (min--max of the per-method means);
 oracle conditional-coverage gap (mean |c(x)-0.9|; compare null spread ~0.016 at n_cal=500) for plain L2 and locally-normalised L2;
 worst-slab coverage for plain L2 and locally-normalised L2;
 region mass (pool_frac) for plain L2, KL, Aitchison, Dirichlet NLL.
"""
from common import *

d = load_e1()
cols = [("or_gap", "l2", 3), ("or_gap", "l2_n", 3), ("wsc", "l2", 2), ("wsc", "l2_n", 2),
        ("pool_frac", "l2", 3), ("pool_frac", "kl", 3), ("pool_frac", "ait", 3), ("pool_frac", "nll", 3)]
for fam, g0 in d.groupby("family"):
    hw = {}
    L = [r"\begin{tabular}{rllc" + "r" * len(cols) + "}", r"\toprule",
         r" & & & & \multicolumn{2}{c}{oracle gap} & \multicolumn{2}{c}{worst slab} & \multicolumn{4}{c}{region mass} \\",
         r"\cmidrule(lr){5-6} \cmidrule(lr){7-8} \cmidrule(lr){9-12}",
         r"$D$ & het. & pred. & cov. range & $L_2$ & $L_2$-n & $L_2$ & $L_2$-n & $L_2$ & KL & Ait. & NLL \\", r"\midrule"]
    for (D, h, p), g in sorted(g0.groupby(["D", "hetero", "pred"]), key=lambda t: (t[0][0], t[0][1], t[0][2])):
        cv = agg(g, "cov10").set_index("method")["mean"]
        row = [str(int(D)), "yes" if h else "no", p, f"{cv.min():.3f}--{cv.max():.3f}"]
        for c, m, nd in cols:
            A = agg(g, c).set_index("method").loc[m]
            row.append(f"{A['mean']:.{nd}f}")
            hw[c] = max(hw.get(c, 0), (A.hi - A.lo) / 2)
        L.append(" & ".join(row) + r" \\")
        if p == "rf" and h:
            L.append(r"\addlinespace")
    L[-1] = L[-1] if L[-1] != r"\addlinespace" else None
    L = [x for x in L if x is not None]
    L += [r"\bottomrule", r"\end{tabular}"]
    L.insert(0, "% means only; largest 95% CI half-width over all cells: " + ", ".join(f"{c} {v:.3f}" for c, v in hw.items()))
    write_table("\n".join(L) + "\n", f"tabA_e1_grid_{fam}.tex")
