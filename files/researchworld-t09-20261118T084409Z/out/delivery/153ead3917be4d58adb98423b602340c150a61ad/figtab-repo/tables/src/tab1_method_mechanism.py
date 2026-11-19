"""Table 1 (C5): normalised RMSE (RMSE / (|beta|+|gamma|); difference in means = 0.50) of each estimator under each interference
mechanism, median / worst over the six graphs.  Reads results/summary/c5_table1.csv.  Writes tables/tab1_method_mechanism.tex (tabular body only).
Bold = lowest median among the non-oracle columns, and every column whose 95% interval of the median overlaps that lowest column's interval."""
import os
import pandas as pd

ROOT = os.path.join(os.path.dirname(__file__), "..", "..")
t = pd.read_csv(os.path.join(ROOT, "results", "summary", "c5_table1.csv"))
OUT = os.path.join(ROOT, "tables", "tab1_method_mechanism.tex")
MECH = [("linear", "linear"), ("concave", "concave"), ("convex", "convex"), ("het-direct", "het. direct"),
        ("thresh0.3", "threshold $0.3$"), ("thresh0.5", "threshold $0.5$"), ("count", "degree-mult."),
        ("het-indirect", "het. indirect"), ("linear-2hop", "2-hop linear"), ("convex-2hop", "2-hop convex")]
EST = [("DM", "DM"), ("HAJEK-r0.25", "H\\'ajek$_{.25}$"), ("REG-L", "REG-L"), ("REG-Q", "REG-Q"), ("REG-G", "REG-G"),
       ("REG-GBM", "GBM"), ("REG-GCN", "GCN$^{\\dagger}$"), ("REG-O", "REG-O")]
ORACLE = {"REG-O"}
f = lambda x: f"{x:.2f}".replace("0.", ".")
lines = []
lines.append("\\footnotesize\\setlength{\\tabcolsep}{3.2pt}")
lines.append("\\begin{tabular}{l" + "c" * len(EST) + "}")
lines.append("\\toprule")
lines.append("mechanism & " + " & ".join(h for _, h in EST) + " \\\\")
lines.append("\\midrule")
for key, lab in MECH:
    r = t[t.mech == key].set_index("est")
    cand = [e for e, _ in EST if e not in ORACLE]
    best = min(cand, key=lambda e: r.loc[e, "median"])
    cells = []
    for e, _ in EST:
        s = f"{f(r.loc[e, 'median'])}/{f(r.loc[e, 'worst'])}"
        if e not in ORACLE and r.loc[e, "median_lo"] <= r.loc[best, "median_hi"] and r.loc[e, "median_hi"] >= r.loc[best, "median_lo"]:
            s = f"\\textbf{{{s}}}"
        if e in ORACLE:
            s = f"\\textcolor{{gray}}{{{s}}}"
        cells.append(s)
    lines.append(f"{lab} & " + " & ".join(cells) + " \\\\")
lines += ["\\bottomrule", "\\end{tabular}"]
open(OUT, "w").write("\n".join(lines) + "\n")
# the widest 95% half-width of any shown median, for the caption
r = t[t.est.isin([e for e, _ in EST]) & t.mech.isin([m for m, _ in MECH])]
print("max half-width of a median interval:", round(float(((r.median_hi - r.median_lo) / 2).max()), 3), "->", OUT)
