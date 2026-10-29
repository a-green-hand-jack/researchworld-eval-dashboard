import ast
import json
import os
import struct

DATA_DIR = "/benchmark/datasets/jnmf_visualization"
OUT_DIR = "/workspace/pred_results"
PREFIX = "fit_result_conscientiousness_"


def read_npy(path):
    """Load a 2-D float64 .npy file as a list of rows (numpy if available)."""
    try:
        import numpy as np
        return np.load(path).tolist()
    except ImportError:
        pass

    with open(path, "rb") as f:
        if f.read(6) != b"\x93NUMPY":
            raise ValueError(f"{path} is not a .npy file")
        major = f.read(2)[0]
        header_len_size = 2 if major == 1 else 4
        header_len = int.from_bytes(f.read(header_len_size), "little")
        header = ast.literal_eval(f.read(header_len).decode("latin1"))
        if header["descr"] not in ("<f8", "=f8"):
            raise ValueError(f"unsupported dtype {header['descr']}")
        rows, cols = header["shape"]
        flat = struct.unpack(f"<{rows * cols}d", f.read(8 * rows * cols))
    if header["fortran_order"]:
        return [[flat[c * rows + r] for c in range(cols)] for r in range(rows)]
    return [list(flat[r * cols:(r + 1) * cols]) for r in range(rows)]


def load(name):
    return read_npy(os.path.join(DATA_DIR, PREFIX + name + ".npy"))


def column(mat, j):
    return [row[j] for row in mat]


def inner(a, b):
    return sum(x * y for x, y in zip(a, b))


def total(mat):
    return sum(sum(row) for row in mat)


def main():
    W_high = load("W_high")
    W_low = load("W_low")
    H_high = load("H_high")
    H_low = load("H_low")

    total_high = total(H_high)
    total_low = total(H_low)
    total_both = total_high + total_low

    scores = {
        "common_error": 1.0 - inner(column(W_high, 0), column(W_low, 0)),
        "common_importance": (sum(column(H_high, 0)) + sum(column(H_low, 0))) / total_both,
        "high_importance": sum(column(H_high, 1)) / total_high,
        "low_importance": sum(column(H_low, 1)) / total_low,
        "distinct_error": inner(column(W_high, 1), column(W_low, 1)),
        "distinct_importance": (sum(column(H_high, 1)) + sum(column(H_low, 1))) / total_both,
    }
    scores = {k: float(v) for k, v in scores.items()}

    os.makedirs(OUT_DIR, exist_ok=True)
    with open(os.path.join(OUT_DIR, "jnmf_h_importances.json"), "w") as f:
        json.dump(scores, f, indent=4)
    print(json.dumps(scores, indent=4))


if __name__ == "__main__":
    main()
