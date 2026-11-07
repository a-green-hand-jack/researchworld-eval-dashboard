"""Data-condition experiments on MTEB (mteb_main): training-set size, training-entry density, benchmark-pool composition,
score transform. Same hold-out-model protocol as run_real.py, restricted to a cheap set of methods.
Usage: python run_conditions.py [--procs P]   -> /work/out/results/conditions__mteb_main.parquet"""
import sys, os, argparse, time, zlib
import numpy as np, pandas as pd
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from multiprocessing import Pool
from bsel.protocol import run_split

PROC = '/work/data/proc'
KS = (2, 5, 10, 20)
KW = dict(ks=KS, selectors=('random', 'greedy_var', 'kmedoids', 'popular'), predictors=('gauss', 'fa', 'mean'), n_rand=10)


def families(names):
    """Heuristic benchmark family = task name without version / task-type / language-variant suffixes."""
    import re
    out = []
    for n in names:
        if n.startswith('CQADupstack'): out.append('CQADupstack'); continue
        t = re.sub(r'\.v\d+$', '', n)
        t = re.sub(r'(HardNegatives|ClusteringP2P|ClusteringS2S|Clustering|PairClassification|Classification|Classfication|Reranking|reranking|Retrieval|retrieval|BitextMining|Summarization|Multilingual|STS)$', '', t)
        t = re.sub(r'[-_](VN|PL|Fa|NL|DE|FR|ES|RU|ZH|JA|KO)$', '', t)
        out.append((t if t else n).lower())
    return np.array(out)


def logit(X):
    p = np.clip(X / 100.0, 0.005, 0.995); return np.log(p / (1 - p))


def inv_logit(y):
    return 100.0 / (1 + np.exp(-y))


def job(a):
    cond, level, fold, X, tr, te, kw = a
    recs, _, meta = run_split(X, tr, te, seed=zlib.crc32(f'{cond}{level}{fold}'.encode()) % 10000, **kw)
    for r in recs: r.update(cond=cond, level=str(level), fold=fold)
    return recs


if __name__ == '__main__':
    ap = argparse.ArgumentParser(); ap.add_argument('--procs', type=int, default=20); a = ap.parse_args()
    df = pd.read_csv(f'{PROC}/mteb_main.csv', index_col=0); X0 = df.values
    tinfo = pd.read_csv(f'{PROC}/mteb_task_info.csv', index_col=0).reindex(df.columns)
    M = len(df)
    perm = np.random.default_rng(100).permutation(M); folds = np.array_split(perm, 5)
    jobs = []
    for f in range(5):
        te = folds[f]; tr = np.concatenate([folds[g] for g in range(5) if g != f])
        rng = np.random.default_rng(f)
        # (a) number of training models
        for m in (25, 50, 100, len(tr)):
            jobs.append(('n_train', m, f, X0, rng.permutation(tr)[:m], te, KW))
        # (b) training-entry density: drop observed training cells
        for q in (0.0, 0.3, 0.6):
            X = X0.copy(); obs = ~np.isnan(X[tr]); drop = rng.random(obs.shape) < q
            Xt = X[tr]; Xt[drop & obs] = np.nan; X[tr] = Xt
            jobs.append(('drop_train_cells', q, f, X, tr, te, KW))
        # (c) benchmark-pool composition
        for name, cols in [('retrieval', tinfo.type == 'Retrieval'), ('classification', tinfo.type == 'Classification'),
                           ('clustering+sts+pair', tinfo.type.isin(['Clustering', 'STS', 'PairClassification'])),
                           ('english-only', tinfo.langs == 'eng'), ('non-english', tinfo.langs != 'eng')]:
            c = np.where(cols.values)[0]
            kw = dict(KW); kw['ks'] = tuple(k for k in KS if k <= 0.7 * len(c) - 3)
            jobs.append(('pool', f'{name}(N={len(c)})', f, X0[:, c], tr, te, kw))
        # (e) fraction of the model's observed benchmarks held out as targets
        for fr in (0.1, 0.5):
            kw = dict(KW); kw['t0_frac'] = fr
            jobs.append(('t0_frac', fr, f, X0, tr, te, kw))
        # (f) family-disjoint targets (near-duplicate tasks of a target never enter the pool)
        gid = pd.factorize(families(df.columns))[0]
        kw = dict(KW); kw['groups'] = gid
        jobs.append(('family', 'disjoint', f, X0, tr, te, kw))
        # (d) transform
        kw = dict(KW); kw['transform'] = logit; kw['inv_transform'] = inv_logit
        jobs.append(('transform', 'logit', f, X0, tr, te, kw))
        jobs.append(('transform', 'none', f, X0, tr, te, KW))
    print(len(jobs), 'jobs', flush=True); t0 = time.time()
    with Pool(a.procs) as p:
        res = p.map(job, jobs, chunksize=1)
    pd.DataFrame([r for rs in res for r in rs]).to_parquet('/work/out/results/conditions__mteb_main.parquet')
    print('done', time.time() - t0)
