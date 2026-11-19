"""Figure 1: closed-form optimism (eq. 1) vs simulation (results/theory.csv)."""
import sys; sys.path.insert(0,"/work/code")
import pandas as pd, numpy as np
from figstyle import *
d = pd.read_csv("/work/results/theory.csv")
fig, ax = plt.subplots(1, 2, figsize=(6.4, 2.5))
a = ax[0]
for i, tp in enumerate(sorted(d.tau_probit.unique())):
    g = d[d.tau_probit == tp]
    a.scatter(100*g.pred, 100*g.opt, s=8, color=OI[i], label=f"$\\tau$={100*g.tau.mean():.1f} pts")
m = 100*d.pred.max(); a.plot([0, m], [0, m], color="k", lw=0.8)
a.set_xlabel("predicted optimism, eq. (1) [pts]"); a.set_ylabel("simulated optimism [pts]"); a.legend(frameon=False, title="true SD of configs", title_fontsize=7)
a.set_title("(a) theory vs. simulation (375 cells)")
a = ax[1]
g = d[(d.rho == 0.8) & (d.B == 32)]
for i, tp in enumerate(sorted(g.tau_probit.unique())):
    h = g[g.tau_probit == tp].sort_values("n")
    a.errorbar(h.n, 100*h.opt, yerr=100*1.96*h.opt_se, color=OI[i], marker="o", capsize=0, label=f"$\\tau$={100*h.tau.mean():.1f}")
    a.plot(h.n, 100*h.pred, color=OI[i], ls=":", lw=1)
a.set_xscale("log"); a.set_xticks([50,100,200,400,800]); a.set_xticklabels(["50","100","200","400","800"]); a.minorticks_off(); a.set_xlabel("benchmark size n"); a.set_ylabel("optimism of best-of-32 [pts]"); a.set_title("(b) optimism vs. n (dotted: eq. 1)")
a.legend(frameon=False, ncol=1, title="true SD [pts]", title_fontsize=7)
plt.savefig("/work/paper/figs/fig_theory.pdf"); print("ok")
