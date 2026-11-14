"""Macro-average tables of the paper, built from figures/generated/*.csv and results/tables/tier1/*.csv.
Usage: python3 -I make_tables.py   (run from paper/)"""
import pandas as pd, numpy as np

G, R = "../figures/generated/", "../results/tables/tier1/"
ORDER = [("const", "B0 mean of sources"), ("random+mean", "B1 random"), ("strat+mean", "B2 stratified"),
         ("random+cal", "B3 random + calibration"), ("anchor+anchor", "Anchor points"), ("anchor+irt", "Anchor + IRT"),
         ("random+lowrank", "Random + low-rank"), ("omp+ridge", "P1 OMP + ridge"),
         ("strat+lowrank_dr", "P3 DR (stratified + low-rank + correction)"), ("strat+lowrank_eb", "P3 EB (shrunk correction)")]


def macro(kind, split):
    m = pd.read_csv(f"{G}fig_macro_curves.csv")
    m = m[(m.metric == kind) & (m.split_type == split) & (m.nbench == 13)]
    return m.set_index(["method", "n"])


def cell(m, meth, n, scale=1.0, d=2):
    if (meth, n) not in m.index:
        raise KeyError(f"missing macro cell {meth} n={n}")
    r = m.loc[(meth, n)]
    return f"{r['mean']*scale:.{d}f}\\,{{\\tiny$\\pm${(r.hi-r.lo)/2*scale:.{d}f}}}"


mae = {s: macro("mae", s) for s in ["random", "extrap"]}
spr = {s: macro("spearman", s) for s in ["random", "extrap"]}
rows = []
for meth, lab in ORDER:
    c = [cell(mae[s], meth, n) for s in ["random", "extrap"] for n in (20, 50, 100)]
    c += [cell(spr[s], meth, 50) if meth != "const" else "--" for s in ["random", "extrap"]]
    rows.append(f"{lab} & " + " & ".join(c) + r" \\")
hdr = r"""{\scriptsize\setlength{\tabcolsep}{3pt}
\begin{tabular}{lrrrrrrrr}
\toprule
 & \multicolumn{3}{c}{MAE (points), random split} & \multicolumn{3}{c}{MAE (points), extrapolation} & \multicolumn{2}{c}{Spearman, $n{=}50$} \\
\cmidrule(lr){2-4}\cmidrule(lr){5-7}\cmidrule(lr){8-9}
Method & $n{=}20$ & $n{=}50$ & $n{=}100$ & $n{=}20$ & $n{=}50$ & $n{=}100$ & random & extrap. \\
\midrule
"""
open("generated/tab_macro.tex", "w").write(hdr + "\n".join(rows) + "\n\\bottomrule\n\\end{tabular}}\n")

# bias/variance decomposition (Q4), mean over benchmarks at n=50, in squared accuracy points
q = pd.read_csv(f"{R}q4_bias_variance.csv")
q = q[q.n == 50].groupby(["split_type", "method"])[["bias2", "var", "mse"]].mean() * 1e4
rows = []
for meth, lab in ORDER:
    c = []
    for s in ["random", "extrap"]:
        r = q.loc[(s, meth)]
        c += [f"{r.bias2:.1f}", f"{r['var']:.1f}"]
    rows.append(f"{lab} & " + " & ".join(c) + r" \\")
hdr = r"""{\scriptsize
\begin{tabular}{lrrrr}
\toprule
 & \multicolumn{2}{c}{random split} & \multicolumn{2}{c}{extrapolation} \\
\cmidrule(lr){2-3}\cmidrule(lr){4-5}
Method & bias$^2$ & variance & bias$^2$ & variance \\
\midrule
"""
open("generated/tab_q4.tex", "w").write(hdr + "\n".join(rows) + "\n\\bottomrule\n\\end{tabular}}\n")

# ---- Tier 2/3 tables (experiment-repo, results/tables/macro/), MAE in accuracy points, n=50
M = "../results/tables/macro/"
NAMES = {"const": "B0", "random+mean": "B1 random", "strat+mean": "B2 stratified", "random+cal": "B3 random+calib.",
         "anchor+anchor": "Anchor points", "anchor+irt": "Anchor+IRT", "random+lowrank": "Random+low-rank",
         "omp+ridge": "OMP+ridge", "random+lowrank_dr": "Random+low-rank+corr.", "strat+lowrank": "Strat.+low-rank",
         "strat+lowrank_dr": "P3 DR", "strat+lowrank_eb": "P3 EB", "random+irt": "Random+IRT"}


def tab(rows, hdr):
    return hdr + "\n".join(rows) + "\n\\bottomrule\n\\end{tabular}}\n"


# family hold-out vs random vs extrapolation, 4 OpenLLM benchmarks
d = pd.read_csv(M + "q3_split_comparison.csv")
d = d[(d.analysis == "q3_4bench_openllm") & (d.n == 50)].set_index(["method", "split_type"])
meths = ["random+mean", "strat+mean", "random+cal", "anchor+anchor", "anchor+irt", "random+lowrank", "omp+ridge",
         "random+lowrank_dr", "strat+lowrank_dr", "strat+lowrank_eb"]
rows = [NAMES[m] + " & " + " & ".join(f"{d.loc[(m, s), 'mae']*100:.2f}" for s in ["random", "family", "extrap"]) + r" \\"
        for m in meths]
open("generated/tab_family.tex", "w").write(tab(rows, r"""{\scriptsize
\begin{tabular}{lrrr}
\toprule
Method & random & organisation hold-out & extrapolation \\
\midrule
"""))
rt = pd.read_csv(M + "q3_method_rank_transfer.csv")

# selector x estimator factorial, 7 benchmarks
f = pd.read_csv(M + "q7_factorial_macro.csv")
f = f[f.n == 50].set_index(["split_type", "selector", "estimator"])
ESTS = [("mean", "mean"), ("cal", "calib."), ("ridge", "ridge"), ("irt", "IRT"), ("lowrank", "low-rank"),
        ("irt_dr", "IRT+corr."), ("lowrank_dr", "low-rank+corr.")]
SEL = [("random", "random"), ("strat", "stratified"), ("pps", "PPS"), ("anchor", "anchor"), ("omp", "OMP"), ("copt", "c-optimal")]
rows = []
for sp, lab in [("random_fact", "random split"), ("extrap_fact", "extrapolation split")]:
    rows.append(r"\multicolumn{8}{l}{\emph{" + lab + r"}} \\")
    for s, sl in SEL:
        c = [f"{f.loc[(sp, s, e), 'mae']*100:.2f}" if (sp, s, e) in f.index else "--" for e, _ in ESTS]
        rows.append(f"{sl} & " + " & ".join(c) + r" \\")
open("generated/tab_factorial.tex", "w").write(tab(rows, r"""{\scriptsize\setlength{\tabcolsep}{3pt}
\begin{tabular}{l""" + "r" * len(ESTS) + r"""}
\toprule
Selector $\backslash$ estimator & """ + " & ".join(l for _, l in ESTS) + r""" \\
\midrule
"""))

# number of source models
s = pd.read_csv(M + "q5_ssize_macro.csv")
s = s[s.n == 50].set_index(["method", "split_type"])
meths = ["random+mean", "strat+mean", "anchor+irt", "random+lowrank", "omp+ridge", "random+lowrank_dr", "strat+lowrank_dr", "strat+lowrank_eb"]
rows = []
for m in meths:
    c = [f"{s.loc[(m, sp + suf), 'mae']*100:.2f}" for sp in ["random", "extrap"] for suf in ["_S10", "_S20", "_S40", ""]]
    rows.append(NAMES[m] + " & " + " & ".join(c) + r" \\")
open("generated/tab_ssize.tex", "w").write(tab(rows, r"""{\scriptsize\setlength{\tabcolsep}{3pt}
\begin{tabular}{lrrrrrrrr}
\toprule
 & \multicolumn{4}{c}{random split, $|\mathcal S|=$} & \multicolumn{4}{c}{extrapolation, $|\mathcal S|=$} \\
\cmidrule(lr){2-5}\cmidrule(lr){6-9}
Method & 10 & 20 & 40 & all & 10 & 20 & 40 & all \\
\midrule
"""))

# rank of the low-rank model
r = pd.read_csv(M + "q7_rank_macro.csv")
r = r[r.n == 50].set_index(["split_type", "method"])
rows = []
for sp, lab in [("random_rank", "random split"), ("extrap_rank", "extrapolation split")]:
    for suf, sl in [("", "plain model"), ("_dr", "+ correction (DR)"), ("_eb", "+ shrunk correction (EB)")]:
        c = []
        for k in [2, 4, 8, 16, 32]:
            name = "strat+lowrank" + suf + ("" if k == 8 else f"_k{k}")
            c.append(f"{r.loc[(sp, name), 'mae']*100:.2f}")
        rows.append(f"{lab if suf == '' else ''} & {sl} & " + " & ".join(c) + r" \\")
open("generated/tab_rank.tex", "w").write(tab(rows, r"""{\scriptsize
\begin{tabular}{llrrrrr}
\toprule
 & stratified design with & $k{=}2$ & $k{=}4$ & $k{=}8$ & $k{=}16$ & $k{=}32$ \\
\midrule
"""))

# coverage of the nominal 95% interval
c = pd.read_csv("../results/tables/coverage_check.csv")
g = c.assign(h=c.coverage * c["count"]).groupby(["split", "n", "method"])[["h", "count"]].sum()
g = (g.h / g["count"]).unstack()
rows = [f"{sp} & {n} & " + " & ".join(f"{g.loc[(sp, n), m]:.3f}" for m in ["random+mean", "random+lowrank_dr", "strat+lowrank_dr"]) + r" \\"
        for sp, n in g.index]
open("generated/tab_coverage.tex", "w").write(tab(rows, r"""{\scriptsize
\begin{tabular}{llrrr}
\toprule
split & $n$ & B1 (analytic) & random+low-rank+corr. & P3 DR \\
\midrule
"""))

# ---- review tables (experiment-repo, results/tables/review/): paired differences, target-model bootstrap, ablation contrasts
V = "../results/tables/review/"
tb = pd.read_csv(V + "target_bootstrap_macro.csv")
tb = tb[tb.baseline == "random+mean"].set_index(["split_type", "method", "n"])


def dcell(r, col, scale=100, d=2):
    v, lo, hi = r[col + "_diff"], r[col + "_diff_lo"], r[col + "_diff_hi"]
    if pd.isna(v):
        return "--"
    return f"{v*scale:+.{d}f}\\,{{\\tiny[{lo*scale:+.{d}f},{hi*scale:+.{d}f}]}}"


ABL = [("strat+mean", "B2 stratified (plain mean)"), ("random+lowrank", "Random + low-rank (no correction)"),
       ("random+lowrank_dr", "Random + low-rank + correction"), ("strat+lowrank", "Stratified + low-rank (no correction)"),
       ("strat+lowrank_dr", "P3 DR (stratified + low-rank + correction)"), ("strat+lowrank_eb", "P3 EB (shrunk correction)")]
rows = []
for m, lab in ABL:
    rows.append(lab + " & " + " & ".join(dcell(tb.loc[(s, m, n)], "mae") for s in ["random", "extrap"] for n in (20, 50, 100)) + r" \\")
ct = pd.read_csv(V + "ablation_contrasts_macro.csv").set_index(["split_type", "contrast", "n"])
rows.append(r"\midrule")
for cname in ["DR correction, given random items", "DR correction, given stratified items", "stratification, given DR",
              "stratification, plain mean", "EB shrinkage vs DR"]:
    rows.append("Contrast: " + cname + " & " + " & ".join(dcell(ct.loc[(s, cname, n)], "mae") for s in ["random", "extrap"] for n in (20, 50, 100)) + r" \\")
open("generated/tab_ablation.tex", "w").write(tab(rows, r"""{\scriptsize\setlength{\tabcolsep}{2pt}
\begin{tabular}{lrrrrrr}
\toprule
 & \multicolumn{3}{c}{random split} & \multicolumn{3}{c}{extrapolation} \\
\cmidrule(lr){2-4}\cmidrule(lr){5-7}
Estimator (difference in MAE to B1, points) & $n{=}20$ & $n{=}50$ & $n{=}100$ & $n{=}20$ & $n{=}50$ & $n{=}100$ \\
\midrule
"""))

# all four metrics, n=50, target-model bootstrap, difference to B1
ALL = [("strat+mean", "B2 stratified"), ("random+cal", "B3 random + calibration"), ("anchor+anchor", "Anchor points"),
       ("anchor+irt", "Anchor + IRT"), ("random+lowrank", "Random + low-rank"), ("omp+ridge", "P1 OMP + ridge"),
       ("random+lowrank_dr", "Random + low-rank + correction"), ("strat+lowrank_dr", "P3 DR"), ("strat+lowrank_eb", "P3 EB")]
rows = []
for s, lab in [("random", "random split"), ("extrap", "extrapolation split")]:
    rows.append(r"\multicolumn{5}{l}{\emph{" + lab + r"}} \\")
    for m, ml in ALL:
        r = tb.loc[(s, m, 50)]
        rows.append(ml + " & " + " & ".join(dcell(r, c, 100 if c in ("mae", "rmse") else 1, 2) for c in ["mae", "rmse", "spearman", "kendall"]) + r" \\")
open("generated/tab_metrics.tex", "w").write(tab(rows, r"""{\scriptsize\setlength{\tabcolsep}{3pt}
\begin{tabular}{lrrrr}
\toprule
Difference to B1 at $n{=}50$ & MAE (points) & RMSE (points) & Spearman & Kendall \\
\midrule
"""))
