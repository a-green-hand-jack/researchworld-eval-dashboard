"""Shared style, method registry and loaders for all figure/table scripts.

Inputs come from a checkout of experiment-repo (env EXP_DIR; default `code/` next to `figures/` in paper-repo, else a sibling
`experiment-repo`): `results/summary_final_<grid>.csv` (written by its src/analyze.py), `results/theory_population.csv`,
`results/theory_predicted_ratios.csv`, `results/theory_check_synth.csv`, `results/frozen_choices.json`.
"""
import json
import os
import numpy as np
import pandas as pd
import matplotlib as mpl

HERE = os.path.dirname(os.path.abspath(__file__))
_cands = [os.path.join(HERE, "..", "..", "code"), os.path.join(HERE, "..", "..", "..", "experiment-repo")]
EXP_DIR = os.environ.get("EXP_DIR", next((c for c in _cands if os.path.isdir(os.path.join(c, "results"))), _cands[0]))
OUT_FIG = os.environ.get("FIG_DIR", os.path.join(HERE, ".."))
OUT_TAB = os.environ.get("TAB_DIR", os.path.join(OUT_FIG, "tables"))
os.makedirs(OUT_FIG, exist_ok=True)
os.makedirs(OUT_TAB, exist_ok=True)

TEXT_W = 5.5      # inches: NeurIPS 2026 single-column text width (venue/VENUE.md); every figure is <= this wide
COL_W = 3.4

# Okabe-Ito (colour-blind safe). One colour + marker per method in every figure; the t / jackknife variants of a method
# keep its colour and use a hollow marker with a dotted / dash-dotted line (see kw()).
PAL = dict(grey="#7f7f7f", orange="#E69F00", blue="#0072B2", vermil="#D55E00", green="#009E73", pink="#CC79A7",
           sky="#56B4E9", yellow="#F0E442", black="#000000")


def find_m4():
    """M4 as frozen before the final runs (results/frozen_choices.json, key "M4"); isotonic with a warning if absent."""
    p = os.path.join(EXP_DIR, "results", "frozen_choices.json")
    if os.path.exists(p):
        return json.load(open(p))["M4"]
    print("WARNING: results/frozen_choices.json not found; M4 = cal_iso (provisional)")
    return "cal_iso"


M4 = find_m4()
CAL_NAME = {"cal_iso": "isotonic", "cal_spl": "spline", "cal_bin": "binned", "cal_lin": "linear"}
# key -> (label, colour, marker, linestyle)
METHODS = {
    "classical":  ("M1 classical", PAL["grey"], "s", (0, (4, 2))),
    "ppi":        ("M2 PPI", PAL["orange"], "^", "-"),
    "ppipp_pkg":  ("M3 PPI++ (package)", PAL["blue"], "o", "-"),
    "ppipp_nc":   ("PPI++, unclipped $\\hat\\lambda$", PAL["sky"], "o", "-"),
    "cal_lin":    ("linear-calibrated", PAL["yellow"], "v", "-"),
    "cal_iso":    ("isotonic-calibrated", PAL["vermil"], "D", "-"),
    "cal_spl":    ("spline-calibrated", PAL["pink"], "X", "-"),
    "cal_bin":    ("binned-calibrated", PAL["green"], "P", "-"),
}
METHODS[M4] = ("M4 " + METHODS[M4][0], *METHODS[M4][1:])
for _b, _lab in (("classical", "M1 classical"), ("ppipp_pkg", "M3"), ("ppipp_nc", "PPI++ unclipped"), (M4, "M4")):
    METHODS[_b + "_t"] = (_lab + ", $t$", *METHODS[_b][1:])
METHODS["ppipp_t"] = ("M3, $t$ (own clipped)", PAL["blue"], "o", "-")
METHODS["ppipp_jk"] = ("M5 M3 + jackknife", PAL["blue"], "o", "-")
METHODS[M4 + "_t"] = ("M5 M4, $t$", *METHODS[M4][1:])
for _k in ("cal_lin", "cal_iso", "cal_spl", "cal_bin"):
    if _k + "_t" not in METHODS:
        METHODS[_k + "_t"] = (METHODS[_k][0] + ", $t$", *METHODS[_k][1:])

DATASET_LABEL = {
    "galaxies": "Galaxies", "forest": "Forest", "alphafold": "AlphaFold", "gene_expression": "Gene expression",
    "census_income": "Census income", "census_healthcare": "Census healthcare", "census_education": "Census education",
    "ballots": "Ballots", "plankton": "Plankton",
}
ORDER = list(DATASET_LABEL)
PRIMARY = ["galaxies", "forest", "alphafold", "gene_expression", "census_income", "ballots"]


def setup():
    mpl.rcParams.update({
        "font.family": "serif", "font.serif": ["Times New Roman", "Nimbus Roman", "TeX Gyre Termes", "STIXGeneral", "DejaVu Serif"],
        "font.size": 8, "axes.titlesize": 8, "axes.labelsize": 8, "xtick.labelsize": 7, "ytick.labelsize": 7,
        "legend.fontsize": 7, "axes.spines.top": False, "axes.spines.right": False, "axes.linewidth": 0.6,
        "xtick.major.width": 0.6, "ytick.major.width": 0.6, "lines.linewidth": 1.1, "lines.markersize": 3.5,
        "axes.grid": True, "grid.color": "#e5e5e5", "grid.linewidth": 0.5, "axes.axisbelow": True,
        "figure.dpi": 150, "savefig.dpi": 300, "pdf.fonttype": 42, "ps.fonttype": 42,
        "mathtext.fontset": "stix", "savefig.bbox": "tight", "savefig.pad_inches": 0.02,
    })


def save(fig, name):
    w = fig.get_size_inches()[0]
    assert w <= TEXT_W + 1e-6, f"{name}: {w:.2f} in > text width"
    for ext in ("pdf", "png"):
        fig.savefig(os.path.join(OUT_FIG, f"{name}.{ext}"))


def kw(m):
    """Matplotlib kwargs of a method: t quantile -> hollow marker, dotted line; jackknife -> hollow marker, dash-dot."""
    lab, c, mk, ls = METHODS[m]
    if m.endswith("_t"):
        return dict(color=c, marker=mk, ls=(0, (1, 1.5)), mfc="white", label=lab)
    if m.endswith("_jk"):
        return dict(color=c, marker="s", ls=(0, (4, 1.5, 1, 1.5)), mfc="white", label=lab)
    return dict(color=c, marker=mk, ls=ls, label=lab)


def _path(name):
    p = os.path.join(EXP_DIR, "results", name)
    if not os.path.exists(p):
        raise FileNotFoundError(f"{p} not found (set EXP_DIR to a checkout of experiment-repo with results)")
    return p


def load(name):
    return pd.read_csv(_path(name))


def summary(*grids):
    """Concatenate results/summary_final_<grid>.csv; columns renamed: population->dataset, (width_mean kept),
    ratio_M3_*->ratio_* (paired width ratio to M3 = ppipp_pkg, same replications)."""
    dfs = []
    for g in grids:
        d = pd.read_csv(_path(f"summary_final_{g}.csv"))
        d["grid"] = g
        dfs.append(d)
    d = pd.concat(dfs, ignore_index=True)
    d = d.rename(columns={"population": "dataset", "ratio_M3_geo": "ratio_geo",
                          "ratio_M3_lo": "ratio_lo", "ratio_M3_hi": "ratio_hi"})
    return d


def predicted(dataset, n, N, calibrator=None):
    """Asymptotic width ratio M4 / M3 (population floor, cross-fitted E[Y|f]) from theory_predicted_ratios.csv."""
    t = load("theory_predicted_ratios.csv")
    cal = (calibrator or M4).replace("cal_", "")
    t = t[(t["calibrator"] == cal)].set_index(["dataset", "n", "N"])
    return np.array([t["pred_ratio_M4_vs_M3"].get((d, int(a), int(b)), np.nan) for d, a, b in zip(dataset, n, N)])


def wilson(k, n, a=0.05):
    """Wilson score interval for k successes in n trials (same as experiment-repo src/analyze.py)."""
    from scipy.stats import norm
    z = norm.ppf(1 - a / 2); p = k / n
    c = (p + z * z / (2 * n)) / (1 + z * z / n)
    h = z * np.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / (1 + z * z / n)
    return c - h, c + h
