"""T2 (claim E4): regressions of log verified budget on the statistical margin and other regressors.

Reads regression_coef.csv (adjacent-pair claims, natural logs, 95% stratified cluster-bootstrap intervals).
Writes table2_regression.tex (models M0, M0c, M1, M1c; main text) and table2b_regression_full.tex (all models; appendix).
z_cl = gap / cluster-bootstrap SE (s5_cluster_se.csv). M2-M4 (SNR) are only in the full table: log z and log SNR are
collinear (r = 1.000 on Arena, 0.99 on NBA seasons, VIF up to 1e4, s5_collinearity.csv), so their coefficients are not separately identified.
Dataset-specific intercepts of the pooled fits are in the csv and not repeated here.
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "figures"))
import common as C

A = C.args(__doc__)
co = C.read(A.results, "regression_coef.csv")
SCOPE = {"pooled": "Pooled, dataset intercepts", "nba_seasons": "NBA single seasons", "arena55k": "Arena 55k"}
COLS = [("log_z", r"$\log z$"), ("log_zc", r"$\log z_{\rm cl}$"), ("log_snr", r"$\log$ SNR"), ("log_gap", r"$\log$ gap"), ("log_n_pair_involving", r"$\log n_{\rm pair}$")]


def cell(sub, term):
    r = sub[sub.term == term]
    if r.empty:
        return "--"
    r = r.iloc[0]
    return f"{r.coef:.2f} [{r.ci_lo:.2f}, {r.ci_hi:.2f}]".replace("-", "$-$")


def label(m):
    code, rest = m.split(" ", 1)
    for a, b in [("log z_cluster", r"$z_{\rm cl}$"), ("log z", "$z$"), ("log snr", "SNR"), ("log n_pair", r"$n_{\rm pair}$"), ("log gap", "gap")]:
        rest = rest.replace(a, b)
    return f"{code}: {rest}"


def build(models, cols):
    lines = [r"\begin{tabular}{ll" + "c" * len(cols) + r"rr}", r"\toprule",
             "Fit & Model & " + " & ".join(c[1] for c in cols) + r" & $R^2$ & claims \\", r"\midrule"]
    for si, scope in enumerate(SCOPE):
        for mi, m in enumerate(models):
            sub = co[(co.scope == scope) & (co.model == m)]
            if sub.empty:
                continue
            r0 = sub.iloc[0]
            lines.append(" & ".join([SCOPE[scope] if mi == 0 else "", label(m)]
                                    + [cell(sub, t) for t, _ in cols] + [f"{r0.r2:.2f}", f"{int(r0.n_claims)}"]) + r" \\")
        if si < len(SCOPE) - 1:
            lines.append(r"\midrule")
    lines += [r"\bottomrule", r"\end{tabular}", ""]
    return "\n".join(lines)


models = list(co.model.unique())
main = [m for m in models if m.split(" ")[0] in ("M0", "M0c", "M1", "M1c")]
for name, ms in [("table2b_regression_full.tex", models), ("table2_regression.tex", main)]:
    cols = [c for c in COLS if ((co.term == c[0]) & co.model.isin(ms)).any()]
    if ms is main:  # one slope column: log z for M0/M1, log z_cl for M0c/M1c
        co.loc[co.term == "log_zc", "term"] = "log_z"
        cols = [(t, r"slope on $\log z$ ($z_{\rm cl}$ in M0c, M1c)" if t == "log_z" else l) for t, l in cols if t != "log_zc"]
    open(os.path.join(A.out, name), "w").write(build(ms, cols))
C.record_inputs(A.out, "table2_regression.tex", [os.path.join(A.results, "regression_coef.csv")])
C.record_inputs(A.out, "table2b_regression_full.tex", [os.path.join(A.results, "regression_coef.csv")])
