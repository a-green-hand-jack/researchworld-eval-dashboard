"""Table 2 (table*, C4): what certification costs and what it gives up, at k=3, delta=0.1.
Per rule, range over the six dataset x model groups (per-group values in tabA_certificates.tex).
Certificate columns (results/certificate_coverage.csv): share of runs certified at some stage of the 7-stage Covert-Lee
schedule, P(exact | certified) on fresh reruns, pooled correct rate of the delivered run, mean coalitions per run (uncertified
runs delivered at the maximum).
Against the oracle (results/oracle_tightness.csv; 30 stratified instances per s0 cell, R~200 reruns; stage x4; these shares
are conditional on the strata, not population rates): share of oracle-certifiable instances (r_3(x;B) >= 0.9) the rule certifies,
and share of the others it certifies.
Cost at equal reliability (results/cost_at_equal_reliability.csv): the cheapest fixed budget on the grid whose pooled
P(top-3 exact) reaches the certificate's delivered rate, for the same estimator (fixed Covert-Lee stage), for KernelSHAP with
l1_reg=False, and for the shipped KernelSHAP default; 'n/a' = no fixed budget up to x16 reaches the rate."""
import os, json
import numpy as np, pandas as pd
import figstyle as fs, common as C

K, DELTA = 3, 0.1
a = C.args(__doc__)
cov = pd.read_csv(os.path.join(C.RESULTS, "certificate_coverage.csv"))
orc = pd.read_csv(os.path.join(C.RESULTS, "oracle_tightness.csv"))
cost = pd.read_csv(os.path.join(C.RESULTS, "cost_at_equal_reliability.csv"))
RULES = [("naive", "plug-in SE, no correction"), ("bonf", "SE + Bonferroni"), ("maxt", "SE + max-$t$"), ("split", "split-half"), ("shapk", "SHAP@k-style")]
hit = lambda d: d[(d.k == K) & np.isclose(d.delta, DELTA)]
cov, orc, cost = hit(cov), hit(orc), hit(cost)


def rng(x, f="{:.2f}", scale=1):
    x = np.asarray(x, dtype=float) / scale
    if np.all(np.isnan(x)):
        return "n/a"
    lo, hi = f.format(np.nanmin(x)), f.format(np.nanmax(x))
    return lo if lo == hi else f"{lo}--{hi}"


def with_na(d, f="{:.1f}", scale=1e3):
    """range of `fixed_cost` over groups; '$\\leq$' when the budget is the grid floor (x0.25), so the true minimum may be lower"""
    x = d.fixed_cost.values.astype(float)
    n_na = int(np.isnan(x).sum())
    if n_na == len(x):
        return "n/a"
    floor = bool((d.fixed_budget.dropna() == "x0.25").all())
    return ("$\\leq$" if floor else "") + rng(x, f, scale) + (f" ({n_na} n/a)" if n_na else "")


SHORT = {"naive": "plug-in SE", "bonf": "Bonferroni", "maxt": "max-$t$", "split": "split-half", "shapk": "SHAP@k"}
cols = []
for r, _ in RULES:
    c = cov[cov.rule == r]
    o = orc[(orc.rule == r) & (orc.stage == "x4")]
    k = cost[cost.rule == r]
    same = k[k.arm == "covert_lee"]; l1 = k[k.arm == "kshap_l1off"]; sh = k[k.arm == "kshap_default"]
    cols.append([rng(c.certified_share), rng(c.correct_given_certified), rng(c.pooled_correct_delivered),
                 rng(o.cert_share_oracle_ok), rng(o.cert_share_oracle_not_ok),
                 rng(c.mean_cost_all, "{:.0f}", 1e3), with_na(same, "{:.0f}"), with_na(l1, "{:.2f}"), with_na(sh, "{:.2f}")])
ROWS = [("\\multicolumn{6}{@{}l}{\\emph{certificate, fresh reruns}} \\\\", None),
        ("share of runs certified", 0), ("P(exact $\\mid$ certified)", 1), ("delivered run correct", 2),
        ("\\multicolumn{6}{@{}l}{\\emph{share of instances certified at $\\times4$ (stratified subset)}} \\\\", None),
        ("where the oracle certifies ($r_3\\geq 0.9$)", 3), ("where it does not", 4),
        ("\\multicolumn{6}{@{}l}{\\emph{coalitions to reach the delivered rate ($\\times10^3$)}} \\\\", None),
        ("this certificate", 5), ("fixed budget, same estimator", 6), ("fixed, KernelSHAP \\texttt{l1\\_reg=False}", 7), ("fixed, KernelSHAP shipped default", 8)]
lines = ["\\begin{tabular}{@{}l" + "c" * len(RULES) + "@{}}", "\\toprule", " & " + " & ".join(SHORT[r] for r, _ in RULES) + " \\\\", "\\midrule"]
for lab, idx in ROWS:
    lines.append(lab if idx is None else f"\\hspace{{0.8em}}{lab} & " + " & ".join(c[idx] for c in cols) + " \\\\")
lines += ["\\bottomrule", "\\end{tabular}"]
out = os.path.join(C.outdir(a), "tab2_certificates.tex")
open(out, "w").write("\n".join(lines) + "\n")
json.dump({"inputs": ["certificate_coverage.csv", "oracle_tightness.csv", "cost_at_equal_reliability.csv"], "groups": sorted(cov.group.unique().tolist()),
           "oracle_cells": sorted(orc.cell.unique().tolist()), "figtab_commit": C.provenance([])["figtab_commit"]}, open(out.replace(".tex", ".json"), "w"), indent=1)
print("wrote", out)
