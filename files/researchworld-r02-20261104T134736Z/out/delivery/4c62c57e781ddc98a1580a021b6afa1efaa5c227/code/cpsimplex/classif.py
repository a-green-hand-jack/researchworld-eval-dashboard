"""Conformal prediction sets from probability vectors (LAC / APS / RAPS / Mondrian-LAC)."""
import numpy as np
from .conformal import conformal_quantile


def label_scores(P, method, u=None, lam=0.01, kreg=5):
    """Matrix S[i,k] = score of sample i if its label were k.  P: (n,K) probability vectors."""
    n, K = P.shape
    if method == "lac":
        return 1.0 - P
    order = np.argsort(-P, axis=1, kind="stable")
    Ps = np.take_along_axis(P, order, 1)
    cs = np.cumsum(Ps, 1)
    rank = np.empty_like(order); np.put_along_axis(rank, order, np.arange(K)[None, :].repeat(n, 0), 1)  # rank[i,k]=position of class k
    cum_incl = np.take_along_axis(cs, rank, 1)          # mass of classes up to and including k
    if method == "aps":
        return cum_incl - u[:, None] * P                  # randomised: u~U(0,1)
    if method == "raps":
        pen = lam * np.maximum(rank + 1 - kreg, 0)
        return cum_incl - u[:, None] * P + pen
    raise ValueError(method)


def split_sets(Pc, yc, Pt, method, alpha, rng, **kw):
    """Calibrate on (Pc,yc); return boolean set matrix for Pt (n_t,K), and threshold."""
    uc, ut = rng.uniform(size=len(Pc)), rng.uniform(size=len(Pt))
    Sc = label_scores(Pc, method, uc, **kw)[np.arange(len(Pc)), yc]
    q = conformal_quantile(Sc, alpha)
    return label_scores(Pt, method, ut, **kw) <= q, q


def mondrian_sets(Pc, yc, Pt, alpha, rng=None):
    """Class-conditional LAC: separate threshold per true class."""
    K = Pc.shape[1]
    S = 1.0 - Pt
    out = np.zeros_like(S, dtype=bool)
    for k in range(K):
        s = 1.0 - Pc[yc == k, k]
        q = conformal_quantile(s, alpha)
        out[:, k] = S[:, k] <= q
    return out
