"""T1 (claim E1): dataset summary. Reads dataset_summary.csv; writes table1_datasets.tex (booktabs, no float wrapper)."""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "figures"))
import common as C

A = C.args(__doc__)
d = C.read(A.results, "dataset_summary.csv")
NAME = {"arena55k": "Arena 55k", "mt_human": "MT-Bench human", "mt_gpt4": "MT-Bench GPT-4", "nba_all": "NBA, all seasons"}
rows = []
for r in d.itertuples():
    k = f"{r.K}" if r.K == r.K_eligible else f"{r.K} ({r.K_eligible})"
    rows.append(" & ".join([
        NAME[r.unit], C.DESIGN_LABEL[r.design], k, f"{r.N:,}".replace(",", r"\,"), f"{100 * r.tie_frac:.0f}\\%",
        f"{r.n_pairs_compared}/{r.n_pairs_possible}",
        f"{r.pair_count_min:g} / {r.pair_count_median:g} / {r.pair_count_max:g}",
    ]) + r" \\")
tex = "\n".join([
    r"\begin{tabular}{llrrrrr}", r"\toprule",
    r"Dataset & Design & $K$ & $N$ & Ties & Pairs seen & Pair count min / med / max \\", r"\midrule",
    *rows, r"\bottomrule", r"\end{tabular}", ""])
with open(os.path.join(A.out, "table1_datasets.tex"), "w") as f:
    f.write(tex)
C.record_inputs(A.out, "table1_datasets.tex", [os.path.join(A.results, "dataset_summary.csv")])
