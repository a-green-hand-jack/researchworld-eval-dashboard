"""Read-outs. phi_hat: (..., d) attribution runs; phi_star: (..., d) exact target (broadcast over the rerun axis).
Ranking is by |phi| (importance); `signed=True` ranks by phi itself (reason codes toward the model output)."""
import numpy as np


def _key(phi, signed):
    return phi if signed else np.abs(phi)


def topk_mask(phi, k, signed=False):
    key = _key(phi, signed)
    idx = np.argsort(-key, axis=-1, kind="stable")[..., :k]
    m = np.zeros(phi.shape, bool)
    np.put_along_axis(m, idx, True, axis=-1)
    return m


def exact_topk(phi_hat, phi_star, k, signed=False):
    return (topk_mask(phi_hat, k, signed) == topk_mask(phi_star, k, signed)).all(-1)


def eps_topk(phi_hat, phi_star, k, eps, signed=False):
    """epsilon-tolerant: the chosen set's weakest member is within eps*(k-th target value) of the strongest excluded feature."""
    key = _key(phi_star, signed)
    T = topk_mask(phi_hat, k, signed)
    big = np.where(T, np.inf, key).min(-1) if False else None
    weakest_in = np.where(T, key, np.inf).min(-1)
    strongest_out = np.where(~T, key, -np.inf).max(-1)
    kth = np.sort(key, -1)[..., ::-1][..., k - 1]
    return (strongest_out - weakest_in) <= eps * np.abs(kth) + 1e-12


def sign_topk(phi_hat, phi_star, k):
    """signs of the target's top-k features are reproduced by the run (sign agreement on the true top-k)."""
    T = topk_mask(phi_star, k)
    ok = np.sign(phi_hat) == np.sign(phi_star)
    return (ok | ~T).all(-1)


def rel_l2(phi_hat, phi_star):
    return np.linalg.norm(phi_hat - phi_star, axis=-1) / (np.linalg.norm(phi_star, axis=-1) + 1e-12)


def rbo(a, b, p=0.9):
    """rank-biased overlap (extrapolated, Webber et al. 2010) between the rankings (by |phi|) of attribution vectors a, b: (..., d)."""
    d = a.shape[-1]
    ra = np.argsort(-np.abs(a), -1, kind="stable"); rb = np.argsort(-np.abs(b), -1, kind="stable")
    # overlap at depth t: |ra[:t] & rb[:t]|
    pa = np.zeros(a.shape, np.int32); pb = np.zeros(b.shape, np.int32)
    np.put_along_axis(pa, ra, np.arange(d, dtype=np.int32)[None] * np.ones_like(ra) if ra.ndim == 1 else np.broadcast_to(np.arange(d, dtype=np.int32), ra.shape), -1)
    np.put_along_axis(pb, rb, np.broadcast_to(np.arange(d, dtype=np.int32), rb.shape), -1)
    mx = np.maximum(pa, pb)                                                     # item enters both lists at depth mx+1
    depth = np.arange(1, d + 1)
    overlap = (mx[..., None, :] < depth[:, None]).sum(-1)                       # (..., d) overlap at each depth
    w = p ** (depth - 1)
    base = ((1 - p) * (overlap / depth * w).sum(-1))
    return base + overlap[..., -1] / d * p ** d


def nogueira(sets):
    """chance-corrected stability of selected sets across reruns. sets: (..., R, d) bool, k = sets.sum(-1) constant.
    Nogueira, Sechidis & Brown (2018): 1 - mean_f var_f / ((k/d)(1-k/d)), var_f = R/(R-1) * pf(1-pf)."""
    R, d = sets.shape[-2:]
    k = sets.sum(-1).mean(-1)
    pf = sets.mean(-2)
    var = (R / (R - 1)) * pf * (1 - pf)
    kd = k / d
    return 1 - var.mean(-1) / (kd * (1 - kd))


def pairwise_jaccard(sets):
    R = sets.shape[-2]
    s = sets.astype(np.float32)
    inter = np.einsum("...rd,...sd->...rs", s, s)
    cnt = s.sum(-1)
    union = cnt[..., :, None] + cnt[..., None, :] - inter
    J = inter / union
    iu = np.triu_indices(R, 1)
    return J[..., iu[0], iu[1]].mean(-1)


def gap(phi_star, k, signed=False):
    key = np.sort(_key(phi_star, signed), -1)[..., ::-1]
    return key[..., k - 1] - key[..., k]


def clopper_pearson(x, n, alpha=0.05):
    from scipy.stats import beta
    lo = np.where(x == 0, 0.0, beta.ppf(alpha / 2, x, n - x + 1))
    hi = np.where(x == n, 1.0, beta.ppf(1 - alpha / 2, x + 1, n - x))
    return lo, hi


def cluster_bootstrap(values, fn=np.mean, B=2000, seed=0):
    """values: (n_clusters, ...) ; resample clusters (instances x model seeds are the clusters). returns (est, lo, hi)."""
    rng = np.random.default_rng(seed)
    n = values.shape[0]
    est = fn(values, axis=0)
    bs = np.stack([fn(values[rng.integers(0, n, n)], axis=0) for _ in range(B)])
    return est, np.percentile(bs, 2.5, axis=0), np.percentile(bs, 97.5, axis=0)
