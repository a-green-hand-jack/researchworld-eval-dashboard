"""Greedy-with-refit search for the smallest data perturbation that reverses the
order of two entities in a Bradley-Terry leaderboard.

Three perturbation types (all measured in number of individual comparisons):
  drop   : delete k existing comparisons
  flip   : change the recorded outcome of k existing comparisons
  inject : add k new comparisons with adversarially chosen pair and outcome

For a target pair (i above j) let Delta = theta_i - theta_j and u = H^{-1}(e_i - e_j).
The first-order (influence-function / one-step Newton) change of Delta is
  drop one comparison n      : -(u.x_n)(y_n - p_n)
  flip  n from y_n to y'     :  (u.x_n)(y' - y_n)
  inject (x, y)              :  (u.x)(y - p_x)
with x_n = e_a - e_b (+ h e_eta).  Comparisons in the same cell are exchangeable, so
we work with cell counts.  At each round the actions are sorted by first-order
effect, the linear prediction q of the number of units still needed is computed,
ceil(q/2) units (1 when q is small) are applied, the model is refit, and the loop
repeats until Delta < 0.  Every reported budget is therefore *verified by an exact
refit* and is an upper bound on the true minimum; under the linear approximation
greedy selection is optimal.
"""
from __future__ import annotations

import numpy as np
from .bt import Cells, fit, grad_hess, sigmoid, _lin

INF = np.inf


def extend_for_injection(c: Cells) -> Cells:
    """Return a copy of c whose grid contains every possible key (pair, home)."""
    m = c.m
    if c.home:
        A, B = np.meshgrid(np.arange(m), np.arange(m), indexing="ij")
        msk = A != B
        keys = np.stack([A[msk], B[msk], np.ones(msk.sum())], 1)
    else:
        A, B = np.triu_indices(m, 1)
        keys = np.stack([A, B, np.zeros(len(A))], 1)
    orig = np.unique(np.stack([c.a, c.b, c.h], 1), axis=0)
    keys = np.unique(np.concatenate([keys, orig]), axis=0)
    ys = np.array([0.0, 0.5, 1.0])
    a = np.repeat(keys[:, 0], 3).astype(int)
    b = np.repeat(keys[:, 1], 3).astype(int)
    h = np.repeat(keys[:, 2], 3).astype(float)
    y = np.tile(ys, len(keys))
    idx = {(int(aa), int(bb), float(hh), float(yy)): k for k, (aa, bb, hh, yy) in enumerate(zip(a, b, h, y))}
    w = np.zeros(len(a))
    for aa, bb, hh, yy, ww in zip(c.a, c.b, c.h, c.y, c.w):
        w[idx[(int(aa), int(bb), float(hh), float(yy))]] += ww
    return Cells(a, b, h, y, w, m, c.names, c.home)


def _first_order(c: Cells, theta, i, j, lam, kind, allow_tie):
    """Return (effect per unit, capacity, move) arrays for all candidate actions.
    move[k] = (src_cell, dst_cell); src=-1 means injection, dst=-1 means deletion."""
    _, H, p = grad_hess(c, theta, lam)
    cvec = np.zeros(c.dim)
    cvec[i], cvec[j] = 1.0, -1.0
    u = np.linalg.solve(H, cvec)
    s = u[c.a] - u[c.b]
    if c.home:
        s = s + u[c.m] * c.h
    ncell = len(c.w)
    if kind == "drop":
        eff = -s * (c.y - p)
        cap = c.w.copy()
        src = np.arange(ncell)
        dst = -np.ones(ncell, int)
    elif kind == "flip":
        # cells are laid out in triples (y = 0, .5, 1) per key
        base = (np.arange(ncell) // 3) * 3
        effs, caps, srcs, dsts = [], [], [], []
        for t, yt in enumerate((0.0, 0.5, 1.0)):
            if yt == 0.5 and not allow_tie:
                continue
            e = s * (yt - c.y)
            ok = c.y != yt
            effs.append(e[ok]); caps.append(c.w[ok]); srcs.append(np.arange(ncell)[ok]); dsts.append(base[ok] + t)
        eff, cap, src, dst = map(np.concatenate, (effs, caps, srcs, dsts))
    elif kind == "inject":
        ok = (c.y != 0.5)
        eff = (s * (c.y - p))[ok]
        cap = np.full(ok.sum(), INF)
        dst = np.arange(ncell)[ok]
        src = -np.ones(ok.sum(), int)
    else:
        raise ValueError(kind)
    return eff, cap, src, dst


def _apply(w, src, dst, units):
    for s_, d_, k in zip(src, dst, units):
        if k <= 0:
            continue
        if s_ >= 0:
            w[s_] -= k
        if d_ >= 0:
            w[d_] += k


def min_budget(c: Cells, i, j, kind="drop", lam=1e-2, theta0=None, max_budget=None,
               prune=True, prune_max=60, max_rounds=400, allow_tie=None,
               lookahead_q=3, lookahead_L=25):
    """Smallest (found) number of comparisons whose perturbation makes theta_j > theta_i.
    Returns dict(k, rounds, theta, moves) ; k = inf if not reached within max_budget."""
    if allow_tie is None:
        allow_tie = bool((c.w[c.y == 0.5]).sum() > 0)
    if kind == "inject" and theta0 is not None and len(theta0) != c.dim:
        theta0 = None
    w0 = c.w.copy()
    cur = c.copy()
    theta = fit(cur, lam, theta0)
    if theta[i] - theta[j] < 0:
        return dict(k=0, rounds=0, theta=theta, moves=[])
    if max_budget is None:
        max_budget = c.n
    k = 0
    log = []  # list of (src, dst, units)
    rounds = 0
    while True:
        rounds += 1
        D = theta[i] - theta[j]
        if D < 0:
            break
        if rounds > max_rounds or k >= max_budget:
            return dict(k=INF, rounds=rounds, theta=theta, moves=log)
        eff, cap, src, dst = _first_order(cur, theta, i, j, lam, kind, allow_tie)
        neg = (eff < 0) & (cap > 0)
        if not neg.any():
            return dict(k=INF, rounds=rounds, theta=theta, moves=log)
        order = np.where(neg)[0][np.argsort(eff[neg], kind="stable")]
        red = -eff[order]
        cp = cap[order]
        # linear prediction of units needed
        cumred = np.cumsum(red * np.minimum(cp, 1e18))
        pos = np.searchsorted(cumred, D)
        if pos >= len(order):
            q = np.minimum(cp, 1e18).sum()
            q = min(q, max_budget - k)
        else:
            prev_red = cumred[pos - 1] if pos > 0 else 0.0
            prev_units = np.minimum(cp[:pos], 1e18).sum()
            q = prev_units + np.ceil((D - prev_red) / red[pos])
        q = max(1, int(min(q, 1e12)))
        if q <= lookahead_q:
            # near the end: exact one-step lookahead over the top candidates
            best, best_D, best_th = None, np.inf, None
            for t in order[:lookahead_L]:
                w_try = cur.w.copy()
                _apply(w_try, [src[t]], [dst[t]], [1])
                th = fit(cur.copy(w_try), lam, theta)
                if th[i] - th[j] < best_D:
                    best, best_D, best_th = t, th[i] - th[j], th
            _apply(cur.w, [src[best]], [dst[best]], [1])
            log.append((int(src[best]), int(dst[best]), 1.0))
            k += 1
            theta = best_th
            continue
        step = q if q <= 2 else int(np.ceil(q / 2))
        step = int(min(step, max(1, max_budget - k)))
        # allocate `step` units greedily
        units = np.zeros(len(order))
        rem = step
        for t in range(len(order)):
            take = min(rem, cp[t])
            units[t] = take
            rem -= take
            if rem <= 0:
                break
        taken = units > 0
        _apply(cur.w, src[order][taken], dst[order][taken], units[taken])
        log.extend(zip(src[order][taken].tolist(), dst[order][taken].tolist(), units[taken].tolist()))
        k += int(units.sum())
        theta = fit(cur, lam, theta)
    # pruning: try to undo single units (least useful first) while staying reversed
    if prune and k <= prune_max:
        agg = {}
        for s_, d_, u_ in log:
            agg[(s_, d_)] = agg.get((s_, d_), 0) + u_
        changed = True
        while changed:
            changed = False
            eff, cap, src, dst = _first_order(cur, theta, i, j, lam, kind, allow_tie)
            # rank moves by their current first-order usefulness (smallest benefit first)
            eff_map = {(int(s_), int(d_)): e for e, s_, d_ in zip(eff, src, dst)}
            cand = sorted(agg.keys(), key=lambda key: eff_map.get(key, 0.0), reverse=True)
            for key in cand:
                if agg[key] <= 0:
                    continue
                s_, d_ = key
                w_try = cur.w.copy()
                if s_ >= 0:
                    w_try[s_] += 1
                if d_ >= 0:
                    w_try[d_] -= 1
                th = fit(cur.copy(w_try), lam, theta)
                if th[i] - th[j] < 0:
                    cur.w[:] = w_try
                    theta = th
                    agg[key] -= 1
                    k -= 1
                    changed = True
                    break
        log = [(s_, d_, u_) for (s_, d_), u_ in agg.items() if u_ > 0]
    return dict(k=k, rounds=rounds, theta=theta, moves=log)


def exhaustive_drop_min(c: Cells, i, j, kmax=3, lam=1e-2):
    """Exact minimum number of dropped comparisons (<= kmax) by enumerating all
    multisets of cells; returns kmax+1 if none found.  Only for tiny instances."""
    from itertools import combinations_with_replacement
    theta = fit(c, lam)
    if theta[i] - theta[j] < 0:
        return 0
    cells = np.where(c.w > 0)[0]
    for k in range(1, kmax + 1):
        for combo in combinations_with_replacement(cells, k):
            w = c.w.copy()
            ok = True
            for cc in combo:
                w[cc] -= 1
                if w[cc] < 0:
                    ok = False
                    break
            if not ok:
                continue
            th = fit(c.copy(w), lam, theta)
            if th[i] - th[j] < 0:
                return k
    return kmax + 1


def exhaustive_flip_min(c: Cells, i, j, kmax=2, lam=1e-2, allow_tie=True):
    from itertools import combinations_with_replacement
    theta = fit(c, lam)
    if theta[i] - theta[j] < 0:
        return 0
    ncell = len(c.w)
    moves = []
    for n in np.where(c.w > 0)[0]:
        base = (n // 3) * 3
        for t, yt in enumerate((0.0, 0.5, 1.0)):
            if c.y[n] == yt or (yt == 0.5 and not allow_tie):
                continue
            moves.append((n, base + t))
    for k in range(1, kmax + 1):
        for combo in combinations_with_replacement(range(len(moves)), k):
            w = c.w.copy()
            ok = True
            for mv in combo:
                s_, d_ = moves[mv]
                w[s_] -= 1
                w[d_] += 1
                if w[s_] < 0:
                    ok = False
                    break
            if not ok:
                continue
            th = fit(c.copy(w), lam, theta)
            if th[i] - th[j] < 0:
                return k
    return kmax + 1
