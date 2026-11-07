"""Exact interventional (marginal) Shapley values of f(x)=P(y=1) w.r.t. a background sample Z:
  v(S) = mean_z f(x_S, z_{not S}),  phi_j = sum_S w(|S|) [v(S+j) - v(S)].
 * trees: shap.TreeExplainer(interventional), exact
 * LR / MLP: full enumeration using the additive first layer (d <= ~22)
 * brute force through any f (tests only)."""
import itertools
from math import comb, factorial
import numpy as np


def shapley_from_values(v, d):
    """v: array of length 2^d indexed by subset bitmask -> phi (d,)."""
    ids = np.arange(1 << d)
    pc = np.zeros(1 << d, dtype=np.int64)
    for j in range(d):
        pc += (ids >> j) & 1
    w = np.array([factorial(s) * factorial(d - s - 1) / factorial(d) for s in range(d)])
    phi = np.zeros(d)
    for j in range(d):
        without = ids[((ids >> j) & 1) == 0]
        phi[j] = np.sum(w[pc[without]] * (v[without | (1 << j)] - v[without]))
    return phi


def exact_bruteforce(f, x, Z):
    d = len(x)
    v = np.zeros(1 << d)
    for S in range(1 << d):
        mask = np.array([(S >> j) & 1 for j in range(d)], bool)
        H = np.where(mask[None, :], x[None, :], Z)
        v[S] = f(H).mean()
    return shapley_from_values(v, d)


def exact_net(model, x, Z, chunk_rows=3_000_000):
    """Exact Shapley values for NetModel (LR/MLP). Cost O(2^d * b * H*(d + width))."""
    d = len(x); b = len(Z); H = model.H
    Ax = np.stack([model.A(j, x[j:j + 1])[0] for j in range(d)])            # (d,H)
    Az = np.stack([model.A(j, Z[:, j]) for j in range(d)])                  # (d,b,H)
    D = Ax[:, None, :] - Az                                                 # (d,b,H)
    base = Az.sum(0)                                                        # (b,H)
    nS = max(1, chunk_rows // (b * H))
    v = np.zeros(1 << d)
    bits = np.arange(d)
    for s0 in range(0, 1 << d, nS):
        ids = np.arange(s0, min(s0 + nS, 1 << d))
        M = ((ids[:, None] >> bits[None, :]) & 1).astype(np.float64)        # (nS,d)
        pre = base[None] + np.tensordot(M, D, axes=([1], [0]))              # (nS,b,H)
        v[ids] = model.rest(pre).mean(1)
    return shapley_from_values(v, d)


def net_value_fn(model, x, Z):
    """Return g(masks)->v for (k,d) 0/1 masks, cheap value function for LR/MLP (used for references)."""
    d = len(x)
    Ax = np.stack([model.A(j, x[j:j + 1])[0] for j in range(d)])
    Az = np.stack([model.A(j, Z[:, j]) for j in range(d)])
    D = Ax[:, None, :] - Az
    base = Az.sum(0)

    def g(M):
        pre = base[None] + np.tensordot(np.asarray(M, float), D, axes=([1], [0]))
        return model.rest(pre).mean(1)
    return g


def exact_tree(model, x, Z):
    import shap
    if model.kind == "xgb":
        ex = shap.TreeExplainer(model.sk, data=Z, feature_perturbation="interventional", model_output="probability")
        return np.asarray(ex.shap_values(x[None], check_additivity=False))[0]
    ex = shap.TreeExplainer(model.sk, data=Z, feature_perturbation="interventional")
    sv = ex.shap_values(x[None], check_additivity=False)
    sv = np.asarray(sv)
    return sv[0, :, 1] if sv.ndim == 3 and sv.shape[-1] == 2 else sv[1, 0, :]


def exact_shap(model, x, Z):
    if hasattr(model, "rest"):
        return exact_net(model, x, Z)
    return exact_tree(model, x, Z)
