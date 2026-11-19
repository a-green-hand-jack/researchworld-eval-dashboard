"""Shared helpers for the experiment scripts."""
import numpy as np
from scipy.stats import rankdata
from . import agg
from .agg import INF

G_GRID = [2.0, 5.0, 10.0, 20.0, 50.0]   # per-task gain bounds (score points)


def caps(x, scenario):
    """scenario: 'ceil' (u=100) or float g (u=min(100, x+g))."""
    if scenario == "ceil":
        return np.full(len(x), 100.0)
    return np.minimum(100.0, x + float(scenario))


def mean_rank_order(S):
    """indices sorted by mean score (descending); stable."""
    return np.argsort(-S.mean(1), kind="stable")


def rule_rank_order(rule, S):
    """Model order (best first) under `rule`; ties broken by mean score."""
    n, m = S.shape
    if rule in agg.SCORE_RULES:
        with np.errstate(divide="ignore", invalid="ignore"):
            v = agg.f_values(rule, S)
        key = np.lexsort((-S.mean(1), -v))
        return key, v
    if rule == "borda":
        pts = np.zeros(n)
        for j in range(m):
            pts += rankdata(S[:, j], method="average") - 1.0
        key = np.lexsort((-S.mean(1), -pts))
        return key, pts
    if rule == "plural":
        top = S.argmax(0)
        cnt = np.bincount(top, minlength=n).astype(float)
        key = np.lexsort((-S.mean(1), -cnt))
        return key, cnt
    raise ValueError(rule)


def one_cost(rule, S, t, scenario, fv=None):
    x = S[t]
    u = caps(x, scenario)
    try:
        r = agg.target_costs(rule, S, int(t), u, fv=fv)
    except ValueError:
        return {"l1": np.nan, "br": np.nan}
    return r


def contender_costs(S, rules, scenario, n_contenders=10, ):
    """Costs for mean-rank 2..(n_contenders+1) targets under every rule. Returns list of dict rows."""
    order = mean_rank_order(S)
    fvs = {}
    for r in rules:
        if r in agg.SCORE_RULES:
            with np.errstate(divide="ignore", invalid="ignore"):
                fvs[r] = agg.f_values(r, S)
    rows = []
    for pos in range(1, n_contenders + 1):
        t = int(order[pos])
        for rule in rules:
            c = one_cost(rule, S, t, scenario, fvs.get(rule))
            rows.append({"rule": rule, "mean_rank": pos + 1, "target": t, "l1": c["l1"], "br": c["br"],
                         "l1_lb": c.get("l1_lb", c["l1"]), "br_lb": c.get("br_lb", c["br"])})
    return rows
