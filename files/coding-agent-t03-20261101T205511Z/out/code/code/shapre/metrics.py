"""Agreement metrics between attribution vectors. Ranking is by |phi| (magnitude of contribution)."""
import numpy as np
from scipy.stats import spearmanr


def topk(a, k):
    return np.argsort(-np.abs(a), kind="stable")[:k]


def rank_order(a):
    return np.argsort(-np.abs(a), kind="stable")


def jaccard_topk(a, b, k):
    A, B = set(topk(a, k)), set(topk(b, k))
    return len(A & B) / len(A | B)


def same_topk_set(a, b, k):
    return float(set(topk(a, k)) == set(topk(b, k)))


def same_top1(a, b):
    return float(topk(a, 1)[0] == topk(b, 1)[0])


def rbo_ext(a, b, p=0.9, depth=10):
    """Rank-biased overlap, extrapolated (Webber et al. 2010, Eq. 32) of the |phi| rankings truncated to `depth`."""
    k = min(depth, len(a))
    ra, rb = rank_order(a)[:k], rank_order(b)[:k]
    ov = np.array([len(set(ra[:d]) & set(rb[:d])) for d in range(1, k + 1)])
    ds = np.arange(1, k + 1)
    return float((ov[-1] / k) * p ** k + (1 - p) / p * np.sum(p ** ds * ov / ds))


def sign_agree_topk(a, ref, k):
    """fraction of the reference's top-k features whose sign in a matches."""
    t = topk(ref, k)
    return float(np.mean(np.sign(a[t]) == np.sign(ref[t])))


def mass_recall(a, ref, k):
    """sum |ref| over a's top-k divided by sum |ref| over ref's top-k (tie-robust top-k quality, in [0,1])."""
    return np.abs(ref[topk(a, k)]).sum() / max(np.abs(ref[topk(ref, k)]).sum(), 1e-300)


def rel_l2(a, ref):
    return np.linalg.norm(a - ref) / max(np.linalg.norm(ref), 1e-300)


def cosine(a, b):
    return float(a @ b / max(np.linalg.norm(a) * np.linalg.norm(b), 1e-300))


def spearman_abs(a, b):
    if np.allclose(np.abs(a), np.abs(a)[0]) or np.allclose(np.abs(b), np.abs(b)[0]):
        return np.nan
    return spearmanr(np.abs(a), np.abs(b))[0]


def nogueira_topk(Phis, k):
    """Nogueira et al. (2018) stability of the top-k selection over R runs (Phis: R x d)."""
    R, d = Phis.shape
    S = np.zeros((R, d))
    for r in range(R):
        S[r, topk(Phis[r], k)] = 1
    pf = S.mean(0)
    kbar = S.sum(1).mean()
    var = R / (R - 1) * pf * (1 - pf)
    denom = (kbar / d) * (1 - kbar / d)
    return 1 - var.mean() / denom


def pairs(R):
    return [(i, j) for i in range(R) for j in range(i + 1, R)]


def pairwise(Phis, fn):
    return float(np.mean([fn(Phis[i], Phis[j]) for i, j in pairs(len(Phis))]))
