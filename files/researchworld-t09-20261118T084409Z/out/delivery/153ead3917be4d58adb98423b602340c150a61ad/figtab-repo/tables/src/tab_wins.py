"""Paired comparison of REG-L with each competitor (C3) over the (response, p, d) cells of grid e3, on the same draws.
Reads results/summary/c3_pairs.csv (outcome = win / tie / loss of REG-L by the 95% paired-bootstrap interval of the RMSE difference).
Writes tables/tab_wins.tex (tabular body only)."""
import os
import pandas as pd

ROOT = os.path.join(os.path.dirname(__file__), "..", "..")
c = pd.read_csv(os.path.join(ROOT, "results", "summary", "c3_pairs.csv"))
ROWS = [("DM", "DM"), ("H0", "H\\'ajek, exact exposure ($\\delta=0$)"), ("H0.1", "H\\'ajek, $\\delta=0.1$"), ("H0.25", "H\\'ajek, $\\delta=0.25$"),
        ("H0.5", "H\\'ajek, $\\delta=0.5$"), ("H0.75", "H\\'ajek, $\\delta=0.75$"), ("H-declared", "H\\'ajek, declared $\\delta$"),
        ("H-oracle", "H\\'ajek, oracle $\\delta$"), ("REG-Q", "REG-Q"), ("REG-O", "REG-O (true shape; a bound)")]
L = ["\\footnotesize", "\\begin{tabular}{lrrrr}", "\\toprule", "competitor & REG-L wins & ties & REG-L loses & pairs \\\\", "\\midrule"]
for k, lab in ROWS:
    r = c[c.competitor == k].outcome.value_counts()
    w, t, l = (int(r.get(x, 0)) for x in ("win", "tie", "loss"))
    L.append(f"{lab} & {w} & {t} & {l} & {w + t + l} \\\\")
L += ["\\bottomrule", "\\end{tabular}"]
open(os.path.join(ROOT, "tables", "tab_wins.tex"), "w").write("\n".join(L) + "\n")
print(open(os.path.join(ROOT, "tables", "tab_wins.tex")).read())
