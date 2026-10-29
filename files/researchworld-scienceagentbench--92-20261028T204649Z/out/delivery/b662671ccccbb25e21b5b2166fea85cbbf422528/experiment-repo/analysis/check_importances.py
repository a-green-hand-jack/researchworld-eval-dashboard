"""Independent cross-check of workspace/pred_results/jnmf_h_importances.json.

Recomputes each factor with a different formulation (einsum / explicit loops),
and checks the identities the definitions imply: common + distinct importance = 1
(H has exactly two columns), and that the W columns are unit L2-norm, so the
inner products are cosine similarities in [0, 1] for nonnegative W.
"""
import json
import os
import sys

import numpy as np

data_dir = sys.argv[1] if len(sys.argv) > 1 else "/benchmark/datasets/jnmf_visualization"
pred = json.load(open(sys.argv[2] if len(sys.argv) > 2 else
                      os.path.join(os.path.dirname(__file__), "..", "workspace", "pred_results", "jnmf_h_importances.json")))
L = lambda n: np.load(os.path.join(data_dir, f"fit_result_conscientiousness_{n}.npy"))
Wh, Wl, Hh, Hl = L("W_high"), L("W_low"), L("H_high"), L("H_low")

ref = {
    "common error": 1 - np.einsum("i,i->", Wh[:, 0], Wl[:, 0]),
    "common importance": np.concatenate([Hh[:, 0], Hl[:, 0]]).sum() / np.concatenate([Hh, Hl]).sum(),
    "high importance": sum(Hh[:, 1]) / sum(Hh.ravel()),
    "low importance": sum(Hl[:, 1]) / sum(Hl.ravel()),
    "distinct error": np.einsum("i,i->", Wh[:, 1], Wl[:, 1]),
    "distinct importance": np.concatenate([Hh[:, 1], Hl[:, 1]]).sum() / np.concatenate([Hh, Hl]).sum(),
}
assert set(pred) == set(ref), (set(pred), set(ref))
for k, v in ref.items():
    print(f"{k:20s} pred={pred[k]:.12f} ref={v:.12f} absdiff={abs(pred[k]-v):.1e}")
    assert abs(pred[k] - v) < 1e-12
print("shapes", Wh.shape, Wl.shape, Hh.shape, Hl.shape)
print("min entries (nonnegativity)", Wh.min(), Wl.min(), Hh.min(), Hl.min())
print("W column L2 norms high", np.linalg.norm(Wh, axis=0), "low", np.linalg.norm(Wl, axis=0))
print("common + distinct importance =", pred["common importance"] + pred["distinct importance"])
assert abs(pred["common importance"] + pred["distinct importance"] - 1) < 1e-12
print("OK")
