"""Shared helpers: minimum-investment statistics for the rank-r contenders of a score matrix."""
import numpy as np
from lib import *

def gstar_card(S, t, rule, T):
    a = S[t]
    wins = lambda g: rule_scores((a + np.minimum(g, UB - a))[None], rule)[0] >= T + EPS - 1e-12
    if not wins(UB): return np.nan
    if wins(0.0): return 0.0
    lo, hi = 0.0, UB
    for _ in range(40):
        m = 0.5 * (lo + hi)
        if wins(m): hi = m
        else: lo = m
    return hi

def gstar_ord(S, t, rule):
    a = S[t]
    wins = lambda g: is_first(S, t, rule, np.minimum(g, UB - a))
    if not wins(UB): return np.nan
    if wins(0.0): return 0.0
    lo, hi = 0.0, UB
    for _ in range(40):
        m = 0.5 * (lo + hi)
        if wins(m): hi = m
        else: lo = m
    return hi

def contender_rows(S, rule, ranks, gs=(100,), tl=30.0, want_gstar=True):
    """For each contender rank r in `ranks`: g*, and K*(g), L1*(g) for g in gs.  Returns list of dict."""
    rows = []
    agg = rule_scores(S, rule); order = np.argsort(-agg, kind='stable')
    for r in ranks:
        t = int(order[r - 1]); row = dict(rule=rule, rank=r)
        if rule in CARDINAL:
            T = np.delete(agg, t).max(); riv = np.delete(S, t, axis=0)
            row['gap'] = T - agg[t]
            if want_gstar: row['gstar'] = gstar_card(S, t, rule, T)
            for g in gs:
                x = solve_cardinal(S[t], riv, rule, g, T=T); row[f'K_{g}'] = x['K']; row[f'L1_{g}'] = x['L1']
        else:
            row['gap'] = np.delete(agg, t).max() - agg[t]
            gs_ = gstar_ord(S, t, rule)
            if want_gstar: row['gstar'] = gs_
            for g in gs:
                if np.isnan(gs_) or g < gs_ - 1e-9: row[f'K_{g}'] = np.nan; row[f'L1_{g}'] = np.nan; continue
                xk = solve_ordinal(S, t, rule, g, 'K', time_limit=tl); xl = solve_ordinal(S, t, rule, g, 'L1', time_limit=tl)
                row[f'K_{g}'] = xk['K']; row[f'L1_{g}'] = xl['L1']
        rows.append(row)
    return rows

def additive_residual_sd(S):
    """residual SD of the two-way additive (model + task) fit; anchors the synthetic experiment."""
    R = S - S.mean(axis=1, keepdims=True) - S.mean(axis=0, keepdims=True) + S.mean()
    return float(np.sqrt((R ** 2).sum() / ((S.shape[0] - 1) * (S.shape[1] - 1))))
