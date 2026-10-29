import json
import numpy as np

d = "/benchmark/datasets/jnmf_visualization/fit_result_conscientiousness_"
W_high, W_low, H_high, H_low = (np.load(d + n + ".npy") for n in ["W_high", "W_low", "H_high", "H_low"])

total = H_high.sum() + H_low.sum()
scores = {
    "common error": float(1 - np.dot(W_high[:, 0], W_low[:, 0])),
    "common importance": float((H_high[:, 0].sum() + H_low[:, 0].sum()) / total),
    "high importance": float(H_high[:, 1].sum() / H_high.sum()),
    "low importance": float(H_low[:, 1].sum() / H_low.sum()),
    "distinct error": float(np.dot(W_high[:, 1], W_low[:, 1])),
    "distinct importance": float((H_high[:, 1].sum() + H_low[:, 1].sum()) / total),
}
with open("/workspace/pred_results/jnmf_h_importances.json", "w") as f:
    json.dump(scores, f, indent=2)
print(scores)
