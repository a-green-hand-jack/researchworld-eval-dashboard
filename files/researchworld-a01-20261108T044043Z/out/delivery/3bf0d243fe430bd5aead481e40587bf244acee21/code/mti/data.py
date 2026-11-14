"""Loading of the processed score matrices and construction of the cap scenarios."""
import pathlib, functools
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
        # the leaderboard's normalised scores of models with the same raw accuracy differ by float noise (~1e-15, 284 such pairs
        # on MATH/GPQA/MUSR); rounding to 1e-9 restores the exact ties that the rank rules must see as ties
        X = np.round(d[cols].values.astype(float), 9)
        if name == "ollb_raw": X = X * 100
        return X, d.fullname.values, OLLB_TASKS, d
    if name in ("ollb_leaf", "ollb6_leafslice"):
        # the 499 of the top-500 OLLB models with a validated result file (code/build_ollb_leaves.py): 39 leaf tasks, or the six
        # published tasks of the same models in the same order
        lf = pd.read_csv(PROC / "ollb_leaves.csv")
        if name == "ollb_leaf":
            cols = [c for c in lf.columns if c not in ("model", "rank_mean6", "file", "n_files")]
            return np.round(lf[cols].values.astype(float), 9), lf.model.values, cols, lf
        d = pd.read_csv(PROC / "ollb6.csv"); d = d[~d.Flagged].drop_duplicates("fullname").set_index("fullname").loc[lf.model].reset_index()
        return np.round(d[OLLB_TASKS].values.astype(float), 9), d.fullname.values, OLLB_TASKS, d
    if name == "helm":
        h = pd.read_csv(PROC / "helm_mmlu57.csv", index_col=0)
        return h.values.astype(float), h.index.values, list(h.columns), h
    raise KeyError(name)


@functools.lru_cache(maxsize=None)
def _gains():
    d = pd.read_csv(PROC / "ollb6.csv"); d = d[~d.Flagged]
    idx = d.set_index("fullname")
    p = d[(d["Base Model"].isin(idx.index)) & (d["Base Model"] != d.fullname)]
    return p[OLLB_TASKS].values - idx.loc[p["Base Model"], OLLB_TASKS].values


def empirical_gain_caps(q):
    """per-task q-quantile (0..100) of (fine-tune - its base model) score differences, OLLB normalised scores"""
    g = _gains()
    return np.percentile(g, q, axis=0), len(g)


def leaf_parent_index(leaf_names):
    """index in OLLB_TASKS of the published task each leaf belongs to (for the parent-task empirical caps)"""
    pre = [("bbh_", "BBH"), ("gpqa_", "GPQA"), ("math_", "MATH Lvl 5"), ("musr_", "MUSR"), ("mmlu_pro", "MMLU-PRO"), ("ifeval", "IFEval")]
    return np.array([OLLB_TASKS.index(next(t for p, t in pre if l.startswith(p))) for l in leaf_names])


def dt_index(task): return OLLB_TASKS.index(task)


def make_cap(scenario, X, i=None, name="ollb", cols=None):
    """Per-task cap vector for target i. scenarios: ceil | front<m> | gain<h> | emp<q>[T|P].
    cols: original task index of each column of X (for task-resampled matrices, so per-task empirical caps follow their task)."""
    M, n = X.shape
    if scenario == "ceil": return np.full(n, 100.0)
    if scenario.startswith("front"):
        m = float(scenario[5:]); fr = np.delete(X, i, axis=0).max(axis=0) if i is not None else X.max(axis=0)
        return np.minimum(fr + m, 100.0)
    if scenario.startswith("gain"):
        h = float(scenario[4:]); return np.minimum(X[i] + h, 100.0)
    if scenario.startswith("emp"):
        # emp<q>   : OLLB per-task q-quantile of fine-tune-minus-base gains (OLLB only, n=6 tasks)
        # emp<q>T  : transfer cap (HELM): the OLLB MMLU-PRO quantile applied to every task
        # emp<q>P  : pooled cap: quantile of all six tasks' gains pooled, applied to every task
        suf = scenario[-1] if scenario[-1] in "TP" else ""
        q = float(scenario[3:len(scenario) - len(suf)]); hq, _ = empirical_gain_caps(q)
        if suf == "T": h = np.full(n, hq[dt_index("MMLU-PRO")])
        elif suf == "P": h = np.full(n, np.percentile(_gains(), q))
        else:
            assert (cols is not None) or n == len(OLLB_TASKS), "per-task empirical caps exist only for the six OLLB tasks"; h = hq if cols is None else hq[np.asarray(cols)]
        return np.minimum(X[i] + np.maximum(h, 0), 100.0)
    raise KeyError(scenario)
