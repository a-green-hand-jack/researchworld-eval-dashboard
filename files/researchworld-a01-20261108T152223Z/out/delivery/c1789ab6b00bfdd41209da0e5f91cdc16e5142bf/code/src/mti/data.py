"""Loading of the processed score matrices and construction of the cap scenarios."""
import pathlib
import numpy as np, pandas as pd

PROC = pathlib.Path(__file__).resolve().parents[2] / "data" / "processed"
OLLB_TASKS = ["IFEval", "BBH", "MATH Lvl 5", "GPQA", "MUSR", "MMLU-PRO"]


def load(name):
    """returns (X (M,n) in 0..100 scale, model names, task names, meta DataFrame)"""
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


def empirical_gain_caps(q):
    """per-task q-quantile (0..100) of (fine-tune - its base model) score differences, OLLB normalised scores"""
    d = pd.read_csv(PROC / "ollb6.csv"); d = d[~d.Flagged]
    idx = d.set_index("fullname")
    p = d[(d["Base Model"].isin(idx.index)) & (d["Base Model"] != d.fullname)]
    g = p[OLLB_TASKS].values - idx.loc[p["Base Model"], OLLB_TASKS].values
    return np.percentile(g, q, axis=0), len(p)


def make_cap(scenario, X, i=None, name="ollb"):
    """Per-task cap vector for target i. scenarios: ceil | front<m> | gain<h> | emp<q>"""
    M, n = X.shape
    if scenario == "ceil": return np.full(n, 100.0)
    if scenario.startswith("front"):
        m = float(scenario[5:]); fr = np.delete(X, i, axis=0).max(axis=0) if i is not None else X.max(axis=0)
        return np.minimum(fr + m, 100.0)
    if scenario.startswith("gain"):
        h = float(scenario[4:]); return np.minimum(X[i] + h, 100.0)
    if scenario.startswith("emp"):
        q = float(scenario[3:]); hq, _ = empirical_gain_caps(q); return np.minimum(X[i] + np.maximum(hq, 0), 100.0)
    raise KeyError(scenario)
