"""T3b (claim E6): the search against exhaustive enumeration on small MT-Bench-human subsamples.

Reads method_validity_exhaustive.csv (900 adjacent-pair claims: 5 per instance, 60 instances at each of m = 60, 80, 100; see
results/README.md for how the instances were drawn). Rows: exact minimum k found by enumerating all removal sets of size <= 5 (rows 1-5), and
the claims for which no set of size <= 5 flips the pair (censored). Cells: number of claims where the method returned exactly the
exact minimum. No method returned less than the exact minimum (it cannot). For censored claims the enumeration only shows
that the budget exceeds 5; the cells give the median [min, max] budget returned by each method. Writes table3b_exhaustive.tex.
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "figures"))
import common as C

A = C.args(__doc__)
m = C.read(A.results, "method_validity_exhaustive.csv")
e = m[m.exact.notna()]
c = m[m.exact.isna()]
assert (e[["greedy", "greedy_polish", "oneshot"]].values >= e.exact.values[:, None]).all()
assert (e.greedy_polish == e.exact).eq(e.greedy_polish_equals_exact).all()
rows = []


def line(name, d, ex):
    return " & ".join([name, str(len(d)), *[f"{int((d[k] == d.exact).sum())}" for k in ["greedy_polish", "greedy", "oneshot"]]]) + r" \\"


for k in sorted(e.exact.unique()):
    d = e[e.exact == k]
    rows.append(line(f"exact minimum {int(k)}", d, True))
rows.append(r"\midrule")
rows.append(line(r"all with exact minimum $\le 5$", e, True))
rows.append(" & ".join([r"no flip with $\le 5$ removals", str(len(c)), *[f"{g.median():g} [{g.min():g}, {g.max():g}]" for g in [c.greedy_polish, c.greedy, c.oneshot]]]) + r" \\")
tex = "\n".join([r"\begin{tabular}{lrrrr}", r"\toprule",
                 r" & & \multicolumn{3}{c}{claims where the method returns the exact minimum} \\", r"\cmidrule(lr){3-5}",
                 r"Claims grouped by & Claims & Greedy + polish (used) & Greedy, unpolished & One-shot ranking \\", r"\midrule", *rows,
                 r"\bottomrule", r"\end{tabular}", ""])
open(os.path.join(A.out, "table3b_exhaustive.tex"), "w").write(tex)
C.record_inputs(A.out, "table3b_exhaustive.tex", [os.path.join(A.results, "method_validity_exhaustive.csv")])
