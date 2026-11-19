"""Shared loading, statistics and style for the figure/table generators.

Paths follow paper-repo: figures/src (this code), figures/*.pdf, figures/tables. Inputs (experiment-repo): RESULTS_DIR/<sweep>_runs.csv, <sweep>_cells.csv, <sweep>_stats.json and
RUNS_DIR/<sweep>/*.json (per-run logs). Set with env FIGTAB_RESULTS / FIGTAB_RUNS (defaults: sibling
checkout of experiment-repo). Nothing is recomputed that analyze.py already provides; only KM curves
of t_gen (not in analyze.py) are computed here, from the runs CSV.
"""
import glob, json, os
import numpy as np
import pandas as pd
import matplotlib as mpl
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__))
FIGROOT = os.path.abspath(os.path.join(HERE, ".."))          # paper-repo/figures
PAPER = os.path.abspath(os.path.join(FIGROOT, ".."))          # paper-repo root (results/ and experiments/ live here)
EXP = os.path.join(PAPER, "..", "experiment-repo")            # fallback: sibling checkout of experiment-repo
_has = os.path.isdir(os.path.join(PAPER, "results"))
RESULTS = os.environ.get("FIGTAB_RESULTS", os.path.join(PAPER if _has else EXP, "results"))
RUNS = os.environ.get("FIGTAB_RUNS", os.path.join(PAPER if _has else EXP, "experiments", "runs"))
FIGDIR = os.environ.get("FIGTAB_FIGDIR", FIGROOT)
TABDIR = os.environ.get("FIGTAB_TABDIR", os.path.join(FIGROOT, "tables"))

# Okabe-Ito based, colourblind safe; width is ordinal -> sequential viridis instead (see width_colors)
OI = dict(blue="#0072B2", orange="#E69F00", green="#009E73", verm="#D55E00", purple="#CC79A7", sky="#56B4E9", grey="#666666")
COL_W, TXT_W = 2.6, 5.5   # inches: NeurIPS text width is 5.5 (paper-repo asked for linewidth figures)


def style():
    mpl.rcParams.update({
        "font.size": 8, "axes.labelsize": 8, "axes.titlesize": 8, "legend.fontsize": 7, "xtick.labelsize": 7, "ytick.labelsize": 7,
        "axes.spines.top": False, "axes.spines.right": False, "axes.linewidth": 0.6, "lines.linewidth": 1.0,
        "figure.dpi": 150, "savefig.dpi": 300, "pdf.fonttype": 42, "ps.fonttype": 42, "axes.grid": True,
        "grid.color": "#dddddd", "grid.linewidth": 0.4, "legend.frameon": False})


def width_colors(widths):
    cm = plt.get_cmap("viridis")
    ws = sorted(widths)
    return {w: cm(0.05 + 0.85 * i / max(1, len(ws) - 1)) for i, w in enumerate(ws)}


def load_runs(sweep):
    f = os.path.join(RESULTS, f"{sweep}_runs.csv")
    return pd.read_csv(f) if os.path.exists(f) else pd.DataFrame()


def load_cells(sweep):
    f = os.path.join(RESULTS, f"{sweep}_cells.csv")
    if not os.path.exists(f):
        return pd.DataFrame()
    c = pd.read_csv(f)
    for k in ("tgen_km_median", "tgen_lo", "tgen_hi", "wnorm_fit_mean", "tfit_median", "tfit_lo", "tfit_hi", "delay_km_median", "delay_lo", "delay_hi"):  # absent when no run in the sweep fit the train set
        if k not in c: c[k] = np.nan
    return c


SWEEPS = ("main", "frac", "wd", "wd0", "alpha", "lrscale", "long", "splitfix", "mlp", "mul")


def all_runs(sweeps=SWEEPS):
    d = [load_runs(s) for s in sweeps]
    d = [x for x in d if not x.empty]
    return pd.concat(d, ignore_index=True) if d else pd.DataFrame()


def all_cells(sweeps=SWEEPS):
    d = []
    for s in sweeps:
        c = load_cells(s)
        if not c.empty:
            c.insert(0, "sweep", s); d.append(c)
    return pd.concat(d, ignore_index=True) if d else pd.DataFrame()


def baseline(df):
    """Rows at the primary setting (tf, add, p=53, f=0.4, wd=1, lr=1e-3, init x1, fresh split, no lr rescale): the `main` sweep."""
    return df[(df.arch == "tf") & (df.op == "add") & (df.frac == 0.4) & (df.wd == 1.0) & (df.init_mult == 1.0) & (df.split_seed == -1) & (df.lr_ref == 0)]


def load_mech():
    f = os.path.join(RESULTS, "mech_stats.json")
    return json.load(open(f)) if os.path.exists(f) else {}


def load_stats(sweep):
    f = os.path.join(RESULTS, f"{sweep}_stats.json")
    return json.load(open(f)) if os.path.exists(f) else {}


def load_log(sweep, run_file):
    """run_file: the `file` column of the runs CSV (relative to experiments/)."""
    f = os.path.join(RUNS, sweep, os.path.basename(run_file))
    return json.load(open(f))["log"]


def km_curve(t, event):
    """Kaplan-Meier survival S(t) of right-censored times; returns step-function (times, S) with S(0)=1."""
    t, event = np.asarray(t, float), np.asarray(event, bool)
    order = np.argsort(t, kind="stable"); t, event = t[order], event[order]
    n, S, xs, ys = len(t), 1.0, [0.0], [1.0]
    for i, (ti, ei) in enumerate(zip(t, event)):
        if ei:
            S *= 1 - 1 / (n - i); xs.append(ti); ys.append(S)
    return np.array(xs), np.array(ys)


def logfmt(ax, axis="y"):
    """Plain thousands-separated labels on a log axis, minor ticks (2, 5) labelled so a sub-decade range still shows numbers."""
    from matplotlib.ticker import FuncFormatter, LogLocator
    f = FuncFormatter(lambda v, _: f"{v:,.0f}")
    a = ax.yaxis if axis == "y" else ax.xaxis
    a.set_major_locator(LogLocator(base=10, subs=(1.0,), numticks=12))
    a.set_minor_locator(LogLocator(base=10, subs=(2.0, 3.0, 5.0), numticks=12))
    a.set_major_formatter(f); a.set_minor_formatter(f)
    ax.tick_params(axis=axis, which="minor", labelsize=6)


def nrange(n):
    return f"{int(n.min())}" if n.min() == n.max() else f"{int(n.min())}–{int(n.max())}"


def save(fig, name):
    os.makedirs(FIGDIR, exist_ok=True)
    fig.savefig(os.path.join(FIGDIR, name + ".pdf"), bbox_inches="tight")
    fig.savefig(os.path.join(FIGDIR, name + ".png"), bbox_inches="tight", dpi=200)
    plt.close(fig)


def main_setting(df):
    """One-line description of the (single) condition in df for captions; raises if several."""
    keys = ["arch", "op", "p", "frac", "wd", "lr", "max_steps"]
    u = df[keys].drop_duplicates()
    assert len(u) == 1, f"several conditions: {u}"
    r = u.iloc[0]
    return f"{r.arch}, {r.op} mod {int(r.p)}, train fraction {r.frac}, AdamW lr {r.lr:g}, wd {r.wd:g}, ceiling {int(r.max_steps)} steps"


def caption(name, text):
    """Caption text for figures/<name> (for paper-repo to paste/\\input); kept out of the image so panel widths match the template."""
    os.makedirs(FIGDIR, exist_ok=True)
    open(os.path.join(FIGDIR, name + ".caption.txt"), "w").write(text.strip() + "\n")
