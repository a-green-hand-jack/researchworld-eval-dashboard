"""Loading and grouping of results/ tables for the figure scripts."""
import argparse, json, os
import numpy as np, pandas as pd


def board_key(board):
    """Evaluation design key (style.DESIGNS) of a board label."""
    if board.startswith("arena"):
        return "A"
    if board.startswith(("mtbench_human", "mtmatched_h")):
        return "M-h"
    if board.startswith(("mtbench_gpt4", "mtmatched_g")):
        return "M-g"
    if board.startswith("nba"):
        return "N"
    raise ValueError(f"unknown board {board}")


def read(results, name, suffix=""):
    """Read results/<name><suffix>.csv, or None when the analysis has not been run."""
    p = os.path.join(results, f"{name}{suffix}.csv")
    return pd.read_csv(p) if os.path.exists(p) else None


def provenance(results, names, suffix=""):
    """Manifest entries (script, seed, code commit) of the files a figure read."""
    m = json.load(open(os.path.join(results, "MANIFEST.json")))
    return {f"{n}{suffix}.csv": {k: m[f"{n}{suffix}.csv"][k] for k in ("script", "seed", "code_commit")}
            for n in names if f"{n}{suffix}.csv" in m}


def wilson(k, n, z=1.96):
    k, n = np.asarray(k, float), np.asarray(n, float)
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * np.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return c - h, c + h


def parser():
    ap = argparse.ArgumentParser()
    ap.add_argument("--results", default=os.path.join(os.path.dirname(__file__), "..", "results"))
    ap.add_argument("--suffix", default="", help="'_pilot' reads the pilot files (not for delivery)")
    ap.add_argument("--out", default=os.path.join(os.path.dirname(__file__), "rendered"))
    return ap
