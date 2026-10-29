"""Bradley-Terry fitting on aggregated cell counts, first-order influence, and exact-refit
verified perturbation search ("attacks").

Model: P(a beats b) = sigmoid(theta_a - theta_b + eta*h); ties/soft labels y in {0,.5,1} enter the
logistic likelihood as soft targets (a tie = half a win for each side).  Ridge LAM on theta only.
Everything depends on the data only through counts N[c, l] of label l in cell c=(a,b,h).
"""
import numpy as np

LAM = 1e-3


def sigmoid(x):
    return 0.5 * (1.0 + np.tanh(0.5 * x))


class Problem:
    def __init__(self, d, lam=LAM):
        self.items = d["items"]; p = self.p = len(self.items)
        a, b, h, y = d["a"], d["b"], d["h"], d["y"]
        self.labels = np.array(sorted(set(np.round(y * 2).astype(int)))) / 2.0
        L = self.L = len(self.labels)
        li = np.searchsorted(self.labels, y)
        key = (a * p + b) * 2 + h
        uniq, inv = np.unique(key, return_inverse=True)
        self.C = len(uniq)
        self.ca = (uniq // 2) // p; self.cb = (uniq // 2) % p; self.ch = uniq % 2
        self.N0 = np.zeros((self.C, L)); np.add.at(self.N0, (inv, li), 1.0)
        self.has_h = bool(h.any())
        self.P = p + int(self.has_h)
        X = np.zeros((self.C, self.P))
        X[np.arange(self.C), self.ca] = 1.0; X[np.arange(self.C), self.cb] = -1.0
        if self.has_h: X[:, p] = self.ch
        self.X = X
        self.lamv = np.full(self.P, lam)
        if self.has_h: self.lamv[p] = 0.0
        self.Ntot = self.N0.sum()

    # ---------------------------------------------------------------- fitting
    def _loss(self, theta, w, s):
        d = self.X @ theta
        # sum_l n_l[-y log s(d) - (1-y) log s(-d)] = w*softplus(-d)*... use stable form
        sp = np.logaddexp(0, d)  # -log s(-d)
        return float(np.sum(w * sp - s * d) + 0.5 * np.sum(self.lamv * theta ** 2))

    def fit(self, N=None, theta0=None, tol=1e-9, maxit=60):
        N = self.N0 if N is None else N
        w = N.sum(1); s = N @ self.labels
        th = np.zeros(self.P) if theta0 is None else theta0.copy()
        f = self._loss(th, w, s)
        for _ in range(maxit):
            sg = sigmoid(self.X @ th)
            g = self.X.T @ (w * sg - s) + self.lamv * th
            H = self.X.T @ (self.X * (w * sg * (1 - sg))[:, None]) + np.diag(self.lamv + 1e-12)
            step = np.linalg.solve(H, g)
            t = 1.0
            while True:
                th2 = th - t * step; f2 = self._loss(th2, w, s)
                if f2 <= f + 1e-12 or t < 1e-6: break
                t *= 0.5
            th, f = th2, f2
            if np.max(np.abs(t * step)) < tol: break
        return th

    def hessian(self, th, N=None):
        N = self.N0 if N is None else N
        w = N.sum(1); sg = sigmoid(self.X @ th)
        return self.X.T @ (self.X * (w * sg * (1 - sg))[:, None]) + np.diag(self.lamv + 1e-12)

    def contrast(self, i, j):
        u = np.zeros(self.P); u[i] = 1.0; u[j] = -1.0
        return u

    def gap_se(self, th, i, j, N=None):
        u = self.contrast(i, j)
        return float(np.sqrt(u @ np.linalg.solve(self.hessian(th, N), u)))

    def n_involving(self, i, j):
        m = (self.ca == i) | (self.cb == i) | (self.ca == j) | (self.cb == j)
        return float(self.N0[m].sum())

    # ------------------------------------------------------------ perturbations
    def _candidates(self, N, th, u, kinds, cell_mask=None):
        """Per-unit first-order gain (decrease of u.theta) of every elementary edit.
        Returns arrays kind, c, l, l2, gain, cap."""
        H = self.hessian(th, N)
        z = np.linalg.solve(H, u)
        xz = self.X @ z
        sg = sigmoid(self.X @ th)
        y = self.labels
        out = []
        C, L = self.C, self.L
        cc = np.repeat(np.arange(C), L); ll = np.tile(np.arange(L), C)
        for kind in kinds:
            if kind == "drop":
                gain = (y[ll] - sg[cc]) * xz[cc]; cap = N[cc, ll]
                out.append((np.zeros(C * L, int), cc, ll, -np.ones(C * L, int), gain, cap))
            elif kind == "relabel":
                for l2 in range(L):
                    gain = -(y[l2] - y[ll]) * xz[cc]; cap = N[cc, ll].copy()
                    cap[ll == l2] = 0
                    out.append((np.ones(C * L, int), cc, ll, np.full(C * L, l2), gain, cap))
            elif kind == "inject_t":
                # target-only rigging: decisive votes *for the lower-ranked item j*, only in battles involving j
                j = int(np.argmin(u))
                favors = ((self.ca[cc] == j) & (y[ll] == 1)) | ((self.cb[cc] == j) & (y[ll] == 0))
                gain = (sg[cc] - y[ll]) * xz[cc]
                cap = np.where(favors, np.inf, 0.0)
                out.append((np.full(C * L, 2), cc, ll, -np.ones(C * L, int), gain, cap))
            elif kind == "inject":
                # attacker may only add decisive votes (y in {0,1}) in observed cells
                gain = (sg[cc] - y[ll]) * xz[cc]
                cap = np.where((y[ll] == 0) | (y[ll] == 1), np.inf, 0.0)
                out.append((np.full(C * L, 2), cc, ll, -np.ones(C * L, int), gain, cap))
        k, c, l, l2, g, cap = [np.concatenate(v) for v in zip(*out)]
        ok = (g > 1e-12) & (cap > 0)
        if cell_mask is not None: ok &= cell_mask[c]
        k, c, l, l2, g, cap = k[ok], c[ok], l[ok], l2[ok], g[ok], cap[ok]
        o = np.argsort(-g, kind="stable")
        return k[o], c[o], l[o], l2[o], g[o], cap[o]

    @staticmethod
    def _apply(N, chunks):
        N = N.copy()
        for kind, c, l, l2, m in chunks:
            if kind == 0: N[c, l] -= m
            elif kind == 1: N[c, l] -= m; N[c, l2] += m
            else: N[c, l] += m
        return N

    @staticmethod
    def _prefix(chunks, k):
        out, used = [], 0
        for ch in chunks:
            if used + ch[4] <= k: out.append(ch); used += ch[4]
            else:
                if k - used > 0: out.append(ch[:4] + (k - used,))
                break
        return out

    def attack(self, i, j, kinds=("drop",), mode="greedy", alpha=0.5, max_frac=0.3,
               cell_mask=None, th_full=None, max_rounds=400):
        """Search a small set of edits (all of the kinds in `kinds`) after which the exact refit has
        theta_i < theta_j.  Requires theta_i > theta_j at the full-data fit.
        Returns (k, info): k = number of edits in a verified flipping set (upper bound on the
        minimal flip budget), or None if none found within max_frac*N edits."""
        th0 = self.fit() if th_full is None else th_full
        u = self.contrast(i, j)
        if u @ th0 <= 1e-9: return 0, dict(tied=True)   # already (numerically) tied at the full-data fit
        cap_total = max_frac * self.Ntot
        chunks, total = [], 0
        N = self.N0.copy(); th = th0
        rounds = 0
        if mode == "oneshot":
            k_, c_, l_, l2_, g_, cap_ = self._candidates(N, th, u, kinds, cell_mask)
            for t in range(len(g_)):
                m = min(cap_[t], cap_total - total)
                if m <= 0: break
                chunks.append((int(k_[t]), int(c_[t]), int(l_[t]), int(l2_[t]), int(m))); total += int(m)
                if total >= cap_total: break
        else:
            while rounds < max_rounds:
                rounds += 1
                gap = u @ th
                if gap < 0: break
                k_, c_, l_, l2_, g_, cap_ = self._candidates(N, th, u, kinds, cell_mask)
                if len(g_) == 0: break
                need = alpha * gap; acc = 0.0; new = []
                for t in range(len(g_)):
                    m = min(cap_[t], max(1.0, np.ceil((need - acc) / g_[t])))
                    new.append((int(k_[t]), int(c_[t]), int(l_[t]), int(l2_[t]), int(m)))
                    acc += m * g_[t]
                    if acc >= need: break
                if total + sum(x[4] for x in new) > cap_total: 
                    new = self._prefix(new, int(cap_total - total))
                    if not new: break
                chunks += new; total += sum(x[4] for x in new)
                N = self._apply(self.N0, chunks); th = self.fit(N, th)
                if total >= cap_total and u @ th >= 0: break
        if not chunks: return None, {}
        # verify & shrink with binary search over the prefix length
        def flips(k):
            Nk = self._apply(self.N0, self._prefix(chunks, k))
            thk = self.fit(Nk, th0)
            return (u @ thk) < 0
        K = sum(c[4] for c in chunks)
        if not flips(K): return None, dict(rounds=rounds, K=K)
        lo, hi = 0, K
        while hi - lo > 1:
            mid = (lo + hi) // 2
            if flips(mid): hi = mid
            else: lo = mid
        return hi, dict(rounds=rounds, K=K)

    # ------------------------------------------------------------------ noise
    def resample_counts(self, rng):
        p = self.N0.ravel() / self.Ntot
        return rng.multinomial(int(self.Ntot), p).reshape(self.N0.shape).astype(float)

    def drop_random(self, k, rng):
        n = self.N0.ravel().astype(np.int64)
        kept = rng.multivariate_hypergeometric(n, int(self.Ntot) - int(k))
        return kept.reshape(self.N0.shape).astype(float)

    def relabel_random(self, k, rng):
        """Reassign k randomly chosen comparisons a uniformly random *different* label."""
        n = self.N0.ravel().astype(np.int64)
        pick = rng.multivariate_hypergeometric(n, int(k)).reshape(self.N0.shape)
        N = self.N0 - pick
        for c in range(self.C):
            for l in range(self.L):
                m = pick[c, l]
                if m:
                    others = [x for x in range(self.L) if x != l]
                    cnt = rng.multinomial(m, np.ones(len(others)) / len(others))
                    for x, v in zip(others, cnt): N[c, x] += v
        return N


def ranks_from_theta(th, p):
    order = np.argsort(-th[:p], kind="stable")
    r = np.empty(p, int); r[order] = np.arange(p)
    return r


def kendall(x, y):
    """Kendall tau-a style on score vectors (ties count 0)."""
    sx = np.sign(x[:, None] - x[None, :]); sy = np.sign(y[:, None] - y[None, :])
    n = len(x)
    return float((sx * sy).sum() / (n * (n - 1)))
