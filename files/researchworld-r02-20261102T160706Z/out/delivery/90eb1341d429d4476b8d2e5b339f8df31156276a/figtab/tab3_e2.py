"""Table 3 (claim C7): CIFAR-10 softmax label sets, alpha=0.1, n_cal=1000, T=1, 200 random cal/test splits of the 10,000 CIFAR-10 test images.
Input: results/e2_summary.csv (mean and 95% t-CI over splits, from scripts/aggregate.py), results/e2_ident_summary.csv (share of sets identical to LAC).
Two predictors: the CNN after 2 and after 12 epochs (test acc. 0.740 / 0.881).
"""
from common import *

S = pd.read_csv(os.path.join(EXP, "results", "e2_summary.csv"))
I = pd.read_csv(os.path.join(EXP, "results", "e2_ident_summary.csv"))
order = [("lac", "LAC"), ("lac_cc", "LAC, class-cond."), ("aps", "APS"), ("raps", "RAPS"), ("l2", "Brier / $L_2$"), ("l1", "$L_1$"),
         ("hell", "Hellinger"), ("kl", "KL"), ("ait1", r"Aitchison ($\varepsilon{=}0.1$)"), ("ait3", r"Aitchison ($\varepsilon{=}10^{-3}$)")]
cols = [("cov10", "cov.", 3), ("size10", "size", 3), ("classcov_min", "min class cov.", 3), ("sscv_min", "SSCV$^\\dagger$", 3), ("empty_frac", "empty", 3)]
lines = [r"\begin{tabular}{l" + "c" * (len(cols) + 1) + "}", r"\toprule",
         "method & " + " & ".join(n for _, n, _ in cols) + r" & = LAC \\"]
for lg, name in [("cnn_logits_ep12.npy", "CNN, 12 epochs (acc. 0.881)"), ("cnn_logits_ep2.npy", "CNN, 2 epochs (acc. 0.740)")]:
    g = S[(S.logits == lg) & (S["T"] == 1.0) & (S.n_cal == 1000)].set_index("method")
    ii = I[(I.logits == lg) & (I["T"] == 1.0) & (I.n_cal == 1000)].iloc[0]
    lines.append(r"\midrule" + "\n" + rf"\multicolumn{{{len(cols) + 2}}}{{l}}{{\emph{{{name}}}}} \\")
    for m, lab in order:
        r = g.loc[m]
        cells = [pm(r[c], r[c + "_lo"], r[c + "_hi"], nd) for c, _, nd in cols]
        same = "--" if m in ("lac", "lac_cc") else f"{ii['same_as_lac_' + m]:.3f}" if f"same_as_lac_{m}" in ii else "--"
        lines.append(" & ".join([lab] + cells + [same]) + r" \\")
lines += [r"\bottomrule", r"\end{tabular}"]
write_table("\n".join(lines) + "\n", "tab3_e2_labelsets.tex")
