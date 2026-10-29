import json
import os

import numpy as np

DATA_DIR = "/benchmark/datasets/jnmf_visualization"
OUT_DIR = "/workspace/pred_results"
PREFIX = "fit_result_conscientiousness_"


def load(name):
    return np.load(os.path.join(DATA_DIR, f"{PREFIX}{name}.npy"))


def main():
    W_high = load("W_high")
    W_low = load("W_low")
    H_high = load("H_high")
    H_low = load("H_low")

    total_H = H_high.sum() + H_low.sum()

    common_error = 1.0 - float(W_high[:, 0] @ W_low[:, 0])
    common_importance = float((H_high[:, 0].sum() + H_low[:, 0].sum()) / total_H)
    high_importance = float(H_high[:, 1].sum() / H_high.sum())
    low_importance = float(H_low[:, 1].sum() / H_low.sum())
    distinct_error = float(W_high[:, 1] @ W_low[:, 1])
    distinct_importance = float((H_high[:, 1].sum() + H_low[:, 1].sum()) / total_H)

    scores = {
        "common_error": common_error,
        "common_importance": common_importance,
        "high_importance": high_importance,
        "low_importance": low_importance,
        "distinct_error": distinct_error,
        "distinct_importance": distinct_importance,
    }

    os.makedirs(OUT_DIR, exist_ok=True)
    with open(os.path.join(OUT_DIR, "jnmf_h_importances.json"), "w") as f:
        json.dump(scores, f, indent=4)
    print(json.dumps(scores, indent=4))


if __name__ == "__main__":
    main()
