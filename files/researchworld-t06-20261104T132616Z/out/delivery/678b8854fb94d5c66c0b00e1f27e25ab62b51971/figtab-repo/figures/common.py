"""Shared style and loaders for the figure/table generators.

Every generator takes `--results DIR` (a `results/` directory of paper-repo / experiment-repo) and `--out DIR`.
"""
import argparse
import hashlib
import json
import os

import matplotlib as mpl
import pandas as pd

# NeurIPS text width is 5.5 in.
TEXTWIDTH = 5.5

# One colour and one marker per evaluation design, used identically in every figure
# (Okabe-Ito; the marker is the secondary encoding for colour-vision deficiency).
DESIGNS = ["crowd", "expert", "llm_judge", "sports"]
DESIGN_LABEL = {"crowd": "crowd votes", "expert": "expert labels", "llm_judge": "LLM judge", "sports": "sports"}
DESIGN_COLOR = {"crowd": "#0072B2", "expert": "#D55E00", "llm_judge": "#009E73", "sports": "#CC79A7"}
DESIGN_MARKER = {"crowd": "o", "expert": "s", "llm_judge": "^", "sports": "D"}
DATASET_LABEL = {
    "arena55k": "Arena 55k (top 20 ranks)",
    "mt_human": "MT-Bench, human experts",
    "mt_gpt4": "MT-Bench, GPT-4 judge",
    "nba_all": "NBA, all seasons pooled (top 20 ranks)",
}
INK = "#222222"
MUTED = "#666666"
GRID = "#dddddd"


def set_style():
    mpl.rcParams.update({
        "font.family": "serif", "font.serif": ["DejaVu Serif"], "font.size": 7.5,
        "axes.labelsize": 7.5, "axes.titlesize": 8, "xtick.labelsize": 7, "ytick.labelsize": 7,
        "legend.fontsize": 7, "axes.edgecolor": MUTED, "axes.labelcolor": INK, "text.color": INK,
        "xtick.color": MUTED, "ytick.color": MUTED, "axes.linewidth": 0.6,
        "axes.spines.top": False, "axes.spines.right": False,
        "axes.grid": True, "grid.color": GRID, "grid.linewidth": 0.5, "axes.axisbelow": True,
        "lines.linewidth": 1.2, "pdf.fonttype": 42, "ps.fonttype": 42, "savefig.dpi": 300,
        "figure.dpi": 150,
    })


def args(description):
    p = argparse.ArgumentParser(description=description)
    p.add_argument("--results", required=True, help="results/ directory with the committed result files")
    p.add_argument("--out", default=".", help="output directory")
    return p.parse_args()


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def record_inputs(out, name, files):
    """Append the input files (sha256) behind output `name` to MANIFEST.json in `out`."""
    path = os.path.join(out, "MANIFEST.json")
    m = json.load(open(path)) if os.path.exists(path) else {}
    m[name] = {os.path.basename(f): sha256(f) for f in files}
    json.dump(m, open(path, "w"), indent=1, sort_keys=True)


SECONDARY_SUFFIX = "_top20count"  # secondary claim set (challengers among the 20 most-compared only), kept in the result files


def read(results, name, secondary=False):
    """Read a result file; rows of the secondary claim sets (`<dataset>_top20count`) are dropped unless `secondary`."""
    d = pd.read_csv(os.path.join(results, name))
    if not secondary and "dataset" in d.columns:
        d = d[~d.dataset.astype(str).str.endswith(SECONDARY_SUFFIX)]
    return d


UNIT_DESIGN = {"arena55k": "crowd", "mt_human": "expert", "mt_gpt4": "llm_judge", "nba_all": "sports"}
BASE_UNITS = list(UNIT_DESIGN)
SHORT_LABEL = {"arena55k": "Arena 55k", "mt_human": "MT-Bench human", "mt_gpt4": "MT-Bench GPT-4", "nba_all": "NBA all seasons",
               "nba_seasons": "NBA single seasons"}


def design_of(unit):
    return UNIT_DESIGN.get(unit, "sports")


def adv_c2(results):
    """Adjacent-pair claims with a strictly ordered base fit (exact ties excluded), as in the regressions."""
    a = read(results, "adv_budgets.csv")
    return a[(a.claim_type == "C2") & (~a.exact_tie) & (a.verified)].copy()


def panel_letter(ax, s):
    ax.text(-0.02, 1.04, s, transform=ax.transAxes, fontweight="bold", fontsize=8.5, ha="right", va="bottom")
