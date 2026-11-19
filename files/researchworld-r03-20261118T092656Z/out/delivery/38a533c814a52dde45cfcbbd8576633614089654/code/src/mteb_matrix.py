"""Build the MTEB model x task matrix and the dense-block settings (A) / sparse (B).

Model = (model dir, primary revision); primary revision = the revision dir with most task
files (ties: lexicographically last). Rule uses only the missingness pattern.
Dense block (setting A): iterative peeling -- repeatedly remove the row or column with the
lowest observed fraction within the current submatrix (ties: the line with fewer observed
entries, then columns before rows) until the submatrix is complete. Uses no scores.
"""
import numpy as np, pandas as pd, re

def load_long(path="data/mteb_long.parquet"):
    d = pd.read_parquet(path)
    c = d.groupby(["model", "revision"]).size().rename("n").reset_index()
    c = c.sort_values(["model", "n", "revision"], ascending=[True, False, False])
    best = c.drop_duplicates("model")[["model", "revision"]]
    return d.merge(best)

def wide(d, col="main_score"):
    return d.pivot_table(index="model", columns="task", values=col, aggfunc="mean")

def task_type(t):
    for key, name in [("PairClassification", "PairClassification"), ("Classification", "Classification"),
                      ("Clustering", "Clustering"), ("Reranking", "Reranking"), ("Summarization", "Summarization"),
                      ("STS", "STS"), ("SICK", "STS"), ("Bitext", "BitextMining"), ("Retrieval", "Retrieval")]:
        if key in t:
            return name
    return "Other"

def peel(obs, min_rows=0):
    """obs: bool array (M,N). returns (rows, cols) index arrays of a complete block."""
    rows = np.arange(obs.shape[0]); cols = np.arange(obs.shape[1])
    while True:
        sub = obs[np.ix_(rows, cols)]
        if sub.all():
            return rows, cols
        rf = sub.mean(1); cf = sub.mean(0)
        if cf.min() <= rf.min():
            cols = np.delete(cols, np.argmin(cf))
        else:
            rows = np.delete(rows, np.argmin(rf))
