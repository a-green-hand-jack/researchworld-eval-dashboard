"""Shared style, loading and aggregation for all figure/table scripts.

Every metric is defined once here, from the per-replicate table
`results/replicates.csv` (one row per replicate x estimator; see
figures/README.md for the schema), so all figures use the same definitions:
  err   = tau_hat - tau_true
  bias  = mean(err),  sd = std(err, ddof=1),  rmse = sqrt(mean(err^2))
  rel_* = metric / |tau_true|   (tau_true is constant within a cell)
Uncertainty: percentile bootstrap over replicates (B=1000, fixed seed).
"""
import os
import numpy as np
import pandas as pd
import matplotlib as mpl

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
RESULTS = os.environ.get("GATE_RESULTS", os.path.join(ROOT, "results"))
OUT = os.environ.get("GATE_FIGOUT", os.path.join(ROOT, "figures"))
TABOUT = os.environ.get("GATE_TABOUT", os.path.join(ROOT, "tables"))

TEXTWIDTH = 5.5  # inches, NeurIPS 2026 \textwidth (neurips_2026.sty)
B_BOOT = 1000
BOOT_SEED = 20261102

# Okabe-Ito colour-blind-safe palette; each estimator also has its own marker,
# so identity never rests on colour alone. Fixed per estimator, never re-assigned.
EST_STYLE = {
    "dm":          dict(color="#555555", marker="s", label="Diff.-in-means"),
    "hajek":       dict(color="#999999", marker="X", label="Hajek, strict exposure"),
    "hajek_q0.75": dict(color="#000000", marker="*", label="Hajek, q=0.75 exposure"),
    "ols_cnt":     dict(color="#F0E442", marker="p", label="OLS(z, neighbour count)"),
    "ols_f":       dict(color="#56B4E9", marker="^", label="OLS(z, f)  [Chin-type]"),
    "ols_f_deg":   dict(color="#009E73", marker="v", label="OLS(z, f, degree int.)"),
    "ols_f2":      dict(color="#0072B2", marker="D", label="OLS(z, f, 2-hop)"),
    "ols_poly":    dict(color="#E69F00", marker="o", label="OLS(z, f, f^2, z*f)"),
    "ols_f_adj":   dict(color="#CC79A7", marker="P", label="OLS(z, f) + covariates"),
    "ols_cnt_adj": dict(color="#B8860B", marker="d", label="OLS(z, count) + covariates"),
    "ols_f_both":  dict(color="#44AA99", marker=">", label="OLS(z, f, count)"),
    "ols_poly3":   dict(color="#AA4499", marker="8", label="OLS cubic in f"),
    "ridge_rich":  dict(color="#882255", marker="<", label="Ridge, rich features"),
    "gbm":         dict(color="#D55E00", marker="h", label="Gradient boosting"),
}
MECH_LABEL = {"M1": "M1 linear in neighbour fraction", "M3": "M3 saturating in fraction",
              "M4": "M4 + 2-hop term", "M5": "M5 degree-heterogeneous spill-over"}
GRAPH_LABEL = {"er": "ER", "sbm": "SBM", "ba": "BA", "ws": "WS",
               "fb_ego": "ego-FB", "fb_stanford": "Stanford3"}
DESIGN_LABEL = {"bern0.5": "Bernoulli(0.5)", "bern0.1": "Bernoulli(0.1)", "cluster0.5": "graph-cluster (p=0.5)"}


def setup_style():
    mpl.rcParams.update({
        "font.family": "serif", "font.serif": ["DejaVu Serif"],
        "font.size": 8, "axes.labelsize": 8, "axes.titlesize": 8,
        "xtick.labelsize": 7, "ytick.labelsize": 7, "legend.fontsize": 7,
        "axes.spines.top": False, "axes.spines.right": False,
        "axes.linewidth": 0.6, "lines.linewidth": 1.2, "lines.markersize": 4.5,
        "grid.color": "#dddddd", "grid.linewidth": 0.5, "axes.grid": True,
        "axes.axisbelow": True, "figure.dpi": 150, "savefig.dpi": 300,
        "pdf.fonttype": 42, "ps.fonttype": 42,
        "savefig.bbox": "tight", "savefig.pad_inches": 0.02,
    })


def load_replicates(path=None, fit_data="observed"):
    """results/replicates.parquet; fit_data='observed' = the estimators as a practitioner would run them,
    'population' = noise- and baseline-free fit (approximation error only)."""
    path = path or os.path.join(RESULTS, "replicates.parquet")
    df = pd.read_parquet(path)
    df = df[df.fit_data == fit_data].copy()
    df["err"] = df["tau_hat"] - df["tau_true"]
    df["abs_tau"] = df["tau_true"].abs()
    df["cell"] = df["tag"]
    mn = df["experiment"] == "MAIN"  # MAIN tags are graph|mechanism|design
    df["dsg"] = np.where(mn, df["tag"].str.split("|").str[-1], None)
    return df


def _boot_idx(n, rng):
    return rng.integers(0, n, size=(B_BOOT, n))


def summarize(g, with_ci=True):
    """Metrics of one cell x estimator group (rows = replicates). Returns a Series."""
    n_all = len(g)
    g = g[g["tau_hat"].notna()]  # Hajek is undefined when no unit has a fully treated/control neighbourhood
    e = g["err"].to_numpy(float)
    n = len(e)
    if n < 2:
        return pd.Series(dict(R=n, frac_undefined=1.0))
    scale = float(g["abs_tau"].iloc[0])
    f = lambda x: (x.mean(axis=-1), x.std(axis=-1, ddof=1),
                   np.sqrt((x ** 2).mean(axis=-1)))
    bias, sd, rmse = f(e)
    out = dict(R=n, frac_undefined=1 - n / n_all, bias=bias / scale, sd=sd / scale, rel_rmse=rmse / scale)
    if "ci_lo" in g and g["ci_lo"].notna().all() and len(g) > 0:
        cov = ((g["ci_lo"] <= g["tau_true"]) & (g["tau_true"] <= g["ci_hi"])).to_numpy(float)
        out["coverage"] = cov.mean()
        out["width"] = float((g["ci_hi"] - g["ci_lo"]).mean() / scale)
        out["cov_se"] = np.sqrt(cov.mean() * (1 - cov.mean()) / n)
    out["sign_err"] = float((np.sign(g["tau_hat"]) != np.sign(g["tau_true"])).mean())
    if with_ci and n > 1:
        rng = np.random.default_rng(BOOT_SEED)
        X = e[_boot_idx(n, rng)]
        b, s, r = f(X)
        for k, v in (("bias", b), ("sd", s), ("rel_rmse", r)):
            lo, hi = np.percentile(v / scale, [2.5, 97.5])
            out[k + "_lo"], out[k + "_hi"] = lo, hi
    return pd.Series(out)


def aggregate(df, by):
    """Summary table, one row per `by` group (include 'estimator' in `by`)."""
    rows = []
    for k, g in df.groupby(by, dropna=False):
        k = k if isinstance(k, tuple) else (k,)
        r = summarize(g).to_dict()
        rows.append({**dict(zip(by, k)), **r})
    return pd.DataFrame(rows)


def _plain_log_ticks(fig):
    """Replace the default 10^k tick labels of log axes (superscripts render at ~70% of the tick size) by plain numbers
    (0.1, 1, 10); minor ticks 2 and 5 are labelled when the axis spans less than 2.2 decades."""
    from matplotlib.ticker import FuncFormatter, LogFormatterSciNotation, NullFormatter
    for ax in fig.axes:
        for axis, scale in ((ax.xaxis, ax.get_xscale()), (ax.yaxis, ax.get_yscale())):
            if scale not in ("log", "symlog") or not isinstance(axis.get_major_formatter(), LogFormatterSciNotation):
                continue
            lo, hi = axis.get_view_interval()
            few = scale == "log" and np.log10(hi / lo) < 2.2
            axis.set_major_formatter(FuncFormatter(lambda v, _: f"{v:g}"))
            axis.set_minor_formatter(FuncFormatter(lambda v, _, few=few: f"{v:g}" if few and round(v / 10 ** np.floor(np.log10(v)), 2) in (2.0, 5.0) else ""))


def save(fig, name):
    _plain_log_ticks(fig)
    os.makedirs(OUT, exist_ok=True)
    p = os.path.join(OUT, name + ".pdf")
    fig.savefig(p)
    fig.savefig(os.path.join(OUT, name + ".png"), dpi=200)
    return p
