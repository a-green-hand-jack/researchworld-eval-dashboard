"""Run the hold-out-model protocol on a real leaderboard matrix.
Usage: python run_real.py <dataset> <split> [--repeats R] [--out DIR]
  dataset: mteb_main | mteb_dense | mteb_eng | openllm | helm_fine | helm_core10 | livebench
  split:   rand (5-fold over models, R repeats) | org (group 5-fold by organisation prefix, MTEB) | time (oldest 70% -> newest 30%)
"""
import sys, os, argparse, pickle, time, zlib
import numpy as np, pandas as pd
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from multiprocessing import Pool
from bsel.protocol import run_split, KS_DEFAULT

PROC = '/work/data/proc'


def load(ds):
    df = pd.read_csv(f'{PROC}/{ds}.csv', index_col=0)
    info = None
    if ds.startswith('mteb'):
        info = pd.read_csv(f'{PROC}/mteb_model_info.csv', index_col=0).reindex(df.index)
    if ds == 'openllm':
        info = pd.read_csv(f'{PROC}/openllm_info.csv', index_col=0).reindex(df.index)
    return df, info


def make_splits(ds, split, df, info, repeats):
    M = len(df); out = []
    if split == 'rand':
        for r in range(repeats):
            perm = np.random.default_rng(100 + r).permutation(M)
            folds = np.array_split(perm, 5)
            for f in range(5):
                te = folds[f]; tr = np.concatenate([folds[g] for g in range(5) if g != f]); out.append((f'r{r}f{f}', tr, te))
    elif split == 'org':
        org = np.array([m.split('__')[0] if '__' in m else m for m in df.index])
        uo = pd.Series(org).value_counts()
        rng = np.random.default_rng(7)
        # greedy balanced assignment of organisations to 5 folds
        folds = [[] for _ in range(5)]; sizes = [0] * 5
        for o in uo.index[np.argsort(-uo.values, kind='stable')]:
            f = int(np.argmin(sizes)); folds[f].append(o); sizes[f] += uo[o]
        for f in range(5):
            te = np.where(np.isin(org, folds[f]))[0]; tr = np.where(~np.isin(org, folds[f]))[0]; out.append((f'org{f}', tr, te))
    elif split == 'time':
        col = 'release_date' if ds.startswith('mteb') else 'Submission Date'
        d = pd.to_datetime(info[col], errors='coerce')
        known = d.notna().values
        cut = d[known].quantile(0.7)
        te = np.where(known & (d > cut).values)[0]; tr = np.where(~(known & (d > cut).values))[0]
        out.append(('time', tr, te))
    return out


def job(args):
    ds, name, tr, te, X, kw = args
    t = time.time()
    recs, pooled, meta = run_split(X, tr, te, seed=zlib.crc32(name.encode()) % 10000, **kw)
    for r in recs: r['fold'] = name
    return name, recs, pooled, meta, time.time() - t


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('dataset'); ap.add_argument('split')
    ap.add_argument('--repeats', type=int, default=3); ap.add_argument('--out', default='/work/out/results')
    ap.add_argument('--procs', type=int, default=20); ap.add_argument('--max_test', type=int, default=0)
    ap.add_argument('--tag', default='')
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    df, info = load(a.dataset); X = df.values
    N = X.shape[1]
    ks = tuple(k for k in KS_DEFAULT if k <= N - 2)
    if N <= 12: ks = tuple(range(1, N - 1))
    kw = dict(ks=ks)
    if a.dataset in ('openllm',): kw['n_rand'] = 5
    if N <= 12: kw['t0_mode'] = 'loo'; kw['ks'] = tuple(range(1, int(np.min((~np.isnan(X)).sum(1))) - 1))
    elif N <= 30: kw['n_t0'] = 4; kw['ks'] = tuple(k for k in KS_DEFAULT if k <= 14)
    if N <= 12 and a.dataset == 'openllm': kw['n_rand'] = 5
    splits = make_splits(a.dataset, a.split, df, info, a.repeats)
    if a.max_test:
        splits = [(n, tr, te[:a.max_test]) for n, tr, te in splits]
    print(a.dataset, a.split, X.shape, 'splits', len(splits), 'ks', kw['ks'], flush=True)
    t0 = time.time()
    with Pool(min(a.procs, len(splits))) as p:
        res = p.map(job, [(a.dataset, n, tr, te, X, kw) for n, tr, te in splits])
    recs = [r for _, rs, _, _, _ in res for r in rs]
    pooled = [dict(fold=n, rows=pl) for n, _, pl, _, _ in res]
    metas = {n: m for n, _, _, m, _ in res}
    pd.DataFrame(recs).to_parquet(f'{a.out}/{a.dataset}__{a.split}{a.tag}.parquet')
    pickle.dump(dict(pooled=pooled, metas=metas, index=list(df.index), columns=list(df.columns)),
                open(f'{a.out}/{a.dataset}__{a.split}{a.tag}.pkl', 'wb'))
    print('done', time.time() - t0, 'sec; fold times', [round(t) for *_, t in res], flush=True)
    print({n: (m['fa_r'], m['chosen']) for n, m in list(metas.items())[:2]})
