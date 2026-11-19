"""T6 (claims E4/E7): how much margin the adjacent-pair claims have, and what the claim "the published intervals separate the pair" costs.

Reads s5_z_shares.csv (shares of adjacent-pair claims with z < 1 and z < 2, with the iid bootstrap SE and with a cluster bootstrap SE
(clusters: MT-Bench question, Arena identical prompt text, NBA week of the season / season for the pooled fit); median SE ratio cluster/iid)
and s5_published_summary.csv (claims on the published output: "the 95% bootstrap interval of the score difference of adjacent pair r excludes 0";
budget = smallest removal after which the claim is false when the perturbed counts are re-bootstrapped; compared with the point-gap budget of
the same pairs; NBA: a sample of seven seasons, every tenth from 1950). C1' (columns 10-11): the top participant's 95% bootstrap rank interval is [1, 1] (p_rank1 >= 0.975): number of data sets/seasons where it holds at base, and the median removal budget over those (re-bootstrapped). Writes table6_published.tex.
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "figures"))
import common as C

A = C.args(__doc__)
z = C.read(A.results, "s5_z_shares.csv").set_index("dataset")
p = C.read(A.results, "s5_published_summary.csv").set_index("dataset")
pct = lambda x: f"{100 * x:.0f}\\%"
rows = []
for g, pg in [("arena55k", "arena55k"), ("mt_human", "mt_human"), ("mt_gpt4", "mt_gpt4"), ("nba_all", "nba_all"), ("nba_seasons", "nba_seasons_sample")]:
    zz, pp = z.loc[g], p.loc[pg]
    name = C.SHORT_LABEL[g] + (f" (right block: {int(pp.units)} sampled seasons)" if g == "nba_seasons" else "")
    rows.append(" & ".join([
        name, str(int(zz.n_claims)), pct(zz.share_z_lt1_iid), pct(zz.share_z_lt1_cluster), f"{zz.median_se_ratio:.2f}",
        f"{int(pp.adjacent_pairs)}", pct(pp.share_ci_separated),
        f"{pp.median_budget_ci_separated:g}" if pp.ci_separated_at_base else "--",
        f"{pp.median_budget_point_same_pairs:g}" if pp.ci_separated_at_base else "--",
        f"{int(pp.c1prime_holds_at_base)}/{int(pp.c1prime_units)}",
        f"{pp.median_c1prime_budget_holding:g}" if pp.c1prime_holds_at_base else "--"]) + r" \\")
tex = "\n".join([r"\begin{tabular}{lrrrcrrrrrr}", r"\toprule",
                 r" & \multicolumn{4}{c}{Margin: adjacent pairs with $z<1$} & \multicolumn{4}{c}{Claim: published 95\% intervals separate the pair} & \multicolumn{2}{c}{C1$^\prime$: top-1 rank interval is $[1,1]$} \\",
                 r"\cmidrule(lr){2-5}\cmidrule(lr){6-9}\cmidrule(lr){10-11}",
                 r"Dataset & Pairs & iid SE & cluster SE & SE ratio & Pairs & separated & median $k$, interval claim & $k$, same pairs, point gap & holds at base & median $k$ to fail \\", r"\midrule", *rows,
                 r"\bottomrule", r"\end{tabular}", ""])
open(os.path.join(A.out, "table6_published.tex"), "w").write(tex)
C.record_inputs(A.out, "table6_published.tex", [os.path.join(A.results, f) for f in ["s5_z_shares.csv", "s5_published_summary.csv"]])
