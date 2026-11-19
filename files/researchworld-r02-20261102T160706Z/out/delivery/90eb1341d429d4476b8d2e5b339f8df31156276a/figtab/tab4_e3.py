"""Table 4 (claim C8): CIFAR-10H human label distributions as a composition-valued response (alpha=0.1, n_cal=1000, T=1, 12-epoch CNN).
Input: results/e3_summary.csv (mean and 95% t-CI over random sigma/cal/test splits).  Columns:
cov = marginal coverage; mass = pool_frac (mean share of a pool of other images' human distributions inside the region; lower = more informative; defined for every K);
ambig = coverage in the least-covered of 5 equal-mass bins of the entropy of the human distribution (an outcome-conditional diagnostic); conf = same for bins of the CNN's top-1 probability;
wsc = worst-slab coverage.  80.6% of the entries of the human distributions are exact zeros: scores take tied values, so only the lower bound 1-alpha holds.
"""
from common import *

S = pd.read_csv(os.path.join(EXP, "results", "e3_summary.csv"))
g = S[(S.logits == "cnn_logits_ep12.npy") & (S["T"] == 1.0) & (S.n_cal == 1000)].set_index("method")
cols = [("cov10", "cov.", 3), ("pool_frac", "mass", 3), ("ambig_min", "ambig. min", 3), ("conf_min", "conf. min", 3), ("wsc", "wsc", 3)]
lines = [r"\begin{tabular}{llccccc}", r"\toprule", "score & scheme & " + " & ".join(n for _, n, _ in cols) + r" \\ \midrule"]
for s in ["l2", "l1", "linf", "hell", "kl", "ait"]:
    for v, vl in [("", "split"), ("_n", "normalised"), ("_m", "Mondrian")]:
        r = g.loc[s + v]
        cells = [pm(r[c], r[c + "_lo"], r[c + "_hi"], nd) for c, _, nd in cols]
        lines.append(" & ".join([SCORE_LAB[s] if v == "" else "", vl] + cells) + r" \\")
    if s != "ait":
        lines.append(r"\addlinespace[2pt]")
lines += [r"\bottomrule", r"\end{tabular}"]
write_table("\n".join(lines) + "\n", "tab4_e3_cifar10h.tex")
