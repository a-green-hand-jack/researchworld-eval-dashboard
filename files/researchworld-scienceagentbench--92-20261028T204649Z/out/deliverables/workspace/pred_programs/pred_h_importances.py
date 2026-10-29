"""Importance factors of the joint NMF fit (jnmf_visualization, conscientiousness).

Inputs: W_high, W_low (features x 2) and H_high, H_low (subjects x 2) from
/benchmark/datasets/jnmf_visualization/. Column 0 is the common factor shared by
the high and low groups, column 1 the group-distinct factor.
Output: pred_results/jnmf_h_importances.json (relative to the working directory).
"""
import json
import os
import sys

import numpy as np

DATA_DIR = "/benchmark/datasets/jnmf_visualization"
PREFIX = "fit_result_conscientiousness_"
OUT_PATH = os.path.join("pred_results", "jnmf_h_importances.json")


def load(data_dir, name):
    return np.load(os.path.join(data_dir, PREFIX + name + ".npy"))


def compute_importances(W_high, W_low, H_high, H_low):
    total_H = H_high.sum() + H_low.sum()
    return {
        # 1 - <W_high[:, 0], W_low[:, 0]>
        "common error": 1.0 - float(np.dot(W_high[:, 0], W_low[:, 0])),
        # (sum H_high[:, 0] + sum H_low[:, 0]) / (sum H_high + sum H_low)
        "common importance": float((H_high[:, 0].sum() + H_low[:, 0].sum()) / total_H),
        # sum H_high[:, 1] / sum H_high
        "high importance": float(H_high[:, 1].sum() / H_high.sum()),
        # sum H_low[:, 1] / sum H_low
        "low importance": float(H_low[:, 1].sum() / H_low.sum()),
        # <W_high[:, 1], W_low[:, 1]>
        "distinct error": float(np.dot(W_high[:, 1], W_low[:, 1])),
        # (sum H_high[:, 1] + sum H_low[:, 1]) / (sum H_high + sum H_low)
        "distinct importance": float((H_high[:, 1].sum() + H_low[:, 1].sum()) / total_H),
    }


def main():
    data_dir = sys.argv[1] if len(sys.argv) > 1 else DATA_DIR
    W_high = load(data_dir, "W_high")
    W_low = load(data_dir, "W_low")
    H_high = load(data_dir, "H_high")
    H_low = load(data_dir, "H_low")
    assert W_high.shape == W_low.shape and W_high.shape[1] == 2
    assert H_high.shape[1] == 2 and H_low.shape[1] == 2

    scores = compute_importances(W_high, W_low, H_high, H_low)

    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    with open(OUT_PATH, "w") as f:
        json.dump(scores, f, indent=4)
    for name, value in scores.items():
        print(f"{name}: {value:.6f}")


if __name__ == "__main__":
    main()
