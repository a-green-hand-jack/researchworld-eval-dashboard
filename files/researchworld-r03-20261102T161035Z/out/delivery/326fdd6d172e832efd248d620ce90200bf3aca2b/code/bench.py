"""Core library: dense-core extraction, factor-model (Gaussian) completion, benchmark selection, inference."""
import numpy as np, pandas as pd

# ---------------------------------------------------------------- data
def dense_core(X, density=0.9, min_models=0):
    """Alternately drop the least-covered row/column until observed fraction >= density."""
    X = X.copy()
    while True:
        obs = X.notna().values
        if obs.mean() >= density: break
        rc, cc = obs.mean(1), obs.mean(0)
        if rc.min() < cc.min() or X.shape[1] <= 10:
            X = X.drop(index=X.index[rc.argmin()])
        else:
            X = X.drop(columns=X.columns[cc.argmin()])
    return X

# ---------------------------------------------------------------- factor model (probabilistic FA with missing data, EM)
class FA:
    """x = mu + L z + e, z~N(0,I_r), e~N(0,diag(psi)) on standardized columns; EM with missing entries."""
    def __init__(self, r=3, iters=100, seed=0, psi_min=1e-2):
        self.r, self.iters, self.seed, self.psi_min = r, iters, seed, psi_min
    def fit(self, X):                      # X: (M,N) ndarray with NaN
        M, N = X.shape; r = self.r
        self.mu = np.nanmean(X, 0); self.sd = np.nanstd(X, 0) + 1e-9
        Z = (X - self.mu) / self.sd; O = ~np.isnan(Z); Z0 = np.where(O, Z, 0.0)
        rng = np.random.default_rng(self.seed)
        # init from SVD of mean-filled matrix
        U, s, Vt = np.linalg.svd(Z0, full_matrices=False)
        L = (Vt[:r].T * (s[:r] / np.sqrt(M))) + 0.01 * rng.standard_normal((N, r))
        psi = np.full(N, 0.3)
        keys = {}
        for i in range(M): keys.setdefault(O[i].tobytes(), []).append(i)
        pats = [(np.array(v), O[v[0]]) for v in keys.values() if O[v[0]].any()]
        for _ in range(self.iters):
            Ez = np.zeros((M, r)); Ezz = np.zeros((M, r, r))
            for rows, o in pats:
                Lo = L[o]; P = np.linalg.inv(np.eye(r) + (Lo.T / psi[o]) @ Lo)
                E = Z0[np.ix_(rows, np.where(o)[0])] @ (Lo / psi[o][:, None]) @ P.T
                Ez[rows] = E; Ezz[rows] = P + E[:, :, None] * E[:, None, :]
            Lnew = np.zeros_like(L); psinew = np.zeros(N)
            for j in range(N):
                oj = O[:, j]
                A = Ezz[oj].sum(0) + 1e-6 * np.eye(r); b = (Ez[oj] * Z0[oj, j][:, None]).sum(0)
                Lnew[j] = np.linalg.solve(A, b)
                psinew[j] = (Z0[oj, j] ** 2 - 2 * Lnew[j] @ b + Lnew[j] @ Ezz[oj].sum(0) @ Lnew[j]).sum() / max(oj.sum(), 1)
            L, psi = Lnew, np.maximum(psinew, self.psi_min)
        self.L, self.psi = L, psi
        return self
    def posterior(self, xs, S):            # xs: raw scores on index set S (ndarray). returns mean and cov of z
        z = (xs - self.mu[S]) / self.sd[S]; Ls = self.L[S]
        P = np.linalg.inv(np.eye(self.r) + (Ls.T / self.psi[S]) @ Ls)
        return P @ (Ls.T / self.psi[S]) @ z, P
    def predict(self, xs, S):              # raw-scale predictions for all N
        m, _ = self.posterior(xs, S)
        return self.mu + self.sd * (self.L @ m)
    def impute(self, X):                   # fill NaNs by conditional mean
        X = X.copy()
        for i in range(X.shape[0]):
            o = ~np.isnan(X[i])
            if o.sum() == 0: X[i] = self.mu; continue
            p = self.predict(X[i, o], np.where(o)[0]); X[i, ~o] = p[~o]
        return X

def fa_cv_rank(X, ranks=(1, 2, 3, 4, 6, 8), psis=(0.05, 0.15, 0.3), seed=0, frac=0.1, iters=40):
    """choose (rank, noise floor) by held-out-cell RMSE (standardized) on the training matrix only"""
    rng = np.random.default_rng(seed); O = ~np.isnan(X)
    mask = O & (rng.random(X.shape) < frac); Xt = np.where(mask, np.nan, X)
    best = None
    for r in ranks:
        for pm in psis:
            fa = FA(r, iters=iters, seed=seed, psi_min=pm).fit(Xt)
            e = np.sqrt(np.mean(((fa.impute(Xt) - X)[mask] / fa.sd[np.where(mask)[1]]) ** 2))
            if best is None or e < best[0]: best = (e, r, pm)
    return best[1], best[2]

# ---------------------------------------------------------------- selection: each returns an ordering (list of column indices)
def sel_random(Xtr, rng, **kw): return list(rng.permutation(Xtr.shape[1]))
def sel_coverage(Xtr, rng, **kw): return list(np.argsort(-(~np.isnan(Xtr)).mean(0), kind="stable"))
def sel_variance(Xtr, rng, **kw): return list(np.argsort(-np.nanstd(Xtr, 0), kind="stable"))
def sel_corr_mean(Xtr, rng, fa=None, Ximp=None, **kw):
    Z = (Ximp - Ximp.mean(0)) / (Ximp.std(0) + 1e-9); m = Z.mean(1)
    c = [abs(np.corrcoef(Z[:, j], m)[0, 1]) for j in range(Z.shape[1])]
    return list(np.argsort(-np.array(c), kind="stable"))
def sel_greedy_bayes(Xtr, rng, fa=None, kmax=None, cand=None, **kw):
    """Greedy Bayesian A-optimal design in the latent space: minimise tr(L^T L P) (reducible posterior variance of all benchmarks)."""
    N = Xtr.shape[1]; r = fa.r; kmax = kmax or N; Lm = fa.L; W = Lm.T @ Lm
    prec = np.eye(r); chosen = []; rest = set(range(N) if cand is None else cand)
    for _ in range(min(kmax, len(rest))):
        best = None
        for j in rest:
            p2 = prec + np.outer(Lm[j], Lm[j]) / fa.psi[j]
            v = np.trace(W @ np.linalg.inv(p2))
            if best is None or v < best[0]: best = (v, j)
        chosen.append(best[1]); rest.discard(best[1]); prec = prec + np.outer(Lm[best[1]], Lm[best[1]]) / fa.psi[best[1]]
    return chosen + list(rest)
def sel_greedy_ridge(Xtr, rng, Ximp=None, kmax=None, cand=None, pen=1e-3, **kw):
    """Greedy forward selection minimising in-sample least-squares reconstruction error of all benchmarks (imputed training matrix)."""
    Z = (Ximp - Ximp.mean(0)) / (Ximp.std(0) + 1e-9); N = Z.shape[1]; kmax = kmax or N
    chosen = []; rest = list(range(N) if cand is None else cand)
    for _ in range(min(kmax, len(rest))):
        best = None
        for j in rest:
            S = chosen + [j]; A = Z[:, S]
            B = np.linalg.solve(A.T @ A + pen * len(Z) * np.eye(len(S)), A.T @ Z)
            v = ((Z - A @ B) ** 2).sum()
            if best is None or v < best[0]: best = (v, j)
        chosen.append(best[1]); rest.remove(best[1])
    return chosen + rest
def sel_qr(Xtr, rng, Ximp=None, **kw):
    """Column-pivoted QR (CUR-style) on standardized imputed matrix."""
    from scipy.linalg import qr
    Z = (Ximp - Ximp.mean(0)) / (Ximp.std(0) + 1e-9)
    return list(qr(Z, pivoting=True, mode="economic")[2])
def sel_kmedoids(Xtr, rng, Ximp=None, kmax=None, **kw):
    """Order by farthest-first traversal in 1-|corr| distance, started at the most central benchmark (cluster representatives)."""
    Z = (Ximp - Ximp.mean(0)) / (Ximp.std(0) + 1e-9); D = 1 - np.abs(np.corrcoef(Z.T))
    first = int(np.argmin(D.sum(0))); order = [first]; dmin = D[first].copy()
    while len(order) < D.shape[0]:
        dmin[order] = -1; j = int(np.argmax(dmin)); order.append(j); dmin = np.minimum(dmin, D[j])
    return order
def sel_backelim(Xtr, rng, Ximp=None, cand=None, reg=1e-2, **kw):
    """MMTEB-style backward elimination: repeatedly drop the candidate benchmark best linearly predicted (R^2 from the inverse correlation
    matrix, ridge-regularised) by the remaining candidates, on the imputed training matrix; the selection of size k is the k survivors
    (the reverse elimination order is nested)."""
    Z = (Ximp - Ximp.mean(0)) / (Ximp.std(0) + 1e-9); cand = list(range(Z.shape[1]) if cand is None else cand)
    C = np.corrcoef(Z[:, cand].T) + reg * np.eye(len(cand)); P = np.linalg.inv(C); alive = list(range(len(cand))); drop = []
    while len(alive) > 1:
        r2 = 1 - 1 / (np.diag(P) * np.diag(C)[alive]); i = int(np.argmax(r2)); drop.append(alive.pop(i))
        P = _shrink(P, i)
    drop.append(alive[0]); return [cand[i] for i in reversed(drop)]
def _shrink(P, i):
    """inverse of the matrix with row/column i removed, from the inverse P of the full matrix"""
    q = np.delete(P[:, i], i); R = np.delete(np.delete(P, i, 0), i, 1)
    return R - np.outer(q, q) / P[i, i]
SELECTORS_EXTRA = dict(backelim=sel_backelim)
SELECTORS_PEN = {f'greedy_ridge_pen{p}': (lambda Xtr, rng, p=p, **kw: sel_greedy_ridge(Xtr, rng, pen=p, **kw)) for p in (1e-4, 1e-2, 1e-1)}
SELECTORS = dict(random=sel_random, coverage=sel_coverage, variance=sel_variance, corr_mean=sel_corr_mean,
                 qr=sel_qr, farthest=sel_kmedoids, greedy_ridge=sel_greedy_ridge, greedy_bayes=sel_greedy_bayes)

# ---------------------------------------------------------------- inference given observed scores xs on columns S
def inf_mean(ctx, xs, S): return ctx["colmean"].copy()
def inf_rank1(ctx, xs, S):
    """one 'general ability' score: mean z over the observed benchmarks; per-benchmark univariate regression of z_j on the same
    statistic computed on the imputed training matrix."""
    Zi = ctx["Zimp"]; g = Zi[:, S].mean(1); g0 = g - g.mean()
    slope = (Zi - Zi.mean(0)).T @ g0 / (g0 @ g0 + 1e-9)
    z = ((xs - ctx["colmean"][S]) / ctx["colsd"][S]).mean() - g.mean()
    return ctx["colmean"] + ctx["colsd"] * (Zi.mean(0) + slope * z)
def inf_fa(ctx, xs, S): return ctx["fa"].predict(xs, S)
def inf_ridge(ctx, xs, S):
    Zi, mu, sd = ctx["Zimp"], ctx["colmean"], ctx["colsd"]
    from sklearn.linear_model import RidgeCV
    key = tuple(S)
    if key not in ctx["ridge_cache"]:
        ctx["ridge_cache"][key] = RidgeCV(alphas=np.logspace(-2, 3, 12)).fit(Zi[:, S], Zi)
    return mu + sd * ctx["ridge_cache"][key].predict(((xs - mu[S]) / sd[S])[None])[0]
def inf_knn(ctx, xs, S, K=10):
    Zi, mu, sd = ctx["Zimp"], ctx["colmean"], ctx["colsd"]
    d = ((Zi[:, S] - ((xs - mu[S]) / sd[S])) ** 2).sum(1); nn = np.argsort(d)[:K]
    w = 1 / (d[nn] + 1e-3); return mu + sd * (Zi[nn] * w[:, None]).sum(0) / w.sum()
INFERENCE = dict(mean=inf_mean, rank1=inf_rank1, ridge=inf_ridge, knn=inf_knn, fa=inf_fa)

def make_ctx(Xtr, fa):
    colmean, colsd = np.nanmean(Xtr, 0), np.nanstd(Xtr, 0) + 1e-9
    Ximp = fa.impute(Xtr); Zimp = (Ximp - colmean) / colsd
    return dict(colmean=colmean, colsd=colsd, Zimp=Zimp, fa=fa, ridge_cache={})
