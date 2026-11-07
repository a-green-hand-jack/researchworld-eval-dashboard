"""Stochastic SHAP estimators (shap library) + deterministic references.

Budget B = number of coalition evaluations per explained instance (each evaluation averages the model over the
m background rows, so the cost in model calls is B*m).
 - kernel : shap.KernelExplainer(nsamples=B, l1_reg=False)  (paired sampling is built into shap)
 - perm   : shap.PermutationExplainer(max_evals=B)          (antithetic forward/reverse permutations)
"""
import numpy as np, shap, warnings
warnings.filterwarnings("ignore")


def kernel_phi(f, x, bg, B, seed, l1_reg=False):
    np.random.seed(seed)
    ex = shap.KernelExplainer(f, bg)
    return np.asarray(ex.shap_values(x[None, :], nsamples=int(B), l1_reg=l1_reg, silent=True)).reshape(-1)


def perm_phi(f, x, bg, B, seed):
    d = len(x)
    masker = shap.maskers.Independent(bg, max_samples=len(bg))
    ex = shap.PermutationExplainer(f, masker, seed=seed)
    # shap needs max_evals >= 2d+1 ; it rounds to whole forward/reverse permutation pairs
    me = max(int(B), 2 * d + 1)
    return np.asarray(ex(x[None, :], max_evals=me, silent=True).values).reshape(-1)


def exact_kernel(f, x, bg):
    """Exact Shapley values (all 2^d coalitions) for small d, via KernelSHAP with full enumeration."""
    d = len(x)
    return kernel_phi(f, x, bg, 2 ** d - 2 if d <= 20 else 2 ** 20, 0)


def tree_phi(model, x, bg):
    """Exact interventional TreeSHAP for the RF probability output (linear in tree outputs => exact)."""
    ex = shap.TreeExplainer(model.m, data=bg, feature_perturbation="interventional")
    v = np.asarray(ex.shap_values(x[None, :], check_additivity=False))
    # sklearn RF returns (n, d, 2) or list; take class 1
    if v.ndim == 3:
        v = v[0, :, 1]
    return v.reshape(-1)


def reference_phi(model, x, bg, d_exact_max=12, ref_B=8192):
    """Deterministic (or near-deterministic) reference. Returns (phi, kind)."""
    d = len(x)
    if model.kind == "rf":
        return tree_phi(model, x, bg), "treeshap-exact"
    if d <= d_exact_max:
        return exact_kernel(model.predict, x, bg), "enumeration-exact"
    return kernel_phi(model.predict, x, bg, ref_B, 12345), f"kernel-B{ref_B}"
