"""T9 (claim E6): does randomised restarting of the search beat the deterministic greedy search?

Reads s5_restarts_summary.csv: 50 randomised restarts of the removal search per claim (C1 and the adjacent-pair claims of the window).
Columns: claims, claims where a restart found a smaller verified budget than the deterministic search used in the paper, claims where every
restart returns the same budget, the largest restart / deterministic ratio, the C1 budget of the deterministic search and the best restart.
Writes table9_restarts.tex.
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "figures"))
import common as C

A = C.args(__doc__)
s = C.read(A.results, "s5_restarts_summary.csv").set_index("unit")
rows = []
for u in ["arena55k", "mt_human", "mt_gpt4", "nba_all"]:
    r = s.loc[u]
    rows.append(" & ".join([C.SHORT_LABEL[u], f"{int(r.claims)}", f"{int(r.restarts_per_claim)}", f"{int(r.claims_where_a_restart_beat_det)}",
                            f"{int(r.claims_where_all_restarts_equal_det)}", f"{r.max_restart_over_det:.2f}", f"{r.c1_det:g}", f"{r.c1_restart_min:g}"]) + r" \\")
tex = "\n".join([r"\begin{tabular}{lrrrrrrr}", r"\toprule",
                 r"Data & Claims & Restarts & Restart beats search & All restarts equal search & max restart / search & C1 search & C1 best restart \\", r"\midrule",
                 *rows, r"\bottomrule", r"\end{tabular}", ""])
open(os.path.join(A.out, "table9_restarts.tex"), "w").write(tex)
C.record_inputs(A.out, "table9_restarts.tex", [os.path.join(A.results, "s5_restarts_summary.csv")])
