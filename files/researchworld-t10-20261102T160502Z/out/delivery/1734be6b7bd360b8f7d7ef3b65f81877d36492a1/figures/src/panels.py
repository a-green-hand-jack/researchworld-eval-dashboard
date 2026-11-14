"""Panel builders shared by the figure scripts (coverage panel, paired-width-ratio panel, legend)."""
import numpy as np
import matplotlib.pyplot as plt
from common import *

ALPHA = 0.05
WLIM = (0.9, 1.3)        # default y range of width-ratio panels; points outside are drawn on the frame and annotated


def jit(x, k, K, log=True, s=0.03):
    x = np.asarray(x, float)
    return x * (1 + s * (k - (K - 1) / 2)) if log else x + s * (k - (K - 1) / 2)


def cov_panel(ax, d, methods, xcol="n", log=True, jitter=0.03, band=True):
    """Coverage with Wilson 95% CIs (experiment's cov_lo/cov_hi), nominal 0.95 line and the Monte-Carlo band
    0.95 +- 1.96 sqrt(.95*.05/R): where a method with exactly nominal coverage lands in 95% of runs."""
    R = int(d["R"].iloc[0])
    if band:
        mc = 1.96 * np.sqrt((1 - ALPHA) * ALPHA / R)
        ax.axhspan(1 - ALPHA - mc, 1 - ALPHA + mc, color="#cfe3f3", lw=0, zorder=0)
    ax.axhline(1 - ALPHA, color="k", lw=0.7, zorder=1)
    for k, m in enumerate(methods):
        s = d[d["method"] == m].sort_values(xcol)
        if s.empty:
            continue
        x = jit(s[xcol].values, k, len(methods), log, jitter)
        y = s["coverage"].values
        ax.errorbar(x, y, yerr=[np.clip(y - s["cov_lo"].values, 0, None), np.clip(s["cov_hi"].values - y, 0, None)], capsize=0, elinewidth=0.6, zorder=3 + k, **kw(m))
    if log:
        ax.set_xscale("log")


def wid_panel(ax, d, methods, xcol="n", log=True, jitter=0.03, ylim=WLIM, floor=None):
    """Paired geometric-mean width ratio vs M3 (same draws), bootstrap 95% CI; ratio = 1 line.
    floor = (x, y, colour): asymptotic prediction drawn dotted."""
    top, bot = ylim[1], ylim[0]
    ax.axhline(1.0, color="k", lw=0.7, zorder=1)
    for k, m in enumerate(methods):
        s = d[d["method"] == m].sort_values(xcol)
        if s.empty:
            continue
        x = jit(s[xcol].values, k, len(methods), log, jitter)
        y, lo, hi = s["ratio_geo"].values, s["ratio_lo"].values, s["ratio_hi"].values
        clip = y > top
        ax.errorbar(x[~clip], y[~clip], yerr=[(y - lo)[~clip], (hi - y)[~clip]], capsize=0, elinewidth=0.6, zorder=3 + k, **kw(m))
        ax.plot(x, np.clip(y, bot, top), **{**kw(m), "label": "_nolegend_"})
        for xi, yi in zip(x[clip], y[clip]):
            ax.annotate(f"{yi:.1f}", (xi, top), xytext=(0, 1.5), textcoords="offset points", fontsize=7, ha="center",
                        va="bottom", color=kw(m)["color"], annotation_clip=False)
    if floor is not None:
        ax.plot(floor[0], floor[1], color=floor[2], lw=0.9, ls=":", zorder=2.5)
    ax.set_ylim(*ylim)
    if log:
        ax.set_xscale("log")


def cat_ticks(axes, xs, rotation=90, labels=None):
    for ax in np.ravel(axes):
        ax.set_xticks(xs)
        ax.set_xticklabels(labels or [str(v) for v in xs], rotation=rotation)
        ax.minorticks_off()


def legend_below(fig, ax, extra=(), ncol=None, y=-0.01):
    h, l = ax.get_legend_handles_labels()
    for hh, ll in extra:
        h.append(hh); l.append(ll)
    fig.legend(h, l, loc="lower center", ncol=ncol or len(h), frameon=False, bbox_to_anchor=(0.5, y), columnspacing=1.0,
               handletextpad=0.4)


FLOOR_H = plt.Line2D([], [], color=METHODS[M4][1], lw=0.9, ls=":")
FLOOR_L = "asymptotic floor for M4"


def floor_curve(d, ds, xcol="n", N=None):
    s = d[(d["method"] == M4)].sort_values(xcol)
    return s[xcol].values, predicted([ds] * len(s), s["n"].values, s["N"].values)
