"""Agreement metrics between attribution vectors (row-wise, vectorised). Inputs A,B: (n,d) arrays."""
import numpy as np


def _rank_desc(abs_phi):
    # rank 0 = largest |phi|; ties broken by index (stable)
    order = np.argsort(-abs_phi, axis=1, kind="stable")
    rank = np.empty_like(order)
    np.put_along_axis(rank, order, np.arange(abs_phi.shape[1])[None, :].repeat(abs_phi.shape[0], 0), axis=1)
    return rank


def topk_sets(A, k):
    r = _rank_desc(np.abs(A))
    return r < k  # boolean (n,d)


def jaccard_topk(A, B, k):
    a, b = topk_sets(A, k), topk_sets(B, k)
    inter = (a & b).sum(1); union = (a | b).sum(1)
    return inter / union


def top1_agree(A, B):
    return (np.argmax(np.abs(A), 1) == np.argmax(np.abs(B), 1)).astype(float)


def rbo_ext(A, B, p=0.9, depth=None):
    """Rank-biased overlap (Webber et al. 2010), extrapolated form, on |phi| rankings of equal length.
    depth<d truncates the evaluation depth (used for large d)."""
    n, d = A.shape
    k = d if depth is None else min(depth, d)
    ra, rb = _rank_desc(np.abs(A)), _rank_desc(np.abs(B))
    s = np.zeros(n); X = None
    for i in range(1, k + 1):
        X = ((ra < i) & (rb < i)).sum(1)
        s += (X / i) * p ** i
    return (1 - p) / p * s + (X / k) * p ** k


def spearman(A, B):
    def rk(M):
        return np.argsort(np.argsort(M, 1, kind="stable"), 1).astype(float)
    ra, rb = rk(A), rk(B)
    ra -= ra.mean(1, keepdims=True); rb -= rb.mean(1, keepdims=True)
    den = np.sqrt((ra ** 2).sum(1) * (rb ** 2).sum(1))
    return (ra * rb).sum(1) / np.maximum(den, 1e-12)


def sign_agree_topk(A, B, k):
    """Among the top-k (by |.|) features of B, fraction whose sign in A equals the sign in B."""
    b = topk_sets(B, k)
    same = (np.sign(A) == np.sign(B))
    return (same & b).sum(1) / k


def rel_l2(A, B_ref):
    return np.linalg.norm(A - B_ref, axis=1) / np.maximum(np.linalg.norm(B_ref, axis=1), 1e-12)


def all_metrics(A, B, k=3, rbo_depth=None):
    return dict(top1=top1_agree(A, B), jac=jaccard_topk(A, B, k), rbo=rbo_ext(A, B, depth=rbo_depth),
                spear=spearman(A, B), sign=sign_agree_topk(A, B, k))
