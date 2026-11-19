"""Loading of the processed score matrices and construction of the cap scenarios."""
import functools, pathlib
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


def gain_pairs(subset="all"):
    """The (fine-tune, base) pairs behind the empirical caps: unflagged OLLB models whose `Base Model` entry is itself an unflagged leaderboard model (and not the model itself).
    Returns (pairs DataFrame, gain matrix (pairs, 6 tasks) = fine-tune minus base, normalised scores). subset: 'all' | 'restricted' = pairs whose fine-tune is neither typed
    'chat models' nor a merge nor named like an instruction/chat tune (name regex instruct|chat|-it|dpo|rlhf|orpo|simpo) -- classification only from the Type/Merged columns and the model name, no hand labels."""
    d = pd.read_csv(PROC / "ollb6.csv"); d = d[~d.Flagged]; idx = d.set_index("fullname")
    p = d[(d["Base Model"].isin(idx.index)) & (d["Base Model"] != d.fullname)].copy()
    if subset == "restricted":
        chat_name = p.fullname.str.contains(r"instruct|chat|[-_]it\b|dpo|rlhf|orpo|simpo", case=False, regex=True)
        p = p[~(p.Type.str.contains("chat") | p.Type.str.contains("merge") | p.Merged | chat_name)]
    g = p[OLLB_TASKS].values - idx.loc[p["Base Model"], OLLB_TASKS].values
    return p, g


@functools.lru_cache(maxsize=None)
def empirical_gain_caps(q, pooled=False, subset="all"):
    """per-task q-quantile (0..100) of (fine-tune - its base model) score differences, OLLB normalised scores;
    pooled=True: one scalar quantile over all six tasks' differences (used to transfer the cap to other leaderboards, e.g. HELM); subset: see gain_pairs"""
    p, g = gain_pairs(subset)
    return (np.percentile(g, q) if pooled else np.percentile(g, q, axis=0)), len(p)


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
        # empPpool: one scalar P-quantile pooled over the six OLLB tasks. empP: per-task quantiles on OLLB; on other leaderboards
        # (HELM, 57 MMLU subjects) the MMLU-PRO quantile is transferred to every subject (closest analogue: knowledge MCQ).
        # empPr: per-task quantiles from the restricted pair subset (no chat/instruct tunes, no merges; see gain_pairs)
        subset = "restricted" if scenario.endswith("r") else "all"
        pooled = scenario.endswith("pool"); q = float(scenario[3:].replace("pool", "").rstrip("r"))
        hq, _ = empirical_gain_caps(q, pooled=pooled, subset=subset)
        if not pooled and n != len(OLLB_TASKS): hq = np.full(n, hq[OLLB_TASKS.index("MMLU-PRO")])
        return np.minimum(X[i] + np.maximum(hq, 0), 100.0)
    raise KeyError(scenario)


def base_clusters(names):
    """cluster key for OLLB models (aligned with `names`): the `Base Model` entry; no usable entry (empty, or a placeholder such as 'Removed', '(Merge)', '[...]' that is not
    a leaderboard model) -> the model's own name, i.e. its own cluster"""
    d = pd.read_csv(PROC / "ollb6.csv").drop_duplicates("fullname").set_index("fullname"); own = set(d.index)
    bm = d["Base Model"].reindex(list(names))
    ph = bm.isna() | (~bm.isin(own) & bm.astype(str).str.contains(r"Removed|\(Merge\)|^\[", regex=True))
    return np.where(ph.values, np.array(list(names), dtype=object), bm.astype(object).values)
