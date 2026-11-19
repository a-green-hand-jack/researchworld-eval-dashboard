"""Reliability metrics for attribution vectors. Arrays are phi[N, R, d] (instances x repeated runs x features)
and targets t[N, d]. Rankings are by |phi| (magnitude of attribution). Every metric is named so that higher =
more reliable unless the name ends in `_err` / `_dist` (lower = more reliable)."""
import numpy as np
from scipy.stats import rankdata

EPS = 1e-12


def topk_mask(a, k):
    """Boolean mask of the k largest |a| along the last axis (stable tie-break by feature index)."""
    order = np.argsort(-np.abs(a), axis=-1, kind="stable")
    m = np.zeros(a.shape, bool)
    np.put_along_axis(m, order[..., :k], True, axis=-1)
    return m


def rank_positions(a):
    """Position (0 = largest |a|) of every feature in the |a| ranking, stable tie-break."""
    order = np.argsort(-np.abs(a), axis=-1, kind="stable")
    pos = np.empty_like(order)
    np.put_along_axis(pos, order, np.arange(a.shape[-1]).reshape([1] * (a.ndim - 1) + [-1]), axis=-1)
    return pos


def _corr(a, b):
    a = a - a.mean(-1, keepdims=True); b = b - b.mean(-1, keepdims=True)
    return (a * b).sum(-1) / np.maximum(np.sqrt((a * a).sum(-1) * (b * b).sum(-1)), EPS)


def rbo_from_positions(pa, pb, p=0.9):
    """Extrapolated RBO (Webber et al. 2010, eq. 32) for two complete rankings of the same d items; pa, pb are
    rank positions [..., d]. Persistence p=0.9 puts ~65% of the weight on the top 10."""
    d = pa.shape[-1]
    m = np.maximum(pa, pb)  # item is in both top-k lists iff max position < k
    ks = np.arange(1, d + 1)
    X = (m[..., None, :] < ks[:, None]).sum(-1)  # [..., d] overlap at depth k
    A = X / ks
    w = p ** (ks - 1)
    return (1 - p) * (A * w).sum(-1) + A[..., -1] * p ** d  # complete lists: tail extrapolated from A_d


def pairwise(phi, ks=(1, 3, 5), rbo_p=0.9):
    """Pairwise (run a vs run b) repeatability metrics. Returns dict name -> [N, R, R]."""
    N, R, d = phi.shape
    out = {}
    ar = np.abs(phi)
    rk = np.stack([rankdata(-x, axis=-1) for x in ar.transpose(1, 0, 2)], 1)  # average ranks [N,R,d]
    rkc = rk - rk.mean(-1, keepdims=True)
    num = np.einsum("nad,nbd->nab", rkc, rkc)
    den = np.sqrt((rkc ** 2).sum(-1))
    out["spearman_abs"] = num / np.maximum(den[:, :, None] * den[:, None, :], EPS)
    for k in ks:
        if k > d: continue
        m = topk_mask(phi, k).astype(float)
        inter = np.einsum("nad,nbd->nab", m, m)
        out[f"top{k}_jaccard"] = inter / (2 * k - inter)
    pos = rank_positions(phi)
    rbo = np.empty((N, R, R))
    for a in range(R):
        rbo[:, a, :] = rbo_from_positions(pos[:, a:a + 1, :], pos, rbo_p)
    out["rbo"] = rbo
    # sign agreement on the top-3 features (Krishna et al.): fraction of run a's top-3 features whose sign equals that in run b
    k3 = topk_mask(phi, 3)
    sg = np.sign(phi)
    same = (sg[:, :, None, :] == sg[:, None, :, :])  # [N,a,b,d]
    sa = (same & k3[:, :, None, :]).sum(-1) / 3.0
    out["sign_top3"] = 0.5 * (sa + sa.transpose(0, 2, 1))
    # normalised L2 distance between runs (lower = more reliable)
    diff = np.linalg.norm(phi[:, :, None, :] - phi[:, None, :, :], axis=-1)
    nrm = np.linalg.norm(phi, axis=-1)
    out["rel_l2_pair_dist"] = diff / np.maximum(0.5 * (nrm[:, :, None] + nrm[:, None, :]), EPS)
    return out


def versus_target(phi, t, ks=(1, 3, 5)):
    """Single-run metrics against the exact/converged target t[N,d]. Returns dict name -> [N, R]."""
    N, R, d = phi.shape
    out = {}
    tn = np.linalg.norm(t, axis=-1)[:, None]
    out["rel_l2_err"] = np.linalg.norm(phi - t[:, None, :], axis=-1) / np.maximum(tn, EPS)
    out["max_abs_err_over_scale"] = np.abs(phi - t[:, None, :]).max(-1) / np.maximum(np.abs(t).max(-1)[:, None], EPS)
    tr = np.stack([rankdata(-x) for x in np.abs(t)])  # [N,d]
    pr = np.stack([rankdata(-x, axis=-1) for x in np.abs(phi).transpose(1, 0, 2)], 1)
    out["spearman_abs_target"] = _corr(pr, tr[:, None, :])
    tm = {k: topk_mask(t, k) for k in ks if k <= d}
    for k, m in tm.items():
        out[f"top{k}_hit"] = (topk_mask(phi, k) & m[:, None, :]).sum(-1) / k
    out["top3_exact_order"] = (np.argsort(-np.abs(phi), -1, kind="stable")[..., :3] ==
                               np.argsort(-np.abs(t), -1, kind="stable")[:, None, :3]).all(-1).astype(float)
    sg = np.sign(phi) == np.sign(t)[:, None, :]
    out["sign_top3_target"] = (sg & tm[3][:, None, :]).sum(-1) / 3.0
    out["sign_all_target"] = sg.mean(-1)
    return out


def gap_to_noise(phi, t, jmax=10):
    """For adjacent ranks j,j+1 of the target |t|: gap, SD over runs of the difference of the two |phi| values,
    ratio, and the fraction of runs reproducing the order of the pair. Arrays [N, jmax]."""
    N, R, d = phi.shape
    jmax = min(jmax, d - 1)
    order = np.argsort(-np.abs(t), -1, kind="stable")
    at = np.abs(t); ap_ = np.abs(phi)
    gap = np.empty((N, jmax)); sd = np.empty((N, jmax)); ok = np.empty((N, jmax))
    for j in range(jmax):
        f1, f2 = order[:, j], order[:, j + 1]
        i = np.arange(N)
        gap[:, j] = at[i, f1] - at[i, f2]
        dif = ap_[i, :, f1] - ap_[i, :, f2]  # [N,R]
        sd[:, j] = dif.std(1, ddof=1)
        ok[:, j] = (dif > 0).mean(1)
    return gap, sd, gap / np.maximum(sd, EPS), ok
