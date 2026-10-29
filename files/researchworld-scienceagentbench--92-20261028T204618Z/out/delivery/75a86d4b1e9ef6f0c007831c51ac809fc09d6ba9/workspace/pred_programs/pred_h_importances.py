"""Importance factors of the joint NMF fit (conscientiousness, high vs. low).

Reads the factor matrices W_high, W_low, H_high, H_low from the
jnmf_visualization dataset and computes the six scores defined in the task:

1. common error: 1 - <W_high[:, 0], W_low[:, 0]>
2. common importance: (sum H_high[:, 0] + sum H_low[:, 0]) / (sum H_high + sum H_low)
3. high importance: sum H_high[:, 1] / sum H_high
4. low importance: sum H_low[:, 1] / sum H_low
5. distinct error: <W_high[:, 1], W_low[:, 1]>
6. distinct importance: (sum H_high[:, 1] + sum H_low[:, 1]) / (sum H_high + sum H_low)

The scores are saved as a JSON dictionary to pred_results/jnmf_h_importances.json.
"""

import json
import os

import numpy as np

DATASET_CANDIDATES = [
    "/benchmark/datasets/jnmf_visualization",
    "benchmark/datasets/jnmf_visualization",
]
PREFIX = "fit_result_conscientiousness_"
OUTPUT_PATH = os.path.join("pred_results", "jnmf_h_importances.json")


def find_dataset_dir():
    for path in DATASET_CANDIDATES:
        if os.path.isfile(os.path.join(path, PREFIX + "W_high.npy")):
            return path
    raise FileNotFoundError(
        "jnmf_visualization dataset not found in: " + ", ".join(DATASET_CANDIDATES)
    )


def load_factors(data_dir):
    names = ["W_high", "W_low", "H_high", "H_low"]
    return [np.load(os.path.join(data_dir, PREFIX + name + ".npy")) for name in names]


def compute_importances(W_high, W_low, H_high, H_low):
    total_high = H_high.sum()
    total_low = H_low.sum()
    total = total_high + total_low
    return {
        "common error": float(1.0 - W_high[:, 0] @ W_low[:, 0]),
        "common importance": float((H_high[:, 0].sum() + H_low[:, 0].sum()) / total),
        "high importance": float(H_high[:, 1].sum() / total_high),
        "low importance": float(H_low[:, 1].sum() / total_low),
        "distinct error": float(W_high[:, 1] @ W_low[:, 1]),
        "distinct importance": float((H_high[:, 1].sum() + H_low[:, 1].sum()) / total),
    }


def main():
    W_high, W_low, H_high, H_low = load_factors(find_dataset_dir())
    scores = compute_importances(W_high, W_low, H_high, H_low)

    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    with open(OUTPUT_PATH, "w") as f:
        json.dump(scores, f, indent=4)

    for name, value in scores.items():
        print(f"{name}: {value:.6f}")


if __name__ == "__main__":
    main()
