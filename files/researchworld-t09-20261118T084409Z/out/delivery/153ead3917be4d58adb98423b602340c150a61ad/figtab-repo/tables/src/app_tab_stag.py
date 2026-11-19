"""Appendix table for C7 (grid e8): repeated Bernoulli measurements vs staggered rollout, at T+1 measurements per unit.
Entries: bias, and RMSE[95% interval]; the single-measurement REG-L baseline (T+1 = 1) is in e8.csv as REG-L.  Reads results/summary/e8.csv.  Writes tables/app_tab_stag.tex (tabular body only)."""
import os
import pandas as pd

ROOT = os.path.join(os.path.dirname(__file__), "..", "..")
e = pd.read_csv(os.path.join(ROOT, "results", "summary", "e8.csv"))
OUT = os.path.join(ROOT, "tables", "app_tab_stag.tex")
TAGS = [("linear", "linear"), ("convex", "convex"), ("2hop-convex", "two-hop, convex"), ("threshold", "threshold")]
EST = [("REPEAT-REG", "REG-L, pooled repeats"), ("STAG-REG", "REG-L, pooled rollout"), ("STAG-direct", "rollout, direct")]
f = lambda x: f"{x:.3f}".replace("0.", ".") if abs(x) < 1 else f"{x:.2f}"
L = ["\\footnotesize\\setlength{\\tabcolsep}{3pt}", "\\begin{tabular}{llrccc}", "\\toprule",
     "$d$ & response & $T{+}1$ & " + " & ".join(l for _, l in EST) + " \\\\",
     " & & & bias, RMSE[95\\%] & bias, RMSE[95\\%] & bias, RMSE[95\\%] \\\\", "\\midrule"]
def cell(r):
    return f"${f(r.bias)}$, {f(r.rmse)}[{f(r.rmse_lo)},{f(r.rmse_hi)}]"
for di, d in enumerate(sorted(e["graph.d"].unique())):
    if di:
        L.append("\\midrule")
    for tg, tl in TAGS:
        for T in sorted(e["stag.T"].unique()):
            x = e[(e["graph.d"] == d) & (e.tag == tg) & (e["stag.T"] == T)].set_index("est")
            L.append(f"{d} & {tl} & {int(T) + 1} & " + " & ".join(cell(x.loc[k]) for k, _ in EST) + " \\\\")
L += ["\\bottomrule", "\\end{tabular}"]
open(OUT, "w").write("\n".join(L) + "\n")
print("wrote", OUT, "rows", len(L))
