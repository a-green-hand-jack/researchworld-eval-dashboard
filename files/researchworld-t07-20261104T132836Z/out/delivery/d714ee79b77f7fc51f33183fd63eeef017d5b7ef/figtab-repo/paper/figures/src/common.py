"""Shared loading, labels, colours and matplotlib style for all figures and tables.

Inputs are the committed tidy tables of experiment-repo (`results/`): cells.csv, paired.csv,
predictions_headline.csv, data_audit.csv, aggregate.csv.  The results directory is taken from the
environment variable FIGTAB_RESULTS (default <repository root>/results).
Nothing here is computed from raw experiments: only re-aggregation of the committed point estimates
and bootstrap intervals (each use is stated in the caption of the output that uses it).
"""
import os
import numpy as np
import pandas as pd
import matplotlib as mpl

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))  # repository root (paper/figures/src -> root)
RESULTS = os.environ.get("FIGTAB_RESULTS", os.path.join(ROOT, "results"))
OUT_FIG = os.environ.get("FIGTAB_OUT_FIG", os.path.join(ROOT, "paper", "figures"))
OUT_TAB = os.environ.get("FIGTAB_OUT_TAB", os.path.join(ROOT, "paper", "tables"))

TEXTWIDTH = 5.5  # in; NeurIPS 2026 text width (neurips_2026.sty: textwidth=5.5in)

LABEL = {
    "sources_only": "Sources only", "random": "Random mean", "strat_random": "Stratified", "anchor": "Anchor points",
    "calib": "Calibrated random", "ridge": "Random + ridge", "irt_rand": "IRT (random)", "irt_info": "IRT (D-opt.)",
    "anchor_irt": "Anchor + IRT", "aipw_rand": "AIPW", "anchor_aipw": "Anchor + AIPW", "ppi": "PPI",
    "aipw_knn": "AIPW-kNN", "aipw_ens": "AIPW-Ens", "mass_ens": "MASS-Ens", "mass_ens_k2": "MASS-Ens (k=2)",
    "mass": "MASS (latent)", "mass_k1": "MASS k=1", "mass_k4": "MASS k=4", "aipw_strat": "AIPW + strat.",
    "aipw_pps": "AIPW + PPS", "aipw_k1": "AIPW k=1", "aipw_k4": "AIPW k=4",
    "aipw_ridge_cf": "AIPW + ridge (cross-fit)", "aipw_ridge_repo": "AIPW + ridge (repo variant)", "mass_sel": "MASS (selection only)",
    "mass_ens_nocorr": "MASS-Ens, no correction", "ens_rand_nocorr": "Ensemble, random, no corr.", "best_cv": "Best baseline by source CV",
}
ROLE = {m: "baseline" for m in LABEL}
ROLE.update({m: "proposed" for m in ["mass_ens", "mass_ens_k2"]})
ROLE.update({m: "proposed" for m in ["mass"]})
ROLE.update({m: "ablation" for m in ["mass_sel", "mass_ens_nocorr", "ens_rand_nocorr", "mass_k1", "mass_k4", "aipw_strat", "aipw_pps", "aipw_k1", "aipw_k4"]})

# Okabe-Ito (colour-blind safe); the proposed method keeps one colour in every figure.
OI = dict(black="#000000", orange="#E69F00", sky="#56B4E9", green="#009E73", yellow="#F0E442",
          blue="#0072B2", verm="#D55E00", pink="#CC79A7", grey="#7F7F7F")
COLOR = {"sources_only": OI["grey"], "random": "#000000", "ridge": OI["sky"], "anchor_irt": OI["orange"], "aipw_rand": OI["green"],
         "anchor": OI["yellow"], "calib": OI["pink"], "irt_info": "#8C510A", "irt_rand": "#B2ABD2", "strat_random": "#999933",
         "ppi": "#44AA99", "aipw_knn": "#88CCEE", "aipw_ens": "#117733", "mass_ens": OI["verm"], "mass_ens_k2": "#882255",
         "anchor_aipw": "#DDCC77", "mass": "#AA4499", "best_cv": OI["blue"], "aipw_ridge_cf": "#CC6677", "mass_sel": "#999999", "aipw_strat": "#332288", "aipw_pps": "#661100"}
MARKER = {"mass": "P", "best_cv": "v", "sources_only": "x", "random": "o", "ridge": "s", "anchor_irt": "^", "aipw_rand": "D", "mass_ens": "*"}
LS = {"best_cv": (0, (5, 1, 1, 1)), "sources_only": (0, (3, 2)), "mass_ens": "-"}

METRIC_LABEL = {"mae": "MAE", "rmse": "RMSE", "spearman": "Spearman $\\rho$", "kendall": "Kendall $\\tau_b$",
                "bias": "Bias (pred. $-$ true)", "rmse_over_sd": "RMSE / SD(true)"}
PROTO_LABEL = {"random": "Interpolation (random held-out models)", "extrap": "Extrapolation (strongest 20% held out)"}
HELM = {"commonsense", "gsm", "legalbench", "math", "med_qa", "mmlu"}
BENCH_LABEL = {"arc_challenge": "ARC-Challenge", "bbh": "BBH", "gpqa": "GPQA", "ifeval": "IFEval", "mmlu_pro": "MMLU-Pro",
               "musr": "MuSR", "openllm_math": "MATH L5 (OLL)", "commonsense": "CommonSense (HELM)", "gsm": "GSM8K (HELM)",
               "legalbench": "LegalBench (HELM)", "math": "MATH (HELM)", "med_qa": "MedQA (HELM)", "mmlu": "MMLU (HELM)"}
BENCH_ORDER = ["arc_challenge", "bbh", "gpqa", "ifeval", "mmlu_pro", "musr", "openllm_math",
               "commonsense", "gsm", "legalbench", "math", "med_qa", "mmlu"]


# Benchmarks on which the predictor of MASS-Ens was chosen in a development pilot (story-repo PLAN v1.1): flagged everywhere.
DEV = {"ifeval", "arc_challenge", "gpqa", "gsm"}


def bl(b, tex=False):
    """Display label; development benchmarks carry an asterisk."""
    lab = BENCH_LABEL.get(b, b)
    return lab + (("$^*$" if tex else "*") if b in DEV else "")


def ml(m):
    return LABEL.get(m, m)


def color(m):
    return COLOR.get(m, "#555555")


def style():
    mpl.rcParams.update({
        "font.family": "serif", "font.serif": ["Times New Roman", "Nimbus Roman", "DejaVu Serif"],
        "mathtext.fontset": "stix", "font.size": 8, "axes.labelsize": 8, "axes.titlesize": 8,
        "xtick.labelsize": 7, "ytick.labelsize": 7, "legend.fontsize": 7, "axes.linewidth": 0.6,
        "xtick.major.width": 0.6, "ytick.major.width": 0.6, "xtick.major.size": 2.5, "ytick.major.size": 2.5,
        "lines.linewidth": 1.2, "lines.markersize": 3.5, "axes.spines.top": False, "axes.spines.right": False,
        "axes.grid": True, "grid.color": "#DDDDDD", "grid.linewidth": 0.4, "figure.dpi": 150, "savefig.dpi": 300,
        "pdf.fonttype": 42, "ps.fonttype": 42, "savefig.bbox": "tight", "savefig.pad_inches": 0.02,
    })


def load(name, required=True):
    p = os.path.join(RESULTS, name)
    if not os.path.exists(p):
        if required:
            raise FileNotFoundError(p)
        return None
    # the method called `sources_only` (formerly `null`) must not be parsed as NaN
    return pd.read_csv(p, keep_default_na=False, na_values=[""])


def benches(df):
    have = set(df.bench.unique())
    return [b for b in BENCH_ORDER if b in have] + sorted(have - set(BENCH_ORDER))


def save(fig, name):
    os.makedirs(OUT_FIG, exist_ok=True)
    p = os.path.join(OUT_FIG, name)
    fig.savefig(p)
    print("wrote", p)


def geomean_ci(vals, B=2000, seed=0):
    """Geometric mean of positive per-benchmark ratios with a benchmark-level percentile bootstrap 95% CI."""
    v = np.log(np.asarray(vals, float))
    rng = np.random.default_rng(seed)
    bs = np.array([v[rng.integers(0, len(v), len(v))].mean() for _ in range(B)])
    return np.exp(v.mean()), np.exp(np.percentile(bs, 2.5)), np.exp(np.percentile(bs, 97.5))
