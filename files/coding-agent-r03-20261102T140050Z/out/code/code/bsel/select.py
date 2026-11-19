"""Benchmark-subset selection rules. Every rule returns an *ordered* list of indices into the candidate set
(prefix of length k = selection of size k), so one call serves all k (except k-medoids).
cov: (n,n) covariance of the candidates (standardized scale)."""
import itertools
import numpy as np


def greedy_var(cov, kmax):
    """Greedy minimisation of sum_j Var(z_j | z_S) over candidates (pivoted-Cholesky / variance-reduction rule)."""
    R = cov.copy(); out = []
    for _ in range(min(kmax, len(R))):
        d = np.diag(R).copy()
        gain = (R ** 2).sum(0) / np.maximum(d, 1e-12)
        gain[out] = -1
        j = int(np.argmax(gain)); out.append(j)
        R = R - np.outer(R[:, j], R[j, :]) / max(R[j, j], 1e-12)
    return out


def greedy_pivot(cov, kmax):
    """Greedy max conditional variance ('highest entropy' rule, the baseline of Krause et al. 2008)."""
    R = cov.copy(); out = []
    for _ in range(min(kmax, len(R))):
        d = np.diag(R).copy(); d[out] = -1
        j = int(np.argmax(d)); out.append(j)
        R = R - np.outer(R[:, j], R[j, :]) / max(R[j, j], 1e-12)
    return out


def greedy_mi(cov, kmax):
    """Greedy mutual-information rule (Krause et al. 2008): argmax Var(j|S) / Var(j | all other candidates)."""
    prec = np.linalg.inv(cov + 1e-8 * np.eye(len(cov)))
    w = np.diag(prec)
    R = cov.copy(); out = []
    for _ in range(min(kmax, len(R))):
        d = np.diag(R) * w; d[out] = -1
        j = int(np.argmax(d)); out.append(j)
        R = R - np.outer(R[:, j], R[j, :]) / max(R[j, j], 1e-12)
    return out


def top_snr(L, psi, kmax):
    """Top-k by factor-model signal-to-noise (communality / unique variance); ignores redundancy."""
    return list(np.argsort(-(L ** 2).sum(1) / psi)[:kmax])


def central(cov, kmax):
    """Top-k by mean absolute correlation with the other candidates; ignores redundancy."""
    d = np.sqrt(np.diag(cov)); C = np.abs(cov / np.outer(d, d)); np.fill_diagonal(C, 0)
    return list(np.argsort(-C.mean(1))[:kmax])


def kmedoids(cov, k, seed=0, n_init=5, n_iter=30):
    """k-medoids on distance 1-|corr|; returns k medoids (not nested in k)."""
    d = np.sqrt(np.diag(cov)); D = 1 - np.abs(cov / np.outer(d, d))
    n = len(D); k = min(k, n); rng = np.random.default_rng(seed); best = None
    for _ in range(n_init):
        med = [int(rng.integers(n))]
        while len(med) < k:
            dm = D[:, med].min(1) ** 2; dm[med] = 0
            med.append(int(rng.choice(n, p=dm / dm.sum())) if dm.sum() > 0 else int(rng.integers(n)))
        for _ in range(n_iter):
            lab = D[:, med].argmin(1); new = []
            for c in range(k):
                idx = np.where(lab == c)[0]
                new.append(int(idx[D[np.ix_(idx, idx)].sum(1).argmin()]) if len(idx) else med[c])
            if new == med:
                break
            med = new
        cost = D[:, med].min(1).sum()
        if best is None or cost < best[0]:
            best = (cost, list(med))
    return best[1]


def objective(cov, S):
    """sum over candidates of Var(z_j | z_S) (zero for members of S)."""
    S = list(S)
    if not S:
        return float(np.trace(cov))
    Kss = cov[np.ix_(S, S)]; Ksa = cov[S, :]
    R = cov - Ksa.T @ np.linalg.solve(Kss, Ksa)
    return float(np.trace(R))


def exhaustive_best(cov, k):
    """Exact minimiser of `objective` over all size-k subsets (small n only)."""
    best = (np.inf, None)
    for S in itertools.combinations(range(len(cov)), k):
        v = objective(cov, S)
        if v < best[0]:
            best = (v, list(S))
    return best[1]
