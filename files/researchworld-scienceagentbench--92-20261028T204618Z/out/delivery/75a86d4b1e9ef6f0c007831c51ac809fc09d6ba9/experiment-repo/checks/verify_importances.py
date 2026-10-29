"""Cross-check of workspace/pred_results/jnmf_h_importances.json.

1. Recomputes every factor the way the original analysis does it
   (brand-d/cogsci-jnmf, analysis/model_evaluation/h_importances.py: np.sum(c1*c2),
   column sums of H), independently of the delivered program.
2. Sanity checks: W columns are unit-norm (so the inner products are cosine
   similarities), H has two columns, common + distinct importance = 1.
Usage: python3 checks/verify_importances.py [path/to/jnmf_h_importances.json]
(keys may use spaces or underscores, as in the task's factor names)
"""
import json
import sys
import numpy as np

d = "/benchmark/datasets/jnmf_visualization/fit_result_conscientiousness_"
Wh, Wl, Hh, Hl = (np.load(d + n + ".npy") for n in ("W_high", "W_low", "H_high", "H_low"))
hs, ls = np.sum(Hh, axis=0), np.sum(Hl, axis=0)
ref = {
    "common_error": 1 - np.sum(Wh[:, 0] * Wl[:, 0]),
    "common_importance": (hs[0] + ls[0]) / np.sum(hs + ls),
    "high_importance": hs[1] / np.sum(hs),
    "low_importance": ls[1] / np.sum(ls),
    "distinct_error": np.sum(Wh[:, 1] * Wl[:, 1]),
    "distinct_importance": (hs[1] + ls[1]) / np.sum(hs + ls),
}
path = sys.argv[1] if len(sys.argv) > 1 else "workspace/pred_results/jnmf_h_importances.json"
print("checking", path)
pred = {k.replace(" ", "_"): v for k, v in json.load(open(path)).items()}
assert list(pred) == list(ref), (list(pred), list(ref))
for k in ref:
    assert np.isclose(pred[k], ref[k], rtol=1e-12, atol=0), (k, pred[k], ref[k])
    print(f"{k}: delivered {pred[k]!r}  reference {float(ref[k])!r}")
print("shapes", Wh.shape, Wl.shape, Hh.shape, Hl.shape)
print("W column norms high", np.linalg.norm(Wh, axis=0), "low", np.linalg.norm(Wl, axis=0))
assert Hh.shape[1] == Hl.shape[1] == Wh.shape[1] == Wl.shape[1] == 2
assert np.allclose(np.linalg.norm(Wh, axis=0), 1, atol=1e-5) and np.allclose(np.linalg.norm(Wl, axis=0), 1, atol=1e-5)
assert np.isclose(pred["common_importance"] + pred["distinct_importance"], 1)
print("all checks passed")
