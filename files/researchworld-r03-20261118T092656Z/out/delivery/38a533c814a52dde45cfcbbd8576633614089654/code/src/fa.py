"""Factor analysis with missing data (EM), held-out likelihood and posterior inference.

Model (standardised units): x = mu + Lam z + eps, z~N(0,I_r), eps~N(0,diag(psi)).
All routines are vectorised over rows with an observation mask (obs: bool M x N).
"""
import numpy as np

PSI_FLOOR = 0.01


def _row_stats(X0, obs, mu, Lam, psi):
    """posterior of z per row. X0: data with NaN->0. returns P (M,r,r), m (M,r)."""
    M, N = X0.shape; r = Lam.shape[1]
    w = obs / psi[None, :]                                      # (M,N)
    Q = np.einsum('ij,jr,js->irs', w, Lam, Lam, optimize=True)  # (M,r,r)
    P = np.linalg.inv(np.eye(r)[None] + Q)
    b = np.einsum('ij,jr->ir', w * np.where(obs, X0 - mu[None, :], 0.0), Lam)
    m = np.einsum('irs,is->ir', P, b)
    return P, m, b


def loglik_rows(X, obs, mu, Lam, psi):
    """marginal log-likelihood of each row under (mu,Lam,psi) with its observed entries."""
    X0 = np.where(obs, X, 0.0)
    r = Lam.shape[1]
    w = obs / psi[None, :]
    Q = np.einsum('ij,jr,js->irs', w, Lam, Lam, optimize=True)
    A = np.eye(r)[None] + Q
    sign, logdetA = np.linalg.slogdet(A)
    P = np.linalg.inv(A)
    d = np.where(obs, X0 - mu[None, :], 0.0)
    b = np.einsum('ij,jr->ir', w * d, Lam)
    quad = (w * d * d).sum(1) - np.einsum('ir,irs,is->i', b, P, b)
    logdet_psi = (obs * np.log(psi)[None, :]).sum(1)
    n = obs.sum(1)
    return -0.5 * (n * np.log(2 * np.pi) + logdet_psi + logdetA + quad)


def fit_fa(X, obs, r, iters=300, tol=1e-5, seed=0, psi_floor=PSI_FLOOR, init=None):
    """EM for FA with missing entries. X standardised (NaN allowed where ~obs)."""
    M, N = X.shape
    X0 = np.where(obs, X, 0.0)
    cnt = obs.sum(0).clip(min=1)
    mu = X0.sum(0) / cnt
    if r == 0:
        var = (np.where(obs, X0 - mu, 0.0) ** 2).sum(0) / cnt
        return dict(mu=mu, Lam=np.zeros((N, 0)), psi=np.maximum(var, psi_floor), ll=np.nan, n_iter=0)
    if init is not None and init['Lam'].shape[1] <= r:
        Lam = np.zeros((N, r)); Lam[:, :init['Lam'].shape[1]] = init['Lam']
        rng = np.random.default_rng(seed)
        Lam[:, init['Lam'].shape[1]:] = 0.01 * rng.standard_normal((N, r - init['Lam'].shape[1]))
        psi = init['psi'].copy(); mu = init['mu'].copy()
    else:
        Xc = np.where(obs, X0 - mu, 0.0)
        U, s, Vt = np.linalg.svd(Xc / np.sqrt(max(M - 1, 1)), full_matrices=False)
        Lam = Vt[:r].T * np.sqrt(np.maximum(s[:r] ** 2 - 0.3, 0.05))[None, :]
        res = (Xc ** 2).sum(0) / cnt - (Lam ** 2).sum(1)
        psi = np.maximum(res, 0.1)
    prev = -np.inf
    for it in range(iters):
        P, m, _ = _row_stats(X0, obs, mu, Lam, psi)
        Ezz = P + np.einsum('ir,is->irs', m, m)                    # (M,r,r)
        # mu update (ECM): mu_j = mean_obs (x - Lam_j m_i)
        pred = m @ Lam.T
        mu = (np.where(obs, X0 - pred, 0.0)).sum(0) / cnt
        D = np.where(obs, X0 - mu[None, :], 0.0)
        A = np.einsum('ij,irs->jrs', obs.astype(float), Ezz, optimize=True)   # (N,r,r)
        bvec = np.einsum('ij,ir->jr', D, m)                         # (N,r)
        A = A + 1e-8 * np.eye(r)[None]
        Lam = np.linalg.solve(A, bvec[:, :, None])[:, :, 0]
        # psi: mean_i obs [ (d - Lam m)^2 + Lam' P Lam ]
        resid = np.where(obs, D - m @ Lam.T, 0.0)
        quadP = np.einsum('jr,irs,js->ij', Lam, P, Lam, optimize=True)
        psi = np.maximum(((resid ** 2 + obs * quadP).sum(0)) / cnt, psi_floor)
        if it % 5 == 4 or it == iters - 1:
            ll = loglik_rows(X, obs, mu, Lam, psi).sum() / obs.sum()
            if abs(ll - prev) < tol:
                break
            prev = ll
    ll = loglik_rows(X, obs, mu, Lam, psi).sum() / obs.sum()
    return dict(mu=mu, Lam=Lam, psi=psi, ll=ll, n_iter=it + 1)


def cv_select_rank(X, obs, ranks, nfold=5, seed=0, iters=200):
    """rank by held-out log-likelihood on history models (whole-row folds). returns best r, table."""
    M = X.shape[0]
    rng = np.random.default_rng(seed)
    perm = rng.permutation(M)
    folds = np.array_split(perm, nfold)
    tab = {r: [] for r in ranks}
    for f in folds:
        tr = np.setdiff1d(np.arange(M), f)
        init = None
        for r in ranks:
            p = fit_fa(X[tr], obs[tr], r, iters=iters, seed=seed, init=init)
            init = p if r > 0 else None
            # held-out rows: likelihood of all their observed entries
            ll = loglik_rows(X[f], obs[f], p['mu'], p['Lam'], p['psi']).sum()
            tab[r].append((ll, obs[f].sum()))
    score = {r: sum(a for a, _ in v) / sum(b for _, b in v) for r, v in tab.items()}
    best = max(score, key=score.get)
    return best, score


# ---------- posterior given a (per-model) observed set ----------
def gain_matrix(Lam, psi, S):
    """E[z|x_S] = G (x_S - mu_S); returns G (r,|S|) and P_S."""
    r = Lam.shape[1]
    LS = Lam[S]; w = 1.0 / psi[S]
    P = np.linalg.inv(np.eye(r) + (LS * w[:, None]).T @ LS)
    G = P @ (LS * w[:, None]).T
    return G, P


def predict_fa(par, S, xS):
    """posterior mean for all N benchmarks. xS: (n,|S|) standardised observed scores."""
    mu, Lam, psi = par['mu'], par['Lam'], par['psi']
    if Lam.shape[1] == 0 or len(S) == 0:
        return np.tile(mu, (xS.shape[0], 1))
    G, P = gain_matrix(Lam, psi, S)
    Z = (xS - mu[S]) @ G.T
    return mu[None, :] + Z @ Lam.T


def predicted_mse(par, S, T):
    """model-based expected squared error per target in T: psi_j + l_j' P_S l_j (vector)."""
    Lam, psi = par['Lam'], par['psi']
    if Lam.shape[1] == 0:
        return psi[T] + 0.0
    P = gain_matrix(Lam, psi, S)[1] if len(S) else np.eye(Lam.shape[1])
    return psi[T] + np.einsum('jr,rs,js->j', Lam[T], P, Lam[T])
