"""Agreement / error metrics between attribution vectors (all vectorised over runs)."""
import numpy as np


def rank_pos(a):
    """position (0 = most important) of each feature when sorting |a| descending. a: (n, d)"""
    order = np.argsort(-np.abs(a), axis=-1, kind="stable")
    pos = np.empty_like(order)
    n, d = order.shape
    pos[np.arange(n)[:, None], order] = np.arange(d)[None, :]
    return pos


def topk_mask(a, k):
    return rank_pos(a) < k


def rbo_ext(posA, posB, p=0.9):
    """Rank-biased overlap (Webber et al. 2010), extrapolated, for two full rankings of the same d items."""
    n, d = posA.shape
    m = np.maximum(posA, posB)  # item is in both top-k lists iff m < k
    ks = np.arange(1, d + 1)
    X = (m[:, :, None] < ks[None, None, :]).sum(1)  # (n, d): overlap at depth k
    term = (X / ks[None, :]) * p ** ks[None, :]
    return X[:, -1] / d * p ** d + (1 - p) / p * term.sum(1)


def pair_metrics(A, B, k=3, p=0.9):
    """Agreement between corresponding rows of A and B (n,d): top-1 identity, top-k set equality, top-k Jaccard,
    Spearman of |.|, RBO, cosine, relative L2 difference."""
    pa, pb = rank_pos(A), rank_pos(B)
    top1 = (pa == 0).argmax(1) == (pb == 0).argmax(1)
    ma, mb = pa < k, pb < k
    inter = (ma & mb).sum(1)
    setok = inter == k
    jac = inter / (2 * k - inter)
    d = A.shape[1]
    sp = 1 - 6 * ((pa - pb) ** 2).sum(1) / (d * (d * d - 1))
    rbo = rbo_ext(pa, pb, p)
    cos = (A * B).sum(1) / (np.linalg.norm(A, axis=1) * np.linalg.norm(B, axis=1) + 1e-12)
    rel = np.linalg.norm(A - B, axis=1) / (np.linalg.norm(B, axis=1) + 1e-12)
    return dict(top1=top1.astype(np.float32), topk=setok.astype(np.float32), jac=jac.astype(np.float32),
                spear=sp.astype(np.float32), rbo=rbo.astype(np.float32), cos=cos.astype(np.float32),
                rel=rel.astype(np.float32))


def vs_truth(Phi, phi, k=3, p=0.9):
    """Phi: (n,d) estimates, phi: (d,) exact."""
    n = Phi.shape[0]
    out = pair_metrics(Phi, np.repeat(phi[None, :], n, 0), k, p)
    t = rank_pos(phi[None, :])[0] < k
    out["sign"] = (np.sign(Phi[:, t]) == np.sign(phi[t])[None, :]).mean(1).astype(np.float32)
    return out


def nogueira(sel):
    """Stability of feature selection (Nogueira, Sechidis & Brown 2018). sel: (M, d) boolean selection matrix."""
    M, d = sel.shape
    pf = sel.mean(0)
    kbar = sel.sum(1).mean()
    s2 = M / (M - 1) * pf * (1 - pf)
    denom = kbar / d * (1 - kbar / d)
    return 1 - s2.mean() / denom if denom > 0 else np.nan


def self_agreement(Phi, k=3, npairs=200, rng=None):
    """Agreement between independent runs on the same instance: random pairs of distinct runs."""
    rng = rng or np.random.default_rng(0)
    n = Phi.shape[0]
    i = rng.integers(0, n, npairs); j = (i + rng.integers(1, n, npairs)) % n
    return pair_metrics(Phi[i], Phi[j], k)
