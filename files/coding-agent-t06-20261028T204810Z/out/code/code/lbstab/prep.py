"""Dataset preparation shared by all experiment scripts."""
from __future__ import annotations

import numpy as np
import pandas as pd

from . import data
from .bt import Cells, cells_from_frame, fit, grad_hess

LAM = 1e-2
MIN_N = 100   # entities with fewer comparisons are removed (LLM datasets only)

NBA_SEASONS = list(range(1980, 2016))
LLM_SETS = ["arena55k", "arena140k", "webdev10k", "mtbench_human", "mtbench_gpt4", "arenaST_human"] + \
           ["arenaST_" + j for j in data.JUDGES]
ALL_SETS = LLM_SETS + [f"nba{s}" for s in NBA_SEASONS]


def filter_entities(df, names, min_n):
    """Iteratively drop entities with < min_n comparisons; re-index."""
    df = df.copy()
    while True:
        cnt = pd.concat([df.a, df.b]).value_counts()
        bad = set(cnt[cnt < min_n].index)
        if not bad:
            break
        df = df[~df.a.isin(bad) & ~df.b.isin(bad)]
    keep = sorted(set(df.a) | set(df.b))
    remap = {o: k for k, o in enumerate(keep)}
    df["a"] = df.a.map(remap)
    df["b"] = df.b.map(remap)
    return df.reset_index(drop=True), [names[o] for o in keep]


def prepare(name, min_n=None):
    df, names, home = data.load(name)
    if min_n is None:
        min_n = 0 if name.startswith("nba") else MIN_N
    if min_n > 0:
        df, names = filter_entities(df, names, min_n)
    return cells_from_frame(df, names, home=home), df


def pair_stats(c: Cells, theta, i, j, lam=LAM, H=None, p=None):
    """Delta, Fisher SE, sandwich (bootstrap-consistent) SE and per-cell drop leverage."""
    if H is None:
        _, H, p = grad_hess(c, theta, lam)
    cv = np.zeros(c.dim)
    cv[i], cv[j] = 1.0, -1.0
    u = np.linalg.solve(H, cv)
    s = u[c.a] - u[c.b]
    if c.home:
        s = s + u[c.m] * c.h
    r = c.y - p
    se_f = float(np.sqrt(cv @ u))
    se_s = float(np.sqrt((c.w * (s * r) ** 2).sum()))
    lev = s * r   # removing one comparison of cell n changes Delta by about -lev[n]
    return float(theta[i] - theta[j]), se_f, se_s, lev
