"""Shared matplotlib style for every figure of the paper.

Sizes come from `venue.json` (written from venue-repo's requirements); until the
venue's numbers arrive the defaults below are the common ICML/ICLR/NeurIPS
two-sizes: a full text-width figure and a half-width panel. Every figure is
drawn at the width the document places it at, so the type is never rescaled.
"""
import json
import os

import matplotlib as mpl

DEFAULT_VENUE = {
    "text_width_in": 5.5,      # NeurIPS/ICLR single column; ICML two-column uses 6.75 (full) / 3.25 (col)
    "column_width_in": 2.65,
    "min_font_pt": 7.0,        # smallest type allowed in a figure at placed size
    "body_font_pt": 9.0,
}

# Okabe-Ito colour-blind-safe palette, one fixed colour + marker + dash per rule
# family so that a rule is recognisable across every figure and in greyscale.
RULES = ["mean", "median", "min", "borda", "plurality", "copeland"]
BOARD_LABEL = {"helm_mmlu": "HELM MMLU", "ollb_bench": "OLLB ($m=6$)", "ollb_sub": "OLLB ($m=39$)"}
RULE_LABEL = {
    "mean": "mean", "median": "median", "min": "min", "borda": "mean rank (Borda)",
    "plurality": "plurality", "copeland": "Copeland",
}
RULE_STYLE = {
    "mean":      dict(color="#0072B2", marker="o", ls="-"),
    "median":    dict(color="#D55E00", marker="s", ls="--"),
    "min":       dict(color="#000000", marker="v", ls=":"),
    "borda":     dict(color="#009E73", marker="^", ls="-."),
    "plurality": dict(color="#CC79A7", marker="P", ls="--"),
    "copeland":  dict(color="#E69F00", marker="X", ls="-."),
}


def venue():
    path = os.path.join(os.path.dirname(__file__), "..", "venue.json")
    cfg = dict(DEFAULT_VENUE)
    if os.path.exists(path):
        cfg.update(json.load(open(path)))
    return cfg


def apply():
    v = venue()
    base = v["body_font_pt"] - 1.0
    mpl.rcParams.update({
        "font.family": "serif", "mathtext.fontset": "cm",
        "font.size": base, "axes.titlesize": base, "axes.labelsize": base,
        "xtick.labelsize": v["min_font_pt"], "ytick.labelsize": v["min_font_pt"],
        "legend.fontsize": v["min_font_pt"], "legend.frameon": False,
        "axes.spines.top": False, "axes.spines.right": False,
        "axes.linewidth": 0.6, "lines.linewidth": 1.3, "lines.markersize": 3.5,
        "grid.linewidth": 0.4, "grid.alpha": 0.35, "axes.grid": True,
        "pdf.fonttype": 42, "ps.fonttype": 42,   # embed TrueType, no Type 3 fonts
        "savefig.bbox": "tight", "savefig.pad_inches": 0.02,
    })
    return v


def size(kind="full", aspect=0.38):
    """(width, height) in inches for a figure placed at full or column width."""
    v = venue()
    w = v["text_width_in"] if kind == "full" else v["column_width_in"]
    return (w, w * aspect)
