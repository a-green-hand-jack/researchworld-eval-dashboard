"""Bradley-Terry fitting on aggregated comparison counts, influence and perturbation search.

Data model. A *type* p is an ordered participant pair (i, j) with an optional home flag h in {-1, 0, 1}
(h = 1: i is at home, -1: j is at home, 0: neutral / not modelled). Each type has integer counts for the three
outcomes o = 0 (i wins), 1 (tie), 2 (j wins). Soft labels s_o = (1, 0.5, 0): a tie is half a win for each side.
A comparison is therefore identified by its (type, outcome) cell; every perturbation is a change of cell counts.

Model. P(i beats j) = sigmoid(theta_i - theta_j + beta * h); loss = sum_cells n_po * CE(sigma(d_p), s_o)
+ lam/2 ||theta||^2 (+ tiny ridge on beta). beta is only present when `home=True`.
"""
from __future__ import annotations

import numpy as np
import scipy.sparse as sp

S_O = np.array([1.0, 0.5, 0.0])


def sigmoid(x):
    return 0.5 * (1.0 + np.tanh(0.5 * x))


class Counts:
    """Aggregated comparisons. n has shape (P, 3), integer valued."""

    def __init__(self, names, ti, tj, th, n, home=False):
        self.names = list(names)
        self.K = len(self.names)
        self.ti = np.asarray(ti, dtype=np.int64)
        self.tj = np.asarray(tj, dtype=np.int64)
        self.th = np.asarray(th, dtype=np.float64)
        self.n = np.asarray(n, dtype=np.float64).reshape(-1, 3).copy()
        self.home = home
        self.P = len(self.ti)
        self.D = self.K + (1 if home else 0)
        rows = np.repeat(np.arange(self.P), 2)
        cols = np.stack([self.ti, self.tj], 1).ravel()
        vals = np.tile([1.0, -1.0], self.P)
        V = sp.csr_matrix((vals, (rows, cols)), shape=(self.P, self.D))
        if home:
            V = V + sp.csr_matrix((self.th, (np.arange(self.P), np.full(self.P, self.K))), shape=(self.P, self.D))
        self.V = V.tocsr()

    @staticmethod
    def from_rows(names, i, j, y, h=None, home=False, drop_ties=False):
        """Rows: participants i, j (indices) and outcome y in {0: i wins, 1: tie, 2: j wins}; h = home flag of i."""
        i = np.asarray(i); j = np.asarray(j); y = np.asarray(y).copy()
        h = np.zeros(len(i)) if h is None else np.asarray(h, dtype=float)
        if not home:
            h = np.zeros(len(i))
        swap = i > j
        i2 = np.where(swap, j, i); j2 = np.where(swap, i, j)
        h2 = np.where(swap, -h, h)
        y2 = np.where(swap & (y != 1), 2 - y, y)
        if drop_ties:
            keep = y2 != 1
            i2, j2, h2, y2 = i2[keep], j2[keep], h2[keep], y2[keep]
        key = (i2.astype(np.int64) * len(names) + j2) * 3 + (h2 + 1).astype(np.int64)
        uk, inv = np.unique(key, return_inverse=True)
        n = np.zeros((len(uk), 3))
        np.add.at(n, (inv, y2.astype(int)), 1.0)
        hh = (uk % 3).astype(float) - 1
        pp = uk // 3
        return Counts(names, pp // len(names), pp % len(names), hh, n, home=home)

    def with_n(self, n):
        c = Counts.__new__(Counts)
        c.__dict__.update(self.__dict__)
        c.n = np.asarray(n, dtype=np.float64).reshape(-1, 3)
        return c

    @property
    def N(self):
        return self.n.sum()

    def participant_counts(self):
        tot = self.n.sum(1)
        return np.bincount(self.ti, tot, self.K) + np.bincount(self.tj, tot, self.K)

    def pair_totals(self):
        """dict {(i, j) with i<j: total comparisons} over home flags."""
        out = {}
        for a, b, t in zip(self.ti, self.tj, self.n.sum(1)):
            out[(a, b)] = out.get((a, b), 0) + t
        return out


def fit(c: Counts, lam=1.0, lam_h=1.0, theta0=None, tol=1e-9, maxit=50, return_hess=False):
    """Newton fit with backtracking. Returns params (theta [, beta]) of length D."""
    Np = c.n.sum(1)
    Wp = c.n @ S_O
    V, VT = c.V, c.V.T.tocsr()
    pen = np.full(c.D, lam)
    if c.home:
        pen[c.K] = lam_h
    x = np.zeros(c.D) if theta0 is None else theta0.copy()

    def obj(x):
        d = V @ x
        # CE(sigma(d), s): log(1+e^d) - s d summed with counts
        return float(np.sum(Np * np.logaddexp(0, d) - Wp * d) + 0.5 * np.sum(pen * x * x))

    f = obj(x)
    for _ in range(maxit):
        d = V @ x
        s = sigmoid(d)
        g = VT @ (Np * s - Wp) + pen * x
        if np.max(np.abs(g)) < tol * max(1.0, c.N ** 0.5):
            break
        w = Np * s * (1 - s)
        H = (VT @ sp.diags(w) @ V).toarray() + np.diag(pen)
        step = np.linalg.solve(H, g)
        t = 1.0
        while True:
            xn = x - t * step
            fn = obj(xn)
            if fn <= f + 1e-12 * abs(f) or t < 1e-6:
                break
            t *= 0.5
        x, f = xn, fn
    if return_hess:
        d = V @ x
        s = sigmoid(d)
        w = Np * s * (1 - s)
        H = (VT @ sp.diags(w) @ V).toarray() + np.diag(pen)
        return x, H
    return x


def scores(x, c: Counts):
    return x[: c.K]


def ranks_of(theta):
    """Rank 0 = best. Ties in theta broken by index (measure zero)."""
    order = np.argsort(-theta, kind="stable")
    r = np.empty(len(theta), dtype=int)
    r[order] = np.arange(len(theta))
    return r


# ----------------------------------------------------------------------------------------------
# influence and the adversarial search


def gains(c: Counts, x, H, u, mode="remove"):
    """Linearised change of the claim functional u.x that *decreases* it, per unit of cell (p, o).

    remove one comparison of cell (p,o): gain = (s_o - sigma_p) * r_p ; add one: gain = (sigma_p - s_o) * r_p
    with r = V H^{-1} u. Returns array (P, 3); cells that cannot be removed (n = 0) get -inf in 'remove' mode.
    """
    r = c.V @ np.linalg.solve(H, u)
    sg = sigmoid(c.V @ x)
    G = (S_O[None, :] - sg[:, None]) * r[:, None]
    if mode == "add":
        return -G
    G = G.copy()
    G[c.n <= 0] = -np.inf
    return G


def claim_vec(c: Counts, a, b):
    """u such that u.x = theta_a - theta_b."""
    u = np.zeros(c.D)
    u[a] = 1.0
    u[b] = -1.0
    return u


def adversarial_flip(c: Counts, a, b, lam=1.0, mode="remove", frac=0.3, small=6, max_units=None,
                     x0=None, strategy="greedy", margin=0.0, rng=None, lam_h=1.0, do_polish=True, est_only=False, gain_noise=0.0):
    """Smallest found perturbation making theta_a - theta_b <= -margin from a positive start.

    mode 'remove': delete comparisons. mode 'add': add comparisons (any type, restricted to existing participants'
    existing types, i.e. pairs that were compared). Strategy:
      'greedy'  : re-linearise after every chunk (chunk = ceil(frac * estimated remaining), 1 when <= `small`)
      'oneshot' : rank cells by influence at the base fit (AMIP-style), remove the top-k, bisect on k with exact refits
    `gain_noise` > 0 (randomised restarts, needs `rng`): the ORDER in which cells are taken in each greedy chunk uses the gains multiplied by
    exp(gain_noise * N(0,1)) and the chunk fraction is drawn from [0.1, 0.6]; budgets are still verified by exact refits.
    Returns dict(k=verified number of comparisons, flipped=bool, delta=(P,3) count change, est=linearised estimate, steps).
    """
    x0 = fit(c, lam, lam_h) if x0 is None else x0
    u = claim_vec(c, a, b)
    if u @ x0 <= 0:
        return dict(k=0, flipped=True, delta=np.zeros_like(c.n), est=0, steps=0)
    xh, H = fit(c, lam, lam_h, theta0=x0, return_hess=True)
    G = gains(c, xh, H, u, mode)
    gflat = G.ravel()
    gap0 = u @ xh
    avail = c.n.ravel() if mode == "remove" else np.full(gflat.shape, np.inf)
    # linearised estimate of the budget: take cells in decreasing gain until the cumulative gain covers the gap
    order = np.argsort(-gflat)
    pos = gflat[order] > 0
    order = order[pos]
    cap = np.minimum(avail[order], 1e12)
    cum = np.cumsum(cap * gflat[order])
    if len(order) == 0:
        est = np.inf
    else:
        idx = np.searchsorted(cum, gap0)
        if idx >= len(order):
            est = np.inf
        else:
            before = cum[idx - 1] if idx > 0 else 0.0
            before_n = np.sum(cap[:idx])
            est = before_n + (gap0 - before) / gflat[order[idx]]
    if est_only:
        return dict(k=np.nan, flipped=False, delta=None, est=est, steps=0)
    if strategy == "oneshot":
        return _oneshot(c, u, x0, order, cap, mode, lam, lam_h, est, max_units)
    delta = np.zeros(c.P * 3)
    total = 0
    steps = 0
    x = x0
    limit = max_units if max_units is not None else (c.N if mode == "remove" else 50 * c.N)
    while True:
        cur_n = c.n.ravel() + delta
        cc = c.with_n(cur_n)
        x, H = fit(cc, lam, lam_h, theta0=x, return_hess=True)
        gap = u @ x
        if gap <= -margin:
            break
        if total >= limit:
            return dict(k=total, flipped=False, delta=delta.reshape(-1, 3), est=est, steps=steps)
        G = gains(cc, x, H, u, mode).ravel()
        if gain_noise > 0:
            o = np.argsort(-(G * np.exp(gain_noise * rng.standard_normal(G.size))))
            frac = float(rng.uniform(0.1, 0.6))
        else:
            o = np.argsort(-G)
        o = o[G[o] > 0]
        if len(o) == 0:
            return dict(k=total, flipped=False, delta=delta.reshape(-1, 3), est=est, steps=steps)
        sign = -1.0 if mode == "remove" else 1.0
        av = cur_n[o] if mode == "remove" else np.full(len(o), np.inf)
        cap_ = np.minimum(av, 1e12)
        cum = np.cumsum(cap_ * G[o])
        idx = np.searchsorted(cum, gap + margin)
        if idx >= len(o):
            rem = float(np.sum(cap_))  # linear model cannot cover the gap: move a fraction of the useful mass
        else:
            before = cum[idx - 1] if idx > 0 else 0.0
            rem = np.sum(cap_[:idx]) + (gap + margin - before) / G[o[idx]]
        chunk = 1 if rem <= small else max(1, int(np.ceil(frac * rem)))
        chunk = int(min(chunk, limit - total))
        taken = []  # ordered (cell, units)
        need = chunk
        for cell, a_ in zip(o, cap_):
            if need <= 0:
                break
            t_ = int(min(a_, need))
            taken.append((cell, t_))
            need -= t_
        prev = delta.copy()
        for cell, t_ in taken:
            delta[cell] += sign * t_
        total += chunk - need
        steps += 1
        # overshoot refinement: if the chunk (>1) already flips, bisect on its prefix
        if chunk > 1:
            xt = fit(c.with_n(c.n.ravel() + delta), lam, lam_h, theta0=x)
            if u @ xt <= -margin:
                units = [cell for cell, t_ in taken for _ in range(t_)]
                lo, hi = 0, len(units)  # hi flips, lo does not (the state before the chunk didn't flip)
                while hi - lo > 1:
                    mid = (lo + hi) // 2
                    dd = prev.copy()
                    for cell in units[:mid]:
                        dd[cell] += sign
                    xm = fit(c.with_n(c.n.ravel() + dd), lam, lam_h, theta0=x)
                    if u @ xm <= -margin:
                        hi = mid
                    else:
                        lo = mid
                dd = prev.copy()
                for cell in units[:hi]:
                    dd[cell] += sign
                delta = dd
                total = int(np.abs(delta).sum())
                steps += 1
                x = xt
                break
    res = dict(k=int(np.abs(delta).sum()), flipped=True, delta=delta.reshape(-1, 3), est=est, steps=steps)
    if do_polish:
        pr = polish(c, a, b, res["delta"], mode, lam, lam_h, x0=x0, margin=margin)
        res["k_greedy"] = res["k"]
        if pr["flipped"] and pr["k"] <= res["k"]:
            res["k"], res["delta"] = pr["k"], pr["delta"]
    return res


def _oneshot(c, u, x0, order, cap, mode, lam, lam_h, est, max_units):
    """Top-k cells by base-fit influence; bisect on k with exact refits."""
    sign = -1.0 if mode == "remove" else 1.0
    cum_n = np.cumsum(cap)
    total_avail = cum_n[-1] if len(cum_n) else 0
    kmax = int(min(total_avail, max_units if max_units is not None else (c.N if mode == "remove" else 50 * c.N)))

    def delta_k(k):
        d = np.zeros(c.P * 3)
        idx = np.searchsorted(cum_n, k, side="left")
        full = order[:idx]
        d[full] = sign * cap[:idx]
        if idx < len(order):
            d[order[idx]] = sign * (k - (cum_n[idx - 1] if idx > 0 else 0))
        return d

    def flips(k):
        d = delta_k(k)
        xk = fit(c.with_n(c.n.ravel() + d), lam, lam_h, theta0=x0)
        return u @ xk <= 0

    if kmax <= 0 or not flips(kmax):
        return dict(k=kmax, flipped=False, delta=delta_k(kmax).reshape(-1, 3), est=est, steps=0)
    lo, hi = 0, kmax
    steps = 0
    while hi - lo > 1:
        mid = (lo + hi) // 2
        steps += 1
        if flips(mid):
            hi = mid
        else:
            lo = mid
    return dict(k=hi, flipped=True, delta=delta_k(hi).reshape(-1, 3), est=est, steps=steps)


# ----------------------------------------------------------------------------------------------
# heuristic baselines (no influence information)


def prefix_flip(c: Counts, a, b, cell_sequence, lam=1.0, lam_h=1.0, x0=None, margin=0.0):
    """Remove the first k entries of `cell_sequence` (flat cell indices, one per comparison); smallest k that
    flips theta_a - theta_b (bisection; assumes monotone), or None if even all of them do not."""
    x0 = fit(c, lam, lam_h) if x0 is None else x0
    u = claim_vec(c, a, b)
    base = c.n.ravel()

    def flips(k):
        d = np.zeros_like(base)
        cells, cnt = np.unique(cell_sequence[:k], return_counts=True)
        d[cells] = -cnt
        xk = fit(c.with_n(base + d), lam, lam_h, theta0=x0)
        return u @ xk <= -margin

    m = len(cell_sequence)
    if m == 0 or not flips(m):
        return None
    lo, hi = 0, m
    while hi - lo > 1:
        mid = (lo + hi) // 2
        if flips(mid):
            hi = mid
        else:
            lo = mid
    return hi


def expand_cells(c: Counts, cells):
    """Flat list of cell indices, one entry per comparison, for the given cells."""
    flat = c.n.ravel().astype(int)
    return np.repeat(cells, flat[cells])


def heuristic_flip(c: Counts, a, b, kind, lam=1.0, lam_h=1.0, x0=None, rng=None):
    """kind 'direct': remove a's wins (and half-wins) over b only (cells of the pair (a, b)), stronger-first order irrelevant;
    kind 'own_wins': remove a's wins against random opponents (random order). Returns number removed or None."""
    rng = rng or np.random.default_rng(0)
    cells = []
    for p in range(c.P):
        i, j = c.ti[p], c.tj[p]
        if i == a and (kind == "own_wins" or j == b):
            cells.append(p * 3 + 0)
        if j == a and (kind == "own_wins" or i == b):
            cells.append(p * 3 + 2)
    seq = expand_cells(c, np.array(cells, dtype=int))
    rng.shuffle(seq)
    return prefix_flip(c, a, b, seq, lam, lam_h, x0)


def polish(c: Counts, a, b, delta, mode="remove", lam=1.0, lam_h=1.0, x0=None, max_swaps=2000, margin=0.0):
    """Local search around a flipping solution `delta` (change of cell counts): alternate
    (i) swaps, moving units from the used cell with the smallest linearised gain to the available cell with the
    largest, accepted only if the exact refit lowers theta_a - theta_b, and (ii) dropping units while the claim stays
    flipped. Every accepted state is exactly refitted, so the returned count is a verified upper bound."""
    sign = -1.0 if mode == "remove" else 1.0
    u = claim_vec(c, a, b)
    base = c.n.ravel()
    r = np.abs(np.asarray(delta, dtype=float).ravel())
    x = fit(c.with_n(base + sign * r), lam, lam_h, theta0=x0)
    n_sw = 0

    def raw_gain(x_, H_):
        rr = c.V @ np.linalg.solve(H_, u)
        sg = sigmoid(c.V @ x_)
        G = (S_O[None, :] - sg[:, None]) * rr[:, None]
        return (G if mode == "remove" else -G).ravel()

    def refit(rv, xw):
        return fit(c.with_n(base + sign * rv), lam, lam_h, theta0=xw)

    while True:
        # --- swap phase: minimise the gap at fixed number of units
        while n_sw < max_swaps:
            xh, H = fit(c.with_n(base + sign * r), lam, lam_h, theta0=x, return_hess=True)
            x = xh
            gap = u @ x
            G = raw_gain(x, H)
            used = np.where(r > 0)[0]
            avail = np.where((base - r > 0) if mode == "remove" else np.ones(len(base), bool))[0]
            if len(used) == 0 or len(avail) == 0:
                break
            A = used[np.argmin(G[used])]
            Bc = avail[np.argmax(G[avail])]
            if A == Bc or G[Bc] <= G[A] * (1 + 1e-9) + 1e-15:
                break
            tmax = int(min(r[A], (base[Bc] - r[Bc]) if mode == "remove" else r[A]))
            t = max(1, tmax)
            moved = False
            while t >= 1:
                r2 = r.copy(); r2[A] -= t; r2[Bc] += t
                x2 = refit(r2, x)
                if u @ x2 < gap - 1e-12:
                    r, x, moved = r2, x2, True
                    break
                t //= 2
            n_sw += 1
            if not moved:
                break
        # --- drop phase
        xh, H = fit(c.with_n(base + sign * r), lam, lam_h, theta0=x, return_hess=True)
        x = xh
        if u @ x > -margin:
            break
        G = raw_gain(x, H)
        used = np.where(r > 0)[0]
        dropped = False
        for A in used[np.argsort(G[used])]:
            lo, hi = 0, int(r[A])  # lo units can be dropped (0 trivially), find the largest
            t = int(r[A])
            while t >= 1:
                r2 = r.copy(); r2[A] -= t
                x2 = refit(r2, x)
                if u @ x2 <= -margin:
                    r, x, dropped = r2, x2, True
                    break
                t //= 2
            if dropped:
                break
        if not dropped:
            break
    flipped = bool(u @ x <= -margin)
    return dict(k=int(r.sum()), flipped=flipped, delta=(sign * r).reshape(-1, 3))


def relabel_flip(c: Counts, a, b, lam=1.0, lam_h=1.0, x0=None, frac=0.3, small=6, margin=0.0, limit=None):
    """Smallest found number of *relabelled* comparisons (outcome changed, N fixed) that reverses theta_a - theta_b.
    Moving one comparison of type p from outcome o to o' changes the gap, to first order, by -(s_o - s_o') r_p with
    r = V H^{-1} u, so greedy over (p, o -> o') with exact refits after every chunk; bisection on the last chunk."""
    x0 = fit(c, lam, lam_h) if x0 is None else x0
    u = claim_vec(c, a, b)
    base = c.n.copy()
    delta = np.zeros_like(base)
    moves_done = 0
    x = x0
    limit = c.N if limit is None else limit
    pairs_o = [(o, q) for o in range(3) for q in range(3) if o != q]
    while True:
        n_cur = base + delta
        cc = c.with_n(n_cur)
        x, H = fit(cc, lam, lam_h, theta0=x, return_hess=True)
        gap = u @ x
        if gap <= -margin:
            return dict(k=moves_done, flipped=True, delta=delta)
        if moves_done >= limit:
            return dict(k=moves_done, flipped=False, delta=delta)
        r = c.V @ np.linalg.solve(H, u)
        cand = []  # (gain, p, o, q, avail)
        G = np.zeros((c.P, len(pairs_o)))
        for m, (o, q) in enumerate(pairs_o):
            G[:, m] = np.where(n_cur[:, o] > 0, (S_O[o] - S_O[q]) * r, -np.inf)
        flat = G.ravel()
        order = np.argsort(-flat)
        order = order[flat[order] > 0]
        if len(order) == 0:
            return dict(k=moves_done, flipped=False, delta=delta)
        pp, mm = np.divmod(order, len(pairs_o))
        av = np.array([n_cur[p, pairs_o[m][0]] for p, m in zip(pp, mm)])
        cum = np.cumsum(av * flat[order])
        idx = np.searchsorted(cum, gap + margin)
        rem = float(np.sum(av)) if idx >= len(order) else np.sum(av[:idx]) + (gap + margin - (cum[idx - 1] if idx else 0.0)) / flat[order[idx]]
        chunk = 1 if rem <= small else max(1, int(np.ceil(frac * rem)))
        chunk = int(min(chunk, limit - moves_done))
        seq = []
        need = chunk
        for p, m, a_ in zip(pp, mm, av):
            if need <= 0:
                break
            t = int(min(a_, need))
            seq += [(p, m)] * t
            need -= t
        prev = delta.copy()
        for p, m in seq:
            o, q = pairs_o[m]
            delta[p, o] -= 1; delta[p, q] += 1
        moves_done += len(seq)
        if len(seq) > 1:
            xt = fit(c.with_n(base + delta), lam, lam_h, theta0=x)
            if u @ xt <= -margin:
                lo, hi = 0, len(seq)
                while hi - lo > 1:
                    mid = (lo + hi) // 2
                    dd = prev.copy()
                    for p, m in seq[:mid]:
                        o, q = pairs_o[m]
                        dd[p, o] -= 1; dd[p, q] += 1
                    xm = fit(c.with_n(base + dd), lam, lam_h, theta0=x)
                    if u @ xm <= -margin:
                        hi = mid
                    else:
                        lo = mid
                dd = prev.copy()
                for p, m in seq[:hi]:
                    o, q = pairs_o[m]
                    dd[p, o] -= 1; dd[p, q] += 1
                return dict(k=moves_done - len(seq) + hi, flipped=True, delta=dd)
