"""Protocol-pitfall experiment: scoring on the complement T = C \\ S (naive) versus on a fixed held-out target set T0
(this paper's protocol). Same Gaussian predictor and selectors; only the evaluation targets differ.
Usage: python run_bias.py <dataset>   -> /work/out/results/bias__<dataset>.parquet"""
import sys, os, zlib
import numpy as np, pandas as pd
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from multiprocessing import Pool
from bsel import predict as P, select as sel
from bsel.protocol import standardize, make_orders

PROC = '/work/data/proc'


def job(a):
    X, tr, te, name, ks, seed = a
    rng = np.random.default_rng(seed)
    mu, sd = standardize(X[tr]); Z = (X[tr] - mu) / sd; N = X.shape[1]
    kw, _ = P.tune('gauss', Z, P.GRIDS['gauss'], seed=seed); g = P.make('gauss', **kw).fit(Z); cov = g.cov()
    pop = (~np.isnan(Z)).sum(0).astype(float)
    recs = []
    for i in te:
        zi = (X[i] - mu) / sd; C = np.where(~np.isnan(zi))[0]
        nt = max(2, int(round(0.3 * len(C)))); T0 = np.sort(rng.choice(C, nt, replace=False)); pool = np.setdiff1d(C, T0)
        for s in ('random', 'greedy_var', 'kmedoids', 'popular'):
            for k in ks:
                if len(pool) - k < 1: continue
                if s == 'kmedoids':
                    Sf = pool[sel.kmedoids(cov[np.ix_(pool, pool)], k, seed=seed)]; Sc = C[sel.kmedoids(cov[np.ix_(C, C)], k, seed=seed)]
                else:
                    Sf = pool[make_orders(s, cov, None, pool, k, rng, pop)]; Sc = C[make_orders(s, cov, None, C, k, rng, pop)]
                zh = g.predict(Sf, zi[Sf]); e_fixed = np.mean((zh[T0] - zi[T0]) ** 2)
                Tc = np.setdiff1d(C, Sc); zh = g.predict(Sc, zi[Sc]); e_comp = np.mean((zh[Tc] - zi[Tc]) ** 2)
                recs.append(dict(model=int(i), fold=name, selector=s, k=k, mse_fixed=e_fixed, mse_complement=e_comp, n_comp=len(Tc), n_fixed=len(T0)))
    return recs


if __name__ == '__main__':
    ds = sys.argv[1]
    df = pd.read_csv(f'{PROC}/{ds}.csv', index_col=0); X = df.values; N = X.shape[1]
    ks = (1, 2, 3, 5, 8, 12) if N <= 30 else (1, 2, 5, 10, 20, 40)
    jobs = []
    for r in range(3 if N > 30 else 6):
        perm = np.random.default_rng(100 + r).permutation(len(X)); folds = np.array_split(perm, 5)
        for f in range(5):
            tr = np.concatenate([folds[g] for g in range(5) if g != f])
            jobs.append((X, tr, folds[f], f'r{r}f{f}', ks, zlib.crc32(f'{r}{f}'.encode()) % 10000))
    with Pool(15) as p:
        res = p.map(job, jobs)
    pd.DataFrame([r for rs in res for r in rs]).to_parquet(f'/work/out/results/bias__{ds}.parquet')
    print('done')
