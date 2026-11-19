"""Stochastic Shapley estimators, run against a value oracle for ONE instance x (interventional value function
v(S) = mean_k f(x_S, b_k,~S)).  The oracle is either a full table over all 2^d coalitions (table engine) or a live
model call (live engine).  Every estimator is charged in *coalition evaluations* (the number of distinct v(S)
calls it makes, excluding the free v(empty), v(N)); masked-input model evaluations = coalitions x m.

Only attributes that actually vary between x and the background (M of them) are players, as in shap.

Estimators
  kshap(M, N, l1)     re-implementation of shap 0.51.0 KernelExplainer (l1='num_features(10)' = shipped default, l1=False = no truncation)
  perm(M, N)          shap PermutationExplainer logic (antithetic permutations, N // (2M+1) of them)
  covert_lee(M, N)    Covert & Lee (2021) unbiased KernelSHAP with SE (paired sampling, analytic A)
"""
import itertools
import numpy as np
from math import comb
from scipy.special import binom
from sklearn.linear_model import lars_path


class Oracle:
    """v(S) for one instance. `bits[j]` = bit position (in the full-d coalition index) of player j."""
    def __init__(self, table=None, live=None, var_idx=None, d=None):
        self.table, self.live = table, live
        self.var_idx = np.asarray(var_idx)               # attribute indices of the M varying players
        self.M = len(self.var_idx)
        self.d = d
        self.pow2 = (1 << self.var_idx.astype(np.int64)) if table is not None else None
        if table is not None:
            self.v0, self.vN = float(table[0]), float(table[-1])
        else:
            self.v0, self.vN = live.v0, live.vN
        self.calls = 0

    def __call__(self, masks):
        """masks: (c, M) {0,1} over the varying players -> v (c,)"""
        self.calls += masks.shape[0]
        if self.table is not None:
            idx = masks.astype(np.int64) @ self.pow2
            return self.table[idx].astype(np.float64)
        full = np.zeros((masks.shape[0], self.d), np.float32)
        full[:, self.var_idx] = masks
        return self.live.value_masks(full)


# ---------------------------------------------------------------- shap KernelExplainer (0.51.0) re-implementation
_enum_cache = {}


def _kernel_plan(M, nsamples):
    key = (M, nsamples)
    if key in _enum_cache:
        return _enum_cache[key]
    num_subset_sizes = int(np.ceil((M - 1) / 2.0))
    num_paired = int(np.floor((M - 1) / 2.0))
    wv = np.array([(M - 1.0) / (i * (M - i)) for i in range(1, num_subset_sizes + 1)])
    wv[:num_paired] *= 2
    wv /= wv.sum()
    masks, weights = [], []
    num_full, left = 0, nsamples
    rem = wv.copy()
    for s in range(1, num_subset_sizes + 1):
        nsub = binom(M, s) * (2 if s <= num_paired else 1)
        if left * rem[s - 1] / nsub >= 1.0 - 1e-8:
            num_full += 1
            left -= nsub
            if rem[s - 1] < 1.0:
                rem = rem / (1 - rem[s - 1])
            w = wv[s - 1] / binom(M, s) / (2.0 if s <= num_paired else 1.0)
            for inds in itertools.combinations(range(M), s):
                m = np.zeros(M, np.float32); m[list(inds)] = 1
                masks.append(m); weights.append(w)
                if s <= num_paired:
                    masks.append(1 - m); weights.append(w)
        else:
            break
    em = np.array(masks, np.float32).reshape(-1, M)
    ew = np.array(weights)
    plan = dict(M=M, nsub=num_subset_sizes, npair=num_paired, wv=wv, num_full=num_full, em=em, ew=ew,
                nfixed=len(em), left=nsamples - len(em))
    if num_full != num_subset_sizes:
        r = wv.copy(); r[:num_paired] /= 2; r = r[num_full:]; plan["rem_p"] = r / r.sum()
        plan["weight_left"] = wv[num_full:].sum()
    if len(_enum_cache) > 64:
        _enum_cache.clear()
    _enum_cache[key] = plan
    return plan


def kshap_samples(M, nsamples, rng):
    """coalition masks and kernel weights exactly as shap 0.51.0 draws them (distributionally)."""
    nsamples = int(min(nsamples, 2 ** M - 2)) if M <= 30 else int(nsamples)
    P = _kernel_plan(M, nsamples)
    masks, w = [P["em"]], [P["ew"]]
    if P["num_full"] != P["nsub"] and P["left"] > 0:
        left = P["left"]
        sizes = rng.choice(len(P["rem_p"]), 4 * left, p=P["rem_p"]) + P["num_full"] + 1
        R = np.argsort(rng.random((len(sizes), M), dtype=np.float32), axis=1)
        rank = np.empty_like(R); np.put_along_axis(rank, R, np.arange(M)[None, :], axis=1)
        dm = (rank < sizes[:, None])                                        # (4*left, M) bool
        if M < 62:
            code = dm.astype(np.int64) @ (1 << np.arange(M, dtype=np.int64))
        else:                                                               # wide games: hash the packed bit rows
            pk = np.ascontiguousarray(np.packbits(dm, axis=1)); code = pk.view(np.dtype((np.void, pk.shape[1]))).ravel()
        uniq, first, inv = np.unique(code, return_index=True, return_inverse=True)
        # a draw is "new" if it is the first occurrence of its mask
        is_new = np.zeros(len(sizes), bool); is_new[first] = True
        paired = sizes <= P["npair"]
        cost = np.where(is_new, 1 + paired.astype(int), 0)
        cum = np.cumsum(cost)
        take = (cum - cost) < left                                          # draws started while samples_left > 0
        # shap: complement is added only if samples_left > 0 after adding the original
        comp_ok = is_new & paired & ((cum - cost + 1) < left)
        use = take & is_new
        counts = np.bincount(inv[take], minlength=len(uniq))
        rows = first[np.argsort(first)]
        rows = np.array([r for r in rows if use[r]], int)
        orig = dm[rows].astype(np.float32); wr = counts[inv[rows]].astype(float)
        cm = comp_ok[rows]
        comp = 1 - orig[cm]
        masks += [orig, comp]
        w += [wr, wr[cm]]
        wcat = np.concatenate(w[1:])
        w = [P["ew"], wcat * P["weight_left"] / wcat.sum()]
    return np.concatenate(masks, 0), np.concatenate(w, 0)


def _solve_kshap(masks, w, y, vN_minus_v0, M, l1):
    """shap KernelExplainer.solve for one output dimension."""
    nonzero = np.arange(M)
    if l1 not in (False, 0):
        s = masks.sum(1)
        w_aug = np.hstack((w * (M - s), w * s)); sq = np.sqrt(w_aug)
        y_aug = np.hstack((y, y - vN_minus_v0)) * sq
        m_aug = (sq[:, None] * np.vstack((masks, masks - 1)))
        r = int(l1[len("num_features("):-1])
        nonzero = np.array(lars_path(m_aug, y_aug, max_iter=r)[1], int)
    if len(nonzero) == 0:
        return np.zeros(M)
    last = nonzero[-1]
    y2 = y - masks[:, last] * vN_minus_v0
    X = masks[:, nonzero[:-1]] - masks[:, [last]]
    WX = w[:, None] * X
    try:
        beta = np.linalg.solve(X.T @ WX, WX.T @ y2)
    except np.linalg.LinAlgError:
        sw = np.sqrt(w); beta = np.linalg.lstsq(sw[:, None] * X, sw * y2, rcond=None)[0]
    phi = np.zeros(M)
    phi[nonzero[:-1]] = beta
    phi[last] = vN_minus_v0 - beta.sum()
    return phi


def kshap(orc, nsamples, rng, l1="num_features(10)"):
    M = orc.M
    if M == 0:
        return np.zeros(0), {}
    if M == 1:
        return np.array([orc.vN - orc.v0]), {}
    masks, w = kshap_samples(M, nsamples, rng)
    y = orc(masks) - orc.v0
    phi = _solve_kshap(masks.astype(np.float64), w, y, orc.vN - orc.v0, M, l1)
    return phi, dict(n_coal=len(masks))


# ---------------------------------------------------------------- permutation (shap PermutationExplainer logic)
def perm(orc, max_evals, rng):
    M = orc.M
    if M == 0:
        return np.zeros(0), {}
    P = max(1, int(max_evals) // (2 * M + 1))
    order = np.argsort(rng.random((P, M)), axis=1)                               # (P, M)
    phi = np.zeros(M)
    for rev in (False, True):
        o = order[:, ::-1] if rev else order
        pre = np.zeros((P, M + 1), np.int64)                                      # prefix membership as ranks
        # prefix t = set of first t players of o
        masks = np.zeros((P, M + 1, M), np.float32)
        for t in range(1, M + 1):
            masks[:, t] = masks[:, t - 1]
            masks[np.arange(P), t, o[:, t - 1]] = 1
        v = np.empty((P, M + 1))
        v[:, 0], v[:, M] = orc.v0, orc.vN
        inner = masks[:, 1:M].reshape(-1, M)
        v[:, 1:M] = orc(inner).reshape(P, M - 1)
        contrib = np.diff(v, axis=1)                                              # (P, M): marginal of o[:, t]
        np.add.at(phi, o.ravel(), contrib.ravel())
    phi /= 2 * P
    return phi, dict(n_coal=2 * P * (M - 1), n_perm=P)


# ---------------------------------------------------------------- Covert & Lee (2021) unbiased KernelSHAP with SE
_A_cache = {}


def _cl_matrices(M):
    if M in _A_cache:
        return _A_cache[M]
    s = np.arange(1, M)
    ps = 1.0 / (s * (M - s)); ps /= ps.sum()
    diag = (ps * s / M).sum()
    off = (ps * s * (s - 1) / (M * (M - 1))).sum()
    A = np.full((M, M), off); np.fill_diagonal(A, diag)
    Ai = np.linalg.inv(A)
    one = np.ones(M)
    Ai1 = Ai @ one
    Pm = Ai - np.outer(Ai1, Ai1) / (one @ Ai1)                                    # phi = Pm b + Ai1 (vN-v0)/(1^T Ai1)
    c = Ai1 / (one @ Ai1)
    _A_cache[M] = (ps, Pm, c)
    return _A_cache[M]


def covert_lee_sample(M, n_pairs, rng):
    ps, _, _ = _cl_matrices(M)
    sizes = rng.choice(np.arange(1, M), n_pairs, p=ps)
    R = np.argsort(rng.random((n_pairs, M), dtype=np.float32), axis=1)
    rank = np.empty_like(R); np.put_along_axis(rank, R, np.arange(M)[None, :], axis=1)
    return (rank < sizes[:, None]).astype(np.float32)


def covert_lee_from(masks, v, orc_v0, orc_vN, M):
    """returns phi_hat (M,), per-pair influence matrix (n_pairs, M) whose mean is phi_hat; SE = std/sqrt(n)."""
    ps, Pm, c = _cl_matrices(M)
    comp = 1 - masks
    n = len(masks)
    y, yc = v[:n] - orc_v0, v[n:] - orc_v0
    u = 0.5 * (masks * y[:, None] + comp * yc[:, None])                           # per-pair estimate of b
    infl = u @ Pm.T + c[None, :] * (orc_vN - orc_v0)
    return infl.mean(0), infl


def covert_lee(orc, nsamples, rng, return_cov=False):
    M = orc.M
    if M <= 1:
        return (np.zeros(M) if M == 0 else np.array([orc.vN - orc.v0])), {}
    n_pairs = max(2, int(nsamples) // 2)
    masks = covert_lee_sample(M, n_pairs, rng)
    v = orc(np.concatenate([masks, 1 - masks], 0))
    phi, infl = covert_lee_from(masks, v, orc.v0, orc.vN, M)
    cov = np.cov(infl.T) / n_pairs
    info = dict(n_coal=2 * n_pairs, se=np.sqrt(np.clip(np.diag(cov), 0, None)))
    if return_cov:
        info["cov"] = cov
    return phi, info



# ---------------------------------------------------------------- Leverage SHAP (Musco & Witter, ICLR 2025), Algorithm 1 as printed
def _lev_solve_c(M, m):
    """c with sum_{s=1}^{M-1} min(C(M,s), 2c) = m - 2 (their Eq. 12), by bisection."""
    C = np.array([comb(M, s) for s in range(1, M)], dtype=np.float64)
    lo, hi = 0.0, C.max()
    for _ in range(80):
        mid = 0.5 * (lo + hi)
        if np.minimum(C, 2 * mid).sum() < m - 2: lo = mid
        else: hi = mid
    return hi


def _draw_sets(M, s, count, rng, pin0=False):
    """`count` distinct uniformly random subsets of size s (bitmask rows); pin0: only sets containing player 0."""
    out = {}
    while len(out) < count:
        need = count - len(out)
        R = np.argsort(rng.random((need + 8, M - 1 if pin0 else M)), axis=1)[:, :(s - 1 if pin0 else s)]
        for r in R:
            key = tuple(sorted(r))
            if key not in out:
                out[key] = r
                if len(out) == count: break
    rows = np.zeros((count, M), np.float32)
    for i, r in enumerate(out.values()):
        rows[i, (r + 1) if pin0 else r] = 1
        if pin0: rows[i, 0] = 1
    return rows


def leverage_shap(orc, nsamples, rng):
    """Paired leverage-score sampling without replacement (Bernoulli, expected evaluations = nsamples), inverse-probability weights, regression
    on the projected system. Leverage score of a set of size s is proportional to 1/C(M,s); kernel weight w(s) = 1/(C(M,s) s (M-s)).
    Evaluations are counted as realised (2|Z'|), which is only m in expectation, as in the paper's Algorithm 1."""
    M = orc.M
    if M <= 1:
        return (np.zeros(M) if M == 0 else np.array([orc.vN - orc.v0])), {}
    m = int(min(max(nsamples, 4), 2 ** M))
    c = _lev_solve_c(M, m)
    rows, wts = [], []
    for s in range(1, M // 2 + 1):
        mid = (2 * s == M)
        Cs = comb(M, s)
        nz = Cs // 2 if mid else Cs                                              # pairs available in this layer
        p = min(1.0, 2 * c / Cs)
        cnt = nz if p >= 1.0 else int(rng.binomial(nz, p))
        if cnt == 0: continue
        if p >= 1.0:
            if mid:
                Z = np.array([[1.0 if j in (0,) + cm else 0.0 for j in range(M)] for cm in itertools.combinations(range(1, M), s - 1)], np.float32)
            else:
                Z = np.array([[1.0 if j in cm else 0.0 for j in range(M)] for cm in itertools.combinations(range(M), s)], np.float32)
        else:
            Z = _draw_sets(M, s, cnt, rng, pin0=mid)
        w = 1.0 / (Cs * s * (M - s)) / p
        rows.append(Z); wts.append(np.full(len(Z), w))
        rows.append(1 - Z); wts.append(np.full(len(Z), w))
    Z = np.concatenate(rows, 0); W = np.concatenate(wts)
    v = orc(Z)
    delta = orc.vN - orc.v0
    b = (v - orc.v0) - delta / M * Z.sum(1)
    P = np.eye(M) - np.ones((M, M)) / M
    sw = np.sqrt(W)
    x = np.linalg.lstsq((Z @ P) * sw[:, None], b * sw, rcond=None)[0]
    return P @ x + delta / M, dict(n_coal=len(Z), c=c)


# ---------------------------------------------------------------- exact Shapley from the full table
def exact_from_table(table, d):
    n = 1 << d
    pc = np.zeros(n, np.int8)
    for j in range(d):
        pc += ((np.arange(n) >> j) & 1).astype(np.int8)
    from scipy.special import gammaln
    s = np.arange(d)
    wlog = gammaln(s + 1) + gammaln(d - s) - gammaln(d + 1)
    w = np.exp(wlog)[np.clip(pc, 0, d - 1)]
    t = table.astype(np.float64)
    idx = np.arange(n)
    phi = np.zeros(d)
    for j in range(d):
        no = idx[((idx >> j) & 1) == 0]
        phi[j] = (w[no] * (t[no | (1 << j)] - t[no])).sum()
    return phi
