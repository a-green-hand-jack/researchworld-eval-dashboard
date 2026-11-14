"""Shared helpers for figure/table scripts.

All scripts read the tidy result tables of experiment-repo from --results (default: <root>/results)
and write to --out. Nothing here generates data.
"""
import argparse
import os
import numpy as np
import pandas as pd
import matplotlib as mpl

mpl.use("Agg")
import matplotlib.pyplot as plt

# Okabe-Ito colour-blind-safe palette; each rule keeps one colour and one marker in every figure.
RULE_STYLE = {
    "condorcet_winner": ("#7F3C8D", "H"), "trimmed_mean:0.2": ("#E69F00", "^"),
    "mean": ("#0072B2", "o"), "median": ("#D55E00", "s"), "trimmed_mean": ("#E69F00", "^"),
    "geomean": ("#56B4E9", "v"), "min": ("#000000", "x"), "borda": ("#009E73", "D"),
    "win_rate": ("#CC79A7", "P"), "plurality": ("#999999", "*"), "copeland": ("#F0E442", "h"),
    "power_mean": ("#0072B2", "o"),
}
RULE_LABEL = {
    "condorcet_winner": "Condorcet winner", "trimmed_mean:0.2": "trimmed mean (20%)", "geomean:0": "geometric mean",
    "mean": "mean", "median": "median", "trimmed_mean": "trimmed mean", "geomean": "geometric mean", "min": "minimum",
    "borda": "Borda / mean win rate", "win_rate": "mean win rate", "plurality": "plurality", "copeland": "Copeland",
    "power_mean": "power mean",
}
LB_LABEL = {"openllm_v2": "Open LLM Lb. v2", "helm_mmlu": "HELM MMLU"}
GAIN_LABEL = {"G1": "G1: cap = best+1", "G1_add10": "G1, <=+10 pts", "G1_add20": "G1, <=+20 pts", "G2_0.25": "G2: 25% of gap",
              "G2_0.5": "G2: 50% of gap", "G2_1": "G2: 100% of gap", "ceil": "cap = 100", "ceil_add10": "cap 100, <=+10 pts"}
GAIN_STYLE = {"G1": ("#0072B2", "o"), "G1_add10": ("#009E73", "s"), "G2_0.5": ("#D55E00", "^"), "ceil": ("#000000", "D")}
# the three main boards: (leaderboard, granularity, population, panel title)
BOARDS = [("helm_mmlu", "headline", "all", "HELM MMLU\n57 subjects, 79 models"),
          ("openllm_v2", "headline", "no_flagged", "Open LLM Lb. v2\nheadline, 6 tasks"),
          ("openllm_v2", "subtask", "subtask_pool_699", "Open LLM Lb. v2\nsub-tasks, 39 tasks")]
GRAN_LABEL = {"headline": "headline tasks", "subtask": "sub-tasks"}


def args(desc, extra=None):
    p = argparse.ArgumentParser(description=desc)
    here = os.path.dirname(os.path.abspath(__file__))
    root = os.path.join(here, "..", "..")  # delivery root (paper-repo): figures/scripts -> root
    p.add_argument("--results", default=os.path.join(root, "results"))
    p.add_argument("--out", default=os.path.join(root, "figures"), help="figures go here, tables to --tables-out")
    p.add_argument("--tables-out", default=os.path.join(root, "tables"))
    p.add_argument("--width", type=float, default=5.5, help="text width in inches (set from the venue template)")
    p.add_argument("--seed", type=int, default=0)
    if extra:
        extra(p)
    a = p.parse_args()
    os.makedirs(a.out, exist_ok=True)
    os.makedirs(a.tables_out, exist_ok=True)
    return a


def setup(width):
    mpl.rcParams.update({
        "font.size": 8, "axes.labelsize": 8, "axes.titlesize": 8, "legend.fontsize": 7, "xtick.labelsize": 7,
        "ytick.labelsize": 7, "axes.spines.top": False, "axes.spines.right": False, "axes.linewidth": 0.6,
        "pdf.fonttype": 42, "ps.fonttype": 42, "figure.dpi": 150, "savefig.bbox": "tight", "font.family": "serif",
        "mathtext.fontset": "cm", "axes.grid": True, "grid.color": "#dddddd", "grid.linewidth": 0.4,
    })


def read(a, name):
    return pd.read_csv(os.path.join(a.results, name))


def save(fig, a, name):
    for ext in ("pdf", "png"):
        fig.savefig(os.path.join(a.out, f"{name}.{ext}"), dpi=300 if ext == "png" else None)
    plt.close(fig)


def boot_ci(x, stat, rng, B=1000, level=0.95):
    """Percentile bootstrap CI of stat(x) resampling the entries of x (targets)."""
    x = np.asarray(x)
    n = len(x)
    if n == 0:
        return np.nan, np.nan
    idx = rng.integers(0, n, size=(B, n))
    vals = np.array([stat(x[i]) for i in idx])
    lo = (1 - level) / 2
    return tuple(np.quantile(vals, [lo, 1 - lo]))


def latex_escape(s):
    return (str(s).replace("_", r"\_").replace("%", r"\%").replace("&", r"\&").replace(">=", r"$\geq$"))


def fmt_ci(est, lo, hi, d=1):
    if pd.isna(est):
        return "--"
    return f"{est:.{d}f} [{lo:.{d}f}, {hi:.{d}f}]"


def caption(a, name, text):
    """Settings text that belongs in the LaTeX caption; written next to the figure so the paper caption can be checked."""
    with open(os.path.join(a.out, f"{name}.settings.txt"), "w") as f:
        f.write(text + "\n")


def write_table(a, name, body, colspec, header, caption_note=""):
    """Write a booktabs tabular (no float/caption: the paper owns captions) to tables/<name>.tex."""
    lines = [r"\begin{tabular}{" + colspec + "}", r"\toprule", " & ".join(header) + r" \\", r"\midrule"]
    lines += [" & ".join(map(str, r)) + r" \\" for r in body]
    lines += [r"\bottomrule", r"\end{tabular}"]
    with open(os.path.join(a.tables_out, name + ".tex"), "w") as f:
        f.write("\n".join(lines) + "\n")
    if caption_note:
        with open(os.path.join(a.tables_out, name + ".settings.txt"), "w") as f:
            f.write(caption_note + "\n")
