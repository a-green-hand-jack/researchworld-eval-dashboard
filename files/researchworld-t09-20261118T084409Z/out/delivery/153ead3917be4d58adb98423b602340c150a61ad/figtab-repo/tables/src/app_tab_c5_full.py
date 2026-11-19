"""Appendix tables for C5: every estimator x mechanism of Table 1, with 95% intervals.  Reads results/summary/c5_table1.csv.
Writes tables/app_tab_c5_median.tex (median over graphs) and tables/app_tab_c5_worst.tex (worst graph), tabular bodies only.
Entry: value[lo,hi]; the interval is the median of the cell 95% intervals' ends (median) or the interval of the worst graph's cell (worst)."""
import os
import pandas as pd

ROOT = os.path.join(os.path.dirname(__file__), "..", "..")
t = pd.read_csv(os.path.join(ROOT, "results", "summary", "c5_table1.csv"))
MECH = [("linear", "linear"), ("concave", "concave"), ("convex", "convex"), ("het-direct", "het. direct"), ("thresh0.3", "thr. $0.3$"),
        ("thresh0.5", "thr. $0.5$"), ("count", "degree-mult."), ("het-indirect", "het. indirect"), ("linear-2hop", "2-hop lin."),
        ("convex-2hop", "2-hop conv.")]
EST = [("DM", "DM"), ("HAJEK", "H\\'ajek"), ("HAJEK-r0.25", "H\\'ajek$_{.25}$"), ("HT-exact", "HT (exact)"), ("REG-L", "REG-L"),
       ("REG-Lc", "REG-Lc"), ("REG-Q", "REG-Q"), ("REG-G", "REG-G"), ("REG-GBM", "GBM"), ("REG-GCN", "GCN$^{\\dagger}$"), ("REG-O", "REG-O")]


def num(x):
    if x >= 100:
        return f"{x:.1e}".replace("e+", "\\!\\times\\!10^{") + "}"   # HT-exact only
    return f"{x:.3f}".replace("0.", ".") if x < 1 else f"{x:.2f}"


def entry(r, stat):
    v, lo, hi = r[stat], r[f"{stat}_lo"], r[f"{stat}_hi"]
    if v >= 100:
        return f"${num(v)}$"
    return f"{num(v)}[{num(lo)},{num(hi)}]"


def make(stat, out):
    L = ["\\footnotesize\\setlength{\\tabcolsep}{2.6pt}", "\\begin{tabular}{l" + "c" * 5 + "}", "\\toprule"]
    for b, block in enumerate([MECH[:5], MECH[5:]]):
        if b:
            L.append("\\midrule")
        L.append("estimator & " + " & ".join(l for _, l in block) + " \\\\")
        L.append("\\midrule")
        for e, el in EST:
            cells = []
            for m, _ in block:
                r = t[(t.est == e) & (t.mech == m)]
                cells.append(entry(r.iloc[0], stat) if len(r) else "--")
            L.append(f"{el} & " + " & ".join(cells) + " \\\\")
    L += ["\\bottomrule", "\\end{tabular}"]
    open(out, "w").write("\n".join(L) + "\n")


for stat, name in [("median", "app_tab_c5_median.tex"), ("worst", "app_tab_c5_worst.tex")]:
    make(stat, os.path.join(ROOT, "tables", name))
print("wrote appendix C5 tables")
