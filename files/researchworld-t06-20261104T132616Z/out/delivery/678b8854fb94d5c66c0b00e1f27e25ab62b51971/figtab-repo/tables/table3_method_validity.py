"""T3 (claim E6): how far each search method or estimate is from the best verified budget, on the claims where all were run.

Reads method_validity.csv (ratio_to_best_verified = budget of the method / smallest verified budget found by any method).
`verified = False` rows (the linearised influence estimate) are predictions, not witnesses; a ratio below 1 means the
estimate undershoots the budget that an exact refit confirms. Writes table3_method_validity.tex.
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "figures"))
import common as C

A = C.args(__doc__)
m = C.read(A.results, "method_validity.csv")
NAME = {
    "influence_linearised_estimate": "Influence estimate (linearised, not refitted)",
    "one_shot_top_k_verified": "One-shot influence ranking + exact refit",
    "greedy_verified_unpolished": "Greedy with exact refits",
    "greedy_polished_verified": "Greedy + swap/drop polish (used)",
    "heuristic_direct_pair_removal": "Heuristic: remove the pair's own decisive comparisons",
    "heuristic_own_wins_removal": "Heuristic: remove the leader's wins",
}
rows = []
for k, name in NAME.items():
    s = m[m.method == k].ratio_to_best_verified.dropna()
    if s.empty:
        continue
    rows.append(" & ".join([name, str(len(s)), f"{100 * (s <= 1 + 1e-9).mean():.0f}\\%", f"{s.median():.2f}", f"{s.quantile(0.9):.2f}", f"{s.max():.2f}",
                            "no" if k.startswith("influence") else "yes"]) + r" \\")
tex = "\n".join([r"\begin{tabular}{lrrrrrc}", r"\toprule",
                 r"Method & Claims & Equal to best & Median ratio & 90th pct & Max & Verified \\", r"\midrule",
                 *rows, r"\bottomrule", r"\end{tabular}", ""])
open(os.path.join(A.out, "table3_method_validity.tex"), "w").write(tex)
C.record_inputs(A.out, "table3_method_validity.tex", [os.path.join(A.results, "method_validity.csv")])
