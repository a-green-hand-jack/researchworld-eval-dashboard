"""Independent recomputation of the six importance factors, used to check deliveries.

Input: /benchmark/datasets/jnmf_visualization/fit_result_conscientiousness_{W_high,W_low,H_high,H_low}.npy
Definitions follow the task text verbatim (Research objective, internal-review-repo#1).
Usage: python3 -I review/reference_check.py [delivered_json]
"""
import json
import sys

import numpy as np

D = "/benchmark/datasets/jnmf_visualization/fit_result_conscientiousness_"
W_high, W_low, H_high, H_low = (np.load(D + n + ".npy") for n in ("W_high", "W_low", "H_high", "H_low"))
total = H_high.sum() + H_low.sum()
ref = {
    "common error": 1 - W_high[:, 0] @ W_low[:, 0],
    "common importance": (H_high[:, 0].sum() + H_low[:, 0].sum()) / total,
    "high importance": H_high[:, 1].sum() / H_high.sum(),
    "low importance": H_low[:, 1].sum() / H_low.sum(),
    "distinct error": W_high[:, 1] @ W_low[:, 1],
    "distinct importance": (H_high[:, 1].sum() + H_low[:, 1].sum()) / total,
}
ref = {k: float(v) for k, v in ref.items()}
print(json.dumps(ref, indent=2))
if len(sys.argv) > 1:
    got = json.load(open(sys.argv[1]))
    ok = set(got) == set(ref) and all(np.isclose(got[k], ref[k], rtol=1e-9, atol=1e-12) for k in ref)
    print("MATCH" if ok else f"MISMATCH: {got}")
    sys.exit(0 if ok else 1)
