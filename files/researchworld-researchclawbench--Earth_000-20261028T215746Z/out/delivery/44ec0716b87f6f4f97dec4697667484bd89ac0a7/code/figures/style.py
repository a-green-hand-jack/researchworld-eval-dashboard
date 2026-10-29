"""Shared figure style for the GlaMBIE reconciliation report.

Method colours are fixed (Okabe-Ito, colour-blind safe) and paired with marker
shapes so that identity never relies on colour alone.  The reconciled estimate
is always black.
"""
import os
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[2]
# Workspace layout of the task: data/glambie, report/images, outputs/tables.
DATA = Path(os.environ.get("GLAMBIE_DATA", ROOT / "data" / "glambie"))
IMAGES = Path(os.environ.get("FIG_DIR", ROOT / "report" / "images"))
TABLES = Path(os.environ.get("TABLE_DIR", ROOT / "outputs" / "tables"))
# Results of experiment-repo's reconciliation (code/run_all.py).
RECON = ROOT / "outputs" / "reconciliation"
VALID = ROOT / "outputs" / "validation"

METHODS = ["glaciological", "demdiff", "altimetry", "gravimetry", "combined"]
METHOD_LABEL = {
    "glaciological": "Glaciological",
    "demdiff": "DEM differencing",
    "altimetry": "Altimetry",
    "gravimetry": "Gravimetry",
    "combined": "Hybrid / combined",
}
METHOD_COLOR = {
    "glaciological": "#0072B2",
    "demdiff": "#E69F00",
    "altimetry": "#009E73",
    "gravimetry": "#CC79A7",
    "combined": "#56B4E9",
}
METHOD_MARKER = {
    "glaciological": "o",
    "demdiff": "s",
    "altimetry": "^",
    "gravimetry": "D",
    "combined": "v",
}
RECONCILED_COLOR = "#000000"
REFERENCE_COLOR = "#7f7f7f"  # published GlaMBIE (2024) results

# The three GlaMBIE data groups combined in the consensus.
GROUPS = ["demdiff_and_glaciological", "altimetry", "gravimetry"]
GROUP_LABEL = {
    "demdiff_and_glaciological": "DEM diff. + glaciological",
    "altimetry": "Altimetry",
    "gravimetry": "Gravimetry",
}
GROUP_COLOR = {
    "demdiff_and_glaciological": METHOD_COLOR["demdiff"],
    "altimetry": METHOD_COLOR["altimetry"],
    "gravimetry": METHOD_COLOR["gravimetry"],
}
GROUP_MARKER = {
    "demdiff_and_glaciological": "s",
    "altimetry": "^",
    "gravimetry": "D",
}

# Sea-level equivalent conversion: 362.5 Gt of ice = 1 mm of global mean sea level.
GT_PER_MM_SLE = 362.5

REGIONS = [
    "1_alaska", "2_western_canada_us", "3_arctic_canada_north",
    "4_arctic_canada_south", "5_greenland_periphery", "6_iceland", "7_svalbard",
    "8_scandinavia", "9_russian_arctic", "10_north_asia", "11_central_europe",
    "12_caucasus_middle_east", "13_central_asia", "14_south_asia_west",
    "15_south_asia_east", "16_low_latitudes", "17_southern_andes",
    "18_new_zealand", "19_antarctic_and_subantarctic",
]


def region_label(region, number=True):
    num, name = region.split("_", 1)
    name = name.replace("_", " ").title().replace(" Us", " & US").replace(" And ", " & ")
    name = name.replace("Middle East", "& Middle East")
    return f"{num}. {name}" if number else name


def apply_style():
    plt.rcParams.update({
        "figure.dpi": 100,
        "savefig.dpi": 200,
        "font.size": 9,
        "axes.titlesize": 9.5,
        "axes.labelsize": 9,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "axes.edgecolor": "#444444",
        "axes.grid": True,
        "grid.color": "#e3e3e3",
        "grid.linewidth": 0.6,
        "legend.frameon": False,
        "legend.fontsize": 8,
        "xtick.labelsize": 8,
        "ytick.labelsize": 8,
    })


def save(fig, name):
    IMAGES.mkdir(parents=True, exist_ok=True)
    path = IMAGES / f"{name}.png"
    fig.savefig(path, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    return path


def num(v, fmt=".1f"):
    """Format a number with a typographic minus sign."""
    return format(v, fmt).replace("-", "\u2212")
