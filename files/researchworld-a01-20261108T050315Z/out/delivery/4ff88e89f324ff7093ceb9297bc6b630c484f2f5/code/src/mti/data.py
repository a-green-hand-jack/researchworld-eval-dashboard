"""Loading of the processed score matrices and construction of the cap scenarios."""
import pathlib, functools
import numpy as np, pandas as pd
from scipy.stats import rankdata

PROC = pathlib.Path(__file__).resolve().parents[2] / "data" / "processed"
OLLB_TASKS = ["IFEval", "BBH", "MATH Lvl 5", "GPQA", "MUSR", "MMLU-PRO"]


def load(name):
    """returns (X (M,n) in 0..100 scale, model names, task names, meta DataFrame)"""
    if name in ("ollb_z", "ollb_pct"):
        X, names, tasks, d = load("ollb")
        if name == "ollb_z": X = (X - X.mean(axis=0)) / X.std(axis=0)           # per-task z-score over the unflagged OLLB population
        else: X = np.column_stack([rankdata(X[:, t], method="average") for t in range(X.shape[1])]) * 100.0 / len(X)   # rank percentile (0,100]
        return X, names, tasks, d
    if name in ("ollb", "ollb_nomerge", "ollb_top500", "ollb_raw"):
        d = pd.read_csv(PROC / "ollb6.csv")
        d = d[~d.Flagged]
        if name == "ollb_nomerge": d = d[~d.Merged]
        cols = OLLB_TASKS if name != "ollb_raw" else [t + " Raw" for t in OLLB_TASKS]
        d = d.reset_index(drop=True)
        if name == "ollb_top500":
            d = d.iloc[(-d[OLLB_TASKS].mean(axis=1)).argsort(kind="stable")[:500]].reset_index(drop=True)
        X = d[cols].values.astype(float)
        if name == "ollb_raw": X = X * 100
        return X, d.fullname.values, OLLB_TASKS, d
    if name == "helm":
        h = pd.read_csv(PROC / "helm_mmlu57.csv", index_col=0)
        return h.values.astype(float), h.index.values, list(h.columns), h
    raise KeyError(name)


@functools.lru_cache(maxsize=None)
def _empirical_gain_caps(q):
    """per-task q-quantile (0..100) of (fine-tune - its base model) score differences, OLLB normalised scores"""
    d = pd.read_csv(PROC / "ollb6.csv"); d = d[~d.Flagged]
    idx = d.set_index("fullname")
    p = d[(d["Base Model"].isin(idx.index)) & (d["Base Model"] != d.fullname)]
    g = p[OLLB_TASKS].values - idx.loc[p["Base Model"], OLLB_TASKS].values
    return np.percentile(g, q, axis=0), len(p)


def empirical_gain_caps(q): return _empirical_gain_caps(float(q))


def _units(name):
    """(scale, top): size of one raw score point per task in the dataset's units, and the highest attainable value (raw 100)"""
    if name == "ollb_z":
        X = load("ollb")[0]; mu, sd = X.mean(axis=0), X.std(axis=0); return sd, (100.0 - mu) / sd
    return 1.0, 100.0


def make_cap(scenario, X, i=None, name="ollb"):
    """Per-task cap vector for target i, in the units of dataset `name`.
    ceil | front<m> (best rival + m) | gain<h> (h raw score points; converted to z units for ollb_z) |
    sgain<h> (h standardised units: SD for ollb_z, percentile points for ollb_pct) | emp<q>.
    Raw-point scenarios (gain, emp) are undefined for ollb_pct."""
    M, n = X.shape
    scale, top = _units(name)
    top = np.broadcast_to(top, (n,)).astype(float)
    if scenario == "ceil": return top.copy()
    if scenario.startswith("front"):
        m = float(scenario[5:]); fr = np.delete(X, i, axis=0).max(axis=0) if i is not None else X.max(axis=0)
        return np.minimum(fr + m, top)
    if name == "ollb_pct" and (scenario.startswith("gain") or scenario.startswith("emp")):
        raise KeyError(f"{scenario} undefined for ollb_pct")
    if scenario.startswith("sgain"): return np.minimum(X[i] + float(scenario[5:]), top)
    if scenario.startswith("gain"): return np.minimum(X[i] + float(scenario[4:]) / scale, top)
    if scenario.startswith("empm"):     # HELM proxy: one pooled gain, the OLLB MMLU-PRO q-quantile of (fine-tune - base), same on every subject
        hq = empirical_gain_caps(float(scenario[4:]))[0][OLLB_TASKS.index("MMLU-PRO")]
        return np.minimum(X[i] + max(hq, 0.0), top)
    if scenario.startswith("emp"):
        hq, _ = empirical_gain_caps(float(scenario[3:])); return np.minimum(X[i] + np.maximum(hq, 0) / scale, top)
    raise KeyError(scenario)


SCALE = {"ollb": "raw", "ollb_nomerge": "raw", "ollb_top500": "raw", "ollb_raw": "rawscore", "ollb_z": "z", "ollb_pct": "pct", "helm": "raw"}


def sample_targets(X, seed=0, nsample=150):
    """rank-stratified target sample used wherever ordinal MILPs are too slow: ranks 2..21 under the mean (all of them) plus nsample
    log-uniform-in-rank targets from the rest. Returns (targets, mean_rank)."""
    mean_rank = rankdata(-X.mean(axis=1), method="min"); order = np.argsort(mean_rank, kind="stable")
    head = order[1:21]; tail = order[21:]
    if len(tail) > nsample:
        pos = np.unique(np.round(np.exp(np.linspace(np.log(1), np.log(len(tail)), nsample))).astype(int) - 1); tail = tail[pos]
    return np.concatenate([head, tail]), mean_rank


RANK_BINS = [(1, 1), (2, 2), (3, 5), (6, 10), (11, 30), (31, 100), (101, 10**6)]


def rank_bin(r):
    for lo, hi in RANK_BINS:
        if lo <= r <= hi: return f"{lo}" if lo == hi else (f"{lo}-{hi}" if hi < 10**6 else f">{lo - 1}")
