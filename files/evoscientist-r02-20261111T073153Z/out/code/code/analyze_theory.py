"""Figures/tables for theory checks and eps-sensitivity. Usage: python code/analyze_theory.py"""
import os, sys, json
import numpy as np, pandas as pd
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from scipy import stats
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from analyze_common import *

os.makedirs("figures", exist_ok=True); os.makedirs("tables", exist_ok=True)
plt.rcParams.update({"font.size": 8, "axes.titlesize": 8, "axes.labelsize": 8, "legend.fontsize": 6.5,
                     "xtick.labelsize": 7, "ytick.labelsize": 7, "figure.dpi": 150, "pdf.fonttype": 42})
S = {}
B = pd.read_csv("results/theory_beta.csv"); E = pd.read_csv("results/theory_beta_eval.csv")
K2 = pd.read_csv("results/theory_k2.csv"); K2f = pd.read_csv("results/theory_k2_formula.csv")
gaps = pd.read_csv("results/theory_k2_gaps.csv")

# ---- table: Beta law check
lines = [r"\begin{tabular}{llrrrrrr}", r"\toprule",
         r"DGP/score & $n$ & mean (emp.) & mean (Beta) & sd (emp.) & sd (Beta) & 5\% q (emp.) & 5\% q (Beta) \\", r"\midrule"]
nm = {("ln", "l2"): r"LN / $\ell_2$", ("ln", "ait"): "LN / Aitchison", ("mult", "l1"): "Multinom. / TV"}
for (d, s), g in B.groupby(["dgp", "score"], sort=False):
    for _, r in g.iterrows():
        lines.append(f"{nm[(d, s)]} & {int(r.n)} & {r.mean_emp:.4f} & {r.mean_beta:.4f} & {r.sd_emp:.4f} & {r.sd_beta:.4f} & {r.q05_emp:.3f} & {r.q05_beta:.3f} \\\\")
    lines.append(r"\midrule")
lines[-1] = r"\bottomrule"; lines.append(r"\end{tabular}")
open("tables/tab_beta.tex", "w").write("\n".join(lines))
S["beta_max_abs_mean_diff"] = float((B.mean_emp - B.mean_beta).abs().max())
S["beta_max_rel_sd_diff"] = float(((B.sd_emp - B.sd_beta).abs() / B.sd_beta).max())
S["beta_ks_max"] = float(B.ks_stat.max())

lines = [r"\begin{tabular}{rrrrr}", r"\toprule", r"$\tau$ & threshold $r$ & min $c(f_1)$ & $f_1$ at min & max $c(f_1)$ \\", r"\midrule"]
for _, r in gaps.iterrows():
    lines.append(f"{r.tau:.2f} & {r.r_pop:.3f} & {r.min_cov:.3f} & {r.f_at_min:.2f} & {r.max_cov:.3f} \\\\")
lines += [r"\bottomrule", r"\end{tabular}"]
open("tables/tab_k2gaps.tex", "w").write("\n".join(lines))

# ---- figure: theory
fig, axs = plt.subplots(1, 3, figsize=(6.8, 2.0))
ax = axs[0]
for n, c in [(20, "C0"), (100, "C1")]:
    cv = np.load(f"results/beta_covs_{n}.npy")
    l = int(np.floor((n + 1) * ALPHA))
    ax.hist(cv, bins=40, range=(0.55, 1), density=True, alpha=0.45, color=c, label=f"$n$={n} (sim.)")
    x = np.linspace(0.55, 0.999, 400); ax.plot(x, stats.beta(n + 1 - l, l).pdf(x), color=c, lw=1)
ax.axvline(0.9, color="k", ls=":", lw=0.6); ax.set_xlabel("coverage given calibration set"); ax.set_ylabel("density")
ax.set_title("(a) Beta law"); ax.legend(frameon=False)
ax = axs[1]
for nt, c in [(100, "C2"), (1000, "C3"), (10000, "C4")]:
    s = E[E.n_test == nt]
    ax.plot(s.n_cal, s.p_outside_tol_theory, "-", color=c, lw=1, label=f"$n_{{test}}$={nt}")
    ax.plot(s.n_cal, s.p_outside_tol_emp, "o", color=c, ms=2.5)
ax.set_xscale("log"); ax.set_xlabel("$n_{cal}$"); ax.set_ylabel(r"P(|cov$-0.9|>0.02$)")
ax.set_title("(b) one-run check"); ax.legend(frameon=False)
ax = axs[2]
ax.plot(K2f.f, K2f.cov_l2_formula, "k--", lw=1, label=r"$\ell_2$ formula")
for c, lab, col in [("cov_l2", r"$\ell_2$", "C0"), ("cov_hell", "Hellinger", "C1"), ("cov_kl", "KL", "C2"), ("cov_ait", "Aitchison", "C3")]:
    ax.plot(K2.f_mid, K2[c], "o-", ms=2, lw=0.8, color=col, label=lab)
ax.axhline(0.9, color="k", ls=":", lw=0.6); ax.set_xlabel("$f_1(x)$"); ax.set_ylabel("conditional coverage")
ax.set_title("(c) $K{=}2$, logistic-normal"); ax.legend(frameon=False, loc="upper center", ncol=2, fontsize=5.5, columnspacing=0.6, handlelength=1.2)
plt.tight_layout(); plt.savefig("figures/fig_theory.pdf"); plt.close()
S["k2_l2_min"] = float(K2.cov_l2.min()); S["k2_l2_max"] = float(K2.cov_l2.max())
S["k2_ait_min"] = float(K2.cov_ait.min()); S["k2_ait_max"] = float(K2.cov_ait.max())
S["k2_ait_central_min"] = float(K2[(K2.f_mid > 0.1) & (K2.f_mid < 0.9)].cov_ait.min())
S["k2_ait_central_max"] = float(K2[(K2.f_mid > 0.1) & (K2.f_mid < 0.9)].cov_ait.max())
S["k2_formula_vs_mc_maxdiff"] = float(np.abs(np.interp(K2.f_mid, K2f.f, K2f.cov_l2_formula) - K2.cov_l2).max())

# ---- zero asymptotics table
Z = pd.read_csv("results/theory_zero.csv")
rows = []
for (K, N), g in Z.groupby(["K", "N"]):
    lo, hi = 1e-10, 1e-8  # finest eps pair
    a = g[np.isclose(g.eps, 1e-8, rtol=1e-6, atol=0)].set_index("rep"); b = g[np.isclose(g.eps, 1e-10, rtol=1e-6, atol=0)].set_index("rep")
    slope = (b.q - a.q) / (b.L - a.L)
    rows.append(dict(K=K, N=N, zero_frac=a.zero_frac.mean(), slope_emp=slope.mean(), slope_hw=1.96 * slope.std() / np.sqrt(len(slope)),
                     slope_pred=a.pred_slope.mean(), max_abs_dev=(slope - a.pred_slope).abs().max(),
                     frac_pred0=(a.pred_slope == 0).mean()))
ZT = pd.DataFrame(rows); ZT.to_csv("results/summary_zero.csv", index=False)
lines = [r"\begin{tabular}{rrrrrr}", r"\toprule", r"$K$ & $N$ & P(zero) & slope (emp.) & slope (Prop.~3) & max $|$dev$|$ \\", r"\midrule"]
for _, r in ZT.iterrows():
    lines.append(f"{int(r.K)} & {int(r.N)} & {r.zero_frac:.2f} & {r.slope_emp:.3f}\\,$\\pm$\\,{r.slope_hw:.3f} & {r.slope_pred:.3f} & {r.max_abs_dev:.1e} \\\\")
lines += [r"\bottomrule", r"\end{tabular}"]
open("tables/tab_zero.tex", "w").write("\n".join(lines))
print(ZT.round(4).to_string())

# ---- figure: eps sensitivity
panels = 3 if os.path.exists("results/cifar10h.csv") else 2
fig, axs = plt.subplots(1, panels, figsize=(6.8, 2.0))
ax = axs[0]
for (K, N), c in [((5, 20), "C0"), ((5, 100), "C1"), ((10, 20), "C2")]:
    g = Z[(Z.K == K) & (Z.N == N)].groupby("eps").agg(q=("q", "mean"), ps=("pred_slope", "mean")).reset_index().sort_values("eps", ascending=False)
    L = np.log10(1 / g.eps)
    ax.plot(L, g.q, "o", ms=2.5, color=c, label=f"$K$={K}, $N$={N}")
    ax.plot(L, g.q.iloc[-1] + g.ps.iloc[-1] * np.log(10) * (L - L.iloc[-1]), "-", color=c, lw=0.7)
ax.set_xlabel(r"$\log_{10}(1/\varepsilon)$"); ax.set_ylabel(r"Aitchison threshold $\hat q$"); ax.set_title("(a) threshold growth"); ax.legend(frameon=False)
ep = pd.read_csv("results/synth_eps.csv") if os.path.exists("results/synth_eps.csv") else None
if ep is not None and ep.rep.nunique() >= 100:
    ax = axs[1]
    for d, c in [("ln", "C0"), ("dir", "C1"), ("mult", "C3")]:
        g = ep[(ep.dgp == d)]
        pts = []
        for m in [x for x in g.method.unique() if x.startswith("ait_eps")]:
            e = float(m.replace("ait_eps", "")); mm, hw = mean_ci(g[g.method == m].size_unif); pts.append((e, mm, hw))
        pts = sorted(pts)
        ax.errorbar([np.log10(1 / p[0]) for p in pts], [p[1] for p in pts], [p[2] for p in pts], fmt="o-", ms=2.5, lw=0.8, color=c, label=DGPN[d])
        l2 = g[g.method == "l2"].size_unif.mean(); ax.axhline(l2, color=c, ls=":", lw=0.7)
    ax.set_xlabel(r"$\log_{10}(1/\varepsilon)$"); ax.set_ylabel("uniform-measure size"); ax.set_title("(b) synthetic, $K{=}5$ (dotted: $\\ell_2$)")
    ax.legend(frameon=False)
    # table of coverage in eps experiment
    S["eps_cov_range"] = [float(ep[ep.method.str.startswith("ait_eps")]["cov"].mean()), float(ep["cov"].min()), float(ep["cov"].max())]
if panels == 3:
    cf = pd.read_csv("results/cifar10h.csv"); ax = axs[2]
    for var, c in [("raw", "C0"), ("ts", "C2")]:
        g = cf[(cf.variant == var) & (cf.n_cal == 500)]
        pts = []
        for m in ["ait_eps1e-08", "ait_eps1e-06", "ait_eps0.0001", "ait_eps0.001", "ait", "ait_eps0.1"]:
            e = {"ait": 0.01}.get(m) or float(m.replace("ait_eps", "")); mm, hw = mean_ci(g[g.method == m].size_pool); pts.append((e, mm, hw))
        pts = sorted(pts)
        ax.errorbar([np.log10(1 / p[0]) for p in pts], [p[1] for p in pts], [p[2] for p in pts], fmt="o-", ms=2.5, lw=0.8, color=c, label=f"Ait. ({var})")
        ax.axhline(g[g.method == "l2"].size_pool.mean(), color=c, ls=":", lw=0.7)
    ax.set_xlabel(r"$\log_{10}(1/\varepsilon)$"); ax.set_ylabel("pool size"); ax.set_title("(c) CIFAR-10H, $n_{cal}$=500"); ax.legend(frameon=False)
plt.tight_layout(); plt.savefig("figures/fig_zero.pdf"); plt.close()
json.dump(S, open("results/summary_theory_misc.json", "w"), indent=1)
print(json.dumps(S, indent=1))
