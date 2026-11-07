"""Library SHAP estimators with explicit seeds. Budget m = nominal number of coalitions evaluated per
instance (each coalition value is an average of f over the b background rows)."""
import numpy as np
import shap


def kernel_run(f, x, Z, m, seed, l1_reg=False):
    np.random.seed(seed)
    ex = shap.KernelExplainer(f, Z)
    return np.asarray(ex.shap_values(x[None], nsamples=int(m), silent=True, l1_reg=l1_reg)).reshape(-1)


def perm_run(f, x, Z, m, seed):
    """shap.PermutationExplainer, floor(m/(2d+1)) forward+reverse permutations (needs m >= 2d+1)."""
    ex = shap.PermutationExplainer(f, shap.maskers.Independent(Z, max_samples=len(Z)), seed=seed)
    return np.asarray(ex(x[None], max_evals=int(m), silent=True).values).reshape(-1)


# ---------------------------------------------------------------------------------------------
# Own antithetic permutation sampler. Keeps the per-pair contributions, so that a single run has a
# within-run standard error; also used with a very large number of pairs as the "reference".
# ---------------------------------------------------------------------------------------------
def make_value_fn(model, x, Z):
    """vf(masks (k,d) bool) -> (k,) v(S)=mean_z f(x_S, z_notS); fast table version for LR/MLP."""
    if hasattr(model, "rest"):
        from .exact import net_value_fn
        g = net_value_fn(model, x, Z)
        return lambda M: g(M)
    b, d = Z.shape

    def vf(M):
        k = len(M)
        H = np.where(M[:, None, :], x[None, None, :], Z[None, :, :])      # (k,b,d)
        return model.predict(H.reshape(k * b, d)).reshape(k, b).mean(1)
    return vf


def perm_pairs(vf, v0, vN, d, n_pairs, rng, batch=16):
    """returns C (n_pairs,d): each row is the antithetic (forward+reverse) average marginal contribution."""
    C = np.zeros((n_pairs, d))
    for p0 in range(0, n_pairs, batch):
        nb = min(batch, n_pairs - p0)
        perms = np.stack([rng.permutation(d) for _ in range(nb)])
        masks = np.zeros((nb, 2, d - 1, d), bool)
        for i in range(nb):
            for r in range(2):
                order = perms[i] if r == 0 else perms[i][::-1]
                tri = np.tril(np.ones((d - 1, d - 1), bool))  # prefix of size k+1
                masks[i, r][:, order[:d - 1]] = tri
        vals = vf(masks.reshape(-1, d)).reshape(nb, 2, d - 1)
        for i in range(nb):
            for r in range(2):
                order = perms[i] if r == 0 else perms[i][::-1]
                chain = np.concatenate([[v0], vals[i, r], [vN]])
                C[p0 + i, order] += 0.5 * np.diff(chain)
    return C


def perm_own(model, x, Z, m, seed, batch=16):
    """m = number of coalition evaluations; each antithetic pair costs 2(d-1). Returns (phi, se)."""
    d = len(x)
    vf = make_value_fn(model, x, Z)
    v0 = model.predict(Z).mean(); vN = model.predict(x[None])[0]
    n_pairs = max(2, int(m // (2 * (d - 1))))
    C = perm_pairs(vf, v0, vN, d, n_pairs, np.random.RandomState(seed), batch)
    return C.mean(0), C.std(0, ddof=1) / np.sqrt(n_pairs), C
