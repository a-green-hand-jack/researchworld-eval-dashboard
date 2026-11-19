"""Core library: factor-model fit with missing data, benchmark selectors, inference rules.

Conventions
  Y  : (M models x N benchmarks) raw scores, NaN = not evaluated.
  Z  : per-benchmark standardised scores (train mean / std), NaN kept.
  All selectors return an *ordering* of benchmark indices (a nested sequence of subsets);
  the subset for budget k is the first k entries that the new model actually has scores for.
"""
import numpy as np

EPS_STD = 1e-6


# ----------------------------------------------------------------------------- preprocessing
def standardise(Y, min_obs=8):
    mu = np.nanmean(Y, 0)
    sd = np.nanstd(Y, 0)
    n = np.sum(~np.isnan(Y), 0)
    ok = (n >= min_obs) & (sd > EPS_STD)
    sd = np.where(ok, sd, 1.0)
    mu = np.where(np.isnan(mu), 0.0, mu)
    return (Y - mu) / sd, mu, sd, ok


# ----------------------------------------------------------------------------- factor analysis (EM, missing data)
class FA:
    """z_ij = mu_j + w_j . f_i + eps_ij,  f_i ~ N(0, I_r),  eps_ij ~ N(0, psi_j); fitted by EM on observed cells."""

    def __init__(self, r, n_iter=150, tol=1e-5, psi_floor=1e-2, ridge=1e-3, seed=0):
        self.r, self.n_iter, self.tol, self.psi_floor, self.ridge, self.seed = r, n_iter, tol, psi_floor, ridge, seed

    def fit(self, Z):
        M, N = Z.shape
        r = self.r
        mask = ~np.isnan(Z)
        X = np.where(mask, Z, 0.0)
        mu = np.where(mask.sum(0) > 0, X.sum(0) / np.maximum(mask.sum(0), 1), 0.0)
        # init by SVD of mean-imputed matrix
        U, s, Vt = np.linalg.svd(np.where(mask, Z - mu, 0.0), full_matrices=False)
        W = (Vt[:r].T * (s[:r] / np.sqrt(max(M - 1, 1)))) if r > 0 else np.zeros((N, 0))
        W = W[:, :r]
        psi = np.full(N, 0.3)
        mf = mask.astype(float)
        nobs = mf.sum(0)
        prev = None
        for it in range(self.n_iter):
            # E-step
            WW = np.einsum('ja,jb->jab', W, W)                       # N r r
            A = np.eye(r)[None] + np.einsum('ij,jab->iab', mf / psi, WW)   # M r r
            b = ((X - mu * mf) / psi) @ W                            # M r
            Sig = np.linalg.inv(A)
            m = np.einsum('iab,ib->ia', Sig, b)
            # M-step on augmented regressor [f; 1]
            Ez = np.zeros((M, r + 1, r + 1))
            Ez[:, :r, :r] = Sig + np.einsum('ia,ib->iab', m, m)
            Ez[:, :r, r] = m
            Ez[:, r, :r] = m
            Ez[:, r, r] = 1.0
            Sj = np.einsum('ij,iab->jab', mf, Ez) + self.ridge * np.eye(r + 1)[None]
            mt = np.concatenate([m, np.ones((M, 1))], 1)
            rhs = (X * mf).T @ mt                                    # N (r+1)
            theta = np.linalg.solve(Sj, rhs[:, :, None])[:, :, 0]
            W, mu = theta[:, :r], theta[:, r]
            ssq = (X * mf * X).sum(0)
            quad = ssq - 2 * (theta * rhs).sum(1) + np.einsum('ja,jab,jb->j', theta, Sj - self.ridge * np.eye(r + 1)[None], theta)
            psi = np.maximum(quad / np.maximum(nobs, 1), self.psi_floor)
            cur = psi.mean()
            if prev is not None and abs(prev - cur) < self.tol * prev:
                break
            prev = cur
        self.W, self.mu, self.psi = W, mu, psi
        self.n_iter_ = it + 1
        return self

    # posterior mean of factors of rows given observed entries (rows may have different masks)
    def latent(self, Z):
        mf = (~np.isnan(Z)).astype(float)
        X = np.where(mf > 0, Z, 0.0)
        r = self.r
        WW = np.einsum('ja,jb->jab', self.W, self.W)
        A = np.eye(r)[None] + np.einsum('ij,jab->iab', mf / self.psi, WW)
        b = ((X - self.mu * mf) / self.psi) @ self.W
        return np.linalg.solve(A, b[:, :, None])[:, :, 0]

    def complete(self, Z):
        F = self.latent(Z)
        R = self.mu + F @ self.W.T
        return np.where(np.isnan(Z), R, Z)

    def predict_from(self, zS, S):
        """posterior-mean prediction of all benchmarks for rows with observed z on columns S. zS: (n, k)."""
        WS = self.W[S]
        A = np.eye(self.r) + (WS / self.psi[S, None]).T @ WS
        b = ((zS - self.mu[S]) / self.psi[S]) @ WS
        F = np.linalg.solve(A, b.T).T
        return self.mu + F @ self.W.T

    def cov(self):
        return self.W @ self.W.T + np.diag(self.psi)


def holdout_rank(Z, ranks, frac=0.1, seed=0, n_iter=100):
    """choose the factor rank by held-out MSE on a random 10% of the observed train cells."""
    rng = np.random.default_rng(seed)
    obs = np.argwhere(~np.isnan(Z))
    h = obs[rng.random(len(obs)) < frac]
    Zt = Z.copy()
    Zt[h[:, 0], h[:, 1]] = np.nan
    best, bestr = np.inf, ranks[0]
    errs = {}
    for r in ranks:
        fa = FA(r, n_iter=n_iter, seed=seed).fit(Zt)
        pred = fa.complete(Zt)
        e = np.mean((pred[h[:, 0], h[:, 1]] - Z[h[:, 0], h[:, 1]]) ** 2)
        errs[r] = e
        if e < best:
            best, bestr = e, r
    return bestr, errs


# ----------------------------------------------------------------------------- selectors (orderings)
def greedy_cond_var(C, kmax, ridge=1e-3, cand=None, cost=None):
    """Greedy forward selection minimising the total conditional variance of all benchmarks given the chosen set
    under Gaussian covariance C (pivoted Cholesky with trace-reduction pivoting).  Nested."""
    N = C.shape[0]
    R = C.copy() + ridge * np.eye(N)   # residual covariance
    order = []
    for _ in range(min(kmax, N if cand is None else int(cand.sum()))):
        gain = (R ** 2).sum(0) / np.maximum(np.diag(R), 1e-12)
        if cost is not None:      # variance reduction per unit evaluation cost
            gain = gain / cost
        gain[order] = -np.inf
        if cand is not None:
            gain[~cand] = -np.inf
        j = int(np.argmax(gain))
        order.append(j)
        R = R - np.outer(R[:, j], R[j, :]) / R[j, j]
    return order


def greedy_dopt(W, psi, kmax, cand=None):
    """greedy maximisation of logdet(I + sum_S w w'/psi): information about the latent factors."""
    N, r = W.shape
    A = np.eye(r)
    order = []
    Ainv = np.eye(r)
    for _ in range(min(kmax, N if cand is None else int(cand.sum()))):
        v = W / np.sqrt(psi)[:, None]
        gain = np.einsum('ja,ab,jb->j', v, Ainv, v)   # logdet gain = log(1+v' A^-1 v), monotone in this
        gain[order] = -np.inf
        if cand is not None:
            gain[~cand] = -np.inf
        j = int(np.argmax(gain))
        order.append(j)
        vj = v[j]
        Ainv = Ainv - np.outer(Ainv @ vj, vj @ Ainv) / (1 + vj @ Ainv @ vj)
    return order


def leverage_order(Zc, r):
    _, _, Vt = np.linalg.svd(Zc - Zc.mean(0), full_matrices=False)
    lev = (Vt[:r] ** 2).sum(0)
    return list(np.argsort(-lev))


def qr_pivot_order(Zc, r):
    from scipy.linalg import qr
    _, _, Vt = np.linalg.svd(Zc - Zc.mean(0), full_matrices=False)
    _, _, piv = qr(Vt[:r], pivoting=True, mode='economic')
    rest = [j for j in range(Zc.shape[1]) if j not in set(piv[:r])]
    # beyond r pivots, continue by residual-trace greedy on remaining
    return list(piv) + rest


def central_order(Zc):
    """most 'representative' first: highest mean absolute correlation with the others (no redundancy control)."""
    C = np.corrcoef(Zc, rowvar=False)
    np.fill_diagonal(C, 0)
    return list(np.argsort(-np.abs(C).mean(0)))


def kcenter_order(Zc, seed=0):
    """farthest-point (k-center) ordering on distance 1-|corr| starting from the most central benchmark."""
    C = np.corrcoef(Zc, rowvar=False)
    D = 1 - np.abs(C)
    start = int(np.argmax(np.abs(C).mean(0)))
    order = [start]
    dmin = D[start].copy()
    for _ in range(Zc.shape[1] - 1):
        dmin[order] = -1
        j = int(np.argmax(dmin))
        order.append(j)
        dmin = np.minimum(dmin, D[j])
    return order


def exhaustive_order(Zc, k, kmax_comb=2000, seed=0):
    """best k-subset by training-set GCV error of ridge on completed train data (exhaustive for small N, else random-restart swap)."""
    import itertools
    N = Zc.shape[1]
    def score(S):
        B, b0 = ridge_gcv_fit(Zc[:, list(S)], Zc)
        res = Zc - (Zc[:, list(S)] @ B + b0)
        T = [j for j in range(N) if j not in S]
        return (res[:, T] ** 2).mean()
    subs = list(itertools.combinations(range(N), k))
    best = min(subs, key=score)
    return list(best) + [j for j in range(N) if j not in best]


def popular_order(Y_raw):
    return list(np.argsort(-np.sum(~np.isnan(Y_raw), 0), kind='stable'))


def rawvar_order(Y_raw):
    sd = np.nanstd(Y_raw, 0)
    return list(np.argsort(-sd, kind='stable'))


def emp_cov(Zc, shrink=0.05):
    C = np.cov(Zc, rowvar=False)
    d = np.diag(np.diag(C))
    return (1 - shrink) * C + shrink * d


# ----------------------------------------------------------------------------- inference rules
def ridge_gcv_fit(ZcS, ZcT, lams=(1e-3, 1e-2, 1e-1, 1, 10, 100)):
    """ridge regression of all targets on the S columns with GCV-chosen lambda (shared across targets). returns coef, intercept."""
    xm, ym = ZcS.mean(0), ZcT.mean(0)
    X, Yc = ZcS - xm, ZcT - ym
    U, s, Vt = np.linalg.svd(X, full_matrices=False)
    UtY = U.T @ Yc
    n = X.shape[0]
    best, bl = np.inf, lams[0]
    for l in lams:
        f = s ** 2 / (s ** 2 + l)
        res = Yc - U @ (f[:, None] * UtY)
        gcv = (res ** 2).sum() / (n - f.sum()) ** 2 * n
        if gcv < best:
            best, bl = gcv, l
    B = Vt.T @ ((s / (s ** 2 + bl))[:, None] * UtY)
    return B, ym - xm @ B


class Predictor:
    """Wraps a fitted training state; predict(method, S, zS) -> (n, N) predictions in z-space."""

    def __init__(self, Ztr, fa):
        self.fa = fa
        self.Zc = fa.complete(Ztr)
        self.N = Ztr.shape[1]
        self._cache = {}

    def predict(self, method, S, zS):
        S = list(S)
        k = len(S)
        n = zS.shape[0]
        N = self.N
        if method == 'mean':
            return np.zeros((n, N))
        if method == 'fa':
            return self.fa.predict_from(zS, S)
        if method == 'ridge':
            key = ('ridge', tuple(S))
            if key not in self._cache:
                self._cache[key] = ridge_gcv_fit(self.Zc[:, S], self.Zc)
            B, b0 = self._cache[key]
            return zS @ B + b0
        if method == 'avgreg':        # single aggregate score = mean of selected z; per-target linear map
            s_tr = self.Zc[:, S].mean(1)
            sc = zS.mean(1)
            vm = s_tr.mean()
            beta = ((s_tr - vm)[:, None] * (self.Zc - self.Zc.mean(0))).sum(0) / ((s_tr - vm) ** 2).sum()
            return self.Zc.mean(0) + (sc - vm)[:, None] * beta[None]
        if method == 'pcals':
            key = ('pcals', tuple(S))
            if key not in self._cache:
                r = min(self.fa.r, k)
                mu = self.Zc.mean(0)
                _, _, Vt = np.linalg.svd(self.Zc - mu, full_matrices=False)
                V = Vt[:r].T
                VS = V[S]
                G = np.linalg.solve(VS.T @ VS + 1e-3 * np.eye(r), VS.T)    # r x k
                self._cache[key] = (mu, V, G)
            mu, V, G = self._cache[key]
            return mu + ((zS - mu[S]) @ G.T) @ V.T
        if method == 'krr':          # linear ridge + RBF kernel ridge on the residuals (nonlinear, smooth)
            key = ('krr', tuple(S))
            if key not in self._cache:
                B, b0 = ridge_gcv_fit(self.Zc[:, S], self.Zc)
                rng = np.random.default_rng(0)
                idx = np.arange(self.Zc.shape[0])
                if len(idx) > 500:
                    idx = rng.choice(idx, 500, replace=False)
                X = self.Zc[idx][:, S]
                R = self.Zc[idx] - (X @ B + b0)
                d2 = ((X[:, None, :] - X[None, :, :]) ** 2).sum(2)
                h2 = np.median(d2[d2 > 0]) if (d2 > 0).any() else 1.0
                K = np.exp(-d2 / h2)
                ev, U = np.linalg.eigh(K)
                ev = np.maximum(ev, 0)
                UtR = U.T @ R
                best, bl = np.inf, 1.0
                n = len(idx)
                for l in (1e-2, 1e-1, 1, 10):
                    f = ev / (ev + l)
                    res = R - U @ (f[:, None] * UtR)
                    gcv = (res ** 2).sum() / (n - f.sum()) ** 2 * n
                    if gcv < best:
                        best, bl = gcv, l
                alpha = U @ (UtR / (ev + bl)[:, None])
                self._cache[key] = (B, b0, X, h2, alpha)
            B, b0, X, h2, alpha = self._cache[key]
            d2 = ((zS[:, None, :] - X[None, :, :]) ** 2).sum(2)
            return zS @ B + b0 + np.exp(-d2 / h2) @ alpha
        if method == 'knn':
            K = min(10, self.Zc.shape[0])
            d = ((zS[:, None, :] - self.Zc[None, :, S]) ** 2).sum(2)
            idx = np.argsort(d, 1)[:, :K]
            return self.Zc[idx].mean(1)
        raise ValueError(method)


METHODS = ['mean', 'fa', 'ridge', 'avgreg', 'pcals', 'knn', 'krr']


# ----------------------------------------------------------------------------- model families (for cluster bootstrap / leave-family-out)
def family_labels(org, adapted_from, names):
    """Strict model family: organisations are merged when a model is declared as adapted from (fine-tuned / distilled from) another
    model that is itself in the matrix (adapted_from = name of that base model); connected components of the resulting organisation
    graph.  Bases outside the matrix (generic backbones) do not link anything.  Unlabelled / placeholder organisations ('NA',
    'Removed', '') stay singletons."""
    org = [str(o) for o in org]
    for i, o in enumerate(org):
        if o in ('NA', 'Removed', '', 'nan'):
            org[i] = f'single_{i}'
    of = dict(zip(names, org))
    par = {}

    def find(x):
        par.setdefault(x, x)
        while par[x] != x:
            par[x] = par[par[x]]
            x = par[x]
        return x

    for o in org:
        find(o)
    for o, a in zip(org, adapted_from):
        if isinstance(a, str) and a in of:
            par[find(o)] = find(of[a])
    return np.array([find(o) for o in org])
