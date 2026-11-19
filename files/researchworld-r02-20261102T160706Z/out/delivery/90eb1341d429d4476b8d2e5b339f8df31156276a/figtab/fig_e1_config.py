"""Per-configuration E1 summary: validity, conditional coverage, efficiency (one 3-panel figure per results file).
Usage: python figtab/fig_e1_config.py [glob]   (default: all results/e1/main_*.csv)
Claim supported: (a) all split-conformal scores are marginally valid at 1-alpha (+/- finite-sample slack) regardless of the score;
(b) they differ strongly in conditional coverage near the simplex boundary and in region size, i.e. validity does not discriminate scores.
Error bars: 95% t-interval of the mean over R independent replicates (fresh data, fit, calibration split each).
"""
import sys
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from common import *

style()
d = load_e1(sys.argv[1] if len(sys.argv) > 1 else "main*_*.csv")


def dotpanel(ax, a, order, xlabel, ref=None, xlim=None):
    for i, m in enumerate(order):
        r = a[a.method == m].iloc[0]
        c = SCORE_COL[r.score]
        fill = c if r.variant != "plain" else "white"
        ax.errorbar(r["mean"], i, xerr=[[r["mean"] - r.lo], [r.hi - r["mean"]]], fmt=VARIANT_MK[r.variant], color=c, mfc=fill,
                    ms=3.8, mew=0.8, elinewidth=0.8, capsize=1.5)
    if ref is not None:
        ax.axvline(ref, color="0.3", lw=0.7, ls="--", zorder=0)
    ax.set_yticks(range(len(order)))
    ax.set_xlabel(xlabel)
    ax.grid(axis="x", lw=0.3, color="0.85")
    if xlim:
        ax.set_xlim(*xlim)


for f, g in d.groupby("file"):
    cfg = g.iloc[0]
    R, n = g.rep.nunique(), int(cfg.n_cal)
    order = list(dict.fromkeys(g.method))
    labels = []
    for m in order:
        s, v = split_method(m)
        labels.append(SCORE_LAB[s] + {"plain": "", "n": " (norm.)", "m": " (Mond.)", "cvp": " (CV+)"}[v])
    fig, ax = plt.subplots(1, 4, figsize=(TEXT_W, 0.19 * len(order) + 0.9), sharey=True, gridspec_kw=dict(wspace=0.12))
    # (a) marginal coverage at alpha=0.1 minus nominal, in percentage points; expected value of the split-conformal coverage is ceil((1-a)(n+1))/(n+1)
    g = g.assign(ex=100 * (g.cov10 - 0.9))
    dotpanel(ax[0], agg(g, "ex"), order, r"marginal cov. $-$ 90% (pp)", ref=0.0)
    exp_cov = np.ceil(0.9 * (n + 1)) / (n + 1)
    ax[0].axvline(100 * (exp_cov - 0.9), color="0.6", lw=0.7, ls=":", zorder=0)
    # (b) boundary / interior coverage
    dotpanel(ax[1], agg(g, "bnd_cov"), order, rf"cov. | $\min_j y_j<0.01$", ref=0.9)
    dotpanel(ax[2], agg(g, "int_cov"), order, rf"cov. | $\min_j y_j\geq0.01$", ref=0.9)
    # (c) region size
    dotpanel(ax[3], agg(g, "vol_med") if g.vol_med.notna().any() else agg(g.assign(vol_med=np.nan), "vol_med"), order,
             "median region volume\n(fraction of simplex)")
    ax[0].set_yticklabels(labels)
    ax[0].invert_yaxis()
    for a_, t in zip(ax, ["(a) marginal", "(b) near boundary", "(c) interior", "(d) size"]):
        a_.set_title(t, loc="left", fontsize=8)
    ttl = f"{cfg.family}, D={cfg.D}, {'heterosc.' if cfg.hetero else 'homosc.'}, predictor={cfg.pred}; n_cal={n}, R={R}; "
    fig.text(0.0, 1.0, ttl + r"$\alpha=0.1$; bars: 95% CI over replicates", fontsize=7, va="bottom")
    h = [Line2D([], [], marker=VARIANT_MK[k], ls="", color="0.3", mfc="white" if k == "plain" else "0.3", ms=4, label=VARIANT_LAB[k]) for k in ["plain", "n", "m", "cvp"] if k in set(g.variant)]
    fig.legend(handles=h, loc="lower center", ncol=len(h), frameon=False, bbox_to_anchor=(0.5, -0.16))
    save(fig, f.replace("main_", "e1_").replace(".csv", ".pdf"))
