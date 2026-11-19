"""Core library: benchmark-subset selection and score inference.

Everything works on a z-scored (per-benchmark, training rows only) model x benchmark matrix Z with NaN=missing.

Latent factor model (FA):  z_i = V u_i + eps_i,  u_i ~ N(0, I_r),  eps_ij ~ N(0, psi_j)
  - fa_em       : EM for (V, psi) with missing data (vectorised)
  - posterior   : Bayes posterior of u given observed subset S
  - predict_fa  : posterior-mean prediction of all benchmarks

Selection methods (all return a *nested or per-k* ordered list of benchmark indices among candidate set C):
  random, greedy_iopt (proposed: Bayesian I-optimal design), top_load, piv_qr, kmeans_cover, cov_greedy
Predictors: mean, fa(r), fa1, ppca (isotropic noise), gauss_cov (shrunk full covariance), knn
"""
import numpy as np

EPS = 1e-9


# ----------------------------------------------------------------------------- standardisation
def fit_std(Y):
    mu = np.nanmean(Y, axis=0)
    sd = np.nanstd(Y, axis=0)
    sd = np.where(sd < 1e-6, 1.0, sd)
    return mu, sd


# ----------------------------------------------------------------------------- factor analysis EM
def fa_em(Z, r, iters=80, iso=False, lam=1e-2, psi_floor=0.02, seed=0):
    """EM for factor analysis with missing data. Z: M x N (NaN missing, columns ~ z-scored)."""
    M, N = Z.shape
    O = ~np.isnan(Z)
    Of = O.astype(float)
    Z0 = np.where(O, Z, 0.0)
    rng = np.random.default_rng(seed)
    U, s, Vt = np.linalg.svd(Z0, full_matrices=False)
    V = Vt[:r].T * (s[:r] / np.sqrt(M))[None, :]
    V = V + 1e-3 * rng.standard_normal(V.shape)
    psi = np.full(N, 0.5)
    n_j = Of.sum(0)
    Ir = np.eye(r)
    for _ in range(iters):
        w = Of / psi[None, :]                                    # M x N
        P = Ir[None] + np.einsum('ij,jk,jl->ikl', w, V, V)       # M x r x r
        rhs = (w * Z0) @ V                                       # M x r
        Sig = np.linalg.inv(P)
        Eu = np.einsum('ikl,il->ik', Sig, rhs)
        Euu = Sig + np.einsum('ik,il->ikl', Eu, Eu)
        A = np.einsum('ij,ikl->jkl', Of, Euu) + lam * Ir[None]   # N x r x r
        b = np.einsum('ij,ij,ik->jk', Of, Z0, Eu)                # N x r
        V = np.linalg.solve(A, b[..., None])[..., 0]
        # residuals
        t1 = (Of * Z0 ** 2).sum(0)
        t2 = 2 * (b * V).sum(1)
        t3 = np.einsum('jk,jkl,jl->j', V, A - lam * Ir[None], V)
        res = np.maximum(t1 - t2 + t3, 0) / np.maximum(n_j, 1)
        if iso:
            psi = np.full(N, max(res @ n_j / n_j.sum(), psi_floor))
        else:
            psi = np.maximum(res, psi_floor)
    return V, psi


def posterior(V, psi, S, zS, prior_prec=None):
    r = V.shape[1]
    VS = V[S]
    w = 1.0 / psi[S]
    P = np.eye(r) + (VS * w[:, None]).T @ VS
    m = np.linalg.solve(P, VS.T @ (w * zS))
    return m, P


def predict_fa(V, psi, S, zS):
    m, _ = posterior(V, psi, S, zS)
    return V @ m


# ----------------------------------------------------------------------------- empirical covariance
def pairwise_corr(Z, min_overlap=15):
    O = (~np.isnan(Z)).astype(float)
    Z0 = np.where(np.isnan(Z), 0.0, Z)
    n = O.T @ O
    num = Z0.T @ Z0
    s1 = Z0.T @ O                     # sum of z_i over rows where both observed (i-th col)
    # use pairwise means/vars to compute Pearson properly
    sx = s1                           # sx[i,j] = sum_{rows both} z_i
    sy = s1.T
    sxx = (Z0 ** 2).T @ O
    syy = sxx.T
    nn = np.maximum(n, 1)
    cov = num / nn - (sx / nn) * (sy / nn)
    vx = sxx / nn - (sx / nn) ** 2
    vy = syy / nn - (sy / nn) ** 2
    R = cov / np.sqrt(np.maximum(vx * vy, 1e-9))
    R = np.where(n >= min_overlap, np.clip(R, -1, 1), 0.0)
    np.fill_diagonal(R, 1.0)
    R = (R + R.T) / 2
    w, Q = np.linalg.eigh(R)
    w = np.maximum(w, 1e-3)
    R = (Q * w) @ Q.T
    d = np.sqrt(np.diag(R))
    return R / d[:, None] / d[None, :]


def shrink_cov(R, alpha):
    return (1 - alpha) * R + alpha * np.eye(R.shape[0])


# ----------------------------------------------------------------------------- selection methods
def sel_random(C, kmax, rng):
    return list(rng.permutation(C)[:kmax])


def sel_greedy_iopt(C, kmax, V, psi, G=None):
    """Greedy Bayesian I-optimal design: minimise tr(G Sigma_post) with Sigma_post=(I+V_S' Psi^-1 V_S)^-1,
    G=V'V (so that the objective is the posterior variance of the *signal* summed over all benchmarks)."""
    C = np.asarray(C)
    r = V.shape[1]
    if G is None:
        G = V.T @ V
    Sg = np.eye(r)
    chosen = []
    avail = np.ones(len(C), bool)
    VC = V[C]
    for _ in range(min(kmax, len(C))):
        B = VC @ Sg
        num = np.einsum('ij,jk,ik->i', B, G, B)
        den = psi[C] + np.einsum('ij,ij->i', B, VC)
        gain = np.where(avail, num / den, -np.inf)
        c = int(np.argmax(gain))
        chosen.append(int(C[c]))
        avail[c] = False
        b = B[c]
        Sg = Sg - np.outer(b, b) / den[c]
    return chosen


def sel_top_load(C, kmax, V, psi):
    C = np.asarray(C)
    h = (V[C] ** 2).sum(1)
    score = h / (h + psi[C])          # communality: reliability w.r.t. common factors
    return [int(c) for c in C[np.argsort(-score)][:kmax]]


def sel_piv_qr(C, kmax, V, psi):
    """Column-pivoted QR / Gram-Schmidt on noise-whitened loadings (CUR/leverage-type deterministic selection).
    Once the span is exhausted (k>r) fall back to communality ordering."""
    C = np.asarray(C)
    X = V[C] / np.sqrt(psi[C])[:, None]
    R = X.copy()
    chosen = []
    avail = np.ones(len(C), bool)
    r = V.shape[1]
    for t in range(min(kmax, len(C))):
        if t >= r:
            break
        nr = np.where(avail, (R ** 2).sum(1), -1)
        c = int(np.argmax(nr))
        chosen.append(c); avail[c] = False
        q = R[c] / (np.linalg.norm(R[c]) + EPS)
        R = R - np.outer(R @ q, q)
    out = [int(C[c]) for c in chosen]
    if len(out) < kmax:
        rest = [c for c in sel_top_load(C, len(C), V, psi) if c not in set(out)]
        out += rest[: kmax - len(out)]
    return out


def sel_kmeans_cover(C, k, V, psi, seed=0):
    """Cluster benchmarks in loading space into k clusters, take the medoid-like member of each (not nested)."""
    from sklearn.cluster import KMeans
    C = np.asarray(C)
    k = min(k, len(C))
    X = V[C] / np.sqrt(psi[C] + (V[C] ** 2).sum(1))[:, None]    # approx. unit-variance loadings
    if k == 1:
        d = ((X - X.mean(0)) ** 2).sum(1)
        return [int(C[np.argmin(d)])]
    km = KMeans(n_clusters=k, n_init=3, random_state=seed).fit(X)
    out = []
    for c in range(k):
        idx = np.where(km.labels_ == c)[0]
        if len(idx) == 0:
            continue
        d = ((X[idx] - km.cluster_centers_[c]) ** 2).sum(1)
        out.append(int(C[idx[np.argmin(d)]]))
    # top up if empty clusters
    if len(out) < k:
        rest = [c for c in sel_top_load(C, len(C), V, psi) if c not in set(out)]
        out += rest[: k - len(out)]
    return out


def sel_cov_greedy(C, kmax, Sigma):
    """Model-free greedy variance reduction under a (shrunk) empirical correlation matrix, targets = C."""
    C = np.asarray(C)
    R = Sigma[np.ix_(C, C)].copy()
    chosen = []
    avail = np.ones(len(C), bool)
    for _ in range(min(kmax, len(C))):
        gain = np.where(avail, (R ** 2).sum(0) / np.maximum(np.diag(R), 1e-6), -np.inf)
        c = int(np.argmax(gain))
        chosen.append(int(C[c])); avail[c] = False
        col = R[:, c].copy()
        R = R - np.outer(col, col) / max(R[c, c], 1e-6)
    return chosen


# ----------------------------------------------------------------------------- other predictors
def predict_gauss(Sigma, S, zS, ridge=1e-2):
    S = np.asarray(S)
    K = Sigma[np.ix_(S, S)] + ridge * np.eye(len(S))
    return Sigma[:, S] @ np.linalg.solve(K, zS)


def predict_knn(Ztr, S, zS, K=10):
    S = np.asarray(S)
    D = Ztr[:, S] - zS[None, :]
    ov = ~np.isnan(D)
    cnt = ov.sum(1)
    d = np.where(cnt > 0, np.nansum(D ** 2, axis=1) / np.maximum(cnt, 1), np.inf)
    order = np.argsort(d)
    Zs = Ztr[order]
    ob = ~np.isnan(Zs) & np.isfinite(d[order])[:, None]
    cum = np.cumsum(ob, axis=0)
    use = ob & (cum <= K)
    num = np.where(use, np.nan_to_num(Zs), 0).sum(0)
    den = use.sum(0)
    return np.where(den > 0, num / np.maximum(den, 1), 0.0)


# ----------------------------------------------------------------------------- model-implied (theoretical) errors
def implied_fa(V, psi, S):
    """Expected MSE over benchmarks j not in S for a model drawn from the fitted FA model, S observed:
    mean_j [ psi_j + v_j' Sigma_post v_j ]."""
    r = V.shape[1]
    VS = V[S]
    w = np.reciprocal(psi[S])
    P = np.eye(r) + (VS * w[:, None]).T @ VS
    Sg = np.linalg.inv(P)
    mask = np.ones(V.shape[0], bool); mask[S] = False
    Vt = V[mask]
    return float(np.mean(psi[mask] + np.einsum('ij,jk,ik->i', Vt, Sg, Vt)))


def implied_gauss(Sigma, S, ridge=1e-2):
    S = np.asarray(S)
    K = Sigma[np.ix_(S, S)] + ridge * np.eye(len(S))
    mask = np.ones(Sigma.shape[0], bool); mask[S] = False
    B = Sigma[np.ix_(S, np.where(mask)[0])]
    cond = np.diag(Sigma)[mask] - np.einsum('ij,ij->j', B, np.linalg.solve(K, B))
    return float(np.mean(cond))
