"""Offline research helpers (NOT used by the RPC entry point ``program.handle``).

Contains: model-level cross-validation (``leave_models_out_cv``), baselines (random subsets, kNN over models),
uncertainty tools (``bootstrap_ci``, paired Wilcoxon), and the synthetic rank-r factor-model theory check
(``synthetic_factor_matrix``, ``theoretical_posterior_error``).

Usage:  python experiments.py [out.json]      (synthetic theory check only; real matrices must be supplied by
the caller as (values, mask) arrays, see ``leave_models_out_cv``). Everything is seeded.
"""
import json
import sys

import numpy as np

try:
    from program import (conditional_gaussian_impute, em_gaussian_covariance,
                         greedy_select_conditional_variance, _build_sigma)
except ImportError:  # pragma: no cover
    from .program import (conditional_gaussian_impute, em_gaussian_covariance,
                          greedy_select_conditional_variance, _build_sigma)


# ---------------------------------------------------------------------------------------------------------
# synthetic theory check
# ---------------------------------------------------------------------------------------------------------
def synthetic_factor_matrix(m, n, r, sigma, missing_rate=0.0, seed=0):
    """Rank-r Gaussian factor model x = L f + sigma eps, f ~ N(0, I_r). Returns X [m, n], mask, true Sigma."""
    rng = np.random.default_rng(seed)
    L = rng.normal(size=(n, r)) / np.sqrt(r)
    f = rng.normal(size=(m, r))
    X = f @ L.T + sigma * rng.normal(size=(m, n))
    mask = rng.random((m, n)) >= missing_rate
    Sigma = L @ L.T + sigma ** 2 * np.eye(n)
    return X, mask, Sigma


def theoretical_posterior_error(Sigma, selected, lam=0.0):
    """Mean per-benchmark posterior variance of the unselected benchmarks:
    tr(Sigma_UU - Sigma_US (Sigma_SS + lam I)^-1 Sigma_SU) / |U|."""
    n = Sigma.shape[0]
    S = np.asarray(selected, dtype=int)
    U = np.setdiff1d(np.arange(n), S)
    Sigma_UU = Sigma[np.ix_(U, U)]
    Sigma_US = Sigma[np.ix_(U, S)]
    Sigma_SS = Sigma[np.ix_(S, S)] + lam * np.eye(len(S))
    post = Sigma_UU - Sigma_US @ np.linalg.solve(Sigma_SS, Sigma_US.T)
    return float(np.trace(post) / len(U))


def synthetic_theory_check(m=400, n=40, r=4, sigma=0.3, ks=(1, 2, 3, 4, 6, 8, 12), n_test=4000, seed=0):
    X, mask, Sigma_true = synthetic_factor_matrix(m, n, r, sigma, 0.0, seed)
    mu, Sig, _, _ = em_gaussian_covariance(X, mask, shrink=0.0)
    Xt, _, _ = synthetic_factor_matrix(n_test, n, r, sigma, 0.0, seed + 1)
    rows = []
    for k in ks:
        sel = greedy_select_conditional_variance(Sig, k, lam=1e-6)
        U = np.setdiff1d(np.arange(n), sel)
        pred = conditional_gaussian_impute(mu, Sig, sel, Xt[:, sel], np.ones((n_test, k), bool), lam=1e-6)
        meas = float(np.mean((pred[:, U] - Xt[:, U]) ** 2))
        rng = np.random.default_rng(seed + k)
        rnd = rng.choice(n, size=k, replace=False)
        rows.append({"k": int(k), "measured_mse_greedy": meas,
                     "theory_mse_greedy": theoretical_posterior_error(Sigma_true, sel),
                     "theory_mse_random_subset": theoretical_posterior_error(Sigma_true, rnd),
                     "noise_floor": sigma ** 2})
    return rows


# ---------------------------------------------------------------------------------------------------------
# baselines
# ---------------------------------------------------------------------------------------------------------
def random_subset_baseline(n, k, rng):
    return [int(j) for j in rng.choice(n, size=k, replace=False)]


def knn_model_impute(Z_train, mask_train, x_obs, obs_mask, selected, n_neighbors=10):
    """kNN over models: average the columns of the nearest training models (distance on commonly observed
    selected columns). x_obs [B, k] standardised, returns [B, N]."""
    sel = np.asarray(selected, dtype=int)
    col_mean = (Z_train * mask_train).sum(0) / np.maximum(mask_train.sum(0), 1)
    out = np.tile(col_mean, (x_obs.shape[0], 1))
    for b in range(x_obs.shape[0]):
        use = obs_mask[b]
        if not use.any():
            continue
        cols = sel[use]
        ok = mask_train[:, cols].all(1)
        if ok.sum() == 0:
            continue
        d = ((Z_train[ok][:, cols] - x_obs[b, use]) ** 2).sum(1)
        nn = np.argsort(d)[:n_neighbors]
        Zn, Mn = Z_train[ok][nn], mask_train[ok][nn]
        out[b] = np.where(Mn.any(0), (Zn * Mn).sum(0) / np.maximum(Mn.sum(0), 1), col_mean)
    return out


# ---------------------------------------------------------------------------------------------------------
# uncertainty
# ---------------------------------------------------------------------------------------------------------
def bootstrap_ci(values, n_boot=2000, alpha=0.05, seed=0):
    values = np.asarray(values, dtype=float)
    rng = np.random.default_rng(seed)
    idx = rng.integers(0, len(values), size=(n_boot, len(values)))
    means = values[idx].mean(1)
    return float(values.mean()), float(np.quantile(means, alpha / 2)), float(np.quantile(means, 1 - alpha / 2))


def paired_wilcoxon(a, b):
    from scipy.stats import wilcoxon
    d = np.asarray(a) - np.asarray(b)
    if np.allclose(d, 0):
        return 1.0
    return float(wilcoxon(a, b).pvalue)


# ---------------------------------------------------------------------------------------------------------
# model-level cross-validation on a real (values, mask) matrix
# ---------------------------------------------------------------------------------------------------------
def leave_models_out_cv(values, mask, k, n_folds=5, n_repeats=2, seed=0, lam=0.05, shrink=0.05):
    """Repeated K-fold over MODELS. Standardisation, EM covariance and selection use training models only; a
    held-out model reveals only its k selected benchmarks (those it has). Returns per-model MSE (standardised
    units) for greedy+Gaussian, random+Gaussian, and kNN-model baselines on identical folds."""
    m, n = values.shape
    res = {"greedy": [], "random": [], "knn": []}
    for rep in range(n_repeats):
        rng = np.random.default_rng(seed + rep)
        for va in np.array_split(rng.permutation(m), n_folds):
            tr = np.setdiff1d(np.arange(m), va)
            cnt = np.maximum(mask[tr].sum(0), 1)
            mean = (values[tr] * mask[tr]).sum(0) / cnt
            var = (((values[tr] - mean) ** 2) * mask[tr]).sum(0) / cnt
            std = np.where(var > 1e-10, np.sqrt(var), 1.0)
            Z = np.where(mask, (values - mean) / std, 0.0)
            mu, Sig, _, _ = em_gaussian_covariance(Z[tr], mask[tr], shrink=shrink)
            sel_g = greedy_select_conditional_variance(Sig, k, lam=lam)
            sel_r = random_subset_baseline(n, k, rng)
            for name, sel in (("greedy", sel_g), ("random", sel_r), ("knn", sel_g)):
                om = mask[va][:, sel]
                xo = Z[va][:, sel]
                if name == "knn":
                    pred = knn_model_impute(Z[tr], mask[tr], xo, om, sel)
                else:
                    pred = conditional_gaussian_impute(mu, Sig, sel, xo, om, lam=lam)
                tgt = mask[va].copy()
                tgt[:, sel] = False
                se = (((pred - Z[va]) ** 2) * tgt).sum(1) / np.maximum(tgt.sum(1), 1)
                res[name].extend(se[tgt.any(1)].tolist())
    return res


def main(out_path=None):
    out = {"synthetic_theory_check": synthetic_theory_check()}
    if out_path:
        with open(out_path, "w") as fh:
            json.dump(out, fh, indent=2)
    else:
        print(json.dumps(out, indent=2))


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else None)
