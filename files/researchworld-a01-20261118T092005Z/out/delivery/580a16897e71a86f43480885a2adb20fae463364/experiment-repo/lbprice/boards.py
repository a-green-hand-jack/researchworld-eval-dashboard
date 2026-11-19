"""Load the frozen boards from data_proc/ as dicts: S (points), names, ceil, groups (bundles), meta."""
import os, numpy as np, pandas as pd

DP = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data_proc")
BEN6 = ["IFEval", "BBH", "MATH Lvl 5", "GPQA", "MUSR", "MMLU-PRO"]


def bench_of(task):
    for key, b in (("bbh", "BBH"), ("gpqa", "GPQA"), ("math", "MATH Lvl 5"), ("musr", "MUSR"), ("ifeval", "IFEval"), ("mmlu_pro", "MMLU-PRO")):
        if task.startswith("leaderboard_" + key): return b
    raise KeyError(task)


def load_helm():
    df = pd.read_csv(os.path.join(DP, "helm_mmlu_em.csv"), index_col=0)
    n = pd.read_csv(os.path.join(DP, "helm_mmlu_neval.csv"), index_col=0)["n_eval"].reindex(df.columns).values
    return dict(S=df.values * 100.0, names=list(df.index), tasks=list(df.columns), ceil=100.0, n_eval=n, official=df.values.mean(axis=1) * 100.0)


def load_ollb(name, slice_="main"):
    """name: m6 (normalised benchmark board from `contents`, all models), m6raw (raw benchmark means of the 39 sub-tasks),
    m39 (raw sub-task board).  m6raw and m39 use the models whose results file reproduces the contents row."""
    meta = pd.read_csv(os.path.join(DP, "ollb_m6_contents.csv"))
    if name == "m6":
        d = meta
        if slice_ == "main": d = d[d.main_slice]
        d = d.reset_index(drop=True)
        return dict(S=d[BEN6].values, names=list(d.fullname), ceil=100.0, tasks=BEN6, meta=d, official=d[BEN6].values.mean(axis=1))
    sub = pd.read_csv(os.path.join(DP, "ollb_sub_scores.csv"))
    d = sub.merge(meta[["eval_name", "fullname", "main_slice", "Type", "#Params (B)", "Base Model", "Submission Date", "Merged", "Flagged", "Available on the hub"]], on="eval_name")
    if slice_ == "main": d = d[d.main_slice]
    d = d.reset_index(drop=True)
    tasks = [c for c in sub.columns if c != "eval_name"]
    X = d[tasks].values
    grp = np.array([BEN6.index(bench_of(t)) for t in tasks])
    nb = np.bincount(grp, minlength=6)
    w_h = 1.0 / (6 * nb[grp])                      # hierarchical weights: board mean = mean of the six benchmark means
    if name == "m39":
        return dict(S=X, names=list(d.fullname), ceil=100.0, tasks=tasks, groups=grp, meta=d, w_h=w_h, official=X @ w_h)
    if name == "m6raw":
        S6 = np.stack([X[:, grp == b].mean(axis=1) for b in range(6)], axis=1)
        return dict(S=S6, names=list(d.fullname), ceil=100.0, tasks=BEN6, meta=d, official=S6.mean(axis=1))
    raise ValueError(name)


def ollb_family(meta):
    """Family of each model in an OLLB board table: follow the `Base Model` column through the table until it stops changing
    (or leaves the table), then take the organisation prefix of that root. Returns (root, family) arrays aligned with meta rows."""
    base = dict(zip(meta.fullname, meta["Base Model"].fillna(meta.fullname)))
    def root(n):
        seen = set()
        while n in base and base[n] != n and n not in seen:
            seen.add(n); n = base[n]
        return n if n in base or isinstance(n, str) else str(n)
    r = [root(n) for n in meta.fullname]
    fam = [(str(x).split("/")[0] if "/" in str(x) else str(n).split("/")[0]).lower() for x, n in zip(r, meta.fullname)]  # unresolvable roots ("removed", lists): own organisation
    return np.array(r, dtype=object), np.array(fam, dtype=object)
