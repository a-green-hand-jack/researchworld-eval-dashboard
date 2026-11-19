"""Shared matplotlib style for the paper's figures (NeurIPS 2026 text width 5.5 in)."""
import matplotlib as mpl

TEXT_WIDTH_IN = 5.5
# colour-blind-safe (Okabe-Ito) cycle; T0 = synthetic, T1 = real MMLU-Pro cache, T2 = live tool
OKABE_ITO = ["#0072B2", "#D55E00", "#009E73", "#CC79A7", "#E69F00", "#56B4E9", "#000000"]
TIER_COLOUR = {"T0": "#0072B2", "T1": "#D55E00", "T2": "#009E73"}


def apply():
    mpl.rcParams.update({
        "font.family": "serif", "font.size": 8, "axes.titlesize": 8, "axes.labelsize": 8,
        "legend.fontsize": 7, "xtick.labelsize": 7, "ytick.labelsize": 7,
        "axes.prop_cycle": mpl.cycler(color=OKABE_ITO),
        "axes.spines.top": False, "axes.spines.right": False,
        "pdf.fonttype": 42, "savefig.bbox": "tight", "figure.dpi": 150,
    })
