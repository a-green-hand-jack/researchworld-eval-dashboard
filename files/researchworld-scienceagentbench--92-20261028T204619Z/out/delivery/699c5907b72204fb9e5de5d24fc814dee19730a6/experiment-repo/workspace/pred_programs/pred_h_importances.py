"""Importance factors of the common and distinct components of a jNMF fit.

Reads W_high, W_low, H_high, H_low (conscientiousness fit) and writes a
JSON dictionary of six scores to <out-dir>/jnmf_h_importances.json.
Column 0 is the common component, column 1 the distinct component.
"""
import argparse
import json
import os

import numpy as np

DATA_DIR = "/benchmark/datasets/jnmf_visualization"
OUT_DIR = "/workspace/pred_results"
PREFIX = "fit_result_conscientiousness_"


def compute_importances(W_high, W_low, H_high, H_low):
    h_total = H_high.sum() + H_low.sum()
    return {
        "common error": float(1.0 - np.dot(W_high[:, 0], W_low[:, 0])),
        "common importance": float((H_high[:, 0].sum() + H_low[:, 0].sum()) / h_total),
        "high importance": float(H_high[:, 1].sum() / H_high.sum()),
        "low importance": float(H_low[:, 1].sum() / H_low.sum()),
        "distinct error": float(np.dot(W_high[:, 1], W_low[:, 1])),
        "distinct importance": float((H_high[:, 1].sum() + H_low[:, 1].sum()) / h_total),
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-dir", default=DATA_DIR)
    ap.add_argument("--out-dir", default=OUT_DIR)
    args = ap.parse_args()

    m = {k: np.load(os.path.join(args.data_dir, f"{PREFIX}{k}.npy"))
         for k in ("W_high", "W_low", "H_high", "H_low")}
    scores = compute_importances(m["W_high"], m["W_low"], m["H_high"], m["H_low"])

    os.makedirs(args.out_dir, exist_ok=True)
    out = os.path.join(args.out_dir, "jnmf_h_importances.json")
    with open(out, "w") as f:
        json.dump(scores, f, indent=2)
    print(json.dumps(scores, indent=2))


if __name__ == "__main__":
    main()
