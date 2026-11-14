"""Controlled factor sweeps on synthetic IRT-style worlds (exhaustive search).  Usage: python exp_synth.py OUT [R] [WORKERS]"""
import sys, os, itertools, time, hashlib
sys.path.insert(0, "/work/code")
import numpy as np, pandas as pd
from multiprocessing import Pool
from sim_lib import *
from worlds import synth_world

def job(a):
    K, tau, sd_int, n, R, seed = a
    Y = synth_world(K=K, N=20000, tau=tau, sd_int=sd_int, seed=seed); th = Y.mean(1); N = Y.shape[1]
    rng = np.random.default_rng(seed * 7 + n); space = np.arange(K); rows = []
    corr = np.corrcoef(Y[:, :4000])[np.triu_indices(K, 1)].mean() if K > 1 else np.nan
    sd_theta = th.std(); sig_n = np.sqrt(np.mean(th * (1 - th)) / n)
    for _ in range(R):
        D = rng.integers(N, size=n); Yd = Y[:, D]; k = int(OPTS['grid'](Yd, space, rng)['k'])
        ns = n // 2; ks = int(OPTS['grid'](Yd[:, :ns], space, rng)['k'])
        rows.append(dict(K=K, tau=tau, sd_int=sd_int, n=n, seed=seed, gap=Yd[k].mean() - th[k], regret=th.max() - th[k],
                         split_bias=Yd[ks, ns:].mean() - th[ks], split_regret=th.max() - th[ks], sd_theta=sd_theta, sig_n=sig_n, corr=corr))
    return rows

def main():
    out = sys.argv[1]; R = int(sys.argv[2]) if len(sys.argv) > 2 else 400; nw = int(sys.argv[3]) if len(sys.argv) > 3 else 2
    os.makedirs(out, exist_ok=True); jobs = []
    for K, tau, sd_int, n in itertools.product((2, 5, 10, 40, 160), (0.0, 0.05, 0.1, 0.2, 0.4), (0.3, 0.8, 1.5), (50, 100, 200, 400, 800)):
        for seed in (1, 2):
            jobs.append((K, tau, sd_int, n, R // 2, seed))
    with Pool(nw) as p: rows = [x for r in p.imap_unordered(job, jobs) for x in r]
    pd.DataFrame(rows).to_parquet(f"{out}/synth_sweep.parquet"); print(len(rows), "rows")
if __name__ == "__main__": main()
