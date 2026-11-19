"""E5: in-run certificates for the top-k set, audited on the exact tables.

One rerun = one stream of Covert-Lee antithetic pairs (unbiased KernelSHAP). A *stage* uses the first n_s pairs, so that
stage s is exactly what a deployer who stopped after N_s coalitions would hold. At each stage and each k we store the
run's p-value-like statistic under every certificate rule (the smallest level delta at which the rule would certify),
and whether the run's top-k set is correct. Sequential rules (stop at the first certified stage, optional-stopping
corrections) are then evaluated afterwards for any delta from these stored arrays, so one pass serves every delta.

Rules (all about the set T = top-k of |phi_hat|; pairs (i in T, j not in T); a_i = |phi_i|):
  naive     boundary pair only (weakest member vs strongest outsider), one-sided z test at level delta  [winner's-curse-prone]
  bonf      all k(d-k) pairs, Bonferroni
  maxt      all pairs, simultaneous max-t critical value from the run's own estimated covariance
  split     T chosen on the first half of the pairs, tested (maxt) on the second half   [independent of the selection]
  shapk     SHAP@k-style overlap stopping (Kariyappa et al.): per-attribute CI at level delta/d (two-sided), certify when
            the lowest lower bound in T is above the highest upper bound outside T (epsilon = 0)
"""
import numpy as np
from scipy.stats import norm
from . import estimators as E
from .metrics import exact_topk, eps_topk

STAGE_MULTS = [0.25, 0.5, 1, 2, 4, 8, 16]
RULES = ["naive", "bonf", "maxt", "split", "shapk"]
KS = (1, 3, 5)
NSIM = 400


def _pairs(T):
    inn = np.where(T)[0]; out = np.where(~T)[0]
    I, J = np.meshgrid(inn, out, indexing="ij")
    return I.ravel(), J.ravel()


def _chol(cov):
    try:
        return np.linalg.cholesky(cov + 1e-14 * np.eye(len(cov)))
    except np.linalg.LinAlgError:
        w, V = np.linalg.eigh(cov)
        return V * np.sqrt(np.clip(w, 0, None))


def _tmin_maxt(phi_sel, phi_test, cov_test, k, Zs, T=None):
    """top-k set T (selected from phi_sel unless given); min pairwise t on the test estimate and its simultaneous max-t p-value."""
    M = len(phi_sel)
    if T is None:
        T = np.zeros(M, bool); T[np.argsort(-np.abs(phi_sel), kind="stable")[:k]] = True
    a = np.abs(phi_test); s = np.where(phi_test >= 0, 1.0, -1.0)
    I, J = _pairs(T)
    se = np.sqrt(np.clip(cov_test[I, I] + cov_test[J, J] - 2 * s[I] * s[J] * cov_test[I, J], 1e-18, None))
    t = (a[I] - a[J]) / se
    W = Zs @ _chol(cov_test).T
    mx = ((s[I] * W[:, I] - s[J] * W[:, J]) / se).max(1)
    p_maxt = float((1 + (mx >= t.min()).sum()) / (len(mx) + 1))
    return T, I, J, t, se, p_maxt


def audit_instance(orc, phi_star, R, rng_seed, stage_mults=STAGE_MULTS, ks=KS, eps=0.1):
    """arrays of shape (R, S, len(ks)): p_<rule> (smallest delta at which the rule certifies), correct / correct_eps (the run's
    top-k set vs exact), correct_split (the half-A set vs exact), set_code (bitmask of the run's set), cost (coalitions per stage)."""
    M = orc.M
    N0 = 2 * orc.d + 2048
    Ns = [int(round(N0 * m)) for m in stage_mults]
    S = len(Ns)
    out = {r: np.full((R, S, len(ks)), np.nan) for r in RULES}
    for nm in ("correct", "correct_eps", "correct_split"):
        out[nm] = np.zeros((R, S, len(ks)), bool)
    out["set_code"] = np.zeros((R, S, len(ks)), np.int64)
    out["cost"] = np.array(Ns)
    if M < 2:
        return out
    Zs = np.random.default_rng(12345).standard_normal((NSIM, M))
    bits = (1 << orc.var_idx.astype(np.int64))
    for r in range(R):
        rng = np.random.default_rng([rng_seed, r])
        masks = E.covert_lee_sample(M, Ns[-1] // 2, rng)
        v = orc(np.concatenate([masks, 1 - masks], 0))
        _, infl = E.covert_lee_from(masks, v, orc.v0, orc.vN, M)           # (npairs, M): mean = phi_hat
        for si, N in enumerate(Ns):
            n = N // 2; h = n // 2
            x = infl[:n]; phi = x.mean(0); cov = np.cov(x.T) / n
            xa, xb = infl[:h], infl[h:2 * h]
            phiA, phiB, covB = xa.mean(0), xb.mean(0), np.cov(xb.T) / h
            full = np.zeros(orc.d); full[orc.var_idx] = phi
            fullA = np.zeros(orc.d); fullA[orc.var_idx] = phiA
            sd = np.sqrt(np.clip(np.diag(cov), 1e-18, None))
            for ki, k in enumerate(ks):
                if k >= M:                                                    # nothing to select: trivially certified
                    for rule in RULES: out[rule][r, si, ki] = 0.0
                    out["correct"][r, si, ki] = out["correct_eps"][r, si, ki] = out["correct_split"][r, si, ki] = True
                    continue
                T, I, J, t, se, p_maxt = _tmin_maxt(phi, phi, cov, k, Zs)
                tmin = t.min()
                out["naive"][r, si, ki] = norm.sf(tmin)
                out["bonf"][r, si, ki] = min(1.0, len(t) * norm.sf(tmin))
                out["maxt"][r, si, ki] = p_maxt
                a = np.abs(phi)
                zneed = ((a[I] - a[J]) / (sd[I] + sd[J])).min()
                out["shapk"][r, si, ki] = min(1.0, M * 2 * norm.sf(zneed))      # delta with z_{1-delta/(2M)} = zneed
                out["correct"][r, si, ki] = bool(exact_topk(full, phi_star, k))
                out["correct_eps"][r, si, ki] = bool(eps_topk(full, phi_star, k, eps))
                out["set_code"][r, si, ki] = int(bits[T].sum())
                # split-half: select on A, test on B
                _, _, _, _, _, p_split = _tmin_maxt(phiA, phiB, covB, k, Zs)
                out["split"][r, si, ki] = p_split
                out["correct_split"][r, si, ki] = bool(exact_topk(fullA, phi_star, k))
    return out
