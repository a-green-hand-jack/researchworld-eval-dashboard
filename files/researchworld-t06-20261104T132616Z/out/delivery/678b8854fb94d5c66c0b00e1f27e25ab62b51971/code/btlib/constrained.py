"""Constrained adversary: additions / relabellings restricted to comparisons that involve ONE target participant.

side 'a_down': the target is the higher-ranked participant a of the claim pair (a, b) and is pushed down (it loses the added comparisons, or
comparisons it won or tied are relabelled as losses); side 'b_up': the target is b and is pushed up. The adversary has no choice of opponent:
the opponent types (participant pair and home flag) are used in proportion to the target's observed comparison frequencies (for relabelling,
in proportion to the observed counts of the cells that may be relabelled), allocated deterministically by largest remainder.
The budget is the smallest k (bisection with exact refits; the gap is monotone in k along this allocation) whose perturbation flips the pair.
"""
from __future__ import annotations

import numpy as np

from . import core


def alloc(k, w, cap=None):
    """Integer allocation of k units proportional to weights w (largest remainder), each entry at most cap (iterated)."""
    w = np.asarray(w, dtype=float).copy()
    out = np.zeros(len(w), dtype=np.int64)
    left = int(k)
    free = w > 0
    for _ in range(50):
        if left <= 0 or not free.any():
            break
        share = np.where(free, w, 0.0)
        share = share / share.sum() * left
        base = np.floor(share).astype(np.int64)
        rem = left - base.sum()
        if rem > 0:
            order = np.argsort(-(share - base), kind="stable")[: int(rem)]
            base[order] += 1
        if cap is not None:
            room = cap - out
            take = np.minimum(base, np.where(free, room, 0))
        else:
            take = base
        out += take
        left -= int(take.sum())
        if cap is not None:
            free = free & (out < cap)
        else:
            break
    return out, left


def _target_cells(c, t):
    inv = (c.ti == t) | (c.tj == t)
    p = np.where(inv)[0]
    win_o = np.where(c.ti[p] == t, 0, 2)
    return p, win_o, 2 - win_o  # types involving t, outcome index where t wins, where t loses


def delta_for(c, t, k, mode, down):
    """Cell-count change (P, 3) of the constrained adversary acting on target t (down: t loses; else t wins)."""
    p, win_o, lose_o = _target_cells(c, t)
    to_o = lose_o if down else win_o
    d = np.zeros((c.P, 3))
    if mode == "add":
        a, _ = alloc(k, c.n[p].sum(1))
        d[p, to_o] += a
        return d, k
    # relabel: cells (p, o != to_o) -> (p, to_o), weights = counts of those cells
    cells = [(pp, o) for pp, to in zip(p, to_o) for o in range(3) if o != to]
    w = np.array([c.n[pp, o] for pp, o in cells])
    a, left = alloc(k, w, cap=w.astype(np.int64))
    for (pp, o), x in zip(cells, a):
        d[pp, o] -= x
        d[pp, to_o[np.searchsorted(p, pp)]] += x
    return d, k - left


def budget(c, a, b, lam, lam_h, x0, mode, side, kmax=None):
    """Smallest k for which the constrained adversary flips theta_a - theta_b <= 0 (NaN if even kmax does not)."""
    t, down = (a, True) if side == "a_down" else (b, False)
    u = core.claim_vec(c, a, b)
    cap = kmax if kmax is not None else (50 * c.N if mode == "add" else c.n[_target_cells(c, t)[0]].sum())

    def flips(k):
        d, used = delta_for(c, t, k, mode, down)
        x = core.fit(c.with_n(c.n + d), lam, lam_h, theta0=x0)
        return u @ x <= 0

    hi = 1
    while hi < cap and not flips(hi):
        hi = min(cap, hi * 2)
    if not flips(hi):
        return np.nan
    lo = hi // 2 if hi > 1 else 0
    while hi - lo > 1:
        mid = (lo + hi) // 2
        if flips(mid):
            hi = mid
        else:
            lo = mid
    return float(hi)
