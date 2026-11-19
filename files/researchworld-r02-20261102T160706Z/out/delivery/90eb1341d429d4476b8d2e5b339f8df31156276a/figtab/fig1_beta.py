"""Fig 1 (claim C1): split-conformal coverage over repeated calibration sets vs the exact Beta(k, n+1-k) law.
Input: results/theory/t1_beta_law.csv (columns family, score, n, k, mean_emp, mean_beta, q05_emp, q05_beta, q95_emp, q95_beta, ks, ks_p).
Shaded: theoretical 5-95% band of the coverage given the calibration set; markers: empirical 5% / mean / 95% quantiles of the same quantity over 4000 calibration draws.
"""
import os
import matplotlib.pyplot as plt
from common import *

style()
t = pd.read_csv(os.path.join(EXP, "results", "theory", "t1_beta_law.csv"))
fams = list(dict.fromkeys(t.family))
fig, ax = plt.subplots(1, len(fams), figsize=(TEXT_W, 2.3), sharey=True, squeeze=False)
ax = ax[0]
ns = sorted(t.n.unique())
xs = {n: i for i, n in enumerate(ns)}
for a, f in zip(ax, fams):
    g = t[t.family == f]
    b = g.drop_duplicates("n").sort_values("n")
    a.fill_between([xs[n] for n in b.n], b.q05_beta, b.q95_beta, color="0.85", lw=0, label="Beta 5-95% band")
    a.plot([xs[n] for n in b.n], b.mean_beta, color="0.4", lw=0.8, ls="--", label="Beta mean")
    for j, s in enumerate(["l2", "hell", "ait"]):
        gs = g[g.score == s].sort_values("n")
        x = np.array([xs[n] for n in gs.n]) + (j - 1) * 0.12
        c = SCORE_COL[s]
        a.plot(x, gs.mean_emp, "o", color=c, ms=3.5, label=SCORE_LAB[s] + " (mean)")
        a.plot(x, gs.q05_emp, "v", color=c, ms=3, mfc="white")
        a.plot(x, gs.q95_emp, "^", color=c, ms=3, mfc="white")
    a.set_xticks(range(len(ns)))
    a.set_xticklabels(ns)
    a.set_xlabel("calibration size $n$")
    a.set_title(f"({'ab'[fams.index(f)]}) {f} noise, K=5", loc="left", fontsize=7.5)
    a.grid(axis="y", lw=0.3, color="0.85")
    ksmax = g.ks.max()
    a.text(0.97, 0.04, f"KS p-values {g.ks_p.min():.2f}-{g.ks_p.max():.2f} (12 tests)", transform=a.transAxes, ha="right", fontsize=6.5)
ax[0].set_ylabel(r"coverage given calibration set ($\alpha=0.1$)")
h, l = ax[0].get_legend_handles_labels()
fig.legend(h, l, loc="lower center", ncol=5, frameon=False, bbox_to_anchor=(0.5, -0.2), columnspacing=1.0, handletextpad=0.4)
fig.text(0.5, 1.0, "open triangles: empirical 5% / 95% quantiles; filled circles: empirical mean over repeated calibration sets", fontsize=6.5, ha="center", va="bottom")
save(fig, "fig1_beta_law.pdf")
