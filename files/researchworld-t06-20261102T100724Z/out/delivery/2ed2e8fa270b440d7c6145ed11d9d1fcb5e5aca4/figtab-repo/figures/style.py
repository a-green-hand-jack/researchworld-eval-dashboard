"""Shared figure style: NeurIPS 2026 text width (5.5 in, one column), one encoding per design.

Design keys follow PLAN.md section 2: A crowd votes, M-h expert, M-g model judge, N sports.
"""
import matplotlib as mpl

TEXT_WIDTH_IN = 5.5   # neurips_2026.sty: textwidth=5.5in
MIN_FONT_PT = 7

# Okabe-Ito; M-h / M-g also differ in marker and fill so the matched pair survives greyscale.
DESIGNS = {
    "A":   dict(label="Arena (crowd votes)",      color="#0072B2", marker="o", fill=True),
    "M-h": dict(label="MT-Bench (expert)",        color="#D55E00", marker="s", fill=True),
    "M-g": dict(label="MT-Bench (GPT-4 judge)",   color="#E69F00", marker="^", fill=False),
    "N":   dict(label="NBA (sports)",             color="#009E73", marker="D", fill=True),
}


def apply():
    mpl.rcParams.update({
        "font.size": 8, "axes.titlesize": 8, "axes.labelsize": 8,
        "xtick.labelsize": 7, "ytick.labelsize": 7, "legend.fontsize": 7,
        "axes.spines.top": False, "axes.spines.right": False,
        "axes.grid": True, "grid.color": "#dddddd", "grid.linewidth": 0.5,
        "axes.axisbelow": True, "pdf.fonttype": 42, "ps.fonttype": 42,
        "figure.dpi": 150, "savefig.dpi": 300, "savefig.bbox": "tight",
    })


def marker_kw(key):
    d = DESIGNS[key]
    return dict(color=d["color"], marker=d["marker"],
                markerfacecolor=d["color"] if d["fill"] else "white", markeredgecolor=d["color"])
