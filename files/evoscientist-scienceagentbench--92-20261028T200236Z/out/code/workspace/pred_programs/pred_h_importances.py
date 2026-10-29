import json
import os

import numpy as np

DATA_DIR = "/benchmark/datasets/jnmf_visualization"
PREFIX = "fit_result_conscientiousness"
OUT_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "pred_results", "jnmf_h_importances.json"
)


def load(name):
    return np.load(os.path.join(DATA_DIR, PREFIX + "_" + name + ".npy")).astype(float)


def ratio(num, den):
    return float(num) / float(den)


def main():
    W_high = load("W_high")
    W_low = load("W_low")
    H_high = load("H_high")
    H_low = load("H_low")

    total_H = float(H_high.sum()) + float(H_low.sum())
    scores = {
        "common error": 1.0 - float(np.dot(W_high[:, 0], W_low[:, 0])),
        "common importance": ratio(H_high[:, 0].sum() + H_low[:, 0].sum(), total_H),
        "high importance": ratio(H_high[:, 1].sum(), H_high.sum()),
        "low importance": ratio(H_low[:, 1].sum(), H_low.sum()),
        "distinct error": float(np.dot(W_high[:, 1], W_low[:, 1])),
        "distinct importance": ratio(H_high[:, 1].sum() + H_low[:, 1].sum(), total_H),
    }

    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    with open(OUT_PATH, "w") as f:
        json.dump(scores, f, indent=4)
    print(json.dumps(scores, indent=4))


if __name__ == "__main__":
    main()
