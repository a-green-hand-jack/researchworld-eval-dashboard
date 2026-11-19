"""LaTeX tables for the paper, generated from /work/results/summary_E*.csv.

Writes /work/paper/tables/*.tex. Every number in a table is copied from the summary
files; nothing is typed by hand.
"""
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, "/work/code")
RES = "/work/results"
TAB = "/work/paper/tables"
GRAPHS = {"stanford3": "Stanford3", "egofb": "ego-Facebook", "ba_n5000_m3": "BA"}
MECH = {"M0": "M0 null", "M1": "M1 linear", "M2": "M2 cubic", "M3": "M3 saturating",
        "M4": "M4 2-hop", "M5": "M5 threshold", "M6": "M6 shocks"}


def f2(x):
    return "--" if pd.isna(x) else f"{x:.2f}"


def cov(x):
    return "--" if pd.isna(x) else f"{x:.2f}"


def pick(s, **kw):
    m = np.ones(len(s), dtype=bool)
    for k, v in kw.items():
        m &= (s[k] == v).values
    return s[m]


def table_main(s1):
    """Bernoulli p=0.5, Stanford3: bias by estimator, plus R2 precision and coverage."""
    rows = []
    for m in MECH:
        d = pick(s1, graph="stanford3", design="bern", p=0.5, mech=m)
        dim = pick(d, estimator="dim").iloc[0]
        r2 = pick(d, estimator="r2").iloc[0]
        r4 = pick(d, estimator="r4").iloc[0]
        r5 = pick(d, estimator="r5").iloc[0]
        rows.append(f"{MECH[m]} & {r2.truth:.0f} & {f2(dim.bias)} & {f2(r2.bias)} & {f2(r2.sd)} & "
                    f"{cov(r2.cov_hc1)} & {cov(r2.cov_cr1)} & {f2(r4.bias)} & {f2(r5.bias)} \\\\")
    body = "\n".join(rows)
    tex = r"""\begin{tabular}{lrrrrrrrr}
\toprule
 & & \multicolumn{1}{c}{DiM} & \multicolumn{4}{c}{OLS, 1-hop ($z,f_1$)} & \multicolumn{1}{c}{OLS, quad.} & \multicolumn{1}{c}{GBM} \\
\cmidrule(lr){4-7}
Mechanism & GATE & bias & bias & SD & cov.\ HC1 & cov.\ CR1 & bias & bias \\
\midrule
""" + body + r"""
\bottomrule
\end{tabular}
"""
    open(f"{TAB}/t_main_stanford3.tex", "w").write(tex)


def table_designs(s1):
    """Bernoulli vs graph-cluster randomisation on Stanford3 for the 1-hop OLS."""
    rows = []
    for m in ["M1", "M2", "M3", "M5", "M6"]:
        for design, p in [("bern", 0.1), ("gcr", 0.1), ("bern", 0.5), ("gcr", 0.5)]:
            d = pick(s1, graph="stanford3", mech=m, design=design, p=p)
            r2 = pick(d, estimator="r2").iloc[0]
            r4 = pick(d, estimator="r4").iloc[0]
            lab = ("Bernoulli" if design == "bern" else "graph-cluster") + f", $p={p}$"
            rows.append(f"{MECH[m]} & {lab} & {f2(r2.bias)} & {f2(r2.sd)} & {f2(r2.rmse)} & "
                        f"{cov(r2.cov_cr1)} & {f2(r4.bias)} & {f2(r4.sd)} \\\\")
        rows.append(r"\midrule")
    rows = rows[:-1]
    tex = r"""\begin{tabular}{llrrrrrr}
\toprule
 & & \multicolumn{4}{c}{OLS, 1-hop ($z,f_1$)} & \multicolumn{2}{c}{OLS, quad.} \\
\cmidrule(lr){3-6}\cmidrule(lr){7-8}
Mechanism & Design & bias & SD & RMSE & cov.\ CR1 & bias & SD \\
\midrule
""" + "\n".join(rows) + r"""
\bottomrule
\end{tabular}
"""
    open(f"{TAB}/t_designs.tex", "w").write(tex)


def table_all_e1(s1):
    """Appendix: every E1 setting, DiM and 1-hop OLS, plus quadratic and GBM bias."""
    rows = []
    for g in GRAPHS:
        for m in MECH:
            for design, p in [("bern", 0.1), ("bern", 0.3), ("bern", 0.5), ("gcr", 0.1), ("gcr", 0.5)]:
                d = pick(s1, graph=g, mech=m, design=design, p=p)
                if d.empty:
                    continue
                dim = pick(d, estimator="dim").iloc[0]
                r2 = pick(d, estimator="r2").iloc[0]
                r4 = pick(d, estimator="r4").iloc[0]
                r5 = pick(d, estimator="r5").iloc[0]
                dl = "B" if design == "bern" else "C"
                rows.append(f"{GRAPHS[g]} & {m} & {dl}, {p} & {f2(dim.bias)} & {f2(r2.bias)} & {f2(r2.sd)} & "
                            f"{cov(r2.cov_hc1)} & {cov(r2.cov_cr1)} & {f2(r4.bias)} & {f2(r5.bias)} \\\\")
    tex = r"""\begin{longtable}{lllrrrrrrr}
\caption{Every E1 setting: bias and coverage for the one-hop OLS, the quadratic OLS (quad.), and gradient boosting (GBM). Design: B = Bernoulli, C = graph-cluster randomization, followed by $p$. Coverage is for nominal 95\% intervals (HC1 and CR1); GBM has no interval. Truth is the GATE in Table~\ref{tab:mech}.} \label{tab:all}\\
\toprule
Graph & Mech. & Design, $p$ & DiM bias & OLS bias & OLS SD & cov.\ HC1 & cov.\ CR1 & quad.\ bias & GBM bias \\
\midrule
\endfirsthead
\multicolumn{10}{l}{\small Table \ref{tab:all} continued} \\
\toprule
Graph & Mech. & Design, $p$ & DiM bias & OLS bias & OLS SD & cov.\ HC1 & cov.\ CR1 & quad.\ bias & GBM bias \\
\midrule
\endhead
\bottomrule
\endfoot
""" + "\n".join(rows) + r"""
\end{longtable}
"""
    open(f"{TAB}/t_all_e1.tex", "w").write(tex)


def table_graphs():
    """Graph statistics (largest connected component) from prepare_graphs.py."""
    g = pd.read_csv(f"{RES}/graph_stats.csv")
    names = {"stanford3": "Stanford3", "egofb": "ego-Facebook", "ba_n5000_m3": "BA ($m=3$)",
             "er_n5000_d20": "ER, $\\bar d\\approx 20$"}
    rows = []
    for k, lab in names.items():
        r = g[g.name == k].iloc[0]
        rows.append(f"{lab} & {int(r.n):,} & {int(r.m):,} & {r.mean_deg:.1f} & {int(r.max_deg)} & "
                    f"{r.clustering:.3f} & {int(r.n_clusters)} \\\\")
    tex = r"""\begin{tabular}{lrrrrrr}
\toprule
Graph & Nodes & Edges & Mean deg. & Max deg. & Clustering & Clusters \\
\midrule
""" + "\n".join(rows) + r"""
\bottomrule
\end{tabular}
"""
    open(f"{TAB}/t_graphs.tex", "w").write(tex)


def table_mech():
    """Mechanisms: mean functions (must match gate/dgp.py) and the exact GATE."""
    from gate import dgp
    text = {
        "M0": r"$x+z$",
        "M1": r"$x+z+2f_1$",
        "M2": r"$x+z+4f_1^3$",
        "M3": r"$x+z+3\,(1-e^{-4f_1})/(1-e^{-4})$",
        "M4": r"$x+z+1.5f_1+1.5f_2$",
        "M5": r"$x+z+3\,\mathbf{1}\{f_1\ge 1/2\}$",
        "M6": r"$x+z+2f_1+u_{c(i)}$ (shock)",
    }
    rows = []
    for m in MECH:
        rows.append(f"{MECH[m]} & {text[m]} & {dgp.true_gate(m):.0f} \\\\")
    tex = r"""\begin{tabular}{llr}
\toprule
Mechanism & Mean function $\mu_m(z,f_1,f_2,x)$ (noise $N(0,1)$) & GATE \\
\midrule
""" + "\n".join(rows) + r"""
\bottomrule
\end{tabular}
"""
    open(f"{TAB}/t_mech.tex", "w").write(tex)


if __name__ == "__main__":
    table_graphs()
    table_mech()
    s1 = pd.read_csv(f"{RES}/summary_E1.csv")
    table_main(s1)
    table_designs(s1)
    table_all_e1(s1)
    print("tables written")
