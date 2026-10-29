"""Bradley-Terry fitting, influence approximations and worst-case perturbation search.

Data are stored in *aggregated* form.  Because the Bradley-Terry likelihood depends on
the data only through the counts of each (pair, home, outcome) cell, every comparison in
a cell has the same influence on the fit; all searches below therefore operate on the
cell-count matrix C[g, o] (g = pair group, o in {0: loss, 1: tie, 2: win} for item a).

Conventions
-----------
P(a beats b) = sigmoid(theta_a - theta_b + eta * h),   ties count as y = 0.5.
A small ridge penalty lam * ||theta||^2 makes the MLE unique and finite.
"""
import itertools

import numpy as np
import pandas as pd

YV = np.array([0.0, 0.5, 1.0])


def sigmoid(x):
    return 0.5 * (1.0 + np.tanh(0.5 * x))


class Data:
    """Aggregated comparison data."""

    def __init__(self, df, items=None, all_pairs=False):
        if items is None:
            items = sorted(set(df.a) | set(df.b))
        self.items = list(items)
        idx = {m: k for k, m in enumerate(self.items)}
        a = df.a.map(idx).to_numpy()
        b = df.b.map(idx).to_numpy()
        y = df.y.to_numpy(float)
        h = df.h.to_numpy(int) if "h" in df else np.zeros(len(df), int)
        # canonical orientation a < b
        sw = a > b
        a, b = np.where(sw, b, a), np.where(sw, a, b)
        y = np.where(sw, 1 - y, y)
        h = np.where(sw, -h, h)
        o = np.rint(y * 2).astype(int)
        key = pd.DataFrame({"a": a, "b": b, "h": h, "o": o})
        grp = key.groupby(["a", "b", "h", "o"]).size().reset_index(name="n")
        groups = grp[["a", "b", "h"]].drop_duplicates().reset_index(drop=True)
        if all_pairs:  # add every unordered pair (h = 0) so that injection can use it
            K = len(self.items)
            ii, jj = np.triu_indices(K, 1)
            extra = pd.DataFrame({"a": ii, "b": jj, "h": 0})
            groups = pd.concat([groups, extra]).drop_duplicates().reset_index(drop=True)
        groups["g"] = np.arange(len(groups))
        grp = grp.merge(groups, on=["a", "b", "h"])
        self.ga = groups.a.to_numpy()
        self.gb = groups.b.to_numpy()
        self.gh = groups.h.to_numpy().astype(float)
        G = len(groups)
        self.C = np.zeros((G, 3))
        np.add.at(self.C, (grp.g.to_numpy(), grp.o.to_numpy()), grp.n.to_numpy())
        self.K = len(self.items)
        self.home = bool(np.any(self.gh != 0))
        self.P = self.K + int(self.home)
        X = np.zeros((G, self.P))
        X[np.arange(G), self.ga] += 1.0
        X[np.arange(G), self.gb] -= 1.0
        if self.home:
            X[:, self.K] = self.gh
        self.X = X
        self.N = int(self.C.sum())

    def counts_involving(self, items):
        m = np.isin(self.ga, items) | np.isin(self.gb, items)
        return int(self.C[m].sum())


class BT:
    def __init__(self, data, lam=1e-3):
        self.d = data
        self.lam = lam
        self.pen = np.zeros(data.P)
        self.pen[: data.K] = 2 * lam

    def fit(self, C=None, theta0=None, tol=1e-9, maxit=100):
        d = self.d
        C = d.C if C is None else C
        n = C.sum(1)
        w = C @ YV
        th = np.zeros(d.P) if theta0 is None else theta0.copy()
        X = d.X
        for _ in range(maxit):
            p = sigmoid(X @ th)
            grad = X.T @ (w - n * p) - self.pen * th
            H = (X * (n * p * (1 - p))[:, None]).T @ X + np.diag(self.pen)
            step = np.linalg.solve(H, grad)
            mx = np.abs(step).max()
            if mx > 3:
                step *= 3 / mx
            th += step
            if mx < tol:
                break
        p = sigmoid(X @ th)
        H = (X * (n * p * (1 - p))[:, None]).T @ X + np.diag(self.pen)
        return th, H, p

    # ------------------------------------------------------------------
    def influence(self, th, H, p, avec):
        """Per-cell first-order change of avec.theta for unit operations.

        Returns xv (G,), and matrices (G, 3):
          drop[g, o]   : remove one comparison with outcome o from group g
          inject[g, o] : add one comparison with outcome o to group g
        flip from o to o' equals inject[g, o'] - inject[g, o] + ... = (y' - y) xv.
        """
        v = np.linalg.solve(H, avec)
        xv = self.d.X @ v
        resid = YV[None, :] - p[:, None]  # (G,3)
        drop = -resid * xv[:, None]
        inject = resid * xv[:, None]
        return xv, drop, inject


def avec_for(d, i, j):
    a = np.zeros(d.P)
    a[i] += 1.0
    a[j] -= 1.0
    return a


def ranking(th, K):
    return np.argsort(-th[:K], kind="stable")


# ----------------------------------------------------------------------
# Worst-case search (greedy with refits, then pruning)
# ----------------------------------------------------------------------
class Target:
    """Gap that the adversary wants to push below zero.

    kind='pair'   : gap = theta_i - theta_j  (i currently above j)
    kind='top'    : gap = max_{k != i} theta_k - theta_i   (promote i to rank 1)
    """

    def __init__(self, kind, i, j=None):
        self.kind, self.i, self.j = kind, i, j

    def gap(self, th, d):
        if self.kind == "pair":
            return th[self.i] - th[self.j], avec_for(d, self.i, self.j)
        t = th[: d.K].copy()
        t[self.i] = -np.inf
        j = int(np.argmax(t))
        return th[j] - th[self.i], avec_for(d, j, self.i)


def _apply(C, op, k):
    mode, g, o, o2 = op
    C = C.copy()
    if mode == "drop":
        C[g, o] -= k
    elif mode == "inject":
        C[g, o] += k
    elif mode == "flip":
        C[g, o] -= k
        C[g, o2] += k
    return C


def _pick(s, rng, q):
    """argmin of s, or (randomised restarts) a uniform pick among the q smallest finite entries."""
    if rng is None or q <= 1:
        return np.unravel_index(np.argmin(s), s.shape)
    flat = s.ravel()
    cand = np.argsort(flat)[:q]
    cand = cand[np.isfinite(flat[cand]) & (flat[cand] < 0)]
    if len(cand) == 0:
        return np.unravel_index(np.argmin(s), s.shape)
    return np.unravel_index(rng.choice(cand), s.shape)


def _best_op(model, C, th, H, p, avec, mode, allowed=None, rng=None, q=1):
    """Return (op, per-unit predicted change, capacity) of the most harmful unit operation."""
    xv, drop, inject = model.influence(th, H, p, avec)
    if mode == "drop":
        s = np.where(C > 0, drop, np.inf)
        if allowed is not None:
            s = np.where(allowed[:, None], s, np.inf)
        g, o = _pick(s, rng, q)
        return ("drop", g, o, None), s[g, o], C[g, o]
    if mode == "inject":
        s = inject.copy()
        if allowed is not None:
            s = np.where(allowed[:, None], s, np.inf)
        g, o = _pick(s, rng, q)
        return ("inject", g, o, None), s[g, o], np.inf
    if mode == "flip":
        # flip o -> o2 : (y2 - y) * xv
        dy = YV[None, :] - YV[:, None]  # [o, o2]
        s = dy[None, :, :] * xv[:, None, None]  # (G, o, o2)
        s = np.where((C > 0)[:, :, None], s, np.inf)
        g, o, o2 = _pick(s, rng, q)
        return ("flip", g, o, o2), s[g, o, o2], C[g, o]
    raise ValueError(mode)


def greedy(model, target, mode="drop", C0=None, th0=None, prune=True, max_steps=20000,
           frac=0.5, budget=None, rng=None, q=1):
    """Greedy worst-case search with refits.

    Returns dict(m=number of unit operations (np.inf if not found), ops=list, refits=...)
    The result is an *upper bound* on the minimal perturbation size.
    With rng and q > 1 the search is randomised (pick among the q most harmful cells, random
    batch fraction) -- used for restarts.
    """
    d = model.d
    C = d.C.copy() if C0 is None else C0.copy()
    th, H, p = model.fit(C, th0)
    gap0, _ = target.gap(th, d)
    if gap0 <= 0:
        return dict(m=0, ops={}, refits=1, gap0=gap0)
    ops = {}
    m = 0
    refits = 1
    for _ in range(max_steps):
        gap, avec = target.gap(th, d)
        if gap < 0:
            break
        op, s, cap = _best_op(model, C, th, H, p, avec, mode, rng=rng, q=q)
        if not np.isfinite(s) or s >= 0:
            return dict(m=np.inf, ops={}, refits=refits, gap0=gap0)
        need = gap / (-s)
        fr = frac if rng is None else rng.uniform(0.1, frac)
        k = int(max(1, np.floor(fr * need))) if need > 2 else 1
        k = int(min(k, cap))
        if budget is not None and m + k > budget:
            return dict(m=np.inf, ops={}, refits=refits, gap0=gap0)
        C = _apply(C, op, k)
        ops[op] = ops.get(op, 0) + k
        m += k
        th, H, p = model.fit(C, th)
        refits += 1
    else:
        return dict(m=np.inf, ops={}, refits=refits, gap0=gap0)

    if prune:
        C, ops, m, r = _prune(model, target, d.C if C0 is None else C0, ops, th)
        refits += r
    return dict(m=m, ops=ops, refits=refits, gap0=gap0, C=C)


def _build(C0, ops):
    C = C0.copy()
    for op, k in ops.items():
        C = _apply(C, op, k)
    return C


def _prune(model, target, C0, ops, th):
    """Undo as many unit operations as possible while the gap stays negative."""
    d = model.d
    refits = 0

    def ok(o):
        nonlocal refits
        refits += 1
        t, _, _ = model.fit(_build(C0, o), th)
        return target.gap(t, d)[0] < 0

    for op in sorted(ops, key=lambda z: ops[z]):
        k = ops[op]
        lo, hi = 0, k  # hi is feasible
        while lo < hi:
            mid = (lo + hi) // 2
            trial = dict(ops)
            trial[op] = mid
            if ok(trial):
                hi = mid
            else:
                lo = mid + 1
        ops[op] = hi
    ops = {o: k for o, k in ops.items() if k > 0}
    return _build(C0, ops), ops, int(sum(ops.values())), refits


def amip_oneshot(model, target, C0=None):
    """Broderick-style one-shot approximation for dropping.

    Returns (m_linear, m_refit): m_linear = number of drops whose summed first-order
    influence exceeds the gap; m_refit = smallest prefix (of the same influence ordering)
    that actually flips after refitting (np.inf if none).
    """
    d = model.d
    C0 = d.C if C0 is None else C0
    th, H, p = model.fit(C0)
    gap, avec = target.gap(th, d)
    _, drop, _ = model.influence(th, H, p, avec)
    s = drop.ravel()
    cnt = C0.ravel()
    order = np.argsort(s)
    order = order[(cnt[order] > 0) & (s[order] < 0)]
    cum_m = np.cumsum(cnt[order])
    cum_s = np.cumsum(cnt[order] * s[order])
    if len(order) == 0 or cum_s[-1] > -gap:
        m_lin = np.inf
    else:
        q = np.searchsorted(-cum_s, gap)  # first cell where cumulative exceeds gap
        prev_m = cum_m[q - 1] if q > 0 else 0
        prev_s = cum_s[q - 1] if q > 0 else 0
        m_lin = int(prev_m + np.ceil((gap + prev_s) / (-s[order[q]])))

    def prefix_C(m):
        C = C0.copy().ravel()
        rem = m
        for c in order:
            take = min(rem, C[c])
            C[c] -= take
            rem -= take
            if rem <= 0:
                break
        return C.reshape(C0.shape)

    def flipped(m):
        t, _, _ = model.fit(prefix_C(m), th)
        return target.gap(t, d)[0] < 0

    total = int(cum_m[-1]) if len(order) else 0
    if total == 0 or not flipped(total):
        return m_lin, np.inf
    lo, hi = 0, total
    if np.isfinite(m_lin) and m_lin <= total and flipped(m_lin):
        hi = m_lin
    while lo < hi:  # binary search (flip is monotone in practice along this ordering)
        mid = (lo + hi) // 2
        if flipped(mid):
            hi = mid
        else:
            lo = mid + 1
    return m_lin, hi


def headtohead(model, target):
    """Naive baseline: drop i-over-j head-to-head wins, then i-j ties."""
    d = model.d
    i, j = target.i, target.j
    th, _, _ = model.fit()
    gs = np.where(((d.ga == i) & (d.gb == j)) | ((d.ga == j) & (d.gb == i)))[0]
    seq = []
    for g in gs:
        win_o = 2 if d.ga[g] == i else 0
        seq.append((g, win_o))
    for g in gs:
        seq.append((g, 1))
    C = d.C.copy()
    m = 0
    for g, o in seq:
        while C[g, o] > 0:
            C[g, o] -= 1
            m += 1
            t, _, _ = model.fit(C, th)
            if target.gap(t, d)[0] < 0:
                return m
    return np.inf


def exhaustive_no_smaller(model, target, m_upper, mode="drop"):
    """Exact check that no drop set of size < m_upper flips the target (small data only).

    Returns (smallest flipping size found <= m_upper - 1 or None, number of fits).
    """
    d = model.d
    th, _, _ = model.fit()
    cells = [(g, o) for g in range(len(d.ga)) for o in range(3) if d.C[g, o] > 0]
    fits = 0
    for size in range(1, int(m_upper)):
        for combo in itertools.combinations_with_replacement(range(len(cells)), size):
            C = d.C.copy()
            okc = True
            for c in combo:
                g, o = cells[c]
                C[g, o] -= 1
                if C[g, o] < 0:
                    okc = False
                    break
            if not okc:
                continue
            t, _, _ = model.fit(C, th, tol=1e-8)
            fits += 1
            if target.gap(t, d)[0] < 0:
                return size, fits
    return None, fits


def random_drop_flip_prob(model, target, m, reps, rng):
    """Probability that dropping m uniformly random comparisons flips the target."""
    d = model.d
    th, _, _ = model.fit()
    flat = d.C.ravel().astype(np.int64)
    hits = 0
    for _ in range(reps):
        dr = rng.multivariate_hypergeometric(flat, m)
        t, _, _ = model.fit((flat - dr).reshape(d.C.shape).astype(float), th)
        hits += target.gap(t, d)[0] < 0
    return hits / reps


def stream_attack(model, target, rng, allowed_groups=None, vote_for=None, max_votes=10 ** 6, frac=0.5):
    """Realistic vote injection: battles arrive with pairs drawn from the empirical
    pair distribution (optionally restricted to `allowed_groups`); the attacker votes in
    every arriving battle, choosing the outcome with the most harmful first-order effect
    (or a fixed policy `vote_for` = item that must win).  Returns the number of votes.
    """
    d = model.d
    C = d.C.copy()
    n = d.C.sum(1)
    w = n.copy()
    if allowed_groups is not None:
        w = np.where(allowed_groups, w, 0)
    w = w / w.sum()
    th, H, p = model.fit(C)
    votes = 0
    while votes < max_votes:
        gap, avec = target.gap(th, d)
        if gap < 0:
            return votes
        xv, _, inject = model.influence(th, H, p, avec)
        if vote_for is None:
            best = inject.min(1)  # attacker picks the best outcome for each battle
            bo = inject.argmin(1)
        else:
            bo = np.where(d.ga == vote_for, 2, 0)
            best = inject[np.arange(len(bo)), bo]
        exp_gain = -(w * np.minimum(best, 0)).sum()
        if exp_gain <= 0:
            return np.inf
        need = gap / exp_gain
        k = int(max(1, np.floor(frac * need))) if need > 2 else 1
        draws = rng.multinomial(k, w)
        g = np.nonzero(draws)[0]
        add = draws[g]
        useful = best[g] < 0
        C[g[useful], bo[g[useful]]] += add[useful]
        votes += k
        th, H, p = model.fit(C, th)
    return np.inf


def pair_stats(model, th, H, p, i, j, C=None):
    """z-score of the gap theta_i - theta_j and influence concentration."""
    d = model.d
    C = d.C if C is None else C
    avec = avec_for(d, i, j)
    gap = th[i] - th[j]
    Hinv_a = np.linalg.solve(H, avec)
    se = float(np.sqrt(avec @ Hinv_a))
    _, drop, _ = model.influence(th, H, p, avec)
    harm = np.where(C > 0, drop, np.inf)
    psi_max = float(-harm.min())
    # sandwich-type SE from per-comparison influences
    s_sand = float(np.sqrt((C * drop ** 2).sum()))
    return dict(gap=float(gap), se=se, z=float(gap / se), psi_max=psi_max, kappa=se / psi_max,
                se_sand=s_sand, n_local=d.counts_involving([i, j]))
