"""Figure 2: optimism of the status-quo report vs search budget B and benchmark size n; real MMLU-Pro cache vs matched synthetic world."""
import sys; sys.path.insert(0, "/work/code")
import pandas as pd, numpy as np
from figstyle import *
real = pd.read_parquet("/work/results/real_sweep_naive.parquet"); syn = pd.read_parquet("/work/results/synth_sweep.parquet")
def opt(d, keys):
    x = d[d.method == "naive"].copy(); x["opt"] = x.est - x.truth
    g = x.groupby(keys).opt.agg(["mean", "std", "count"]).reset_index(); g["se"] = g["std"] / np.sqrt(g["count"]); return g
gr = opt(real, ["n", "kw_B"])
gs = opt(syn[(syn.w_a == -0.4) & (syn.w_rho == 0.8) & (syn.w_tau == 0.03)], ["n", "kw_B"])
fig, ax = plt.subplots(1, 3, figsize=(7.0, 2.4))
ns = sorted(gr.n.unique())
for i, n in enumerate(ns):
    h = gr[gr.n == n].sort_values("kw_B"); s = gs[gs.n == n].sort_values("kw_B")
    ax[0].errorbar(h.kw_B, 100 * h["mean"], yerr=100 * 1.96 * h.se, color=OI[i], marker="o", capsize=0, label=f"n={n}")
    ax[0].plot(s.kw_B, 100 * s["mean"], color=OI[i], ls=":", lw=1)
ax[0].set_xscale("log", base=2); ax[0].set_xticks([1, 2, 4, 8, 16, 32, 72]); ax[0].set_xticklabels(["1", "2", "4", "8", "16", "32", "72"]); ax[0].minorticks_off()
ax[0].set_xlabel("search budget B (configs evaluated)"); ax[0].set_ylabel("optimism: reported $-$ true [pts]"); ax[0].legend(frameon=False, fontsize=6)
ax[0].set_title("(a) real MMLU-Pro (solid), matched sim (dotted)")
# (b) reported vs true gain over the average configuration, B=72
m = real[real.method.isin(["naive", "mean_cfg"])].copy()
piv = m.pivot_table(index=["n", "kw_B", "rep"], columns="method", values=["est", "truth"]).reset_index()
piv.columns = ["_".join([c for c in col if c]) for col in piv.columns]
piv["rep_gain"] = piv.est_naive - piv.est_mean_cfg; piv["true_gain"] = piv.truth_naive - piv.truth_mean_cfg
g = piv[piv.kw_B == 72].groupby("n").agg(rep=("rep_gain", "mean"), tru=("true_gain", "mean"), sd_t=("true_gain", "std"), c=("rep_gain", "size")).reset_index()
x = np.arange(len(g)); ax[1].bar(x - 0.18, 100 * g.rep, 0.34, color=OI[1], label="reported gain"); ax[1].bar(x + 0.18, 100 * g.tru, 0.34, color=OI[0], label="true gain")
ax[1].errorbar(x + 0.18, 100 * g.tru, yerr=100 * 1.96 * g.sd_t / np.sqrt(g.c), fmt="none", color="k", lw=0.8, capsize=0)
ax[1].set_xticks(x); ax[1].set_xticklabels(g.n); ax[1].set_xlabel("n"); ax[1].set_ylabel("tuned $-$ average config [pts]"); ax[1].legend(frameon=False, fontsize=6); ax[1].set_title("(b) gain from tuning (B=72)")
# (c) synthetic: optimism vs n for several tau at B=72 (+ real)
for i, tau in enumerate((0.0, 0.1, 0.2)):
    s = opt(syn[(syn.w_a == -0.4) & (syn.w_rho == 0.8) & (syn.w_tau == tau) & (syn.kw_B == 72)], ["n"]).sort_values("n")
    ax[2].plot(s.n, 100 * s["mean"], color=OI[2 + i], marker="s", label=f"sim, $\\tau$={tau}")
h = gr[gr.kw_B == 72].sort_values("n"); ax[2].errorbar(h.n, 100 * h["mean"], yerr=100 * 1.96 * h.se, color="k", marker="o", capsize=0, label="real")
ax[2].set_xscale("log"); ax[2].set_xticks([50, 100, 200, 400, 800]); ax[2].set_xticklabels(["50", "100", "200", "400", "800"]); ax[2].minorticks_off()
ax[2].set_xlabel("n"); ax[2].set_ylabel("optimism at B=72 [pts]"); ax[2].legend(frameon=False, fontsize=6); ax[2].set_title("(c) role of true spread $\\tau$")
plt.tight_layout(); plt.savefig("/work/paper/figs/fig_sweep.pdf"); print("ok")
