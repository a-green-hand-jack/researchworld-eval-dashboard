"""Appendix table (C4): the per-cell values behind Table 2 (k=3, delta=0.1), one row per dataset x model and rule.
Columns: share of runs certified, P(exact | certified) with its cluster-bootstrap 95% CI, delivered-correct rate, mean coalitions per run,
and the cheapest fixed budget reaching the delivered rate for the same estimator (Covert-Lee stage) and for KernelSHAP with l1_reg=False
(coalitions; <= marks the grid floor x0.25; n/a = none up to x16).
Inputs: results/certificate_coverage.csv, results/cost_at_equal_reliability.csv."""
import os, json
import numpy as np, pandas as pd
import common as C

K, DELTA = 3, 0.1
a = C.args(__doc__)
cov = pd.read_csv(os.path.join(C.RESULTS, "certificate_coverage.csv"))
cost = pd.read_csv(os.path.join(C.RESULTS, "cost_at_equal_reliability.csv"))
hit = lambda d: d[(d.k == K) & np.isclose(d.delta, DELTA)]
cov, cost = hit(cov), hit(cost)
RULES = [("naive", "plug-in SE"), ("bonf", "Bonferroni"), ("maxt", "max-$t$"), ("split", "split-half"), ("shapk", "SHAP@k")]


def fx(g, rule, arm):
    r = cost[(cost.group == g) & (cost.rule == rule) & (cost.arm == arm)]
    if r.empty or r.fixed_cost.isna().all():
        return "n/a"
    return ("$\\leq$" if r.fixed_budget.iloc[0] == "x0.25" else "") + f"{r.fixed_cost.iloc[0]:.0f}"


lines = ["\\begin{tabular}{@{}llccccrr@{}}", "\\toprule",
         "Dataset, model & Rule & certified & P(exact $\\mid$ certified) & delivered correct & coalitions & fixed Covert--Lee & fixed \\texttt{l1\\_reg=False} \\\\", "\\midrule"]
for gi, g in enumerate(sorted(cov.group.unique())):
    p = g.split("_")
    name = f"{C.DATA_LABEL.get(p[0], p[0])} {C.MODEL_LABEL.get(p[2], p[2])}"
    if gi:
        lines.append("\\addlinespace[2pt]")
    for ri, (r, lab) in enumerate(RULES):
        c = cov[(cov.group == g) & (cov.rule == r)].iloc[0]
        lines.append(f"{name if ri == 0 else ''} & {lab} & {c.certified_share:.2f} & {c.correct_given_certified:.3f} [{c.ci_lo:.3f}, {c.ci_hi:.3f}] & "
                     f"{c.pooled_correct_delivered:.2f} & {c.mean_cost_all:.0f} & {fx(g, r, 'covert_lee')} & {fx(g, r, 'kshap_l1off')} \\\\")
lines += ["\\bottomrule", "\\end{tabular}"]
out = os.path.join(C.outdir(a), "tabA_certificates.tex")
open(out, "w").write("\n".join(lines) + "\n")
json.dump({"inputs": ["certificate_coverage.csv", "cost_at_equal_reliability.csv"], "figtab_commit": C.provenance([])["figtab_commit"]}, open(out.replace(".tex", ".json"), "w"), indent=1)
print("wrote", out)
