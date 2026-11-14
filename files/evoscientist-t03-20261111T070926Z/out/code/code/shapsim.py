"""Shapley-value estimators over an interventional (marginal / baseline) value function
    v(S) = mean_b f(x_S, b_{not S}),  b in a background set,
re-implemented so that (i) the number of coalition evaluations (the budget) is controlled exactly and
(ii) for d <= 12 all 2^d coalition values can be tabulated once, giving exact Shapley values and
making thousands of independent estimator runs essentially free. The KernelSHAP implementation follows the
sampling/weighting scheme of the `shap` package (paired sampling, full enumeration of cheap size strata,
random sampling of the remainder with weight renormalisation). It is validated against
shap.KernelExplainer in validate_impl.py.
"""
import numpy as np
from math import comb
from functools import lru_cache
from itertools import combinations

# --------------------------------------------------------------------------- value function


def hybrid_rows(x, bg, masks):
    """masks (m,d) bool -> rows (m*B, d): feature j from x if mask[j] else from background row."""
    m, d = masks.shape
    B = bg.shape[0]
    return np.where(masks[:, None, :], x[None, None, :], bg[None, :, :]).reshape(m * B, d)


def eval_masks(predict, x, bg, masks, logit=False, chunk=20000):
    m, d = masks.shape
    B = bg.shape[0]
    out = np.empty(m)
    step = max(1, chunk // B)
    for s in range(0, m, step):
        mk = masks[s:s + step]
        p = predict(hybrid_rows(x, bg, mk))
        if logit:
            p = np.clip(p, 1e-6, 1 - 1e-6)
            p = np.log(p / (1 - p))
        out[s:s + step] = p.reshape(len(mk), B).mean(1)
    return out


def all_masks(d):
    codes = np.arange(2 ** d)
    return ((codes[:, None] >> np.arange(d)[None, :]) & 1).astype(bool)


def build_table(predict, x, bg, logit=False):
    """values of all 2^d coalitions, indexed by integer code sum_j mask_j 2^j."""
    d = len(x)
    return eval_masks(predict, x, bg, all_masks(d), logit=logit)


class TableV:
    def __init__(self, table):
        self.table = table
        d = int(np.log2(len(table)))
        self.pw = (1 << np.arange(d)).astype(np.int64)

    def __call__(self, masks):
        return self.table[masks.astype(np.int64) @ self.pw]


class LiveV:
    def __init__(self, predict, x, bg, logit=False):
        self.predict, self.x, self.bg, self.logit = predict, x, bg, logit

    def __call__(self, masks):
        return eval_masks(self.predict, self.x, self.bg, masks, self.logit)


# --------------------------------------------------------------------------- exact Shapley from table


def exact_shapley(table):
    d = int(np.log2(len(table)))
    phi = np.zeros(d)
    codes = np.arange(2 ** d)
    sizes = np.array([bin(c).count("1") for c in range(2 ** d)])
    wt = np.array([1.0 / (d * comb(d - 1, s)) for s in range(d)])  # weight for |S|=s, S not containing j
    for j in range(d):
        without = codes[(codes >> j) & 1 == 0]
        s = sizes[without]
        phi[j] = np.sum(wt[s] * (table[without | (1 << j)] - table[without]))
    return phi


def nonadditivity(table, phi):
    """Shapley-kernel-weighted share of the coalition-value variation not explained by the additive fit
    v(S) ~ v(empty) + sum_{j in S} phi_j (the quantity that drives KernelSHAP sampling noise)."""
    d = int(np.log2(len(table)))
    M = all_masks(d)
    s = M.sum(1)
    keep = (s > 0) & (s < d)
    w = np.array([(d - 1) / (comb(d, k) * k * (d - k)) if 0 < k < d else 0.0 for k in range(d + 1)])[s]
    y = table - table[0]
    add = M @ phi
    num = np.sum(w[keep] * (y[keep] - add[keep]) ** 2)
    den = np.sum(w[keep] * y[keep] ** 2)
    return float(num / den) if den > 0 else 0.0


# --------------------------------------------------------------------------- estimators


@lru_cache(maxsize=None)
def _enum_plan(d, nsamples):
    """deterministic part of shap's KernelExplainer allocation: fully enumerated size strata."""
    n_sizes = int(np.ceil((d - 1) / 2.0))
    n_paired = int(np.floor((d - 1) / 2.0))
    wv = np.array([(d - 1.0) / (i * (d - i)) for i in range(1, n_sizes + 1)])
    wv[:n_paired] *= 2
    wv /= wv.sum()
    rem = wv.copy()
    n_full = 0
    left = nsamples
    masks, weights = [], []
    for size in range(1, n_sizes + 1):
        nsub = comb(d, size)
        if size <= n_paired:
            nsub *= 2
        if left * rem[size - 1] / nsub >= 1.0 - 1e-8:
            n_full += 1
            left -= nsub
            if rem[size - 1] < 1.0:
                rem = rem / (1 - rem[size - 1])
            w = wv[size - 1] / comb(d, size)
            if size <= n_paired:
                w /= 2.0
            for idx in combinations(range(d), size):
                mk = np.zeros(d, dtype=bool)
                mk[list(idx)] = True
                masks.append(mk); weights.append(w)
                if size <= n_paired:
                    masks.append(~mk); weights.append(w)
        else:
            break
    fm = np.array(masks).reshape(-1, d)
    return n_sizes, n_paired, wv, n_full, left, fm, np.array(weights)


def _kernel_plan(d, nsamples, rng):
    """returns masks (m,d) bool and weights (m,) following shap.KernelExplainer's allocation."""
    nsamples = min(nsamples, 2 ** d - 2)
    n_sizes, n_paired, wv, n_full, left, fm, fw = _enum_plan(d, nsamples)
    masks, weights = [fm], [fw]
    if n_full != n_sizes and left > 0:
        rw = wv.copy()
        rw[:n_paired] /= 2
        rw = rw[n_full:]
        rw /= rw.sum()
        ind = rng.choice(len(rw), 4 * left, p=rw)
        pos = 0
        used = {}
        rnd_masks, rnd_w = [], []
        while left > 0 and pos < len(ind):
            size = ind[pos] + n_full + 1
            pos += 1
            mk = np.zeros(d, dtype=bool)
            mk[rng.permutation(d)[:size]] = True
            key = mk.tobytes()
            new = False
            if key not in used:
                new = True
                used[key] = len(rnd_masks)
                left -= 1
                rnd_masks.append(mk); rnd_w.append(1.0)
            else:
                rnd_w[used[key]] += 1.0
            if left > 0 and size <= n_paired:
                cm = ~mk
                if new:
                    left -= 1
                    rnd_masks.append(cm); rnd_w.append(1.0)
                else:
                    rnd_w[used[key] + 1] += 1.0
        rnd_w = np.array(rnd_w)
        rnd_w *= wv[n_full:].sum() / rnd_w.sum()
        masks.append(np.array(rnd_masks)); weights.append(rnd_w)
    return np.concatenate(masks), np.concatenate(weights)


def kernel_shap(vfun, d, v_null, v_x, nsamples, rng):
    masks, w = _kernel_plan(d, nsamples, rng)
    y = vfun(masks) - v_null
    Mf = masks.astype(float)
    last = Mf[:, -1]
    ya = y - last * (v_x - v_null)
    et = Mf[:, :-1] - last[:, None]
    A = et.T @ (et * w[:, None])
    b = et.T @ (w * ya)
    try:
        phi_ = np.linalg.solve(A, b)
    except np.linalg.LinAlgError:
        phi_ = np.linalg.lstsq(A, b, rcond=None)[0]
    phi = np.empty(d)
    phi[:-1] = phi_
    phi[-1] = (v_x - v_null) - phi_.sum()
    return phi, len(masks)


def perm_shap(vfun, d, v_null, v_x, budget, rng, return_pairs=False):
    """Antithetic permutation sampling (forward + reversed path), as in shap.PermutationExplainer.
    One pair costs 2(d-1) distinct coalition evaluations."""
    n_pairs = max(1, budget // (2 * (d - 1)))
    perms = np.argsort(rng.random((n_pairs, d)), axis=1)  # (n,d)
    # forward sets S_k = first k elements, k=1..d-1 ; reverse sets T_k = last k elements
    ar = np.arange(d)
    rank = np.empty_like(perms)
    np.put_along_axis(rank, perms, np.broadcast_to(ar, perms.shape), axis=1)  # rank[p, j] = position of j
    ks = np.arange(1, d)
    fwd = rank[:, None, :] < ks[None, :, None]            # (n, d-1, d)
    rev = rank[:, None, :] >= (d - ks)[None, :, None]     # (n, d-1, d)
    allm = np.concatenate([fwd, rev], axis=1).reshape(-1, d)
    vals = vfun(allm).reshape(n_pairs, 2, d - 1)
    vf = np.concatenate([np.full((n_pairs, 1), v_null), vals[:, 0], np.full((n_pairs, 1), v_x)], axis=1)  # (n, d+1)
    vr = np.concatenate([np.full((n_pairs, 1), v_null), vals[:, 1], np.full((n_pairs, 1), v_x)], axis=1)
    dfw = np.diff(vf, axis=1)  # contribution of perm element k (position k-1)
    drv = np.diff(vr, axis=1)  # contribution of element perms[:, d-k] at reverse step k
    C = np.zeros((n_pairs, d))
    np.put_along_axis(C, perms, dfw, axis=1)
    Cr = np.zeros((n_pairs, d))
    np.put_along_axis(Cr, perms[:, ::-1], drv, axis=1)
    pair = 0.5 * (C + Cr)
    phi = pair.mean(0)
    if return_pairs:
        return phi, n_pairs * 2 * (d - 1), pair
    return phi, n_pairs * 2 * (d - 1)


# --------------------------------------------------------------------------- metrics


def _order(phi):
    return np.argsort(-np.abs(phi), axis=-1, kind="stable")


def _rank(order):
    r = np.empty_like(order)
    np.put_along_axis(r, order, np.broadcast_to(np.arange(order.shape[-1]), order.shape), axis=-1)
    return r


def _rbo(posA, posB, p=0.9):
    d = posA.shape[-1]
    mx = np.maximum(posA, posB)  # (P,d)
    X = np.stack([(mx < i).sum(-1) for i in range(1, d + 1)], axis=-1)  # (P,d)
    i = np.arange(1, d + 1)
    return X[:, -1] / d * p ** d + (1 - p) / p * np.sum(X / i * p ** i, axis=-1)


def _tau(ra, rb):
    d = ra.shape[-1]
    iu = np.triu_indices(d, 1)
    sa = np.sign(ra[:, iu[0]] - ra[:, iu[1]])
    sb = np.sign(rb[:, iu[0]] - rb[:, iu[1]])
    return (sa * sb).mean(-1)


def pair_metrics(PA, PB, k=3):
    """metrics between matched attribution vectors PA, PB of shape (P,d)."""
    oa, ob = _order(PA), _order(PB)
    ra, rb = _rank(oa), _rank(ob)
    out = {}
    out["top1"] = (oa[:, 0] == ob[:, 0]).astype(float)
    for kk in (k, 5):
        if kk <= PA.shape[1]:
            A, B = ra < kk, rb < kk
            inter = (A & B).sum(-1)
            out[f"jac{kk}"] = inter / (2 * kk - inter)
            if kk == k:
                out[f"same{kk}"] = (inter == kk).astype(float)
    out["rbo"] = _rbo(ra, rb)
    out["tau"] = _tau(ra, rb)
    out["rel_l2"] = np.linalg.norm(PA - PB, axis=-1) / (0.5 * (np.linalg.norm(PA, axis=-1) + np.linalg.norm(PB, axis=-1)) + 1e-12)
    # sign consistency among features that are in the top-k of both
    A, B = ra < k, rb < k
    both = A & B
    agree = (np.sign(PA) == np.sign(PB)) & both
    out["sign_k"] = np.where(both.sum(-1) > 0, agree.sum(-1) / np.maximum(both.sum(-1), 1), np.nan)
    return out


def nogueira(sel):
    """Nogueira et al. (2018) stability of a (R,d) binary selection matrix."""
    R, d = sel.shape
    pf = sel.mean(0)
    kbar = sel.sum(1).mean()
    var = (R / (R - 1)) * pf * (1 - pf)
    return 1 - var.mean() / ((kbar / d) * (1 - kbar / d))
