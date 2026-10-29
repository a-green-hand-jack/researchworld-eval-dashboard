"""Bradley-Terry fitting on aggregated comparison counts, influence quantities, and
worst-case perturbation search (drop / relabel / inject) with exact refit verification.

Data model.  A leaderboard is a set of comparisons (a, b, y, home) with y in {0, 1/2, 1}
(ties count as half a win, as in Chatbot Arena's BT leaderboard).  Because the BT likelihood
depends on the data only through per-group counts, we store a weight table W[g, o] where
g indexes a "group" (unordered pair, or ordered pair plus home flag) and o indexes the outcome
y = OUT[o] in (0, 0.5, 1) from the perspective of the group's first competitor.

Model.  P(a beats b) = sigmoid(theta_a - theta_b + eta * home).  We minimise the negative
log-likelihood plus (lam/2)||theta||^2 with a tiny lam (1e-3) that only fixes the location
and guarantees a finite optimum.
"""
import numpy as np
import pandas as pd

OUT = np.array([0.0, 0.5, 1.0])
LAM = 1e-3


def sigmoid(z):
    return 1.0 / (1.0 + np.exp(-z))


class Board:
    """Aggregated leaderboard.  Groups cover *all* pairs so that injections are possible."""

    def __init__(self, df, all_pairs=True):
        names = sorted(set(df.a) | set(df.b))
        self.names = np.array(names)
        self.K = K = len(names)
        idx = {n: i for i, n in enumerate(names)}
        a = df.a.map(idx).to_numpy()
        b = df.b.map(idx).to_numpy()
        y = df.y.to_numpy(float)
        h = df.home.to_numpy(int) if "home" in df else np.zeros(len(df), int)
        self.has_home = bool(h.any())
        # canonical orientation for neutral comparisons: a < b
        sw = (h == 0) & (a > b)
        a, b = np.where(sw, b, a), np.where(sw, a, b)
        y = np.where(sw, 1 - y, y)
        # group table
        if all_pairs:
            ga, gb = np.triu_indices(K, 1)
            gh = np.zeros(len(ga), int)
            if self.has_home:  # ordered pairs with home flag (a at home)
                aa, bb = np.where(~np.eye(K, dtype=bool))
                ga, gb, gh = aa, bb, np.ones(len(aa), int)
                # keep neutral groups for neutral games if present
                if (h == 0).any():
                    na, nb = np.triu_indices(K, 1)
                    ga = np.concatenate([ga, na]); gb = np.concatenate([gb, nb])
                    gh = np.concatenate([gh, np.zeros(len(na), int)])
        else:
            u = pd.DataFrame(dict(a=a, b=b, h=h)).drop_duplicates()
            ga, gb, gh = u.a.to_numpy(), u.b.to_numpy(), u.h.to_numpy()
        self.ga, self.gb, self.gh = ga, gb, gh
        key = {(x, z, w): i for i, (x, z, w) in enumerate(zip(ga, gb, gh))}
        gid = np.array([key[(x, z, w)] for x, z, w in zip(a, b, h)])
        oid = np.searchsorted(OUT, y)
        W = np.zeros((len(ga), 3))
        np.add.at(W, (gid, oid), 1.0)
        self.W0 = W
        self.N = int(W.sum())
        P = K + (1 if self.has_home else 0)
        X = np.zeros((len(ga), P))
        X[np.arange(len(ga)), ga] = 1.0
        X[np.arange(len(ga)), gb] -= 1.0
        if self.has_home:
            X[:, K] = gh
        self.X = X
        self.P = P
        # comparison-level arrays (for bootstrap / random perturbation)
        self.gid, self.oid = gid, oid

    # ------------------------------------------------------------------ fitting
    def fit(self, W=None, theta0=None, tol=1e-10, maxit=100):
        W = self.W0 if W is None else W
        n = W.sum(1)
        S = W @ OUT
        m = n > 0
        X, n, S = self.X[m], n[m], S[m]
        th = np.zeros(self.P) if theta0 is None else theta0.copy()
        reg = np.full(self.P, LAM)
        if self.has_home:
            reg[self.K] = 1e-8
        for it in range(maxit):
            s = X @ th
            p = sigmoid(s)
            g = X.T @ (n * p - S) + reg * th
            H = (X * (n * p * (1 - p))[:, None]).T @ X + np.diag(reg)
            step = np.linalg.solve(H, g)
            # damped Newton (objective is convex; damping only for safety)
            t = 1.0
            f0 = self._obj(th, X, n, S, reg)
            while t > 1e-4 and self._obj(th - t * step, X, n, S, reg) > f0 + 1e-12:
                t *= 0.5
            th = th - t * step
            if np.abs(g).max() < tol:
                break
        s = self.X @ th
        p = sigmoid(s)
        Hf = (self.X * (W.sum(1) * p * (1 - p))[:, None]).T @ self.X + np.diag(reg)
        return th, Hf, p

    @staticmethod
    def _obj(th, X, n, S, reg):
        s = X @ th
        # -[S log sig(s) + (n-S) log sig(-s)]
        return float(np.sum(n * np.logaddexp(0, s) - S * s) + 0.5 * np.sum(reg * th * th))

    def ranking(self, th):
        return np.argsort(-th[: self.K], kind="stable")

    def contrast(self, i, j):
        v = np.zeros(self.P)
        v[i] = 1.0
        v[j] = -1.0
        return v


# ---------------------------------------------------------------------- perturbations
MODES = ("drop", "flip", "add", "add_target")


def unit_effects(board, W, th, H, p, v, mode, target=None):
    """First-order change of v.theta per unit of each candidate move.
    Returns (effects[G,3], capacity[G,3], dest_outcome[G,3] or None)."""
    u = np.linalg.solve(H, v)
    ux = board.X @ u  # (G,)
    if mode == "drop":
        eff = ux[:, None] * (p[:, None] - OUT[None, :])
        cap = W.copy()
        return eff, cap, None
    if mode == "flip":
        # relabel to the most harmful other outcome (always an extreme: 0 or 1)
        e0 = ux[:, None] * (0.0 - OUT[None, :])
        e1 = ux[:, None] * (1.0 - OUT[None, :])
        dest = np.where(e0 <= e1, 0, 2)
        eff = np.minimum(e0, e1)
        cap = W.copy()
        cap[dest == np.arange(3)[None, :]] = 0  # relabel to same outcome is a no-op
        return eff, cap, dest
    if mode in ("add", "add_target"):
        eff = ux[:, None] * (OUT[None, :] - p[:, None])
        cap = np.full_like(W, np.inf)
        cap[:, 1] = 0  # only inject decisive votes
        if board.has_home:
            pass
        if mode == "add_target":
            # only votes on battles that involve one of the two competitors in v
            i, j = target
            inv = np.isin(board.ga, (i, j)) | np.isin(board.gb, (i, j))
            cap[~inv] = 0
        # restrict injections to groups that exist in the original design (observed pairs)
        cap[board.W0.sum(1) == 0] = 0
        return eff, cap, None
    raise ValueError(mode)


def apply_moves(W, moves, mode, dest):
    W = W.copy()
    for (g, o), c in moves.items():
        if mode == "drop":
            W[g, o] -= c
        elif mode == "flip":
            W[g, o] -= c
            W[g, dest[(g, o)]] += c
        else:
            W[g, o] += c
    return W


def plan_units(eff, cap, need, limit=None):
    """Greedy first-order plan: smallest number of units whose summed effect <= -need."""
    flat = eff.ravel()
    capf = cap.ravel()
    order = np.argsort(flat, kind="stable")
    order = order[(capf[order] > 0) & (flat[order] < 0)]
    total, k, plan = 0.0, 0, []
    for idx in order:
        e = flat[idx]
        c_need = int(np.ceil((need - total) / (-e) - 1e-12))
        c = int(min(capf[idx], max(c_need, 1)))
        plan.append((idx, c, e))
        total += -e * c
        k += c
        if total >= need:
            return plan, k, True
        if limit is not None and k > limit:
            break
    return plan, k, False


def min_perturbation(board, i, j, mode, max_units=None, step_frac=0.5, prune=True, W_start=None):
    """Smallest perturbation (found by iterated first-order greedy + refit) that makes
    theta_j > theta_i, given theta_i > theta_j originally.  Returns dict with
    k (number of comparisons dropped / relabelled / injected), verified flag, and the moves."""
    W0 = board.W0 if W_start is None else W_start
    v = board.contrast(i, j)
    th, H, p = board.fit(W0)
    f0 = float(v @ th)
    if f0 <= 1e-9:  # exact (numerical) tie: the order is already arbitrary
        return dict(k=0, verified=True, f0=f0, f_final=f0, iters=0, moves={}, W=W0.copy(), tie=True)
    max_units = max_units or (board.N if mode in ("drop", "flip") else 50 * board.N)
    G = W0.shape[0]
    moves = {}
    dest_map = {}
    W = W0.copy()
    k = 0
    target = (i, j)
    eps = 1e-9
    it = 0
    while True:
        it += 1
        f = float(v @ th)
        if f < -eps:
            break
        eff, cap, dest = unit_effects(board, W, th, H, p, v, mode, target)
        plan, kk, ok = plan_units(eff, cap, f + 1e-7, limit=max_units - k)
        if not plan:
            return dict(k=None, verified=False, f0=f0, iters=it)
        # take a fraction of the plan (at least one unit) then refit
        take = max(1, int(np.ceil(step_frac * kk))) if kk > 2 else kk
        seq = []  # ordered (cell, count) runs of this step
        left = take
        for idx, c, e in plan:
            g, o = divmod(idx, 3)
            cc = min(c, left)
            if cc <= 0:
                break
            seq.append(((g, o), cc))
            if dest is not None:
                dest_map[(g, o)] = dest[g, o]
            left -= cc

        def prefix(m):
            st = {}
            for key, cc in seq:
                c = min(cc, m)
                if c <= 0:
                    break
                st[key] = c
                m -= c
            return st

        def try_step(m):
            st = prefix(m)
            dd = {key: dest_map[key] for key in st} if dest is not None else None
            W2 = apply_moves(W, st, mode, dd)
            th2, H2, p2 = board.fit(W2, th)
            return st, W2, th2, H2, p2

        st, W2, th2, H2, p2 = try_step(take)
        if float(v @ th2) < -eps and take > 1:
            # overshoot: bisect for the shortest prefix of this step that already flips
            lo, hi = 0, take
            best = (st, W2, th2, H2, p2)
            while hi - lo > 1:
                mid = (lo + hi) // 2
                cand = try_step(mid)
                if float(v @ cand[2]) < -eps:
                    hi, best = mid, cand
                else:
                    lo = mid
            st, W2, th2, H2, p2 = best
        W, th, H, p = W2, th2, H2, p2
        for key, c in st.items():
            moves[key] = moves.get(key, 0) + c
        k += sum(st.values())
        if k > max_units:
            return dict(k=None, verified=False, f0=f0, iters=it)
    # pruning: try undoing single units, least useful first (bounded number of refits)
    if prune and k > 1:
        budget = 25
        eff_now, _, _ = unit_effects(board, W, th, H, p, v, mode if mode != "add_target" else "add", target)
        keys = sorted(moves, key=lambda kk_: eff_now[kk_])[::-1]  # least harmful first
        for key in keys:
            while moves[key] > 0 and budget > 0:
                budget -= 1
                undo = {key: -1}
                dd = {key: dest_map[key]} if mode == "flip" else None
                W2 = apply_moves(W, undo, mode, dd)
                th2, H2, p2 = board.fit(W2, th)
                if float(v @ th2) < -eps:
                    W, th, H, p = W2, th2, H2, p2
                    moves[key] -= 1
                    k -= 1
                else:
                    break
            if budget <= 0:
                break
    # exact verification from scratch
    thv, _, _ = board.fit(W)
    fv = float(v @ thv)
    moves = {kk_: c for kk_, c in moves.items() if c}
    return dict(k=int(k), verified=bool(fv < 0), f0=f0, f_final=fv, iters=it, moves=moves, W=W)


def first_order_k(board, i, j, mode="drop", W=None):
    """One-shot first-order (AMIP-style) estimate at the original fit and its refit check
    along the same ordering (Broderick et al. style)."""
    W0 = board.W0 if W is None else W
    v = board.contrast(i, j)
    th, H, p = board.fit(W0)
    f0 = float(v @ th)
    if f0 <= 1e-9:
        return dict(k_fo=0, k_os=0, k_lb1=0)
    eff, cap, dest = unit_effects(board, W0, th, H, p, v, mode, (i, j))
    plan, k_fo, ok = plan_units(eff, cap, f0)
    if not ok:
        return dict(k_fo=None, k_os=None)
    max_eff = -eff[cap > 0].min()
    # walk along the one-shot ordering until the refit flips
    flat = eff.ravel(); capf = cap.ravel()
    order = [idx for idx in np.argsort(flat, kind="stable") if flat[idx] < 0 and capf[idx] > 0]
    units = []
    for idx in order:
        units += [idx] * int(min(capf[idx], 20 * k_fo + 1000))
        if len(units) > 20 * k_fo + 1000:
            break

    def flips(k):
        moves = {}
        for idx in units[:k]:
            g, o = divmod(idx, 3)
            moves[(g, o)] = moves.get((g, o), 0) + 1
        dd = {key: dest[key] for key in moves} if dest is not None else None
        Wk = apply_moves(W0, moves, mode, dd)
        return float(v @ board.fit(Wk, th)[0]) < -1e-9

    k = k_fo
    if flips(k):
        lo, hi = 0, k  # shrink
        while hi - lo > 1:
            mid = (lo + hi) // 2
            if flips(mid):
                hi = mid
            else:
                lo = mid
        k_os = hi
    else:
        step = max(1, k // 10)
        k_os = None
        kk = k
        while kk < len(units):
            kk = min(len(units), kk + step)
            if flips(kk):
                lo, hi = kk - step, kk
                while hi - lo > 1:
                    mid = (lo + hi) // 2
                    if flips(mid):
                        hi = mid
                    else:
                        lo = mid
                k_os = hi
                break
            step *= 2
    return dict(k_fo=int(k_fo), k_os=k_os, k_lb1=int(np.ceil(f0 / max_eff)))


def pair_stats(board, i, j, th=None, H=None):
    if th is None:
        th, H, _ = board.fit()
    v = board.contrast(i, j)
    d = float(v @ th)
    se = float(np.sqrt(v @ np.linalg.solve(H, v)))
    n = board.W0.sum(1)
    inv = np.isin(board.ga, (i, j)) | np.isin(board.gb, (i, j))
    direct = ((board.ga == i) & (board.gb == j)) | ((board.ga == j) & (board.gb == i))
    ni = n[(board.ga == i) | (board.gb == i)].sum()
    nj = n[(board.ga == j) | (board.gb == j)].sum()
    return dict(gap=d, se=se, z=d / se, n_loc=float(n[inv].sum()), n_i=float(ni), n_j=float(nj),
                n_direct=float(n[direct].sum()))
