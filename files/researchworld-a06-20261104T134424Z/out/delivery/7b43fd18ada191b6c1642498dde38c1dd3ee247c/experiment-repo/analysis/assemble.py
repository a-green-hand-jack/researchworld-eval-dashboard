"""Merge per-job score files into the correctness matrix. usage: assemble.py OUTDIR TEST_PARQUET QIDX OUT_NPZ"""
import sys, glob, numpy as np, pandas as pd
outdir, test_pq, qidx, out = sys.argv[1:5]
t = pd.read_parquet(test_pq); q = np.load(qidx); y = t.answer_index.values[q]
parts = sorted(glob.glob(f"{outdir}/pool_*.npy"), key=lambda p: int(p.split("pool_")[1].split("-")[0]))
NC = 60; L = None
for p in parts:                                              # each file holds configs start..start+6; missing files stay NaN (incomplete)
    a = np.load(p); st = int(p.split("pool_")[1].split("-")[0])
    if L is None: L = np.full((NC,) + a.shape[1:], np.nan, dtype=a.dtype)
    L[st:st + a.shape[0]] = a                                # (60, N, 10) log-probs by original option index
done = np.array([not np.isnan(L[i]).any() for i in range(L.shape[0])])   # a config counts only if complete on all N items
cfg_idx = np.flatnonzero(done); L = L[cfg_idx]
pred = L.argmax(-1); Y = pred == y[None, :]
np.savez_compressed(out, Y=Y, logp=L.astype(np.float16), cfg_idx=cfg_idx, qidx=q, answer=y, category=t.category.values[q])
print("complete configs", len(cfg_idx), cfg_idx.tolist()); print("Y", Y.shape, "acc range", Y.mean(1).min(), Y.mean(1).max())
