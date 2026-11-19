"""Core library: select-then-report simulation on a (K configs x N questions) 0/1 correctness matrix.

Selection procedure: draw n selection questions, pick argmax-mean config (random tie-break).
'Truth' for real data = mean of the selected config on the N-n held-out questions (fresh-question proxy).
Estimators of the selected config's accuracy on fresh questions:
  naive, holdout, cv (cross-fitted), boot (Efron-Tibshirani optimism correction), eb (empirical-Bayes
  shrinkage of the winner toward the config-mean), and intervals: wilson (naive), simult (max-t bootstrap).
"""
import numpy as np
from scipy import stats

Z = 1.959964


def argmax_tb(m, rng):
    mx = m.max(-1, keepdims=True)
    ties = (m >= mx - 1e-12)
    noise = rng.random(m.shape)
    return np.argmax(np.where(ties, noise, -1), axis=-1)


def wilson(p, n, z=Z):
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * np.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return c - h, c + h


def eb_estimate(Ssel):
    """Empirical-Bayes: m_bar + lam*(m_k - m_bar) for the winner. lam from method-of-moments
    using paired (deviation-from-config-mean) variance.  Returns (estimate, k_hat, lam)."""
    K, n = Ssel.shape
    m = Ssel.mean(1)
    mbar = m.mean()
    dev = Ssel - Ssel.mean(0, keepdims=True)  # per-question deviation from mean over configs
    # sampling variance of d_k = m_k - mbar : Var_q(dev_kq)/n
    s2 = dev.var(1, ddof=1) / n
    d = m - mbar
    tau2 = max(0.0, (d ** 2).sum() / max(K - 1, 1) - s2.mean())
    lam = tau2 / (tau2 + s2.mean()) if (tau2 + s2.mean()) > 0 else 0.0
    return mbar + lam * d, lam


def one_replicate(S, n, Kc, rng, **kw):
    """S: KxN matrix. Draw Kc configs, n selection questions; truth = held-out mean."""
    K, N = S.shape
    cfg = rng.choice(K, Kc, replace=False) if Kc < K else np.arange(K)
    perm = rng.permutation(N)
    si, hi = perm[:n], perm[n:]
    Ssel = S[np.ix_(cfg, si)].astype(np.float64)
    Shold = S[np.ix_(cfg, hi)].astype(np.float64)
    truth_all = Shold.mean(1)
    tv = truth_all * (1 - truth_all) / len(hi)
    return estimate(Ssel, rng, truth_all, tv, **kw)


def estimate(Ssel, rng, truth_all, tvar_all, B=200, F=5, hold_frac=0.5, do_boot=True):
    """Ssel: Kc x n selection data; truth_all: per-config target; tvar_all: variance of target proxy."""
    Kc, n = Ssel.shape
    m = Ssel.mean(1)
    k = int(argmax_tb(m, rng))
    out = {}
    out["truth"] = truth_all[k]
    out["truth_var"] = tvar_all[k]
    out["best_truth"] = truth_all.max()
    out["mean_truth"] = truth_all.mean()
    out["naive"] = m[k]
    lo, hi_ = wilson(m[k], n)
    out["naive_lo"], out["naive_hi"] = lo, hi_
    nh = int(round(n * hold_frac)); ns = n - nh
    if ns >= 2 and nh >= 2:
        k2 = int(argmax_tb(Ssel[:, :ns].mean(1), rng))
        e = Ssel[k2, ns:].mean()
        out["hold"] = e; out["hold_truth"] = truth_all[k2]; out["hold_truth_var"] = tvar_all[k2]
        l, h = wilson(e, nh); out["hold_lo"], out["hold_hi"] = l, h
    if n >= F * 2 and Kc > 1:
        folds = np.array_split(np.arange(n), F)
        ests, tr = [], []
        for f in folds:
            tr_i = np.setdiff1d(np.arange(n), f)
            kk = int(argmax_tb(Ssel[:, tr_i].mean(1), rng))
            ests.append(Ssel[kk, f].mean()); tr.append(truth_all[kk])
        out["cv"] = float(np.mean(ests)); out["cv_proc_truth"] = float(np.mean(tr))
        out["cv_lo"], out["cv_hi"] = wilson(out["cv"], n)
    else:
        out["cv"] = m[k]; out["cv_proc_truth"] = truth_all[k]; out["cv_lo"], out["cv_hi"] = lo, hi_
    if Kc > 2:
        eb, lam = eb_estimate(Ssel)
        out["eb"] = eb[k]; out["eb_lam"] = lam
    else:
        out["eb"] = m[k]; out["eb_lam"] = 1.0
    seb = np.sqrt(m[k] * (1 - m[k]) / n)
    out["eb_lo"], out["eb_hi"] = out["eb"] - Z * seb, out["eb"] + Z * seb
    if do_boot and Kc > 1:
        W = rng.multinomial(n, np.ones(n) / n, size=B).T.astype(np.float64)
        mb = Ssel @ W / n
        kb = argmax_tb(mb.T, rng)
        in_boot = mb[kb, np.arange(B)]
        opt = (in_boot - m[kb]).mean()
        out["boot"] = m[k] - opt
        out["boot_opt"] = opt
        oob = []
        for b in range(min(B, 100)):
            msk = W[:, b] == 0
            if msk.sum() > 0:
                oob.append(Ssel[kb[b], msk].mean())
        out["b632"] = 0.368 * m[k] + 0.632 * float(np.mean(oob))
        se = np.sqrt(np.maximum(m * (1 - m), 1e-6) / n)
        t = np.abs(mb - m[:, None]) / se[:, None]
        c = np.quantile(t.max(0), 0.95)
        out["sim_lo"], out["sim_hi"] = m[k] - c * se[k], m[k] + c * se[k]
        out["sim_c"] = c
        out["boot_lo"], out["boot_hi"] = out["boot"] - Z * seb, out["boot"] + Z * seb
    else:
        out["boot"] = m[k]; out["b632"] = m[k]; out["boot_opt"] = 0.0
        out["sim_lo"], out["sim_hi"] = lo, hi_; out["sim_c"] = Z
        out["boot_lo"], out["boot_hi"] = lo, hi_
    return out


def cover(lo, hi, truth, tv):
    """predictive coverage: interval widened in quadrature by the held-out proxy's own sampling noise."""
    c = (lo + hi) / 2; hw = (hi - lo) / 2
    hw2 = np.sqrt(hw ** 2 + Z ** 2 * tv)
    return (np.abs(truth - c) <= hw2)
