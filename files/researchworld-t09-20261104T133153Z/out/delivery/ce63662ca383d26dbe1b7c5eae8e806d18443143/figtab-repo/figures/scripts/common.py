"""Shared loading, style and uncertainty helpers for the figure/table scripts.

Inputs are the aggregated Monte-Carlo summaries of experiment-repo (`results/summary/e*.csv`,
`theory_vs_sim_e9.csv`). Set FIGTAB_RESULTS to that directory (default: <delivery root>/results/summary);
outputs go to FIGTAB_OUT (default: <delivery root>/figures/out).
"""
import os
import numpy as np
import pandas as pd
import matplotlib as mpl

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
RES = os.environ.get("FIGTAB_RESULTS", os.path.join(ROOT, "results", "summary"))
OUT = os.environ.get("FIGTAB_OUT", os.path.join(ROOT, "figures", "out"))
os.makedirs(OUT, exist_ok=True)

TEXTW = 5.5  # ICLR text width in inches

GNAME = {"sbm:5000,50,20,0.8": "SBM", "ba:5000,10": "BA", "ws:5000,20,0.1": "WS", "er:5000,20": "ER",
         "stanford3": "Stanford3", "ego": "ego-Facebook"}
GORDER = ["SBM", "ER", "WS", "BA", "Stanford3", "ego-Facebook"]
# Okabe-Ito (colour-blind safe); colour follows the entity everywhere in the paper
GCOL = {"SBM": "#0072B2", "ER": "#56B4E9", "WS": "#009E73", "BA": "#D55E00", "Stanford3": "#CC79A7", "ego-Facebook": "#E69F00"}
GMARK = {"SBM": "o", "ER": "s", "WS": "^", "BA": "D", "Stanford3": "v", "ego-Facebook": "P"}
ECOL = {"DM": "#000000", "OLS_f": "#0072B2", "OLS_fd": "#56B4E9", "OLS_quad": "#E69F00", "OLS_cubic": "#D55E00",
        "OLS_big": "#CC79A7", "ORACLE": "#009E73", "ORACLE_D": "#009E73", "GBM": "#999999", "HajekKappa": "#F0E442",
        "HajekFull": "#F0E442", "OLS_zf": "#882255", "OLS_cnt": "#44AA99", "OLS_f2": "#AA4499"}
ELAB = {"DM": "diff. in means", "OLS_f": "OLS $z,f$", "OLS_zf": "OLS $z,f,zf$", "OLS_cnt": "OLS $z$,count",
        "OLS_fd": "OLS $+\\log d$", "OLS_f2": "OLS $+f^{(2)}$", "OLS_quad": "OLS quad", "OLS_cubic": "OLS cubic",
        "OLS_big": "OLS big (11)", "ORACLE": "oracle spec.", "ORACLE_D": "oracle spec.", "GBM": "grad. boosting",
        "HajekFull": "Hájek (full nbhd)", "HajekKappa": "Hájek ($\\kappa$=.75)"}
KLAB = {"linear": "linear", "concave": "concave", "convex": "convex", "sigmoid": "sigmoid"}


def style():
    mpl.rcParams.update({
        "font.family": "STIXGeneral", "mathtext.fontset": "stix", "font.size": 8, "axes.labelsize": 8,
        "axes.titlesize": 8, "legend.fontsize": 7, "xtick.labelsize": 7, "ytick.labelsize": 7,
        "axes.spines.top": False, "axes.spines.right": False, "axes.linewidth": 0.6,
        "xtick.major.width": 0.6, "ytick.major.width": 0.6, "xtick.major.size": 2.5, "ytick.major.size": 2.5,
        "lines.linewidth": 1.2, "lines.markersize": 3.5, "grid.linewidth": 0.4, "grid.color": "#dddddd",
        "axes.grid": True, "axes.axisbelow": True, "legend.frameon": False, "figure.dpi": 150,
        "savefig.dpi": 300, "pdf.fonttype": 42, "ps.fonttype": 42, "legend.handlelength": 1.6,
        "legend.borderaxespad": 0.2, "legend.columnspacing": 1.0,
    })


def load(e):
    p = os.path.join(RES, f"{e}.csv")
    d = pd.read_csv(p)
    d["gname"] = d.graph.map(lambda s: GNAME.get(s, s))
    a = d.graph.str.extract(r"^(\w+):(\d+),(?:\d+,)?(\d+)")
    d["n_nom"] = pd.to_numeric(a[1]); d["d_nom"] = pd.to_numeric(a[2])
    d["p"] = pd.to_numeric(d.design.str.extract(r"bern:([\d.]+)")[0])
    d["dkind"] = d.design.str.split(":").str[0]
    d["dres"] = pd.to_numeric(d.design.str.extract(r"(?:louv|rand):([\d.]+)")[0])
    return d


def rmse_se(d):
    """Delta-method MC SE of the RMSE from bias_se and the SE of the SD (normal approx.)."""
    n = d.n_rep.clip(lower=2)
    var_m2 = 4 * d.bias ** 2 * d.bias_se ** 2 + 2 * d.sd ** 4 / (n - 1)
    return np.sqrt(var_m2) / (2 * d.rmse.clip(lower=1e-12))


def sd_se(d):
    return d.sd / np.sqrt(2 * (d.n_rep.clip(lower=2) - 1))


def cov_se(c, n):
    return np.sqrt(np.clip(c * (1 - c), 1e-4, None) / n)


def save(fig, name):
    p = os.path.join(OUT, name + ".pdf")
    fig.savefig(p, bbox_inches="tight", pad_inches=0.02, metadata={"CreationDate": None, "Creator": "matplotlib"})
    fig.savefig(os.path.join(OUT, name + ".png"), dpi=200, bbox_inches="tight", pad_inches=0.02)
    print("wrote", p)


def present(order, have):
    return [g for g in order if g in set(have)]


def panel_label(ax, s):
    ax.text(0.0, 1.04, s, transform=ax.transAxes, fontsize=8, fontweight="bold", va="bottom", ha="left")


def plainlog(ax, axis="y"):
    """Plain decimal tick labels (0.3, 1, 2) on a log axis, minor ticks labelled too."""
    from matplotlib.ticker import FuncFormatter
    f = FuncFormatter(lambda v, _: f"{v:g}")
    a = ax.yaxis if axis == "y" else ax.xaxis
    a.set_major_formatter(f); a.set_minor_formatter(f)


def symlogy(ax, lin=0.1, ticks=(-10, -1, -0.1, 0, 0.1, 1, 10)):
    """Symmetric-log y axis with plain decimal tick labels; linear inside +-lin. Ticks outside the data range are dropped."""
    from matplotlib.ticker import FuncFormatter, NullLocator
    ax.set_yscale("symlog", linthresh=lin, linscale=0.5)
    ax.margins(y=0.06)
    lo, hi = ax.get_ylim()
    ax.set_yticks([t for t in ticks if lo <= t <= hi])
    ax.yaxis.set_major_formatter(FuncFormatter(lambda v, _: f"{v:g}"))
    ax.yaxis.set_minor_locator(NullLocator())
