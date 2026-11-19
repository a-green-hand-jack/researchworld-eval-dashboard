"""Predictors: given a fitted history matrix (standardized, NaN = missing), predict all benchmarks of a new
model from its scores on an observed subset S.   API:  p.fit(Z);  p.predict(S, zS) -> vector (N,)  ;  p.cov() -> (N,N)"""
import numpy as np
from .fa import fit_fa, predict_fa, model_cov


def pairwise_corr(Z, min_n=5):
    M, N = Z.shape
    W = (~np.isnan(Z)).astype(float); Z0 = np.where(W > 0, Z, 0.0)
    n = W.T @ W
    mu = (Z0.T @ W) / np.maximum(n, 1)            # mu_ij : mean of z_i over rows where i and j both observed
    sxy = Z0.T @ Z0 / np.maximum(n, 1) - mu * mu.T
    sxx = (Z0 ** 2).T @ W / np.maximum(n, 1) - mu ** 2   # variance of i on rows where i,j co-observed
    d = np.sqrt(np.maximum(sxx * sxx.T, 1e-12))
    C = np.where(n >= min_n, sxy / d, 0.0)
    C = np.clip((C + C.T) / 2, -1, 1); np.fill_diagonal(C, 1.0)
    w, V = np.linalg.eigh(C)
    C = (V * np.maximum(w, 1e-3)) @ V.T          # PSD projection
    dd = np.sqrt(np.diag(C)); return C / np.outer(dd, dd)


class MeanPred:
    name = 'mean'
    def fit(self, Z): self.N = Z.shape[1]; self.mu = np.nanmean(Z, 0); self.C = pairwise_corr(Z); return self
    def predict(self, S, zS): return self.mu.copy()
    def cov(self): return self.C


class AvgShift:
    """z_hat_j = mu_j + beta_j * mean(z_S - mu_S): the 'average of the benchmarks you ran' heuristic,
    with the slope beta_j taken from the pairwise correlation matrix."""
    name = 'avgshift'
    def fit(self, Z): self.mu = np.nanmean(Z, 0); self.C = pairwise_corr(Z); return self
    def predict(self, S, zS):
        S = np.asarray(S); cs = self.C[:, S].mean(1); vs = self.C[np.ix_(S, S)].mean()
        return self.mu + (cs / max(vs, 1e-6)) * np.mean(zS - self.mu[S])
    def cov(self): return self.C


class Gauss:
    """Full-covariance Gaussian conditional with shrinkage toward the identity (correlation scale)."""
    name = 'gauss'
    def __init__(self, shrink=0.1): self.shrink = shrink
    def fit(self, Z):
        self.mu = np.nanmean(Z, 0); C = pairwise_corr(Z)
        self.C = (1 - self.shrink) * C + self.shrink * np.eye(len(C)); return self
    def predict(self, S, zS):
        S = np.asarray(S); K = self.C[np.ix_(S, S)]
        a = np.linalg.solve(K + 1e-6 * np.eye(len(S)), zS - self.mu[S])
        return self.mu + self.C[:, S] @ a
    def cov(self): return self.C


class FA:
    name = 'fa'
    def __init__(self, r=3, seed=0): self.r = r; self.seed = seed
    def fit(self, Z): self.par = fit_fa(Z, self.r, seed=self.seed); return self
    def predict(self, S, zS): return predict_fa(self.par, np.asarray(S), zS)
    def cov(self): return model_cov(self.par)


class ISVD:
    """Iterative-SVD (hard-rank) imputation with ridge fold-in of the new row."""
    name = 'isvd'
    def __init__(self, r=3, ridge=1.0, n_iter=100): self.r = r; self.ridge = ridge; self.n_iter = n_iter
    def fit(self, Z):
        W = ~np.isnan(Z); mu = np.nanmean(Z, 0); X = np.where(W, Z, mu)
        for _ in range(self.n_iter):
            m = X.mean(0); U, s, Vt = np.linalg.svd(X - m, full_matrices=False)
            R = (U[:, :self.r] * s[:self.r]) @ Vt[:self.r] + m
            Xn = np.where(W, Z, R)
            if np.max(np.abs(Xn - X)) < 1e-4: X = Xn; break
            X = Xn
        self.mu = X.mean(0); U, s, Vt = np.linalg.svd(X - self.mu, full_matrices=False)
        self.V = Vt[:self.r].T * (s[:self.r] / np.sqrt(len(X)))      # loadings scaled to unit-variance scores
        self.res = np.nanmean((Z - np.where(W, R, np.nan)) ** 2, 0) if False else None
        return self
    def predict(self, S, zS):
        S = np.asarray(S); VS = self.V[S]
        c = np.linalg.solve(VS.T @ VS + self.ridge * np.eye(VS.shape[1]), VS.T @ (zS - self.mu[S]))
        return self.mu + self.V @ c
    def cov(self): return self.V @ self.V.T + 0.3 * np.eye(len(self.V))


class KNN:
    name = 'knn'
    def __init__(self, K=10): self.K = K
    def fit(self, Z): self.Z = Z; self.mu = np.nanmean(Z, 0); self.C = pairwise_corr(Z); return self
    def predict(self, S, zS):
        S = np.asarray(S); D = self.Z[:, S] - zS[None]
        ok = ~np.isnan(D); n = ok.sum(1)
        d = np.sqrt(np.where(ok, D ** 2, 0).sum(1) / np.maximum(n, 1)); d[n < min(len(S), max(2, len(S) // 2))] = np.inf
        idx = np.argsort(d)[:self.K]; idx = idx[np.isfinite(d[idx])]
        if len(idx) == 0: return self.mu.copy()
        w = 1.0 / (d[idx] + 0.1); V = self.Z[idx]; ok = ~np.isnan(V)
        num = (np.where(ok, V, 0) * w[:, None]).sum(0); den = (ok * w[:, None]).sum(0)
        return np.where(den > 0, num / np.maximum(den, 1e-12), self.mu)
    def cov(self): return self.C


def make(name, **kw):
    return {'mean': MeanPred, 'avgshift': AvgShift, 'gauss': Gauss, 'fa': FA, 'isvd': ISVD, 'knn': KNN, 'hybrid': Hybrid}[name](**kw)


GRIDS = {
    'avgshift': [dict()],
    'gauss': [dict(shrink=s) for s in (0.0, 0.05, 0.15, 0.3, 0.5)],
    'fa': None,   # filled by dataset (rank grid)
    'isvd': [dict(r=r, ridge=e) for r in (1, 2, 3, 5, 8) for e in (0.3, 3.0)],
    'knn': [dict(K=K) for K in (5, 15, 40)],
    'hybrid': [dict(r=r, a=a, shrink=0.05) for r in (2, 4, 8) for a in (0.3, 0.6, 0.9)],
}


def tune(name, Z, grid, seed=0):
    """Pick hyper-parameters by an inner row split of the training matrix (80/20; random half of each validation
    row's observed entries play S, the rest are targets)."""
    rng = np.random.default_rng(seed)
    M = Z.shape[0]; perm = rng.permutation(M); nv = max(5, M // 5)
    va, tr = perm[:nv], perm[nv:]
    Ztr = Z[tr]
    # keep only columns with data in Ztr (all columns kept; NaN columns handled by fit)
    plans = []
    for i in va:
        obs = np.where(~np.isnan(Z[i]))[0]
        if len(obs) < 6: continue
        ns = int(min(10, max(2, len(obs) // 2)))
        S = rng.choice(obs, ns, replace=False); T = np.setdiff1d(obs, S)
        plans.append((i, S, T))
    best = (np.inf, None)
    for kw in grid:
        try:
            p = make(name, **kw).fit(Ztr)
            e = np.mean([np.mean((p.predict(S, Z[i, S])[T] - Z[i, T]) ** 2) for i, S, T in plans])
        except Exception:
            e = np.inf
        if e < best[0]: best = (e, kw)
    return best[1], best[0]


class Hybrid:
    """Gaussian conditional with covariance (1-a) * pairwise correlation + a * FA(r) correlation (low-rank + diag),
    i.e. pairwise estimate shrunk toward a factor-model structure."""
    name = 'hybrid'
    def __init__(self, r=3, a=0.5, shrink=0.05, seed=0): self.r = r; self.a = a; self.shrink = shrink; self.seed = seed
    def fit(self, Z):
        self.mu = np.nanmean(Z, 0)
        self.par = fit_fa(Z, self.r, seed=self.seed, n_iter=150, tol=1e-4)
        S = model_cov(self.par); d = np.sqrt(np.diag(S)); Cf = S / np.outer(d, d)
        C = (1 - self.a) * pairwise_corr(Z) + self.a * Cf
        self.C = (1 - self.shrink) * C + self.shrink * np.eye(len(C)); return self
    def predict(self, S, zS):
        S = np.asarray(S); K = self.C[np.ix_(S, S)]
        a = np.linalg.solve(K + 1e-6 * np.eye(len(S)), zS - self.mu[S])
        return self.mu + self.C[:, S] @ a
    def cov(self): return self.C
