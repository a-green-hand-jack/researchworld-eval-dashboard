"""Fig 5 (claim C5): what the conditional-coverage metrics read when conditional coverage is exact.
Input: results/null/null_binned.csv (500 replicates per n_cal; coverage indicators Bernoulli(p), p ~ Beta(k, n+1-k), independent of x; n_test = 2000;
metrics computed by the same code as in E1).  Line = mean over replicates, band = 5-95% quantiles over replicates.
A method's value is interpretable as 'non-null' only outside this band at the same n_cal.
"""
import matplotlib.pyplot as plt
from common import *

style()
n = load_null()
panels = [("ymax_gap", "top-prob. bin gap\n(max $-$ min coverage, 5 bins)"), ("wsc", "worst-slab coverage\n(10% mass)"), ("or_gap", "oracle gap $E_x|c(x)-0.9|$\n(60 pts $\\times$ 400 draws)")]
fig, ax = plt.subplots(1, 3, figsize=(TEXT_W, 2.0))
q = n.groupby("n_cal")
for a, (col, ttl) in zip(ax, panels):
    m = q[col].mean()
    a.fill_between(m.index, q[col].quantile(0.05), q[col].quantile(0.95), color="0.85", lw=0)
    a.plot(m.index, m, "o-", color="0.25", ms=3, lw=0.9)
    a.set_xscale("log")
    tk = [30, 100, 500, 2000]; a.set_xticks(tk); a.set_xticklabels(tk); a.minorticks_off()
    a.set_xlabel("calibration size $n_{cal}$")
    a.set_title(ttl, fontsize=7)
    a.grid(lw=0.3, color="0.88")
ax[1].axhline(0.9, color="0.4", lw=0.6, ls="--")
ax[0].set_ylabel("null value (mean, 5-95% band)")
fig.tight_layout()
save(fig, "fig5_null_spread.pdf")
