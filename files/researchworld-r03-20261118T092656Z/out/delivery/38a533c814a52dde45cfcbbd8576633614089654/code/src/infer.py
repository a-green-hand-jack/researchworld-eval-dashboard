"""Inference methods: predict all benchmarks of a new model from its k observed scores.
Every method is built from a `Ctx` (history-only quantities) and exposes predict(S, xS) -> (N,) or
predict_common(S, XS) -> (n,N) for one common S.  Standardised units throughout (history mean 0, sd 1)."""
import numpy as np
from fa import fit_fa, cv_select_rank, predict_fa, loglik_rows


class Ctx:
    """History-only context: standardisation, FA fit, completed history, correlations."""
    def __init__(self, Xraw, obs, ranks=(0, 1, 2, 3, 4, 6, 8, 12), r=None, seed=0, transform=None, psi_floor=0.01, rank_nfold=5):
        self.obs = obs
        X = Xraw.copy()
        if transform is not None:
            X = transform(X)
        cnt = obs.sum(0).clip(min=1)
        X0 = np.where(obs, X, 0.0)
        self.m = X0.sum(0) / cnt
        v = (np.where(obs, X0 - self.m, 0.0) ** 2).sum(0) / np.maximum(cnt - 1, 1)
        self.sd = np.sqrt(np.maximum(v, 1e-8))
        self.Xs = np.where(obs, (X - self.m) / self.sd, np.nan)
        self.M, self.N = X.shape
        self.seed = seed
        if r is None:
            r, self.rank_scores = cv_select_rank(self.Xs, obs, list(ranks), nfold=rank_nfold, seed=seed)
        else:
            self.rank_scores = None
        self.r = r
        self.par = fit_fa(self.Xs, obs, r, seed=seed, psi_floor=psi_floor)
        self.coverage = obs.mean(0)
        # completed history (observed entries kept, missing -> FA posterior mean)
        if obs.all():
            self.Xc = self.Xs.copy()
        else:
            Xc = np.zeros_like(self.Xs)
            for i in range(self.M):
                S = np.where(obs[i])[0]
                Xc[i] = predict_fa(self.par, S, self.Xs[i, S][None, :])[0]
                Xc[i, S] = self.Xs[i, S]
            self.Xc = Xc


def predict_many(meth, S, XS):
    if hasattr(meth, 'predict_common'):
        return meth.predict_common(S, XS)
    return np.stack([meth.predict(S, x) for x in XS])


class MeanPred:
    name = 'mean'
    def __init__(self, ctx): self.N = ctx.N
    def predict(self, S, xS): return np.zeros(self.N)
    def predict_common(self, S, XS): return np.zeros((len(XS), self.N))


class FAPred:
    name = 'fa'
    def __init__(self, ctx, par=None):
        self.par = par if par is not None else ctx.par
    def predict(self, S, xS):
        return predict_fa(self.par, np.asarray(S), xS[None, :])[0]
    def predict_common(self, S, XS):
        return predict_fa(self.par, np.asarray(S), XS)


class MeanZPred:
    """one-factor: average of observed standardised scores, then per-target simple regression on history."""
    name = 'meanz'
    def __init__(self, ctx): self.ctx = ctx
    def predict(self, S, xS): return self.predict_common(S, xS[None, :])[0]
    def predict_common(self, S, XS):
        S = np.asarray(S); X = self.ctx.Xc
        s = X[:, S].mean(1); sc = s - s.mean()
        b = (sc @ X) / max(sc @ sc, 1e-9); a = X.mean(0) - b * s.mean()
        return a[None, :] + XS.mean(1)[:, None] * b[None, :]


class RidgePred:
    name = 'ridge'
    def __init__(self, ctx, lam=1.0): self.ctx, self.lam = ctx, lam
    def predict(self, S, xS): return self.predict_common(S, xS[None, :])[0]
    def predict_common(self, S, XS):
        S = np.asarray(S); X = self.ctx.Xc; A = X[:, S]
        am = A.mean(0); ym = X.mean(0)
        Ac = A - am
        B = np.linalg.solve(Ac.T @ Ac + self.lam * len(A) / 10 * np.eye(len(S)), Ac.T @ (X - ym))
        return ym[None, :] + (XS - am) @ B


class KnnPred:
    name = 'knn'
    def __init__(self, ctx, K=10): self.ctx, self.K = ctx, K
    def predict(self, S, xS): return self.predict_common(S, xS[None, :])[0]
    def predict_common(self, S, XS):
        S = np.asarray(S); X = self.ctx.Xc; A = X[:, S]
        D = ((XS[:, None, :] - A[None, :, :]) ** 2).sum(2)           # (n, M)
        K = min(self.K, A.shape[0])
        idx = np.argpartition(D, K - 1, axis=1)[:, :K]
        return X[idx].mean(1)


class SoftImpute:
    """soft-impute (ALS, Hastie et al. 2015 form) fitted on history; new row by ridge fold-in."""
    name = 'softimpute'
    def __init__(self, ctx, lam=1.0, rank=20, iters=60):
        self.ctx = ctx; self.lam = lam
        X = np.where(ctx.obs, ctx.Xs, 0.0); obs = ctx.obs.astype(float)
        M, N = X.shape; R = min(rank, M - 1, N)
        rng = np.random.default_rng(0)
        V = rng.standard_normal((N, R)) * 0.1; U = np.zeros((M, R))
        I = np.eye(R)
        dense = bool(ctx.obs.all())
        for _ in range(iters):
            if dense:
                U = X @ V @ np.linalg.inv(V.T @ V + lam * I)
                V = X.T @ U @ np.linalg.inv(U.T @ U + lam * I)
                continue
            Q = np.einsum('ij,jr,js->irs', obs, V, V, optimize=True) + lam * I[None]
            U = np.linalg.solve(Q, np.einsum('ij,jr->ir', X * obs, V)[:, :, None])[:, :, 0]
            Q = np.einsum('ij,ir,is->jrs', obs, U, U, optimize=True) + lam * I[None]
            V = np.linalg.solve(Q, np.einsum('ij,ir->jr', X * obs, U)[:, :, None])[:, :, 0]
        self.V = V; self.R = R
    def predict(self, S, xS): return self.predict_common(S, xS[None, :])[0]
    def predict_common(self, S, XS):
        S = np.asarray(S); V = self.V
        U = np.linalg.solve(V[S].T @ V[S] + self.lam * np.eye(self.R), V[S].T @ XS.T)   # (R,n)
        return (V @ U).T


class TreePred:
    """nonlinear imputer: multi-output ExtraTrees from S to all targets (completed history)."""
    name = 'extratrees'
    def __init__(self, ctx, n_estimators=100, min_samples_leaf=2):
        self.ctx = ctx; self.ne = n_estimators; self.msl = min_samples_leaf
    def predict(self, S, xS):
        from sklearn.ensemble import ExtraTreesRegressor
        S = np.asarray(S)
        f = ExtraTreesRegressor(self.ne, min_samples_leaf=self.msl, n_jobs=1, random_state=0, max_features=0.7)
        f.fit(self.ctx.Xc[:, S], self.ctx.Xc)
        return f.predict(xS[None, :])[0]


def precision_floor_predict(ctx, lam, rows_x, rows_obs):
    """model-agnostic-ish floor: predict each benchmark from ALL other observed benchmarks of the same model
    via ridge-shrunk Gaussian conditional (history covariance + lam I). rows_x: (n,N) standardised w/ NaN."""
    Xc = ctx.Xc
    C = np.cov(Xc.T) + lam * np.eye(ctx.N)
    out = np.full(rows_x.shape, np.nan)
    for i in range(rows_x.shape[0]):
        O = np.where(rows_obs[i])[0]
        CO = C[np.ix_(O, O)]
        Th = np.linalg.inv(CO)
        d = np.diag(Th)
        x = rows_x[i, O]
        out[i, O] = x - (Th @ x) / d          # LOO-benchmark conditional mean
    return out


class GaussPred:
    """rank-free Gaussian conditioning with a shrunk full covariance of the completed history:
    Sigma_a = (1-a) R + a I (R = correlation matrix of the standardised completed history)."""
    name = 'gcov'
    def __init__(self, ctx, alpha=0.2):
        R = np.corrcoef(ctx.Xc.T)
        R = np.nan_to_num(R); np.fill_diagonal(R, 1.0)
        self.Sigma = (1 - alpha) * R + alpha * np.eye(ctx.N); self.alpha = alpha
    def predict(self, S, xS): return self.predict_common(S, xS[None, :])[0]
    def predict_common(self, S, XS):
        S = np.asarray(S); Sg = self.Sigma
        W = np.linalg.solve(Sg[np.ix_(S, S)], Sg[S, :])              # (k,N)
        return XS @ W
    def cond_var(self, S):
        Sg = self.Sigma; S = np.asarray(S)
        W = np.linalg.solve(Sg[np.ix_(S, S)], Sg[S, :])
        return np.diag(Sg) - np.einsum('kj,kj->j', Sg[S, :], W)
