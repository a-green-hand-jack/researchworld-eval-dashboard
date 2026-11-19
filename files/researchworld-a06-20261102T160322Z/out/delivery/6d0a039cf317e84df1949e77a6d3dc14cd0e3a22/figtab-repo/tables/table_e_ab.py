"""Table E (Q1c, Q2a): decisions comparing two tuned systems A and B ('A beats B'), T0.
False-winner rate = share claiming A > B when A is not truly better; detection rate = share claiming it when A is truly better.
'point' compares the methods' estimates, 'lo' requires the lower bound of A to exceed B's estimate. Wilson 95% intervals over replicates.
Reads results/decisions_ab_t0.csv. Writes tables/table_e_ab.tex"""
import os, sys
import numpy as np, pandas as pd
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "figures"))
import common

d = pd.read_csv(common.path("decisions_ab_t0.csv"))
d = d[(d.margin_m == 0) & d.cell_A.str.endswith("rho=0.6|acc=0.3|proc=exhaustive") & d.cell_B.str.endswith("rho=0.6|acc=0.3|proc=exhaustive")]
for c in ("A", "B"):
    d[c] = d["cell_" + c].str.extract(r"(n=\d+\|K=\d+\|tau=[\d.]+)")
order = ["M0", "M1_f0.2", "M1_f0.5", "M1_f0.8", "M2", "M4_simult", "M4_cond", "M4_hybrid", "M5_eb", "M5_ladder"]
# columns: (A cell, B cell, regime, variant)
cols = [("n=200|K=200|tau=0.0", "n=200|K=5|tau=0.0", "A_not_better", "point"), ("n=200|K=200|tau=0.0", "n=200|K=5|tau=0.0", "A_not_better", "lo"),
        ("n=200|K=200|tau=0.1", "n=200|K=5|tau=0.1", "A_not_better", "point"), ("n=200|K=200|tau=0.1", "n=200|K=5|tau=0.1", "A_better", "point"),
        ("n=50|K=50|tau=0.0", "n=500|K=50|tau=0.0", "A_not_better", "point")]
head = [r"\shortstack{$\tau{=}0$, A: $K{=}200$ vs B: $K{=}5$\\ false winner, point}", r"\shortstack{same\\ false winner, lower bound}",
        r"\shortstack{$\tau{=}0.1$, same pair\\ false winner, point}", r"\shortstack{$\tau{=}0.1$, same pair\\ A truly better, point}",
        r"\shortstack{$\tau{=}0$, A: $n{=}50$ vs B: $n{=}500$\\ ($K{=}50$) false winner, point}"]
def cell(c, meth):
    x = d[(d.A == c[0]) & (d.B == c[1]) & (d.regime == c[2]) & (d.variant == c[3]) & (d.method == meth)]
    if x.empty: return "--"
    k, n = x.n_reject.sum(), x.n_reps.sum(); lo, hi = common.wilson(k, n)
    return rf"{100 * k / n:.1f} [{100 * lo:.1f}, {100 * hi:.1f}]"
lines = [r"\begin{tabular}{l" + "r" * len(cols) + "}", r"\toprule", "method & " + " & ".join(head) + r" \\", r"\midrule"]
for m in order:
    lines.append(m.replace("_", r"\_") + " & " + " & ".join(cell(c, m) for c in cols) + r" \\")
lines += [r"\bottomrule", r"\end{tabular}"]
open(f"{common.TOUT}/table_e_ab.tex", "w").write("\n".join(lines) + "\n")
