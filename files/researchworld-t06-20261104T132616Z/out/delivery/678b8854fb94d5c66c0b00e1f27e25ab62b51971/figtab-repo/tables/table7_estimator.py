"""T7 (claim E7): sensitivity of the headline budgets to the estimator.

Reads s5_estimator.csv (greedy verified removal budget per claim and variant: base = lambda 1 with ties as half a win; lam_1e-6 =
almost unregularised; drop_ties = tied comparisons removed; tie_wl = a tie counted as one win and one loss) and s5_estimator_rank.csv
(top-1 identity, overlap of the claim window, Kendall tau on the base window against the base fit). Per data set and variant: C1 budget,
median budget over the adjacent-pair claims (C2) with its range, whether the top-1 participant is the same as in the base fit (otherwise the new leader is named), and tau.
Writes table7_estimator.tex.
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "figures"))
import common as C

A = C.args(__doc__)
e = C.read(A.results, "s5_estimator.csv", secondary=True)
r = C.read(A.results, "s5_estimator_rank.csv", secondary=True)
e = e[~e.unit.astype(str).str.endswith(C.SECONDARY_SUFFIX)]
VAR = {"base": "baseline ($\\lambda=1$, tie = half a win)", "lam_1e-6": "$\\lambda=10^{-6}$", "drop_ties": "ties removed", "tie_wl": "tie = one win + one loss"}
rows = []
for u in ["arena55k", "mt_human", "mt_gpt4", "nba_all"]:
    first = True
    for v in VAR:
        d = e[(e.unit == u) & (e.variant == v)]
        rk = r[(r.dataset == u) & (r.variant == v)]
        if d.empty:
            continue
        c1 = d[d.claim == "c1"].budget.iloc[0]
        c2 = d[d.claim.str.startswith("c2")]
        rows.append(" & ".join([C.SHORT_LABEL[u] if first else "", VAR[v], f"{c1:g}", f"{c2.budget.median():g} [{c2.budget.min():g}--{c2.budget.max():g}]",
                                "yes" if bool(rk.top1_same.iloc[0]) else "no: " + str(rk.top1.iloc[0]), f"{rk.tau_vs_base_window.iloc[0]:.2f}" if not rk.empty else "--"]) + r" \\")
        first = False
    rows.append(r"\midrule")
tex = "\n".join([r"\begin{tabular}{llrclc}", r"\toprule",
                 r"Data & Estimator & C1 budget & C2 median [min--max] & top-1 unchanged & Kendall $\tau$, window \\", r"\midrule", *rows[:-1], r"\bottomrule", r"\end{tabular}", ""])
open(os.path.join(A.out, "table7_estimator.tex"), "w").write(tex)
C.record_inputs(A.out, "table7_estimator.tex", [os.path.join(A.results, f) for f in ["s5_estimator.csv", "s5_estimator_rank.csv"]])
