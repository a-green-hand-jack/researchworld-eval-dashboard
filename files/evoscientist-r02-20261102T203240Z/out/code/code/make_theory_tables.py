"""LaTeX fragments from results/theory_*.csv  ->  tables/theory_*.tex"""
import pandas as pd, numpy as np
g = pd.read_csv("results/theory_gini_cond.csv")
L = [r"\begin{tabular}{rl|ccccc|ccccc}", r"\toprule",
     r" & & \multicolumn{5}{c|}{simulated (Dirichlet)} & \multicolumn{5}{c}{Gaussian approx.} \\",
     r"$\phi$ & score & Q1 & Q2 & Q3 & Q4 & Q5 & Q1 & Q2 & Q3 & Q4 & Q5 \\", r"\midrule"]
for phi in [3, 20, 100]:
    for sc in ["L2", "L2/sqrtGini"]:
        d = g[(g.phi == phi) & (g.score == sc)].sort_values("bin")
        name = "$L_2$" if sc == "L2" else r"$L_2/\sqrt{G}$"
        L.append(f"{phi} & {name} & " + " & ".join(f"{v:.3f}" for v in d.cov_emp) + " & " + " & ".join(f"{v:.3f}" for v in d.cov_gauss) + r" \\")
L += [r"\bottomrule", r"\end{tabular}"]
open("tables/theory_gini.tex", "w").write("\n".join(L))
v = pd.read_csv("results/theory_aitchison_volume.csv")
L = [r"\begin{tabular}{rrr}", r"\toprule", r"$\varepsilon$ & $A(R\cap\{\min p\ge\varepsilon\})$ & increment per decade \\", r"\midrule"]
for _, r in v.iterrows():
    inc = "" if np.isnan(r.increment_per_decade) else f"{r.increment_per_decade:.4f}"
    L.append(f"$10^{{{int(round(np.log10(r.eps)))}}}$ & {r.volA:.4f} & {inc} \\\\")
L += [r"\bottomrule", r"\end{tabular}"]
open("tables/theory_volume.tex", "w").write("\n".join(L))
m = pd.read_csv("results/theory_gini_moment.csv")
L = [r"\begin{tabular}{rcc}", r"\toprule", r"$\phi$ & $\mathbb E\|y-\mu\|^2$ (simulated) & $\overline{G(\mu)}/(\phi+1)$ \\", r"\midrule"]
for _, r in m.iterrows():
    L.append(f"{int(r.phi)} & {r.mean_s2_emp:.4f} & {r.mean_s2_formula:.4f} \\\\")
L += [r"\bottomrule", r"\end{tabular}"]
open("tables/theory_moment.tex", "w").write("\n".join(L))
print("ok")
j = pd.read_csv("results/theory_jacobian.csv")
L = [r"\begin{tabular}{rr}", r"\toprule", r"$K$ & max relative error \\", r"\midrule"]
for K, d in j.groupby("K"):
    L.append(f"{K} & {d.rel_err.max():.1e} \\\\")
L += [r"\bottomrule", r"\end{tabular}"]
open("tables/theory_jac.tex", "w").write("\n".join(L))
