"""Ties in the top-k ranking: how often does the tie-break of `topk_ind` (smaller feature index first) decide a top-k set?

usage: python3 analysis/ties.py [raw_dir] [out_dir]
Ranking is by |attribution|.  For the reference and for the runs of every explainer x budget and k in {1, 3, 5}:
  tie_boundary  share of instances (runs) whose k-th and (k+1)-th largest |attribution| differ by < 1e-12 (the set is decided by the tie-break)
  zero_in_topk  share of instances (runs) whose k-th largest |attribution| is < 1e-12 (an exactly-zero attribution is inside the top-k)
Writes tables/ties.csv.
"""
import glob, os, sys
import numpy as np, pandas as pd

raw = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(__file__), "..", "results", "raw")
out = sys.argv[2] if len(sys.argv) > 2 else os.path.join(os.path.dirname(__file__), "..", "results", "tables")
EPS = 1e-12
res = []


def stats(A, k):
    """A (..., d) attribution vectors."""
    a = np.sort(np.abs(A), axis=-1)[..., ::-1]
    return float((a[..., k - 1] - a[..., k] < EPS).mean()), float((a[..., k - 1] < EPS).mean())


for fref in sorted(glob.glob(f"{raw}/*__ref.npz")):
    cell = os.path.basename(fref).rsplit("__", 1)[0]; ds, model = cell.split("__")
    ref = np.load(fref)["ref"]; d = ref.shape[1]
    for k in (1, 3, 5):
        if k < d:
            tb, zt = stats(ref, k)
            res.append(dict(dataset=ds, model=model, d=d, source="reference", budget=np.nan, k=k, n=ref.shape[0], tie_boundary=tb, zero_in_topk=zt))
    for ex in ("kernel", "perm"):
        f = f"{raw}/{cell}__{ex}.npz"
        if not os.path.exists(f):
            continue
        z = np.load(f); phi = z["phi"]
        for b, bud in enumerate(z["budgets"]):
            for k in (1, 3, 5):
                if k < d:
                    tb, zt = stats(phi[:, b], k)
                    res.append(dict(dataset=ds, model=model, d=d, source=ex, budget=int(bud), k=k, n=phi[:, b].shape[0] * phi.shape[2],
                                    tie_boundary=tb, zero_in_topk=zt))
pd.DataFrame(res).to_csv(f"{out}/ties.csv", index=False)
print(len(res), "rows")
