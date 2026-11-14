"""T0 (headline): verified adversarial removal budgets per dataset.

Reads adv_budgets.csv, exact ties excluded. C1 = top-1 claim (for NBA single seasons: median over the seasons); C2 = adjacent-pair
claims (median [min, max] over all claims of the data set; for NBA single seasons over all claims of the 68 seasons); z = gap / bootstrap SE
of the gap (iid resampling of comparisons / cluster bootstrap, s5_cluster_se.csv); share of the pair's own comparisons = k / (comparisons involving either participant); verified = share of claims for which an exact refit confirmed the
flip. The 95% intervals of the C1 budget and of the median C2 budget are percentile intervals over dataset-bootstrap resamples
(s5_budget_intervals.csv; 100-200 resamples, claims re-defined on each resample's own ranking). Writes table0_headline.tex.
"""
import math
import os
import sys

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "figures"))
import common as C

A = C.args(__doc__)
a = C.read(A.results, "adv_budgets.csv")
a = a[~a.exact_tie].copy()
cl = C.read(A.results, "s5_cluster_se.csv").rename(columns={"unit": "dataset", "claim": "claim_id"})[["dataset", "claim_id", "z_cluster"]]
a = a.merge(cl, on=["dataset", "claim_id"], how="left")
assert a[a.claim_type == "C2"].z_cluster.notna().all()
a["group"] = a.dataset.where(a.dataset.isin(C.BASE_UNITS), "nba_seasons")
iv = C.read(A.results, "s5_budget_intervals.csv").set_index(["dataset", "statistic"])


def interval(g, stat):
    """95% interval over dataset-bootstrap resamples (s5_budget_intervals.csv); not available for the pool of NBA seasons."""
    if (g, stat) not in iv.index:
        return "--"
    r = iv.loc[(g, stat)]
    return f"[{math.floor(r.lo95)}, {math.ceil(r.hi95)}]"  # outward-rounded to integers


rows = []
for g in ["arena55k", "mt_human", "mt_gpt4", "nba_all", "nba_seasons"]:
    d = a[a.group == g]
    c1 = d[d.claim_type == "C1"]
    c2 = d[d.claim_type == "C2"]
    c1_txt = f"{c1.budget.median():g} ({100 * c1.budget_frac_N.median():.2f}\\%)"
    if g == "nba_seasons":
        c1_txt = "median " + c1_txt
    rows.append(" & ".join([
        C.SHORT_LABEL[g], str(c1.dataset.nunique()) if g == "nba_seasons" else "1", c1_txt, interval(g, "c1"),
        f"{c2.budget.median():g}", interval(g, "median_c2"), f"{c2.budget.min():g}--{c2.budget.max():g}",
        f"{100 * c2.budget_frac_N.median():.3f}\\%", f"{c2.z_gap.median():.2f} / {c2.z_cluster.median():.2f}", f"{100 * c2.budget_frac_pair.median():.1f}\\%",
        f"{100 * d.verified.mean():.0f}\\%"]) + r" \\")
tex = "\n".join([r"\begin{tabular}{lrccccccccc}", r"\toprule",
                 r" & Data & \multicolumn{2}{c}{C1 budget} & \multicolumn{3}{c}{C2 budget (comparisons)} & C2 median & median & C2 median, & \\",
                 r"\cmidrule(lr){3-4}\cmidrule(lr){5-7}",
                 r"Dataset & sets & count (\% of $N$) & 95\% interval & median & 95\% interval & min--max & \% of $N$ & $z$ iid / cluster & \% of pair's comparisons & verified \\",
                 r"\midrule", *rows, r"\bottomrule", r"\end{tabular}", ""])
open(os.path.join(A.out, "table0_headline.tex"), "w").write(tex)
C.record_inputs(A.out, "table0_headline.tex", [os.path.join(A.results, f) for f in ["adv_budgets.csv", "s5_budget_intervals.csv", "s5_cluster_se.csv"]])
