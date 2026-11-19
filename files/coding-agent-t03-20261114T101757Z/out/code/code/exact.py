"""Exact interventional Shapley values by full coalition enumeration.

v(S) = mean_k f(x_S, b_k,complement(S)) over the K background rows, and
phi_j = sum_{S not containing j} |S|!(d-|S|-1)!/d! * (v(S+j) - v(S)).
Feasible for d <= 10 (2^d coalitions). Used as ground truth for ACS and Pima
and as an independent check of shap's enumeration mode.
"""
import math
import os
import sys

import numpy as np

from common import RES_DIR, MODELS, get_model, output_fn, split, DATASETS


def coalition_values(f, x_inst, bg, chunk=1):
    """Return v with shape (N, 2^d): coalition values for each instance."""
    N, d = x_inst.shape
    masks = ((np.arange(2 ** d)[:, None] >> np.arange(d)) & 1).astype(bool)
    K = bg.shape[0]
    v = np.zeros((N, 2 ** d))
    for i in range(N):
        Z = np.where(masks[:, None, :], x_inst[i][None, None, :], bg[None, :, :])
        v[i] = f(Z.reshape(-1, d)).reshape(2 ** d, K).mean(axis=1)
    return v


def exact_shapley(f, x_inst, bg):
    N, d = x_inst.shape
    assert d <= 12, "enumeration only intended for small d"
    v = coalition_values(f, x_inst, bg)
    masks = ((np.arange(2 ** d)[:, None] >> np.arange(d)) & 1).astype(bool)
    sizes = masks.sum(axis=1)
    phi = np.zeros((N, d))
    for j in range(d):
        wo = np.where(~masks[:, j])[0]  # coalitions not containing j
        w_idx = wo + (1 << j)  # same coalition with j added
        w = np.array([math.factorial(s) * math.factorial(d - s - 1) / math.factorial(d)
                      for s in sizes[wo]])
        phi[:, j] = (v[:, w_idx] - v[:, wo]) @ w
    # efficiency check: sum_j phi_j = f(x) - E[f(background)]
    fx = v[:, -1]
    base = v[:, 0]
    gap = np.abs(phi.sum(axis=1) - (fx - base)).max()
    return phi, gap


if __name__ == "__main__":
    ds, model_name, seed, output = sys.argv[1], sys.argv[2], int(sys.argv[3]), sys.argv[4]
    s = split(ds)
    m = get_model(ds, model_name, seed)
    f = output_fn(m, model_name, output)
    phi, gap = exact_shapley(f, s["X_inst"], s["background"][:100])
    os.makedirs(f"{RES_DIR}/exact", exist_ok=True)
    out = f"{RES_DIR}/exact/{ds}_{model_name}_s{seed}_{output}.npy"
    np.save(out, phi)
    print(f"{ds} {model_name} seed={seed} out={output}: additivity max|err|={gap:.2e} -> {out}")
