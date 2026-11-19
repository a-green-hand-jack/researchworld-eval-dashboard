"""Shapley-value estimators operating on a *value-table oracle*.

All estimators only touch the cooperative game through v(S) for the coalitions they sample, so for a
game with d <= 20 players we tabulate v on all 2^d coalitions once (see common.build_table) and then
every estimator run is a table lookup.  This gives *exactly* the output a run with real model calls
would give (same coalitions, same values), at negligible cost, and lets us repeat runs thousands of times.

Budget accounting: `m` = number of coalition evaluations v(S) (excluding the empty and full coalition,
which every method evaluates once); each costs |background| model calls.

Estimators
  kernel   : Kernel SHAP following the sampling/enumeration logic of shap.KernelExplainer
             (paired sampling, complete enumeration of the cheapest size strata, size-proportional
             sampling for the rest, constrained weighted least squares; no L1 selection).
  leverage : same machinery but sampling pairs from the leverage-score distribution of the Shapley
             regression (uniform over sizes; Musco & Witter 2024) and Horvitz-Thompson weights.
             This is OUR re-implementation of the idea, not the authors' code.
  perm     : antithetic permutation sampling (forward + reversed permutation), as shap.PermutationExplainer.
"""
import numpy as np
import numba as nb
from math import comb, factorial

# ----------------------------------------------------------------------------------------------
# exact Shapley values from a full table
# ----------------------------------------------------------------------------------------------

def popcount_table(d):
    pc = np.zeros(1 << d, dtype=np.int8)
    for i in range(d):
        pc[(1 << i):(1 << (i + 1))] = pc[:(1 << i)] + 1
    return pc


def exact_shapley(v, d, pc=None):
    """v: array (2^d,) of coalition values indexed by bitmask (bit i = player i in S)."""
    if pc is None:
        pc = popcount_table(d)
    v = np.asarray(v, dtype=np.float64)
    w = np.array([factorial(s) * factorial(d - s - 1) / factorial(d) for s in range(d)])
    ids = np.arange(1 << d)
    phi = np.zeros(d)
    for i in range(d):
        without = ids[(ids >> i) & 1 == 0]
        phi[i] = np.sum(w[pc[without]] * (v[without | (1 << i)] - v[without]))
    return phi


def additivity_residual(v, d, phi, pc=None):
    """Kernel-weighted share of the variance of v(S)-v(0) NOT explained by the additive game phi.
    0 = game is additive (any estimator is exact), larger = more interaction / more estimator noise."""
    if pc is None:
        pc = popcount_table(d)
    ids = np.arange(1, (1 << d) - 1)
    s = pc[ids].astype(np.float64)
    k = (d - 1.0) / (np.array([comb(d, int(a)) for a in range(d + 1)])[pc[ids]] * s * (d - s))
    add = np.zeros(1 << d)
    for i in range(d):
        add += phi[i] * ((np.arange(1 << d) >> i) & 1)
    y = v[ids] - v[0]
    r = y - add[ids]
    return float(np.sum(k * r * r) / np.sum(k * y * y))


# ----------------------------------------------------------------------------------------------
# Kernel-SHAP-style sampler (numba)
# ----------------------------------------------------------------------------------------------

def class_plan(d, mode):
    """Per-size-class quantities used by the sampler.  Classes are sizes s = 1..S, S=ceil((d-1)/2);
    class s stands for sizes s and d-s (paired) unless s == d/2."""
    S = int(np.ceil((d - 1) / 2.0))
    P = int(np.floor((d - 1) / 2.0))
    if mode == "kernel":
        mass = np.array([(d - 1.0) / (s * (d - s)) for s in range(1, S + 1)])
    elif mode == "leverage":
        mass = np.ones(S)
    else:
        raise ValueError(mode)
    return S, P, mass


@nb.njit(cache=True)
def _binom(n, k):
    r = 1.0
    for i in range(1, k + 1):
        r = r * (n - k + i) / i
    return r


@nb.njit(cache=True)
def _sample_design(d, nsamples, mass, S, P, seed, seen):
    """Port of the sampling logic of shap.KernelExplainer.explain (see shap/explainers/_kernel.py).
    Returns arrays: ids (bitmask) of rows, kind (0 enumerated, 1 sampled), count (draw counts for sampled rows),
    nfull (number of fully enumerated classes), and per-draw records (row index of original, paired flag)."""
    np.random.seed(seed)
    full_mask = (1 << d) - 1
    # class weights as in shap: mass, doubled for paired classes, normalised
    wv = mass.copy()
    for i in range(P):
        wv[i] *= 2.0
    wv = wv / wv.sum()
    maxrows = nsamples + 2
    ids = np.empty(maxrows, dtype=np.int64)
    cnt = np.zeros(maxrows, dtype=np.float64)
    nrows = 0
    rem = wv.copy()
    nleft = float(nsamples)
    nfull = 0
    # --- enumerate complete size classes while affordable
    for s in range(1, S + 1):
        nsub = _binom(d, s)
        if s <= P:
            nsub *= 2.0
        if nleft * rem[s - 1] / nsub >= 1.0 - 1e-8:
            nfull += 1
            nleft -= nsub
            if rem[s - 1] < 1.0:
                rem = rem / (1.0 - rem[s - 1])
            # enumerate all subsets of size s (Gosper's hack)
            x = (1 << s) - 1
            while x <= full_mask:
                ids[nrows] = x
                nrows += 1
                if s <= P:
                    ids[nrows] = full_mask ^ x
                    nrows += 1
                c = x & (-x)
                r = x + c
                x = (((r ^ x) >> 2) // c) | r
        else:
            break
    nfixed = nrows
    samples_left = nsamples - nrows
    # draws: original row index + paired flag
    ndraw_max = 4 * max(samples_left, 1)
    draw_row = np.empty(ndraw_max, dtype=np.int64)
    draw_pair = np.zeros(ndraw_max, dtype=np.bool_)
    draw_size = np.zeros(ndraw_max, dtype=np.int64)
    ndraw = 0
    if nfull != S and samples_left > 0:
        rw = mass.copy()
        rw = rw[nfull:]
        rw = rw / rw.sum()
        cum = np.cumsum(rw)
        used_rows = np.empty(ndraw_max, dtype=np.int64)  # ids marked in `seen` (to reset)
        nused = 0
        perm = np.arange(d)
        while samples_left > 0 and ndraw < ndraw_max:
            u = np.random.random()
            ind = 0
            while ind < len(cum) - 1 and u > cum[ind]:
                ind += 1
            s = ind + nfull + 1
            # random subset of size s
            for i in range(d):
                perm[i] = i
            for i in range(s):  # partial Fisher-Yates
                j = i + int(np.random.random() * (d - i))
                t = perm[i]; perm[i] = perm[j]; perm[j] = t
            m = 0
            for i in range(s):
                m |= (1 << perm[i])
            paired = s <= P
            if seen[m] < 0:
                # new sample
                seen[m] = nrows
                used_rows[nused] = m
                nused += 1
                ids[nrows] = m
                cnt[nrows] = 1.0
                r0 = nrows
                nrows += 1
                samples_left -= 1
                if samples_left > 0 and paired:
                    ids[nrows] = full_mask ^ m
                    cnt[nrows] = 1.0
                    nrows += 1
                    samples_left -= 1
                    draw_pair[ndraw] = True
                draw_row[ndraw] = r0
            else:
                r0 = seen[m]
                cnt[r0] += 1.0
                if paired:
                    cnt[r0 + 1] += 1.0
                    draw_pair[ndraw] = True
                draw_row[ndraw] = r0
            draw_size[ndraw] = s
            ndraw += 1
        for k in range(nused):
            seen[used_rows[k]] = -1
    return ids[:nrows], cnt[:nrows], nfixed, nfull, draw_row[:ndraw], draw_pair[:ndraw], draw_size[:ndraw]


_SEEN = {}


def _seen_buf(d):
    if d not in _SEEN:
        _SEEN[d] = -np.ones(1 << d, dtype=np.int64)
    return _SEEN[d]


def _bits(ids, d):
    return ((ids[:, None] >> np.arange(d)[None, :]) & 1).astype(np.float64)


def kernel_like(vfun, d, m, seed, mode="kernel", want_se=False, pc=None):
    """Run Kernel SHAP ('kernel') or leverage-score SHAP ('leverage') with budget m coalition evaluations.

    vfun(ids) -> array of v values for coalition bitmasks (vectorised). v(0) and v(full) are obtained via vfun too.
    Returns phi (d,) and optionally the sandwich standard errors (d,)."""
    S, P, mass = class_plan(d, mode)
    full = (1 << d) - 1
    max_samples = (1 << d) - 2
    m = min(int(m), max_samples)
    ids, cnt, nfixed, nfull, drow, dpair, dsize = _sample_design(d, m, mass, S, P, int(seed), _seen_buf(d))
    v0, vf = vfun(np.array([0, full]))
    delta = vf - v0
    # Z: total unnormalised kernel mass over all sets of size 1..d-1 (paired classes counted twice)
    wv = mass.copy(); wv[:P] *= 2.0
    pcl = pc if pc is not None else popcount_table(d)
    sz = pcl[ids].astype(np.int64)
    binoms = np.array([comb(d, s) for s in range(d + 1)], dtype=np.float64)
    ssum = np.sum(1.0 / (np.arange(1, d) * (d - np.arange(1, d))))
    # normalised Shapley kernel weight of ONE set of size s: 1 / (C(d,s) s (d-s) sum_s' 1/(s'(d-s')))
    kS = 1.0 / (binoms[sz] * sz * (d - sz) * ssum)
    Z = (d - 1.0) * ssum
    w = kS.copy()
    nsampled_rows = len(ids) - nfixed
    ndraw = len(drow)
    cdraw = None
    if nsampled_rows > 0 and ndraw > 0:
        if mode == "kernel":
            weight_left = np.sum(wv[nfull:]) / Z  # share of kernel mass not enumerated (cf. shap)
            tot = cnt[nfixed:].sum()
            w[nfixed:] = cnt[nfixed:] * weight_left / tot
            cset = weight_left / tot  # weight per set per draw
            cdraw = np.full(ndraw, cset)
        else:
            rw = mass[nfull:] / mass[nfull:].sum()
            pi = rw[dsize - nfull - 1]  # class probability of each draw
            kd = 1.0 / (binoms[dsize] * dsize * (d - dsize) * ssum)
            cdraw = kd * binoms[dsize] / pi / ndraw
            # rows' weights = sum of the per-draw weights of draws that touched them
            w[nfixed:] = 0.0
            np.add.at(w, drow, cdraw)
            pr = dpair
            np.add.at(w, drow[pr] + 1, cdraw[pr])
    # --- constrained weighted least squares
    vals = vfun(ids)
    y = vals - v0
    B = _bits(ids, d)
    Zm = B[:, :-1] - B[:, -1:]
    yt = y - B[:, -1] * delta
    Wz = w[:, None] * Zm
    A = Zm.T @ Wz
    rhs = Wz.T @ yt
    try:
        theta = np.linalg.solve(A, rhs)
    except np.linalg.LinAlgError:
        theta = np.linalg.lstsq(A, rhs, rcond=None)[0]
    phi = np.append(theta, delta - theta.sum())
    if not want_se:
        return phi
    # --- sandwich standard error from the iid draws (enumerated part treated as fixed)
    if cdraw is None or ndraw < 3:
        return phi, np.zeros(d)
    resid = yt - Zm @ theta
    zr = Zm * resid[:, None]  # per-row score contribution before weights  (rows, d-1)
    G = np.zeros((ndraw, d - 1))
    G += cdraw[:, None] * zr[drow]
    pr = dpair
    G[pr] += cdraw[pr][:, None] * zr[drow[pr] + 1]
    # contribution of a draw to the score is its own weight (no multiplicity), mean-centre and scale
    Gc = G - G.mean(0, keepdims=True)
    meat = (ndraw / (ndraw - 1.0)) * (Gc.T @ Gc)
    Ainv = np.linalg.pinv(A)
    V = Ainv @ meat @ Ainv
    T = np.vstack([np.eye(d - 1), -np.ones((1, d - 1))])
    Vfull = T @ V @ T.T
    se = np.sqrt(np.maximum(np.diag(Vfull), 0.0))
    return phi, se


# ----------------------------------------------------------------------------------------------
# permutation SHAP
# ----------------------------------------------------------------------------------------------

def perm_shap(vfun, d, m, seed, want_se=False):
    """Antithetic permutation sampling: each forward+reverse pair costs 2(d-1) coalition evaluations."""
    rng = np.random.default_rng(seed)
    npair = max(int(m // (2 * (d - 1))), 1)
    perms = np.argsort(rng.random((npair, d)), axis=1)
    full = (1 << d) - 1
    v0, vf = vfun(np.array([0, full]))
    out = np.zeros((npair, d))
    for rev in (0, 1):
        p = perms[:, ::-1] if rev else perms
        bit = (1 << p.astype(np.int64))
        pref = np.cumsum(bit, axis=1)  # coalition after adding k-th element (disjoint bits => sum == OR)
        vv = vfun(pref.ravel()).reshape(npair, d)
        vv[:, -1] = vf
        prev = np.concatenate([np.full((npair, 1), v0), vv[:, :-1]], axis=1)
        contrib = vv - prev
        rows = np.arange(npair)[:, None]
        out[rows, p] += 0.5 * contrib
    phi = out.mean(0)
    if not want_se:
        return phi
    se = out.std(0, ddof=1) / np.sqrt(npair) if npair > 1 else np.full(d, np.nan)
    return phi, se


def run_estimator(name, vfun, d, m, seed, want_se=False, pc=None):
    if name == "kernel" or name == "leverage":
        return kernel_like(vfun, d, m, seed, mode=name, want_se=want_se, pc=pc)
    if name == "perm":
        return perm_shap(vfun, d, m, seed, want_se=want_se)
    raise ValueError(name)
