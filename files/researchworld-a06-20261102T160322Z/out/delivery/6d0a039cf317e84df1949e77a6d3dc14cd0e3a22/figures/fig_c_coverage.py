"""Fig C (Q2a, Q2b): empirical coverage of the nominal-95% interval of each reporting method, T0 synthetic.
Coverage of the method's own target (theta_target) vs n, one line per method, panels = tau (columns) x K (rows).
Bands: Wilson 95% intervals over replicates. Reads results/methods_t0.parquet. Writes figures/fig_c_coverage.pdf"""
import numpy as np, pandas as pd, matplotlib.pyplot as plt
import style, common

style.apply()
m = pd.read_parquet(common.path("methods_t0.parquet"))
m = common.reference(common.main_grid(m))
m = m[m.lo.notna() | m.hi.notna()]
m = m.assign(cover=((m.lo <= m.theta_target) & (m.theta_target <= m.hi)).astype(int))
g = m.groupby(["method", "tau", "K", "n"]).cover.agg(k="sum", N="size").reset_index()
g["p"] = g.k / g.N
g["lo"], g["hi"] = common.wilson(g.k, g.N)
methods = [x for x in ["M0", "M1_f0.5", "M2", "M3_opt", "M4_simult", "M4_cond", "M4_hybrid", "M5_eb"] if x in set(g.method)]
MCOL = {"M0": "#000000", "M1_f0.5": "#D55E00", "M2": "#009E73", "M3_opt": "#E69F00", "M4_simult": "#CC79A7", "M4_cond": "#0072B2", "M4_hybrid": "#56B4E9", "M5_eb": "#999999"}
MLS = {"M4_cond": "-", "M4_hybrid": "--"}
mcol = MCOL
taus = [t for t in (0.0, 0.1) if t in set(g.tau)]; Ks = [k for k in (5, 50, 200) if k in set(g.K)]
fig, axs = plt.subplots(len(taus), len(Ks), figsize=(style.TEXT_WIDTH_IN, 1.35 * len(taus) + 0.35), sharex=True, sharey=True, squeeze=False)
for i, tau in enumerate(taus):
    for j, K in enumerate(Ks):
        ax = axs[i, j]
        for meth in methods:
            d = g[(g.method == meth) & (g.tau == tau) & (g.K == K)].sort_values("n")
            if d.empty: continue
            ax.plot(d.n, d.p, color=mcol[meth], marker="o", ms=2.5, lw=0.9, ls=MLS.get(meth, "-"), label=meth)
            ax.fill_between(d.n, d.lo, d.hi, color=mcol[meth], alpha=0.12, lw=0)
        ax.axhline(0.95, color="0.4", ls=":", lw=0.8)
        ax.set_xscale("log"); ax.set_xticks([50, 200, 1000]); ax.set_xticklabels([50, 200, 1000]); ax.minorticks_off()
        ax.set_ylim(0, 1.02)
        ax.set_title(rf"$\tau$={tau:g}, K={K}", fontsize=7)
        if i == len(taus) - 1: ax.set_xlabel("search-set size $n$")
fig.supylabel("coverage of nominal 95%", fontsize=8)
h, l = axs[0, 0].get_legend_handles_labels()
fig.tight_layout(rect=(0, 0.06, 1, 1))
fig.legend(h, l, frameon=False, fontsize=6.5, loc="lower center", ncol=len(l))
fig.savefig(f"{common.OUT}/fig_c_coverage.pdf")
print("min replicates per point:", int(g.N.min()))
