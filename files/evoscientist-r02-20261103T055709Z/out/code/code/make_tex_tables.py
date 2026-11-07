"""Build LaTeX tables (paper/tables/*.tex) from result CSVs. No number is typed by hand.
Usage: python code/make_tex_tables.py   (run after analyze_synth.py and analyze_cifar.py)"""
import os, numpy as np, pandas as pd
os.makedirs("paper/tables", exist_ok=True)
LAB = {"l2": r"$\ell_2$", "l1": "TV", "linf": r"$\ell_\infty$", "hell": "Hellinger", "aitch": r"Aitch.($10^{-2}$)",
       "aitch@0.001": r"Aitch.($10^{-3}$)", "aitch@0.1": r"Aitch.($10^{-1}$)", "kl": "KL"}
MN = {"plain": "plain", "norm": "normalised", "mond": "Mondrian"}
SC = ["l2", "l1", "linf", "hell", "aitch", "kl"]


def wr(name, lines):
    open(f"paper/tables/{name}.tex", "w").write("\n".join(lines) + "\n")


# ---- theory (appendix, full) and compact
t = pd.read_csv("results/theory.csv")
L = [r"\begin{tabular}{llrrrrrrr}", r"\toprule",
     r"score & $n$ & mean $\bar C$ (s.e.) & $\frac{n+1-\ell}{n+1}$ & SD & Beta SD & $\hat P(C<.9)$ & Beta & KS $p$ \\", r"\midrule"]
for _, r in t.iterrows():
    L.append(f"{LAB[r.score]} & {r.n} & {r.emp_mean:.4f} ({r.emp_mean_se:.4f}) & {r.beta_mean:.4f} & {r.emp_sd:.4f} & {r.beta_sd:.4f} & {r.p_below_90:.3f} & {r.beta_p_below_90:.3f} & {r.ks_p:.2f} \\\\")
L += [r"\bottomrule", r"\end{tabular}"]; wr("theory", L)

# ---- mass by score (synthetic)
m = pd.read_csv("results/tables/mass_by_score.csv")
L = [r"\begin{tabular}{rr" + "r" * len(SC) + "}", r"\toprule", r"$K$ & $\kappa_0$ & " + " & ".join(LAB[s] for s in SC) + r" \\", r"\midrule"]
cols = [c for c in m.columns if c not in ("K", "kappa0")]
for _, r in m.iterrows():
    vals = [r[c] for c in cols]; best = min(vals)
    L.append(f"{int(r.K)} & {int(r.kappa0)} & " + " & ".join((f"\\textbf{{{v:.3f}}}" if v == best else f"{v:.3f}") for v in vals) + r" \\")
L += [r"\bottomrule", r"\end{tabular}"]; wr("mass_by_score", L)

# ---- mass vs volume K=3
v = pd.read_csv("results/tables/mass_vs_volume_K3.csv")
L = [r"\begin{tabular}{rlrrrr}", r"\toprule", r"$\kappa_0$ & score & mass & rank & volume & rank \\", r"\midrule"]
for _, r in v.iterrows():
    L.append(f"{int(r.kappa0)} & {LAB[r.score]} & {r['mass']:.3f} & {r.rank_mass:g} & {r.vol:.3f} & {r.rank_vol:g} \\\\")
    if r.score == "kl": L.append(r"\midrule")
L[-1] = r"\bottomrule"; L.append(r"\end{tabular}"); wr("mass_vs_volume", L)

# ---- conditional coverage (synthetic)
c = pd.read_csv("results/tables/conditional_coverage.csv")
L = [r"\begin{tabular}{llcccc}", r"\toprule", r"scenario & method & worst $x_1$-slice & worst conf.-slice & max dev. $x_1$ & max dev. conf. \\", r"\midrule"]
names = {(0, 0): "homosk., well-spec.", (0, 1): "homosk., misspec.", (1, 0): "heterosk., well-spec.", (1, 1): "heterosk., misspec."}
for (h, ms), g in c.groupby(["hetero", "misspec"], sort=True):
    for i, (_, r) in enumerate(g.iterrows()):
        L.append(f"{names[(h, ms)] if i == 0 else ''} & {MN[r.method]} & {r.wsc_x1} & {r.wsc_conf} & {r.maxdev_x1} & {r.maxdev_conf} \\\\")
    L.append(r"\midrule")
L[-1] = r"\bottomrule"; L.append(r"\end{tabular}"); wr("conditional", L)

# ---- paired tests
p = pd.read_csv("results/tables/paired_tests_conditional.csv")
L = [r"\begin{tabular}{lllrrrr}", r"\toprule", r"scenario & metric & method vs plain & diff. & scen.\ $>0$ & $p$ & Holm $p$ \\", r"\midrule"]
for _, r in p.iterrows():
    L.append(f"{names[(r.hetero, r.misspec)]} & {r.metric.replace('_', ' ')} & {MN[r.method]} & {r.mean_diff:+.4f} & {r.n_scen_pos}/{r.n_scen} & {r.p:.3f} & {r.p_holm:.3f} \\\\")
L += [r"\bottomrule", r"\end{tabular}"]; wr("paired", L)

# ---- CIFAR
if os.path.exists("results/tables/cifar_summary.csv"):
    R = pd.read_csv("results/tables/cifar_summary.csv")
    f = lambda r, c: f"{r[c]:.3f}$\\pm${r[c + '_hw']:.3f}"
    SCC = [s for s in LAB if s in R.score.unique()]
    L = [r"\begin{tabular}{l" + "cc" * 2 + "}", r"\toprule",
         r" & \multicolumn{2}{c}{exchangeable} & \multicolumn{2}{c}{covariate shift} \\", r"score & coverage & mass & coverage & mass \\", r"\midrule"]
    for s in SCC:
        a = R[(R.setting == "iid") & (R.ncal == 500) & (R.method == "plain") & (R.score == s)].iloc[0]
        b = R[(R.setting == "shift") & (R.ncal == 500) & (R.method == "plain") & (R.score == s)].iloc[0]
        L.append(f"{LAB[s]} & {f(a, 'cov')} & {f(a, 'mass')} & {f(b, 'cov')} & {f(b, 'mass')} \\\\")
    L += [r"\bottomrule", r"\end{tabular}"]; wr("cifar_scores", L)
    L = [r"\begin{tabular}{llllcccc}", r"\toprule", r"setting & score & method & coverage & mass & worst entropy-slice & worst conf.-slice \\", r"\midrule"]
    for st in ["iid", "shift"]:
        for s in ["l2", "kl"]:
            for mth in ["plain", "norm", "mond"]:
                r = R[(R.setting == st) & (R.ncal == 500) & (R.method == mth) & (R.score == s)].iloc[0]
                L.append(f"{'exch.' if st == 'iid' else 'shift'} & {LAB[s]} & {MN[mth]} & {f(r, 'cov')} & {f(r, 'mass')} & {f(r, 'wsc_ent')} & {f(r, 'wsc_conf')} \\\\")
        L.append(r"\midrule")
    L[-1] = r"\bottomrule"; L.append(r"\end{tabular}"); wr("cifar_methods", L)
    L = [r"\begin{tabular}{llrcccc}", r"\toprule", r"score & method & $n_{cal}$ & cov.\ (seed 0) & cov.\ (seed 1) & mass (seed 0) & mass (seed 1) \\", r"\midrule"]
    for s in ["l2", "kl"]:
        for mth in ["plain", "mond"]:
            for n in [100, 500, 2000]:
                r = R[(R.setting == "iid") & (R.ncal == n) & (R.method == mth) & (R.score == s)].iloc[0]
                L.append(f"{LAB[s]} & {MN[mth]} & {n} & {r.cov_seed0:.3f} & {r.cov_seed1:.3f} & {r.mass_seed0:.3f} & {r.mass_seed1:.3f} \\\\")
    L += [r"\bottomrule", r"\end{tabular}"]; wr("cifar_seeds", L)
print("tables written:", sorted(os.listdir("paper/tables")))
