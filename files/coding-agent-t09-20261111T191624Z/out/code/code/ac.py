"""Shared helpers for analysis / figures."""
import numpy as np, pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

RES = "/work/results"
FIG = "/work/paper/figs"
TAB = "/work/paper/tables"
# categorical slots from the validated default palette (light mode), fixed order
C = dict(blue="#2a78d6", orange="#eb6834", aqua="#1baf7a", magenta="#e87ba4", violet="#6250d6", yellow="#eda100", red="#e34948", green="#008300")
INK, INK2 = "#0b0b0b", "#52514e"
plt.rcParams.update({
    "font.size": 8, "axes.titlesize": 8.5, "axes.labelsize": 8, "legend.fontsize": 7, "xtick.labelsize": 7.5, "ytick.labelsize": 7.5,
    "axes.spines.top": False, "axes.spines.right": False, "axes.edgecolor": INK2, "axes.labelcolor": INK, "text.color": INK,
    "xtick.color": INK2, "ytick.color": INK2, "axes.grid": True, "grid.color": "#e6e5e1", "grid.linewidth": 0.5,
    "lines.linewidth": 1.4, "lines.markersize": 4.5, "figure.dpi": 150, "savefig.bbox": "tight", "pdf.fonttype": 42,
    "axes.axisbelow": True,
})


def load(name):
    return pd.read_csv(f"{RES}/{name}.csv")


def gkey(df):
    """readable graph label"""
    def f(r):
        n = r["graph_name"]
        if n in ("stanford3", "egofb"):
            return {"stanford3": "Stanford3", "egofb": "ego-Facebook"}[n]
        return {"er": "ER", "regular": "Reg", "sbm": "SBM", "ba": "BA", "ws": "WS"}[n]
    return df.apply(f, axis=1)


def agg_worlds(df, keys, cols=("bias", "sd", "rmse", "truth", "fail", "lev", "lev_theory", "mean_deg", "cut_frac", "proj_bias_theory",
                               "cov_hc", "cov_cr", "cov_hac", "n_clusters", "se_ratio_hc", "se_ratio_cr", "se_ratio_hac")):
    """mean over independent worlds, plus across-world min/max/sem for rmse and bias"""
    cols = [c for c in cols if c in df.columns]
    g = df.groupby(keys, dropna=False)
    out = g[cols].mean()
    out["n_worlds"] = g.size()
    for c in ("rmse", "bias", "cov_hc", "cov_cr", "cov_hac"):
        if c in df.columns:
            out[c + "_sem"] = g[c].std(ddof=1) / np.sqrt(g.size())
            out[c + "_min"] = g[c].min()
            out[c + "_max"] = g[c].max()
    return out.reset_index()


def save(fig, name):
    fig.savefig(f"{FIG}/{name}.pdf")
    fig.savefig(f"{FIG}/{name}.png", dpi=170)
    plt.close(fig)
