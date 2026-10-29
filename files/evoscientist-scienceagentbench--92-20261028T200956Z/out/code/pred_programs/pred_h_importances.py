import json
import os

import numpy as np

DATA_DIR = "/benchmark/datasets/jnmf_visualization"
PREFIX = "fit_result_conscientiousness"
OUT_PATH = "/workspace/pred_results/jnmf_h_importances.json"


def load(name):
    return np.load(os.path.join(DATA_DIR, f"{PREFIX}_{name}.npy"))


def main():
    W_high = load("W_high")
    W_low = load("W_low")
    H_high = load("H_high")
    H_low = load("H_low")

    total_H = H_high.sum() + H_low.sum()

    scores = {
        # 1. common error
        "common error": float(1.0 - np.dot(W_high[:, 0], W_low[:, 0])),
        # 2. common importance
        "common importance": float((H_high[:, 0].sum() + H_low[:, 0].sum()) / total_H),
        # 3. high importance
        "high importance": float(H_high[:, 1].sum() / H_high.sum()),
        # 4. low importance
        "low importance": float(H_low[:, 1].sum() / H_low.sum()),
        # 5. distinct error
        "distinct error": float(np.dot(W_high[:, 1], W_low[:, 1])),
        # 6. distinct importance
        "distinct importance": float((H_high[:, 1].sum() + H_low[:, 1].sum()) / total_H),
    }

    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    with open(OUT_PATH, "w") as f:
        json.dump(scores, f, indent=4)

    print(json.dumps(scores, indent=4))


if __name__ == "__main__":
    main()
