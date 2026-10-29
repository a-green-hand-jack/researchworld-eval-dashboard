"""Bradley-Terry fitting and worst-case perturbation search.

Model: P(a beats b) = sigmoid(theta_a - theta_b + gamma * h), h = optional per-comparison
covariate (home advantage for NBA).  Outcome y in {0, 0.5, 1} (ties = half win), fractional
cross-entropy loss, tiny ridge `LAM` for identifiability.  Fitting is exact Newton (O(N) bincount
Hessian); the perturbation search returns *verified* upper bounds on the minimum number of votes
that must be changed (each reported k comes with an explicit modified data set whose refit
flips the target pair).
"""
import os
os.environ.setdefault("OMP_NUM_THREADS", "1")
os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
import numpy as np
from scipy.special import expit

LAM = 1e-3  # ridge; negligible relative to N >= 1e3 votes, makes the Hessian PD


class Data:
    """Comparison data set.  a,b: int indices of the two parties; y in {0,.5,1} for a; extra: (n,q)"""

    def __init__(self, a, b, y, names, extra=None):
        self.a = np.asarray(a, np.int64)
        self.b = np.asarray(b, np.int64)
        self.y = np.asarray(y, float)
        self.names = list(names)
        self.M = len(names)
        self.E = None if extra is None else np.asarray(extra, float).reshape(len(a), -1)
        self.q = 0 if self.E is None else self.E.shape[1]
        self.P = self.M + self.q
        self.N = len(a)

    def subset(self, idx):
        return Data(self.a[idx], self.b[idx], self.y[idx], self.names, None if self.E is None else self.E[idx])


def _lin(M, a, b, E, th):
    z = th[a] - th[b]
    if E is not None:
        z = z + E @ th[M:]
    return z


def objective(M, a, b, E, y, w, th, lam=LAM):
    z = _lin(M, a, b, E, th)
    ll = np.logaddexp(0, z) - y * z
    return float(w @ ll + 0.5 * lam * th @ th)


def _grad(M, a, b, E, r):
    g = np.bincount(a, r, M) - np.bincount(b, r, M)
    if E is not None:
        g = np.concatenate([g, E.T @ r])
    return g


def hess(M, a, b, E, s, lam=LAM):
    P = M + (0 if E is None else E.shape[1])
    H = np.zeros((P, P))
    d = np.bincount(a, s, M) + np.bincount(b, s, M)
    B = np.bincount(a * M + b, s, M * M).reshape(M, M)
    H[:M, :M] = np.diag(d) - B - B.T
    if E is not None:
        for c in range(E.shape[1]):
            col = np.bincount(a, s * E[:, c], M) - np.bincount(b, s * E[:, c], M)
            H[:M, M + c] = col
            H[M + c, :M] = col
        H[M:, M:] = E.T @ (s[:, None] * E)
    return H + lam * np.eye(P)


def fit(M, a, b, E, y, w, th0=None, lam=LAM, tol=1e-7, maxit=60):
    P = M + (0 if E is None else E.shape[1])
    th = np.zeros(P) if th0 is None else th0.copy()
    f = objective(M, a, b, E, y, w, th, lam)
    for _ in range(maxit):
        p = expit(_lin(M, a, b, E, th))
        g = _grad(M, a, b, E, w * (p - y)) + lam * th
        if np.max(np.abs(g)) < tol:
            break
        H = hess(M, a, b, E, w * p * (1 - p), lam)
        step = np.linalg.solve(H, g)
        if np.max(np.abs(step)) < 1e-9:
            break
        t = 1.0
        while True:
            thn = th - t * step
            fn = objective(M, a, b, E, y, w, thn, lam)
            if fn <= f + 1e-10 * max(1.0, abs(f)) or t < 1e-6:
                break
            t *= 0.5
        th, f = thn, fn
    return th


def fit_data(D, w=None, y=None, th0=None):
    w = np.ones(D.N) if w is None else w
    y = D.y if y is None else y
    return fit(D.M, D.a, D.b, D.E, y, w, th0)


def se_gap_sandwich(D, th, i, j):
    """Sandwich (robust) standard error of theta_i - theta_j: v' (sum r_n^2 x_n x_n') v, v = H^-1 d."""
    p = expit(_lin(D.M, D.a, D.b, D.E, th))
    H = hess(D.M, D.a, D.b, D.E, p * (1 - p))
    d = np.zeros(D.P)
    d[i], d[j] = 1, -1
    v = np.linalg.solve(H, d)
    xv = _xv(D.M, D.a, D.b, D.E, v)
    r = D.y - p
    return float(np.sqrt(np.sum((r * xv) ** 2)))


def _xv(M, a, b, E, v):
    x = v[a] - v[b]
    if E is not None:
        x = x + E @ v[M:]
    return x


# ---------------------------------------------------------------------------------------
# worst-case perturbation search
# ---------------------------------------------------------------------------------------
class State:
    """Mutable perturbed data set (drop: weights, flip: labels, add: appended rows)."""

    def __init__(self, D):
        self.M, self.a, self.b, self.E = D.M, D.a, D.b, D.E
        self.y = D.y.copy()
        self.w = np.ones(D.N)
        self.flipped = np.zeros(D.N, bool)

    def copy(self):
        s = State.__new__(State)
        s.M, s.a, s.b, s.E = self.M, self.a, self.b, self.E
        s.y, s.w, s.flipped = self.y.copy(), self.w.copy(), self.flipped.copy()
        return s

    def fit(self, th0):
        return fit(self.M, self.a, self.b, self.E, self.y, self.w, th0)

    def hess(self, th):
        p = expit(_lin(self.M, self.a, self.b, self.E, th))
        return hess(self.M, self.a, self.b, self.E, self.w * p * (1 - p)), p


def _scores(mode, st, th, v, p):
    """first-order reduction of gap = th_i - th_j per perturbed vote."""
    xv = _xv(st.M, st.a, st.b, st.E, v)
    if mode == "drop":
        s = xv * (st.y - p)
        s[st.w < 1] = -np.inf
        return s
    if mode == "flip":
        s = -xv * (1 - 2 * st.y)
        s[st.flipped | (st.y == 0.5)] = -np.inf
        return s
    raise ValueError(mode)


def _apply(mode, st, idx):
    if mode == "drop":
        st.w[idx] = 0.0
    else:
        st.y[idx] = 1 - st.y[idx]
        st.flipped[idx] = True


def _klin_from(s, gap):
    s = np.sort(s[s > 0])[::-1]
    cs = np.cumsum(s)
    idx = np.searchsorted(cs, gap)
    return float(idx + 1) if idx < len(s) else np.inf


def min_perturbation(D, th_hat, i, j, mode, max_frac=0.5, step_frac=0.5, max_iter=80):
    """Smallest found number of perturbed votes making theta_i <= theta_j (i currently above j).

    Returns dict(k=verified upper bound (inf if not reached within budget), k_lin=first-order
    estimate at the original fit).  mode in {drop, flip, add}.
    """
    d = np.zeros(D.P)
    d[i], d[j] = 1.0, -1.0
    th = th_hat.copy()
    gap0 = th[i] - th[j]
    assert gap0 > 0
    if mode == "add":
        return _search_add(D, th_hat, i, j, max_frac, step_frac, max_iter)
    st = State(D)
    H, p = st.hess(th)
    v = np.linalg.solve(H, d)
    k_lin = _klin_from(_scores(mode, st, th, v, p), gap0)
    used, budget = 0, max_frac * D.N
    for _ in range(max_iter):
        gap = th[i] - th[j]
        if gap <= 0:
            break
        H, p = st.hess(th)
        v = np.linalg.solve(H, d)
        s = _scores(mode, st, th, v, p)
        order = np.argsort(-s)
        order = order[s[order] > 0]
        if len(order) == 0:
            return dict(k=np.inf, k_lin=k_lin)
        cs = np.cumsum(s[order])
        idx = np.searchsorted(cs, gap)
        kl = idx + 1 if idx < len(order) else len(order)
        b = min(max(1, int(np.ceil(step_frac * kl))), len(order))
        if used + b > budget:
            b = int(budget - used)
            if b <= 0:
                return dict(k=np.inf, k_lin=k_lin)
        prev, th_prev = st.copy(), th
        _apply(mode, st, order[:b])
        th = st.fit(th)
        if th[i] - th[j] <= 0:
            lo, hi = 0, b  # lo: not flipped, hi: flipped (bisection inside last batch)
            while hi - lo > 1:
                mid = (lo + hi) // 2
                s2 = prev.copy()
                _apply(mode, s2, order[:mid])
                t2 = s2.fit(th_prev)
                if t2[i] - t2[j] <= 0:
                    hi = mid
                else:
                    lo = mid
            return dict(k=used + hi, k_lin=k_lin)
        used += b
        if used >= budget:
            break
    return dict(k=np.inf, k_lin=k_lin)


def _pair_scores_add(M, th, v):
    # injecting "a beats b" changes gap by (v_a - v_b)(1-p_ab); we want it negative
    va, thm = v[:M], th[:M]
    S = -(va[:, None] - va[None, :]) * (1 - expit(thm[:, None] - thm[None, :]))
    np.fill_diagonal(S, -np.inf)
    return S


def _search_add(D, th_hat, i, j, max_frac, step_frac, max_iter):
    """Inject k new votes (each: a beats b, pair chosen adversarially among all ordered pairs of
    parties; covariate = 0).  Batch-greedy with refit, then bisection inside the last batch."""
    M = D.M
    d = np.zeros(D.P)
    d[i], d[j] = 1.0, -1.0
    a, b, E, y = D.a, D.b, D.E, D.y
    w = np.ones(D.N)
    th = th_hat.copy()
    used, budget, k_lin = 0, max_frac * D.N, None

    def make(m, aa, bb):
        E2 = None if E is None else np.vstack([E, np.zeros((m, E.shape[1]))])
        return (np.concatenate([a, np.full(m, aa)]), np.concatenate([b, np.full(m, bb)]), E2,
                np.concatenate([y, np.ones(m)]), np.concatenate([w, np.ones(m)]))

    for _ in range(max_iter):
        gap = th[i] - th[j]
        if gap <= 0:
            break
        p = expit(_lin(M, a, b, E, th))
        H = hess(M, a, b, E, w * p * (1 - p))
        v = np.linalg.solve(H, d)
        S = _pair_scores_add(M, th, v)
        aa, bb = np.unravel_index(np.argmax(S), S.shape)
        sc = S[aa, bb]
        if sc <= 0:
            return dict(k=np.inf, k_lin=k_lin if k_lin is not None else np.inf)
        kl = max(1, int(np.ceil(gap / sc)))
        if k_lin is None:
            k_lin = float(kl)
        bsz = max(1, int(np.ceil(step_frac * kl)))
        if used + bsz > budget:
            bsz = int(budget - used)
            if bsz <= 0:
                return dict(k=np.inf, k_lin=k_lin)
        a2, b2, E2, y2, w2 = make(bsz, aa, bb)
        thn = fit(M, a2, b2, E2, y2, w2, th)
        if thn[i] - thn[j] <= 0:
            lo, hi = 0, bsz
            while hi - lo > 1:
                mid = (lo + hi) // 2
                a3, b3, E3, y3, w3 = make(mid, aa, bb)
                t3 = fit(M, a3, b3, E3, y3, w3, th)
                if t3[i] - t3[j] <= 0:
                    hi = mid
                else:
                    lo = mid
            return dict(k=used + hi, k_lin=k_lin)
        a, b, E, y, w, th = a2, b2, E2, y2, w2, thn
        used += bsz
        if used >= budget:
            break
    return dict(k=np.inf, k_lin=k_lin if k_lin is not None else np.inf)
