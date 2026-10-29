"""Bradley-Terry leaderboards on aggregated comparison classes, plus worst-case
(adversarial) perturbation search: remove / flip / add K comparisons so that a
chosen ranking statement flips.  All fits operate on *classes*: comparisons that
are identical for the model (same pair, same home flag, same outcome) are merged
and carry an integer weight, so every fit costs O(d^2) rather than O(N)."""
import numpy as np
import scipy.sparse as sp
import scipy.linalg as sla

LAM = 1e-3  # tiny ridge on all parameters (fixes the gauge, keeps winless teams finite)


def sigmoid(x):
    return 0.5 * (1.0 + np.tanh(0.5 * x))


class Board:
    """Weighted logistic (Bradley-Terry) model.
    Class c: P(A_c beats B_c) = sigmoid(theta[A_c]-theta[B_c] + gamma*H_c); outcome y_c in {0,.5,1}
    with weight w_c (count).  group[c] indexes the (pair, home) key shared by the alternative
    outcomes of a comparison (used for 'flip' moves)."""

    def __init__(self, names, A, B, H, Y, W, group, has_home=False, lam=LAM):
        self.names = list(names)
        self.m = len(names)
        self.A, self.B, self.H, self.Y = map(np.asarray, (A, B, H, Y))
        self.W0 = np.asarray(W, dtype=float)
        self.group = np.asarray(group)
        self.has_home = has_home
        self.d = self.m + (1 if has_home else 0)
        self.lam = lam
        C = len(self.A)
        rows = np.concatenate([np.arange(C), np.arange(C)])
        cols = np.concatenate([self.A, self.B])
        vals = np.concatenate([np.ones(C), -np.ones(C)])
        X = sp.csr_matrix((vals, (rows, cols)), shape=(C, self.d))
        if has_home:
            X = sp.hstack([X[:, :self.m], sp.csr_matrix(self.H.reshape(-1, 1).astype(float))]).tocsr()
        self.X = X
        self.XT = X.T.tocsr()
        # members of each group (for flips)
        order = np.argsort(self.group, kind="stable")
        self._gorder = order
        ng = self.group.max() + 1
        self._gstart = np.searchsorted(self.group[order], np.arange(ng + 1))
        self.n_total = int(self.W0.sum())
        self.theta0 = None

    # ---------------- fitting
    def _nll(self, theta, w):
        eta = self.X @ theta
        # y*log p + (1-y)*log(1-p) = y*eta - log(1+e^eta)
        ll = np.sum(w * (self.Y * eta - np.logaddexp(0, eta)))
        return -ll + 0.5 * self.lam * theta @ theta

    def fit(self, w=None, theta0=None, tol=1e-9, maxit=60):
        w = self.W0 if w is None else w
        th = np.zeros(self.d) if theta0 is None else theta0.copy()
        f = self._nll(th, w)
        for _ in range(maxit):
            eta = self.X @ th
            p = sigmoid(eta)
            grad = self.XT @ (w * (self.Y - p)) - self.lam * th
            Hm = (self.XT @ sp.diags(w * p * (1 - p)) @ self.X).toarray() + self.lam * np.eye(self.d)
            step = sla.solve(Hm, grad, assume_a="pos")
            t = 1.0
            while True:
                th_new = th + t * step
                f_new = self._nll(th_new, w)
                if f_new <= f + 1e-12 or t < 1e-6:
                    break
                t *= 0.5
            th, f_old, f = th_new, f, f_new
            if np.max(np.abs(t * step)) < tol:
                break
        return th

    def hess(self, th, w):
        p = sigmoid(self.X @ th)
        return (self.XT @ sp.diags(w * p * (1 - p)) @ self.X).toarray() + self.lam * np.eye(self.d)

    def base_fit(self):
        if self.theta0 is None:
            self.theta0 = self.fit()
        return self.theta0

    def ranking(self, th=None):
        th = self.base_fit() if th is None else th
        return np.argsort(-th[:self.m], kind="stable")

    def comparisons_per_model(self, w=None):
        w = self.W0 if w is None else w
        n = np.zeros(self.m)
        np.add.at(n, self.A, w)
        np.add.at(n, self.B, w)
        return n

    # ---------------- influence helpers
    def contrast(self, i, j):
        c = np.zeros(self.d)
        c[i], c[j] = 1.0, -1.0
        return c

    def class_effects(self, th, w, c):
        """s_c = (y_c - p_c) * (x_c . v), v = H^{-1} c.   Removing one comparison of class c shifts
        c.theta by -s_c (first order); adding one shifts it by +s_c; moving a comparison from class
        c to class c' of the same group shifts it by s_{c'} - s_c."""
        Hm = self.hess(th, w)
        v = sla.solve(Hm, c, assume_a="pos")
        p = sigmoid(self.X @ th)
        s = (self.Y - p) * (self.X @ v)
        se = float(np.sqrt(c @ v))
        return s, se

    # ---------------- attack search
    def _benefits(self, mode, s, w, allowed):
        """returns (benefit per source class, capacity per source class, dest class or -1)."""
        C = len(s)
        dest = -np.ones(C, dtype=int)
        if mode == "remove":
            ben, cap = s.copy(), w.copy()
        elif mode == "add":
            ben, cap = -s, np.full(C, np.inf)
        elif mode == "flip":
            ben = np.full(C, -np.inf)
            cap = w.copy()
            for g in range(len(self._gstart) - 1):
                idx = self._gorder[self._gstart[g]:self._gstart[g + 1]]
                if len(idx) < 2:
                    continue
                sg = s[idx]
                for k, cidx in enumerate(idx):
                    if w[cidx] <= 0:
                        continue
                    sg2 = sg.copy()
                    sg2[k] = np.inf
                    kk = int(np.argmin(sg2))
                    ben[cidx] = s[cidx] - sg[kk]
                    dest[cidx] = idx[kk]
        else:
            raise ValueError(mode)
        if allowed is not None:
            ben = np.where(allowed, ben, -np.inf)
        ben = np.where(cap > 0, ben, -np.inf)
        return ben, cap, dest

    @staticmethod
    def _plan(ben, cap, need):
        """greedy plan: list of (class, count) in decreasing benefit until cumulative benefit>=need;
        returns plan and the total number of unit moves K_est (inf if infeasible)."""
        order = np.argsort(-ben)
        plan, tot, K = [], 0.0, 0
        for c in order:
            if ben[c] <= 1e-15:
                break
            avail = cap[c]
            if np.isinf(avail):
                k = int(np.ceil((need - tot) / ben[c]))
            else:
                k = int(min(avail, np.ceil((need - tot) / ben[c])))
            plan.append((int(c), k))
            tot += k * ben[c]
            K += k
            if tot >= need - 1e-12:
                return plan, K
        return plan, np.inf

    def attack(self, i, j, mode, frac=0.5, allowed=None, max_rounds=60, w_start=None):
        """Smallest number of unit moves found (a constructive upper bound on the true minimum)
        that makes theta_j >= theta_i, given theta_i > theta_j at the base fit.
        mode in {'remove','flip','add'}.  allowed: optional boolean mask of source classes.
        Returns dict(K, K_lin, rounds, feasible)."""
        th0 = self.base_fit()
        c = self.contrast(i, j)
        w = self.W0.copy() if w_start is None else w_start.copy()
        th = th0
        K_done, K_lin = 0, None
        for r in range(max_rounds):
            g = c @ th
            if g <= 0:
                return dict(K=K_done, K_lin=K_lin, rounds=r, feasible=True, w=w)
            s, _ = self.class_effects(th, w, c)
            ben, cap, dest = self._benefits(mode, s, w, allowed)
            plan, K_est = self._plan(ben, cap, g)
            if K_lin is None:
                K_lin = K_est
            if not plan:
                return dict(K=np.inf, K_lin=K_lin, rounds=r, feasible=False)
            if not np.isfinite(K_est):
                # linearisation says infeasible; apply whole plan and re-linearise
                m = int(sum(k for _, k in plan))
            else:
                m = 1 if K_est <= 3 else int(max(1, np.floor(frac * K_est)))
            moves, left = [], m
            for cidx, k in plan:
                kk = min(k, left)
                if kk > 0:
                    moves.append((cidx, kk))
                    left -= kk
                if left == 0:
                    break

            def apply(wv, upto):
                wv = wv.copy()
                left = upto
                for cidx, k in moves:
                    kk = min(k, left)
                    if kk <= 0:
                        break
                    if mode in ("remove", "flip"):
                        wv[cidx] -= kk
                    if mode in ("add", "flip"):
                        tgt = cidx if mode == "add" else dest[cidx]
                        wv[tgt] += kk
                    left -= kk
                return wv
            m_eff = int(sum(k for _, k in moves))
            w_new = apply(w, m_eff)
            th_new = self.fit(w_new, th)
            if c @ th_new <= 0:
                lo, hi = 1, m_eff  # smallest prefix achieving the flip
                while lo < hi:
                    mid = (lo + hi) // 2
                    if c @ self.fit(apply(w, mid), th) <= 0:
                        hi = mid
                    else:
                        lo = mid + 1
                return dict(K=K_done + lo, K_lin=K_lin, rounds=r + 1, feasible=True, w=apply(w, lo))
            w, th, K_done = w_new, th_new, K_done + m_eff
            if K_done > 3 * self.n_total:
                break
        return dict(K=np.inf, K_lin=K_lin, rounds=max_rounds, feasible=False)

    def one_shot(self, i, j, mode, allowed=None):
        """K for the *single-linearisation* greedy set (top-K by first-order effect at the base fit),
        refitted exactly (smallest K whose refit flips the pair).  Returns inf if none up to K_max."""
        th0 = self.base_fit()
        c = self.contrast(i, j)
        s, _ = self.class_effects(th0, self.W0, c)
        ben, cap, dest = self._benefits(mode, s, self.W0, allowed)
        order = np.argsort(-ben)
        order = order[ben[order] > 1e-15]
        # expand into unit list lazily via cumulative capacities
        caps = np.where(np.isinf(cap[order]), self.n_total, cap[order]).astype(int)
        cum = np.cumsum(caps)

        def wfor(K):
            wv = self.W0.copy()
            left = K
            for cidx, cp in zip(order, caps):
                kk = min(cp, left)
                if kk <= 0:
                    break
                if mode in ("remove", "flip"):
                    wv[cidx] -= kk
                if mode in ("add", "flip"):
                    wv[cidx if mode == "add" else dest[cidx]] += kk
                left -= kk
            return wv
        Kmax = int(min(cum[-1], self.n_total)) if len(cum) else 0
        if Kmax == 0 or c @ self.fit(wfor(Kmax), th0) > 0:
            return np.inf
        lo, hi = 1, Kmax
        while lo < hi:
            mid = (lo + hi) // 2
            if c @ self.fit(wfor(mid), th0) <= 0:
                hi = mid
            else:
                lo = mid + 1
        return lo


# ---------------------------------------------------------------- construction
def build_board(names, a, b, y, h=None, outcomes=(0.0, 0.5, 1.0), lam=LAM, all_pairs=True):
    """a, b: model indices (arrays); y: outcome for a vs b in {0,.5,1}; h: 1 if a is home, 0 neutral.
    Without home info, comparisons are canonicalised to a<b.  With home info the key is (home,away)
    for home games and (a<b) for neutral games.  Every key gets one class per allowed outcome
    (zero-weight when unobserved) so that flips and adds can move mass between classes."""
    a, b, y = np.asarray(a), np.asarray(b), np.asarray(y, dtype=float)
    m = len(names)
    has_home = h is not None
    h = np.zeros(len(a), dtype=int) if h is None else np.asarray(h, dtype=int)
    sw = (h == 0) & (a > b)
    a2, b2, y2 = np.where(sw, b, a), np.where(sw, a, b), np.where(sw, 1 - y, y)
    key = (a2.astype(np.int64) * m + b2) * 2 + h
    outs = np.array(outcomes)
    yi = np.searchsorted(outs, y2)
    assert np.allclose(outs[yi], y2)
    cnt = {}
    uk, inv = np.unique(key, return_inverse=True)
    counts = np.zeros((len(uk), len(outs)))
    np.add.at(counts, (inv, yi), 1)
    keys = list(uk)
    if all_pairs and not has_home:
        full = set(((i * m + j) * 2) for i in range(m) for j in range(i + 1, m))
        extra = sorted(full - set(keys))
        keys = keys + extra
        counts = np.vstack([counts, np.zeros((len(extra), len(outs)))])
    keys = np.array(keys)
    kh = (keys % 2).astype(int)
    kp = keys // 2
    ka, kb = kp // m, kp % m
    G = len(keys)
    A = np.repeat(ka, len(outs)); B = np.repeat(kb, len(outs)); Hh = np.repeat(kh, len(outs))
    Y = np.tile(outs, G); W = counts.reshape(-1)
    group = np.repeat(np.arange(G), len(outs))
    return Board(names, A, B, Hh, Y, W, group, has_home=has_home, lam=lam)


def with_weights(board, w):
    """shallow copy of a Board with different class weights (bootstrap / subsample replicates)."""
    import copy
    b = copy.copy(board)
    b.W0 = np.asarray(w, dtype=float)
    b.n_total = int(b.W0.sum())
    b.theta0 = None
    return b


def bootstrap_weights(board, rng):
    p = board.W0 / board.W0.sum()
    return rng.multinomial(board.n_total, p).astype(float)


def subsample_weights(board, n, rng):
    """uniform subsample without replacement of n comparisons (multivariate hypergeometric over classes)."""
    return rng.multivariate_hypergeometric(board.W0.astype(np.int64), n).astype(float)
