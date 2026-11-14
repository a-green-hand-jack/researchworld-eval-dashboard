"""T4 (claim E7): median verified removal budget of the adjacent-pair claims under modelling variants.

Reads ablations_summary.csv (median budget share of N with its 95% percentile interval from a claim-level bootstrap of the median;
claims are not independent) and ablations.csv (for the per-season home-advantage variant, which has no summary row: median budget
only (marked $\\dagger$), over all verified claims of the single seasons, no interval). Cells: median budget in comparisons [interval of the
budget as % of N]; "--" = variant not run on that data set. Writes table4_ablations.tex.
"""
import os
import sys

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "figures"))
import common as C

A = C.args(__doc__)
s = C.read(A.results, "ablations_summary.csv", secondary=True)  # old claim set rows are the *_top20count datasets
ab = C.read(A.results, "ablations.csv")
assert not s.synthetic.any()
COLS = ["arena55k", "mt_human", "mt_gpt4", "nba_all", "nba_seasons"]
ROWS = [("baseline", "Baseline ($\\lambda=1$, ties = half a win)"), ("drop_ties", "Tied comparisons removed"), ("lam=0.01", "$\\lambda=0.01$"),
        ("lam=100.0", "$\\lambda=100$"), ("home_param", "Home-advantage parameter"), ("playoffs_incl", "Playoff games added"),
        ("claims=top10", "Arena: window of 10 ranks"),
        ("claims=top20_by_count", "Old claim set: 20 most-compared participants (Arena, NBA pooled)"),
        ("elig=n>=1000", "Arena: models with $\\ge 1000$ comparisons (39 claims)"), ("elig=all64", "Arena: all 64 models (63 claims)")]


def pct(x):
    return f"{100 * x:.2g}"


def cell(variant, col):
    if variant == "home_param":
        if col == "nba_all":
            col = "nba_all_home"
        elif col == "nba_seasons":
            h = ab[(ab.variant == "home_param") & ab.dataset.str.fullmatch(r"nba\d{4}_home") & ~ab.exact_tie & ab.flipped]
            return f"{h.budget.median():g}$^\\dagger$"
    if variant == "claims=top20_by_count" and col in ("arena55k", "nba_all"):
        col += "_top20count"
    r = s[(s.variant == variant) & (s.dataset == col)]
    if r.empty:
        return "--"
    r = r.iloc[0]
    return f"{r.median_budget:g} [{pct(r.ci_lo)}, {pct(r.ci_hi)}]"


n = {c: int(s[(s.variant == "baseline") & (s.dataset == c)].n_claims.iloc[0]) for c in COLS}
rows = [" & ".join([lab, *[cell(v, c) for c in COLS]]) + r" \\" for v, lab in ROWS]
n = {c: int(s[(s.variant == "baseline") & (s.dataset == c)].n_claims.iloc[0]) for c in COLS}
for v in ("elig=n>=1000", "elig=all64"):
    n[v] = int(s[s.variant == v].n_claims.iloc[0])
tex = "\n".join([r"\begin{tabular}{lccccc}", r"\toprule",
                 r"Variant & Arena 55k & MT-Bench human & MT-Bench GPT-4 & NBA pooled & NBA single seasons \\", r"\midrule",
                 *rows, r"\midrule", "Claims (baseline) & " + " & ".join(str(n[c]) for c in COLS) + r" \\", r"\bottomrule", r"\end{tabular}", ""])
open(os.path.join(A.out, "table4_ablations.tex"), "w").write(tex)
C.record_inputs(A.out, "table4_ablations.tex", [os.path.join(A.results, f) for f in ["ablations_summary.csv", "ablations.csv"]])
print({k: v for k, v in n.items()})
