"""Loading of the processed score matrices and construction of the cap scenarios."""
import os, pathlib, re
import numpy as np, pandas as pd

PROC = pathlib.Path(__file__).resolve().parents[2] / "data" / "processed"
OLLB_CSV = pathlib.Path(os.environ.get("MTI_OLLB_CSV", PROC / "ollb6.csv"))   # override: duplicate-name variants (src/build_dup_variants.py)
OLLB_TASKS = ["IFEval", "BBH", "MATH Lvl 5", "GPQA", "MUSR", "MMLU-PRO"]


def load(name):
    """returns (X (M,n) in 0..100 scale, model names, task names, meta DataFrame)"""
    if name in ("ollb", "ollb_nomerge", "ollb_top500", "ollb_raw"):
        d = pd.read_csv(OLLB_CSV)
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


import functools


CHAT = "💬 chat models (RLHF, DPO, IFT, ...)"
DOMAIN = "🔶 fine-tuned on domain-specific datasets"


CHAT_NAME = re.compile(r"instruct|chat|[-_]it\b|\bit\b|inst\b|-ins\b|dpo|sft|rlhf|orpo", re.I)   # chat-like model names


def empirical_pairs(subset="all"):
    """(fine-tune scores, base scores) arrays over the pairs whose declared `Base Model` is itself in the data and differs from
    the model. subset: all | chat | nochat (Type of the fine-tune != chat) | domain (Type = domain-specific fine-tune) |
    nochatname (Type != chat and the model name has no chat-like token)."""
    d = pd.read_csv(OLLB_CSV); d = d[~d.Flagged]
    idx = d.set_index("fullname")
    p = d[(d["Base Model"].isin(idx.index)) & (d["Base Model"] != d.fullname)]
    if subset == "chat": p = p[p.Type == CHAT]
    elif subset == "nochat": p = p[p.Type != CHAT]
    elif subset == "domain": p = p[p.Type == DOMAIN]
    elif subset == "nochatname": p = p[(p.Type != CHAT) & ~p.fullname.str.contains(CHAT_NAME)]
    elif subset != "all": raise KeyError(subset)
    return p[OLLB_TASKS].values, idx.loc[p["Base Model"], OLLB_TASKS].values, p


@functools.lru_cache(maxsize=None)
def empirical_gain_caps(q, subset="all"):
    """per-task q-quantile (0..100) of (fine-tune - its base model) score differences, OLLB normalised scores"""
    ft, base, p = empirical_pairs(subset)
    return np.percentile(ft - base, q, axis=0), len(p)


@functools.lru_cache(maxsize=None)
def empirical_frac_caps(q, subset="all"):
    """per-task q-quantile of the share of the base model's remaining headroom closed by the fine-tune,
    (ft - base) / (100 - base), over pairs with base < 100 (a gain conditional on the starting score)"""
    ft, base, p = empirical_pairs(subset)
    ok = base < 100
    fr = np.where(ok, (ft - base) / np.where(ok, 100 - base, 1), np.nan)
    return np.array([np.nanpercentile(fr[:, t], q) for t in range(fr.shape[1])]), len(p)


def make_cap(scenario, X, i=None, name="ollb"):
    """Per-task cap vector for target i. scenarios: ceil | front<m> | gain<h> | emp<q>[_nochat|_chat|_domain|_nochatname] | empfrac<q>[_..] | head<f>"""
    M, n = X.shape
    if scenario == "ceil": return np.full(n, 100.0)
    if scenario.startswith("front"):
        m = float(scenario[5:]); fr = np.delete(X, i, axis=0).max(axis=0) if i is not None else X.max(axis=0)
        return np.minimum(fr + m, 100.0)
    if scenario.startswith("gain"):
        h = float(scenario[4:]); return np.minimum(X[i] + h, 100.0)
    if scenario.startswith("empfrac"):      # empfrac95[_nochat|_chat|_domain]: x + share_q * (100 - x)
        q, _, sub = scenario[7:].partition("_"); fq, _ = empirical_frac_caps(float(q), sub or "all")
        return np.minimum(X[i] + np.maximum(fq, 0) * (100 - X[i]), 100.0)
    if scenario.startswith("emp"):          # emp95[_nochat|_chat|_domain]
        q, _, sub = scenario[3:].partition("_"); hq, _ = empirical_gain_caps(float(q), sub or "all")
        return np.minimum(X[i] + np.maximum(hq, 0), 100.0)
    if scenario.startswith("head"):         # head<f>: a fixed fraction f of the remaining headroom
        return X[i] + float(scenario[4:]) * (100 - X[i])
    raise KeyError(scenario)
