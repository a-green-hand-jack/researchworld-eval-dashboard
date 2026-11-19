"""Benchmark selectors. All return an ordered index array (prefix of length k = selection for budget k,
except clustering which depends on k and is called per k).  `cand` = candidate indices (availability
constraint); `par` = fitted FA parameters on history (standardised units)."""
import numpy as np
from scipy.linalg import qr


def greedy_design(par, cand, kmax, criterion='A_all', target=None, cost=None):
    """Greedy Bayesian experimental design on the factor posterior.
    criterion: 'A_all'  W = Lam'Lam (variance reduction of all latent directions),
               'A_T'    W = Lam_T'Lam_T for a fixed target index set `target`,
               'A_comp' minimise expected total squared error on the complement of S,
               'D'      D-optimal  (1/2 logdet), mutual information I(z;x_S).
    cost: optional per-benchmark cost; selects the largest gain per unit cost."""
    Lam, psi = par['Lam'], par['psi']
    N, r = Lam.shape
    cand = list(cand)
    chosen = []
    if r == 0:
        return np.array(cand[:kmax])
    P = np.eye(r)
    if criterion == 'A_all':
        W = Lam.T @ Lam
    elif criterion == 'A_T':
        W = Lam[target].T @ Lam[target]
    else:
        W = None
    Wall = Lam.T @ Lam
    Wc = Wall.copy()                        # sum over complement (A_comp)
    for _ in range(min(kmax, len(cand))):
        c = np.array([j for j in cand if j not in set(chosen)])
        Lc = Lam[c]; PL = Lc @ P
        quad = np.einsum('jr,jr->j', PL, Lc)
        den = psi[c] + quad
        if criterion in ('A_all', 'A_T'):
            gain = np.einsum('jr,jr->j', PL @ W, PL) / den
        elif criterion == 'D':
            gain = 0.5 * np.log1p(quad / psi[c])
        elif criterion == 'A_comp':
            # SSE(S+j) = sum_{i not in S+j} (psi_i + l_i' P' l_i) = const - psi_j ... computed exactly
            gain = np.empty(len(c))
            for a, j in enumerate(c):
                Pn = P - np.outer(PL[a], PL[a]) / den[a]
                Wn = Wc - np.outer(Lam[j], Lam[j])
                sse_new = (psi.sum() - psi[chosen + [j]].sum()) + np.trace(Wn @ Pn)
                gain[a] = -sse_new
        else:
            raise ValueError(criterion)
        if cost is not None and criterion != 'A_comp':
            gain = gain / cost[c]
        a = int(np.argmax(gain)); j = int(c[a])
        P = P - np.outer(PL[a], PL[a]) / den[a]
        Wc = Wc - np.outer(Lam[j], Lam[j])
        chosen.append(j)
    return np.array(chosen)


def f_value(par, S, W=None):
    """f_W(S) = tr(W (I - P_S)), W default Lam'Lam."""
    Lam, psi = par['Lam'], par['psi']
    r = Lam.shape[1]
    W = Lam.T @ Lam if W is None else W
    if len(S) == 0:
        return 0.0
    LS = Lam[S]
    P = np.linalg.inv(np.eye(r) + (LS / psi[S][:, None]).T @ LS)
    return float(np.trace(W @ (np.eye(r) - P)))


def local_search_opt(par, cand, k, n_start=10, rng=None, W=None, init=None):
    """swap local search maximising f_W over k-subsets of cand (reference for greedy)."""
    rng = rng or np.random.default_rng(0)
    cand = np.array(cand); best, bestv = None, -1
    starts = [list(init)] if init is not None else []
    starts += [list(rng.choice(cand, k, replace=False)) for _ in range(n_start)]
    for S in starts:
        S = list(S); v = f_value(par, S, W)
        improved = True
        while improved:
            improved = False
            for pos in range(k):
                for j in cand:
                    if j in S:
                        continue
                    S2 = S.copy(); S2[pos] = j
                    v2 = f_value(par, S2, W)
                    if v2 > v + 1e-12:
                        S, v, improved = S2, v2, True
        if v > bestv:
            best, bestv = S, v
    return np.array(best), bestv


def brute_force_opt(par, cand, k, W=None):
    from itertools import combinations
    best, bv = None, -1
    for S in combinations(cand, k):
        v = f_value(par, list(S), W)
        if v > bv:
            best, bv = S, v
    return np.array(best), bv


def random_order(cand, rng):
    return rng.permutation(np.array(cand))


def most_covered_order(cand, coverage, rng):
    cand = np.array(cand)
    tie = rng.random(len(cand))
    return cand[np.lexsort((tie, -coverage[cand]))]


def abs_corr(Xs, obs, min_overlap=8):
    """pairwise-complete |correlation| on standardised history; NaN pairs -> 0."""
    N = Xs.shape[1]
    X0 = np.where(obs, Xs, 0.0); O = obs.astype(float)
    n = O.T @ O
    sx = X0.T @ O                                   # sum x_i over rows where j observed (i,j)
    sxy = X0.T @ X0
    sxx = (X0 ** 2).T @ O
    with np.errstate(all='ignore'):
        cov = sxy / n - (sx / n) * (sx.T / n)
        vi = sxx / n - (sx / n) ** 2
        vj = vi.T
        c = cov / np.sqrt(vi * vj)
    c[(n < min_overlap) | ~np.isfinite(c)] = 0.0
    np.fill_diagonal(c, 1.0)
    return np.clip(np.abs(c), 0, 1)


def centrality_order(cand, C):
    cand = np.array(cand)
    s = (C[np.ix_(cand, cand)].sum(1) - 1) / max(len(cand) - 1, 1)
    return cand[np.argsort(-s)]


def kmedoids(cand, C, k, rng, n_init=5, iters=50):
    cand = np.array(cand); D = 1 - C[np.ix_(cand, cand)]
    n = len(cand); k = min(k, n)
    best, bc = None, np.inf
    for _ in range(n_init):
        med = rng.choice(n, k, replace=False)
        for _ in range(iters):
            lab = np.argmin(D[:, med], 1)
            new = med.copy()
            for c in range(k):
                idx = np.where(lab == c)[0]
                if len(idx):
                    new[c] = idx[np.argmin(D[np.ix_(idx, idx)].sum(1))]
            if (new == med).all():
                break
            med = new
        cost = D[np.arange(n), med[np.argmin(D[:, med], 1)]].sum()
        if cost < bc:
            best, bc = med.copy(), cost
    return cand[best]


def pivoted_qr_order(cand, Xc):
    """Xc: (M,N) standardised history (complete or imputed). deterministic column-pivoted QR."""
    cand = np.array(cand)
    _, _, piv = qr(Xc[:, cand], pivoting=True, mode='economic')
    return cand[piv]


def leverage_order(cand, Xc, r):
    cand = np.array(cand)
    U, s, Vt = np.linalg.svd(Xc[:, cand], full_matrices=False)
    lev = (Vt[:r] ** 2).sum(0)
    return cand[np.argsort(-lev)]


def greedy_forward_regression(cand, Xc, kmax, lam=1.0):
    """Das-Kempe style: add the benchmark minimising LOO ridge error of predicting ALL columns from S
    (history models only; Xc complete or FA-imputed)."""
    M, N = Xc.shape
    cand = list(cand); chosen = []
    for _ in range(min(kmax, len(cand))):
        best, bj = np.inf, None
        for j in cand:
            if j in chosen:
                continue
            S = chosen + [j]
            A = Xc[:, S]
            H = A @ np.linalg.solve(A.T @ A + lam * np.eye(len(S)), A.T)
            h = np.diag(H)
            R = (Xc - H @ Xc) / (1 - h)[:, None]
            e = (R ** 2).mean()
            if e < best:
                best, bj = e, j
        chosen.append(bj)
    return np.array(chosen)


def greedy_gauss(Sigma, cand, kmax, target=None, cost=None):
    """Greedy minimisation of the expected total squared error under a Gaussian with covariance Sigma
    (classical A-optimal sensor placement).  target=None: error on the complement of S (selected benchmarks
    leave the target set): gain_j = C_jj + sum_{i in T\\j} C_ij^2 / C_jj with C the conditional covariance.
    target=indices: fixed target set (group transfer; candidates exclude it): gain_j = sum_{i in T} C_ij^2/C_jj.
    cost: optional per-benchmark cost, gain per unit cost."""
    C = Sigma.copy(); N = len(C)
    cand = np.array([j for j in cand if target is None or j not in set(target)]); chosen = []
    inT = np.ones(N, bool)
    if target is not None:
        inT[:] = False; inT[list(target)] = True
    for _ in range(min(kmax, len(cand))):
        c = np.array([j for j in cand if j not in set(chosen)])
        d = np.diag(C)[c]
        Csq = C[np.ix_(c, np.where(inT)[0])] ** 2
        if target is None:
            gain = d + (Csq.sum(1) - d ** 2) / d
        else:
            gain = Csq.sum(1) / d
        if cost is not None:
            gain = gain / cost[c]
        j = int(c[np.argmax(gain)])
        C = C - np.outer(C[:, j], C[j, :]) / C[j, j]
        if target is None:
            inT[j] = False
        chosen.append(j)
    return np.array(chosen)
