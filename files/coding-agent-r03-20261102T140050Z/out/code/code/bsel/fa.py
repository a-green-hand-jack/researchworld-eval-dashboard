"""Factor analysis with missing data (EM), and Gaussian-conditional fold-in for a new row.

Model (on standardized scores z, one row per model, one column per benchmark):
    z_i = mu + Lam f_i + eps_i,   f_i ~ N(0, I_r),  eps_ij ~ N(0, psi_j)
"""
import numpy as np

def fit_fa(Z, r, n_iter=300, tol=1e-5, ridge=0.05, psi_min=0.02, seed=0, verbose=False):
    """Z: (M,N) with NaN for missing. Returns dict(mu, L, psi)."""
    M, N = Z.shape
    W = (~np.isnan(Z)).astype(float)
    Z0 = np.where(W > 0, Z, 0.0)
    nj = np.maximum(W.sum(0), 1.0)
    mu = Z0.sum(0) / nj
    rng = np.random.default_rng(seed)
    # init from SVD of mean-filled, centred matrix
    Zf = np.where(W > 0, Z0 - mu, 0.0)
    U, s, Vt = np.linalg.svd(Zf, full_matrices=False)
    r = min(r, len(s))
    L = (Vt[:r].T * (s[:r] / np.sqrt(max(M - 1, 1)))) * 0.8 + 0.01 * rng.standard_normal((N, r))
    psi = np.maximum(((Zf ** 2).sum(0) / nj) - (L ** 2).sum(1), 0.3)
    I = np.eye(r)
    Rg = ridge * np.eye(r + 1); Rg[-1, -1] = 0.0
    prev = None
    for it in range(n_iter):
        # E-step
        Q = np.einsum('jk,jl->jkl', L, L) / psi[:, None, None]          # (N,r,r)
        A = I[None] + np.einsum('ij,jkl->ikl', W, Q)                     # (M,r,r)
        b = ((W * (Z0 - mu)) / psi) @ L                                  # (M,r)
        P = np.linalg.inv(A)
        m = np.einsum('ikl,il->ik', P, b)
        # M-step
        Euu = np.zeros((M, r + 1, r + 1))
        Euu[:, :r, :r] = P + m[:, :, None] * m[:, None, :]
        Euu[:, :r, r] = m; Euu[:, r, :r] = m; Euu[:, r, r] = 1.0
        Suu = (W.T @ Euu.reshape(M, -1)).reshape(N, r + 1, r + 1)        # (N,r+1,r+1)
        u = np.concatenate([m, np.ones((M, 1))], 1)                      # (M,r+1)
        Sxu = (W * Z0).T @ u                                             # (N,r+1)
        th = np.linalg.solve(Suu + Rg[None], Sxu[:, :, None])[:, :, 0]
        L, mu = th[:, :r], th[:, r]
        res = Z0 - mu - m @ L.T
        vq = np.einsum('jk,ikl,jl->ij', L, P, L)
        psi = np.maximum(((W * (res ** 2 + vq)).sum(0)) / nj, psi_min)
        cur = np.concatenate([psi, (L @ L.T)[np.triu_indices(N, 0)] if N <= 60 else (L ** 2).sum(1)])
        if prev is not None and np.max(np.abs(cur - prev)) < tol:
            break
        prev = cur
    return dict(mu=mu, L=L, psi=psi, n_iter=it + 1)

def fold_in(par, S, zS):
    """Posterior mean/cov of latent f given observed benchmarks S (index array) with standardized values zS."""
    L, psi, mu = par['L'], par['psi'], par['mu']
    LS = L[S]
    A = np.eye(L.shape[1]) + (LS / psi[S, None]).T @ LS
    b = (LS / psi[S, None]).T @ (zS - mu[S])
    P = np.linalg.inv(A)
    return P @ b, P

def predict_fa(par, S, zS):
    m, P = fold_in(par, S, zS)
    return par['mu'] + par['L'] @ m

def model_cov(par):
    return par['L'] @ par['L'].T + np.diag(par['psi'])

def expected_mse(par, S, C=None):
    """Model-implied expected squared error (standardized units) for benchmarks in C\\S given S observed."""
    L, psi = par['L'], par['psi']
    N = L.shape[0]
    C = np.arange(N) if C is None else np.asarray(C)
    T = np.setdiff1d(C, S)
    if len(S) == 0:
        return float(np.mean(psi[T] + (L[T] ** 2).sum(1)))
    _, P = fold_in(par, np.asarray(S), np.zeros(len(S)))
    return float(np.mean(psi[T] + np.einsum('jk,kl,jl->j', L[T], P, L[T])))
