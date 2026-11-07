"""Conclusion-level experiment: 'tuning improves over a baseline configuration by X'.
Baselines: (a) 'default' = config 0 (instruction 0, format 0, demo-set 0); (b) 'strong' = the best fixed config in the pool
(oracle; a claim that tuning beats it is true only if the selected config is as good).
Reported gain = score(selected) - score(baseline) on the SAME search set. We build a two-sided 90% interval for the gain with
  naive  : paired normal interval on the search set
  holdout: select on first half, paired normal interval on 2nd half
  maxT   : simultaneous bootstrap band over the 72 paired differences (S[:,c]-S[:,base]), valid for any selection
A 'positive claim' = lower end of interval > 0.  A 'false positive claim' = positive claim while true gain <= 0 (strong baseline) or
true gain < 0.02 (default).  Usage: python code/exp_gain.py MODEL PARSER REPS OUT [nlist]
"""
import sys, os, time
import numpy as np, pandas as pd, multiprocessing as mp
sys.path.insert(0, "code")
from data_io import load
from selinf import *
from search_algs import *
model, parser, REPS, OUT = sys.argv[1:5]; REPS = int(REPS)
NS = [int(x) for x in sys.argv[5].split(",")] if len(sys.argv) > 5 else [50, 100, 200, 400, 800]
M, info = load(model, parser=parser); Q = M.shape[0]; MU = M.mean(0)
BASES = {"default": 0, "strong": int(np.argmax(MU))}
Z = 1.6449

def pair_ci(d):
    m = d.mean(); se = d.std(ddof=1) / np.sqrt(len(d)) + 1e-12
    return m, m - Z * se, m + Z * se

def one_rep(a):
    n, rep = a
    rng = np.random.RandomState(7000003 * n + rep)
    S = M[rng.randint(0, Q, n)]; rows = []
    for aname, K in [("grid", 72), ("random", 12), ("coord", 72)]:
        alg = ALGS[aname]; r2 = np.random.RandomState(rng.randint(1 << 30))
        sel, cols, _ = alg(S, r2, K)
        sh, _, _ = alg(S[: n // 2], np.random.RandomState(rng.randint(1 << 30)), K)
        for bn, b in BASES.items():
            D = S - S[:, [b]]
            tg = MU[sel] - MU[b]
            res = {}
            res["naive"] = pair_ci(D[:, sel])
            ho = S[n // 2:]; res["holdout50"] = pair_ci(ho[:, sh] - ho[:, b])
            tg_h = MU[sh] - MU[b]
            e, lo, hi, _ = maxT(D, r2, 0.1, c=sel); res["maxT"] = (e, lo, hi)
            for k, (e, lo, hi) in res.items():
                t = tg_h if k == "holdout50" else tg
                rows.append(dict(n=n, rep=rep, alg=aname, K=K, base=bn, method=k, est=e, lo=lo, hi=hi, true_gain=t,
                                 claim=lo > 0, covered=lo <= t <= hi))
    return rows
if __name__ == "__main__":
    t0 = time.time(); jobs = [(n, r) for n in NS for r in range(REPS)]; out = []
    with mp.Pool(min(24, os.cpu_count())) as p:
        for rows in p.imap_unordered(one_rep, jobs, chunksize=4): out.extend(rows)
    df = pd.DataFrame(out); df.insert(0, "parser", parser); df.insert(0, "model", model)
    df.to_csv(OUT, index=False); print("saved", OUT, df.shape, "Q", Q, round(time.time() - t0))
