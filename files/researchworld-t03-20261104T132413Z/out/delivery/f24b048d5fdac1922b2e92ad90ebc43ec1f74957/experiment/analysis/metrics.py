"""Per-instance reliability measures from stored explainer runs (pure functions of arrays).

Notation: runs  P (R, d) attribution vectors of one instance; reference ref (d,).
Ranking is by |attribution| (importance), signs are looked at separately.
"""
import numpy as np
from scipy.stats import kendalltau, rankdata

KS = (1, 3, 5)


def topk_ind(P, k):
    """(R, d) boolean indicator of the k largest-|.| features per row (ties broken by index, irrelevant for continuous values)."""
    P = np.atleast_2d(P)
    idx = np.argsort(-np.abs(P), axis=1, kind="stable")[:, :k]
    out = np.zeros(P.shape, bool)
    np.put_along_axis(out, idx, True, axis=1)
    return out


def pair_matrix(S):
    """overlap counts between all pairs of indicator rows."""
    Sf = S.astype(float)
    return Sf @ Sf.T


def pairwise_set_match(S, k):
    """fraction of distinct run pairs with identical top-k sets, and mean top-k Jaccard."""
    R = len(S)
    O = pair_matrix(S)
    iu = np.triu_indices(R, 1)
    o = O[iu]
    return float((o == k).mean()), float((o / (2 * k - o)).mean())


def nogueira(S, k):
    """Nogueira et al. (2018) stability of the R selected top-k sets (chance corrected)."""
    R, d = S.shape
    p = S.mean(0)
    s2 = R / (R - 1) * p * (1 - p)
    kbar = k
    return float(1 - s2.mean() / ((kbar / d) * (1 - kbar / d))) if 0 < k < d else np.nan


def rbo(a, b, p=0.9):
    """rank-biased overlap of two full rankings (by |.|), truncated at depth d and normalised to [0, 1]."""
    ra = np.argsort(-np.abs(a), kind="stable")
    rb = np.argsort(-np.abs(b), kind="stable")
    d = len(a)
    sa, sb = np.zeros(d, bool), np.zeros(d, bool)
    num, tot = 0.0, 0.0
    for k in range(1, d + 1):
        ia, ib = ra[k - 1], rb[k - 1]
        sa[ia] = True; sb[ib] = True
        num += p ** (k - 1) * (sa & sb).sum() / k
        tot += p ** (k - 1)
    return float(num / tot)


def instance_metrics(P, ref, ks=KS):
    """metrics of R single runs against the reference, plus run-to-run agreement."""
    R, d = P.shape
    out = {}
    nr = np.linalg.norm(ref) + 1e-12
    err = np.linalg.norm(P - ref, axis=1)
    out["relerr_mean"] = float((err / nr).mean())
    out["relerr_med"] = float(np.median(err / nr))
    out["blowup_frac"] = float((err / nr > 10).mean())  # numerically failed runs (singular regression at tiny budgets)
    out["mse"] = float((err ** 2).mean())  # for rmse aggregation / slope fits
    out["ref_norm"] = float(nr)
    out["bias_norm"] = float(np.linalg.norm(P.mean(0) - ref) / nr)
    out["sd_norm"] = float(np.sqrt(P.var(0, ddof=1).sum()) / nr)
    cs = (P @ ref) / (np.linalg.norm(P, axis=1) * nr + 1e-12)
    out["cos_ref"] = float(cs.mean())
    out["kendall_ref"] = float(np.mean([kendalltau(p, ref).statistic for p in P]))
    out["rbo_ref"] = float(np.mean([rbo(p, ref) for p in P]))
    # null: random vector pairs are handled in standards
    for k in ks:
        if k >= d:
            continue
        S = topk_ind(P, k)
        Sr = topk_ind(ref[None], k)[0]
        match = (S == Sr).all(1)
        out[f"match_ref_k{k}"] = float(match.mean())
        out[f"jac_ref_k{k}"] = float(((S & Sr).sum(1) / (2 * k - (S & Sr).sum(1))).mean())
        pm, pj = pairwise_set_match(S, k)
        out[f"pair_match_k{k}"] = pm
        out[f"pair_jac_k{k}"] = pj
        out[f"nogueira_k{k}"] = nogueira(S, k)
        # sign flips among the reference's top-k features
        top = np.where(Sr)[0]
        out[f"signflip_k{k}"] = float((np.sign(P[:, top]) != np.sign(ref[top])).mean())
        # margin of the reference between rank k and k+1 (|phi|), relative to the largest
        a = np.sort(np.abs(ref))[::-1]
        out[f"margin_k{k}"] = float((a[k - 1] - a[k]) / (a[0] + 1e-12))
        out[f"margin_abs_k{k}"] = float(a[k - 1] - a[k])
        # empirical noise on the gap: sd of (|phi_(k)| - |phi_(k+1)|) across runs (ref ordering)
        order = np.argsort(-np.abs(ref))
        gap = np.abs(P[:, order[k - 1]]) - np.abs(P[:, order[k]])
        out[f"gap_sd_k{k}"] = float(gap.std(ddof=1))
    return out


def null_pair_match(refs, k, rng, n=200):
    """top-k set match / jaccard between references of two random distinct instances (null floor)."""
    N, d = refs.shape
    S = topk_ind(refs, k)
    i = rng.randint(0, N, n); j = (i + rng.randint(1, N, n)) % N
    o = (S[i] & S[j]).sum(1)
    return float((o == k).mean()), float((o / (2 * k - o)).mean())


def random_jaccard(d, k):
    """expected Jaccard / exact-match probability for two independent uniformly random k-subsets of d features."""
    from math import comb
    ej = 0.0
    for o in range(0, k + 1):
        p = comb(k, o) * comb(d - k, k - o) / comb(d, k)
        ej += p * (o / (2 * k - o))
    return ej, 1 / comb(d, k)


def boot_ci(x, rng, B=2000, stat=np.mean, alpha=0.05):
    """cluster (instance-level) percentile bootstrap CI of a statistic of a 1d array."""
    x = np.asarray(x, float)
    x = x[~np.isnan(x)]
    if len(x) == 0:
        return (np.nan, np.nan, np.nan)
    idx = rng.randint(0, len(x), (B, len(x)))
    s = stat(x[idx], axis=1)
    return float(stat(x)), float(np.quantile(s, alpha / 2)), float(np.quantile(s, 1 - alpha / 2))
