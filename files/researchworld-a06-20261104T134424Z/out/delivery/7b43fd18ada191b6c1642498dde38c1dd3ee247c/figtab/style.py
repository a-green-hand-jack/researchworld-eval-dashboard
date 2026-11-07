"""Shared rendering conventions (NeurIPS 2026 template: text width 5.5 in, >=7 pt fonts, legible in B/W)."""
import os
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__))
RESULTS = os.environ.get("RESULTS_DIR", os.path.join(HERE, "..", "results"))  # delivery layout: results/ at the root
OUT = os.environ.get("FIG_OUT", os.path.join(HERE, "..", "paper", "figures"))
W = 5.5  # inches, full text width

# Okabe-Ito (colour-blind safe); every series also gets its own marker and line style
OI = ["#0072B2", "#D55E00", "#009E73", "#CC79A7", "#E69F00", "#56B4E9", "#000000"]
MARK = ["o", "s", "^", "D", "v", "P", "X"]
LS = ["-", "--", "-.", ":", (0, (5, 1)), (0, (3, 1, 1, 1)), "-"]

EST_LABEL = {"naive": "naive (same items)", "split": "held-out split", "crossfit": "5-fold cross-fit",
             "boot_opt": "bootstrap optimism", "boot_oob": "bootstrap out-of-bag", "simul": "simultaneous bound",
             "cond": "conditional (winner-aware)"}
EST_ORDER = ["naive", "split", "crossfit", "boot_opt", "boot_oob", "simul", "cond"]
EST_STYLE = {e: (OI[i], MARK[i], LS[i]) for i, e in enumerate(EST_ORDER)}
PROC_LABEL = {"argmax": "best-of-K", "sh": "successive halving", "greedy": "greedy coordinate"}

def setup():
    plt.rcParams.update({
        "font.size": 7.5, "axes.titlesize": 8, "axes.labelsize": 7.5, "xtick.labelsize": 7, "ytick.labelsize": 7,
        "legend.fontsize": 7, "legend.frameon": False, "axes.spines.top": False, "axes.spines.right": False,
        "axes.linewidth": 0.6, "lines.linewidth": 1.2, "lines.markersize": 3.5, "pdf.fonttype": 42, "ps.fonttype": 42,
        "font.family": "serif", "mathtext.fontset": "stix", "figure.dpi": 150,
    })

def load_synth():
    return pd.read_csv(os.path.join(RESULTS, "synthetic_main_summary.csv"))

def load_plan():
    return pd.read_csv(os.path.join(RESULTS, "synth_plan_summary.csv"))

def save(fig, name):
    os.makedirs(OUT, exist_ok=True)
    p = os.path.join(OUT, name)
    fig.savefig(p, bbox_inches="tight")
    plt.close(fig)
    print("wrote", os.path.normpath(p))

def binom_band(p0, reps, z=1.96):
    h = z * np.sqrt(p0 * (1 - p0) / reps)
    return p0 - h, p0 + h

def tau_title(t):
    return r"$\tau$ = %g" % t
