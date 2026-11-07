"""Fig 2 (claim C2): region size of each score relative to the plain-L2 region, E1, alpha=0.1.
Quantity: per replicate, median (over test points) Lebesgue volume fraction of the region within the simplex (Monte Carlo, only D<=5 in the results);
shown is the ratio to the plain-L2 volume of the *same replicate* (paired), geometric mean over replicates with 95% CI of the mean log-ratio.
Reference measure is the uniform measure on the simplex for every score; ratios compare scores within a configuration only.
Coverage of all compared methods is marginally 0.9, so smaller is better at equal marginal coverage.
Usage: python figtab/fig2_size.py [file stems...]
"""
import sys
import matplotlib.pyplot as plt
from common import *

style()
d = load_e1()
METRIC = os.environ.get("SIZE_METRIC", "pool_frac")  # pool_frac: any D (marginal-law mass); vol_med: Lebesgue volume fraction, D<=5
d = d[d[METRIC].notna()]
if len(sys.argv) > 1:
    d = d[d.file.isin([f if f.endswith(".csv") else f + ".csv" for f in sys.argv[1:]])]
files = [f if f.endswith(".csv") else f + ".csv" for f in sys.argv[1:]] or list(dict.fromkeys(d.file))
files = [f for f in files if f in set(d.file)]
scores = ["l2", "l1", "hell", "kl", "ait", "linf", "nll"]
fig, ax = plt.subplots(1, len(files), figsize=(TEXT_W, 2.3), sharey=True, squeeze=False)
ax = ax[0]
for a, f in zip(ax, files):
    g = d[d.file == f]
    base = g[g.method == "l2"].set_index("rep")[METRIC]
    for i, s in enumerate(scores):
        for v, off in (("plain", -0.18), ("n", 0.0), ("m", 0.18)):
            m = s if v == "plain" else f"{s}_{v}"
            x = g[g.method == m].set_index("rep")[METRIC]
            if x.empty:
                continue
            lr = np.log(x / base).dropna()
            mu, lo, hi, n = mean_ci(lr)
            c = SCORE_COL[s]
            a.errorbar(np.exp(mu), i + off, xerr=[[np.exp(mu) - np.exp(lo)], [np.exp(hi) - np.exp(mu)]], fmt=VARIANT_MK[v], color=c,
                       mfc="white" if v == "plain" else c, ms=3.2, elinewidth=0.7, capsize=1)
    a.axvline(1, color="0.3", lw=0.6, ls="--")
    a.set_xscale("log")
    a.set_xticks([0.5, 1, 2]); a.set_xticklabels(["0.5", "1", "2"]); a.minorticks_off()
    a.set_yticks(range(len(scores)))
    a.set_yticklabels([SCORE_LAB[s] for s in scores])
    if a is ax[len(ax) // 2 - (len(ax) % 2 == 0)]:
        a.set_xlabel(("region mass" if METRIC == "pool_frac" else "region volume") + r" / plain-$L_2$ (paired, geometric mean)", fontsize=7, loc="left" if len(ax) % 2 == 0 else "center")
    r = g.iloc[0]; a.set_title(f"{r['family']}, D={int(r['D'])}\n{'het.' if r['hetero'] else 'hom.'}, {r['pred']}", fontsize=6.5)
    a.grid(axis="x", lw=0.3, color="0.88")
ax[0].invert_yaxis()
fig.subplots_adjust(wspace=0.08)
from matplotlib.lines import Line2D
h = [Line2D([], [], marker=VARIANT_MK[k], ls="", color="0.3", mfc="white" if k == "plain" else "0.3", ms=4, label=VARIANT_LAB[k]) for k in ("plain", "n", "m")]
fig.legend(handles=h, loc="lower center", ncol=3, frameon=False, bbox_to_anchor=(0.5, -0.22))
save(fig, "fig2_size.pdf" if METRIC == "pool_frac" else "fig2_size_volume.pdf")
