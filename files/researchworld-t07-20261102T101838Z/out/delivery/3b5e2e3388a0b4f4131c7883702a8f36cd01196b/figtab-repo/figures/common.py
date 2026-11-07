"""Shared style, method colours and metric/bootstrap helpers for all figure scripts."""
import numpy as np
import matplotlib as mpl

TEXTWIDTH_IN = 5.5  # NeurIPS 2026 template textwidth (venue/template/neurips_2026.sty)

mpl.rcParams.update({
    "pdf.fonttype": 42, "ps.fonttype": 42,        # embedded TrueType, accepted by the venue checker
    "font.size": 8, "axes.labelsize": 8.5, "axes.titlesize": 8.5,
    "legend.fontsize": 7, "xtick.labelsize": 7, "ytick.labelsize": 7,
    "axes.spines.top": False, "axes.spines.right": False,
    "axes.grid": True, "grid.alpha": 0.25, "grid.linewidth": 0.5,
    "lines.linewidth": 1.3, "lines.markersize": 3.5,
    "figure.dpi": 150, "savefig.bbox": "tight", "savefig.pad_inches": 0.02,
})

# Okabe-Ito (colour-blind safe) plus grey/brown; marker and line style are redundant with colour so figures stay
# legible in black and white. The baseline B1 is black and drawn heavier; the proposed method P3 is vermillion.
LABELS = {"const": "B0 mean-of-sources", "random+mean": "B1 random", "strat+mean": "B2 stratified",
          "random+cal": "B3 random+cal.", "anchor+anchor": "Anchor points", "anchor+irt": "Anchor+IRT",
          "random+lowrank": "Random+low-rank", "omp+ridge": "P1 OMP+ridge",
          "strat+lowrank_dr": "P3 DR", "strat+lowrank_eb": "P3 EB"}
_FIXED = {
    "const": dict(color="#999999", marker="x", ls=":", lw=1.0),
    "random+mean": dict(color="#000000", marker="o", ls="-", lw=2.0),
    "strat+mean": dict(color="#56B4E9", marker="s", ls="-", lw=1.2),
    "random+cal": dict(color="#009E73", marker="^", ls="-", lw=1.2),
    "anchor+anchor": dict(color="#E69F00", marker="v", ls="--", lw=1.2),
    "anchor+irt": dict(color="#CC79A7", marker="D", ls="--", lw=1.2),
    "random+lowrank": dict(color="#0072B2", marker="P", ls="-.", lw=1.2),
    "omp+ridge": dict(color="#8B5A2B", marker="*", ls="-.", lw=1.2),
    "strat+lowrank_dr": dict(color="#D55E00", marker="s", ls="-", lw=1.6),
    "strat+lowrank_eb": dict(color="#D55E00", marker="^", ls="--", lw=1.6),
}
_PALETTE = ["#0072B2", "#D55E00", "#009E73", "#CC79A7", "#E69F00", "#56B4E9", "#F0E442", "#000000"]
_registry = {}


def label(method):
    return LABELS.get(method, method)


def style(method):
    """Fixed colour/marker/linestyle per method name, identical in every figure of a run."""
    if method not in _registry:
        i = len(_registry)
        _registry[method] = _FIXED.get(method, dict(color=_PALETTE[i % 8], marker="o", ls="-", lw=1.2))
    return _registry[method]


def register(methods):
    for m in methods:
        style(m)


def mae(t, p):
    return float(np.mean(np.abs(np.asarray(p) - np.asarray(t))))


def rmse(t, p):
    return float(np.sqrt(np.mean((np.asarray(p) - np.asarray(t)) ** 2)))


def boot_ci(x, stat=np.mean, B=2000, alpha=0.05, rng=None):
    """Percentile bootstrap CI of stat(x) over units in x."""
    rng = rng or np.random.default_rng(0)
    x = np.asarray(x, float)
    x = x[~np.isnan(x)]
    if len(x) == 0:
        return np.nan, np.nan, np.nan
    idx = rng.integers(0, len(x), size=(B, len(x)))
    bs = np.array([stat(x[i]) for i in idx]) if stat is not np.mean else x[idx].mean(1)
    return float(stat(x)), float(np.quantile(bs, alpha / 2)), float(np.quantile(bs, 1 - alpha / 2))
