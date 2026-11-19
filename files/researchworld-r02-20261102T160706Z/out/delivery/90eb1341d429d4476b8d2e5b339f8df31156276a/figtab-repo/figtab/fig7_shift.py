"""E4 exhibit (claim C10): marginal coverage on the shifted test set vs shift delta, D=5, heteroscedastic, linear predictor, 100 replicates.
Calibration x ~ N(0,I), test x ~ N(delta w, I), w = noise direction.  Coloured lines: ordinary split conformal, plain (solid) and locally normalised (dashed) scores;
grey dots: weighted split conformal with the exact likelihood ratio (Tibshirani et al. 2019), all 8 methods.  Bars: 95% t-CI over replicates.
Input: results/e4_summary.csv.
"""
import matplotlib.pyplot as plt
from common import *

style()
S = pd.read_csv(os.path.join(EXP, "results", "e4_summary.csv"))
fams = ["dirichlet", "lognormal", "multinomial"]
fig, ax = plt.subplots(1, 3, figsize=(TEXT_W, 2.1), sharey=True)
for a, f in zip(ax, fams):
    g = S[S.family == f]
    for m in g.method.unique():
        s, v = split_method(m)
        u = g[(g.method == m) & (g.weighted == 0)].sort_values("delta")
        c = SCORE_COL[s]
        a.errorbar(u.delta, u.cov10, yerr=[u.cov10 - u.cov10_lo, u.cov10_hi - u.cov10], color=c, ls="-" if v == "plain" else "--",
                   marker=VARIANT_MK[v], ms=3, mfc="white" if v == "plain" else c, lw=0.8, elinewidth=0.6, capsize=1)
    w = g[g.weighted == 1]
    a.plot(w.delta, w.cov10, "x", color="0.2", ms=3.5, mew=0.6, alpha=0.8, zorder=5)
    a.axhline(0.9, color="0.3", lw=0.6, ls=":")
    a.set_title(f"({'abc'[fams.index(f)]}) {f}", loc="left", fontsize=7.5)
    a.set_xlabel(r"shift $\delta$"); a.grid(lw=0.3, color="0.88")
ax[0].set_ylabel("coverage on shifted test set")
from matplotlib.lines import Line2D
h = [Line2D([], [], color=SCORE_COL[s], lw=1.2, label=SCORE_LAB[s]) for s in ["l2", "hell", "kl", "ait"]]
h += [Line2D([], [], color="0.3", ls="-", lw=1, label="plain"), Line2D([], [], color="0.3", ls="--", lw=1, label="normalised"),
      Line2D([], [], color="0.2", marker="x", ls="", label="weighted (all)")]
fig.legend(handles=h, loc="lower center", ncol=7, frameon=False, bbox_to_anchor=(0.5, -0.12), fontsize=6, columnspacing=0.9, handletextpad=0.4)
fig.tight_layout()
save(fig, "fig7_shift.pdf")
