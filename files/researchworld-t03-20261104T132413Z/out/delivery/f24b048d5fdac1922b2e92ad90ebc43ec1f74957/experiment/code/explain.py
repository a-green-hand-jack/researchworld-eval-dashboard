"""Explainers over attribute-level inputs; every call is counted in model-row evaluations.

value function v(S;x) = mean_b f(x_S, b_{~S}) over a fixed background set (interventional Shapley game).
"""
import warnings, itertools
import numpy as np
import shap
from math import factorial


class Counter:
    """Wraps f so that the number of model rows evaluated is recorded."""
    def __init__(self, f):
        self.f, self.rows = f, 0

    def __call__(self, A):
        self.rows += len(A)
        return self.f(A)


def exact_shapley(f, x, bg, chunk=200_000):
    """Exact interventional Shapley values by enumerating all 2^d coalitions (d <= ~14)."""
    d, B = len(x), len(bg)
    M = 1 << d
    masks = ((np.arange(M)[:, None] >> np.arange(d)[None, :]) & 1).astype(bool)  # (M, d)
    v = np.empty(M)
    per = max(1, chunk // B)
    for s in range(0, M, per):
        mk = masks[s:s + per]
        Z = np.where(mk[:, None, :], x[None, None, :], bg[None, :, :]).reshape(-1, d)
        v[s:s + per] = f(Z).reshape(len(mk), B).mean(1)
    size = masks.sum(1)
    w = np.array([factorial(k) * factorial(d - k - 1) / factorial(d) for k in range(d)])
    phi = np.zeros(d)
    idx = np.arange(M)
    for j in range(d):
        without = idx[~masks[:, j]]
        phi[j] = np.sum(w[size[without]] * (v[without | (1 << j)] - v[without]))
    return phi, v[0], v[M - 1]


def kernel_shap(f, x, bg, m, seed, l1_reg=False):
    """shap.KernelExplainer with m sampled coalitions (library's sampling scheme, paired, size-enumeration first)."""
    cf = Counter(f)
    np.random.seed(seed)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        ke = shap.KernelExplainer(cf, bg)
        cf.rows = 0
        phi = ke.shap_values(x[None, :], nsamples=m, l1_reg=l1_reg, silent=True)
    return np.asarray(phi).reshape(-1), cf.rows


def perm_shap(f, x, bg, m, seed):
    """shap Permutation explainer (antithetic permutations) with max_evals=m."""
    cf = Counter(f)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        pe = shap.explainers.Permutation(cf, bg, seed=seed)
        cf.rows = 0
        e = pe(x[None, :], max_evals=m, silent=True)
    return np.asarray(e.values).reshape(-1), cf.rows
